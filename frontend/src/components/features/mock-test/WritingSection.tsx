'use client'

import { useState } from 'react'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Badge } from '@/components/ui/badge'
import { PenTool, Send } from 'lucide-react'
import { cn } from '@/lib/utils'
import { useMockTestStore } from '@/lib/store/mockTestStore'
import type { SectionContentData } from '@/lib/services/mocktest'

interface Props {
  content: SectionContentData
  onSubmit: () => void
}

export function MockTestWritingSection({ content, onSubmit }: Props) {
  const { writingAnswers, setWritingAnswer } = useMockTestStore()
  const tasks = content.tasks || []
  const [activeTask, setActiveTask] = useState(0)

  const currentTask = tasks[activeTask]
  if (!currentTask) return null

  const wordCount = (text: string) => text.trim().split(/\s+/).filter(Boolean).length

  return (
    <div className="space-y-4">
      <div className="flex items-center gap-3">
        <PenTool className="h-6 w-6 text-orange-500" />
        <h2 className="text-xl font-semibold">Writing Section</h2>
      </div>

      {/* Task tabs */}
      <div className="flex gap-2">
        {tasks.map((t, idx) => (
          <button
            key={idx}
            onClick={() => setActiveTask(idx)}
            className={cn(
              'px-4 py-2 rounded-lg text-sm font-medium transition-all',
              activeTask === idx
                ? 'bg-primary text-primary-foreground'
                : 'bg-muted hover:bg-muted/80'
            )}
          >
            Task {t.task_number}
            <span className="ml-1 text-xs opacity-70">
              ({t.task_type === 'task_1' ? '20 min' : '40 min'})
            </span>
          </button>
        ))}
      </div>

      {/* Writing workspace */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
        {/* Prompt */}
        <Card>
          <CardHeader>
            <CardTitle className="text-base">
              {currentTask.task_type === 'task_1' ? 'Task 1' : 'Task 2'}
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="p-4 rounded-lg bg-muted/50 text-sm leading-relaxed whitespace-pre-wrap">
              {currentTask.prompt}
            </div>
            <p className="text-xs text-muted-foreground mt-3">
              Minimum {currentTask.min_words} words
            </p>
          </CardContent>
        </Card>

        {/* Editor */}
        <Card>
          <CardHeader>
            <div className="flex items-center justify-between">
              <CardTitle className="text-base">Your Response</CardTitle>
              <Badge
                variant={
                  wordCount(writingAnswers[currentTask.task_type] || '') >= currentTask.min_words
                    ? 'default'
                    : 'secondary'
                }
              >
                {wordCount(writingAnswers[currentTask.task_type] || '')} words
              </Badge>
            </div>
          </CardHeader>
          <CardContent>
            <textarea
              value={writingAnswers[currentTask.task_type] || ''}
              onChange={(e) => setWritingAnswer(currentTask.task_type, e.target.value)}
              placeholder={`Write your ${currentTask.task_type === 'task_1' ? 'report' : 'essay'} here...`}
              className="w-full h-[400px] p-4 rounded-lg border bg-background text-sm leading-relaxed resize-none focus:outline-none focus:ring-2 focus:ring-ring"
            />
          </CardContent>
        </Card>
      </div>

      <div className="flex justify-end">
        <Button onClick={onSubmit} size="lg">
          <Send className="h-4 w-4 mr-2" />
          Submit Writing &amp; Continue
        </Button>
      </div>
    </div>
  )
}
