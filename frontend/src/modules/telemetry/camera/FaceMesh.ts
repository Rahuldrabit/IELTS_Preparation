/**
 * FaceMesh — MediaPipe FaceLandmarker wrapper with lazy initialization.
 *
 * Design:
 *   - Lazy-loads @mediapipe/tasks-vision on first use (code-split friendly)
 *   - Emits typed events: result, ready, error
 *   - Extracts iris/eye landmarks subset from 478-point mesh
 *   - EAR-based blink detection
 *   - Head pose extraction from transformation matrix
 *   - Single-face mode optimized for performance
 *
 * Key landmark indices (0-indexed):
 *   Left iris center:  468    Right iris center: 473
 *   Left eye inner:    133    Left eye outer:    33
 *   Right eye inner:   362    Right eye outer:   263
 *   Left eye upper:    159    Left eye lower:    145
 *   Right eye upper:   386    Right eye lower:   374
 */

import { Emitter } from '../core/Emitter'
import type { EyeLandmarks, FaceMeshEventMap, FaceMeshResult, FaceMeshProgress, HeadPose, ILifecycle, Point3D } from '../types'

// ─────────────────────────────────────────────
//  Constants
// ─────────────────────────────────────────────

const LM = {
  LEFT_IRIS: 468,
  RIGHT_IRIS: 473,
  LEFT_EYE_INNER: 133,
  LEFT_EYE_OUTER: 33,
  RIGHT_EYE_INNER: 362,
  RIGHT_EYE_OUTER: 263,
  LEFT_EYE_UPPER: 159,
  LEFT_EYE_LOWER: 145,
  RIGHT_EYE_UPPER: 386,
  RIGHT_EYE_LOWER: 374,
} as const

export interface FaceMeshConfig {
  /** CDN base URL for WASM files */
  wasmUrl: string
  /** CDN URL for the model .task file */
  modelUrl: string
  /** Use GPU delegate if available */
  useGpu: boolean
  /** EAR threshold for blink detection (lower = more sensitive) */
  earThreshold: number
  /** Consecutive low-EAR frames to confirm blink */
  blinkFrameCount: number
  /** Whether to pre-warm download on page load */
  prewarm: boolean
}



const DEFAULT_CONFIG: FaceMeshConfig = {
  wasmUrl: 'https://cdn.jsdelivr.net/npm/@mediapipe/tasks-vision@0.10.18/wasm',
  modelUrl: 'https://storage.googleapis.com/mediapipe-models/face_landmarker/face_landmarker/float16/1/face_landmarker.task',
  useGpu: true,
  earThreshold: 0.2,
  blinkFrameCount: 2,
  prewarm: true,
}

export class FaceMeshProcessor extends Emitter<FaceMeshEventMap> implements ILifecycle {
  private config: FaceMeshConfig
  private landmarker: unknown = null
  private initialized = false
  private processing = false
  private blinkCounter = 0
  private prewarmPromise: Promise<void> | null = null

  constructor(config: Partial<FaceMeshConfig> = {}) {
    super()
    this.config = { ...DEFAULT_CONFIG, ...config }
  }

  // ─────────────────────────────────────────────
  //  Public API
  // ─────────────────────────────────────────────

  get ready(): boolean {
    return this.initialized
  }

  /** Pre-warm download in background (call on page load) */
  prewarm(): void {
    if (this.prewarmPromise || this.initialized) return
    
    if (this.config.prewarm) {
      this.prewarmPromise = this.internalStart(true).catch(() => {
        // Silent fail for pre-warm - we'll try again on real start
        this.prewarmPromise = null
      })
    }
  }

  /** Check if model is likely cached (based on previous success) */
  isLikelyCached(): boolean {
    if (typeof window === 'undefined') return false
    const cacheKey = `cte_facemesh_cached_${this.config.modelUrl}`
    return localStorage.getItem(cacheKey) === 'true'
  }

  /**
   * Lazy-load MediaPipe and create FaceLandmarker.
   * Safe to call multiple times (idempotent).
   */
  async start(): Promise<void> {
    if (this.initialized) return
    
    // If pre-warm is in progress, wait for it
    if (this.prewarmPromise) {
      try {
        await this.prewarmPromise
        if (this.initialized) return // Pre-warm succeeded
      } catch {
        // Pre-warm failed, continue with normal start
      }
    }

    await this.internalStart(false)
  }

  /** Internal start with progress tracking */
  private async internalStart(isPrewarm: boolean): Promise<void> {
    try {
      // Stage 1: Download MediaPipe library
      if (!isPrewarm) this.emitProgress('library', 10)
      const { FaceLandmarker, FilesetResolver } = await import('@mediapipe/tasks-vision')
      if (!isPrewarm) this.emitProgress('library', 40)

      // Stage 2: Download WASM files
      if (!isPrewarm) this.emitProgress('wasm', 50)
      const fileset = await FilesetResolver.forVisionTasks(this.config.wasmUrl)
      if (!isPrewarm) this.emitProgress('wasm', 80)

      // Stage 3: Download model file
      if (!isPrewarm) this.emitProgress('model', 85)
      this.landmarker = await FaceLandmarker.createFromOptions(fileset, {
        baseOptions: {
          modelAssetPath: this.config.modelUrl,
          delegate: this.config.useGpu ? 'GPU' : 'CPU',
        },
        runningMode: 'VIDEO',
        numFaces: 1,
        outputFaceBlendshapes: false,
        outputFacialTransformationMatrixes: true,
      })
      if (!isPrewarm) this.emitProgress('model', 95)

      // Stage 4: Initialization complete
      if (!isPrewarm) this.emitProgress('initializing', 100)
      this.initialized = true
      
      // Mark as cached for future sessions
      if (!isPrewarm && typeof window !== 'undefined') {
        const cacheKey = `cte_facemesh_cached_${this.config.modelUrl}`
        localStorage.setItem(cacheKey, 'true')
      }
      
      if (!isPrewarm) this.emit('ready', undefined as never)
    } catch (err) {
      const error = err instanceof Error ? err : new Error(String(err))
      if (!isPrewarm) this.emit('error', error)
      throw error
    }
  }

