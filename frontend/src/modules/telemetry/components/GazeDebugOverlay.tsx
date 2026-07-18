/**
 * GazeDebugOverlay — development-only visualization of gaze tracking.
 *
 * Shows:
 *   - Current gaze position (dot)
 *   - Gaze trail (fading line)
 *   - Fixation markers (circles scaled by duration)
 *   - Regression count badge
 *   - FPS counter
 */
'use client'

import { useRef, useEffect } from 'react'
import type { Fixation, GazePoint } from '../types'

export interface GazeDebugOverlayProps {
  trail: GazePoint[]
  fixations: Fixation[]
  regressionCount: number
  visible: boolean
}

export function GazeDebugOverlay({ trail, fixations, regressionCount, visible }: GazeDebugOverlayProps) {
  const canvasRef = useRef<HTMLCanvasElement>(null)
  const fpsRef = useRef({ frames: 0, lastTime: performance.now(), fps: 0 })

  useEffect(() => {
    if (!visible || !canvasRef.current) return

    const canvas = canvasRef.current
    const ctx = canvas.getContext('2d')
    if (!ctx) return

    // Match canvas to window size
    canvas.width = window.innerWidth
    canvas.height = window.innerHeight

    // Clear
    ctx.clearRect(0, 0, canvas.width, canvas.height)

    // Draw trail (fading line)
    if (trail.length > 1) {
      ctx.beginPath()
      ctx.moveTo(trail[0].x, trail[0].y)

      for (let i = 1; i < trail.length; i++) {
        const alpha = i / trail.length
        ctx.strokeStyle = `rgba(59, 130, 246, ${alpha * 0.6})`
        ctx.lineWidth = 1 + alpha
        ctx.lineTo(trail[i].x, trail[i].y)
        ctx.stroke()
        ctx.beginPath()
        ctx.moveTo(trail[i].x, trail[i].y)
      }
    }

    // Draw fixation circles (size proportional to duration)
    for (const fix of fixations) {
      const radius = Math.min(30, Math.max(5, fix.duration / 50))
      const alpha = Math.min(0.6, fix.duration / 1000)

      ctx.beginPath()
      ctx.arc(fix.x, fix.y, radius, 0, Math.PI * 2)
      ctx.fillStyle = `rgba(234, 179, 8, ${alpha})`
      ctx.fill()
      ctx.strokeStyle = `rgba(234, 179, 8, ${alpha + 0.2})`
      ctx.lineWidth = 1
      ctx.stroke()
    }

    // Draw current gaze point (last trail point)
    if (trail.length > 0) {
      const current = trail[trail.length - 1]
      ctx.beginPath()
      ctx.arc(current.x, current.y, 8, 0, Math.PI * 2)
      ctx.fillStyle = 'rgba(239, 68, 68, 0.8)'
      ctx.fill()
      ctx.strokeStyle = 'rgba(239, 68, 68, 1)'
      ctx.lineWidth = 2
      ctx.stroke()
    }

    // FPS counter
    fpsRef.current.frames++
    const now = performance.now()
    if (now - fpsRef.current.lastTime >= 1000) {
      fpsRef.current.fps = fpsRef.current.frames
      fpsRef.current.frames = 0
      fpsRef.current.lastTime = now
    }
  }, [trail, fixations, visible])

  if (!visible) return null

  return (
    <>
      <canvas
        ref={canvasRef}
        className="fixed inset-0 z-[9998] pointer-events-none"
        aria-hidden="true"
      />
      {/* Stats badge */}
      <div className="fixed top-4 right-4 z-[9998] pointer-events-none bg-black/70 text-white text-xs font-mono px-3 py-2 rounded-lg space-y-0.5">
        <div>Gaze: {trail.length > 0 ? `${trail[trail.length - 1].x.toFixed(0)}, ${trail[trail.length - 1].y.toFixed(0)}` : '--'}</div>
        <div>Fixations: {fixations.length}</div>
        <div>Regressions: {regressionCount}</div>
        <div>FPS: {fpsRef.current.fps}</div>
        <div className="text-yellow-300">
          Confidence: {trail.length > 0 ? `${(trail[trail.length - 1].confidence * 100).toFixed(0)}%` : '--'}
        </div>
      </div>
    </>
  )
}
