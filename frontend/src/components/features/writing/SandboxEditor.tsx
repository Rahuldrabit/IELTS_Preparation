/**
 * SandboxEditor — the active rewrite input for the Band Booster Scaffold.
 *
 * Shows the current locked sentence at the top (read-only, red),
 * a textarea for the student's rewrite, a live band meter,
 * structural hints from evaluationFeedback, and a manual "Check" button
 * when liveEvaluation is disabled.
 *
 * Calls useBandEvaluator as a side-effect — the hook fires 800ms after
 * the student stops typing (when liveEvaluation is on).
 *
 * When passes_threshold is true, auto-commits after a 500ms delay so
 * the student sees the green bar before the canvas updates.
 */
'use client'

import { useEffect, useRef } from 'react'
import { motion, AnimatePresence } from 'framer-motion'
import { Loader2, CheckCircle2, Lightbulb, Zap } from 'lucide-react'
import { Button } from '@/components/ui/button'
import { Progress } from '@/components/ui/progress'
import { cn } from '@/lib/utils'
import { useWritingStore } from '@/lib/store/writingStore'
import { useBandEvaluator } from '@/lib/hooks/useBandEvaluator'
import { useFeature } from '@/lib/hooks/useFeature'

export function SandboxEditor() {
  const {
    segmentedSentences,
    activeLockedIndex,
    sandboxBuffer,
    isEvaluating,
    evaluationFeedback,
    scaffoldComplete,
    targetBand,
    updateSandboxBuffer,
    commitUpgrade,
  } = useWritingStore()

  const liveEvaluationEnabled = useFeature('writing', 'liveEvaluation')

  // Mount the side-effect evaluator hook
  const { checkManually } = useBandEvaluator()

  // Auto-commit with 500ms celebratory pause on pass
  const commitTimerRef = useRef<ReturnType<typeof setTimeout> | null>(null)
  useEffect(() => {
    if (evaluationFeedback?.passes_threshold && sandboxBuffer.trim()) {
      commitTimerRef.current = setTimeout(() => {
        commitUpgrade(sandboxBuffer.trim())
      }, 500)
    }
    return () => {
      if (commitTimerRef.current) clearTimeout(commitTimerRef.current)
    }
  }, [evaluationFeedback, sandboxBuffer, commitUpgrade])

  if (scaffoldComplete) {
    return (
      <motion.div
        initial={{ opacity: 0, scale: 0.96 }}
        animate={{ opacity: 1, scale: 1 }}
        className="h-full flex flex-col items-center justify-center gap-4 p-8 text-center"
      >
        <div className="h-16 w-16 rounded-full bg-green-100 dark:bg-green-950 flex items-center justify-center">
          <CheckCircle2 className="h-8 w-8 text-green-500" />
        </div>
        <h3 className="text-lg font-semibold text-green-700 dark:text-green-400">
          All sentences upgraded!
        </h3>
        <p className="text-sm text-muted-foreground">
          Your essay now meets Band {targetBand}. Submit it for full AI feedback.
        </p>
      </motion.div>
    )
  }

  if (activeLockedIndex === null) return null

  const activeSentence = segmentedSentences[activeLockedIndex]
  const bandProgress = evaluationFeedback
    ? Math.round((evaluationFeedback.estimated_band / 9) * 100)
    : 0
  const passes = evaluationFeedback?.passes_threshold ?? false

  return (
    <div className="flex flex-col gap-4 p-4 h-full">
      {/* Sentence label */}
      <div>
        <p className="text-xs font-medium text-muted-foreground uppercase tracking-wider mb-1">
          Sentence {activeLockedIndex + 1} — Rewrite to Band {targetBand}
        </p>
        <div className="p-3 rounded-lg bg-destructive/5 border border-destructive/20">
          <p className="text-sm text-destructive italic leading-relaxed">
            "{activeSentence?.text}"
          </p>
        </div>
      </div>

      {/* Sandbox textarea */}
      <div className="relative flex-1">
        <textarea
          value={sandboxBuffer}
          onChange={(e) => updateSandboxBuffer(e.target.value)}
          placeholder="Rewrite this sentence here…"
          className={cn(
            'w-full h-full min-h-[120px] p-4 rounded-xl border text-sm leading-relaxed',
            'bg-background resize-none focus:outline-none focus:ring-2 focus:ring-ring',
            isEvaluating && 'border-primary/40'
          )}
        />
        {/* Evaluating shimmer border — does NOT disable typing */}
        {isEvaluating && (
          <div className="absolute inset-0 rounded-xl pointer-events-none">
            <div className="absolute inset-0 rounded-xl border-2 border-primary/30 animate-pulse" />
          </div>
        )}
      </div>

      {/* Band meter */}
      <AnimatePresence>
        {evaluationFeedback && (
          <motion.div
            initial={{ opacity: 0, height: 0 }}
            animate={{ opacity: 1, height: 'auto' }}
            exit={{ opacity: 0, height: 0 }}
            className="space-y-1.5"
          >
            <div className="flex items-center justify-between text-xs">
              <span className="text-muted-foreground">Estimated band</span>
              <span className={cn('font-semibold', passes ? 'text-green-600' : 'text-amber-600')}>
                {evaluationFeedback.estimated_band.toFixed(1)}
                {passes && ' ✓'}
              </span>
            </div>
            <Progress
              value={bandProgress}
              className={cn(
                'h-2',
                passes ? '[&>div]:bg-green-500' : '[&>div]:bg-amber-500'
              )}
            />
          </motion.div>
        )}
      </AnimatePresence>

      {/* Structural hint */}
      <AnimatePresence>
        {evaluationFeedback?.structural_suggestions && !passes && (
          <motion.div
            initial={{ opacity: 0, y: 4 }}
            animate={{ opacity: 1, y: 0 }}
            exit={{ opacity: 0 }}
            className="p-3 rounded-lg bg-muted/60 flex items-start gap-2"
          >
            <Lightbulb className="h-4 w-4 text-amber-500 shrink-0 mt-0.5" />
            <p className="text-xs leading-relaxed text-muted-foreground">
              {evaluationFeedback.structural_suggestions}
            </p>
          </motion.div>
        )}
      </AnimatePresence>

      {/* Controls */}
      <div className="flex items-center gap-2">
        {!liveEvaluationEnabled && (
          <Button
            size="sm"
            variant="outline"
            className="flex-1 gap-1.5"
            onClick={checkManually}
            disabled={isEvaluating || sandboxBuffer.trim().length < 5}
          >
            {isEvaluating ? (
              <Loader2 className="h-3.5 w-3.5 animate-spin" />
            ) : (
              <Zap className="h-3.5 w-3.5" />
            )}
            Check Sentence
          </Button>
        )}
        {liveEvaluationEnabled && isEvaluating && (
          <div className="flex items-center gap-2 text-xs text-muted-foreground">
            <Loader2 className="h-3.5 w-3.5 animate-spin" />
            Evaluating…
          </div>
        )}
      </div>
    </div>
  )
}
