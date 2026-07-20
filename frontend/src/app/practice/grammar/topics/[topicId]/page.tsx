'use client'

import { useState, useCallback } from 'react'
import { useParams, useRouter } from 'next/navigation'
import { motion, AnimatePresence } from 'framer-motion'
import {
  ArrowLeft, BookOpen, Sparkles, Lightbulb, AlertCircle, CheckCircle2,
  ChevronRight, PenTool, Mic, Brain, GraduationCap, Languages
} from 'lucide-react'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Badge } from '@/components/ui/badge'
import { cn } from '@/lib/utils'
import { getTopicById, getModuleForTopic } from '@/lib/data/grammar'
import { grammarApi } from '@/lib/services/grammar'

type ExampleLevel = 'easy' | 'medium' | 'ielts' | 'academic'
type ExplanationLevel = 'beginner' | 'intermediate' | 'advanced'

export default function TopicLessonPage() {
  const params = useParams()
  const router = useRouter()
  const topicId = Number(params.topicId)

  // Get content from STATIC frontend data — no API call needed
  const topic = getTopicById(topicId)
  const parentModule = getModuleForTopic(topicId)

  const [activeSection, setActiveSection] = useState<string>('overview')
  const [selectedExampleLevel, setSelectedExampleLevel] = useState<ExampleLevel>('medium')
  const [explanationLevel, setExplanationLevel] = useState<ExplanationLevel>('intermediate')
  const [explanationLanguage, setExplanationLanguage] = useState<'english' | 'bangla'>('english')
  const [aiExplanation, setAiExplanation] = useState<string | null>(null)
  const [isLoadingExplanation, setIsLoadingExplanation] = useState(false)

  const handleGetAIExplanation = useCallback(async () => {
    setIsLoadingExplanation(true)
    try {
      const response = await grammarApi.getAIExplanation(topicId, {
        level: explanationLevel,
        language: explanationLanguage
      })
      setAiExplanation(response.explanation)
    } catch (err) {
      setAiExplanation('AI explanation unavailable. Please try again later.')
    } finally {
      setIsLoadingExplanation(false)
    }
  }, [topicId, explanationLevel, explanationLanguage])

  if (!topic || !parentModule) {
    return (
      <div className="p-6 rounded-xl bg-destructive/10 border border-destructive/20">
        <AlertCircle className="h-5 w-5 text-destructive mb-2" />
        <p className="font-medium text-destructive">Topic not found</p>
        <p className="text-sm text-muted-foreground">Topic ID {topicId} does not exist in the curriculum.</p>
        <Button variant="outline" className="mt-4" onClick={() => router.push('/practice/grammar')}>
          <ArrowLeft className="h-4 w-4 mr-2" />Back to Grammar
        </Button>
      </div>
    )
  }

  const sections = [
    { id: 'overview', label: 'Overview', icon: GraduationCap },
    { id: 'rules', label: 'Grammar Rules', icon: BookOpen },
    { id: 'ai-explanation', label: 'AI Explanation', icon: Sparkles },
    { id: 'examples', label: 'Examples', icon: Lightbulb },
    { id: 'common-mistakes', label: 'Common Mistakes', icon: AlertCircle },
    { id: 'practice', label: 'Practice', icon: PenTool },
  ]

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center gap-4">
        <Button variant="ghost" size="icon" onClick={() => router.push('/practice/grammar')}>
          <ArrowLeft className="h-4 w-4" />
        </Button>
        <div className="flex-1">
          <div className="flex items-center gap-2 mb-1">
            <Badge variant="outline">{parentModule.module_name}</Badge>
            <ChevronRight className="h-3 w-3 text-muted-foreground" />
            <span className="text-sm text-muted-foreground">Topic {topic.topic_id}</span>
          </div>
          <h1 className="text-2xl font-bold">{topic.topic_name}</h1>
          <p className="text-muted-foreground">{topic.description}</p>
        </div>
      </div>

      {/* Section Tabs */}
      <div className="flex gap-2 overflow-x-auto pb-2">
        {sections.map(({ id, label, icon: Icon }) => (
          <button
            key={id}
            onClick={() => setActiveSection(id)}
            className={cn(
              'flex items-center gap-2 px-4 py-2 rounded-lg text-sm font-medium whitespace-nowrap transition-all',
              activeSection === id
                ? 'bg-primary text-primary-foreground'
                : 'bg-muted/50 text-muted-foreground hover:bg-muted'
            )}
          >
            <Icon className="h-4 w-4" />
            {label}
          </button>
        ))}
      </div>

      {/* Section Content */}
      <AnimatePresence mode="wait">
        {/* Overview */}
        {activeSection === 'overview' && (
          <motion.div key="overview" initial={{ opacity: 0, y: 10 }} animate={{ opacity: 1, y: 0 }} exit={{ opacity: 0, y: -10 }}>
            <Card>
              <CardContent className="p-6 space-y-6">
                {/* Topic Summary */}
                <div className="text-center space-y-3">
                  <div className="h-16 w-16 rounded-2xl bg-primary/10 flex items-center justify-center mx-auto">
                    <GraduationCap className="h-8 w-8 text-primary" />
                  </div>
                  <h2 className="text-xl font-semibold">{topic.topic_name}</h2>
                  <p className="text-muted-foreground max-w-md mx-auto">{topic.description}</p>
                  <Badge variant="outline">{parentModule.module_name}</Badge>
                </div>

                  <div className="grid grid-cols-1 md:grid-cols-3 gap-4 pt-4">
                  <div className="p-4 rounded-xl bg-muted/50 text-center">
                    <BookOpen className="h-6 w-6 text-primary mx-auto mb-2" />
                    <p className="text-sm font-medium">{topic.rules.length} Rules</p>
                    <p className="text-xs text-muted-foreground">Grammar patterns to learn</p>
                  </div>
                  <div className="p-4 rounded-xl bg-muted/50 text-center">
                    <Lightbulb className="h-6 w-6 text-amber-500 mx-auto mb-2" />
                    <p className="text-sm font-medium">{Object.values(topic.examples).flat().length} Examples</p>
                    <p className="text-xs text-muted-foreground">From easy to academic</p>
                  </div>
                  <div className="p-4 rounded-xl bg-muted/50 text-center">
                    <AlertCircle className="h-6 w-6 text-red-500 mx-auto mb-2" />
                    <p className="text-sm font-medium">{topic.common_mistakes.length} Common Mistakes</p>
                    <p className="text-xs text-muted-foreground">Avoid these errors</p>
                  </div>
                </div>

                {/* Start Learning CTA */}
                <div className="flex justify-center pt-4">
                  <Button size="lg" onClick={() => setActiveSection('rules')}>
                    Start Learning
                    <ChevronRight className="h-4 w-4 ml-2" />
                  </Button>
                </div>
              </CardContent>
            </Card>
          </motion.div>
        )}

        {/* Grammar Rules */}
        {activeSection === 'rules' && (
          <motion.div key="rules" initial={{ opacity: 0, y: 10 }} animate={{ opacity: 1, y: 0 }} exit={{ opacity: 0, y: -10 }}>
            <div className="space-y-4">
              {topic.rules.map((rule, idx) => (
                <Card key={rule.rule_id || idx}>
                  <CardContent className="p-6">
                    <div className="flex items-start gap-3">
                      <div className="h-8 w-8 rounded-lg bg-primary/10 flex items-center justify-center shrink-0">
                        <span className="text-sm font-bold text-primary">{idx + 1}</span>
                      </div>
                      <div className="space-y-3 flex-1">
                        <p className="font-medium text-lg">{rule.rule}</p>
                        <div className="p-3 rounded-lg bg-muted/50 border">
                          <p className="text-sm"><span className="font-medium">Example:</span> {rule.example}</p>
                        </div>
                        <div className="p-3 rounded-lg bg-primary/5 border border-primary/10">
                          <p className="text-sm">
                            <span className="font-medium text-primary">IELTS Usage:</span> {rule.ielts_usage}
                          </p>
                        </div>
                      </div>
                    </div>
                  </CardContent>
                </Card>
              ))}
            </div>
          </motion.div>
        )}

        {/* AI Explanation */}
        {activeSection === 'ai-explanation' && (
          <motion.div key="ai" initial={{ opacity: 0, y: 10 }} animate={{ opacity: 1, y: 0 }} exit={{ opacity: 0, y: -10 }}>
            <Card>
              <CardHeader>
                <CardTitle className="flex items-center gap-2">
                  <Brain className="h-5 w-5 text-primary" />
                  AI-Powered Explanation
                </CardTitle>
              </CardHeader>
              <CardContent className="space-y-4">
                {/* Level selector */}
                <div className="space-y-2">
                  <label className="text-sm font-medium flex items-center gap-2">
                    <GraduationCap className="h-4 w-4" />
                    Explanation Level
                  </label>
                  <div className="flex gap-2">
                    {(['beginner', 'intermediate', 'advanced'] as const).map((level) => (
                      <button
                        key={level}
                        onClick={() => setExplanationLevel(level)}
                        className={cn(
                          'px-4 py-2 rounded-lg text-sm font-medium capitalize transition-all',
                          explanationLevel === level
                            ? 'bg-primary text-primary-foreground'
                            : 'bg-muted text-muted-foreground hover:bg-muted/80'
                        )}
                      >
                        {level}
                      </button>
                    ))}
                  </div>
                </div>

                {/* Language selector */}
                <div className="space-y-2">
                  <label className="text-sm font-medium flex items-center gap-2">
                    <Languages className="h-4 w-4" />
                    Language
                  </label>
                  <div className="flex gap-2">
                    {(['english', 'bangla'] as const).map((lang) => (
                      <button
                        key={lang}
                        onClick={() => setExplanationLanguage(lang)}
                        className={cn(
                          'px-4 py-2 rounded-lg text-sm font-medium capitalize transition-all',
                          explanationLanguage === lang
                            ? 'bg-primary text-primary-foreground'
                            : 'bg-muted text-muted-foreground hover:bg-muted/80'
                        )}
                      >
                        {lang}
                      </button>
                    ))}
                  </div>
                </div>

                <Button onClick={handleGetAIExplanation} disabled={isLoadingExplanation} className="w-full">
                  {isLoadingExplanation ? (
                    <><Sparkles className="h-4 w-4 mr-2 animate-spin" />Generating...</>
                  ) : (
                    <><Sparkles className="h-4 w-4 mr-2" />Get AI Explanation</>
                  )}
                </Button>

                {aiExplanation && (
                  <div className="p-4 rounded-xl bg-muted/50 border mt-4">
                    <p className="text-sm whitespace-pre-wrap leading-relaxed">{aiExplanation}</p>
                  </div>
                )}
              </CardContent>
            </Card>
          </motion.div>
        )}

        {/* Examples */}
        {activeSection === 'examples' && (
          <motion.div key="examples" initial={{ opacity: 0, y: 10 }} animate={{ opacity: 1, y: 0 }} exit={{ opacity: 0, y: -10 }}>
            <Card>
              <CardHeader>
                <CardTitle className="text-base">Examples by Difficulty</CardTitle>
                <div className="flex gap-2 mt-2">
                  {(['easy', 'medium', 'ielts', 'academic'] as const).map((level) => (
                    <button
                      key={level}
                      onClick={() => setSelectedExampleLevel(level)}
                      className={cn(
                        'px-3 py-1.5 rounded-lg text-xs font-medium capitalize transition-all',
                        selectedExampleLevel === level
                          ? 'bg-primary text-primary-foreground'
                          : 'bg-muted text-muted-foreground hover:bg-muted/80'
                      )}
                    >
                      {level}
                    </button>
                  ))}
                </div>
              </CardHeader>
              <CardContent>
                <div className="space-y-3">
                  {(topic.examples[selectedExampleLevel] || []).map((example, idx) => (
                    <div key={idx} className="p-4 rounded-xl bg-muted/30 border">
                      <div className="flex items-start gap-3">
                        <div className="h-6 w-6 rounded-full bg-primary/10 flex items-center justify-center shrink-0 mt-0.5">
                          <span className="text-xs font-bold text-primary">{idx + 1}</span>
                        </div>
                        <p className="text-sm leading-relaxed">{example}</p>
                      </div>
                    </div>
                  ))}
                  {(!topic.examples[selectedExampleLevel] || topic.examples[selectedExampleLevel].length === 0) && (
                    <p className="text-sm text-muted-foreground text-center py-4">No examples available for this level.</p>
                  )}
                </div>
              </CardContent>
            </Card>
          </motion.div>
        )}

        {/* Common Mistakes */}
        {activeSection === 'common-mistakes' && (
          <motion.div key="mistakes" initial={{ opacity: 0, y: 10 }} animate={{ opacity: 1, y: 0 }} exit={{ opacity: 0, y: -10 }}>
            <div className="space-y-4">
              {topic.common_mistakes.map((mistake, idx) => (
                <Card key={idx} className="border-warning/20">
                  <CardContent className="p-6 space-y-3">
                    <div className="flex items-center gap-2 mb-2">
                      <AlertCircle className="h-4 w-4 text-warning" />
                      <span className="text-sm font-medium text-warning">Common Mistake #{idx + 1}</span>
                    </div>
                    <div className="p-3 rounded-lg bg-destructive/5 border border-destructive/10">
                      <p className="text-xs text-muted-foreground mb-1">Incorrect</p>
                      <p className="text-sm line-through text-destructive">{mistake.incorrect}</p>
                    </div>
                    <div className="p-3 rounded-lg bg-success/5 border border-success/10">
                      <p className="text-xs text-muted-foreground mb-1">Correct</p>
                      <p className="text-sm font-medium text-green-700 dark:text-green-400">{mistake.correct}</p>
                    </div>
                    {mistake.correct_alternative && (
                      <div className="p-3 rounded-lg bg-primary/5 border border-primary/10">
                        <p className="text-xs text-muted-foreground mb-1">Alternative</p>
                        <p className="text-sm">{mistake.correct_alternative}</p>
                      </div>
                    )}
                    <div className="p-3 rounded-lg bg-muted/50">
                      <p className="text-xs text-muted-foreground mb-1">Why?</p>
                      <p className="text-sm">{mistake.explanation}</p>
                    </div>
                  </CardContent>
                </Card>
              ))}
            </div>
          </motion.div>
        )}

        {/* Practice Options */}
        {activeSection === 'practice' && (
          <motion.div key="practice" initial={{ opacity: 0, y: 10 }} animate={{ opacity: 1, y: 0 }} exit={{ opacity: 0, y: -10 }}>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <Card className="hover:shadow-md transition-shadow cursor-pointer" onClick={() => router.push(`/practice/grammar/topics/${topicId}/exercises`)}>
                <CardContent className="p-6 text-center space-y-3">
                  <div className="h-14 w-14 rounded-xl bg-primary/10 flex items-center justify-center mx-auto">
                    <Brain className="h-7 w-7 text-primary" />
                  </div>
                  <h3 className="font-semibold">Interactive Exercises</h3>
                  <p className="text-sm text-muted-foreground">
                    8 exercise types: fill in blank, drag & drop, error correction, and more
                  </p>
                  <Badge>AI-Generated</Badge>
                </CardContent>
              </Card>

              <Card className="hover:shadow-md transition-shadow cursor-pointer" onClick={() => router.push(`/practice/grammar/topics/${topicId}/writing`)}>
                <CardContent className="p-6 text-center space-y-3">
                  <div className="h-14 w-14 rounded-xl bg-green-500/10 flex items-center justify-center mx-auto">
                    <PenTool className="h-7 w-7 text-green-600" />
                  </div>
                  <h3 className="font-semibold">Writing Practice</h3>
                  <p className="text-sm text-muted-foreground">
                    Write sentences using {topic.topic_name} and get AI feedback
                  </p>
                  <Badge variant="outline">Grammar Focus</Badge>
                </CardContent>
              </Card>

              <Card className="hover:shadow-md transition-shadow cursor-pointer" onClick={() => router.push(`/practice/grammar/topics/${topicId}/speaking`)}>
                <CardContent className="p-6 text-center space-y-3">
                  <div className="h-14 w-14 rounded-xl bg-blue-500/10 flex items-center justify-center mx-auto">
                    <Mic className="h-7 w-7 text-blue-600" />
                  </div>
                  <h3 className="font-semibold">Speaking Practice</h3>
                  <p className="text-sm text-muted-foreground">
                    Speak using {topic.topic_name} and get grammar analysis
                  </p>
                  <Badge variant="outline">Speech-to-Text</Badge>
                </CardContent>
              </Card>

              <Card className="hover:shadow-md transition-shadow cursor-pointer" onClick={() => router.push('/practice/grammar')}>
                <CardContent className="p-6 text-center space-y-3">
                  <div className="h-14 w-14 rounded-xl bg-amber-500/10 flex items-center justify-center mx-auto">
                    <CheckCircle2 className="h-7 w-7 text-amber-600" />
                  </div>
                  <h3 className="font-semibold">Back to Dashboard</h3>
                  <p className="text-sm text-muted-foreground">
                    Check progress and explore other topics
                  </p>
                  <Badge variant="outline">Overview</Badge>
                </CardContent>
              </Card>
            </div>
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  )
}