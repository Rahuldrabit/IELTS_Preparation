'use client'

import { motion } from 'framer-motion'
import { CheckCircle2, XCircle, HelpCircle } from 'lucide-react'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Badge } from '@/components/ui/badge'
import { Progress } from '@/components/ui/progress'
import { cn } from '@/lib/utils'
import type { QuestionGroupPublic } from '@/lib/services/reading'
import { TrapAlertBadge } from './TrapAlertBadge'

// ─────────────────────────────────────────────
//  Props
// ─────────────────────────────────────────────

interface QuestionSectionProps {
  group: QuestionGroupPublic
  answers: Record<number, string>
  submitted: boolean
  reviewResults?: Array<{
    question_id: number
    is_correct: boolean
    correct_answer: string
    evidence_text: string
  }>
  onAnswer: (questionId: number, answer: string) => void
  onQuestionFocus?: (questionId: number) => void
}

// ─────────────────────────────────────────────
//  Question Type Labels
// ─────────────────────────────────────────────

const QUESTION_TYPE_LABELS: Record<string, string> = {
  TRUE_FALSE_NOT_GIVEN: 'True / False / Not Given',
  MATCHING_HEADINGS: 'Matching Headings',
  SUMMARY_COMPLETION: 'Summary Completion',
  MULTIPLE_CHOICE: 'Multiple Choice',
  SENTENCE_COMPLETION: 'Sentence Completion',
  MATCHING_INFORMATION: 'Matching Information',
  FILL_BLANK: 'Fill in the Blanks',
}

// ─────────────────────────────────────────────
//  Component
// ─────────────────────────────────────────────

