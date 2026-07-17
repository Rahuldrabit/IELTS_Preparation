'use client'

import { useState, useCallback, useEffect, useRef } from 'react'
import { motion, AnimatePresence } from 'framer-motion'
import { useSearchParams } from 'next/navigation'
import {
  PenTool, Send, FileText, Loader2, Sparkles, RotateCcw,
  Target, BookOpen, CheckCircle2, AlertCircle, Lock, Zap,
} from 'lucide-react'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Badge } from '@/components/ui/badge'
import { cn } from '@/lib/utils'
import { writingApi, type CouncilReport } from '@/lib/services/writing'
import { profileApi } from '@/lib/services/profile'
import { useWritingStore } from '@/lib/store/writingStore'
import { CriterionFeedbackTabs } from '@/components/features/writing/CriterionFeedbackTabs'
import { AnnotatedEssay } from '@/components/features/writing/AnnotatedEssay'
import { SentenceCanvas } from '@/components/features/writing/SentenceCanvas'
import { SandboxEditor } from '@/components/features/writing/SandboxEditor'
import { CouncilVerdict } from '@/components/features/writing/CouncilVerdict'
import { Task1Chart } from '@/components/features/writing/Task1Chart'
import { SessionFeatureBar } from '@/components/ui/SessionFeatureBar'
import { useFeature } from '@/lib/hooks/useFeature'

// ─────────────────────────────────────────────
//  Page Component
// ─────────────────────────────────────────────

