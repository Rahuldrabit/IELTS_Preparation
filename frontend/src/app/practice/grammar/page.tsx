'use client'

import { useState, useEffect } from 'react'
import { useRouter } from 'next/navigation'
import { motion } from 'framer-motion'
import { 
  FileText, ChevronRight, AlertCircle, CheckCircle2, Lightbulb, 
  TrendingUp, Sparkles, Target, BookOpen, Zap, Calendar
} from 'lucide-react'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Badge } from '@/components/ui/badge'
import { Progress } from '@/components/ui/progress'
import { cn } from '@/lib/utils'
import { fadeInUp, staggerItem, staggerContainer } from '@/lib/animations'
import { useGrammarStore } from '@/lib/store/grammarStore'

export default function GrammarPage() {
  const router = useRouter()
  const {
    phase,
    dashboard,
    isLoading,
    error,
    fetchDashboard,
    setPhase,
    setCurrentTopic,
  } = useGrammarStore()
  
  const [selectedSkillId, setSelectedSkillId] = useState<number | null>(null)
  
  useEffect(() => {
    fetchDashboard()
  }, [fetchDashboard])
  
  // Combine weak and strong topics into a single "all topics" list for selection
  const allTopics = [
    ...(dashboard?.weak_topics || []),
    ...(dashboard?.strong_topics || [])
  ]
  
  const selectedSkill = selectedSkillId 
    ? allTopics.find(s => s.id === selectedSkillId)
    : null
  
  const handleSelectSkill = (skillId: number) => {
    setSelectedSkillId(skillId)
    setCurrentTopic(skillId)
  }
  
  const handleNavigateToJourney = () => {
    router.push('/practice/grammar/journey')
  }
  
  const handleNavigateToTopic = (topicId: number) => {
    router.push(`/practice/grammar/topics/${topicId}`)
  }

  if (isLoading && !dashboard) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="text-center">
          <div className="h-12 w-12 rounded-xl bg-primary/10 flex items-center justify-center mx-auto mb-4">
            <BookOpen className="h-6 w-6 text-primary animate-pulse" />
          </div>
          <p className="text-muted-foreground">Loading your grammar dashboard...</p>
        </div>
      </div>
    )
  }
  
  if (error) {
    return (
      <div className="space-y-6">
        <div className="p-4 rounded-xl bg-destructive/10 border border-destructive/20">
          <div className="flex items-center gap-3">
            <AlertCircle className="h-5 w-5 text-destructive" />
            <div>
              <p className="font-medium text-destructive">Could not load personalized dashboard</p>
              <p className="text-sm text-muted-foreground">{error}</p>
            </div>
          </div>
        </div>
        
        {/* Fallback: show quick links to journey and topics that work without DB */}
        <Card>
          <CardHeader>
            <CardTitle className="text-base">Grammar Learning</CardTitle>
          </CardHeader>
          <CardContent className="space-y-4">
            <p className="text-sm text-muted-foreground">
              While the personalized dashboard is unavailable, you can still explore grammar topics:
            </p>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <Button onClick={handleNavigateToJourney} className="h-auto py-4">
                <div className="text-center">
                  <Sparkles className="h-6 w-6 mx-auto mb-2" />
                  <p className="font-medium">Learning Journey</p>
                  <p className="text-xs opacity-80">Explore all 10 modules and 23 topics</p>
                </div>
              </Button>
              <Button variant="outline" onClick={() => handleNavigateToTopic(1)} className="h-auto py-4">
                <div className="text-center">
                  <BookOpen className="h-6 w-6 mx-auto mb-2" />
                  <p className="font-medium">Start Learning</p>
                  <p className="text-xs text-muted-foreground">Begin with Parts of Speech</p>
                </div>
              </Button>
            </div>
          </CardContent>
        </Card>
      </div>
    )
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <motion.div
        initial={{ opacity: 0, y: -20 }}
        animate={{ opacity: 1, y: 0 }}
      >
        <div className="flex items-center justify-between">
          <div>
            <h1 className="text-3xl font-bold mb-2">Grammar Coach</h1>
            <p className="text-muted-foreground">
              AI-powered personalized grammar coaching based on your mistakes
            </p>
          </div>
          <Button 
            onClick={handleNavigateToJourney}
            variant="outline"
          >
            <Sparkles className="h-4 w-4 mr-2" />
            View Learning Journey
          </Button>
        </div>
      </motion.div>

      {/* Overall Stats */}
      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ delay: 0.1 }}
      >
        <Card>
          <CardContent className="p-6">
            <div className="flex items-center justify-between mb-4 flex-wrap gap-4">
              <div className="flex items-center gap-3">
                <div className="h-12 w-12 rounded-xl bg-primary/10 flex items-center justify-center">
                  <TrendingUp className="h-6 w-6 text-primary" />
                </div>
                <div>
                  <p className="text-sm text-muted-foreground">Overall Grammar Mastery</p>
                  <p className="text-2xl font-bold">{dashboard?.overall_mastery?.toFixed(1) || 0}%</p>
                </div>
              </div>
              <div className="flex gap-6 text-center">
                {[
                  { 
                    label: 'Streak', 
                    value: dashboard?.grammar_streak || 0,
                    icon: <Calendar className="h-4 w-4 mx-auto mb-1" />
                  },
                  { 
                    label: 'Today\'s Accuracy', 
                    value: dashboard?.today_accuracy ? `${dashboard.today_accuracy.toFixed(1)}%` : '--',
                    icon: <Target className="h-4 w-4 mx-auto mb-1" />
                  },
                  { 
                    label: 'Weak Topics', 
                    value: dashboard?.weak_topics?.length || 0,
                    icon: <AlertCircle className="h-4 w-4 mx-auto mb-1" />
                  },
                  { 
                    label: 'Strong Topics', 
                    value: dashboard?.strong_topics?.length || 0,
                    icon: <CheckCircle2 className="h-4 w-4 mx-auto mb-1" />
                  },
                ].map((stat) => (
                  <div key={stat.label} className="min-w-16">
                    <div className="text-muted-foreground mb-1">{stat.icon}</div>
                    <p className="text-xl font-bold">{stat.value}</p>
                    <p className="text-xs text-muted-foreground">{stat.label}</p>
                  </div>
                ))}
              </div>
            </div>
            <Progress value={dashboard?.overall_mastery || 0} className="h-3" />
          </CardContent>
        </Card>
      </motion.div>

      {/* Daily Mission */}
      {dashboard?.daily_mission && (
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.2 }}
        >
          <Card className="border-primary/20 bg-primary/5">
            <CardContent className="p-6">
              <div className="flex items-center justify-between">
                <div className="flex items-center gap-3">
                  <div className="h-10 w-10 rounded-lg bg-primary/10 flex items-center justify-center">
                    <Zap className="h-5 w-5 text-primary" />
                  </div>
                  <div>
                    <p className="font-medium">Today's Grammar Mission</p>
                    <p className="text-sm text-muted-foreground">
                      {dashboard.daily_mission.title}
                    </p>
                  </div>
                </div>
                <Button size="sm">Start Mission</Button>
              </div>
            </CardContent>
          </Card>
        </motion.div>
      )}

      {/* Continue Learning */}
      {dashboard?.continue_learning && (
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.25 }}
        >
          <Card>
            <CardContent className="p-6">
              <div className="flex items-center justify-between">
                <div className="flex items-center gap-3">
                  <div className="h-10 w-10 rounded-lg bg-primary/10 flex items-center justify-center">
                    <BookOpen className="h-5 w-5 text-primary" />
                  </div>
                  <div>
                    <p className="font-medium">Continue Learning</p>
                    <p className="text-sm text-muted-foreground">
                      Resume {dashboard.continue_learning.skill_name}
                    </p>
                  </div>
                </div>
                <Button 
                  size="sm"
                  onClick={() => handleNavigateToTopic(dashboard.continue_learning!.skill_id)}
                >
                  Continue
                  <ChevronRight className="h-4 w-4 ml-2" />
                </Button>
              </div>
            </CardContent>
          </Card>
        </motion.div>
      )}

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Weak Topics */}
        <motion.div
          initial={{ opacity: 0, x: -20 }}
          animate={{ opacity: 1, x: 0 }}
          transition={{ delay: 0.3 }}
        >
          <Card className="h-full">
            <CardHeader className="pb-3">
              <CardTitle className="text-base flex items-center gap-2">
                <AlertCircle className="h-4 w-4 text-warning" />
                Weak Topics (Needs Review)
              </CardTitle>
            </CardHeader>
            <CardContent>
              {dashboard?.weak_topics && dashboard.weak_topics.length > 0 ? (
                <div className="space-y-3">
                  {dashboard.weak_topics.slice(0, 5).map((skill) => (
                    <button
                      key={skill.id}
                      onClick={() => handleSelectSkill(skill.id)}
                      className={cn(
                        "w-full p-4 rounded-xl border text-left transition-all hover:shadow-md",
                        selectedSkillId === skill.id
                          ? "border-warning bg-warning/5"
                          : "border-border hover:border-warning/50"
                      )}
                    >
                      <div className="flex items-center justify-between mb-2">
                        <span className="font-medium">{skill.skill_name}</span>
                        <Badge variant="warning">
                          {skill.mistake_count} mistakes
                        </Badge>
                      </div>
                      <Progress value={skill.mastery} className="h-2 mb-2" />
                      <div className="flex items-center justify-between text-xs text-muted-foreground">
                        <span>{skill.mastery}% mastery</span>
                        <span className="text-warning">Needs improvement</span>
                      </div>
                    </button>
                  ))}
                </div>
              ) : (
                <div className="p-4 rounded-xl bg-success/10 border border-success/20 text-center">
                  <CheckCircle2 className="h-8 w-8 text-success mx-auto mb-2" />
                  <p className="text-sm">No weak topics! Great job!</p>
                </div>
              )}
            </CardContent>
          </Card>
        </motion.div>

        {/* Strong Topics */}
        <motion.div
          initial={{ opacity: 0, x: 20 }}
          animate={{ opacity: 1, x: 0 }}
          transition={{ delay: 0.35 }}
        >
          <Card className="h-full">
            <CardHeader className="pb-3">
              <CardTitle className="text-base flex items-center gap-2">
                <CheckCircle2 className="h-4 w-4 text-success" />
                Strong Topics (Mastered)
              </CardTitle>
            </CardHeader>
            <CardContent>
              {dashboard?.strong_topics && dashboard.strong_topics.length > 0 ? (
                <div className="space-y-3">
                  {dashboard.strong_topics.slice(0, 5).map((skill) => (
                    <button
                      key={skill.id}
                      onClick={() => handleSelectSkill(skill.id)}
                      className={cn(
                        "w-full p-4 rounded-xl border text-left transition-all hover:shadow-md",
                        selectedSkillId === skill.id
                          ? "border-success bg-success/5"
                          : "border-border hover:border-success/50"
                      )}
                    >
                      <div className="flex items-center justify-between mb-2">
                        <span className="font-medium">{skill.skill_name}</span>
                        <Badge variant="success">
                          Mastered
                        </Badge>
                      </div>
                      <Progress value={skill.mastery} className="h-2 mb-2" />
                      <div className="flex items-center justify-between text-xs text-muted-foreground">
                        <span>{skill.mastery}% mastery</span>
                        <span className="text-success">Excellent</span>
                      </div>
                    </button>
                  ))}
                </div>
              ) : (
                <div className="p-4 rounded-xl bg-muted border-border text-center">
                  <FileText className="h-8 w-8 text-muted-foreground mx-auto mb-2" />
                  <p className="text-sm text-muted-foreground">Keep practicing to build strong topics!</p>
                </div>
              )}
            </CardContent>
          </Card>
        </motion.div>
      </div>

      {/* Selected Skill Details */}
      {selectedSkill && (
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.4 }}
        >
          <Card>
            <CardHeader className="pb-3">
              <div className="flex items-center justify-between">
                <CardTitle className="text-xl">{selectedSkill.skill_name}</CardTitle>
                <div className="flex items-center gap-4">
                  <div className="flex items-center gap-2">
                    <Progress value={selectedSkill.mastery} className="w-24 h-2" />
                    <span className="text-sm font-medium">{selectedSkill.mastery}% mastery</span>
                  </div>
                  <Button 
                    onClick={() => handleNavigateToTopic(selectedSkill.id)}
                    size="lg"
                  >
                    Practice {selectedSkill.skill_name}
                    <ChevronRight className="h-4 w-4 ml-2" />
                  </Button>
                </div>
              </div>
              <p className="text-muted-foreground">{selectedSkill.description}</p>
            </CardHeader>
            <CardContent>
              <div className="space-y-6">
                {/* Quick Stats */}
                <div className="grid grid-cols-3 gap-4">
                  <div className="p-4 rounded-xl bg-primary/5 text-center">
                    <p className="text-sm text-muted-foreground mb-1">Confidence</p>
                    <p className="text-2xl font-bold text-primary">
                      {(selectedSkill.confidence * 100).toFixed(1)}%
                    </p>
                  </div>
                  <div className="p-4 rounded-xl bg-warning/5 text-center">
                    <p className="text-sm text-muted-foreground mb-1">Mistakes</p>
                    <p className="text-2xl font-bold text-warning">
                      {selectedSkill.mistake_count}
                    </p>
                  </div>
                  <div className="p-4 rounded-xl bg-success/5 text-center">
                    <p className="text-sm text-muted-foreground mb-1">Last Practiced</p>
                    <p className="text-lg font-bold text-success">
                      {selectedSkill.last_practiced 
                        ? new Date(selectedSkill.last_practiced).toLocaleDateString() 
                        : 'Never'}
                    </p>
                  </div>
                </div>

                {/* Practice Options */}
                <div className="grid grid-cols-2 gap-4">
                  <Button 
                    variant="outline" 
                    className="h-auto py-4"
                    onClick={() => handleNavigateToTopic(selectedSkill.id)}
                  >
                    <div className="text-center">
                      <BookOpen className="h-6 w-6 mx-auto mb-2" />
                      <p className="font-medium">Learn Topic</p>
                      <p className="text-xs text-muted-foreground">Study rules & examples</p>
                    </div>
                  </Button>
                  <Button 
                    variant="outline" 
                    className="h-auto py-4"
                    onClick={() => router.push(`/practice/grammar/topics/${selectedSkill.id}/exercises`)}
                  >
                    <div className="text-center">
                      <Sparkles className="h-6 w-6 mx-auto mb-2" />
                      <p className="font-medium">Practice Exercises</p>
                      <p className="text-xs text-muted-foreground">8 interactive types</p>
                    </div>
                  </Button>
                </div>
              </div>
            </CardContent>
          </Card>
        </motion.div>
      )}
    </div>
  )
}