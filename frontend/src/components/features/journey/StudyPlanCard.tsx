'use client'

import { useState, useEffect } from 'react'
import { motion, AnimatePresence } from 'framer-motion'
import {
  Calendar,
  Check,
  ChevronRight,
  Clock,
  Flame,
  Loader2,
  Target,
  BookOpen,
  Headphones,
  PenTool,
  MessageCircle,
  GraduationCap,
} from 'lucide-react'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Badge } from '@/components/ui/badge'
import { Progress } from '@/components/ui/progress'
import { cn } from '@/lib/utils'
import { journeyApi } from '@/lib/services/journey'

interface DailyTask {
  id: string
  day: string
  date: string
  skill: string
  task_type: string
  title: string
  description: string
  duration_minutes: number
  priority: string
  completed: boolean
}

interface StudyPlan {
  week_start: string
  week_end: string
  target_band: number
  days_until_exam: number | null
  current_streak: number
  tasks: DailyTask[]
  focus_skills: string[]
  grammar_focus: string | null
  total_minutes: number
  completed_tasks: number
  message: string
}

interface StudyPlanCardProps {
  className?: string
}

const skillIcons: Record<string, typeof BookOpen> = {
  reading: BookOpen,
  listening: Headphones,
  writing: PenTool,
  speaking: MessageCircle,
  vocabulary: GraduationCap,
  grammar: GraduationCap,
}

