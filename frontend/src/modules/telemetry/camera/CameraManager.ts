/**
 * CameraManager — webcam access, permission flow, and frame-loop lifecycle.
 *
 * Responsibilities:
 *   - Request camera with optimal constraints for eye tracking
 *   - Manage HTMLVideoElement lifecycle (offscreen, muted)
 *   - Emit typed events: stateChange, frame
 *   - Graceful permission-denied handling
 *   - rAF-based frame loop (delegates to consumer for processing)
 *
 * Usage:
 *   const cam = new CameraManager({ width: 640, height: 480 })
 *   cam.on('frame', ({ video, timestamp }) => { ... })
 *   await cam.start()
 *   cam.stop()
 */

import { Emitter } from '../core/Emitter'
import type { CameraConfig, CameraEventMap, CameraState, ILifecycle } from '../types'

const DEFAULT_CONFIG: CameraConfig = {
  width: 640,
  height: 480,
  frameRate: 30,
  facingMode: 'user',
}

export class CameraManager extends Emitter<CameraEventMap> implements ILifecycle {
  private config: CameraConfig
  private stream: MediaStream | null = null
  private video: HTMLVideoElement | null = null
  private rafId: number | null = null
  private _state: CameraState = { status: 'idle', stream: null, error: null }

  constructor(config: Partial<CameraConfig> = {}) {
    super()
    this.config = { ...DEFAULT_CONFIG, ...config }
  }

  // ─────────────────────────────────────────────
  //  Public API
  // ─────────────────────────────────────────────

  get state(): CameraState {
    return this._state
  }

  get videoElement(): HTMLVideoElement | null {
    return this.video
  }

  static isSupported(): boolean {
    return typeof navigator !== 'undefined' &&
      !!navigator.mediaDevices &&
      !!navigator.mediaDevices.getUserMedia
  }

  static async checkPermission(): Promise<PermissionState> {
    try {
      const result = await navigator.permissions.query({ name: 'camera' as PermissionName })
      return result.state
    } catch {
      return 'prompt'
    }
  }

  async start(existingStream?: MediaStream): Promise<void> {
    if (!CameraManager.isSupported()) {
      this.setState({ status: 'error', stream: null, error: 'Camera API not supported in this browser.' })
      return
    }

    if (this._state.status === 'active') return

    this.setState({ status: 'requesting', stream: null, error: null })

    try {
      if (existingStream) {
        // Use provided stream (e.g., from permission check)
        this.stream = existingStream
      } else {
        // Create new stream
        this.stream = await navigator.mediaDevices.getUserMedia({
          video: {
            width: { ideal: this.config.width },
            height: { ideal: this.config.height },
            frameRate: { ideal: this.config.frameRate },
            facingMode: this.config.facingMode,
          },
          audio: false,
        })
      }

      this.video = this.createVideo()
      await this.video.play()

      this.setState({ status: 'active', stream: this.stream, error: null })
      this.startFrameLoop()
    } catch (err) {
      const error = err instanceof Error ? err : new Error(String(err))
      const denied = error.name === 'NotAllowedError' || error.name === 'PermissionDeniedError'

      this.setState({
        status: denied ? 'denied' : 'error',
        stream: null,
        error: denied
          ? 'Camera access denied. Enable camera in browser settings.'
          : `Camera error: ${error.message}`,
      })
    }
  }

  stop(): void {
    this.stopFrameLoop()
    this.releaseStream()
    this.removeVideo()
    this.setState({ status: 'idle', stream: null, error: null })
  }

  destroy(): void {
    this.stop()
    this.removeAllListeners()
  }

  /** Update config (takes effect on next start) */
  configure(config: Partial<CameraConfig>): void {
    this.config = { ...this.config, ...config }
  }

  // ─────────────────────────────────────────────
  //  Private
  // ─────────────────────────────────────────────

  private createVideo(): HTMLVideoElement {
    const el = document.createElement('video')
    el.setAttribute('playsinline', '')
    el.setAttribute('autoplay', '')
    el.muted = true
    el.width = this.config.width
    el.height = this.config.height
    el.srcObject = this.stream

    // Offscreen — invisible to user
    Object.assign(el.style, {
      position: 'fixed',
      top: '-9999px',
      left: '-9999px',
      width: '1px',
      height: '1px',
      opacity: '0',
      pointerEvents: 'none',
    })
    document.body.appendChild(el)
    return el
  }

  private removeVideo(): void {
    if (this.video) {
      this.video.srcObject = null
      this.video.remove()
      this.video = null
    }
  }

  private releaseStream(): void {
    if (this.stream) {
      this.stream.getTracks().forEach((t) => t.stop())
      this.stream = null
    }
  }

  private startFrameLoop(): void {
    const tick = () => {
      if (this.video && this._state.status === 'active') {
        this.emit('frame', { video: this.video, timestamp: performance.now() })
      }
      this.rafId = requestAnimationFrame(tick)
    }
    this.rafId = requestAnimationFrame(tick)
  }

  private stopFrameLoop(): void {
    if (this.rafId !== null) {
      cancelAnimationFrame(this.rafId)
      this.rafId = null
    }
  }

  private setState(state: CameraState): void {
    this._state = state
    this.emit('stateChange', state)
  }
}
