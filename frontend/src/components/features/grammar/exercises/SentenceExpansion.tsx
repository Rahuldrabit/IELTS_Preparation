'use client'

import type { ExerciseData } from '@/lib/types/grammar'

interface Props {
  exercise: ExerciseData
  userAnswer: string
  setUserAnswer: (val: string) => void
  disabled: boolean
}

export function SentenceExpansion({ exercise, userAnswer, setUserAnswer, disabled }: Props) {
  const baseSentence = exercise.question_data?.sentence || exercise.question_data?.question || ''
  const instruction = exercise.question_data?.instruction || 'Expand the sentence using the grammar structure indicated'
  const targetStructure = exercise.question_data?.target_structure || ''

  return (
    <div className="space-y-4">
      <p className="text-sm text-muted-foreground">{instruction}</p>
      
      <div className="p-4 rounded-xl bg-muted/50 border">
        <p className="text-xs text-muted-foreground mb-1">Base sentence</p>
        <p className="text-lg leading-relaxed">{baseSentence}</p>
      </div>

      {targetStructure && (
        <div className="p-3 rounded-lg bg-primary/5 border border-primary/10">
          <p className="text-sm">
            <span className="font-medium text-primary">Target structure:</span> {targetStructure}
          </p>
        </div>
      )}

      <div>
        <label className="text-sm font-medium mb-2 block">Your expanded sentence:</label>
        <textarea
          value={userAnswer}
          onChange={(e) => setUserAnswer(e.target.value)}
          disabled={disabled}
          placeholder="Expand the sentence using the required grammar structure..."
          rows={3}
          className="w-full p-3 rounded-xl border border-input bg-background text-sm leading-relaxed resize-none focus:outline-none focus:ring-2 focus:ring-ring disabled:opacity-50"
        />
      </div>
    </div>
  )
}