export function StudyPlanCard({ className }: StudyPlanCardProps) {
  const [plan, setPlan] = useState<StudyPlan | null>(null)
  const [loading, setLoading] = useState(true)
  const [selectedDay, setSelectedDay] = useState<string | null>(null)
  
  useEffect(() => {
    loadPlan()
  }, [])
  
  const loadPlan = async () => {
    setLoading(true)
    try {
      const data = await journeyApi.getStudyPlan()
      setPlan(data as unknown as StudyPlan)
      
      // Select today by default
      const today = new Date().toLocaleDateString('en-US', { weekday: 'long' })
      setSelectedDay(today)
    } catch (error) {
      console.error('Failed to load study plan:', error)
    } finally {
      setLoading(false)
    }
  }
  
  const toggleTask = async (taskId: string, completed: boolean) => {
    try {
      await journeyApi.completeTask(taskId, completed)
      
      // Update local state
      setPlan(prev => {
        if (!prev) return prev
        return {
          ...prev,
          tasks: prev.tasks.map(t =>
            t.id === taskId ? { ...t, completed } : t
          ),
          completed_tasks: completed
            ? prev.completed_tasks + 1
            : prev.completed_tasks - 1,
        }
      })
    } catch (error) {
      console.error('Failed to update task:', error)
    }
  }
  
  if (loading) {
    return (
      <Card className={cn('animate-pulse', className)}>
        <CardContent className="p-6">
          <div className="h-64 bg-muted rounded" />
        </CardContent>
      </Card>
    )
  }
  
  if (!plan) {
    return null
  }
  
  // Group tasks by day
  const tasksByDay = plan.tasks.reduce((acc, task) => {
    if (!acc[task.day]) acc[task.day] = []
    acc[task.day].push(task)
    return acc
  }, {} as Record<string, DailyTask[]>)
  
  const days = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']
  const today = new Date().toLocaleDateString('en-US', { weekday: 'long' })
  
  return (
    <Card className={className}>
      <CardHeader>
        <div className="flex items-center justify-between">
          <CardTitle className="text-base flex items-center gap-2">
            <Calendar className="h-4 w-4" />
            Weekly Study Plan
          </CardTitle>
          {plan.current_streak > 0 && (
            <Badge variant="secondary" className="flex items-center gap-1">
              <Flame className="h-3 w-3 text-orange-500" />
              {plan.current_streak} day streak
            </Badge>
          )}
        </div>
        {plan.message && (
          <p className="text-sm text-muted-foreground mt-2">{plan.message}</p>
        )}
      </CardHeader>
      <CardContent className="space-y-4">
        {/* Progress */}
        <div className="flex items-center justify-between text-sm">
          <span className="text-muted-foreground">
            {plan.completed_tasks}/{plan.tasks.length} tasks completed
          </span>
          <span className="text-muted-foreground">
            {Math.round(plan.completed_tasks / plan.tasks.length * 100)}%
          </span>
        </div>
        
        {/* Day Tabs */}
        <div className="flex gap-1 overflow-x-auto pb-2">
          {days.map((day) => {
            const dayTasks = tasksByDay[day] || []
            const completed = dayTasks.filter(t => t.completed).length
            const isToday = day === today
            
            return (
              <button
                key={day}
                onClick={() => setSelectedDay(day)}
                className={cn(
                  'flex-shrink-0 px-3 py-2 rounded-lg text-xs font-medium transition-colors',
                  selectedDay === day
                    ? 'bg-primary text-primary-foreground'
                    : isToday
                    ? 'bg-primary/10 text-primary'
                    : 'bg-muted hover:bg-muted/80'
                )}
              >
                <div>{day.slice(0, 3)}</div>
                {dayTasks.length > 0 && (
                  <div className="text-[10px] mt-0.5">
                    {completed}/{dayTasks.length}
                  </div>
                )}
              </button>
            )
          })}
        </div>
        
        {/* Tasks for Selected Day */}
        <AnimatePresence mode="wait">
          {selectedDay && tasksByDay[selectedDay] && (
            <motion.div
              key={selectedDay}
              initial={{ opacity: 0, y: 10 }}
              animate={{ opacity: 1, y: 0 }}
              exit={{ opacity: 0, y: -10 }}
              className="space-y-2"
            >
              {tasksByDay[selectedDay].map((task, i) => {
                const SkillIcon = skillIcons[task.skill] || BookOpen
                
                return (
                  <motion.div
                    key={task.id}
                    initial={{ opacity: 0, x: -20 }}
                    animate={{ opacity: 1, x: 0 }}
                    transition={{ delay: i * 0.05 }}
                    className={cn(
                      'flex items-center gap-3 p-3 rounded-lg border transition-colors',
                      task.completed
                        ? 'bg-green-500/5 border-green-200'
                        : 'bg-muted/50 hover:bg-muted'
                    )}
                  >
                    <button
                      onClick={() => toggleTask(task.id, !task.completed)}
                      className={cn(
                        'w-5 h-5 rounded-full border-2 flex items-center justify-center flex-shrink-0 transition-colors',
                        task.completed
                          ? 'bg-green-500 border-green-500'
                          : 'border-muted-foreground hover:border-primary'
                      )}
                    >
                      {task.completed && <Check className="h-3 w-3 text-white" />}
                    </button>
                    
                    <SkillIcon className={cn(
                      'h-4 w-4 flex-shrink-0',
                      task.completed ? 'text-green-500' : 'text-muted-foreground'
                    )} />
                    
                    <div className="flex-1 min-w-0">
                      <p className={cn(
                        'text-sm font-medium truncate',
                        task.completed && 'line-through text-muted-foreground'
                      )}>
                        {task.title}
                      </p>
                      <div className="flex items-center gap-2 mt-0.5">
                        <Badge variant="outline" className="text-[10px]">
                          {task.skill}
                        </Badge>
                        <span className="text-[10px] text-muted-foreground">
                          {task.duration_minutes}min
                        </span>
                      </div>
                    </div>
                    
                    <ChevronRight className="h-4 w-4 text-muted-foreground" />
                  </motion.div>
                )
              })}
            </motion.div>
          )}
        </AnimatePresence>
        
        {/* Focus Skills */}
        {plan.focus_skills.length > 0 && (
          <div className="pt-4 border-t">
            <p className="text-xs text-muted-foreground mb-2">Focus areas this week:</p>
            <div className="flex flex-wrap gap-1">
              {plan.focus_skills.map((skill) => (
                <Badge key={skill} variant="secondary" className="text-xs capitalize">
                  {skill}
                </Badge>
              ))}
              {plan.grammar_focus && (
                <Badge variant="outline" className="text-xs">
                  Grammar: {plan.grammar_focus}
                </Badge>
              )}
            </div>
          </div>
        )}
        
        {/* Exam Countdown */}
        {plan.days_until_exam !== null && (
          <div className="p-3 rounded-lg bg-yellow-500/10 border border-yellow-200">
            <div className="flex items-center gap-2">
              <Target className="h-4 w-4 text-yellow-600" />
              <span className="text-sm font-medium text-yellow-700">
                {plan.days_until_exam} days until your exam
              </span>
            </div>
          </div>
        )}
      </CardContent>
    </Card>
  )
}
