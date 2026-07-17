'use client'

import { useState, useCallback, useRef, useEffect } from 'react'
import { useSearchParams } from 'next/navigation'
import { motion, AnimatePresence } from 'framer-motion'
import {
  Send, Loader2, AlertCircle,
  RotateCcw, Activity, Headphones,
} from 'lucide-react'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Badge } from '@/components/ui/badge'
import { Progress } from '@/components/ui/progress'
import { cn } from '@/lib/utils'
import { listeningApi, type GenerateListeningRequest } from '@/lib/services/listening'
import {
  useListeningStore,
  useTotalListeningQuestions,
  useAnsweredListeningCount,
  useIsAllListeningAnswered,
} from '@/lib/store/listeningStore'
import { ListeningConfigPanel } from '@/components/features/listening/ListeningConfigPanel'
import { ListeningPlayer, type ListeningPlayerHandle } from '@/components/features/listening/ListeningPlayer'
import { ReviewPanel } from '@/components/features/reading/ReviewPanel'
import { WorkspaceFeatureChipGroup } from '@/components/ui/WorkspaceFeatureChip'
import { useFeature } from '@/lib/hooks/useFeature'

// ─────────────────────────────────────────────
//  Reusable Question Section (shared with reading)
// ─────────────────────────────────────────────

interface QuestionGroupPublic {
  group_id: string;
  question_type: string;
  instructions: string;
  questions: Array<{
    id: number;
    question_number: number;
    prompt_text: string;
    local_options: string[] | null;
    question_type: string;
  }>;
}

function ListeningQuestionSection({
  group,
  answers,
  submitted,
  onAnswer,
}: {
  group: QuestionGroupPublic;
  answers: Record<number, string>;
  submitted: boolean;
  onAnswer: (id: number, answer: string) => void;
}) {
  return (
    <Card>
      <CardHeader className="pb-3">
        <div className="flex items-center justify-between">
          <CardTitle className="text-base">
            {group.question_type.replace(/_/g, ' ')}
          </CardTitle>
          <Badge variant="outline">{group.questions.length} questions</Badge>
        </div>
        <p className="text-sm text-muted-foreground">{group.instructions}</p>
      </CardHeader>
      <CardContent>
        <div className="space-y-4">
          {group.questions.map((question) => (
            <div
              key={question.id}
              className={cn(
                'p-4 rounded-xl border transition-all',
                answers[question.id] ? 'border-primary/30 bg-primary/5' : 'border-border'
              )}
            >
              <div className="flex items-start gap-2 mb-3">
                <span className="flex h-6 w-6 items-center justify-center rounded-full bg-muted text-xs font-medium">
                  {question.question_number}
                </span>
                <p className="text-sm font-medium flex-1">{question.prompt_text}</p>
              </div>

              {/* Fill Blank */}
              {group.question_type === 'FILL_BLANK' && (
                <input
                  type="text"
                  value={answers[question.id] || ''}
                  onChange={(e) => onAnswer(question.id, e.target.value)}
                  disabled={submitted}
                  placeholder="Type your answer..."
                  className="w-full p-3 rounded-lg border bg-background text-sm"
                />
              )}

              {/* Multiple Choice */}
              {group.question_type === 'MULTIPLE_CHOICE' && question.local_options && (
                <div className="space-y-2">
                  {question.local_options.map((option, idx) => (
                    <button
                      key={idx}
                      onClick={() => onAnswer(question.id, option)}
                      disabled={submitted}
                      className={cn(
                        'w-full p-3 rounded-lg text-sm text-left transition-all',
                        answers[question.id] === option
                          ? 'bg-primary text-primary-foreground'
                          : 'bg-muted hover:bg-muted/80'
                      )}
                    >
                      <span className="font-medium mr-2">{String.fromCharCode(65 + idx)}.</span>
                      {option}
                    </button>
                  ))}
                </div>
              )}

              {/* Matching Information */}
              {group.question_type === 'MATCHING_INFORMATION' && question.local_options && (
                <div className="space-y-2">
                  <select
                    value={answers[question.id] || ''}
                    onChange={(e) => onAnswer(question.id, e.target.value)}
                    disabled={submitted}
                    className="w-full p-3 rounded-lg border bg-background text-sm"
                  >
                    <option value="">Select...</option>
                    {question.local_options.map((option, idx) => (
                      <option key={idx} value={option}>
                        {String.fromCharCode(65 + idx)}. {option}
                      </option>
                    ))}
                  </select>
                </div>
              )}
            </div>
          ))}
        </div>
      </CardContent>
    </Card>
  )
}

// ─────────────────────────────────────────────
//  Page Component
// ─────────────────────────────────────────────

