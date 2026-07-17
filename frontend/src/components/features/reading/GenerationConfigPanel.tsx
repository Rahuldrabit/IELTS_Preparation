'use client'

import { useState } from 'react'
import { motion, AnimatePresence } from 'framer-motion'
import {
  Sparkles, ChevronDown, BookOpen, GraduationCap, Languages,
  Clock, CheckCircle2, Plus, X, Activity, Brain, ShieldAlert, Loader2,
} from 'lucide-react'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Badge } from '@/components/ui/badge'
import { cn } from '@/lib/utils'
import type { QuestionTypeConfig } from '@/lib/services/reading'
import { SessionFeatureBar } from '@/components/ui/SessionFeatureBar'
import type { StudentWeaknessProfile } from '@/lib/services/reading-adversarial'

// ─────────────────────────────────────────────
//  Configuration Options
// ─────────────────────────────────────────────

const DIFFICULTY_OPTIONS = [
  { value: 'beginner', label: 'Beginner', description: 'Simple vocabulary, short sentences' },
  { value: 'intermediate', label: 'Intermediate', description: 'Standard IELTS level' },
  { value: 'advanced', label: 'Advanced', description: 'Complex structures' },
  { value: 'ielts_6', label: 'IELTS 6', description: 'Band 6 target' },
  { value: 'ielts_7', label: 'IELTS 7', description: 'Band 7 target' },
  { value: 'ielts_8', label: 'IELTS 8', description: 'Band 8 target' },
  { value: 'ielts_9', label: 'IELTS 9', description: 'Band 9 target' },
]

const VOCABULARY_OPTIONS = [
  { value: 'basic', label: 'Basic', description: 'A1-A2 words' },
  { value: 'medium', label: 'Medium', description: 'B1-B2 words' },
  { value: 'academic', label: 'Academic', description: 'IELTS academic' },
  { value: 'c1', label: 'C1', description: 'Advanced' },
  { value: 'c2', label: 'C2', description: 'Proficiency' },
]

const GRAMMAR_OPTIONS = [
  { value: 'simple', label: 'Simple', description: 'Basic sentences' },
  { value: 'medium', label: 'Medium', description: 'Mixed structures' },
  { value: 'complex', label: 'Complex', description: 'Advanced syntax' },
  { value: 'mixed', label: 'Mixed', description: 'Variety' },
]

const TOPIC_OPTIONS = [
  { value: 'environment', label: 'Environment' },
  { value: 'science', label: 'Science' },
  { value: 'history', label: 'History' },
  { value: 'technology', label: 'Technology' },
  { value: 'health', label: 'Health' },
  { value: 'education', label: 'Education' },
  { value: 'business', label: 'Business' },
  { value: 'culture', label: 'Culture' },
  { value: 'society', label: 'Society' },
  { value: 'random', label: 'Random' },
]

const PASSAGE_LENGTH_OPTIONS = [
  { value: 300, label: 'Short', description: '~300 words' },
  { value: 600, label: 'Medium', description: '~600 words' },
  { value: 900, label: 'Long', description: '~900 words' },
  { value: 1200, label: 'Extended', description: '~1200 words' },
]

const QUESTION_TYPE_OPTIONS = [
  { value: 'TRUE_FALSE_NOT_GIVEN', label: 'True / False / Not Given' },
  { value: 'MATCHING_HEADINGS', label: 'Matching Headings' },
  { value: 'SUMMARY_COMPLETION', label: 'Summary Completion' },
  { value: 'MULTIPLE_CHOICE', label: 'Multiple Choice' },
  { value: 'SENTENCE_COMPLETION', label: 'Sentence Completion' },
]

// ─────────────────────────────────────────────
//  Props
// ─────────────────────────────────────────────

interface GenerationConfigPanelProps {
  onGenerate: (config: {
    difficulty: string
    vocabulary_level: string
    grammar_complexity: string
    topic: string
    passage_length_words: number
    question_types: QuestionTypeConfig[]
  }) => void
  onGenerateAdversarial?: (profile: StudentWeaknessProfile, questionType: string) => Promise<void>
  isGenerating?: boolean
  weaknessProfile?: StudentWeaknessProfile | null
}

