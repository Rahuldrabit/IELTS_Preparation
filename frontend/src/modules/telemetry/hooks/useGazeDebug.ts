/**
 * useGazeDebug — accumulates gaze trail + fixation data for debug overlay.
 *
 * Keeps a rolling buffer of recent gaze points for trail visualization
 * and a list of recent fixations for heatmap rendering.
 */
'use client'

import { useEffect, useRef, useState } from 'react'
import type { Fixation, GazePoint } from '../types'
import { ReadingTracker } from '../trackers/ReadingTracker'

export interface UseGazeDebugOptions {
  tracker: ReadingTracker | null
  /** Max trail points to keep */
  trailLength?: number
  /** Max fixations to keep */
  maxFixations?: number
  enabled?: boolean
}

export interface UseGazeDebugReturn {
  /** Rolling gaze trail (newest last) */
  trail: GazePoint[]
  /** Recent fixations for heatmap */
  fixations: Fixation[]
  /** Current regression count */
  regressionCount: number
  /** Clear all debug data */
  clear: () => void
}

export function useGazeDebug(options: UseGazeDebugOptions): UseGazeDebugReturn {
  const { tracker, trailLength = 60, maxFixations = 100, enabled = true } = options
  const [trail, setTrail] = useState<GazePoint[]>([])
  const [fixations, setFixations] = useState<Fixation[]>([])
  const [regressionCount, setRegressionCount] = useState(0)
  const trailRef = useRef<GazePoint[]>([])
  const fixationsRef = useRef<Fixation[]>([])

  useEffect(() => {
    if (!tracker || !enabled) return

    const d1 = tracker.on('gazePoint', (point: GazePoint) => {
      trailRef.current.push(point)
      if (trailRef.current.length > trailLength) {
        trailRef.current.shift()
      }
      // Update state at ~10fps to avoid thrashing
      if (trailRef.current.length % 3 === 0) {
        setTrail([...trailRef.current])
      }
    })

    const d2 = tracker.on('fixation', (fixation: Fixation) => {
      fixationsRef.current.push(fixation)
      if (fixationsRef.current.length > maxFixations) {
        fixationsRef.current.shift()
      }
      setFixations([...fixationsRef.current])
    })

    const d3 = tracker.on('regression', () => {
      setRegressionCount((c) => c + 1)
    })

    return () => {
      d1()
      d2()
      d3()
    }
  }, [tracker, enabled, trailLength, maxFixations])

  const clear = () => {
    trailRef.current = []
    fixationsRef.current = []
    setTrail([])
    setFixations([])
    setRegressionCount(0)
  }

  return { trail, fixations, regressionCount, clear }
}
