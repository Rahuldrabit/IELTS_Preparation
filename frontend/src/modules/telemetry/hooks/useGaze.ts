/**
 * useGaze — subscribes to real-time gaze point updates from the tracker.
 *
 * Provides the current gaze position for UI overlays or component logic.
 * Throttled state updates to avoid excessive re-renders.
 */
'use client'

import { useEffect, useRef, useState } from 'react'
import type { GazePoint } from '../types'
import { ReadingTracker } from '../trackers/ReadingTracker'
import { ListeningTracker } from '../trackers/ListeningTracker'

export interface UseGazeOptions {
  /** The active tracker instance */
  tracker: ReadingTracker | ListeningTracker | null
  /** Throttle state updates (ms, default: 33 = ~30fps) */
  throttleMs?: number
  /** Only update state if this is true (prevents updates when not needed) */
  enabled?: boolean
}

export interface UseGazeReturn {
  /** Current gaze point (null if no tracking) */
  point: GazePoint | null
  /** Whether gaze data is actively flowing */
  active: boolean
}

export function useGaze(options: UseGazeOptions): UseGazeReturn {
  const { tracker, throttleMs = 33, enabled = true } = options
  const [point, setPoint] = useState<GazePoint | null>(null)
  const [active, setActive] = useState(false)
  const lastUpdateRef = useRef(0)

  useEffect(() => {
    if (!tracker || !enabled) {
      setActive(false)
      return
    }

    const dispose = (tracker as any).on('gazePoint', (gazePoint: GazePoint) => {
      const now = performance.now()
      if (now - lastUpdateRef.current >= throttleMs) {
        lastUpdateRef.current = now
        setPoint(gazePoint)
        if (!active) setActive(true)
      }
    })

    return () => {
      dispose()
      setActive(false)
    }
  }, [tracker, throttleMs, enabled, active])

  return { point, active }
}
