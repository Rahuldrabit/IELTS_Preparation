/**
 * useTelemetry — master lifecycle hook for the Cognitive Telemetry Engine.
 *
 * Orchestrates: ReadingTracker/ListeningTracker + Analytics + Storage + Upload.
 * Provides a simple start/stop/config API for page components.
 *
 * Usage:
 *   const { start, stop, status, config } = useTelemetry({ skill: 'reading', sessionId })
 */
'use client'

import { useCallback, useEffect, useRef, useState } from 'react'
import type { TelemetryConfig, TelemetrySkill, ReadingAnalyticsSummary } from '../types'
import { DEFAULT_CONFIG } from '../types'
import { ReadingTracker } from '../trackers/ReadingTracker'
import { ListeningTracker } from '../trackers/ListeningTracker'
import { ReadingAnalytics } from '../analytics/ReadingAnalytics'
import { IndexedDBStore } from '../storage/IndexedDBStore'
import { TelemetryUploader } from '../storage/TelemetryUploader'

export type TelemetryStatus = 'idle' | 'starting' | 'active' | 'stopping' | 'error'

export interface UseTelemetryOptions {
  skill: TelemetrySkill
  sessionId: string
  backendSessionId?: number
  config?: Partial<TelemetryConfig>
  /** Auto-start on mount (default: false) */
  autoStart?: boolean
  /** Total words in passage (for skip rate) */
  totalWords?: number
}

export interface UseTelemetryReturn {
  status: TelemetryStatus
  error: string | null
  start: (existingStream?: MediaStream, onProgress?: (progress: any) => void) => Promise<void>
  stop: () => void
  config: TelemetryConfig
  /** Access underlying tracker for advanced usage */
  tracker: ReadingTracker | ListeningTracker | null
}

export function useTelemetry(options: UseTelemetryOptions): UseTelemetryReturn {
  const { skill, sessionId, config: configOverride, autoStart = false, totalWords } = options
  const config = { ...DEFAULT_CONFIG, ...configOverride }

  const [status, setStatus] = useState<TelemetryStatus>('idle')
  const [error, setError] = useState<string | null>(null)

  const trackerRef = useRef<ReadingTracker | ListeningTracker | null>(null)
  const analyticsRef = useRef<ReadingAnalytics | null>(null)
  const storeRef = useRef<IndexedDBStore | null>(null)
  const uploaderRef = useRef<TelemetryUploader | null>(null)
  const disposersRef = useRef<(() => void)[]>([])

  const start = useCallback(async (existingStream?: MediaStream, onProgress?: (progress: any) => void) => {
    if (status === 'active' || status === 'starting') return
    setStatus('starting')
    setError(null)

    try {
      // 1. Storage
      const store = new IndexedDBStore()
      await store.open()
      storeRef.current = store

      // 2. Tracker (reading or listening)
      const tracker = skill === 'reading'
        ? new ReadingTracker(sessionId, config, existingStream)
        : new ListeningTracker(sessionId, config, existingStream)
      trackerRef.current = tracker

      if (onProgress && 'faceMesh' in tracker) {
        const d0 = tracker.faceMesh.on('progress', onProgress)
        disposersRef.current.push(d0)
      }

      // 3. Analytics (reading only for now)
      if (skill === 'reading') {
        const analytics = new ReadingAnalytics(sessionId, { intervalMs: config.uploadIntervalMs })
        if (totalWords) analytics.setTotalWords(totalWords)
        analyticsRef.current = analytics

        // Wire tracker events → analytics
        const d1 = (tracker as ReadingTracker).on('fixation', (f) => analytics.addFixation(f))
        const d2 = (tracker as ReadingTracker).on('regression', (r) => analytics.addRegression(r))
        disposersRef.current.push(d1, d2)
      }

      // 4. Uploader
      const uploader = new TelemetryUploader(store, sessionId, {
        intervalMs: config.uploadIntervalMs,
        endpoint: '/api/telemetry/upload',
      })
      uploaderRef.current = uploader

      // Wire events → store (buffer everything locally first)
      const d3 = (tracker as any).on('event', async (event: any) => {
        await store.put(event)
      })
      disposersRef.current.push(d3)

      // Wire analytics summaries → uploader
      if (analyticsRef.current) {
        const d4 = analyticsRef.current.on('summary', (summary: ReadingAnalyticsSummary) => {
          uploader.setSummary(summary)
        })
        disposersRef.current.push(d4)
        analyticsRef.current.start()
      }

      // 5. Start everything
      await tracker.start()
      uploader.start()

      setStatus('active')
    } catch (err) {
      const msg = err instanceof Error ? err.message : String(err)
      setError(msg)
      setStatus('error')
    }
  }, [skill, sessionId, config, status, totalWords])

  const stop = useCallback(() => {
    if (status !== 'active') return
    setStatus('stopping')

    // Flush analytics before stopping
    analyticsRef.current?.stop()
    uploaderRef.current?.flush()

    // Stop tracker
    trackerRef.current?.stop()
    uploaderRef.current?.stop()

    // Cleanup subscriptions
    disposersRef.current.forEach((d) => d())
    disposersRef.current = []

    // Close storage
    storeRef.current?.close()

    setStatus('idle')
  }, [status])

  // Auto-start
  useEffect(() => {
    if (autoStart) {
      start()
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [autoStart])

  // Cleanup on unmount
  useEffect(() => {
    return () => {
      trackerRef.current?.destroy()
      analyticsRef.current?.destroy()
      uploaderRef.current?.destroy()
      storeRef.current?.close()
      disposersRef.current.forEach((d) => d())
    }
  }, [])

  return {
    status,
    error,
    start,
    stop,
    config,
    tracker: trackerRef.current,
  }
}
