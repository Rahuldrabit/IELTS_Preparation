'use client'

import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Badge } from '@/components/ui/badge'
import { Headphones, Send } from 'lucide-react'
import { useMockTestStore } from '@/lib/store/mockTestStore'
import type { SectionContentData } from '@/lib/services/mocktest'

interface Props {
  content: SectionContentData
  onSubmit: () => void
}

export function MockTestListeningSection({ content, onSubmit }: Props) {
  const { listeningAnswers, setListeningAnswer } = useMockTestStore()
  const sections = content.sections || []

  return (
    <div className="space-y-6">
      <div className="flex items-center gap-3">
        <Headphones className="h-6 w-6 text-green-500" />
        <h2 className="text-xl font-semibold">Listening Section</h2>
        <Badge variant="outline">
          {Object.keys(listeningAnswers).length} / {content.total_questions || 20} answered
        </Badge>
      </div>

      {sections.map((section) => (
        <Card key={section.section_number}>
          <CardHeader>
            <CardTitle className="text-base">
              Section {section.section_number}: {section.title}
            </CardTitle>
          </CardHeader>
          <CardContent className="space-y-4">
            {/* Transcript display (exam would play audio) */}
            <div className="p-4 rounded-lg bg-muted/50 text-sm max-h-48 overflow-y-auto whitespace-pre-wrap">
              {section.transcript}
            </div>

            {/* Questions */}
            <div className="space-y-3">
              {section.questions.map((q) => (
                <div key={q.id} className="p-3 rounded-lg border">
                  <p className="text-sm font-medium mb-2">{q.id}. {q.text}</p>
                  {q.options ? (
                    <div className="grid grid-cols-1 gap-1">
                      {q.options.map((opt, idx) => (
                        <label
                          key={idx}
                          className="flex items-center gap-2 p-2 rounded hover:bg-muted/50 cursor-pointer text-sm"
                        >
                          <input
                            type="radio"
                            name={`q-${q.id}`}
                            value={opt.charAt(0)}
                            checked={listeningAnswers[String(q.id)] === opt.charAt(0)}
                            onChange={(e) => setListeningAnswer(String(q.id), e.target.value)}
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
                      value={listeningAnswers[String(q.id)] || ''}
                      onChange={(e) => setListeningAnswer(String(q.id), e.target.value)}
                      className="w-full p-2 rounded border bg-background text-sm"
                    />
                  )}
                </div>
              ))}
            </div>
          </CardContent>
        </Card>
      ))}

      <div className="flex justify-end">
        <Button onClick={onSubmit} size="lg">
          <Send className="h-4 w-4 mr-2" />
          Submit Listening &amp; Continue
        </Button>
      </div>
    </div>
  )
}
