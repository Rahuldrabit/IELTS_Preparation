/**
 * GazeEstimator — maps iris landmarks to screen coordinates via calibration.
 *
 * Design:
 *   - Strategy pattern: accepts any ICalibrationProvider
 *   - Smoothing via exponential moving average (reduces jitter)
 *   - Confidence scoring based on eye openness + head stability
 *   - Emits GazePoint events at configured sampling rate
 *   - Clamping to viewport bounds
 */

import { Emitter } from '../core/Emitter'
import type {
  CalibrationMatrix,
  EyeLandmarks,
  GazeEventMap,
  GazePoint,
  HeadPose,
  ILifecycle,
  Point2D,
} from '../types'
import { applyCalibration } from '../camera/Calibration'

// ─────────────────────────────────────────────
//  Pluggable calibration interface
// ─────────────────────────────────────────────

export interface ICalibrationProvider {
  getMatrix(): CalibrationMatrix | null
}

// ─────────────────────────────────────────────
//  Config
// ─────────────────────────────────────────────

export interface GazeEstimatorConfig {
  /** EMA smoothing factor (0-1). Higher = less smoothing. */
  smoothingFactor: number
  /** Max head yaw (degrees) before confidence drops to 0 */
  maxHeadYaw: number
  /** Max head pitch (degrees) before confidence drops to 0 */
  maxHeadPitch: number
  /** Minimum confidence to emit a gaze point */
  minConfidence: number
}

const DEFAULT_CONFIG: GazeEstimatorConfig = {
  smoothingFactor: 0.4,
  maxHeadYaw: 30,
  maxHeadPitch: 25,
  minConfidence: 0.3,
}

export class GazeEstimator extends Emitter<GazeEventMap> implements ILifecycle {
  private config: GazeEstimatorConfig
  private calibrationProvider: ICalibrationProvider
  private smoothed: Point2D | null = null
  private _active = false

  constructor(
    calibrationProvider: ICalibrationProvider,
    config: Partial<GazeEstimatorConfig> = {},
  ) {
    super()
    this.calibrationProvider = calibrationProvider
    this.config = { ...DEFAULT_CONFIG, ...config }
  }

  // ─────────────────────────────────────────────
  //  Public API
  // ─────────────────────────────────────────────

  get active(): boolean {
    return this._active
  }

  start(): void {
    this._active = true
    this.smoothed = null
  }

  stop(): void {
    this._active = false
  }

  destroy(): void {
    this.stop()
    this.removeAllListeners()
  }

  /** Update config at runtime (e.g., user adjusts smoothing) */
  configure(config: Partial<GazeEstimatorConfig>): void {
    this.config = { ...this.config, ...config }
  }

  /** Swap calibration provider (e.g., after recalibration) */
  setCalibrationProvider(provider: ICalibrationProvider): void {
    this.calibrationProvider = provider
  }

  /**
   * Process eye landmarks into a screen gaze point.
   * Call this on every FaceMesh result.
   * Returns null if calibration unavailable or confidence too low.
   */
  estimate(landmarks: EyeLandmarks, headPose: HeadPose | null, timestamp: number): GazePoint | null {
    if (!this._active) return null

    const matrix = this.calibrationProvider.getMatrix()
    if (!matrix) return null

    // Average both irises for stability
    const irisX = (landmarks.leftIris.x + landmarks.rightIris.x) / 2
    const irisY = (landmarks.leftIris.y + landmarks.rightIris.y) / 2

    // Apply polynomial calibration
    const raw = applyCalibration(matrix, irisX, irisY)

    // Smooth with EMA
    const smoothed = this.applySmoothing(raw)

    // Clamp to viewport
    const clamped = this.clamp(smoothed)

    // Compute confidence
    const confidence = this.computeConfidence(landmarks, headPose)

    if (confidence < this.config.minConfidence) return null

    const point: GazePoint = {
      x: clamped.x,
      y: clamped.y,
      timestamp,
      confidence,
    }

    this.emit('point', point)
    return point
  }

  // ─────────────────────────────────────────────
  //  Private — Smoothing
  // ─────────────────────────────────────────────

  private applySmoothing(raw: Point2D): Point2D {
    const alpha = this.config.smoothingFactor

    if (!this.smoothed) {
      this.smoothed = raw
      return raw
    }

    this.smoothed = {
      x: alpha * raw.x + (1 - alpha) * this.smoothed.x,
      y: alpha * raw.y + (1 - alpha) * this.smoothed.y,
    }

    return this.smoothed
  }

  // ─────────────────────────────────────────────
  //  Private — Confidence
  // ─────────────────────────────────────────────

  private computeConfidence(landmarks: EyeLandmarks, headPose: HeadPose | null): number {
    // Factor 1: Eye openness (if eyes nearly closed, low confidence)
    const leftOpen = Math.hypot(
      landmarks.leftEyeUpper.x - landmarks.leftEyeLower.x,
      landmarks.leftEyeUpper.y - landmarks.leftEyeLower.y,
    )
    const rightOpen = Math.hypot(
      landmarks.rightEyeUpper.x - landmarks.rightEyeLower.x,
      landmarks.rightEyeUpper.y - landmarks.rightEyeLower.y,
    )
    const avgOpen = (leftOpen + rightOpen) / 2
    // Normalize: typical open eye ~0.04-0.06 in normalized coords
    const openScore = Math.min(1, avgOpen / 0.03)

    // Factor 2: Head pose stability
    let poseScore = 1
    if (headPose) {
      const yawPenalty = Math.min(1, Math.abs(headPose.yaw) / this.config.maxHeadYaw)
      const pitchPenalty = Math.min(1, Math.abs(headPose.pitch) / this.config.maxHeadPitch)
      poseScore = 1 - Math.max(yawPenalty, pitchPenalty)
    }

    // Composite: geometric mean of factors
    return Math.sqrt(openScore * poseScore)
  }

  // ─────────────────────────────────────────────
  //  Private — Clamping
  // ─────────────────────────────────────────────

  private clamp(point: Point2D): Point2D {
    return {
      x: Math.max(0, Math.min(window.innerWidth, point.x)),
      y: Math.max(0, Math.min(window.innerHeight, point.y)),
    }
  }
}
