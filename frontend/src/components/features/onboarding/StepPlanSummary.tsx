'use client'

import { motion } from 'framer-motion'
import { Rocket, Calendar, Target, Clock, ArrowRight, RefreshCw, Play } from 'lucide-react'
import { Card, CardContent } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { useOnboardingStore } from '@/lib/store/onboardingStore'
import { useRouter } from 'next/navigation'
import { cn } from '@/lib/utils'

const staggerContainer = {
  initial: {},
  animate: {
    transition: { staggerChildren: 0.1 },
  },
}

const fadeInUp = {
  initial: { opacity: 0, y: 20 },
  animate: { opacity: 1, y: 0 },
}

const SKILL_COLORS: Record<string, string> = {
  reading: 'bg-blue-500/10 text-blue-700 border-blue-200',
  writing: 'bg-purple-500/10 text-purple-700 border-purple-200',
  listening: 'bg-green-500/10 text-green-700 border-green-200',
  speaking: 'bg-orange-500/10 text-orange-700 border-orange-200',
}

const SKILL_ROUTES: Record<string, string> = {
  reading: '/practice/reading?auto=ai',
  writing: '/practice/writing?auto=ai',
  listening: '/practice/listening?auto=ai',
  speaking: '/practice/speaking?auto=ai',
}

export function StepPlanSummary() {
  const { plan, submitOnboarding, isSubmitting, error } = useOnboardingStore()
  const router = useRouter()

  if (!plan) {
    return (
      <Card>
        <CardContent className="p-8 text-center space-y-4">
          <div className="animate-pulse space-y-3">
            <div className="h-6 bg-muted rounded w-2/3 mx-auto" />
            <div className="h-4 bg-muted rounded w-1/2 mx-auto" />
            <div className="h-32 bg-muted rounded mt-4" />
          </div>
          <p className="text-sm text-muted-foreground">Generating your personalized plan...</p>
        </CardContent>
      </Card>
    )
  }

  return (
    <motion.div
      variants={staggerContainer}
      initial="initial"
      animate="animate"
      className="space-y-5"
    >
      {/* Motivational Message */}
      <motion.div variants={fadeInUp}>
        <Card className="border-primary/20 bg-gradient-to-r from-primary/5 to-primary/10">
          <CardContent className="p-6">
            <div className="flex items-start gap-4">
              <div className="h-12 w-12 rounded-full bg-primary/20 flex items-center justify-center shrink-0">
                <Rocket className="h-6 w-6 text-primary" />
              </div>
              <div>
                <h3 className="font-semibold text-lg mb-1">Your Journey Starts Now</h3>
                <p className="text-muted-foreground">{plan.motivational_message}</p>
                {plan.estimated_weeks_to_target && (
                  <p className="text-sm text-primary font-medium mt-2">
                    Estimated time to reach your target: ~{plan.estimated_weeks_to_target} weeks
                  </p>
                )}
              </div>
            </div>
          </CardContent>
        </Card>
      </motion.div>

      {/* Skill Priorities — click to start practicing */}
      <motion.div variants={fadeInUp}>
        <Card>
          <CardContent className="p-6">
            <div className="flex items-center gap-2 mb-4">
              <Target className="h-5 w-5 text-primary" />
              <h3 className="font-semibold">Skill Priorities</h3>
              <span className="text-xs text-muted-foreground ml-auto">Click to start practicing</span>
            </div>
            <div className="space-y-3">
              {plan.skill_priorities.map((priority, index) => (
                <button
                  key={index}
                  onClick={() => {
                    const route = SKILL_ROUTES[priority.skill.toLowerCase()]
                    if (route) router.push(route)
                  }}
                  className={cn(
                    'w-full flex items-center justify-between p-3 rounded-xl border transition-all',
                    'hover:shadow-md hover:scale-[1.01] active:scale-[0.99] cursor-pointer text-left',
                    SKILL_COLORS[priority.skill] || 'bg-muted/50 border-border'
                  )}
                >
                  <div className="flex-1">
                    <span className="font-medium capitalize">{priority.skill}</span>
                    <p className="text-xs opacity-80 mt-0.5">{priority.reason}</p>
                  </div>
                  <div className="flex items-center gap-3">
                    <div className="flex items-center gap-1 text-sm font-medium">
                      <Clock className="h-3.5 w-3.5" />
                      {priority.suggested_hours}h/day
                    </div>
                    <div className="h-7 w-7 rounded-full bg-current/10 flex items-center justify-center">
                      <Play className="h-3.5 w-3.5" />
                    </div>
                  </div>
                </button>
              ))}
            </div>
          </CardContent>
        </Card>
      </motion.div>

      {/* Weekly Focus Roadmap */}
      <motion.div variants={fadeInUp}>
        <Card>
          <CardContent className="p-6">
            <div className="flex items-center gap-2 mb-4">
              <Calendar className="h-5 w-5 text-primary" />
              <h3 className="font-semibold">Weekly Focus Plan</h3>
            </div>
            <div className="space-y-2">
              {plan.weekly_focus.map((week, index) => (
                <div
                  key={index}
                  className="flex items-start gap-3 p-3 rounded-lg bg-muted/30"
                >
                  <div className="h-6 w-6 rounded-full bg-primary/20 flex items-center justify-center shrink-0 mt-0.5">
                    <span className="text-xs font-bold text-primary">{index + 1}</span>
                  </div>
                  <p className="text-sm">{week}</p>
                </div>
              ))}
            </div>
          </CardContent>
        </Card>
      </motion.div>

      {/* Daily Schedule Suggestion */}
      <motion.div variants={fadeInUp}>
        <Card>
          <CardContent className="p-6">
            <div className="flex items-center gap-2 mb-3">
              <Clock className="h-5 w-5 text-primary" />
              <h3 className="font-semibold">Daily Schedule</h3>
            </div>
            <p className="text-sm text-muted-foreground leading-relaxed">
              {plan.study_schedule_suggestion}
            </p>
          </CardContent>
        </Card>
      </motion.div>

      {/* Error state */}
      {error && (
        <motion.div variants={fadeInUp}>
          <div className="p-3 rounded-lg bg-destructive/10 border border-destructive/20 text-destructive text-sm flex items-center justify-between">
            <span>{error}</span>
            <Button variant="ghost" size="sm" onClick={submitOnboarding} disabled={isSubmitting}>
              <RefreshCw className="h-3.5 w-3.5 mr-1" />
              Retry
            </Button>
          </div>
        </motion.div>
      )}

      {/* CTA */}
      <motion.div variants={fadeInUp} className="pt-2">
        <Button
          size="xl"
          className="w-full"
          onClick={() => router.push('/')}
        >
          Start Learning
          <ArrowRight className="h-5 w-5 ml-2" />
        </Button>
      </motion.div>
    </motion.div>
  )
}
