/**
 * ShadowingAssessment — recording + assessment UI for the shadowing step.
 *
 * Shows: the target tier text (read guide), a live waveform from rmsHistory,
 * record / stop button, an "Assess" button, and result feedback.
 * Uses useAudioWorkletRecorder (with MediaRecorder fallback).
 */
'use client'

import { useEffect, useCallback } from 'react'
import { motion, AnimatePresence } from 'framer-motion'
import {
  Mic, Square, Loader2, CheckCircle2, XCircle, AlertCircle, RotateCcw, ChevronLeft,
} from 'lucide-react'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Badge } from '@/components/ui/badge'
import { cn } from '@/lib/utils'
import { useAudioWorkletRecorder } from '@/lib/hooks/useAudioWorkletRecorder'
import { useSpeakingStore } from '@/lib/store/speakingStore'
import { useMutationEngine } from '@/lib/hooks/useMutationEngine'
import type { MutationTier } from '@/lib/services/speaking'

interface ShadowingAssessmentProps {
  targetTier: MutationTier
  onBack: () => void
}

export function ShadowingAssessment({ targetTier, onBack }: ShadowingAssessmentProps) {
  const { phase, assessmentResult, error } = useSpeakingStore()
  const { assessShadowing } = useMutationEngine()

  const {
    isRecording,
    secondsRemaining,
    audioBlob,
    fluencyMetrics,
    startRecording,
    stopRecording,
    reset: resetRecorder,
    error: recorderError,
    isWorkletSupported,
  } = useAudioWorkletRecorder()

  // Auto-stop at 0
  useEffect(() => {
    if (secondsRemaining === 0 && isRecording) stopRecording()
  }, [secondsRemaining, isRecording, stopRecording])

  const formatTime = (s: number) =>
    `${Math.floor(s / 60)}:${String(s % 60).padStart(2, '0')}`

  const handleAssess = useCallback(async () => {
    if (!audioBlob) return
    await assessShadowing(audioBlob, targetTier)
  }, [audioBlob, targetTier, assessShadowing])

  const handleTryAgain = useCallback(() => {
    resetRecorder()
    useSpeakingStore.getState().setAssessmentResult(null as any)
    useSpeakingStore.getState().setPhase('shadowing')
    useSpeakingStore.getState().setError(null)
  }, [resetRecorder])

  const isAssessing = phase === 'assessing'
  const hasResult   = !!assessmentResult

  // Live waveform bars — from rmsHistory or simulate while recording
  const bars = fluencyMetrics?.rmsHistory.slice(-20) ?? Array(20).fill(0.05)

  return (
    <div className="space-y-4">
      {/* Back button */}
      <button
        onClick={onBack}
        className="flex items-center gap-1.5 text-sm text-muted-foreground hover:text-foreground transition-colors"
      >
        <ChevronLeft className="h-4 w-4" /> Back to tiers
      </button>

      {/* Target text reading guide */}
      <Card>
        <CardHeader className="pb-2">
          <div className="flex items-center justify-between">
            <CardTitle className="text-sm">Read aloud — {targetTier.band_label}</CardTitle>
            <Badge variant="outline" className="text-xs">Target</Badge>
          </div>
        </CardHeader>
        <CardContent>
          <p className="text-sm leading-loose bg-muted/50 p-4 rounded-xl">
            {targetTier.text}
          </p>
        </CardContent>
      </Card>

      {/* Recording interface */}
      <Card className={cn(isRecording && 'border-primary shadow-lg shadow-primary/20')}>
        <CardContent className="p-6">
          <div className="flex flex-col items-center gap-6">
            {/* Waveform bars */}
            <div className="flex items-center justify-center gap-0.5 h-16 w-full">
              {bars.map((rms, i) => (
                <motion.div
                  key={i}
                  animate={{ height: isRecording ? Math.max(4, rms * 200) : 4 }}
                  transition={{ duration: 0.1 }}
                  className={cn(
                    'w-2 rounded-full',
                    isRecording ? 'bg-primary' : 'bg-muted'
                  )}
                />
              ))}
            </div>

            {/* Timer */}
            <p className={cn(
              'text-3xl font-mono font-bold',
              isRecording ? 'text-primary' : 'text-muted-foreground'
            )}>
              {isAssessing
                ? <Loader2 className="inline h-8 w-8 animate-spin" />
                : formatTime(secondsRemaining)
              }
            </p>
            <p className="text-sm text-muted-foreground -mt-4">
              {isAssessing ? 'Assessing…'
                : isRecording ? 'Recording…'
                : audioBlob ? 'Recording ready'
                : 'Press to record your shadowing attempt'}
            </p>

            {/* Record / Stop button */}
            {!audioBlob && !isAssessing && (
              <motion.button
                whileHover={{ scale: 1.05 }}
                whileTap={{ scale: 0.95 }}
                onClick={isRecording ? stopRecording : startRecording}
                className={cn(
                  'h-20 w-20 rounded-full flex items-center justify-center shadow-lg transition-colors',
                  isRecording
                    ? 'bg-destructive hover:bg-destructive/90'
                    : 'bg-primary hover:bg-primary/90'
                )}
              >
                {isRecording
                  ? <Square className="h-8 w-8 text-white" />
                  : <Mic className="h-8 w-8 text-white" />
                }
              </motion.button>
            )}

            {/* Assess button */}
            {audioBlob && !isAssessing && !hasResult && (
              <div className="flex gap-3">
                <Button variant="outline" onClick={handleTryAgain} className="gap-1.5">
                  <RotateCcw className="h-4 w-4" /> Re-record
                </Button>
                <Button onClick={handleAssess} className="gap-1.5">
                  Assess My Recording
                </Button>
              </div>
            )}
          </div>
        </CardContent>
      </Card>

      {/* Recorder error */}
      {recorderError && (
        <div className="p-3 rounded-xl bg-destructive/10 border border-destructive/20 flex items-center gap-2">
          <AlertCircle className="h-4 w-4 text-destructive shrink-0" />
          <p className="text-sm text-destructive">{recorderError}</p>
        </div>
      )}

      {/* Assessment result */}
      <AnimatePresence>
        {hasResult && assessmentResult && (
          <motion.div
            initial={{ opacity: 0, y: 8 }}
            animate={{ opacity: 1, y: 0 }}
            exit={{ opacity: 0 }}
            className="space-y-3"
          >
            {/* Pass / Fail banner */}
            <div className={cn(
              'p-4 rounded-xl border flex items-center gap-3',
              assessmentResult.passed
                ? 'bg-green-50 dark:bg-green-950/20 border-green-200 dark:border-green-800'
                : 'bg-amber-50 dark:bg-amber-950/20 border-amber-200 dark:border-amber-800'
            )}>
              {assessmentResult.passed
                ? <CheckCircle2 className="h-6 w-6 text-green-500 shrink-0" />
                : <XCircle className="h-6 w-6 text-amber-500 shrink-0" />
              }
              <div>
                <p className={cn(
                  'font-semibold',
                  assessmentResult.passed
                    ? 'text-green-700 dark:text-green-400'
                    : 'text-amber-700 dark:text-amber-400'
                )}>
                  {assessmentResult.passed ? 'Passed! Great shadowing.' : 'Not quite — keep practising.'}
                </p>
                <p className="text-sm text-muted-foreground mt-0.5">
                  {assessmentResult.feedback}
                </p>
              </div>
            </div>

            {/* Scores */}
            <div className="grid grid-cols-3 gap-3 text-center">
              {[
                { label: 'Phoneme', value: assessmentResult.phoneme_accuracy },
                { label: 'Rhythm', value: assessmentResult.rhythm_score },
                { label: 'Connected', value: assessmentResult.connected_speech_score },
              ].map(({ label, value }) => (
                <div key={label} className="p-3 rounded-xl bg-muted/50">
                  <p className="text-xs text-muted-foreground mb-1">{label}</p>
                  <p className="text-lg font-bold">
                    {Math.round(value * 100)}%
                  </p>
                </div>
              ))}
            </div>

            {/* Specific errors */}
            {assessmentResult.specific_errors.length > 0 && (
              <ul className="space-y-1.5">
                {assessmentResult.specific_errors.map((err, i) => (
                  <li key={i} className="flex items-start gap-2 text-sm text-muted-foreground">
                    <span className="h-5 w-5 rounded-full bg-amber-100 dark:bg-amber-900/40 text-amber-600 text-xs flex items-center justify-center shrink-0 mt-0.5">
                      {i + 1}
                    </span>
                    {err}
                  </li>
                ))}
              </ul>
            )}

            {/* Try again if failed */}
            {!assessmentResult.passed && (
              <Button onClick={handleTryAgain} variant="outline" className="w-full gap-1.5">
                <RotateCcw className="h-4 w-4" /> Try Again
              </Button>
            )}
          </motion.div>
        )}
      </AnimatePresence>

      {/* Store-level error */}
      {error && !recorderError && (
        <div className="p-3 rounded-xl bg-destructive/10 border border-destructive/20 flex items-center gap-2">
          <AlertCircle className="h-4 w-4 text-destructive shrink-0" />
          <p className="text-sm text-destructive">{error}</p>
        </div>
      )}
    </div>
  )
}
