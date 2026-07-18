'use client'

import { useState, useEffect } from 'react'
import { cn } from '@/lib/utils'
import type { ExerciseData } from '@/lib/types/grammar'

interface Props {
  exercise: ExerciseData
  userAnswer: string
  setUserAnswer: (val: string) => void
  disabled: boolean
}

export function DragAndDrop({ exercise, userAnswer, setUserAnswer, disabled }: Props) {
  const question = exercise.question_data?.question || 'Arrange the words to form a correct sentence'
  const words: string[] = exercise.question_data?.words || exercise.correct_answer.split(' ')
  
  const [selectedWords, setSelectedWords] = useState<string[]>([])
  const [availableWords, setAvailableWords] = useState<string[]>([])

  useEffect(() => {
    // Shuffle words for initial display
    const shuffled = [...words].sort(() => Math.random() - 0.5)
    setAvailableWords(shuffled)
    setSelectedWords([])
  }, [exercise.id])

  useEffect(() => {
    setUserAnswer(selectedWords.join(' '))
  }, [selectedWords, setUserAnswer])

  const handleSelectWord = (word: string, index: number) => {
    if (disabled) return
    setSelectedWords(prev => [...prev, word])
    setAvailableWords(prev => prev.filter((_, i) => i !== index))
  }

  const handleRemoveWord = (word: string, index: number) => {
    if (disabled) return
    setAvailableWords(prev => [...prev, word])
    setSelectedWords(prev => prev.filter((_, i) => i !== index))
  }

  return (
    <div className="space-y-4">
      <p className="text-sm text-muted-foreground">{question}</p>
      
      {/* Constructed sentence area */}
      <div className="min-h-[60px] p-4 rounded-xl border-2 border-dashed border-primary/30 bg-primary/5">
        <p className="text-xs text-muted-foreground mb-2">Your sentence:</p>
        <div className="flex flex-wrap gap-2">
          {selectedWords.length === 0 ? (
            <p className="text-sm text-muted-foreground italic">Click words below to build your sentence...</p>
          ) : (
            selectedWords.map((word, idx) => (
              <button
                key={`selected-${idx}`}
                onClick={() => handleRemoveWord(word, idx)}
                disabled={disabled}
                className={cn(
                  'px-3 py-1.5 rounded-lg text-sm font-medium bg-primary text-primary-foreground transition-all hover:opacity-80',
                  disabled && 'cursor-not-allowed opacity-50'
                )}
              >
                {word}
              </button>
            ))
          )}
        </div>
      </div>
      
      {/* Available words */}
      <div className="p-4 rounded-xl bg-muted/50 border">
        <p className="text-xs text-muted-foreground mb-2">Available words:</p>
        <div className="flex flex-wrap gap-2">
          {availableWords.map((word, idx) => (
            <button
              key={`available-${idx}`}
              onClick={() => handleSelectWord(word, idx)}
              disabled={disabled}
              className={cn(
                'px-3 py-1.5 rounded-lg text-sm font-medium bg-background border border-border transition-all hover:border-primary hover:bg-primary/5',
                disabled && 'cursor-not-allowed opacity-50'
              )}
            >
              {word}
            </button>
          ))}
        </div>
      </div>
    </div>
  )
}