export function QuestionSection({
  group,
  answers,
  submitted,
  reviewResults,
  onAnswer,
  onQuestionFocus,
}: QuestionSectionProps) {
  const getReviewResult = (questionId: number) =>
    reviewResults?.find((r) => r.question_id === questionId)

  return (
    <Card>
      <CardHeader className="pb-3">
        <div className="flex items-center justify-between">
          <div>
            <CardTitle className="text-base">
              {QUESTION_TYPE_LABELS[group.question_type] || group.question_type}
            </CardTitle>
            <p className="text-sm text-muted-foreground mt-1">{group.instructions}</p>
          </div>
          <Badge variant="outline">{group.questions.length} questions</Badge>
        </div>
      </CardHeader>
      <CardContent>
        <div className="space-y-4">
          {group.questions.map((question) => {
            const review = getReviewResult(question.id)
            const isAnswered = question.id in answers
            const isCorrect = review?.is_correct ?? false

            return (
              <motion.div
                key={question.id}
                layout
                className={cn(
                  'p-4 rounded-xl border transition-all',
                  submitted
                    ? isCorrect
                      ? 'border-green-500/30 bg-green-50/50 dark:bg-green-950/20'
                      : 'border-red-500/30 bg-red-50/50 dark:bg-red-950/20'
                    : isAnswered
                    ? 'border-primary/30 bg-primary/5'
                    : 'border-border'
                )}
              >
                {/* Question header */}
                <div className="flex items-start gap-3 mb-3">
                  <span className="flex h-6 w-6 items-center justify-center rounded-full bg-muted text-xs font-medium shrink-0">
                    {question.question_number}
                  </span>
                  <div className="flex-1">
                    <p className="text-sm font-medium">{question.prompt_text}</p>
                    {/* Show trap badge if this is an adversarial question */}
                    {question.question_evaluation?.trap_type && (
                      <TrapAlertBadge
                        trapType={question.question_evaluation.trap_type}
                        className="mt-1.5"
                      />
                    )}
                  </div>
                </div>

                {/* TRUE_FALSE_NOT_GIVEN */}
                {group.question_type === 'TRUE_FALSE_NOT_GIVEN' && (
                  <div className="grid grid-cols-3 gap-2">
                    {['True', 'False', 'Not Given'].map((option) => (
                      <button
                        key={option}
                        onFocus={() => onQuestionFocus?.(question.id)}
                        onClick={() => !submitted && onAnswer(question.id, option)}
                        disabled={submitted}
                        className={cn(
                          'p-3 rounded-lg text-sm font-medium transition-all',
                          answers[question.id] === option
                            ? 'bg-primary text-primary-foreground'
                            : 'bg-muted hover:bg-muted/80',
                          submitted && 'cursor-not-allowed opacity-80'
                        )}
                      >
                        {option}
                        {submitted && review && (
                          <span className="ml-2">
                            {option === review.correct_answer ? (
                              <CheckCircle2 className="inline h-4 w-4 text-green-500" />
                            ) : answers[question.id] === option ? (
                              <XCircle className="inline h-4 w-4 text-red-500" />
                            ) : null}
                          </span>
                        )}
                      </button>
                    ))}
                  </div>
                )}

                {/* MULTIPLE_CHOICE */}
                {group.question_type === 'MULTIPLE_CHOICE' && question.local_options && (
                  <div className="space-y-2">
                    {question.local_options.map((option, idx) => {
                      const optionLetter = String.fromCharCode(65 + idx) // A, B, C, D
                      return (
                        <button
                          key={idx}
                          onFocus={() => onQuestionFocus?.(question.id)}
                          onClick={() => !submitted && onAnswer(question.id, option)}
                          disabled={submitted}
                          className={cn(
                            'w-full p-3 rounded-lg text-sm text-left flex items-center justify-between transition-all',
                            answers[question.id] === option
                              ? 'bg-primary text-primary-foreground'
                              : 'bg-muted hover:bg-muted/80',
                            submitted && 'cursor-not-allowed opacity-80'
                          )}
                        >
                          <span>
                            <span className="font-medium mr-2">{optionLetter}.</span>
                            {option}
                          </span>
                          {submitted && review && (
                            option === review.correct_answer ? (
                              <CheckCircle2 className="h-4 w-4 text-green-500" />
                            ) : answers[question.id] === option ? (
                              <XCircle className="h-4 w-4 text-red-500" />
                            ) : null
                          )}
                        </button>
                      )
                    })}
                  </div>
                )}

                {/* MATCHING_HEADINGS */}
                {group.question_type === 'MATCHING_HEADINGS' && question.local_options && (
                  <div className="space-y-2">
                    <select
                      value={answers[question.id] || ''}
                      onFocus={() => onQuestionFocus?.(question.id)}
                      onChange={(e) => !submitted && onAnswer(question.id, e.target.value)}
                      disabled={submitted}
                      className={cn(
                        'w-full p-3 rounded-lg border bg-background text-sm',
                        submitted && 'cursor-not-allowed opacity-80'
                      )}
                    >
                      <option value="">Select a heading...</option>
                      {question.local_options.map((option, idx) => (
                        <option key={idx} value={option}>
                          {String.fromCharCode(65 + idx)}. {option}
                        </option>
                      ))}
                    </select>
                  </div>
                )}

                {/* SUMMARY_COMPLETION & SENTENCE_COMPLETION & FILL_BLANK */}
                {['SUMMARY_COMPLETION', 'SENTENCE_COMPLETION', 'FILL_BLANK'].includes(
                  group.question_type
                ) && (
                  <div className="space-y-2">
                    <input
                      type="text"
                      value={answers[question.id] || ''}
                      onFocus={() => onQuestionFocus?.(question.id)}
                      onChange={(e) => onAnswer(question.id, e.target.value)}
                      disabled={submitted}
                      placeholder="Type your answer..."
                      className={cn(
                        'w-full p-3 rounded-lg border bg-background text-sm',
                        submitted && 'cursor-not-allowed opacity-80'
                      )}
                    />
                    {submitted && review && !isCorrect && (
                      <p className="text-sm text-green-600 dark:text-green-400">
                        Correct answer: <strong>{review.correct_answer}</strong>
                      </p>
                    )}
                  </div>
                )}

                {/* Review explanation */}
                {submitted && review && !isCorrect && review.evidence_text && (
                  <motion.div
                    initial={{ opacity: 0, height: 0 }}
                    animate={{ opacity: 1, height: 'auto' }}
                    className="mt-3 p-3 rounded-lg bg-muted/50"
                  >
                    <div className="flex items-start gap-2">
                      <HelpCircle className="h-4 w-4 text-primary shrink-0 mt-0.5" />
                      <div className="text-sm">
                        <p className="font-medium text-muted-foreground">Evidence:</p>
                        <p className="text-foreground">{review.evidence_text}</p>
                      </div>
                    </div>
                  </motion.div>
                )}
              </motion.div>
            )
          })}
        </div>
      </CardContent>
    </Card>
  )
}

// ─────────────────────────────────────────────
//  Questions Panel (All Groups)
// ─────────────────────────────────────────────

interface QuestionsPanelProps {
  groups: QuestionGroupPublic[]
  answers: Record<number, string>
  submitted: boolean
  reviewResults?: Array<{
    question_id: number
    is_correct: boolean
    correct_answer: string
    evidence_text: string
  }>
  onAnswer: (questionId: number, answer: string) => void
  onQuestionFocus?: (questionId: number) => void
}

export function QuestionsPanel({
  groups,
  answers,
  submitted,
  reviewResults,
  onAnswer,
  onQuestionFocus,
}: QuestionsPanelProps) {
  const totalQuestions = groups.reduce((sum, g) => sum + g.questions.length, 0)
  const answeredCount = Object.keys(answers).length
  const progress = totalQuestions > 0 ? (answeredCount / totalQuestions) * 100 : 0

  return (
    <div className="space-y-4">
      {/* Progress */}
      <div className="flex items-center justify-between">
        <span className="text-sm text-muted-foreground">
          {answeredCount} / {totalQuestions} answered
        </span>
        <Progress value={progress} className="w-32 h-2" />
      </div>

      {/* Question groups */}
      {groups.map((group) => (
        <QuestionSection
          key={group.group_id}
          group={group}
          answers={answers}
          submitted={submitted}
          reviewResults={reviewResults}
          onAnswer={onAnswer}
          onQuestionFocus={onQuestionFocus}
        />
      ))}
    </div>
  )
}
