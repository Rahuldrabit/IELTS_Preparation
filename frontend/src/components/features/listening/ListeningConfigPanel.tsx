'use client'

import { useState } from 'react'
import { motion } from 'framer-motion'
import {
  Headphones, Globe, Gauge, BookOpen, Plus, X, Sparkles, Activity,
} from 'lucide-react'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Badge } from '@/components/ui/badge'
import { cn } from '@/lib/utils'
import { SessionFeatureBar } from '@/components/ui/SessionFeatureBar'

// ─────────────────────────────────────────────
//  Options
// ─────────────────────────────────────────────

const SECTION_OPTIONS = [
  { value: 1, label: 'Section 1', description: 'Everyday conversation' },
  { value: 2, label: 'Section 2', description: 'Social monologue' },
  { value: 3, label: 'Section 3', description: 'Educational discussion' },
  { value: 4, label: 'Section 4', description: 'Academic lecture' },
]

const ACCENT_OPTIONS = [
  { value: 'british', label: '🇬🇧 British' },
  { value: 'australian', label: '🇦🇺 Australian' },
  { value: 'american', label: '🇺🇸 American' },
]

const SPEED_OPTIONS = [
  { value: 'normal', label: 'Normal' },
  { value: 'exam', label: 'Exam Pace' },
  { value: 'fast', label: 'Fast' },
]

const TOPIC_OPTIONS = [
  'Hotel Booking', 'Course Enrolment', 'Tour Description', 'Library Events',
  'University Lecture', 'Research Discussion', 'Health & Fitness', 'Travel',
  'Environment', 'Technology', 'Business', 'Random',
]

const QUESTION_TYPE_OPTIONS = [
  'FILL_BLANK', 'MULTIPLE_CHOICE', 'MATCHING_INFORMATION',
]

// ─────────────────────────────────────────────
//  Props
// ─────────────────────────────────────────────

interface ListeningConfigPanelProps {
  onGenerate: (config: {
    section: number
    accent: string
    speed: string
    topic: string
    weakness_focus: string[]
    question_types: string[]
    question_count: number
  }) => void
  isGenerating?: boolean
}

// ─────────────────────────────────────────────
//  Component
// ─────────────────────────────────────────────

