/**
 * useCalibration — React hook for managing the 9-point calibration flow.
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
  /** Load calibration from localStorage */
  loadStored: () => CalibrationMatrix | null
}

export function useCalibration(): UseCalibrationReturn {
  const calRef = useRef<CalibrationSystem>(new CalibrationSystem())
  const [state, setState] = useState<CalibrationState>(calRef.current.state)
  const [hasStored, setHasStored] = useState(false)

  useEffect(() => {
    const cal = calRef.current
    const dispose = cal.on('stateChange', (newState) => {
      setState(newState)
    })

    // Check for stored calibration on mount
    const stored = cal.loadFromStorage()
    setHasStored(stored !== null)

    return () => {
      dispose()
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

  const loadStored = useCallback((): CalibrationMatrix | null => {
    return calRef.current.loadFromStorage()
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
