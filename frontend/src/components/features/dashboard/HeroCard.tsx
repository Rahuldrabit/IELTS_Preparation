'use client'

import { useState } from 'react'
import { motion } from 'framer-motion'
import { Target, Calendar, Flame, ArrowRight, Trophy } from 'lucide-react'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Progress } from '@/components/ui/progress'
import { useRouter } from 'next/navigation'
import { useProfile } from '@/lib/hooks/useProfile'
import { getGreeting, calculateDaysUntil } from '@/lib/utils'
import { progressRing, fadeInUp, staggerItem } from '@/lib/animations'
import { SkillPickerDialog } from '@/components/features/journey/SkillPickerDialog'

interface ProgressRingProps {
  value: number
  max: number
  size?: number
  strokeWidth?: number
}

function ProgressRing({ value, max, size = 120, strokeWidth = 8 }: ProgressRingProps) {
  const radius = (size - strokeWidth) / 2
  const circumference = radius * 2 * Math.PI
  const progress = (value / max) * 100
  const offset = circumference - (progress / 100) * circumference

  return (
    <div className="relative" style={{ width: size, height: size }}>
      <svg className="transform -rotate-90" width={size} height={size}>
        {/* Background circle */}
        <circle
          cx={size / 2}
          cy={size / 2}
          r={radius}
          stroke="currentColor"
          strokeWidth={strokeWidth}
          fill="none"
          className="text-muted"
        />
        {/* Progress circle */}
        <motion.circle
          cx={size / 2}
          cy={size / 2}
          r={radius}
          stroke="currentColor"
          strokeWidth={strokeWidth}
          fill="none"
          className="text-primary"
          strokeLinecap="round"
          initial={{ strokeDashoffset: circumference }}
          animate={{ strokeDashoffset: offset }}
          variants={progressRing}
          style={{
            strokeDasharray: circumference,
          }}
        />
      </svg>
      <div className="absolute inset-0 flex flex-col items-center justify-center">
        <span className="text-2xl font-bold">{value}</span>
        <span className="text-xs text-muted-foreground">band</span>
      </div>
    </div>
  )
}

export function HeroCard() {
  const { data: user, isLoading } = useProfile()
  const router = useRouter()
  const [journeyDialogOpen, setJourneyDialogOpen] = useState(false)
  const daysUntil = user?.exam_date ? calculateDaysUntil(new Date(user.exam_date)) : 0
  const goalProgress = user ? (user.tasks_completed / user.daily_goal) * 100 : 0

  if (isLoading) {
    return (
      <Card className="overflow-hidden border-0 bg-gradient-to-br from-primary/80 to-secondary/80 shadow-xl">
        <CardContent className="p-8">
          <div className="flex items-center justify-center h-48">
            <p className="text-white/80">Loading...</p>
          </div>
        </CardContent>
      </Card>
    )
  }

  if (!user) return null

  return (
    <motion.div variants={fadeInUp} initial="initial" animate="animate">
      <Card className="overflow-hidden border-0 bg-gradient-to-br from-primary via-primary/90 to-secondary shadow-xl">
        <CardContent className="p-8">
          <div className="flex flex-col lg:flex-row lg:items-center lg:justify-between gap-8">
            {/* Left side - Greeting and stats */}
            <div className="space-y-6">
              <div>
                <motion.p 
                  initial={{ opacity: 0, y: 10 }}
                  animate={{ opacity: 1, y: 0 }}
                  className="text-white/80 text-lg mb-1"
                >
                  {getGreeting()}, {user.name}!
                </motion.p>
                <motion.h1 
                  initial={{ opacity: 0, y: 10 }}
                  animate={{ opacity: 1, y: 0 }}
                  transition={{ delay: 0.1 }}
                  className="text-3xl lg:text-4xl font-bold text-white"
                >
                  Ready to ace IELTS?
                </motion.h1>
              </div>

              <div className="flex flex-wrap gap-6">
                {/* Target band */}
                <motion.div 
                  initial={{ opacity: 0, x: -20 }}
                  animate={{ opacity: 1, x: 0 }}
                  transition={{ delay: 0.2 }}
                  className="flex items-center gap-3"
                >
                  <div className="flex h-10 w-10 items-center justify-center rounded-xl bg-white/20">
                    <Target className="h-5 w-5 text-white" />
                  </div>
                  <div>
                    <p className="text-white/70 text-xs">Target Band</p>
                    <p className="text-white font-semibold">{user.target_band}</p>
                  </div>
                </motion.div>

                {/* Days until exam */}
                <motion.div 
                  initial={{ opacity: 0, x: -20 }}
                  animate={{ opacity: 1, x: 0 }}
                  transition={{ delay: 0.3 }}
                  className="flex items-center gap-3"
                >
                  <div className="flex h-10 w-10 items-center justify-center rounded-xl bg-white/20">
                    <Calendar className="h-5 w-5 text-white" />
                  </div>
                  <div>
                    <p className="text-white/70 text-xs">Days Until Exam</p>
                    <p className="text-white font-semibold">{daysUntil} days</p>
                  </div>
                </motion.div>

                {/* Streak */}
                <motion.div 
                  initial={{ opacity: 0, x: -20 }}
                  animate={{ opacity: 1, x: 0 }}
                  transition={{ delay: 0.4 }}
                  className="flex items-center gap-3"
                >
                  <div className="flex h-10 w-10 items-center justify-center rounded-xl bg-white/20">
                    <Flame className="h-5 w-5 text-white" />
                  </div>
                  <div>
                    <p className="text-white/70 text-xs">Day Streak</p>
                    <p className="text-white font-semibold">{user.streak} days</p>
                  </div>
                </motion.div>
              </div>

              {/* Daily goal */}
              <motion.div 
                initial={{ opacity: 0, y: 10 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ delay: 0.5 }}
                className="bg-white/10 rounded-xl p-4 space-y-2"
              >
                <div className="flex justify-between items-center">
                  <span className="text-white/90 text-sm font-medium">Daily Goal</span>
                  <span className="text-white/90 text-sm">{user.tasks_completed}/{user.daily_goal} tasks</span>
                </div>
                <Progress value={goalProgress} className="h-2 bg-white/20" />
              </motion.div>
            </div>

            {/* Right side - Progress ring and CTA */}
            <div className="flex flex-col items-center gap-6">
              <motion.div
                initial={{ scale: 0.8, opacity: 0 }}
                animate={{ scale: 1, opacity: 1 }}
                transition={{ delay: 0.3, type: 'spring' }}
              >
                <ProgressRing value={user.current_band} max={user.target_band} />
              </motion.div>

              <motion.div
                initial={{ opacity: 0, y: 20 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ delay: 0.5 }}
              >
                <div className="flex flex-col sm:flex-row gap-3">
                  <Button 
                    size="xl" 
                    className="bg-white text-primary hover:bg-white/90 shadow-lg"
                    onClick={() => setJourneyDialogOpen(true)}
                  >
                    Start Today's Journey
                    <ArrowRight className="ml-2 h-5 w-5" />
                  </Button>
                  <Button 
                    size="xl"
                    variant="outline"
                    className="border-white text-white hover:bg-white/20 shadow-lg"
                    onClick={() => router.push('/insights')}
                  >
                    View AI Analytics
                    <Trophy className="ml-2 h-5 w-5" />
                  </Button>
                </div>
              </motion.div>
            </div>
          </div>
        </CardContent>
      </Card>

      <SkillPickerDialog open={journeyDialogOpen} onOpenChange={setJourneyDialogOpen} />
    </motion.div>
  )
}