export function ListeningConfigPanel({ onGenerate, isGenerating = false }: ListeningConfigPanelProps) {
  const [section, setSection] = useState(1)
  const [accent, setAccent] = useState('british')
  const [speed, setSpeed] = useState('normal')
  const [topic, setTopic] = useState('Hotel Booking')
  const [questionTypes, setQuestionTypes] = useState<string[]>(['FILL_BLANK'])
  const [questionCount, setQuestionCount] = useState(8)

  const addQuestionType = (type: string) => {
    if (!questionTypes.includes(type)) setQuestionTypes([...questionTypes, type])
  }

  const removeQuestionType = (type: string) => {
    setQuestionTypes(questionTypes.filter((t) => t !== type))
  }

  const handleGenerate = () => {
    onGenerate({
      section,
      accent,
      speed,
      topic,
      weakness_focus: [],
      question_types: questionTypes,
      question_count: questionCount,
    })
  }

  return (
    <motion.div
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      exit={{ opacity: 0, y: -20 }}
    >
      <Card className="max-w-4xl mx-auto">
        <CardHeader>
          <div className="flex items-center gap-3">
            <div className="h-12 w-12 rounded-xl bg-green-500/10 flex items-center justify-center">
              <Headphones className="h-6 w-6 text-green-500" />
            </div>
            <div>
              <CardTitle className="text-xl">Generate Listening Practice</CardTitle>
              <p className="text-sm text-muted-foreground">
                Configure your IELTS listening test
              </p>
            </div>
          </div>
        </CardHeader>

        <CardContent className="space-y-6">
          {/* Section */}
          <div className="space-y-2">
            <label className="text-sm font-medium flex items-center gap-2">
              <BookOpen className="h-4 w-4" />
              Section
            </label>
            <div className="grid grid-cols-2 sm:grid-cols-4 gap-2">
              {SECTION_OPTIONS.map((opt) => (
                <button
                  key={opt.value}
                  onClick={() => setSection(opt.value)}
                  className={cn(
                    'p-3 rounded-lg text-sm border transition-all text-center',
                    section === opt.value
                      ? 'bg-green-500 text-white border-green-500'
                      : 'bg-muted/50 border-border hover:bg-muted'
                  )}
                >
                  <div className="font-medium">{opt.label}</div>
                  <div className="text-xs opacity-70">{opt.description}</div>
                </button>
              ))}
            </div>
          </div>

          {/* Accent */}
          <div className="space-y-2">
            <label className="text-sm font-medium flex items-center gap-2">
              <Globe className="h-4 w-4" />
              Accent
            </label>
            <div className="grid grid-cols-3 gap-2">
              {ACCENT_OPTIONS.map((opt) => (
                <button
                  key={opt.value}
                  onClick={() => setAccent(opt.value)}
                  className={cn(
                    'p-3 rounded-lg text-sm border transition-all text-center',
                    accent === opt.value
                      ? 'bg-primary text-primary-foreground border-primary'
                      : 'bg-muted/50 border-border hover:bg-muted'
                  )}
                >
                  {opt.label}
                </button>
              ))}
            </div>
          </div>

          {/* Speed */}
          <div className="space-y-2">
            <label className="text-sm font-medium flex items-center gap-2">
              <Gauge className="h-4 w-4" />
              Speed
            </label>
            <div className="grid grid-cols-3 gap-2">
              {SPEED_OPTIONS.map((opt) => (
                <button
                  key={opt.value}
                  onClick={() => setSpeed(opt.value)}
                  className={cn(
                    'p-2 rounded-lg text-sm border transition-all text-center',
                    speed === opt.value
                      ? 'bg-primary text-primary-foreground border-primary'
                      : 'bg-muted/50 border-border hover:bg-muted'
                  )}
                >
                  {opt.label}
                </button>
              ))}
            </div>
          </div>

          {/* Topic */}
          <div className="space-y-2">
            <label className="text-sm font-medium">Topic</label>
            <div className="flex flex-wrap gap-2">
              {TOPIC_OPTIONS.map((opt) => (
                <button
                  key={opt}
                  onClick={() => setTopic(opt)}
                  className={cn(
                    'px-3 py-1.5 rounded-lg text-sm border transition-all',
                    topic === opt
                      ? 'bg-primary text-primary-foreground border-primary'
                      : 'bg-muted/50 border-border hover:bg-muted'
                  )}
                >
                  {opt}
                </button>
              ))}
            </div>
          </div>

          {/* Question Count */}
          <div className="space-y-2">
            <label className="text-sm font-medium">Number of Questions</label>
            <div className="flex gap-2">
              {[6, 8, 10].map((n) => (
                <button
                  key={n}
                  onClick={() => setQuestionCount(n)}
                  className={cn(
                    'px-4 py-2 rounded-lg text-sm border transition-all',
                    questionCount === n
                      ? 'bg-primary text-primary-foreground border-primary'
                      : 'bg-muted/50 border-border hover:bg-muted'
                  )}
                >
                  {n}
                </button>
              ))}
            </div>
          </div>

          {/* Question Types */}
          <div className="space-y-2">
            <label className="text-sm font-medium">Question Types</label>
            <div className="space-y-2">
              {questionTypes.map((qt) => (
                <div
                  key={qt}
                  className="flex items-center gap-3 p-2 rounded-lg border bg-muted/30"
                >
                  <Badge variant="outline">{qt.replace(/_/g, ' ')}</Badge>
                  <button
                    onClick={() => removeQuestionType(qt)}
                    className="ml-auto p-1 rounded hover:bg-destructive/10"
                  >
                    <X className="h-3 w-3" />
                  </button>
                </div>
              ))}
              {questionTypes.length < 2 && (
                <div className="flex flex-wrap gap-2">
                  {QUESTION_TYPE_OPTIONS.filter((t) => !questionTypes.includes(t)).map((t) => (
                    <Button key={t} variant="outline" size="sm" onClick={() => addQuestionType(t)} className="gap-1">
                      <Plus className="h-3 w-3" />
                      {t.replace(/_/g, ' ')}
                    </Button>
                  ))}
                </div>
              )}
            </div>
          </div>

          {/* Generate Button */}
          <SessionFeatureBar
            skill="listening"
            features={[
              {
                featureKey: 'acousticLevel',
                label: 'Acoustic',
                icon: Headphones,
                options: [
                  { value: 1, label: 'Studio' },
                  { value: 2, label: 'Exam Room' },
                ],
              },
              { featureKey: 'telemetry', label: 'Playback Log', icon: Activity },
            ]}
          />
          <Button
            onClick={handleGenerate}
            disabled={isGenerating || questionTypes.length === 0}
            className="w-full mt-4"
            size="lg"
          >
            {isGenerating ? (
              <>
                <span className="animate-spin mr-2">⏳</span>
                Generating...
              </>
            ) : (
              <>
                <Sparkles className="h-4 w-4 mr-2" />
                Generate Listening Test
              </>
            )}
          </Button>
        </CardContent>
      </Card>
    </motion.div>
  )
}
