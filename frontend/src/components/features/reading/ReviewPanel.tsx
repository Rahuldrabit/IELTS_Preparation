/**
 * ReviewPanel — Comprehensive review panel for IELTS reading practice.
 * Shows score summary, tab-by-tab question analysis with AI-powered insights.
 */
'use client'

import { useState } from 'react'
import { motion } from 'framer-motion'
import { CheckCircle2, XCircle, AlertCircle, Lightbulb, BookOpen, Target, ArrowRight, RotateCcw } from 'lucide-react'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs'
import { cn } from '@/lib/utils'
import { useFeature } from '@/lib/hooks/useFeature'
import { LowConfidenceInsightCard } from './LowConfidenceInsightCard'
import { SocraticHintPanel } from './SocraticHintPanel'
import type { QuestionExplanation } from '@/lib/services/reading'

// ─────────────────────────────────────────────
//  Props
// ─────────────────────────────────────────────

interface ReviewPanelProps {
  results: QuestionExplanation[]
  score: number
  bandEstimate: number
  sessionId: number
  // paragraphs from the passage — needed to supply excerpt to SocraticHintPanel
  paragraphs: Array<{ paragraph_id: string; text: string }>
  onPracticeSimilar?: () => void
  onTryAgain?: () => void
  onHighlightParagraph?: (paragraphId: string) => void
}

// ─────────────────────────────────────────────
//  Mistake Type Colors
// ─────────────────────────────────────────────

const MISTAKE_TYPE_COLORS: Record<string, string> = {
  Inference: 'text-purple-500',
  Vocabulary: 'text-orange-500',
  Distractor: 'text-red-500',
  'Skim-Scan': 'text-blue-500',
  Detail: 'text-cyan-500',
  None: 'text-green-500',
}

// ─────────────────────────────────────────────
//  Component
// ─────────────────────────────────────────────

