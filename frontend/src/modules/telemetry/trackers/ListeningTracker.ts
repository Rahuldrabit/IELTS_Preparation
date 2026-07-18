/**
 * ListeningTracker — audio-synchronized telemetry for listening practice.
 *
 * Tracks what the user is looking at relative to audio playback position.
 * Detects distractor attraction (gaze on wrong choices during keywords).
 *
 * Design:
 *   - Accepts audio element reference for time sync
 *   - Reuses gaze pipeline from ReadingTracker subsystems
 *   - Emits events correlated with audio timestamps
 *   - Computes audio-gaze alignment metric
 */

import { Emitter } from '../core/Emitter'
import type {
  GazePoint,
  ILifecycle,
  TelemetryConfig,
  TelemetryEvent,
  TelemetryEventType,
} from '../types'
import { CameraManager } from '../camera/CameraManager'
import { FaceMeshProcessor } from '../camera/FaceMesh'
import { CalibrationSystem } from '../camera/Calibration'
import { GazeEstimator } from '../gaze/GazeEstimator'
import { AOIMapper } from '../gaze/AOIMapper'
import { FocusTracker } from './FocusTracker'

export interface ListeningTrackerEventMap {
  event: TelemetryEvent
  gazePoint: GazePoint
  choiceGaze: { questionId: number; optionIndex: number; duration: number; audioTimeMs: number }
}

export interface ListeningTrackerDeps {
  /** HTML audio element to sync with */
  audioElement: HTMLAudioElement
}

export class ListeningTracker extends Emitter<ListeningTrackerEventMap> implements ILifecycle {
  readonly camera: CameraManager
  readonly faceMesh: FaceMeshProcessor
  readonly calibration: CalibrationSystem
  readonly gazeEstimator: GazeEstimator
  readonly aoiMapper: AOIMapper
  readonly focusTracker: FocusTracker

  private config: TelemetryConfig
  private sessionId: string
  private existingStream?: MediaStream
  private audioElement: HTMLAudioElement | null = null
  private disposers: (() => void)[] = []
  private eventIdCounter = 0

  // Choice gaze tracking
  private currentChoiceStart: number | null = null
  private currentChoiceAoi: string | null = null

  constructor(sessionId: string, config: TelemetryConfig, existingStream?: MediaStream) {
    super()
    this.sessionId = sessionId
    this.config = config
    this.existingStream = existingStream

    this.camera = new CameraManager()
    this.faceMesh = new FaceMeshProcessor()
    this.calibration = new CalibrationSystem()
    this.aoiMapper = new AOIMapper()
    this.gazeEstimator = new GazeEstimator({ getMatrix: () => this.calibration.state.matrix })
    this.focusTracker = new FocusTracker()
  }

  // ─────────────────────────────────────────────
  //  Public API
  // ─────────────────────────────────────────────

  /** Set the audio element to sync timestamps with */
  setAudioElement(el: HTMLAudioElement): void {
    this.audioElement = el
  }

  get audioTimeMs(): number {
    return this.audioElement ? this.audioElement.currentTime * 1000 : 0
  }

  async start(): Promise<void> {
    this.aoiMapper.start()
    this.focusTracker.start()

    if (this.config.gazeEnabled) {
      await this.faceMesh.start()
      await this.camera.start(this.existingStream)
      this.gazeEstimator.start()
      this.wireGaze()
    }

    this.pushEvent('session_start', { skill: 'listening' })
  }

  stop(): void {
    this.pushEvent('session_end', { skill: 'listening' })
    this.gazeEstimator.stop()
    this.focusTracker.stop()
    this.aoiMapper.stop()
    this.camera.stop()
    this.disposers.forEach((d) => d())
    this.disposers = []
  }

  destroy(): void {
    this.stop()
    this.camera.destroy()
    this.faceMesh.destroy()
    this.calibration.destroy()
    this.gazeEstimator.destroy()
    this.aoiMapper.destroy()
    this.focusTracker.destroy()
    this.removeAllListeners()
  }

  // ─────────────────────────────────────────────
  //  Private — Gaze Pipeline
  // ─────────────────────────────────────────────

  private wireGaze(): void {
    const d1 = this.camera.on('frame', ({ video, timestamp }) => {
      if (!this.focusTracker.focused) return

      const result = this.faceMesh.process(video, timestamp)
      if (!result?.landmarks) return

      const gazePoint = this.gazeEstimator.estimate(result.landmarks, result.headPose, timestamp)
      if (!gazePoint) return

      this.emit('gazePoint', gazePoint)

      // Map gaze to AOI (choice/question)
      const hit = this.aoiMapper.resolve(gazePoint.x, gazePoint.y)

      // Track choice gaze duration for distractor analysis
      this.trackChoiceGaze(hit.aoiId, gazePoint.timestamp)

      this.pushEvent('mouse_move', {
        x: gazePoint.x,
        y: gazePoint.y,
        aoiId: hit.aoiId,
        audioTimeMs: this.audioTimeMs,
      })
    })
    this.disposers.push(d1)
  }

  private trackChoiceGaze(aoiId: string | null, timestamp: number): void {
    // If gaze moved to a different AOI
    if (aoiId !== this.currentChoiceAoi) {
      // Emit duration for previous choice
      if (this.currentChoiceAoi && this.currentChoiceStart) {
        const duration = timestamp - this.currentChoiceStart
        if (duration > 100 && this.currentChoiceAoi.startsWith('opt_')) {
          const parts = this.currentChoiceAoi.replace('opt_', '').split('-')
          const questionId = parseInt(parts[0], 10)
          const optionIndex = parseInt(parts[1], 10)
          this.emit('choiceGaze', {
            questionId,
            optionIndex,
            duration,
            audioTimeMs: this.audioTimeMs,
          })
        }
      }

      this.currentChoiceAoi = aoiId
      this.currentChoiceStart = timestamp
    }
  }

  // ─────────────────────────────────────────────
  //  Private — Event Push
  // ─────────────────────────────────────────────

  private pushEvent(type: TelemetryEventType, data: Record<string, unknown>): void {
    const event: TelemetryEvent = {
      id: `${this.sessionId}_${++this.eventIdCounter}`,
      type,
      timestamp: performance.now(),
      sessionId: this.sessionId,
      data: { ...data, audioTimeMs: this.audioTimeMs },
    }
    this.emit('event', event)
  }
}
