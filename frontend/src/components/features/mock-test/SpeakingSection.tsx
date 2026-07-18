'use client'

import { useState } from 'react'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Badge } from '@/components/ui/badge'
import { Mic, Send, MessageCircle } from 'lucide-react'
import { cn } from '@/lib/utils'
import { useMockTestStore } from '@/lib/store/mockTestStore'
import type { SectionContentData } from '@/lib/services/mocktest'

interface Props {
  content: SectionContentData
  onSubmit: () => void
}

export function MockTestSpeakingSection({ content, onSubmit }: Props) {
  const { speakingAnswers, setSpeakingAnswer } = useMockTestStore()
  const parts = content.parts || []
  const [activePart, setActivePart] = useState(0)

  const currentPart = parts[activePart]
  if (!currentPart) return null

  return (
    <div className="space-y-4">
      <div className="flex items-center gap-3">
        <Mic className="h-6 w-6 text-purple-500" />
        <h2 className="text-xl font-semibold">Speaking Section</h2>
      </div>

      {/* Part tabs */}
      <div className="flex gap-2">
        {parts.map((p, idx) => (
          <button
            key={idx}
            onClick={() => setActivePart(idx)}
            className={cn(
              'px-4 py-2 rounded-lg text-sm font-medium transition-all',
              activePart === idx
                ? 'bg-primary text-primary-foreground'
                : 'bg-muted hover:bg-muted/80'
            )}
          >
            Part {p.part_number}
          </button>
        ))}
      </div>

      <Card>
        <CardHeader>
          <CardTitle className="text-base flex items-center gap-2">
            <MessageCircle className="h-4 w-4" />
            {currentPart.title}
          </CardTitle>
        </CardHeader>
        <CardContent className="space-y-4">
          {/* Cue card for Part 2 */}
          {currentPart.cue_card && (
            <div className="p-4 rounded-lg bg-yellow-500/10 border border-yellow-500/20 text-sm whitespace-pre-wrap">
              {currentPart.cue_card}
            </div>
          )}

          {/* Questions for Part 1 and 3 */}
          {currentPart.questions?.map((question, idx) => (
            <div key={idx} className="space-y-2">
              <p className="text-sm font-medium">{idx + 1}. {question}</p>
              <textarea
                value={speakingAnswers[`part_${currentPart.part_number}`]?.[`q_${idx}`] || ''}
                onChange={(e) =>
                  setSpeakingAnswer(
                    `part_${currentPart.part_number}`,
                    `q_${idx}`,
                    e.target.value
                  )
                }
                placeholder="Type your spoken response here (or record audio)..."
                className="w-full h-24 p-3 rounded-lg border bg-background text-sm resize-none focus:outline-none focus:ring-2 focus:ring-ring"
              />
            </div>
          ))}

          {/* Part 2 response area */}
          {currentPart.cue_card && (
            <div className="space-y-2">
              <p className="text-sm font-medium">Your response:</p>
              <textarea
                value={speakingAnswers[`part_${currentPart.part_number}`]?.['response'] || ''}
                onChange={(e) =>
                  setSpeakingAnswer(
                    `part_${currentPart.part_number}`,
                    'response',
                    e.target.value
                  )
                }
                placeholder="Type your 2-minute response here..."
                className="w-full h-40 p-3 rounded-lg border bg-background text-sm resize-none focus:outline-none focus:ring-2 focus:ring-ring"
              />
            </div>
          )}
        </CardContent>
      </Card>

      <div className="flex justify-end">
        <Button onClick={onSubmit} size="lg">
          <Send className="h-4 w-4 mr-2" />
          Submit Speaking &amp; Finish Test
        </Button>
      </div>
    </div>
  )
}
