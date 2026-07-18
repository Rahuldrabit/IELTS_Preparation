'use client'

import { cn } from '@/lib/utils'
import type { ExerciseData } from '@/lib/types/grammar'

interface Props {
  exercise: ExerciseData
  userAnswer: string
  setUserAnswer: (val: string) => void
  disabled: boolean
}

export function MultipleChoice({ exercise, userAnswer, setUserAnswer, disabled }: Props) {
  const question = exercise.question_data?.question || 'Choose the correct answer'
  const options: string[] = exercise.question_data?.options || ['A', 'B', 'C', 'D']

  return (
    <div className="space-y-4">
      <p className="text-sm text-muted-foreground">Choose the correct answer:</p>
      <div className="p-4 rounded-xl bg-muted/50 border">
        <p className="text-lg leading-relaxed">{question}</p>
      </div>
      <div className="grid gap-3">
        {options.map((option, idx) => (
          <button
            key={idx}
            onClick={() => !disabled && setUserAnswer(option)}
            disabled={disabled}
            className={cn(
              'w-full p-4 rounded-xl border text-left transition-all text-sm',
              userAnswer === option
                ? 'border-primary bg-primary/5 ring-2 ring-primary/20'
                : 'border-border hover:border-primary/50 hover:bg-muted/50',
              disabled && 'cursor-not-allowed opacity-50'
            )}
          >
            <div className="flex items-center gap-3">
              <div className={cn(
                'h-6 w-6 rounded-full border-2 flex items-center justify-center shrink-0',
                userAnswer === option ? 'border-primary bg-primary text-primary-foreground' : 'border-muted-foreground/30'
              )}>
                {userAnswer === option && (
                  <div className="h-2 w-2 rounded-full bg-current" />
                )}
              </div>
              <span>{option}</span>
            </div>
          </button>
        ))}
      </div>
    </div>
  )
}