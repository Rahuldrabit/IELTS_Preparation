'use client'

import { useState } from 'react'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Badge } from '@/components/ui/badge'
import { BookOpen, Send } from 'lucide-react'
import { cn } from '@/lib/utils'
import { useMockTestStore } from '@/lib/store/mockTestStore'
import type { SectionContentData } from '@/lib/services/mocktest'

interface Props {
  content: SectionContentData
  onSubmit: () => void
}

export function MockTestReadingSection({ content, onSubmit }: Props) {
  const { readingAnswers, setReadingAnswer } = useMockTestStore()
  const passages = content.passages || []
  const [activePassage, setActivePassage] = useState(0)

  const currentPassage = passages[activePassage]
  if (!currentPassage) return null

  return (
    <div className="space-y-4">
      <div className="flex items-center gap-3">
        <BookOpen className="h-6 w-6 text-blue-500" />
        <h2 className="text-xl font-semibold">Reading Section</h2>
        <Badge variant="outline">
          {Object.keys(readingAnswers).length} / {content.total_questions || 20} answered
        </Badge>
      </div>

      {/* Passage tabs */}
      <div className="flex gap-2">
        {passages.map((p, idx) => (
          <button
            key={idx}
            onClick={() => setActivePassage(idx)}
            className={cn(
              'px-4 py-2 rounded-lg text-sm font-medium transition-all',
              activePassage === idx
                ? 'bg-primary text-primary-foreground'
                : 'bg-muted hover:bg-muted/80'
            )}
          >
            Passage {p.passage_number}
            <span className="ml-1 text-xs opacity-70">({p.difficulty})</span>
          </button>
        ))}
      </div>

      {/* Split pane: passage + questions */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
        {/* Passage */}
        <Card className="h-[600px] overflow-y-auto">
          <CardHeader>
            <CardTitle className="text-base">{currentPassage.title}</CardTitle>
            <Badge variant="outline" className="w-fit">{currentPassage.difficulty}</Badge>
          </CardHeader>
          <CardContent>
            <div className="text-sm leading-relaxed whitespace-pre-wrap">
              {currentPassage.content}
            </div>
          </CardContent>
        </Card>

        {/* Questions */}
        <Card className="h-[600px] overflow-y-auto">
          <CardHeader>
            <CardTitle className="text-base">Questions</CardTitle>
          </CardHeader>
          <CardContent className="space-y-4">
            {currentPassage.questions.map((q) => (
              <div key={q.id} className="p-3 rounded-lg border">
                <p className="text-sm font-medium mb-2">{q.id}. {q.text}</p>
                {q.options ? (
                  <div className="space-y-1">
                    {q.options.map((opt, idx) => (
                      <label
                        key={idx}
                        className="flex items-center gap-2 p-2 rounded hover:bg-muted/50 cursor-pointer text-sm"
                      >
                        <input
                          type="radio"
                          name={`rq-${q.id}`}
                          value={typeof opt === 'string' && opt.length <= 3 ? opt : opt.charAt(0)}
                          checked={readingAnswers[String(q.id)] === (typeof opt === 'string' && opt.length <= 3 ? opt : opt.charAt(0))}
                          onChange={(e) => setReadingAnswer(String(q.id), e.target.value)}
                          className="shrink-0"
                        />
                        {opt}
                      </label>
                    ))}
                  </div>
                ) : (
                  <input
                    type="text"
                    placeholder="Type your answer..."
                    value={readingAnswers[String(q.id)] || ''}
                    onChange={(e) => setReadingAnswer(String(q.id), e.target.value)}
                    className="w-full p-2 rounded border bg-background text-sm"
                  />
                )}
              </div>
            ))}
          </CardContent>
        </Card>
      </div>

      <div className="flex justify-end">
        <Button onClick={onSubmit} size="lg">
          <Send className="h-4 w-4 mr-2" />
          Submit Reading &amp; Continue
        </Button>
      </div>
    </div>
  )
}