export function ReviewPanel({
  results,
  score,
  bandEstimate,
  sessionId,
  paragraphs,
  onPracticeSimilar,
  onTryAgain,
  onHighlightParagraph,
}: ReviewPanelProps) {
  const [activeTab, setActiveTab] = useState(String(results[0]?.question_id || '1'))

  // Separate correct and incorrect
  const correctCount = results.filter((r) => r.is_correct).length
  const incorrectCount = results.filter((r) => !r.is_correct).length
  const total = results.length
  const lowConfidenceCount = results.filter((r) => r.confidence_flag === 'low_confidence_win').length

  // Compute band estimate with low-confidence penalty
  // If more than 20% are low confidence, reduce band by 0.5
  const lowConfidencePenalty = lowConfidenceCount > total * 0.2 ? -0.5 : 0
  const adjustedBandEstimate = bandEstimate + lowConfidencePenalty

  return (
    <motion.div
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      className="space-y-6"
    >
      {/* Score Summary */}
      <Card className="bg-gradient-to-r from-primary/10 to-primary/5 border-primary/20">
        <CardContent className="p-6">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm text-muted-foreground">Your Score</p>
              <p className="text-4xl font-bold text-primary">{score.toFixed(0)}%</p>
              <p className="text-sm text-muted-foreground mt-1">
                {correctCount} correct out of {total}
              </p>
            </div>
            <div className="text-right">
              <p className="text-sm text-muted-foreground">Estimated Band</p>
              <p className="text-4xl font-bold">{adjustedBandEstimate.toFixed(1)}</p>
            </div>
          </div>

          {/* Progress bar showing correct/incorrect/low-confidence */}
          <div className="mt-4 flex gap-1 h-2 rounded-full overflow-hidden bg-muted">
            <div
              className="bg-green-500"
              style={{ width: `${((correctCount - lowConfidenceCount) / total) * 100}%` }}
            />
            <div
              className="bg-amber-500"
              style={{ width: `${(lowConfidenceCount / total) * 100}%` }}
            />
            <div
              className="bg-red-500"
              style={{ width: `${(incorrectCount / total) * 100}%` }}
            />
          </div>
          
          {lowConfidenceCount > 0 && (
            <p className="text-xs text-amber-600 mt-2">
              {lowConfidenceCount} correct answer{lowConfidenceCount > 1 ? 's' : ''} flagged as low-confidence. Under exam time pressure, hesitation costs marks.
            </p>
          )}
        </CardContent>
      </Card>

      {/* Tab-by-tab review */}
      <Card>
        <CardHeader>
          <CardTitle className="text-base">Question Review</CardTitle>
          <p className="text-sm text-muted-foreground">
            Click each question tab to see detailed analysis
          </p>
        </CardHeader>
        <CardContent>
          <Tabs value={activeTab} onValueChange={setActiveTab}>
            {/* Tab list with question numbers */}
            <TabsList className="flex flex-wrap gap-1 h-auto p-1 bg-muted/50">
              {results.map((r) => {
                const isLowConfidence = r.confidence_flag === 'low_confidence_win'
                
                return (
                  <TabsTrigger
                    key={r.question_id}
                    value={String(r.question_id)}
                    className={cn(
                      'w-10 h-10 p-0 rounded-lg relative',
                      r.is_correct
                        ? 'data-[state=active]:bg-green-500 data-[state=active]:text-white'
                        : 'data-[state=active]:bg-red-500 data-[state=active]:text-white'
                    )}
                  >
                    {r.is_correct ? (
                      <CheckCircle2 className="h-4 w-4" />
                    ) : (
                      <XCircle className="h-4 w-4" />
                    )}
                    {isLowConfidence && (
                      <div className="absolute -top-1 -right-1">
                        <AlertCircle className="h-3 w-3 text-amber-500" />
                      </div>
                    )}
                  </TabsTrigger>
                )
              })}
            </TabsList>

            {/* Tab content */}
            {results.map((r) => (
              <TabsContent
                key={r.question_id}
                value={String(r.question_id)}
                className="mt-4"
              >
                <QuestionReviewCard
                  result={r}
                  sessionId={sessionId}
                  paragraphs={paragraphs}
                  onHighlightParagraph={onHighlightParagraph}
                  onPracticeSimilar={onPracticeSimilar}
                />
              </TabsContent>
            ))}
          </Tabs>
        </CardContent>
      </Card>

      {/* Actions */}
      <div className="flex gap-3">
        <Button variant="outline" onClick={onTryAgain} className="flex-1">
          <RotateCcw className="h-4 w-4 mr-2" />
          Try Another Test
        </Button>
        <Button onClick={onPracticeSimilar} className="flex-1">
          <Target className="h-4 w-4 mr-2" />
          Practice Similar
        </Button>
      </div>
    </motion.div>
  )
}

// ─────────────────────────────────────��───────
//  Individual Question Review Card
// ─────────────────────────────────────────────

interface QuestionReviewCardProps {
  result: QuestionExplanation
  sessionId: number
  paragraphs: Array<{ paragraph_id: string; text: string }>
  onHighlightParagraph?: (paragraphId: string) => void
  onPracticeSimilar?: () => void
}

