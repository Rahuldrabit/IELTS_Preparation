/**
 * UmaInterventionCard — surfaces the Autonomous Syllabus Curating Agent's
 * personalised intervention on the dashboard.
 *
 * Fetches the latest stored intervention from GET /api/profile/uma-intervention.
 * Shows a shimmer skeleton while loading; shows nothing if no intervention exists yet.
 *
 * The agent identifies the student's single highest-leverage weakness,
 * writes a data-driven insight, and lists prioritised tasks.
 * All analysis runs on the backend — this component only renders the JSON result.
 */
'use client'

import { useEffect, useState } from 'react'
import { motion, AnimatePresence } from 'framer-motion'
import {
  Brain, Zap, BookOpen, Headphones, Mic, PenTool,
  ChevronDown, ArrowRight, Sparkles, FlaskConical,
} from 'lucide-react'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Badge } from '@/components/ui/badge'
import { Button } from '@/components/ui/button'
import { cn } from '@/lib/utils'
import { profileApi, type UmaIntervention, type UmaRoadmapTask } from '@/lib/services/profile'
import Link from 'next/link'

// ─────────────────────────────────────────────
//  Skill helpers
// ─────────────────────────────────────────────

function getSkillIcon(skill: string) {
  switch (skill) {
    case 'speaking':  return Mic
    case 'reading':   return BookOpen
    case 'listening': return Headphones
    case 'writing':   return PenTool
    default:          return BookOpen
  }
}

function getSkillColor(skill: string) {
  switch (skill) {
    case 'speaking':  return 'bg-purple-100 dark:bg-purple-900/30 text-purple-700 dark:text-purple-300 border-purple-300'
    case 'reading':   return 'bg-blue-100 dark:bg-blue-900/30 text-blue-700 dark:text-blue-300 border-blue-300'
    case 'listening': return 'bg-green-100 dark:bg-green-900/30 text-green-700 dark:text-green-300 border-green-300'
    case 'writing':   return 'bg-orange-100 dark:bg-orange-900/30 text-orange-700 dark:text-orange-300 border-orange-300'
    default:          return 'bg-muted text-muted-foreground border-border'
  }
}

function getPracticeHref(skill: string) {
  return `/practice/${skill}`
}

// ─────────────────────────────────────────────
//  Task row
// ─────────────────────────────────────────────

function TaskRow({ task }: { task: UmaRoadmapTask }) {
  const Icon = getSkillIcon(task.skill)
  return (
    <div className="flex items-start gap-3 p-3 rounded-xl bg-muted/40 hover:bg-muted/70 transition-colors group">
      <div className={cn('h-7 w-7 rounded-lg flex items-center justify-center shrink-0', getSkillColor(task.skill))}>
        <Icon className="h-3.5 w-3.5" />
      </div>
      <div className="flex-1 min-w-0">
        <p className="text-sm font-medium leading-tight">{task.title}</p>
        <p className="text-xs text-muted-foreground mt-0.5 leading-relaxed">{task.description}</p>
      </div>
      <Link href={getPracticeHref(task.skill)}>
        <ArrowRight className="h-4 w-4 text-muted-foreground opacity-0 group-hover:opacity-100 transition-opacity shrink-0 mt-0.5" />
      </Link>
    </div>
  )
}

// ─────────────────────────────────────────────
//  Skeleton
// ─────────────────────────────────────────────

function Skeleton() {
  return (
    <Card className="h-full border-primary/20 animate-pulse">
      <CardHeader className="pb-3">
        <div className="h-5 w-40 bg-muted rounded" />
      </CardHeader>
      <CardContent className="space-y-3">
        <div className="h-4 w-full bg-muted rounded" />
        <div className="h-4 w-3/4 bg-muted rounded" />
        <div className="h-16 w-full bg-muted rounded-xl" />
        <div className="h-12 w-full bg-muted rounded-xl" />
      </CardContent>
    </Card>
  )
}

// ─────────────────────────────────────────────
//  Main component
// ─────────────────────────────────────────────

