'use client'

import { useState, useEffect, useCallback } from 'react'
import { useParams, useRouter } from 'next/navigation'
import { motion, AnimatePresence } from 'framer-motion'
import {
  ArrowLeft, ChevronRight, ChevronLeft, CheckCircle2, XCircle,
  Sparkles, Brain, Loader2, RotateCcw, Trophy
} from 'lucide-react'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Badge } from '@/components/ui/badge'
import { Progress } from '@/components/ui/progress'
import { cn } from '@/lib/utils'
import { grammarApi } from '@/lib/services/grammar'
import type { ExerciseData, ExerciseEvaluation } from '@/lib/types/grammar'

// Exercise components
import { FillInBlank } from '@/components/features/grammar/exercises/FillInBlank'
import { MultipleChoice } from '@/components/features/grammar/exercises/MultipleChoice'
import { ErrorCorrection } from '@/components/features/grammar/exercises/ErrorCorrection'
import { RewriteSentence } from '@/components/features/grammar/exercises/RewriteSentence'
import { DragAndDrop } from '@/components/features/grammar/exercises/DragAndDrop'
import { SentenceOrdering } from '@/components/features/grammar/exercises/SentenceOrdering'
import { SentenceExpansion } from '@/components/features/grammar/exercises/SentenceExpansion'
import { GrammarTransformation } from '@/components/features/grammar/exercises/GrammarTransformation'

const EXERCISE_TYPES = [
  'fill_blank', 'multiple_choice', 'error_correction', 'rewrite',
  'drag_drop', 'sentence_ordering', 'expansion', 'transformation'
]

