'use client'

import type { ExerciseData } from '@/lib/types/grammar'

interface Props {
  exercise: ExerciseData
  userAnswer: string
  setUserAnswer: (val: string) => void
  disabled: boolean
}

export function ErrorCorrection({ exercise, userAnswer, setUserAnswer, disabled }: Props) {
  const sentence = exercise.question_data?.sentence || exercise.question_data?.question || ''

  return (
    <div className="space-y-4">
      <p className="text-sm text-muted-foreground">
        The following sentence contains a grammar error. Rewrite it correctly:
      </p>
      <div className="p-4 rounded-xl bg-destructive/5 border border-destructive/20">
        <p className="text-lg leading-relaxed text-destructive">{sentence}</p>
      </div>
      <div>
        <label className="text-sm font-medium mb-2 block">Your corrected sentence:</label>
        <textarea
          value={userAnswer}
          onChange={(e) => setUserAnswer(e.target.value)}
          disabled={disabled}
          placeholder="Type the corrected sentence here..."
          rows={3}
          className="w-full p-3 rounded-xl border border-input bg-background text-sm leading-relaxed resize-none focus:outline-none focus:ring-2 focus:ring-ring disabled:opacity-50"
        />
      </div>
    </div>
  )
}