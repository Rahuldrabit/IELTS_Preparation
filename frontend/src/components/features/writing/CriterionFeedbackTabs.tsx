'use client'

import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs'
import { Card, CardContent } from '@/components/ui/card'
import { Progress } from '@/components/ui/progress'
import { Lightbulb, Target, BookOpen, PenTool } from 'lucide-react'
import { cn } from '@/lib/utils'
import type { CriterionFeedback } from '@/lib/services/writing'

// ─────────────────────────────────────────────
//  Props
// ─────────────────────────────────────────────

interface CriterionFeedbackTabsProps {
  feedback: CriterionFeedback[]
}

// ─────────────────────────────────────────────
//  Config
// ─────────────────────────────────────────────

const CRITERION_CONFIG: Record<string, { label: string; icon: typeof Target; color: string }> = {
  task_response: { label: 'Task Response', icon: Target, color: 'text-blue-500' },
  coherence: { label: 'Coherence & Cohesion', icon: BookOpen, color: 'text-green-500' },
  lexical: { label: 'Lexical Resource', icon: PenTool, color: 'text-purple-500' },
  grammar: { label: 'Grammar', icon: Lightbulb, color: 'text-orange-500' },
}

// ─────────────────────────────────────────────
//  Component
// ─────────────────────────────────────────────

export function CriterionFeedbackTabs({ feedback }: CriterionFeedbackTabsProps) {
  if (!feedback || feedback.length === 0) return null

  return (
    <Tabs defaultValue={feedback[0]?.criterion || 'task_response'}>
      <TabsList className="w-full grid grid-cols-4 h-auto p-1 bg-muted/50">
        {feedback.map((cf) => {
          const config = CRITERION_CONFIG[cf.criterion] || CRITERION_CONFIG.task_response
          return (
            <TabsTrigger
              key={cf.criterion}
              value={cf.criterion}
              className="flex flex-col items-center gap-1 py-2 px-1 data-[state=active]:bg-primary data-[state=active]:text-primary-foreground"
            >
              <span className="text-xs font-medium">{config.label}</span>
              <span className="text-sm font-bold">{cf.band.toFixed(1)}</span>
            </TabsTrigger>
          )
        })}
      </TabsList>

      {feedback.map((cf) => (
        <TabsContent key={cf.criterion} value={cf.criterion} className="mt-4">
          <CriterionCard criterion={cf} />
        </TabsContent>
      ))}
    </Tabs>
  )
}

// ─────────────────────────────────────────────
//  Criterion Card
// ─────────────────────────────────────────────

function CriterionCard({ criterion }: { criterion: CriterionFeedback }) {
  const config = CRITERION_CONFIG[criterion.criterion] || CRITERION_CONFIG.task_response

  return (
    <Card>
      <CardContent className="p-4 space-y-4">
        {/* Band score */}
        <div className="flex items-center justify-between">
          <span className={cn('text-sm font-medium', config.color)}>
            {config.label}
          </span>
          <span className="text-2xl font-bold">Band {criterion.band.toFixed(1)}</span>
        </div>
        <Progress value={(criterion.band / 9) * 100} className="h-2" />

        {/* Explanation */}
        <div className="p-3 rounded-xl bg-muted/50">
          <p className="text-sm leading-relaxed">{criterion.explanation}</p>
        </div>

        {/* Improvement tip */}
        {criterion.improvement_tip && (
          <div className="p-3 rounded-xl bg-primary/5 border border-primary/20">
            <div className="flex items-start gap-2">
              <Lightbulb className="h-4 w-4 text-primary shrink-0 mt-0.5" />
              <div>
                <p className="text-xs font-medium text-primary mb-1">Improvement Tip</p>
                <p className="text-sm">{criterion.improvement_tip}</p>
              </div>
            </div>
          </div>
        )}
      </CardContent>
    </Card>
  )
}