export default function ExercisesPage() {
  const params = useParams()
  const router = useRouter()
  const topicId = Number(params.topicId)

  const [exercises, setExercises] = useState<ExerciseData[]>([])
  const [currentIndex, setCurrentIndex] = useState(0)
  const [userAnswer, setUserAnswer] = useState('')
  const [evaluation, setEvaluation] = useState<ExerciseEvaluation | null>(null)
  const [results, setResults] = useState<Array<{ exerciseId: number; correct: boolean }>>([])
  const [isLoading, setIsLoading] = useState(true)
  const [isEvaluating, setIsEvaluating] = useState(false)
  const [isComplete, setIsComplete] = useState(false)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    generateExercises()
  }, [topicId])

  const generateExercises = async () => {
    setIsLoading(true)
    setError(null)
    try {
      const data = await grammarApi.generateExercises(topicId, {
        types: EXERCISE_TYPES,
        count: 8,
        difficulty: 'medium'
      })
      setExercises(data)
      setCurrentIndex(0)
      setResults([])
      setIsComplete(false)
      setEvaluation(null)
      setUserAnswer('')
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to generate exercises')
    } finally {
      setIsLoading(false)
    }
  }

  const handleSubmitAnswer = useCallback(async () => {
    if (!userAnswer.trim() || !exercises[currentIndex]) return
    setIsEvaluating(true)
    try {
      const result = await grammarApi.evaluateExercise({
        exercise_id: exercises[currentIndex].id,
        user_answer: userAnswer
      })
      setEvaluation(result)
      setResults(prev => [...prev, { exerciseId: exercises[currentIndex].id, correct: result.is_correct }])
    } catch (err) {
      // Fallback: simple comparison
      const isCorrect = userAnswer.trim().toLowerCase() === exercises[currentIndex].correct_answer.trim().toLowerCase()
      const fallbackEval: ExerciseEvaluation = {
        is_correct: isCorrect,
        correct_answer: exercises[currentIndex].correct_answer,
        explanation: exercises[currentIndex].explanation || '',
        mastery_change: isCorrect ? 2 : -1
      }
      setEvaluation(fallbackEval)
      setResults(prev => [...prev, { exerciseId: exercises[currentIndex].id, correct: isCorrect }])
    } finally {
      setIsEvaluating(false)
    }
  }, [userAnswer, exercises, currentIndex])

  const handleNext = () => {
    if (currentIndex < exercises.length - 1) {
      setCurrentIndex(prev => prev + 1)
      setUserAnswer('')
      setEvaluation(null)
    } else {
      setIsComplete(true)
    }
  }

  const currentExercise = exercises[currentIndex]
  const correctCount = results.filter(r => r.correct).length
  const progress = exercises.length > 0 ? ((currentIndex + (evaluation ? 1 : 0)) / exercises.length) * 100 : 0

  if (isLoading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="text-center">
          <Sparkles className="h-8 w-8 text-primary animate-pulse mx-auto mb-3" />
          <p className="text-muted-foreground">Generating exercises...</p>
        </div>
      </div>
    )
  }

  if (error) {
    return (
      <div className="space-y-4">
        <Button variant="ghost" onClick={() => router.back()}>
          <ArrowLeft className="h-4 w-4 mr-2" />Back
        </Button>
        <Card className="border-destructive/20">
          <CardContent className="p-6 text-center">
            <XCircle className="h-8 w-8 text-destructive mx-auto mb-3" />
            <p className="font-medium text-destructive">{error}</p>
            <Button className="mt-4" onClick={generateExercises}>Try Again</Button>
          </CardContent>
        </Card>
      </div>
    )
  }

  // Completion screen
  if (isComplete) {
    const accuracy = exercises.length > 0 ? (correctCount / exercises.length) * 100 : 0
    return (
      <div className="space-y-6 max-w-lg mx-auto">
        <motion.div initial={{ scale: 0.8, opacity: 0 }} animate={{ scale: 1, opacity: 1 }}>
          <Card>
            <CardContent className="p-8 text-center space-y-4">
              <Trophy className={cn("h-16 w-16 mx-auto", accuracy >= 70 ? "text-amber-500" : "text-muted-foreground")} />
              <h2 className="text-2xl font-bold">Exercise Complete!</h2>
              <div className="p-4 rounded-xl bg-primary/10">
                <p className="text-sm text-muted-foreground mb-1">Score</p>
                <p className="text-4xl font-bold text-primary">{correctCount}/{exercises.length}</p>
                <p className="text-sm text-muted-foreground mt-1">{accuracy.toFixed(0)}% accuracy</p>
              </div>
              <Progress value={accuracy} className="h-3" />
              <div className="flex gap-3 pt-4">
                <Button variant="outline" className="flex-1" onClick={generateExercises}>
                  <RotateCcw className="h-4 w-4 mr-2" />Try Again
                </Button>
                <Button className="flex-1" onClick={() => router.push(`/practice/grammar/topics/${topicId}`)}>
                  Back to Lesson
                </Button>
              </div>
            </CardContent>
          </Card>
        </motion.div>
      </div>
    )
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <Button variant="ghost" onClick={() => router.push(`/practice/grammar/topics/${topicId}`)}>
          <ArrowLeft className="h-4 w-4 mr-2" />Back to Lesson
        </Button>
        <Badge variant="outline">
          {currentIndex + 1} / {exercises.length}
        </Badge>
      </div>

      {/* Progress */}
      <div className="space-y-2">
        <div className="flex items-center justify-between text-sm">
          <span className="text-muted-foreground">Progress</span>
          <span className="font-medium">{correctCount} correct so far</span>
        </div>
        <Progress value={progress} className="h-2" />
      </div>

      {/* Exercise Card */}
      {currentExercise && (
        <AnimatePresence mode="wait">
          <motion.div
            key={currentIndex}
            initial={{ opacity: 0, x: 20 }}
            animate={{ opacity: 1, x: 0 }}
            exit={{ opacity: 0, x: -20 }}
          >
            <Card>
              <CardHeader>
                <div className="flex items-center justify-between">
                  <CardTitle className="text-base flex items-center gap-2">
                    <Brain className="h-4 w-4 text-primary" />
                    <span className="capitalize">{currentExercise.exercise_type.replace(/_/g, ' ')}</span>
                  </CardTitle>
                  <Badge variant="outline" className="capitalize">{currentExercise.difficulty}</Badge>
                </div>
              </CardHeader>
              <CardContent className="space-y-4">
                {/* Render exercise based on type */}
                {renderExercise(currentExercise, userAnswer, setUserAnswer, !!evaluation)}

                {/* Evaluation feedback */}
                {evaluation && (
                  <motion.div
                    initial={{ opacity: 0, y: 10 }}
                    animate={{ opacity: 1, y: 0 }}
                    className={cn(
                      "p-4 rounded-xl border",
                      evaluation.is_correct
                        ? "bg-success/5 border-success/20"
                        : "bg-destructive/5 border-destructive/20"
                    )}
                  >
                    <div className="flex items-center gap-2 mb-2">
                      {evaluation.is_correct ? (
                        <CheckCircle2 className="h-5 w-5 text-success" />
                      ) : (
                        <XCircle className="h-5 w-5 text-destructive" />
                      )}
                      <span className="font-medium">
                        {evaluation.is_correct ? 'Correct!' : 'Incorrect'}
                      </span>
                    </div>
                    {!evaluation.is_correct && (
                      <p className="text-sm mb-2">
                        <span className="font-medium">Correct answer:</span> {evaluation.correct_answer}
                      </p>
                    )}
                    {evaluation.explanation && (
                      <p className="text-sm text-muted-foreground">{evaluation.explanation}</p>
                    )}
                  </motion.div>
                )}

                {/* Action buttons */}
                <div className="flex justify-between pt-2">
                  <Button
                    variant="outline"
                    disabled={currentIndex === 0}
                    onClick={() => { setCurrentIndex(prev => prev - 1); setUserAnswer(''); setEvaluation(null) }}
                  >
                    <ChevronLeft className="h-4 w-4 mr-2" />Previous
                  </Button>

                  {!evaluation ? (
                    <Button onClick={handleSubmitAnswer} disabled={!userAnswer.trim() || isEvaluating}>
                      {isEvaluating ? (
                        <><Loader2 className="h-4 w-4 mr-2 animate-spin" />Checking...</>
                      ) : (
                        'Submit Answer'
                      )}
                    </Button>
                  ) : (
                    <Button onClick={handleNext}>
                      {currentIndex < exercises.length - 1 ? (
                        <>Next<ChevronRight className="h-4 w-4 ml-2" /></>
                      ) : (
                        <>Finish<Trophy className="h-4 w-4 ml-2" /></>
                      )}
                    </Button>
                  )}
                </div>
              </CardContent>
            </Card>
          </motion.div>
        </AnimatePresence>
      )}
    </div>
  )
}

function renderExercise(
  exercise: ExerciseData,
  userAnswer: string,
  setUserAnswer: (val: string) => void,
  isDisabled: boolean
) {
  const props = { exercise, userAnswer, setUserAnswer, disabled: isDisabled }

  switch (exercise.exercise_type) {
    case 'fill_blank':
      return <FillInBlank {...props} />
    case 'multiple_choice':
      return <MultipleChoice {...props} />
    case 'error_correction':
      return <ErrorCorrection {...props} />
    case 'rewrite':
      return <RewriteSentence {...props} />
    case 'drag_drop':
      return <DragAndDrop {...props} />
    case 'sentence_ordering':
      return <SentenceOrdering {...props} />
    case 'expansion':
      return <SentenceExpansion {...props} />
    case 'transformation':
      return <GrammarTransformation {...props} />
    default:
      return <FillInBlank {...props} />
  }
}