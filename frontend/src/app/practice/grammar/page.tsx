'use client'

import { useState } from 'react'
import { motion } from 'framer-motion'
import { FileText, ChevronRight, AlertCircle, CheckCircle2, Lightbulb, TrendingUp } from 'lucide-react'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Badge } from '@/components/ui/badge'
import { Progress } from '@/components/ui/progress'
import { mockGrammarTopics } from '@/lib/mock-data/grammar'
import { cn } from '@/lib/utils'
import { fadeInUp, staggerItem, staggerContainer } from '@/lib/animations'

export default function GrammarPage() {
  const [selectedTopic, setSelectedTopic] = useState<string | null>(null)

  const totalMastery = Math.round(
    mockGrammarTopics.reduce((acc, t) => acc + t.mastery, 0) / mockGrammarTopics.length
  )

  const topic = selectedTopic ? mockGrammarTopics.find(t => t.id === selectedTopic) : null

  return (
    <div className="space-y-6">
      {/* Header */}
      <motion.div
        initial={{ opacity: 0, y: -20 }}
        animate={{ opacity: 1, y: 0 }}
      >
        <h1 className="text-3xl font-bold mb-2">Grammar</h1>
        <p className="text-muted-foreground">
          Master grammar topics with personalized exercises based on your mistakes
        </p>
      </motion.div>

      {/* Overall Stats */}
      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ delay: 0.1 }}
      >
        <Card>
          <CardContent className="p-6">
            <div className="flex items-center justify-between mb-4">
              <div className="flex items-center gap-3">
                <div className="h-12 w-12 rounded-xl bg-primary/10 flex items-center justify-center">
                  <TrendingUp className="h-6 w-6 text-primary" />
                </div>
                <div>
                  <p className="text-sm text-muted-foreground">Overall Mastery</p>
                  <p className="text-2xl font-bold">{totalMastery}%</p>
                </div>
              </div>
              <div className="flex gap-6 text-center">
                {[
                  { label: 'Topics', value: mockGrammarTopics.length },
                  { label: 'Mistakes', value: mockGrammarTopics.reduce((a, t) => a + t.mistakeCount, 0) },
                  { label: 'Mastered', value: mockGrammarTopics.filter(t => t.mastery >= 80).length },
                ].map((stat) => (
                  <div key={stat.label}>
                    <p className="text-xl font-bold">{stat.value}</p>
                    <p className="text-xs text-muted-foreground">{stat.label}</p>
                  </div>
                ))}
              </div>
            </div>
            <Progress value={totalMastery} className="h-3" />
          </CardContent>
        </Card>
      </motion.div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Topics List */}
        <motion.div
          initial={{ opacity: 0, x: -20 }}
          animate={{ opacity: 1, x: 0 }}
          transition={{ delay: 0.2 }}
          className="lg:col-span-1"
        >
          <Card className="h-full">
            <CardHeader className="pb-3">
              <CardTitle className="text-base">Grammar Topics</CardTitle>
            </CardHeader>
            <CardContent>
              <motion.div
                variants={staggerContainer}
                initial="initial"
                animate="animate"
                className="space-y-3"
              >
                {mockGrammarTopics.map((t) => (
                  <motion.button
                    key={t.id}
                    variants={staggerItem}
                    onClick={() => setSelectedTopic(t.id)}
                    className={cn(
                      "w-full p-4 rounded-xl border text-left transition-all hover:shadow-md",
                      selectedTopic === t.id
                        ? "border-primary bg-primary/5"
                        : "border-border hover:border-primary/50"
                    )}
                  >
                    <div className="flex items-center justify-between mb-2">
                      <span className="font-medium">{t.name}</span>
                      <Badge variant={t.mistakeCount > 10 ? 'destructive' : t.mistakeCount > 5 ? 'warning' : 'secondary'}>
                        {t.mistakeCount} mistakes
                      </Badge>
                    </div>
                    <Progress value={t.mastery} className="h-2 mb-2" />
                    <div className="flex items-center justify-between text-xs text-muted-foreground">
                      <span>{t.mastery}% mastery</span>
                      {t.lastPracticed && (
                        <span>Last: {t.lastPracticed.toLocaleDateString()}</span>
                      )}
                    </div>
                  </motion.button>
                ))}
              </motion.div>
            </CardContent>
          </Card>
        </motion.div>

        {/* Topic Details */}
        <motion.div
          initial={{ opacity: 0, x: 20 }}
          animate={{ opacity: 1, x: 0 }}
          transition={{ delay: 0.3 }}
          className="lg:col-span-2"
        >
          {topic ? (
            <Card>
              <CardHeader className="pb-3">
                <div className="flex items-center justify-between">
                  <CardTitle className="text-xl">{topic.name}</CardTitle>
                  <div className="flex items-center gap-2">
                    <Progress value={topic.mastery} className="w-24 h-2" />
                    <span className="text-sm font-medium">{topic.mastery}%</span>
                  </div>
                </div>
                <p className="text-muted-foreground">{topic.description}</p>
              </CardHeader>
              <CardContent>
                <div className="space-y-6">
                  {/* Rule Explanation */}
                  <div className="p-4 rounded-xl bg-primary/5 border border-primary/20">
                    <div className="flex items-start gap-2 mb-2">
                      <Lightbulb className="h-4 w-4 text-primary shrink-0 mt-0.5" />
                      <h4 className="font-medium">Key Concepts</h4>
                    </div>
                    <p className="text-sm text-muted-foreground">
                      Click on a topic to see detailed explanations, examples, and your personal mistakes in this area.
                    </p>
                  </div>

                  {/* Your Mistakes */}
                  <div>
                    <h4 className="font-medium mb-3 flex items-center gap-2">
                      <AlertCircle className="h-4 w-4 text-warning" />
                      Your Mistakes in {topic.name}
                    </h4>
                    {topic.mistakes.length > 0 ? (
                      <div className="space-y-3">
                        {topic.mistakes.map((mistake) => (
                          <div
                            key={mistake.id}
                            className="p-4 rounded-xl border border-warning/20 bg-warning/5"
                          >
                            <div className="space-y-2">
                              <div>
                                <p className="text-xs text-muted-foreground">Your sentence</p>
                                <p className="text-sm line-through text-destructive">{mistake.incorrectSentence}</p>
                              </div>
                              <div>
                                <p className="text-xs text-muted-foreground">Correct</p>
                                <p className="text-sm font-medium text-success">{mistake.correctSentence}</p>
                              </div>
                              <div className="pt-2 border-t border-warning/20">
                                <p className="text-xs text-muted-foreground">{mistake.explanation}</p>
                              </div>
                            </div>
                          </div>
                        ))}
                      </div>
                    ) : (
                      <div className="p-4 rounded-xl bg-success/10 border border-success/20 text-center">
                        <CheckCircle2 className="h-8 w-8 text-success mx-auto mb-2" />
                        <p className="text-sm">No mistakes in this topic! Great job!</p>
                      </div>
                    )}
                  </div>

                  {/* Practice Button */}
                  <Button className="w-full" size="lg">
                    Practice {topic.name}
                    <ChevronRight className="h-4 w-4 ml-2" />
                  </Button>
                </div>
              </CardContent>
            </Card>
          ) : (
            <Card className="h-full">
              <CardContent className="h-full flex flex-col items-center justify-center py-12">
                <FileText className="h-16 w-16 text-muted-foreground mb-4" />
                <p className="text-muted-foreground text-center">
                  Select a grammar topic from the list to see your mistakes and practice exercises
                </p>
              </CardContent>
            </Card>
          )}
        </motion.div>
      </div>
    </div>
  )
}