export default function ListeningPage() {
  const {
    phase,
    sessionId,
    title,
    script,
    ttsConfig,
    questionGroups,
    answers,
    reviewResults,
    score,
    bandEstimate,
    error,
    setSection,
    setAnswer,
    setReviewResults,
    setError,
    reset,
  } = useListeningStore()

  const totalQuestions = useTotalListeningQuestions()
  const answeredCount  = useAnsweredListeningCount()
  const isAllAnswered  = useIsAllListeningAnswered()
  const [isSubmitting, setIsSubmitting] = useState(false)
  const telemetryEnabled = useFeature('listening', 'telemetry')

  // Ref to player so we can pull telemetry at submit time
  const playerRef = useRef<ListeningPlayerHandle>(null)

  const handleGenerate = useCallback(async (config: GenerateListeningRequest) => {
    setError(null)
    try {
      const response = await listeningApi.generate(config)
      setSection(response)
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to generate test. Check your GEMINI_API_KEY.')
    }
  }, [setSection, setError])

  // Auto-generate AI test when ?auto=ai (from AI journey)
  const searchParams = useSearchParams()
  const autoMode = searchParams.get('auto')
  const autoTriggeredRef = useRef(false)

  useEffect(() => {
    if (autoMode === 'ai' && phase === 'config' && !autoTriggeredRef.current) {
      autoTriggeredRef.current = true
      const topic = searchParams.get('topic') || 'general'
      handleGenerate({
        section: 2,
        accent: 'british',
        speed: 'normal',
        topic,
        weakness_focus: [],
        question_types: ['FILL_BLANK', 'MULTIPLE_CHOICE'],
        question_count: 8,
      })
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [autoMode, phase])

  const handleSubmit = useCallback(async () => {
    if (!sessionId || !isAllAnswered) return
    setIsSubmitting(true)
    try {
      const answerArray = Object.entries(answers).map(([questionId, answer]) => ({
        question_id: Number(questionId),
        answer,
      }))
      // Attach telemetry payload if feature is enabled
      const telemetryPayload = telemetryEnabled && playerRef.current
        ? playerRef.current.getTelemetryPayload()
        : {}
      const response = await listeningApi.submitAndAnalyze(sessionId, answerArray)
      setReviewResults(response.results, response.score, response.band_estimate)
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to submit answers')
    } finally {
      setIsSubmitting(false)
    }
  }, [sessionId, answers, isAllAnswered, setReviewResults, setError, telemetryEnabled])

  return (
    <div className="space-y-6">
      <AnimatePresence mode="wait">
        {/* Phase: Config */}
        {phase === 'config' && (
          <ListeningConfigPanel onGenerate={handleGenerate} />
        )}

        {/* Phase: Loading */}
        {phase === 'loading' && (
          <motion.div
            key="loading"
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            className="flex flex-col items-center justify-center py-20"
          >
            <Loader2 className="h-12 w-12 animate-spin text-primary mb-4" />
            <p className="text-lg font-medium">Generating your IELTS listening test...</p>
            <p className="text-sm text-muted-foreground">AI is creating a realistic script</p>
          </motion.div>
        )}

        {/* Phase: Workspace */}
        {phase === 'workspace' && ttsConfig && (
          <motion.div
            key="workspace"
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            className="space-y-6"
          >
            {/* Player with feature chips */}
            <div className="space-y-2">
              <div className="flex items-center justify-between">
                <h2 className="text-xl font-semibold">{title}</h2>
                <WorkspaceFeatureChipGroup
                  skill="listening"
                  chips={[
                    { featureKey: 'acousticLevel', label: 'Exam Room DSP', icon: Headphones },
                    { featureKey: 'telemetry', label: 'Telemetry', icon: Activity },
                  ]}
                />
              </div>
              <ListeningPlayer
                ref={playerRef}
                script={script}
                title={title}
                ttsConfig={ttsConfig}
              />
            </div>

            {/* Questions */}
            <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
              <div className="lg:col-span-2 space-y-4">
                <Card>
                  <CardHeader className="pb-3">
                    <div className="flex items-center justify-between">
                      <CardTitle className="text-base">Questions</CardTitle>
                      <div className="flex items-center gap-2">
                        <Badge variant="outline">{totalQuestions} questions</Badge>
                        <Progress
                          value={(answeredCount / totalQuestions) * 100}
                          className="w-24 h-2"
                        />
                        <span className="text-xs text-muted-foreground">
                          {answeredCount}/{totalQuestions}
                        </span>
                      </div>
                    </div>
                  </CardHeader>
                </Card>

                {questionGroups.map((group) => (
                  <ListeningQuestionSection
                    key={group.group_id}
                    group={group}
                    answers={answers}
                    submitted={false}
                    onAnswer={setAnswer}
                  />
                ))}

                <Button
                  onClick={handleSubmit}
                  disabled={!isAllAnswered || isSubmitting}
                  className="w-full"
                  size="lg"
                >
                  {isSubmitting ? (
                    <>
                      <Loader2 className="h-4 w-4 mr-2 animate-spin" />
                      Analyzing...
                    </>
                  ) : (
                    <>
                      <Send className="h-4 w-4 mr-2" />
                      Submit Answers
                    </>
                  )}
                </Button>
              </div>

              {/* Script panel (optional sidebar) */}
              <Card className="h-fit">
                <CardHeader className="pb-3">
                  <CardTitle className="text-base">Transcript</CardTitle>
                </CardHeader>
                <CardContent>
                  <p className="text-sm text-muted-foreground leading-relaxed max-h-[400px] overflow-y-auto">
                    {script}
                  </p>
                </CardContent>
              </Card>
            </div>
          </motion.div>
        )}

        {/* Phase: Review */}
        {phase === 'review' && reviewResults && (
          <motion.div
            key="review"
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
          >
            <ReviewPanel
              results={reviewResults}
              score={score!}
              bandEstimate={bandEstimate!}
              onTryAgain={reset}
            />
          </motion.div>
        )}
      </AnimatePresence>

      {/* Error state */}
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
