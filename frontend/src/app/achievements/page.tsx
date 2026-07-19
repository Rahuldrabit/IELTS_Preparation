'use client'

import { useState, useEffect } from 'react'
import { motion } from 'framer-motion'
import { Trophy, Lock, Check, Loader2, Star, Flame, Target, BookOpen } from 'lucide-react'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Badge } from '@/components/ui/badge'
import { Progress } from '@/components/ui/progress'
import { cn } from '@/lib/utils'

interface Achievement {
  achievement_id: string
  name: string
  description: string
  icon: string
  category: string
  tier: number
  unlocked_at?: string
  progress?: number
}

interface AchievementSummary {
  total_unlocked: number
  total_available: number
  by_category: Record<string, number>
  by_tier: Record<number, number>
  recent_unlocks: Achievement[]
  in_progress: Achievement[]
}

const categoryIcons: Record<string, typeof Trophy> = {
  milestone: Target,
  score: Star,
  streak: Flame,
  skill: BookOpen,
  vocabulary: BookOpen,
  special: Trophy,
}

const tierColors = {
  1: 'from-bronze-500 to-bronze-600',
  2: 'from-silver-400 to-silver-500',
  3: 'from-gold-400 to-gold-500',
  4: 'from-purple-400 to-purple-500',
}

export default function AchievementsPage() {
  const [summary, setSummary] = useState<AchievementSummary | null>(null)
  const [allAchievements, setAllAchievements] = useState<Achievement[]>([])
  const [loading, setLoading] = useState(true)
  
  useEffect(() => {
    loadData()
  }, [])
  
  const loadData = async () => {
    setLoading(true)
    try {
      const [summaryRes, allRes] = await Promise.all([
        fetch('/api/analytics/achievements'),
        fetch('/api/analytics/achievements/all'),
      ])
      
      if (summaryRes.ok) {
        setSummary(await summaryRes.json())
      }
      if (allRes.ok) {
        const data = await allRes.json()
        setAllAchievements(data.achievements)
      }
    } catch (error) {
      console.error('Failed to load achievements:', error)
    } finally {
      setLoading(false)
    }
  }
  
  if (loading) {
    return (
      <div className="container max-w-4xl mx-auto py-8 px-4">
        <div className="text-center py-12">
          <Loader2 className="h-8 w-8 mx-auto animate-spin text-muted-foreground" />
        </div>
      </div>
    )
  }
  
  const unlockedIds = new Set(summary?.recent_unlocks.map(a => a.achievement_id) || [])
  
  return (
    <div className="container max-w-4xl mx-auto py-8 px-4">
      {/* Header */}
      <motion.div
        initial={{ opacity: 0, y: -20 }}
        animate={{ opacity: 1, y: 0 }}
        className="mb-8"
      >
        <div className="flex items-center gap-3 mb-2">
          <Trophy className="h-8 w-8 text-yellow-500" />
          <h1 className="text-3xl font-bold">Achievements</h1>
        </div>
        <p className="text-muted-foreground">
          Track your milestones and unlock badges as you progress
        </p>
      </motion.div>
      
      {/* Summary Stats */}
      {summary && (
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          className="mb-8"
        >
          <Card>
            <CardContent className="py-6">
              <div className="flex items-center justify-around">
                <div className="text-center">
                  <p className="text-4xl font-bold text-primary">{summary.total_unlocked}</p>
                  <p className="text-sm text-muted-foreground">Unlocked</p>
                </div>
                <div className="h-12 w-px bg-border" />
                <div className="text-center">
                  <p className="text-4xl font-bold">{summary.total_available}</p>
                  <p className="text-sm text-muted-foreground">Total</p>
                </div>
                <div className="h-12 w-px bg-border" />
                <div className="text-center">
                  <p className="text-4xl font-bold text-yellow-500">
                    {Math.round((summary.total_unlocked / summary.total_available) * 100)}%
                  </p>
                  <p className="text-sm text-muted-foreground">Complete</p>
                </div>
              </div>
            </CardContent>
          </Card>
        </motion.div>
      )}
      
      {/* Recent Unlocks */}
      {summary?.recent_unlocks && summary.recent_unlocks.length > 0 && (
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.1 }}
          className="mb-8"
        >
          <h2 className="text-xl font-bold mb-4">Recently Unlocked</h2>
          <div className="grid grid-cols-2 md:grid-cols-3 gap-4">
            {summary.recent_unlocks.map((achievement, i) => (
              <motion.div
                key={achievement.achievement_id}
                initial={{ opacity: 0, scale: 0.9 }}
                animate={{ opacity: 1, scale: 1 }}
                transition={{ delay: i * 0.1 }}
              >
                <Card className="bg-gradient-to-br from-yellow-500/10 to-orange-500/10 border-yellow-200">
                  <CardContent className="py-6 text-center">
                    <div className="text-4xl mb-2">{achievement.icon}</div>
                    <h3 className="font-bold">{achievement.name}</h3>
                    <p className="text-xs text-muted-foreground mt-1">{achievement.description}</p>
                    {achievement.unlocked_at && (
                      <p className="text-xs text-muted-foreground mt-2">
                        {new Date(achievement.unlocked_at).toLocaleDateString()}
                      </p>
                    )}
                  </CardContent>
                </Card>
              </motion.div>
            ))}
          </div>
        </motion.div>
      )}
      
      {/* In Progress */}
      {summary?.in_progress && summary.in_progress.length > 0 && (
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.2 }}
          className="mb-8"
        >
          <h2 className="text-xl font-bold mb-4">In Progress</h2>
          <div className="space-y-3">
            {summary.in_progress.map((achievement) => (
              <Card key={achievement.achievement_id}>
                <CardContent className="py-4">
                  <div className="flex items-center gap-4">
                    <div className="text-3xl opacity-50">{achievement.icon}</div>
                    <div className="flex-1">
                      <div className="flex items-center justify-between mb-1">
                        <h3 className="font-medium">{achievement.name}</h3>
                        <span className="text-sm text-muted-foreground">
                          {Math.round((achievement.progress || 0) * 100)}%
                        </span>
                      </div>
                      <Progress value={(achievement.progress || 0) * 100} className="h-2" />
                      <p className="text-xs text-muted-foreground mt-1">{achievement.description}</p>
                    </div>
                  </div>
                </CardContent>
              </Card>
            ))}
          </div>
        </motion.div>
      )}
      
      {/* All Achievements Grid */}
      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ delay: 0.3 }}
      >
        <h2 className="text-xl font-bold mb-4">All Achievements</h2>
        <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
          {allAchievements.map((achievement) => {
            const isUnlocked = unlockedIds.has(achievement.achievement_id)
            
            return (
              <motion.div
                key={achievement.achievement_id}
                whileHover={{ scale: isUnlocked ? 1.02 : 1 }}
                className={cn(
                  'relative p-4 rounded-lg border text-center transition-colors',
                  isUnlocked
                    ? 'bg-gradient-to-br from-primary/10 to-primary/5 border-primary/30'
                    : 'bg-muted/50 border-muted opacity-60'
                )}
              >
                {isUnlocked && (
                  <div className="absolute top-2 right-2">
                    <Check className="h-4 w-4 text-green-500" />
                  </div>
                )}
                <div className={cn('text-3xl mb-2', !isUnlocked && 'grayscale')}>
                  {achievement.icon}
                </div>
                <h4 className="font-medium text-sm mb-1">{achievement.name}</h4>
                <p className="text-xs text-muted-foreground line-clamp-2">{achievement.description}</p>
                <Badge
                  variant="outline"
                  className={cn(
                    'mt-2 text-xs',
                    achievement.tier === 1 && 'border-amber-700 text-amber-700',
                    achievement.tier === 2 && 'border-gray-400 text-gray-500',
                    achievement.tier === 3 && 'border-yellow-500 text-yellow-600',
                    achievement.tier === 4 && 'border-purple-500 text-purple-600'
                  )}
                >
                  Tier {achievement.tier}
                </Badge>
              </motion.div>
            )
          })}
        </div>
      </motion.div>
    </div>
  )
}