export function UmaInterventionCard() {
  const [intervention, setIntervention] = useState<UmaIntervention | null>(null)
  const [loading, setLoading]           = useState(true)
  const [tasksExpanded, setTasksExpanded] = useState(false)

  useEffect(() => {
    profileApi.getUmaIntervention()
      .then((data) => setIntervention(data))
      .catch(() => {/* No intervention yet — show nothing */})
      .finally(() => setLoading(false))
  }, [])

  if (loading) return <Skeleton />

  // No intervention yet — show a placeholder prompting the student to complete a session
  if (!intervention) {
    return (
      <motion.div initial={{ opacity: 0, y: 16 }} animate={{ opacity: 1, y: 0 }}>
        <Card className="h-full border-dashed border-primary/20">
          <CardContent className="flex flex-col items-center justify-center text-center py-10 gap-3">
            <div className="h-12 w-12 rounded-full bg-primary/10 flex items-center justify-center">
              <FlaskConical className="h-6 w-6 text-primary" />
            </div>
            <p className="font-medium text-sm">Uma hasn't analysed your patterns yet</p>
            <p className="text-xs text-muted-foreground max-w-[200px]">
              Complete a reading or writing session and Uma will build a personalised intervention.
            </p>
          </CardContent>
        </Card>
      </motion.div>
    )
  }

  const SkillIcon = getSkillIcon(intervention.targeted_skill)

  return (
    <motion.div
      initial={{ opacity: 0, y: 16 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.4 }}
    >
      <Card className="h-full border-primary/30 bg-gradient-to-br from-primary/5 to-transparent">
        <CardHeader className="pb-3">
          <CardTitle className="text-base flex items-center gap-2">
            <div className="h-6 w-6 rounded-full bg-primary/15 flex items-center justify-center">
              <Brain className="h-3.5 w-3.5 text-primary" />
            </div>
            <span>Uma's Intervention</span>
            <Badge variant="outline" className={cn('ml-auto text-xs', getSkillColor(intervention.targeted_skill))}>
              <SkillIcon className="h-3 w-3 mr-1" />
              {intervention.targeted_skill}
            </Badge>
          </CardTitle>
        </CardHeader>

        <CardContent className="space-y-4">
          {/* Headline */}
          <div className="flex items-start gap-2">
            <Zap className="h-4 w-4 text-amber-500 shrink-0 mt-0.5" />
            <p className="font-semibold text-sm leading-snug">{intervention.headline}</p>
          </div>

          {/* Insight text */}
          <p className="text-sm text-muted-foreground leading-relaxed">
            {intervention.insight_text}
          </p>

          {/* Weak pattern badge */}
          <div className="flex items-center gap-2 p-2.5 rounded-lg bg-amber-50 dark:bg-amber-950/20 border border-amber-200 dark:border-amber-800">
            <Sparkles className="h-3.5 w-3.5 text-amber-500 shrink-0" />
            <p className="text-xs text-amber-700 dark:text-amber-400 font-medium">
              Pattern identified: {intervention.weak_pattern_identified}
            </p>
          </div>

          {/* Recommended tasks — collapsible */}
          {intervention.recommended_tasks.length > 0 && (
            <div>
              <button
                onClick={() => setTasksExpanded(v => !v)}
                className="flex items-center gap-1.5 text-xs font-medium text-primary hover:text-primary/80 transition-colors mb-2"
              >
                Targeted task plan ({intervention.recommended_tasks.length} tasks)
                <ChevronDown className={cn('h-3.5 w-3.5 transition-transform', tasksExpanded && 'rotate-180')} />
              </button>

              <AnimatePresence>
                {tasksExpanded && (
                  <motion.div
                    initial={{ height: 0, opacity: 0 }}
                    animate={{ height: 'auto', opacity: 1 }}
                    exit={{ height: 0, opacity: 0 }}
                    transition={{ duration: 0.2 }}
                    className="overflow-hidden space-y-2"
                  >
                    {intervention.recommended_tasks
                      .sort((a, b) => a.priority - b.priority)
                      .map((task, i) => (
                        <TaskRow key={i} task={task} />
                      ))}
                  </motion.div>
                )}
              </AnimatePresence>
            </div>
          )}

          {/* CTA — start the recommended drill */}
          <Link href={getPracticeHref(intervention.targeted_skill)}>
            <Button size="sm" className="w-full gap-2 mt-1">
              <ArrowRight className="h-3.5 w-3.5" />
              Start Targeted Practice
            </Button>
          </Link>
        </CardContent>
      </Card>
    </motion.div>
  )
}
