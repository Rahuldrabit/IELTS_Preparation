'use client'

import { useState } from 'react'
import { useParams, useRouter } from 'next/navigation'
import { motion } from 'framer-motion'
import {
  ArrowLeft, PenTool, Send, Loader2, CheckCircle2, XCircle, Sparkles, Plus, Trash2
} from 'lucide-react'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Badge } from '@/components/ui/badge'
import { Progress } from '@/components/ui/progress'
import { cn } from '@/lib/utils'
import { grammarApi } from '@/lib/services/grammar'
import { getTopicById } from '@/lib/data/grammar'
import type { WritingPracticeResponse, SentenceFeedback } from '@/lib/types/grammar'

export default function GrammarWritingPage() {
  const params = useParams()
  const router = useRouter()
  const topicId = Number(params.topicId)

  // Static frontend data — no API needed for topic info
  const topicData = getTopicById(topicId)
  const topicName = topicData?.topic_name || `Topic ${topicId}`

  const [sentences, setSentences] = useState<string[]>(['', '', '', '', ''])
  const [isSubmitting, setIsSubmitting] = useState(false)
  const [feedback, setFeedback] = useState<WritingPracticeResponse | null>(null)
  const [error, setError] = useState<string | null>(null)

  const handleSentenceChange = (index: number, value: string) => {
    setSentences(prev => {
      const updated = [...prev]
      updated[index] = value
      return updated
    })
  }

  const addSentence = () => {
    setSentences(prev => [...prev, ''])
  }

  const removeSentence = (index: number) => {
    if (sentences.length <= 1) return
    setSentences(prev => prev.filter((_, i) => i !== index))
  }

  const handleSubmit = async () => {
    const validSentences = sentences.filter(s => s.trim().length > 0)
    if (validSentences.length === 0) return

    setIsSubmitting(true)
    setError(null)
    try {
      const response = await grammarApi.practiceWriting(topicId, {
        sentences: validSentences,
        target_grammar: topicName
      })
      setFeedback(response)
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to evaluate writing')
    } finally {
      setIsSubmitting(false)
    }
  }

  const handleReset = () => {
    setSentences(['', '', '', '', ''])
    setFeedback(null)
    setError(null)
  }

  const filledCount = sentences.filter(s => s.trim().length > 0).length

  return (
    <div className="space-y-6 max-w-3xl mx-auto">
      {/* Header */}
      <div className="flex items-center gap-4">
        <Button variant="ghost" size="icon" onClick={() => router.push(`/practice/grammar/topics/${topicId}`)}>
          <ArrowLeft className="h-4 w-4" />
        </Button>
        <div>
          <h1 className="text-2xl font-bold flex items-center gap-2">
            <PenTool className="h-6 w-6 text-green-600" />
            Writing Practice
          </h1>
          <p className="text-muted-foreground">
            Write sentences using <span className="font-medium">{topicName}</span> and get AI feedback
          </p>
        </div>
      </div>

      {!feedback ? (
        /* Writing Input */
        <Card>
          <CardHeader>
            <CardTitle className="text-base">
              Write 5 sentences using {topicName}
            </CardTitle>
            <p className="text-sm text-muted-foreground">
              The AI will analyze each sentence for grammar accuracy, target structure usage, and estimated IELTS band.
            </p>
          </CardHeader>
          <CardContent className="space-y-4">
            {sentences.map((sentence, idx) => (
              <div key={idx} className="flex gap-2">
                <div className="flex items-center gap-2 shrink-0">
                  <span className="text-sm font-bold text-primary w-5">{idx + 1}.</span>
                </div>
                <textarea
                  value={sentence}
                  onChange={(e) => handleSentenceChange(idx, e.target.value)}
                  placeholder={`Write sentence ${idx + 1} using ${topicName}...`}
                  rows={2}
                  className="flex-1 p-3 rounded-xl border border-input bg-background text-sm leading-relaxed resize-none focus:outline-none focus:ring-2 focus:ring-ring"
                />
                <Button
                  variant="ghost"
                  size="icon"
                  onClick={() => removeSentence(idx)}
                  disabled={sentences.length <= 1}
                  className="shrink-0"
                >
                  <Trash2 className="h-4 w-4 text-muted-foreground" />
                </Button>
              </div>
            ))}

            <Button variant="outline" size="sm" onClick={addSentence}>
              <Plus className="h-4 w-4 mr-2" />Add Sentence
            </Button>

            {error && (
              <div className="p-3 rounded-lg bg-destructive/10 border border-destructive/20">
                <p className="text-sm text-destructive">{error}</p>
              </div>
            )}

            <div className="flex items-center justify-between pt-4">
              <span className="text-sm text-muted-foreground">{filledCount} sentences written</span>
              <Button onClick={handleSubmit} disabled={filledCount === 0 || isSubmitting}>
                {isSubmitting ? (
                  <><Loader2 className="h-4 w-4 mr-2 animate-spin" />Analyzing...</>
                ) : (
                  <><Send className="h-4 w-4 mr-2" />Submit for AI Review</>
                )}
              </Button>
            </div>
          </CardContent>
        </Card>
      ) : (
        /* Feedback */
        <motion.div initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }} className="space-y-6">
          {/* Score Overview */}
          <Card>
            <CardContent className="p-6">
              <div className="flex items-center justify-between mb-4">
                <div>
                  <h3 className="font-semibold">Overall Accuracy</h3>
                  <p className="text-sm text-muted-foreground">Based on grammar correctness and target structure usage</p>
                </div>
                <div className="text-center">
                  <p className="text-3xl font-bold text-primary">{(feedback.overall_accuracy * 100).toFixed(0)}%</p>
                </div>
              </div>
              <Progress value={feedback.overall_accuracy * 100} className="h-3" />
            </CardContent>
          </Card>

          {/* Per-sentence feedback */}
          <div className="space-y-4">
            {feedback.sentences_feedback.map((sf, idx) => (
              <Card key={idx} className={cn(
                "border-l-4",
                sf.is_correct ? "border-l-green-500" : "border-l-red-500"
              )}>
                <CardContent className="p-4 space-y-3">
                  <div className="flex items-start justify-between gap-4">
                    <div className="flex items-start gap-2">
                      {sf.is_correct ? (
                        <CheckCircle2 className="h-5 w-5 text-success shrink-0 mt-0.5" />
                      ) : (
                        <XCircle className="h-5 w-5 text-destructive shrink-0 mt-0.5" />
                      )}
                      <p className="text-sm">{sf.sentence}</p>
                    </div>
                    <Badge variant="outline">Band {sf.estimated_band.toFixed(1)}</Badge>
                  </div>
                  <div className="pl-7 space-y-2">
                    <p className="text-sm text-muted-foreground">{sf.grammar_feedback}</p>
                    <div className="flex items-center gap-2">
                      <Badge variant={sf.target_structure_used ? 'success' : 'warning'} className="text-xs">
                        {sf.target_structure_used ? 'Target structure used' : 'Target structure missing'}
                      </Badge>
                    </div>
                  </div>
                </CardContent>
              </Card>
            ))}
          </div>

          {/* Recommendations */}
          {feedback.recommendations.length > 0 && (
            <Card className="border-primary/20 bg-primary/5">
              <CardContent className="p-4">
                <div className="flex items-center gap-2 mb-3">
                  <Sparkles className="h-4 w-4 text-primary" />
                  <span className="font-medium text-sm">AI Recommendations</span>
                </div>
                <ul className="space-y-2">
                  {feedback.recommendations.map((rec, idx) => (
                    <li key={idx} className="text-sm text-muted-foreground flex items-start gap-2">
                      <span className="text-primary">•</span>
                      {rec}
                    </li>
                  ))}
                </ul>
              </CardContent>
            </Card>
          )}

          {/* Actions */}
          <div className="flex gap-3">
            <Button variant="outline" className="flex-1" onClick={handleReset}>
              Try Again
            </Button>
            <Button className="flex-1" onClick={() => router.push(`/practice/grammar/topics/${topicId}`)}>
              Back to Lesson
            </Button>
          </div>
        </motion.div>
      )}
    </div>
  )
}