function QuestionReviewCard({
  result,
  sessionId,
  paragraphs,
  onHighlightParagraph,
  onPracticeSimilar,
}: QuestionReviewCardProps) {
  const confidenceFlagsEnabled = useFeature('reading', 'confidenceFlags')

  // Find the relevant passage excerpt for the Socratic panel
  // Use the evidence paragraph if known, otherwise use first paragraph
  const passageExcerpt = (() => {
    if (result.evidence_paragraph_id) {
      const para = paragraphs.find(p => p.paragraph_id === result.evidence_paragraph_id)
      if (para) return para.text
    }
    return paragraphs.slice(0, 2).map(p => p.text).join(' ')
  })()

  if (result.is_correct) {
    return (
      <div className="space-y-4">
        <div className="p-6 rounded-xl bg-green-50 dark:bg-green-950/20 border border-green-200 dark:border-green-900">
          <div className="flex items-center gap-3">
            <CheckCircle2 className="h-8 w-8 text-green-500" />
            <div>
              <p className="font-semibold text-green-700 dark:text-green-400">
                Correct!
              </p>
              <p className="text-sm text-green-600 dark:text-green-500">
                Your answer: {result.user_answer}
              </p>
            </div>
          </div>
        </div>

        {confidenceFlagsEnabled && result.confidence_flag === 'low_confidence_win' && (
          <LowConfidenceInsightCard result={result} />
        )}
      </div>
    )
  }

  return (
    <div className="space-y-4">
      {/* Answer comparison */}
      <div className="p-4 rounded-xl bg-red-50 dark:bg-red-950/20 border border-red-200 dark:border-red-900">
        <div className="flex items-start gap-3">
          <XCircle className="h-6 w-6 text-red-500 shrink-0 mt-0.5" />
          <div className="flex-1">
            <div className="flex items-center gap-4 mb-2">
              <div>
                <p className="text-sm text-muted-foreground">Your answer</p>
                <p className="font-medium line-through text-red-600 dark:text-red-400">
                  {result.user_answer}
                </p>
              </div>
              <ArrowRight className="h-4 w-4 text-muted-foreground" />
              <div>
                <p className="text-sm text-muted-foreground">Correct answer</p>
                <p className="font-medium text-green-600 dark:text-green-400">
                  {result.correct_answer}
                </p>
              </div>
            </div>
          </div>
        </div>
      </div>

      {/* Mistake type */}
      <div className="flex items-center gap-2">
        <AlertCircle className={cn('h-4 w-4', MISTAKE_TYPE_COLORS[result.mistake_type] || 'text-gray-500')} />
        <span className="text-sm font-medium">
          Mistake Type: <span className={MISTAKE_TYPE_COLORS[result.mistake_type]}>{result.mistake_type}</span>
        </span>
      </div>

      {/* Why wrong */}
      {result.why_wrong && (
        <div className="p-4 rounded-xl bg-muted/50">
          <div className="flex items-start gap-2">
            <Lightbulb className="h-4 w-4 text-amber-500 shrink-0 mt-0.5" />
            <div>
              <p className="text-sm font-medium text-muted-foreground mb-1">
                Why this answer is wrong
              </p>
              <p className="text-sm">{result.why_wrong}</p>
            </div>
          </div>
        </div>
      )}

      {/* Evidence */}
      {result.evidence_text && (
        <div className="p-4 rounded-xl bg-blue-50 dark:bg-blue-950/20 border border-blue-200 dark:border-blue-900">
          <div className="flex items-start gap-2">
            <BookOpen className="h-4 w-4 text-blue-500 shrink-0 mt-0.5" />
            <div className="flex-1">
              <p className="text-sm font-medium text-blue-700 dark:text-blue-400 mb-1">
                Evidence from passage
              </p>
              <p className="text-sm italic text-blue-600 dark:text-blue-300">
                "{result.evidence_text}"
              </p>
              {result.evidence_paragraph_id && onHighlightParagraph && (
                <Button
                  variant="link"
                  size="sm"
                  className="p-0 h-auto mt-2 text-blue-600 dark:text-blue-400"
                  onClick={() => onHighlightParagraph(result.evidence_paragraph_id)}
                >
                  Highlight paragraph {result.evidence_paragraph_id} in passage →
                </Button>
              )}
            </div>
          </div>
        </div>
      )}

      {/* Correct strategy */}
      {result.correct_strategy && (
        <div className="p-4 rounded-xl bg-primary/5 border border-primary/20">
          <div className="flex items-start gap-2">
            <Target className="h-4 w-4 text-primary shrink-0 mt-0.5" />
            <div>
              <p className="text-sm font-medium text-primary mb-1">
                Strategy for next time
              </p>
              <p className="text-sm">{result.correct_strategy}</p>
            </div>
          </div>
        </div>
      )}

      {/* Socratic Debugging Agent — guided hint dialogue */}
      <SocraticHintPanel
        result={result}
        passageExcerpt={passageExcerpt}
        sessionId={sessionId}
      />

      {/* Practice similar */}
      {onPracticeSimilar && (
        <Button variant="outline" size="sm" onClick={onPracticeSimilar}>
          <Target className="h-4 w-4 mr-2" />
          Practice similar questions
        </Button>
      )}
    </div>
  )
}
