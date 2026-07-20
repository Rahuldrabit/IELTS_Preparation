'use client'

import React, { useEffect, useRef, useState, useCallback } from 'react'
import { motion, AnimatePresence } from 'framer-motion'
import { Loader2, Camera, CheckCircle2, AlertCircle } from 'lucide-react'
import { Button } from '@/components/ui/button'
import type { UseTelemetryReturn } from '../hooks/useTelemetry'
import type { FaceMeshResult, Point3D } from '../types'

interface EyeTrackingSetupModalProps {
  isOpen: boolean
  onClose: () => void
  onComplete: (stream: MediaStream) => void
  cte: UseTelemetryReturn
}

type SetupStep = 'intro' | 'requesting' | 'loading' | 'ready' | 'error'

export function EyeTrackingSetupModal({
  isOpen,
  onClose,
  onComplete,
  cte,
}: EyeTrackingSetupModalProps) {
  const [step, setStep] = useState<SetupStep>('intro')
  const [stream, setStream] = useState<MediaStream | null>(null)
  const [errorMsg, setErrorMsg] = useState<string | null>(null)
  const [progress, setProgress] = useState<{ stage: string; percent: number } | null>(null)

  const videoRef = useRef<HTMLVideoElement>(null)
  const canvasRef = useRef<HTMLCanvasElement>(null)

  // Reset state on open
  useEffect(() => {
    if (isOpen) {
      setStep('intro')
      setStream(null)
      setErrorMsg(null)
      setProgress(null)
    }
  }, [isOpen])

  // Bind stream to video element
  useEffect(() => {
    if (videoRef.current && stream) {
      videoRef.current.srcObject = stream
    }
  }, [stream, step])

  // Draw FaceMesh when ready
  useEffect(() => {
    if (step !== 'ready' || !cte.tracker) return

    const tracker = cte.tracker as any
    if (!tracker.faceMesh) return

    const handleResult = (result: FaceMeshResult) => {
      const canvas = canvasRef.current
      const video = videoRef.current
      if (!canvas || !video || !result.fullMesh) return

      const ctx = canvas.getContext('2d')
      if (!ctx) return

      // Match canvas to video size
      canvas.width = video.clientWidth
      canvas.height = video.clientHeight

      ctx.clearRect(0, 0, canvas.width, canvas.height)

      const w = canvas.width
      const h = canvas.height

      // Draw full mesh
      ctx.fillStyle = 'rgba(255, 255, 255, 0.4)'
      for (const p of result.fullMesh) {
        ctx.beginPath()
        ctx.arc(p.x * w, p.y * h, 1, 0, 2 * Math.PI)
        ctx.fill()
      }

      // Highlight Irises
      if (result.landmarks) {
        ctx.fillStyle = '#38bdf8' // bright blue
        ctx.shadowColor = '#38bdf8'
        ctx.shadowBlur = 10

        const leftIris = result.landmarks.leftIris
        const rightIris = result.landmarks.rightIris

        ctx.beginPath()
        ctx.arc(leftIris.x * w, leftIris.y * h, 3, 0, 2 * Math.PI)
        ctx.arc(rightIris.x * w, rightIris.y * h, 3, 0, 2 * Math.PI)
        ctx.fill()

        ctx.shadowBlur = 0
      }
    }

    const dispose = tracker.faceMesh.on('result', handleResult)
    return () => dispose()
  }, [step, cte.tracker])

  const handleAllowCamera = async () => {
    setStep('requesting')
    try {
      const mediaStream = await navigator.mediaDevices.getUserMedia({
        video: { width: { ideal: 640 }, height: { ideal: 480 }, facingMode: 'user' },
        audio: false,
      })
      setStream(mediaStream)
      setStep('loading')

      await cte.start(mediaStream, (p) => {
        setProgress({ stage: p.stage, percent: p.progress })
      })
      setStep('ready')
    } catch (err) {
      const error = err instanceof Error ? err : new Error(String(err))
      setErrorMsg(error.message)
      setStep('error')
      console.error('[EyeTrackingSetup] Error:', error)
    }
  }

  const handleStartCalibration = () => {
    if (stream) {
      onComplete(stream)
    }
  }

  const handleCancel = () => {
    if (stream) {
      stream.getTracks().forEach((t) => t.stop())
    }
    // Also stop cte if it was started here and we cancel
    if (cte.status === 'active' || cte.status === 'starting') {
      cte.stop()
    }
    onClose()
  }

  if (!isOpen) return null

  return (
    <div className="fixed inset-0 z-[9999] flex items-center justify-center bg-black/60 backdrop-blur-sm p-4">
      <motion.div
        initial={{ opacity: 0, scale: 0.95 }}
        animate={{ opacity: 1, scale: 1 }}
        exit={{ opacity: 0, scale: 0.95 }}
        className="bg-background rounded-2xl shadow-2xl border border-border overflow-hidden w-full max-w-md"
      >
        <div className="p-6">
          <h2 className="text-2xl font-semibold mb-2">Eye Tracking Setup</h2>
          
          {step === 'intro' && (
            <div className="space-y-4">
              <p className="text-muted-foreground text-sm">
                Eye tracking helps us understand your reading patterns to provide personalized feedback on your reading speed, focus, and areas of friction.
              </p>
              <div className="bg-muted p-4 rounded-xl flex items-start gap-3">
                <Camera className="w-5 h-5 text-primary shrink-0 mt-0.5" />
                <p className="text-sm font-medium">
                  We need access to your webcam. All processing happens locally on your device; no video is ever recorded or sent to our servers.
                </p>
              </div>
              <div className="flex justify-end gap-3 mt-6">
                <Button variant="ghost" onClick={handleCancel}>Cancel</Button>
                <Button onClick={handleAllowCamera}>Allow Camera Access</Button>
              </div>
            </div>
          )}

          {step === 'requesting' && (
            <div className="py-8 flex flex-col items-center justify-center space-y-4 text-center">
              <Loader2 className="w-8 h-8 animate-spin text-primary" />
              <p className="font-medium">Please allow camera access in your browser popup...</p>
            </div>
          )}

          {step === 'loading' && (
            <div className="space-y-4">
              <div className="relative aspect-video bg-muted rounded-xl overflow-hidden shadow-inner">
                <video
                  ref={videoRef}
                  autoPlay
                  playsInline
                  muted
                  className="w-full h-full object-cover scale-x-[-1]"
                />
                <div className="absolute inset-0 bg-background/50 flex flex-col items-center justify-center backdrop-blur-sm">
                  <Loader2 className="w-8 h-8 animate-spin text-primary mb-3" />
                  <p className="font-medium text-sm">Downloading FaceMesh Model...</p>
                  
                  {progress ? (
                    <div className="w-48 mt-4">
                      <div className="flex justify-between text-[10px] text-muted-foreground mb-1.5 uppercase tracking-wider font-semibold">
                        <span>
                          {progress.stage === 'library' && 'Loading library...'}
                          {progress.stage === 'wasm' && 'Downloading WASM...'}
                          {progress.stage === 'model' && 'Downloading model...'}
                          {progress.stage === 'initializing' && 'Initializing...'}
                        </span>
                        <span>{Math.round(progress.percent)}%</span>
                      </div>
                      <div className="h-1.5 bg-black/10 rounded-full overflow-hidden shadow-inner">
                        <motion.div 
                          className="h-full bg-primary rounded-full"
                          initial={{ width: 0 }}
                          animate={{ width: `${progress.percent}%` }}
                          transition={{ duration: 0.3, ease: 'easeOut' }}
                        />
                      </div>
                    </div>
                  ) : (
                    <p className="text-xs text-muted-foreground mt-1">This may take a moment on the first run.</p>
                  )}
                </div>
              </div>
            </div>
          )}

          {step === 'ready' && (
            <div className="space-y-4">
              <p className="text-sm text-muted-foreground text-center">
                Face detected! Please ensure your face is well-lit and centered.
              </p>
              <div className="relative aspect-video bg-muted rounded-xl overflow-hidden shadow-inner border border-primary/20">
                <video
                  ref={videoRef}
                  autoPlay
                  playsInline
                  muted
                  className="w-full h-full object-cover scale-x-[-1]"
                />
                <canvas
                  ref={canvasRef}
                  className="absolute inset-0 w-full h-full object-cover scale-x-[-1]"
                />
                <div className="absolute top-2 right-2 bg-black/60 text-white text-xs px-2 py-1 rounded-md flex items-center gap-1.5 backdrop-blur-md">
                  <span className="w-2 h-2 rounded-full bg-green-400 animate-pulse" />
                  Tracking Active
                </div>
              </div>
              <div className="flex justify-end gap-3 mt-6">
                <Button variant="ghost" onClick={handleCancel}>Cancel</Button>
                <Button onClick={handleStartCalibration} className="gap-2">
                  <CheckCircle2 className="w-4 h-4" />
                  Start Calibration
                </Button>
              </div>
            </div>
          )}

          {step === 'error' && (
            <div className="space-y-4">
              <div className="bg-destructive/10 text-destructive p-4 rounded-xl flex items-start gap-3">
                <AlertCircle className="w-5 h-5 shrink-0 mt-0.5" />
                <div>
                  <p className="font-semibold">Failed to start eye tracking</p>
                  <p className="text-sm mt-1">{errorMsg}</p>
                </div>
              </div>
              <div className="flex justify-end gap-3 mt-6">
                <Button variant="ghost" onClick={handleCancel}>Close</Button>
                <Button onClick={() => setStep('intro')}>Try Again</Button>
              </div>
            </div>
          )}
        </div>
      </motion.div>
    </div>
  )
}