// ─────────────────────────────────────────────
//  Component
// ─────────────────────────────────────────────

export function GenerationConfigPanel({
  onGenerate,
  onGenerateAdversarial,
  isGenerating = false,
  weaknessProfile = null,
}: GenerationConfigPanelProps) {
  const [difficulty, setDifficulty] = useState('intermediate')
  const [vocabularyLevel, setVocabularyLevel] = useState('academic')
  const [grammarComplexity, setGrammarComplexity] = useState('medium')
  const [topic, setTopic] = useState('technology')
  const [passageLength, setPassageLength] = useState(600)
  const [questionTypes, setQuestionTypes] = useState<QuestionTypeConfig[]>([
    { type: 'TRUE_FALSE_NOT_GIVEN', count: 5 },
  ])
  const [adversarialMode, setAdversarialMode] = useState(false)
  const [isGeneratingAdversarial, setIsGeneratingAdversarial] = useState(false)

  // Add a question type
  const addQuestionType = (type: string) => {
    if (!questionTypes.find(qt => qt.type === type)) {
      setQuestionTypes([...questionTypes, { type, count: 5 }])
    }
  }

  // Remove a question type
  const removeQuestionType = (type: string) => {
    setQuestionTypes(questionTypes.filter(qt => qt.type !== type))
  }

  // Update count for a question type
  const updateQuestionCount = (type: string, count: number) => {
    setQuestionTypes(
      questionTypes.map(qt =>
        qt.type === type ? { ...qt, count } : qt
      )
    )
  }

  const handleGenerate = async () => {
    onGenerate({
      difficulty,
      vocabulary_level: vocabularyLevel,
      grammar_complexity: grammarComplexity,
      topic,
      passage_length_words: passageLength,
      question_types: questionTypes,
    })
  }

  const handleGenerateAdversarial = async () => {
    if (!onGenerateAdversarial) return
    const profile: StudentWeaknessProfile = weaknessProfile ?? {
      wrong_question_types: [],
      distractor_patterns_fallen_for: [],
      low_confidence_win_topics: [],
      avg_time_per_question_ms: 0,
      target_band: 7.0,
    }
    setIsGeneratingAdversarial(true)
    try {
      await onGenerateAdversarial(profile, questionTypes[0]?.type ?? 'TRUE_FALSE_NOT_GIVEN')
    } finally {
      setIsGeneratingAdversarial(false)
    }
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
            <div className="h-12 w-12 rounded-xl bg-primary/10 flex items-center justify-center">
              <BookOpen className="h-6 w-6 text-primary" />
            </div>
            <div>
              <CardTitle className="text-xl">Generate Reading Practice</CardTitle>
              <p className="text-sm text-muted-foreground">
                Configure your IELTS reading test
              </p>
            </div>
          </div>
        </CardHeader>

        <CardContent className="space-y-6">
          {/* Difficulty */}
          <div className="space-y-2">
            <label className="text-sm font-medium flex items-center gap-2">
              <GraduationCap className="h-4 w-4" />
              Difficulty Level
            </label>
            <div className="grid grid-cols-3 sm:grid-cols-4 lg:grid-cols-7 gap-2">
              {DIFFICULTY_OPTIONS.map((opt) => (
                <button
                  key={opt.value}
                  onClick={() => setDifficulty(opt.value)}
                  className={cn(
                    'p-2 rounded-lg text-sm border transition-all text-center',
                    difficulty === opt.value
                      ? 'bg-primary text-primary-foreground border-primary'
                      : 'bg-muted/50 border-border hover:bg-muted'
                  )}
                >
                  {opt.label}
                </button>
              ))}
            </div>
          </div>

          {/* Vocabulary */}
          <div className="space-y-2">
            <label className="text-sm font-medium flex items-center gap-2">
              <Languages className="h-4 w-4" />
              Vocabulary Level
            </label>
            <div className="grid grid-cols-3 sm:grid-cols-5 gap-2">
              {VOCABULARY_OPTIONS.map((opt) => (
                <button
                  key={opt.value}
                  onClick={() => setVocabularyLevel(opt.value)}
                  className={cn(
                    'p-2 rounded-lg text-sm border transition-all text-center',
                    vocabularyLevel === opt.value
                      ? 'bg-primary text-primary-foreground border-primary'
                      : 'bg-muted/50 border-border hover:bg-muted'
                  )}
                >
                  {opt.label}
                </button>
              ))}
            </div>
          </div>

          {/* Grammar */}
          <div className="space-y-2">
            <label className="text-sm font-medium">Grammar Complexity</label>
            <div className="grid grid-cols-2 sm:grid-cols-4 gap-2">
              {GRAMMAR_OPTIONS.map((opt) => (
                <button
                  key={opt.value}
                  onClick={() => setGrammarComplexity(opt.value)}
                  className={cn(
                    'p-2 rounded-lg text-sm border transition-all text-center',
                    grammarComplexity === opt.value
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
            <div className="grid grid-cols-3 sm:grid-cols-5 gap-2">
              {TOPIC_OPTIONS.map((opt) => (
                <button
                  key={opt.value}
                  onClick={() => setTopic(opt.value)}
                  className={cn(
                    'p-2 rounded-lg text-sm border transition-all text-center',
                    topic === opt.value
                      ? 'bg-primary text-primary-foreground border-primary'
                      : 'bg-muted/50 border-border hover:bg-muted'
                  )}
                >
                  {opt.label}
                </button>
              ))}
            </div>
          </div>

          {/* Passage Length */}
          <div className="space-y-2">
            <label className="text-sm font-medium flex items-center gap-2">
              <Clock className="h-4 w-4" />
              Passage Length
            </label>
            <div className="grid grid-cols-2 sm:grid-cols-4 gap-2">
              {PASSAGE_LENGTH_OPTIONS.map((opt) => (
                <button
                  key={opt.value}
                  onClick={() => setPassageLength(opt.value)}
                  className={cn(
                    'p-3 rounded-lg text-sm border transition-all text-center',
                    passageLength === opt.value
                      ? 'bg-primary text-primary-foreground border-primary'
                      : 'bg-muted/50 border-border hover:bg-muted'
                  )}
                >
                  <div className="font-medium">{opt.label}</div>
                  <div className="text-xs opacity-70">{opt.description}</div>
                </button>
              ))}
            </div>
          </div>

          {/* Question Types */}
          <div className="space-y-2">
            <label className="text-sm font-medium flex items-center gap-2">
              <CheckCircle2 className="h-4 w-4" />
              Question Types
            </label>
            
            {/* Selected question types */}
            <div className="space-y-2">
              {questionTypes.map((qt) => (
                <div
                  key={qt.type}
                  className="flex items-center gap-3 p-3 rounded-lg border bg-muted/30"
                >
                  <Badge variant="outline" className="shrink-0">
                    {QUESTION_TYPE_OPTIONS.find(o => o.value === qt.type)?.label || qt.type}
                  </Badge>
                  <div className="flex items-center gap-2">
                    <span className="text-sm text-muted-foreground">Count:</span>
                    <select
                      value={qt.count}
                      onChange={(e) => updateQuestionCount(qt.type, Number(e.target.value))}
                      className="bg-background border rounded px-2 py-1 text-sm"
                    >
                      {[3, 4, 5, 6, 7, 8, 10].map(n => (
                        <option key={n} value={n}>{n}</option>
                      ))}
                    </select>
                  </div>
                  <button
                    onClick={() => removeQuestionType(qt.type)}
                    className="ml-auto p-1 rounded hover:bg-destructive/10 text-muted-foreground hover:text-destructive"
                  >
                    <X className="h-4 w-4" />
                  </button>
                </div>
              ))}
            </div>

            {/* Add more question types */}
            {questionTypes.length < 3 && (
              <div className="flex flex-wrap gap-2 mt-2">
                {QUESTION_TYPE_OPTIONS.filter(
                  opt => !questionTypes.find(qt => qt.type === opt.value)
                ).map((opt) => (
                  <Button
                    key={opt.value}
                    variant="outline"
                    size="sm"
                    onClick={() => addQuestionType(opt.value)}
                    className="gap-1"
                  >
                    <Plus className="h-3 w-3" />
                    {opt.label}
                  </Button>
                ))}
              </div>
            )}
          </div>

          {/* Generate Button */}
          <div className="pt-4">
            <SessionFeatureBar
              skill="reading"
              features={[
                { featureKey: 'telemetry', label: 'Telemetry', icon: Activity },
                { featureKey: 'confidenceFlags', label: 'Confidence Insights', icon: Brain },
              ]}
              className="mb-4"
            />

            {/* Adversarial Mode Toggle */}
            {onGenerateAdversarial && (
              <div className={cn(
                'mb-4 p-4 rounded-xl border transition-all',
                adversarialMode
                  ? 'bg-red-50 dark:bg-red-950/20 border-red-200 dark:border-red-800'
                  : 'bg-muted/40 border-border'
              )}>
                <button
                  onClick={() => setAdversarialMode(v => !v)}
                  className="flex items-center justify-between w-full"
                >
                  <div className="flex items-center gap-2">
                    <ShieldAlert className={cn('h-4 w-4', adversarialMode ? 'text-red-500' : 'text-muted-foreground')} />
                    <span className={cn('text-sm font-medium', adversarialMode && 'text-red-700 dark:text-red-400')}>
                      Adversarial Mode
                    </span>
                    {weaknessProfile && weaknessProfile.wrong_question_types.length > 0 && (
                      <Badge variant="outline" className="text-xs text-red-600 border-red-300">
                        {weaknessProfile.wrong_question_types.length} weak patterns tracked
                      </Badge>
                    )}
                  </div>
                  <ChevronDown className={cn('h-4 w-4 text-muted-foreground transition-transform', adversarialMode && 'rotate-180')} />
                </button>

                <AnimatePresence>
                  {adversarialMode && (
                    <motion.div
                      initial={{ height: 0, opacity: 0 }}
                      animate={{ height: 'auto', opacity: 1 }}
                      exit={{ height: 0, opacity: 0 }}
                      transition={{ duration: 0.2 }}
                      className="overflow-hidden"
                    >
                      <div className="mt-3 space-y-3">
                        <p className="text-xs text-muted-foreground leading-relaxed">
                          Generates a reading test with targeted cognitive traps based on your personal error history.
                          Questions are intentionally designed to expose your specific blind spots.
                        </p>

                        {weaknessProfile && weaknessProfile.distractor_patterns_fallen_for.length > 0 ? (
                          <div className="flex flex-wrap gap-1.5">
                            {weaknessProfile.distractor_patterns_fallen_for.map(p => (
                              <span key={p} className="text-xs px-2 py-0.5 rounded-full bg-red-100 dark:bg-red-900/30 text-red-700 dark:text-red-300 border border-red-300">
                                {p.replace(/_/g, ' ')}
                              </span>
                            ))}
                          </div>
                        ) : (
                          <p className="text-xs text-amber-600 dark:text-amber-400 italic">
                            No weakness patterns tracked yet. Complete more sessions for targeted traps.
                            A general adversarial set will be generated.
                          </p>
                        )}

                        <Button
                          onClick={handleGenerateAdversarial}
                          disabled={isGeneratingAdversarial}
                          variant="destructive"
                          className="w-full"
                          size="sm"
                        >
                          {isGeneratingAdversarial ? (
                            <><Loader2 className="h-4 w-4 mr-2 animate-spin" />Generating Traps...</>
                          ) : (
                            <><ShieldAlert className="h-4 w-4 mr-2" />Generate Adversarial Test</>
                          )}
                        </Button>
                      </div>
                    </motion.div>
                  )}
                </AnimatePresence>
              </div>
            )}

            <Button
              onClick={handleGenerate}
              disabled={isGenerating || questionTypes.length === 0}
              className="w-full"
              size="lg"
            >
              {isGenerating ? (
                <>
                  <Loader2 className="h-4 w-4 mr-2 animate-spin" />
                  Generating...
                </>
              ) : (
                <>
                  <Sparkles className="h-4 w-4 mr-2" />
                  Generate Reading Test
                </>
              )}
            </Button>
          </div>
        </CardContent>
      </Card>
    </motion.div>
  )
}
