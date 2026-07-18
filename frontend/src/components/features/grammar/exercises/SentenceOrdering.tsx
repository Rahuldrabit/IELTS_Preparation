'use client'

import { useState, useEffect } from 'react'
import { cn } from '@/lib/utils'
import { GripVertical, ArrowUp, ArrowDown } from 'lucide-react'
import type { ExerciseData } from '@/lib/types/grammar'

interface Props {
  exercise: ExerciseData
  userAnswer: string
  setUserAnswer: (val: string) => void
  disabled: boolean
}

export function SentenceOrdering({ exercise, userAnswer, setUserAnswer, disabled }: Props) {
  const question = exercise.question_data?.question || 'Put the sentences in the correct order'
  const sentences: string[] = exercise.question_data?.sentences || exercise.correct_answer.split('. ').filter(Boolean)
  
  const [orderedSentences, setOrderedSentences] = useState<string[]>([])

  useEffect(() => {
    // Shuffle sentences for initial display
    const shuffled = [...sentences].sort(() => Math.random() - 0.5)
    setOrderedSentences(shuffled)
  }, [exercise.id])

  useEffect(() => {
    setUserAnswer(orderedSentences.join('. '))
  }, [orderedSentences, setUserAnswer])

  const moveUp = (index: number) => {
    if (disabled || index === 0) return
    const newOrder = [...orderedSentences]
    ;[newOrder[index - 1], newOrder[index]] = [newOrder[index], newOrder[index - 1]]
    setOrderedSentences(newOrder)
  }

  const moveDown = (index: number) => {
    if (disabled || index === orderedSentences.length - 1) return
    const newOrder = [...orderedSentences]
    ;[newOrder[index], newOrder[index + 1]] = [newOrder[index + 1], newOrder[index]]
    setOrderedSentences(newOrder)
  }

  return (
    <div className="space-y-4">
      <p className="text-sm text-muted-foreground">{question}</p>
      <div className="space-y-2">
        {orderedSentences.map((sentence, idx) => (
          <div
            key={`${sentence}-${idx}`}
            className={cn(
              'flex items-center gap-3 p-3 rounded-xl border bg-background transition-all',
              !disabled && 'hover:shadow-sm'
            )}
          >
            <div className="flex items-center gap-1 shrink-0">
              <GripVertical className="h-4 w-4 text-muted-foreground" />
              <span className="text-sm font-bold text-primary w-5">{idx + 1}</span>
            </div>
            <p className="text-sm flex-1">{sentence}</p>
            <div className="flex flex-col gap-1">
              <button
                onClick={() => moveUp(idx)}
                disabled={disabled || idx === 0}
                className="p-1 rounded hover:bg-muted disabled:opacity-30"
              >
                <ArrowUp className="h-3 w-3" />
              </button>
              <button
                onClick={() => moveDown(idx)}
                disabled={disabled || idx === orderedSentences.length - 1}
                className="p-1 rounded hover:bg-muted disabled:opacity-30"
              >
                <ArrowDown className="h-3 w-3" />
              </button>
            </div>
          </div>
        ))}
      </div>
    </div>
  )
}