export default function WritingPage() {
  const {
    phase,
    task,
    essay,
    feedback,
    wordCount,
    error,
    mode,
    scaffoldComplete,
    segmentedSentences,
    setPhase,
    setTask,
    setEssay,
    setFeedback,
    setError,
    reset,
    setMode,
    initializeScaffold,
    clearScaffold,
  } = useWritingStore()

  const scaffoldFeatureOn = useFeature('writing', 'scaffoldMode')
  const [selectedTaskType, setSelectedTaskType] = useState<'task_1' | 'task_2'>('task_2')
  const [isGeneratingTask, setIsGeneratingTask] = useState(false)
  const [councilReport, setCouncilReport] = useState<CouncilReport | null>(null)

  // When scaffold feature is toggled off while in scaffold mode, drop back to standard
  useEffect(() => {
    if (!scaffoldFeatureOn && mode === 'scaffold') {
      setMode('standard')
      clearScaffold()
    }
  }, [scaffoldFeatureOn, mode, setMode, clearScaffold])

  // Auto-generate AI task when ?auto=ai (from onboarding/AI journey)
  const searchParams = useSearchParams()
  const autoMode = searchParams.get('auto')
  const autoTriggeredRef = useRef(false)

  useEffect(() => {
    if (autoMode === 'ai' && phase === 'config' && !autoTriggeredRef.current) {
      autoTriggeredRef.current = true
      const topic = searchParams.get('topic') || undefined
      handleGenerateTask(topic)
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [autoMode, phase])

  // ─────────────────────────────────────────────
  //  Handlers
  // ─────────────────────────────────────────────

  const handleGenerateTask = useCallback(async (topicOverride?: string) => {
    setIsGeneratingTask(true)
    try {
      const newTask = await writingApi.generateTask({
        task_type: selectedTaskType,
        target_band: 7.0,
        topic: topicOverride,
      })
      setTask(newTask)
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to generate task. Check your GEMINI_API_KEY.')
    } finally {
      setIsGeneratingTask(false)
    }
  }, [selectedTaskType, setTask, setError])

  const handleSubmit = useCallback(async () => {
    if (!task || wordCount < task.min_words) return
    setPhase('analyzing')
    try {
      const response = await writingApi.submitEssay(task.id, essay)
      setFeedback(response.feedback)
      if (response.council_report) setCouncilReport(response.council_report)

      // Fire-and-forget: refresh Uma's intervention with writing result
      if (response.feedback) {
        profileApi.refreshUmaIntervention({
          writing_band:         response.feedback.overall,
          writing_sessions:     1,
          writing_weak_criteria: response.feedback.per_criterion_feedback
            ?.filter(c => c.band < 7)
            .map(c => c.criterion) ?? [],
        }).catch(() => {/* silent */})
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to submit essay.')
    }
  }, [task, essay, wordCount, setPhase, setFeedback, setError])

  const handleTryAgain = useCallback(() => {
    reset()
    setCouncilReport(null)
  }, [reset])

  const handleModeSwitch = useCallback((next: 'standard' | 'scaffold') => {
    setMode(next)
    if (next === 'scaffold' && essay.trim()) {
      initializeScaffold(essay)
    } else if (next === 'standard') {
      clearScaffold()
    }
  }, [essay, setMode, initializeScaffold, clearScaffold])

  // ─────────────────────────────────────────────
  //  Render
  // ─────────────────────────────────────────────

  return (
    <div className="space-y-6">
      <AnimatePresence mode="wait">
        {/* ── Phase: Config ── */}
        {phase === 'config' && (
          <motion.div
            key="config"
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            exit={{ opacity: 0, y: -20 }}
          >
            <Card className="max-w-2xl mx-auto">
              <CardHeader>
                <div className="flex items-center gap-3">
                  <div className="h-12 w-12 rounded-xl bg-primary/10 flex items-center justify-center">
                    <PenTool className="h-6 w-6 text-primary" />
                  </div>
                  <div>
                    <CardTitle className="text-xl">Writing Practice</CardTitle>
                    <p className="text-sm text-muted-foreground">
                      Generate an AI writing task or pick from existing ones
                    </p>
                  </div>
                </div>
              </CardHeader>
              <CardContent className="space-y-6">
                {/* Task type selection */}
                <div className="space-y-2">
                  <label className="text-sm font-medium">Task Type</label>
                  <div className="grid grid-cols-2 gap-3">
                    {(['task_1', 'task_2'] as const).map((type) => (
                      <button
                        key={type}
                        onClick={() => setSelectedTaskType(type)}
                        className={cn(
                          'p-4 rounded-xl border text-center transition-all',
                          selectedTaskType === type
                            ? 'bg-primary text-primary-foreground border-primary'
                            : 'bg-muted/50 border-border hover:bg-muted'
                        )}
                      >
                        <div className="font-medium">{type === 'task_1' ? 'Task 1' : 'Task 2'}</div>
                        <div className="text-xs opacity-70 mt-1">
                          {type === 'task_1' ? 'Describe data/chart (150 words)' : 'Essay (250 words)'}
                        </div>
                      </button>
                    ))}
                  </div>
                </div>

                <SessionFeatureBar
                  skill="writing"
                  features={[
                    { featureKey: 'scaffoldMode', label: 'Scaffold', icon: Lock },
                    { featureKey: 'liveEvaluation', label: 'Live AI', icon: Zap },
                  ]}
                  className="mb-2"
                />

                <Button
                  onClick={() => handleGenerateTask()}
                  disabled={isGeneratingTask}
                  className="w-full"
                  size="lg"
                >
                  {isGeneratingTask ? (
                    <><Loader2 className="h-4 w-4 mr-2 animate-spin" />Generating…</>
                  ) : (
                    <><Sparkles className="h-4 w-4 mr-2" />Generate Writing Task</>
                  )}
                </Button>
              </CardContent>
            </Card>
          </motion.div>
        )}

        {/* ── Phase: Writing / Analyzing / Review ── */}
        {(phase === 'writing' || phase === 'analyzing' || phase === 'review') && task && (
          <motion.div
            key="workspace"
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            className="space-y-6"
          >
            {/* Header */}
            <div className="flex items-center justify-between flex-wrap gap-3">
              <div className="flex items-center gap-3">
                <h2 className="text-xl font-semibold">Writing Practice</h2>
                <Badge variant="outline">{task.task_type.replace('_', ' ').toUpperCase()}</Badge>
                <span className="text-sm text-muted-foreground">Min {task.min_words} words</span>
              </div>

              {/* Mode selector — only visible when scaffold feature is on */}
              {scaffoldFeatureOn && phase === 'writing' && (
                <div className="flex items-center gap-1 p-1 bg-muted rounded-xl">
                  {(['standard', 'scaffold'] as const).map((m) => (
                    <button
                      key={m}
                      onClick={() => handleModeSwitch(m)}
                      className={cn(
                        'px-4 py-1.5 rounded-lg text-sm font-medium transition-all',
                        mode === m
                          ? 'bg-background shadow-sm text-foreground'
                          : 'text-muted-foreground hover:text-foreground'
                      )}
                    >
                      {m === 'standard' ? '✏️ Standard' : '🔒 Scaffold'}
                    </button>
                  ))}
                </div>
              )}
            </div>

            {/* Session Feature Bar — accessible during practice */}
            {phase === 'writing' && (
              <SessionFeatureBar
                skill="writing"
                features={[
                  { featureKey: 'scaffoldMode', label: 'Scaffold', icon: Lock },
                  { featureKey: 'liveEvaluation', label: 'Live AI', icon: Zap },
                ]}
              />
            )}

            {/* Task prompt */}
            <Card>
              <CardHeader className="pb-3">
                <CardTitle className="text-base flex items-center gap-2">
                  <FileText className="h-4 w-4" />
                  {task.task_type.replace('_', ' ').toUpperCase()}
                </CardTitle>
              </CardHeader>
              <CardContent className="space-y-3">
                <div className="p-4 rounded-xl bg-muted/50">
                  <p className="leading-relaxed">{task.prompt}</p>
                </div>
                {/* Task 1 Chart Visualization */}
                {task.chart_data && (
                  <div className="p-4 rounded-xl border bg-background">
                    <Task1Chart chartData={task.chart_data} />
                  </div>
                )}
                {task.description && (
                  <p className="text-sm text-muted-foreground">{task.description}</p>
                )}
                {task.band_descriptor && (
                  <p className="text-xs text-muted-foreground italic">{task.band_descriptor}</p>
                )}
              </CardContent>
            </Card>

            {/* ── STANDARD mode: existing textarea + feedback ── */}
            {mode === 'standard' && (
              <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
                {/* Essay editor */}
                <Card className="h-full">
                  <CardHeader className="pb-3">
                    <div className="flex items-center justify-between">
                      <CardTitle className="text-base">Your Essay</CardTitle>
                      <div className="flex items-center gap-2">
                        <span className={cn(
                          'text-sm font-mono',
                          wordCount < task.min_words ? 'text-yellow-500' : 'text-green-500'
                        )}>
                          {wordCount} words
                        </span>
                        {wordCount >= task.min_words && (
                          <CheckCircle2 className="h-4 w-4 text-green-500" />
                        )}
                      </div>
                    </div>
                  </CardHeader>
                  <CardContent>
                    <textarea
                      value={essay}
                      onChange={(e) => setEssay(e.target.value)}
                      disabled={phase === 'analyzing'}
                      placeholder={`Start writing your essay here… Aim for at least ${task.min_words} words.`}
                      className="w-full h-[400px] p-4 rounded-xl border border-input bg-background text-sm leading-relaxed resize-none focus:outline-none focus:ring-2 focus:ring-ring disabled:opacity-50"
                    />
                    <div className="flex items-center justify-between mt-4">
                      <Button variant="outline" size="sm" onClick={() => setEssay('')}>
                        <PenTool className="h-4 w-4 mr-2" />Clear
                      </Button>
                      <Button
                        onClick={handleSubmit}
                        disabled={wordCount < task.min_words || phase === 'analyzing'}
                      >
                        {phase === 'analyzing' ? (
                          <><Loader2 className="h-4 w-4 mr-2 animate-spin" />Analyzing…</>
                        ) : (
                          <><Send className="h-4 w-4 mr-2" />Submit for Review</>
                        )}
                      </Button>
                    </div>
                  </CardContent>
                </Card>

                {/* Feedback panel */}
                <Card className="h-full">
                  <CardHeader className="pb-3">
                    <CardTitle className="text-base flex items-center gap-2">
                      <Sparkles className="h-4 w-4" />AI Feedback
                    </CardTitle>
                  </CardHeader>
                  <CardContent>
                    {!feedback ? (
                      <div className="h-full flex flex-col items-center justify-center text-center py-12">
                        <div className="h-16 w-16 rounded-full bg-muted flex items-center justify-center mb-4">
                          <PenTool className="h-8 w-8 text-muted-foreground" />
                        </div>
                        <p className="text-muted-foreground">
                          Write your essay and click &quot;Submit for Review&quot; to get AI feedback
                        </p>
                      </div>
                    ) : (
                      <div className="space-y-6">
                        <div className="p-4 rounded-xl bg-primary/10 border border-primary/20 text-center">
                          <p className="text-sm text-muted-foreground mb-1">Overall Band Score</p>
                          <p className="text-3xl font-bold text-primary">{feedback.overall.toFixed(1)}</p>
                        </div>
                        {/* Council of Judges verdict — shown when available, else standard tabs */}
                        {councilReport ? (
                          <CouncilVerdict report={councilReport} />
                        ) : (
                          <CriterionFeedbackTabs feedback={feedback.per_criterion_feedback} />
                        )}
                        {feedback.inline_corrections.length > 0 && (
                          <div className="space-y-3">
                            <h4 className="text-sm font-medium flex items-center gap-2">
                              <BookOpen className="h-4 w-4" />
                              Inline Corrections ({feedback.inline_corrections.length})
                            </h4>
                            <AnnotatedEssay essay={essay} corrections={feedback.inline_corrections} />
                          </div>
                        )}
                        <div className="flex gap-3 pt-2">
                          <Button onClick={handleTryAgain} variant="outline" className="flex-1">
                            <RotateCcw className="h-4 w-4 mr-2" />New Task
                          </Button>
                          <Button onClick={() => handleGenerateTask()} className="flex-1" disabled={isGeneratingTask}>
                            <Target className="h-4 w-4 mr-2" />Generate Another
                          </Button>
                        </div>
                      </div>
                    )}
                  </CardContent>
                </Card>
              </div>
            )}

            {/* ── SCAFFOLD mode: SentenceCanvas + SandboxEditor ── */}
            {mode === 'scaffold' && (
              <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
                {/* Left: read-only coloured essay */}
                <Card className="h-full min-h-[500px]">
                  <CardHeader className="pb-2">
                    <CardTitle className="text-base flex items-center gap-2">
                      <Lock className="h-4 w-4 text-muted-foreground" />
                      Essay View
                    </CardTitle>
                    <p className="text-xs text-muted-foreground">
                      Red = needs upgrading · Green = passed · Dim = not yet reached
                    </p>
                  </CardHeader>
                  <CardContent className="h-[calc(100%-5rem)] overflow-y-auto">
                    <SentenceCanvas />
                  </CardContent>
                </Card>

                {/* Right: sandbox rewrite area */}
                <Card className="h-full min-h-[500px]">
                  <CardHeader className="pb-2">
                    <CardTitle className="text-base flex items-center gap-2">
                      <Zap className="h-4 w-4 text-primary" />
                      Rewrite Sandbox
                    </CardTitle>
                    {segmentedSentences.length > 0 && (
                      <p className="text-xs text-muted-foreground">
                        {segmentedSentences.filter((s) => !s.isLocked).length} of{' '}
                        {segmentedSentences.length} sentences upgraded
                      </p>
                    )}
                  </CardHeader>
                  <CardContent className="h-[calc(100%-5rem)]">
                    <SandboxEditor />
                  </CardContent>
                </Card>
              </div>
            )}

            {/* Submit button — shown in both modes once word count is met */}
            {phase === 'writing' && mode === 'standard' && wordCount >= task.min_words && (
              <div className="flex justify-end">
                <Button onClick={handleSubmit} size="lg">
                  <Send className="h-4 w-4 mr-2" />Submit for Review
                </Button>
              </div>
            )}

            {/* Scaffold complete — enable submit */}
            {phase === 'writing' && mode === 'scaffold' && scaffoldComplete && (
              <motion.div
                initial={{ opacity: 0, y: 8 }}
                animate={{ opacity: 1, y: 0 }}
                className="flex justify-end"
              >
                <Button onClick={handleSubmit} size="lg" className="bg-green-600 hover:bg-green-700">
                  <Send className="h-4 w-4 mr-2" />Submit Upgraded Essay
                </Button>
              </motion.div>
            )}
          </motion.div>
        )}
      </AnimatePresence>

      {/* Error banner */}
      {error && (
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          className="p-4 rounded-xl bg-destructive/10 border border-destructive/20"
        >
          <div className="flex items-center gap-3">
            <AlertCircle className="h-5 w-5 text-destructive" />
            <div>
              <p className="font-medium text-destructive">Error</p>
              <p className="text-sm text-muted-foreground">{error}</p>
            </div>
          </div>
        </motion.div>
      )}
    </div>
  )
}
