'use client'

import type { ExerciseData } from '@/lib/types/grammar'

interface Props {
  exercise: ExerciseData
  userAnswer: string
  setUserAnswer: (val: string) => void
  disabled: boolean
}

export function FillInBlank({ exercise, userAnswer, setUserAnswer, disabled }: Props) {
  const question = exercise.question_data?.question || 'Fill in the blank'
  const sentence = exercise.question_data?.sentence || question

  return (
    <div className="space-y-4">
      <p className="text-sm text-muted-foreground">Fill in the blank with the correct word or phrase:</p>
      <div className="p-4 rounded-xl bg-muted/50 border">
        <p className="text-lg leading-relaxed">{sentence}</p>
      </div>
      <input
        type="text"
        value={userAnswer}
        onChange={(e) => setUserAnswer(e.target.value)}
        disabled={disabled}
        placeholder="Type your answer here..."
        className="w-full p-3 rounded-xl border border-input bg-background text-sm focus:outline-none focus:ring-2 focus:ring-ring disabled:opacity-50"
        onKeyDown={(e) => e.key === 'Enter' && !disabled && userAnswer.trim() && e.preventDefault()}
      />
    </div>
  )
}