  stop(): void {
    // No-op for pause semantics; use destroy() for full teardown
  }

  destroy(): void {
    if (this.landmarker) {
      // eslint-disable-next-line @typescript-eslint/no-explicit-any
      (this.landmarker as any).close?.()
      this.landmarker = null
    }
    this.initialized = false
    this.removeAllListeners()
  }

  /**
   * Process a single video frame. Returns result and emits 'result' event.
   * Non-blocking: skips frame if previous is still processing.
   */
  process(video: HTMLVideoElement, timestamp: number): FaceMeshResult | null {
    if (!this.initialized || !this.landmarker || this.processing) {
      return null
    }

    this.processing = true

    try {
      // eslint-disable-next-line @typescript-eslint/no-explicit-any
      const results = (this.landmarker as any).detectForVideo(video, timestamp)

      if (!results?.faceLandmarks?.length) {
        const empty: FaceMeshResult = { landmarks: null, blinkDetected: false, headPose: null, timestamp }
        this.emit('result', empty)
        return empty
      }

      const raw = results.faceLandmarks[0]
      const landmarks = this.extractEyeLandmarks(raw)
      const blinkDetected = this.detectBlink(raw)
      const headPose = this.extractHeadPose(results.facialTransformationMatrixes)
      const fullMesh = raw.map((p: any) => ({ x: p.x, y: p.y, z: p.z }))

      const result: FaceMeshResult = { landmarks, blinkDetected, headPose, timestamp, fullMesh }
      this.emit('result', result)
      return result
    } catch (err) {
      console.warn('[CTE:FaceMesh] Frame error:', err)
      return null
    } finally {
      this.processing = false
    }
  }

  /** Update config (takes effect immediately for thresholds, on next start for URLs) */
  configure(config: Partial<FaceMeshConfig>): void {
    this.config = { ...this.config, ...config }
  }

  /** Emit progress event */
  private emitProgress(stage: string, progress: number, estimatedMs?: number): void {
    this.emit('progress', { stage, progress, estimatedMs })
  }

  // ─────────────────────────────────────────────
  //  Private — Extraction
  // ─────────────────────────────────────────────

  private extractEyeLandmarks(raw: Array<{ x: number; y: number; z: number }>): EyeLandmarks {
    const p = (idx: number): Point3D => ({
      x: raw[idx].x,
      y: raw[idx].y,
      z: raw[idx].z,
    })

    return {
      leftIris: p(LM.LEFT_IRIS),
      rightIris: p(LM.RIGHT_IRIS),
      leftEyeCorners: { inner: p(LM.LEFT_EYE_INNER), outer: p(LM.LEFT_EYE_OUTER) },
      rightEyeCorners: { inner: p(LM.RIGHT_EYE_INNER), outer: p(LM.RIGHT_EYE_OUTER) },
      leftEyeUpper: p(LM.LEFT_EYE_UPPER),
      leftEyeLower: p(LM.LEFT_EYE_LOWER),
      rightEyeUpper: p(LM.RIGHT_EYE_UPPER),
      rightEyeLower: p(LM.RIGHT_EYE_LOWER),
    }
  }

  // ─────────────────────────────────────────────
  //  Private — Blink Detection (Eye Aspect Ratio)
  // ─────────────────────────────────────────────

  private detectBlink(raw: Array<{ x: number; y: number; z: number }>): boolean {
    const leftEAR = this.ear(
      raw[LM.LEFT_EYE_UPPER], raw[LM.LEFT_EYE_LOWER],
      raw[LM.LEFT_EYE_INNER], raw[LM.LEFT_EYE_OUTER],
    )
    const rightEAR = this.ear(
      raw[LM.RIGHT_EYE_UPPER], raw[LM.RIGHT_EYE_LOWER],
      raw[LM.RIGHT_EYE_INNER], raw[LM.RIGHT_EYE_OUTER],
    )

    const avgEAR = (leftEAR + rightEAR) / 2
    const closed = avgEAR < this.config.earThreshold

    if (closed) {
      this.blinkCounter++
      return false // Don't emit until eyes re-open
    }

    if (this.blinkCounter >= this.config.blinkFrameCount) {
      this.blinkCounter = 0
      return true
    }

    this.blinkCounter = 0
    return false
  }

  /** Eye Aspect Ratio: vertical / horizontal distance */
  private ear(
    upper: { x: number; y: number },
    lower: { x: number; y: number },
    inner: { x: number; y: number },
    outer: { x: number; y: number },
  ): number {
    const v = Math.hypot(upper.x - lower.x, upper.y - lower.y)
    const h = Math.hypot(inner.x - outer.x, inner.y - outer.y)
    return h > 0 ? v / h : 0
  }

  // ─────────────────────────────────────────────
  //  Private — Head Pose
  // ─────────────────────────────────────────────

  private extractHeadPose(
    matrices?: Array<{ data: Float32Array }>
  ): HeadPose | null {
    if (!matrices?.length) return null
    const m = matrices[0].data
    if (!m || m.length < 16) return null

    const RAD2DEG = 180 / Math.PI
    const pitch = Math.asin(-m[6]) * RAD2DEG
    const yaw = Math.atan2(m[2], m[10]) * RAD2DEG
    const roll = Math.atan2(m[4], m[5]) * RAD2DEG

    return { pitch, yaw, roll }
  }
}
