/**
 * useCalibration — React hook for managing the 9-point calibration flow.
 * Now syncs user calibration with the backend API.
 */
 *
 * Exposes calibration state, current target, and control functions
 * for the CalibrationOverlay component.
 */
'use client'

import { useCallback, useEffect, useRef, useState } from 'react'
import type { CalibrationMatrix, CalibrationState, Point2D } from '../types'
import { CalibrationSystem } from '../camera/Calibration'

export interface UseCalibrationReturn {
  state: CalibrationState
  currentTarget: Point2D | null
  targets: Point2D[]
  matrix: CalibrationMatrix | null
  /** Begin calibration sequence */
  startCalibration: () => void
  /** Signal that user is looking at current target (begin sample collection) */
  confirmLooking: () => void
  /** Feed iris position from FaceMesh */
  addSample: (irisX: number, irisY: number) => void
  /** Cancel calibration */
  cancel: () => void
  /** Check if stored calibration exists */
  hasStored: boolean
  /** Load calibration from backend/localStorage */
  loadStored: () => Promise<CalibrationMatrix | null>
}

const API_BASE = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'

export function useCalibration(): UseCalibrationReturn {
  const calRef = useRef<CalibrationSystem>(new CalibrationSystem())
  const [state, setState] = useState<CalibrationState>(calRef.current.state)
  const [hasStored, setHasStored] = useState(false)

  useEffect(() => {
    const cal = calRef.current
    const dispose1 = cal.on('stateChange', (newState) => {
      setState(newState)
    })
    
    // Save to backend when complete
    const dispose2 = cal.on('complete', (matrix) => {
      fetch(`${API_BASE}/api/v1/telemetry/calibration`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          screen_width: window.innerWidth,
          screen_height: window.innerHeight,
          device_pixel_ratio: window.devicePixelRatio,
          calibration_matrix: matrix,
          accuracy_score: Math.max(0, 1 - matrix.mse / 100)
        })
      }).catch(console.error)
    })

    return () => {
      dispose1()
      dispose2()
      cal.destroy()
    }
  }, [])

  const startCalibration = useCallback(() => {
    calRef.current.start()
  }, [])

  const confirmLooking = useCallback(() => {
    calRef.current.beginCollection()
  }, [])

  const addSample = useCallback((irisX: number, irisY: number) => {
    calRef.current.addSample(irisX, irisY)
  }, [])

  const cancel = useCallback(() => {
    calRef.current.stop()
  }, [])

  const loadStored = useCallback(async (): Promise<CalibrationMatrix | null> => {
    try {
      const res = await fetch(`${API_BASE}/api/v1/telemetry/calibration?screen_width=${window.innerWidth}&screen_height=${window.innerHeight}`)
      if (res.ok) {
        const data = await res.json()
        const matrix = data.calibration_matrix as CalibrationMatrix
        calRef.current.setCalibrationMatrix(matrix)
        setHasStored(true)
        return matrix
      }
    } catch (e) {
      console.warn("Failed to load calibration from backend", e)
    }
    
    // Fallback to local storage if backend fails
    const matrix = calRef.current.loadFromStorage()
    setHasStored(matrix !== null)
    return matrix
  }, [])

  return {
    state,
    currentTarget: calRef.current.getCurrentTarget(),
    targets: calRef.current.getTargetPoints(),
    matrix: state.matrix,
    startCalibration,
    confirmLooking,
    addSample,
    cancel,
    hasStored,
    loadStored,
  }
}
