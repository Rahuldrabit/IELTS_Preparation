'use client'

import type { ExerciseData } from '@/lib/types/grammar'

interface Props {
  exercise: ExerciseData
  userAnswer: string
  setUserAnswer: (val: string) => void
  disabled: boolean
}

export function RewriteSentence({ exercise, userAnswer, setUserAnswer, disabled }: Props) {
  const originalSentence = exercise.question_data?.sentence || ''
  const instruction = exercise.question_data?.instruction || exercise.question_data?.question || 'Rewrite the sentence'

  return (
    <div className="space-y-4">
      <p className="text-sm text-muted-foreground">{instruction}</p>
      <div className="p-4 rounded-xl bg-muted/50 border">
        <p className="text-xs text-muted-foreground mb-1">Original sentence</p>
        <p className="text-lg leading-relaxed">{originalSentence}</p>
      </div>
      <div>
        <label className="text-sm font-medium mb-2 block">Your rewritten sentence:</label>
        <textarea
          value={userAnswer}
          onChange={(e) => setUserAnswer(e.target.value)}
          disabled={disabled}
          placeholder="Rewrite the sentence here..."
          rows={3}
          className="w-full p-3 rounded-xl border border-input bg-background text-sm leading-relaxed resize-none focus:outline-none focus:ring-2 focus:ring-ring disabled:opacity-50"
        />
      </div>
    </div>
  )
}