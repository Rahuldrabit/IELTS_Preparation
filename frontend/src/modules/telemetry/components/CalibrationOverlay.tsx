/**
 * CalibrationOverlay — full-screen 9-point calibration UI.
 *
 * Renders calibration target dots and guides the user through the sequence.
 * Uses Framer Motion for smooth animations between points.
 *
 * During 'collecting' phase, it receives iris data via onIrisFrame and feeds
 * it to the calibration system via onAddSample.
 */
'use client'

import { useEffect, useCallback, useState } from 'react'
import { motion, AnimatePresence } from 'framer-motion'
import type { CalibrationState, Point2D } from '../types'

export interface CalibrationOverlayProps {
  state: CalibrationState
  currentTarget: Point2D | null
  targets: Point2D[]
  /** Called when user confirms they're looking at the target */
  onConfirmLooking: () => void
  /** Called to feed an iris sample during collection */
  onAddSample: (irisX: number, irisY: number) => void
  onCancel: () => void
  /** Current iris position from FaceMesh (for visual feedback) */
  irisPosition?: Point2D | null
  /** Whether camera/FaceMesh is producing data */
  cameraReady?: boolean
}

export function CalibrationOverlay({
  state,
  currentTarget,
  targets,
  onConfirmLooking,
  onAddSample,
  onCancel,
  irisPosition,
  cameraReady = false,
}: CalibrationOverlayProps) {
  const [waitingForCamera, setWaitingForCamera] = useState(!cameraReady)

  // Update waiting state when camera becomes ready
  useEffect(() => {
    if (cameraReady) setWaitingForCamera(false)
  }, [cameraReady])

  // Auto-confirm after 2 seconds when calibrating (user stares at dot)
  // Only if camera is ready
  useEffect(() => {
    if (state.status === 'calibrating' && currentTarget && cameraReady) {
      const timer = setTimeout(onConfirmLooking, 2000)
      return () => clearTimeout(timer)
    }
  }, [state.status, currentTarget, onConfirmLooking, cameraReady])

  // During collection: feed iris samples from FaceMesh
  useEffect(() => {
    if (state.status === 'collecting' && irisPosition) {
      onAddSample(irisPosition.x, irisPosition.y)
    }
  }, [state.status, irisPosition, onAddSample])

  const handleKeyDown = useCallback(
    (e: KeyboardEvent) => {
      if (e.key === 'Escape') onCancel()
      if (e.key === ' ' || e.key === 'Enter') onConfirmLooking()
    },
    [onCancel, onConfirmLooking],
  )

  useEffect(() => {
    window.addEventListener('keydown', handleKeyDown)
    return () => window.removeEventListener('keydown', handleKeyDown)
  }, [handleKeyDown])

  if (state.status === 'idle' || state.status === 'complete') return null

  const progress = state.currentPointIndex / state.totalPoints

  return (
    <motion.div
      className="fixed inset-0 z-[9999] bg-black/80 backdrop-blur-sm flex items-center justify-center font-sans"
      initial={{ opacity: 0 }}
      animate={{ opacity: 1 }}
      exit={{ opacity: 0 }}
    >
      {/* Instructions Panel */}
      <div className="absolute top-12 left-1/2 -translate-x-1/2 text-center text-white bg-white/10 px-8 py-4 rounded-2xl border border-white/20 shadow-2xl backdrop-blur-md">
        <h2 className="text-xl font-semibold tracking-wide mb-1">Eye Tracking Calibration</h2>
        <p className="text-base text-white/90 font-medium">
          {waitingForCamera && 'Warming up camera...'}
          {!waitingForCamera && state.status === 'calibrating' && 'Look directly at the pulsating blue dot.'}
          {!waitingForCamera && state.status === 'collecting' && 'Hold your gaze steady...'}
          {state.status === 'failed' && 'Calibration failed. Please try again.'}
        </p>
        
        {/* Camera status indicator */}
        <div className="mt-3 flex items-center justify-center gap-2 bg-black/20 w-max mx-auto px-3 py-1 rounded-full">
          <span className={`inline-flex h-2 w-2 rounded-full ${cameraReady ? 'bg-green-400' : 'bg-yellow-400 animate-pulse'}`} />
          <span className="text-xs font-medium text-white/70">
            {cameraReady ? 'Camera Active' : 'Waiting for Camera...'}
          </span>
        </div>

        {/* Progress bar */}
        <div className="mt-4 w-56 mx-auto">
          <div className="flex justify-between text-[10px] uppercase font-bold tracking-wider text-white/50 mb-1.5">
            <span>Progress</span>
            <span>{Math.round(progress * 100)}%</span>
          </div>
          <div className="h-1.5 bg-black/30 rounded-full overflow-hidden shadow-inner">
            <motion.div
              className="h-full bg-gradient-to-r from-blue-500 to-cyan-400 rounded-full"
              initial={{ width: 0 }}
              animate={{ width: `${progress * 100}%` }}
              transition={{ duration: 0.4, ease: "easeOut" }}
            />
          </div>
        </div>
      </div>

      {/* Render all target positions as dim dots */}
      {targets.map((point, i) => (
        <div
          key={i}
          className="absolute w-2 h-2 rounded-full bg-white/10"
          style={{ left: point.x - 4, top: point.y - 4 }}
        />
      ))}

      {/* Active calibration target */}
      <AnimatePresence mode="wait">
        {currentTarget && (
          <motion.div
            key={state.currentPointIndex}
            className="absolute"
            style={{ left: currentTarget.x, top: currentTarget.y }}
            initial={{ scale: 0, opacity: 0 }}
            animate={{ scale: 1, opacity: 1 }}
            exit={{ scale: 0, opacity: 0 }}
            transition={{ type: 'spring', stiffness: 400, damping: 25 }}
          >
            {/* Outer pulse ring */}
            <motion.div
              className="absolute -translate-x-1/2 -translate-y-1/2 w-16 h-16 rounded-full border border-blue-400/40"
              animate={{ scale: [1, 1.8, 1], opacity: [0.8, 0, 0.8] }}
              transition={{ duration: 2.5, repeat: Infinity, ease: "easeInOut" }}
            />
            {/* Inner dot */}
            <div className="absolute -translate-x-1/2 -translate-y-1/2 w-5 h-5 rounded-full bg-gradient-to-tr from-blue-600 to-cyan-400 shadow-[0_0_15px_rgba(56,189,248,0.6)]" />
            
            {/* Collection progress ring */}
            {state.status === 'collecting' && (
              <svg
                className="absolute -translate-x-1/2 -translate-y-1/2 w-10 h-10 -rotate-90"
                viewBox="0 0 40 40"
              >
                <circle
                  cx="20"
                  cy="20"
                  r="18"
                  fill="none"
                  stroke="rgba(56, 189, 248, 0.2)"
                  strokeWidth="3"
                />
                <motion.circle
                  cx="20"
                  cy="20"
                  r="18"
                  fill="none"
                  stroke="#38bdf8"
                  strokeWidth="3"
                  strokeLinecap="round"
                  strokeDasharray={113} // 2 * PI * 18 ≈ 113
                  initial={{ strokeDashoffset: 113 }}
                  animate={{
                    strokeDashoffset: 113 - (state.collectedSamples / state.samplesPerPoint) * 113,
                  }}
                  transition={{ duration: 0.1 }}
                />
              </svg>
            )}
          </motion.div>
        )}
      </AnimatePresence>

      {/* Iris indicator (debug) */}
      {irisPosition && cameraReady && (
        <div
          className="absolute w-3 h-3 rounded-full bg-rose-500/50 border border-rose-400/80 pointer-events-none transition-all duration-75 shadow-[0_0_10px_rgba(244,63,94,0.5)] z-50"
          style={{ left: irisPosition.x - 6, top: irisPosition.y - 6 }}
        />
      )}

      {/* Cancel button */}
      <button
        onClick={onCancel}
        className="absolute bottom-10 left-1/2 -translate-x-1/2 px-6 py-2.5 bg-white/5 hover:bg-white/10 text-sm font-medium text-white/80 hover:text-white border border-white/10 rounded-full transition-all flex items-center gap-2 shadow-lg backdrop-blur-md"
      >
        <span className="px-1.5 py-0.5 bg-white/10 rounded text-[10px] tracking-widest">ESC</span>
        Cancel Calibration
      </button>
    </motion.div>
  )
}
