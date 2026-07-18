'use client'

import type { ExerciseData } from '@/lib/types/grammar'
import { Badge } from '@/components/ui/badge'

interface Props {
  exercise: ExerciseData
  userAnswer: string
  setUserAnswer: (val: string) => void
  disabled: boolean
}

export function GrammarTransformation({ exercise, userAnswer, setUserAnswer, disabled }: Props) {
  const originalSentence = exercise.question_data?.sentence || exercise.question_data?.question || ''
  const transformation = exercise.question_data?.transformation || 'Transform the sentence'
  const hint = exercise.question_data?.hint || ''

  return (
    <div className="space-y-4">
      <p className="text-sm text-muted-foreground">Transform the sentence as instructed:</p>
      
      <div className="p-4 rounded-xl bg-muted/50 border">
        <p className="text-xs text-muted-foreground mb-1">Original sentence</p>
        <p className="text-lg leading-relaxed">{originalSentence}</p>
      </div>

      <div className="p-3 rounded-lg bg-amber-500/5 border border-amber-500/20">
        <p className="text-sm">
          <span className="font-medium">Transformation:</span> {transformation}
        </p>
      </div>

      {hint && (
        <div className="flex items-center gap-2">
          <Badge variant="outline" className="text-xs">Hint</Badge>
          <span className="text-xs text-muted-foreground">{hint}</span>
        </div>
      )}

      <div>
        <label className="text-sm font-medium mb-2 block">Your transformed sentence:</label>
        <textarea
          value={userAnswer}
          onChange={(e) => setUserAnswer(e.target.value)}
          disabled={disabled}
          placeholder="Write the transformed sentence..."
          rows={3}
          className="w-full p-3 rounded-xl border border-input bg-background text-sm leading-relaxed resize-none focus:outline-none focus:ring-2 focus:ring-ring disabled:opacity-50"
        />
      </div>
    </div>
  )
}