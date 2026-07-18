'use client'

import { useEffect } from 'react'
import { motion } from 'framer-motion'
import { 
  ArrowLeft, BookOpen, Lock, CheckCircle2, AlertCircle, 
  Sparkles, TrendingUp, ChevronRight
} from 'lucide-react'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Badge } from '@/components/ui/badge'
import { Progress } from '@/components/ui/progress'
import { cn } from '@/lib/utils'
import { useGrammarStore } from '@/lib/store/grammarStore'
import { useRouter } from 'next/navigation'

export default function GrammarJourneyPage() {
  const router = useRouter()
  const {
    journeyMap,
    isLoading,
    error,
    fetchJourneyMap,
    setPhase,
    fetchLessonContent
  } = useGrammarStore()
  
  useEffect(() => {
    fetchJourneyMap()
  }, [fetchJourneyMap])
  
  if (isLoading && !journeyMap) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="text-center">
          <div className="h-12 w-12 rounded-xl bg-primary/10 flex items-center justify-center mx-auto mb-4">
            <BookOpen className="h-6 w-6 text-primary animate-pulse" />
          </div>
          <p className="text-muted-foreground">Loading your grammar journey...</p>
        </div>
      </div>
    )
  }
  
  if (error) {
    return (
      <div className="p-4 rounded-xl bg-destructive/10 border border-destructive/20">
        <div className="flex items-center gap-3">
          <AlertCircle className="h-5 w-5 text-destructive" />
          <div>
            <p className="font-medium text-destructive">Error loading journey map</p>
            <p className="text-sm text-muted-foreground">{error}</p>
          </div>
        </div>
      </div>
    )
  }
  
  const handleStartTopic = async (topicId: number) => {
    try {
      await fetchLessonContent(topicId)
      setPhase('lesson')
    } catch (error) {
      console.error('Failed to load lesson:', error)
    }
  }
  
  const getModuleColor = (moduleIndex: number) => {
    const colors = [
      'bg-blue-500/10 border-blue-500/20 text-blue-600',
      'bg-purple-500/10 border-purple-500/20 text-purple-600',
      'bg-green-500/10 border-green-500/20 text-green-600',
      'bg-amber-500/10 border-amber-500/20 text-amber-600',
      'bg-rose-500/10 border-rose-500/20 text-rose-600',
      'bg-cyan-500/10 border-cyan-500/20 text-cyan-600',
      'bg-violet-500/10 border-violet-500/20 text-violet-600',
      'bg-emerald-500/10 border-emerald-500/20 text-emerald-600',
    ]
    return colors[moduleIndex % colors.length]
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-4">
          <Button
            variant="ghost"
            size="icon"
            onClick={() => router.push('/practice/grammar')}
          >
            <ArrowLeft className="h-4 w-4" />
          </Button>
          <div>
            <h1 className="text-3xl font-bold mb-2">Grammar Learning Journey</h1>
            <p className="text-muted-foreground">
              Your personalized path to grammar mastery across {journeyMap?.total_modules || 0} modules
            </p>
          </div>
        </div>
        <Badge variant="outline" className="text-sm">
          <Sparkles className="h-3 w-3 mr-1" />
          {journeyMap?.total_topics || 0} Topics
        </Badge>
      </div>
      
      {/* Journey Visualization */}
      <div className="space-y-8">
        {journeyMap?.modules.map((module, moduleIndex) => {
          const moduleColor = getModuleColor(moduleIndex)
          const colorClass = moduleColor.split(' ')[0]
          const borderClass = moduleColor.split(' ')[1]
          const textClass = moduleColor.split(' ')[2]
          
          return (
            <motion.div
              key={module.module_id}
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ delay: moduleIndex * 0.1 }}
            >
              <Card className={cn("border-l-4", borderClass)}>
                <CardHeader className="pb-3">
                  <div className="flex items-center justify-between">
                    <div className="flex items-center gap-3">
                      <div className={cn("h-10 w-10 rounded-lg flex items-center justify-center", colorClass)}>
                        <BookOpen className={cn("h-5 w-5", textClass)} />
                      </div>
                      <div>
                        <CardTitle className="text-xl">
                          Module {module.module_id}: {module.module_name}
                        </CardTitle>
                        <p className="text-sm text-muted-foreground">
                          {module.description} • {module.topic_count} topics
                        </p>
                      </div>
                    </div>
                    <Badge variant="outline" className={textClass}>
                      {moduleIndex === 0 ? 'Foundation' : 
                       moduleIndex === journeyMap.modules.length - 1 ? 'Advanced' : 
                       'Intermediate'}
                    </Badge>
                  </div>
                </CardHeader>
                <CardContent>
                  {/* Module Progress */}
                  <div className="mb-6">
                    <div className="flex items-center justify-between mb-2">
                      <span className="text-sm font-medium">Module Progress</span>
                      <span className="text-sm text-muted-foreground">
                        Estimated mastery: 65%
                      </span>
                    </div>
                    <Progress value={65} className="h-2" />
                  </div>
                  
                  {/* Topics Grid */}
                  <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
                    {module.topics.map((topic, topicIndex) => {
                      // Simulate mastery - in real app this would come from user data
                      const mastery = Math.max(20, 100 - (topicIndex * 15))
                      const isLocked = topicIndex > 0 && mastery < 40
                      const isCompleted = mastery >= 80
                      
                      return (
                        <Card 
                          key={topic.topic_id}
                          className={cn(
                            "transition-all hover:shadow-md",
                            isLocked ? "opacity-60" : "hover:border-primary/50",
                            isCompleted ? "border-success/20 bg-success/5" : ""
                          )}
                        >
                          <CardContent className="p-4">
                            <div className="space-y-3">
                              <div className="flex items-start justify-between">
                                <div>
                                  <h4 className="font-medium">{topic.topic_name}</h4>
                                  <p className="text-xs text-muted-foreground line-clamp-2">
                                    {topic.description || 'Grammar topic for IELTS preparation'}
                                  </p>
                                </div>
                                <div>
                                  {isLocked ? (
                                    <Lock className="h-4 w-4 text-muted-foreground" />
                                  ) : isCompleted ? (
                                    <CheckCircle2 className="h-4 w-4 text-success" />
                                  ) : (
                                    <div className="h-4 w-4 rounded-full bg-primary/20 border border-primary/30" />
                                  )}
                                </div>
                              </div>
                              
                              <Progress value={mastery} className="h-2" />
                              
                              <div className="flex items-center justify-between text-xs">
                                <span className={cn(
                                  mastery >= 80 ? 'text-success' :
                                  mastery >= 50 ? 'text-amber-500' :
                                  'text-warning'
                                )}>
                                  {mastery}% mastery
                                </span>
                                <span className="text-muted-foreground">
                                  Topic {topic.order}
                                </span>
                              </div>
                              
                              <Button
                                size="sm"
                                className="w-full"
                                disabled={isLocked}
                                variant={isCompleted ? "outline" : "default"}
                                onClick={() => handleStartTopic(topic.topic_id)}
                              >
                                {isCompleted ? 'Review' : isLocked ? 'Locked' : 'Start'}
                                {!isLocked && <ChevronRight className="h-3 w-3 ml-2" />}
                              </Button>
                            </div>
                          </CardContent>
                        </Card>
                      )
                    })}
                  </div>
                </CardContent>
              </Card>
            </motion.div>
          )
        })}
      </div>
      
      {/* Journey Legend */}
      <Card>
        <CardHeader className="pb-3">
          <CardTitle className="text-base">Journey Legend</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
            <div className="flex items-center gap-3 p-3 rounded-lg border">
              <div className="h-8 w-8 rounded-lg bg-success/10 flex items-center justify-center">
                <CheckCircle2 className="h-4 w-4 text-success" />
              </div>
              <div>
                <p className="text-sm font-medium">Completed</p>
                <p className="text-xs text-muted-foreground">80%+ mastery</p>
              </div>
            </div>
            
            <div className="flex items-center gap-3 p-3 rounded-lg border">
              <div className="h-8 w-8 rounded-lg bg-primary/10 flex items-center justify-center">
                <TrendingUp className="h-4 w-4 text-primary" />
              </div>
              <div>
                <p className="text-sm font-medium">In Progress</p>
                <p className="text-xs text-muted-foreground">40-79% mastery</p>
              </div>
            </div>
            
            <div className="flex items-center gap-3 p-3 rounded-lg border">
              <div className="h-8 w-8 rounded-lg bg-warning/10 flex items-center justify-center">
                <AlertCircle className="h-4 w-4 text-warning" />
              </div>
              <div>
                <p className="text-sm font-medium">Needs Review</p>
                <p className="text-xs text-muted-foreground">Below 40% mastery</p>
              </div>
            </div>
            
            <div className="flex items-center gap-3 p-3 rounded-lg border">
              <div className="h-8 w-8 rounded-lg bg-muted flex items-center justify-center">
                <Lock className="h-4 w-4 text-muted-foreground" />
              </div>
              <div>
                <p className="text-sm font-medium">Locked</p>
                <p className="text-xs text-muted-foreground">Prerequisites needed</p>
              </div>
            </div>
          </div>
        </CardContent>
      </Card>
      
      {/* AI Recommendation */}
      <Card className="border-primary/20 bg-primary/5">
        <CardContent className="p-6">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-3">
              <div className="h-10 w-10 rounded-lg bg-primary/10 flex items-center justify-center">
                <Sparkles className="h-5 w-5 text-primary" />
              </div>
              <div>
                <p className="font-medium">AI Learning Recommendation</p>
                <p className="text-sm text-muted-foreground">
                  Based on your progress, start with Module 2: Articles for maximum improvement
                </p>
              </div>
            </div>
            <Button 
              onClick={() => {
                // Start with Module 2, Topic 3 (Indefinite Articles)
                handleStartTopic(3)
              }}
            >
              Start Recommended Topic
            </Button>
          </div>
        </CardContent>
      </Card>
    </div>
  )
}