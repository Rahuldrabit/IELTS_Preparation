/**
 * WorkerBridge — typed main-thread ↔ worker communication layer.
 *
 * Abstracts Worker instantiation and message passing behind a typed API.
 * Handles:
 *   - Worker creation with proper URL (Next.js compatible)
 *   - Typed send/receive via discriminated unions
 *   - Frame transfer using OffscreenCanvas + ImageBitmap for zero-copy
 *   - Graceful error handling and termination
 *
 * Usage:
 *   const bridge = new WorkerBridge()
 *   bridge.on('result', (faceMeshResult) => { ... })
 *   await bridge.init()
 *   bridge.sendFrame(video) // per-frame in rAF loop
 */

import { Emitter } from '../core/Emitter'
import type { FaceMeshResult, ILifecycle, WorkerInMessage, WorkerOutMessage } from '../types'

export interface WorkerBridgeConfig {
  /** URL for the worker script (relative to public/) */
  workerUrl: string
  /** CDN URL for MediaPipe WASM files */
  wasmUrl: string
  /** CDN URL for the FaceLandmarker model */
  modelUrl: string
}

const DEFAULT_CONFIG: WorkerBridgeConfig = {
  workerUrl: '', // Will use inline worker creation
  wasmUrl: 'https://cdn.jsdelivr.net/npm/@mediapipe/tasks-vision@0.10.18/wasm',
  modelUrl: 'https://storage.googleapis.com/mediapipe-models/face_landmarker/face_landmarker/float16/1/face_landmarker.task',
}

export interface WorkerBridgeEventMap {
  ready: void
  result: FaceMeshResult
  error: Error
}

export class WorkerBridge extends Emitter<WorkerBridgeEventMap> implements ILifecycle {
  private config: WorkerBridgeConfig
  private worker: Worker | null = null
  private canvas: OffscreenCanvas | null = null
  private ctx: OffscreenCanvasRenderingContext2D | null = null
  private ready = false

  constructor(config: Partial<WorkerBridgeConfig> = {}) {
    super()
    this.config = { ...DEFAULT_CONFIG, ...config }
  }

  // ─────────────────────────────────────────────
  //  Public API
  // ─────────────────────────────────────────────

  get isReady(): boolean {
    return this.ready
  }

  /**
   * Create the worker and send init message.
   * Resolves when worker reports 'ready'.
   */
  async start(): Promise<void> {
    return new Promise((resolve, reject) => {
      try {
        this.worker = new Worker(
          new URL('./telemetry.worker.ts', import.meta.url),
          { type: 'module' }
        )

        this.worker.onmessage = (e: MessageEvent<WorkerOutMessage>) => {
          this.handleMessage(e.data)
        }

        this.worker.onerror = (err) => {
          const error = new Error(`Worker error: ${err.message}`)
          this.emit('error', error)
          reject(error)
        }

        // Listen for ready signal
        const readyDispose = this.once('ready', () => {
          this.ready = true
          resolve()
        })

        // Also handle init error
        const errorDispose = this.once('error', (err) => {
          readyDispose()
          reject(err)
        })

        // Send init message
        this.send({ type: 'init', payload: { modelUrl: this.config.modelUrl, wasmUrl: this.config.wasmUrl } })

        // Timeout after 30 seconds
        setTimeout(() => {
          if (!this.ready) {
            readyDispose()
            errorDispose()
            reject(new Error('Worker initialization timed out'))
          }
        }, 30000)
      } catch (err) {
        reject(err instanceof Error ? err : new Error(String(err)))
      }
    })
  }

  /**
   * Send a video frame to the worker for processing.
   * Uses createImageBitmap for efficient transfer (zero-copy where supported).
   */
  async sendFrame(video: HTMLVideoElement, timestamp: number): Promise<void> {
    if (!this.worker || !this.ready) return

    try {
      // Create ImageBitmap from video — this is the most efficient transfer
      const bitmap = await createImageBitmap(video)

      this.send(
        { type: 'process_frame', payload: { imageData: bitmap, timestamp } },
        [bitmap] // Transfer ownership — zero copy
      )
    } catch {
      // Frame capture failed (video not ready, etc.) — skip silently
    }
  }

  /**
   * Alternative: send frame using OffscreenCanvas (for browsers without ImageBitmap transfer).
   * Slightly slower but more compatible.
   */
  sendFrameCanvas(video: HTMLVideoElement, timestamp: number): void {
    if (!this.worker || !this.ready) return

    if (!this.canvas) {
      this.canvas = new OffscreenCanvas(video.videoWidth || 640, video.videoHeight || 480)
      this.ctx = this.canvas.getContext('2d')
    }

    if (!this.ctx) return

    this.ctx.drawImage(video, 0, 0)
    const bitmap = this.canvas.transferToImageBitmap()

    this.send(
      { type: 'process_frame', payload: { imageData: bitmap, timestamp } },
      [bitmap]
    )
  }

  stop(): void {
    if (this.worker) {
      this.send({ type: 'destroy' })
    }
    this.ready = false
  }

  destroy(): void {
    this.stop()
    if (this.worker) {
      this.worker.terminate()
      this.worker = null
    }
    this.canvas = null
    this.ctx = null
    this.removeAllListeners()
  }

  // ─────────────────────────────────────────────
  //  Private
  // ─────────────────────────────────────────────

  private handleMessage(msg: WorkerOutMessage): void {
    switch (msg.type) {
      case 'ready':
        this.emit('ready', undefined as never)
        break
      case 'result':
        this.emit('result', msg.payload)
        break
      case 'error':
        this.emit('error', new Error(msg.payload.message))
        break
    }
  }

  private send(msg: WorkerInMessage, transfer?: Transferable[]): void {
    if (!this.worker) return
    if (transfer) {
      this.worker.postMessage(msg, transfer)
    } else {
      this.worker.postMessage(msg)
    }
  }
}
