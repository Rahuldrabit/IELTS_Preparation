'use client'

import { useEffect } from 'react'
import { useRouter } from 'next/navigation'
import { motion } from 'framer-motion'
import {
  ArrowLeft, TrendingUp, Target, Calendar, AlertCircle, CheckCircle2,
  BarChart3, Flame
} from 'lucide-react'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Progress } from '@/components/ui/progress'
import { useGrammarStore } from '@/lib/store/grammarStore'

export default function GrammarAnalyticsPage() {
  const router = useRouter()
  const { analytics, isLoading, fetchAnalytics } = useGrammarStore()

  useEffect(() => {
    fetchAnalytics()
  }, [fetchAnalytics])

  if (isLoading && !analytics) {
    return (
      <div className="flex items-center justify-center h-32">
        <BarChart3 className="h-6 w-6 text-primary animate-pulse" />
      </div>
    )
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center gap-4">
        <Button variant="ghost" size="icon" onClick={() => router.push('/practice/grammar')}>
          <ArrowLeft className="h-4 w-4" />
        </Button>
        <div>
          <h1 className="text-2xl font-bold flex items-center gap-2">
            <BarChart3 className="h-6 w-6 text-primary" />
            Grammar Analytics
          </h1>
          <p className="text-muted-foreground">Track your grammar learning progress</p>
        </div>
      </div>

      {/* Stats Grid */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
        <motion.div initial={{ opacity: 0, y: 10 }} animate={{ opacity: 1, y: 0 }} transition={{ delay: 0 }}>
          <Card>
            <CardContent className="p-4 text-center">
              <TrendingUp className="h-8 w-8 text-primary mx-auto mb-2" />
              <p className="text-2xl font-bold text-primary">
                {analytics?.overall_grammar.toFixed(1) || 0}%
              </p>
              <p className="text-xs text-muted-foreground">Overall Grammar</p>
            </CardContent>
          </Card>
        </motion.div>

        <motion.div initial={{ opacity: 0, y: 10 }} animate={{ opacity: 1, y: 0 }} transition={{ delay: 0.05 }}>
          <Card>
            <CardContent className="p-4 text-center">
              <Target className="h-8 w-8 text-blue-500 mx-auto mb-2" />
              <p className="text-2xl font-bold">
                {analytics?.today_accuracy ? `${analytics.today_accuracy.toFixed(0)}%` : '--'}
              </p>
              <p className="text-xs text-muted-foreground">Today&apos;s Accuracy</p>
            </CardContent>
          </Card>
        </motion.div>

        <motion.div initial={{ opacity: 0, y: 10 }} animate={{ opacity: 1, y: 0 }} transition={{ delay: 0.1 }}>
          <Card>
            <CardContent className="p-4 text-center">
              <Flame className="h-8 w-8 text-orange-500 mx-auto mb-2" />
              <p className="text-2xl font-bold">
                {analytics?.grammar_streak || 0}
              </p>
              <p className="text-xs text-muted-foreground">Day Streak</p>
            </CardContent>
          </Card>
        </motion.div>

        <motion.div initial={{ opacity: 0, y: 10 }} animate={{ opacity: 1, y: 0 }} transition={{ delay: 0.15 }}>
          <Card>
            <CardContent className="p-4 text-center">
              <CheckCircle2 className="h-8 w-8 text-green-500 mx-auto mb-2" />
              <p className="text-2xl font-bold">
                {analytics?.total_exercises_completed || 0}
              </p>
              <p className="text-xs text-muted-foreground">Exercises Done</p>
            </CardContent>
          </Card>
        </motion.div>
      </div>

      {/* Mastery Progress */}
      <motion.div initial={{ opacity: 0, y: 10 }} animate={{ opacity: 1, y: 0 }} transition={{ delay: 0.2 }}>
        <Card>
          <CardHeader>
            <CardTitle className="text-base">Grammar Mastery Progress</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="space-y-2">
              <div className="flex items-center justify-between text-sm">
                <span>Overall Mastery</span>
                <span className="font-medium">{analytics?.overall_grammar.toFixed(1) || 0}%</span>
              </div>
              <Progress value={analytics?.overall_grammar || 0} className="h-4" />
            </div>
          </CardContent>
        </Card>
      </motion.div>

      {/* Weakest / Strongest */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        <motion.div initial={{ opacity: 0, x: -10 }} animate={{ opacity: 1, x: 0 }} transition={{ delay: 0.25 }}>
          <Card className="border-warning/20">
            <CardContent className="p-4">
              <div className="flex items-center gap-3">
                <AlertCircle className="h-8 w-8 text-warning" />
                <div>
                  <p className="text-sm text-muted-foreground">Weakest Topic</p>
                  <p className="font-semibold">{analytics?.weakest_topic || 'N/A'}</p>
                </div>
              </div>
            </CardContent>
          </Card>
        </motion.div>

        <motion.div initial={{ opacity: 0, x: 10 }} animate={{ opacity: 1, x: 0 }} transition={{ delay: 0.3 }}>
          <Card className="border-success/20">
            <CardContent className="p-4">
              <div className="flex items-center gap-3">
                <CheckCircle2 className="h-8 w-8 text-success" />
                <div>
                  <p className="text-sm text-muted-foreground">Strongest Topic</p>
                  <p className="font-semibold">{analytics?.strongest_topic || 'N/A'}</p>
                </div>
              </div>
            </CardContent>
          </Card>
        </motion.div>
      </div>

      {/* Weekly Stats */}
      {analytics?.weekly_stats && (
        <motion.div initial={{ opacity: 0, y: 10 }} animate={{ opacity: 1, y: 0 }} transition={{ delay: 0.35 }}>
          <Card>
            <CardHeader>
              <CardTitle className="text-base flex items-center gap-2">
                <Calendar className="h-4 w-4" />
                This Week
              </CardTitle>
            </CardHeader>
            <CardContent>
              <div className="grid grid-cols-2 gap-4">
                <div className="p-4 rounded-xl bg-muted/50 text-center">
                  <p className="text-2xl font-bold">{analytics.weekly_stats.attempts_last_week}</p>
                  <p className="text-xs text-muted-foreground">Attempts This Week</p>
                </div>
                <div className="p-4 rounded-xl bg-muted/50 text-center">
                  <p className="text-2xl font-bold">{analytics.weekly_stats.weekly_accuracy.toFixed(0)}%</p>
                  <p className="text-xs text-muted-foreground">Weekly Accuracy</p>
                </div>
              </div>
            </CardContent>
          </Card>
        </motion.div>
      )}
    </div>
  )
}