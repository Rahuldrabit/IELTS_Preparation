/**
 * TelemetryUploader — batched upload with retry and exponential backoff.
 *
 * Responsibilities:
 *   - Periodically drain IndexedDBStore and POST to backend
 *   - Retry failed uploads with exponential backoff
 *   - Respect max batch size to avoid oversized requests
 *   - Pause uploads when offline (navigator.onLine)
 *   - Flush on page unload (sendBeacon fallback)
 *
 * Design:
 *   - Composition: depends on IndexedDBStore (injected)
 *   - Configurable endpoint, batch size, retry policy
 *   - Emits events for monitoring (success, failure, retrying)
 */

import { Emitter } from '../core/Emitter'
import type { ReadingAnalyticsSummary, TelemetryEvent, TelemetryUploadPayload } from '../types'
import { IndexedDBStore } from './IndexedDBStore'

export interface TelemetryUploaderConfig {
  /** Backend endpoint URL */
  endpoint: string
  /** Upload interval (ms) */
  intervalMs: number
  /** Max events per upload batch */
  batchSize: number
  /** Max retry attempts before dropping */
  maxRetries: number
  /** Base delay for exponential backoff (ms) */
  retryBaseMs: number
  /** Use sendBeacon on page unload */
  useSendBeacon: boolean
}

const DEFAULT_CONFIG: TelemetryUploaderConfig = {
  endpoint: '/api/telemetry/upload',
  intervalMs: 2000,
  batchSize: 100,
  maxRetries: 3,
  retryBaseMs: 1000,
  useSendBeacon: true,
}

export interface UploaderEventMap {
  uploadSuccess: { count: number; durationMs: number }
  uploadFail: { error: string; retryCount: number }
  offline: void
  online: void
}

export class TelemetryUploader extends Emitter<UploaderEventMap> {
  private config: TelemetryUploaderConfig
  private store: IndexedDBStore
  private sessionId: string
  private intervalId: ReturnType<typeof setInterval> | null = null
  private retryCount = 0
  private uploading = false
  private onlineHandler: (() => void) | null = null
  private offlineHandler: (() => void) | null = null
  private unloadHandler: (() => void) | null = null

  // Holds the latest summary for inclusion in uploads
  private latestSummary: ReadingAnalyticsSummary | null = null

  constructor(
    store: IndexedDBStore,
    sessionId: string,
    config: Partial<TelemetryUploaderConfig> = {},
  ) {
    super()
    this.store = store
    this.sessionId = sessionId
    this.config = { ...DEFAULT_CONFIG, ...config }
  }

  // ─────────────────────────────────────────────
  //  Public API
  // ─────────────────────────────────────────────

  /** Set latest analytics summary to include with next upload */
  setSummary(summary: ReadingAnalyticsSummary): void {
    this.latestSummary = summary
  }

  /** Start periodic upload cycle */
  start(): void {
    this.intervalId = setInterval(() => this.tick(), this.config.intervalMs)
    this.registerNetworkListeners()
  }

  /** Stop periodic uploads (does not flush) */
  stop(): void {
    if (this.intervalId) {
      clearInterval(this.intervalId)
      this.intervalId = null
    }
    this.unregisterNetworkListeners()
  }

  /** Force flush all buffered events now */
  async flush(): Promise<void> {
    await this.tick()
  }

  destroy(): void {
    this.stop()
    this.removeAllListeners()
  }

  // ─────────────────────────────────────────────
  //  Private — Upload Cycle
  // ─────────────────────────────────────────────

  private async tick(): Promise<void> {
    if (this.uploading) return
    if (!navigator.onLine) return

    const events = await this.store.drain(this.config.batchSize)
    if (events.length === 0) return

    this.uploading = true

    try {
      const payload: TelemetryUploadPayload = {
        sessionId: this.sessionId,
        timestamp: Date.now(),
        summary: this.latestSummary as ReadingAnalyticsSummary,
        events,
      }

      const start = performance.now()
      await this.upload(payload)
      const durationMs = performance.now() - start

      this.retryCount = 0
      this.emit('uploadSuccess', { count: events.length, durationMs })
    } catch (err) {
      // Put events back in store for retry
      await this.store.putBatch(events)

      this.retryCount++
      const errMsg = err instanceof Error ? err.message : String(err)
      this.emit('uploadFail', { error: errMsg, retryCount: this.retryCount })

      if (this.retryCount <= this.config.maxRetries) {
        // Schedule retry with exponential backoff
        const delay = this.config.retryBaseMs * 2 ** (this.retryCount - 1)
        setTimeout(() => this.tick(), delay)
      }
    } finally {
      this.uploading = false
    }
  }

  private async upload(payload: TelemetryUploadPayload): Promise<void> {
    const response = await fetch(this.config.endpoint, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(payload),
    })

    if (!response.ok) {
      throw new Error(`Upload failed: HTTP ${response.status}`)
    }
  }

  // ─────────────────────────────────────────────
  //  Private — Network & Unload
  // ─────────────────────────────────────────────

  private registerNetworkListeners(): void {
    this.onlineHandler = () => {
      this.emit('online', undefined as never)
      this.tick() // Try uploading when back online
    }
    this.offlineHandler = () => {
      this.emit('offline', undefined as never)
    }
    window.addEventListener('online', this.onlineHandler)
    window.addEventListener('offline', this.offlineHandler)

    if (this.config.useSendBeacon) {
      this.unloadHandler = () => this.sendBeaconFlush()
      window.addEventListener('visibilitychange', this.unloadHandler)
    }
  }

  private unregisterNetworkListeners(): void {
    if (this.onlineHandler) window.removeEventListener('online', this.onlineHandler)
    if (this.offlineHandler) window.removeEventListener('offline', this.offlineHandler)
    if (this.unloadHandler) window.removeEventListener('visibilitychange', this.unloadHandler)
    this.onlineHandler = null
    this.offlineHandler = null
    this.unloadHandler = null
  }

  /**
   * Last-resort flush using navigator.sendBeacon when page is being unloaded.
   * sendBeacon is fire-and-forget but survives page close.
   */
  private sendBeaconFlush(): void {
    if (document.visibilityState !== 'hidden') return
    if (!navigator.sendBeacon) return

    // Synchronous: can't use async drain here
    // Use whatever summary we have
    if (this.latestSummary) {
      const payload: TelemetryUploadPayload = {
        sessionId: this.sessionId,
        timestamp: Date.now(),
        summary: this.latestSummary,
        events: [], // Can't drain IndexedDB synchronously
      }
      navigator.sendBeacon(this.config.endpoint, JSON.stringify(payload))
    }
  }
}
