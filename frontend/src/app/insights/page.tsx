'use client'

import { motion } from 'framer-motion'
import { BarChart3, TrendingUp, Calendar, Target, Clock, Award, ArrowRight } from 'lucide-react'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Badge } from '@/components/ui/badge'
import { Progress } from '@/components/ui/progress'
import { mockProgress, mockMistakeTrends, mockWeeklyReport, mockBandScore, mockUser } from '@/lib/mock-data/user'
import { ErrorReportCard } from '@/components/features/insights/ErrorReportCard'
import { MishearingProfileCard } from '@/components/features/insights/MishearingProfileCard'
import { BandTrajectoryCard } from '@/components/features/insights/BandTrajectoryCard'
import { cn } from '@/lib/utils'
import { fadeInUp, staggerItem, staggerContainer } from '@/lib/animations'

export default function InsightsPage() {
  // Calculate predicted band
  const predictedBand = 7.0
  const weeksToTarget = 6

  return (
    <div className="space-y-6">
      {/* Header */}
      <motion.div
        initial={{ opacity: 0, y: -20 }}
        animate={{ opacity: 1, y: 0 }}
      >
        <h1 className="text-3xl font-bold mb-2">AI Insights</h1>
        <p className="text-muted-foreground">
          Track your progress and get personalized predictions
        </p>
      </motion.div>

      {/* Band Prediction */}
      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ delay: 0.1 }}
      >
        <Card className="bg-gradient-to-r from-primary to-secondary text-white overflow-hidden">
          <CardContent className="p-8">
            <div className="flex flex-col md:flex-row md:items-center md:justify-between gap-6">
              <div>
                <div className="flex items-center gap-2 mb-2">
                  <Target className="h-5 w-5" />
                  <span className="text-white/80">Band Prediction</span>
                </div>
                <div className="flex items-baseline gap-3">
                  <span className="text-5xl font-bold">{predictedBand}</span>
                  <span className="text-white/70">predicted</span>
                </div>
                <p className="text-white/80 mt-2">
                  Based on your progress, you're on track to achieve Band {predictedBand} within {weeksToTarget} weeks
                </p>
              </div>
              
              <div className="flex gap-8">
                {[
                  { label: 'Current', value: mockBandScore.reading, icon: TrendingUp },
                  { label: 'Target', value: mockUser.targetBand, icon: Target },
                ].map((stat) => (
                  <div key={stat.label} className="text-center">
                    <stat.icon className="h-6 w-6 mx-auto mb-2 opacity-70" />
                    <p className="text-2xl font-bold">{stat.value}</p>
                    <p className="text-xs text-white/70">{stat.label}</p>
                  </div>
                ))}
              </div>
            </div>
          </CardContent>
        </Card>
      </motion.div>

      {/* Stats Grid */}
      <motion.div
        variants={staggerContainer}
        initial="initial"
        animate="animate"
        className="grid grid-cols-2 md:grid-cols-4 gap-4"
      >
        {[
          { label: 'This Week', value: `${mockWeeklyReport.timeSpent}min`, icon: Clock, color: 'text-blue-500' },
          { label: 'Tasks Done', value: mockWeeklyReport.tasksCompleted, icon: Award, color: 'text-green-500' },
          { label: 'Improvement', value: `+${mockWeeklyReport.improvement}`, icon: TrendingUp, color: 'text-purple-500' },
          { label: 'Streak', value: `${mockUser.streak} days`, icon: Calendar, color: 'text-orange-500' },
        ].map((stat) => (
          <motion.div key={stat.label} variants={staggerItem}>
            <Card>
              <CardContent className="p-4 text-center">
                <stat.icon className={cn("h-6 w-6 mx-auto mb-2", stat.color)} />
                <p className="text-2xl font-bold">{stat.value}</p>
                <p className="text-xs text-muted-foreground">{stat.label}</p>
              </CardContent>
            </Card>
          </motion.div>
        ))}
      </motion.div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Progress Chart */}
        <motion.div
          initial={{ opacity: 0, x: -20 }}
          animate={{ opacity: 1, x: 0 }}
          transition={{ delay: 0.2 }}
        >
          <Card>
            <CardHeader>
              <CardTitle className="text-base flex items-center gap-2">
                <BarChart3 className="h-4 w-4" />
                Band Progress
              </CardTitle>
            </CardHeader>
            <CardContent>
              <div className="flex items-end gap-3 h-48">
                {mockProgress.map((week, index) => {
                  const height = ((week.band - 5.5) / 3) * 100
                  return (
                    <div key={week.week} className="flex-1 flex flex-col items-center gap-2">
                      <motion.div
                        initial={{ height: 0 }}
                        animate={{ height: `${Math.max(height, 10)}%` }}
                        transition={{ delay: index * 0.1, duration: 0.5 }}
                        className="w-full bg-primary rounded-t-lg relative group"
                      >
                        <div className="absolute bottom-full mb-2 left-1/2 -translate-x-1/2 bg-primary text-white text-xs px-2 py-1 rounded opacity-0 group-hover:opacity-100 transition-opacity whitespace-nowrap">
                          Band {week.band}
                        </div>
                      </motion.div>
                      <span className="text-[10px] text-muted-foreground -rotate-45 origin-center">
                        {week.week.replace('Week ', 'W')}
                      </span>
                    </div>
                  )
                })}
              </div>
            </CardContent>
          </Card>
        </motion.div>

        {/* Skills Breakdown */}
        <motion.div
          initial={{ opacity: 0, x: 20 }}
          animate={{ opacity: 1, x: 0 }}
          transition={{ delay: 0.3 }}
        >
          <Card>
            <CardHeader>
              <CardTitle className="text-base">Skills Breakdown</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="space-y-4">
                {[
                  { name: 'Reading', value: mockBandScore.reading, color: 'bg-blue-500' },
                  { name: 'Listening', value: mockBandScore.listening, color: 'bg-green-500' },
                  { name: 'Speaking', value: mockBandScore.speaking, color: 'bg-purple-500' },
                  { name: 'Writing', value: mockBandScore.writing, color: 'bg-orange-500' },
                ].map((skill) => (
                  <div key={skill.name} className="space-y-2">
                    <div className="flex items-center justify-between">
                      <span className="text-sm font-medium">{skill.name}</span>
                      <span className="text-sm text-muted-foreground">Band {skill.value}</span>
                    </div>
                    <div className="h-3 bg-muted rounded-full overflow-hidden">
                      <motion.div
                        initial={{ width: 0 }}
                        animate={{ width: `${(skill.value / 9) * 100}%` }}
                        transition={{ duration: 1, delay: 0.2 }}
                        className={cn("h-full rounded-full", skill.color)}
                      />
                    </div>
                  </div>
                ))}
              </div>

              <Button variant="outline" className="w-full mt-6">
                View Detailed Analysis
                <ArrowRight className="h-4 w-4 ml-2" />
              </Button>
            </CardContent>
          </Card>
        </motion.div>
      </div>

      {/* Weekly Report */}
      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ delay: 0.4 }}
      >
        <Card>
          <CardHeader>
            <CardTitle className="text-base">Weekly Report</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
              {mockWeeklyReport.skills.map((skill) => (
                <div key={skill.name} className="p-4 rounded-xl bg-muted/50">
                  <div className="flex items-center justify-between mb-2">
                    <span className="font-medium">{skill.name}</span>
                    <Badge variant={skill.progress > 0 ? 'success' : 'secondary'}>
                      +{skill.progress}%
                    </Badge>
                  </div>
                  <Progress value={(skill.progress / 10) * 100} className="h-2" />
                  <p className="text-xs text-muted-foreground mt-2">Improvement this week</p>
                </div>
              ))}
            </div>
          </CardContent>
        </Card>
      </motion.div>

      {/* Band Score Trajectory */}
      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ delay: 0.35 }}
      >
        <BandTrajectoryCard />
      </motion.div>

      {/* Error DNA Report */}
      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ delay: 0.5 }}
      >
        <ErrorReportCard />
      </motion.div>

      {/* Mishearing Profile (from Dictation) */}
      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ delay: 0.6 }}
      >
        <MishearingProfileCard />
      </motion.div>
    </div>
  )
}