'use client'

import { useState, useEffect } from 'react'
import { motion } from 'framer-motion'
import { TrendingUp, Target, Calendar, Loader2, AlertCircle } from 'lucide-react'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Badge } from '@/components/ui/badge'
import { Progress } from '@/components/ui/progress'
import { cn } from '@/lib/utils'

interface SkillTrajectory {
  skill: string
  current_band: number
  target_band: number
  improvement_rate: number
  weeks_to_target: number | null
  confidence: number
  sessions_count: number
  trend: string
}

interface TrajectoryData {
  target_band: number
  overall_current_band: number
  overall_start_band: number
  overall_improvement_rate: number
  projected_target_date: string | null
  confidence: number
  skill_trajectories: SkillTrajectory[]
  message: string
  recommendations: string[]
}

interface BandTrajectoryCardProps {
  targetBand?: number
  className?: string
}

export function BandTrajectoryCard({ targetBand = 7.0, className }: BandTrajectoryCardProps) {
  const [trajectory, setTrajectory] = useState<TrajectoryData | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  
  useEffect(() => {
    loadTrajectory()
  }, [targetBand])
  
  const loadTrajectory = async () => {
    setLoading(true)
    setError(null)
    try {
      const response = await fetch(`/api/analytics/trajectory?target_band=${targetBand}`)
      if (!response.ok) throw new Error('Failed to load trajectory')
      const data = await response.json()
      setTrajectory(data)
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Unknown error')
    } finally {
      setLoading(false)
    }
  }
  
  if (loading) {
    return (
      <Card className={cn('animate-pulse', className)}>
        <CardContent className="p-6">
          <div className="h-32 bg-muted rounded" />
        </CardContent>
      </Card>
    )
  }
  
  if (error || !trajectory) {
    return null
  }
  
  const projectedDate = trajectory.projected_target_date
    ? new Date(trajectory.projected_target_date)
    : null
  
  const weeksRemaining = projectedDate
    ? Math.max(0, Math.ceil((projectedDate.getTime() - Date.now()) / (7 * 24 * 60 * 60 * 1000)))
    : null
  
  const progressPercent = trajectory.overall_start_band > 0
    ? Math.min(100, ((trajectory.overall_current_band - trajectory.overall_start_band) / 
       (targetBand - trajectory.overall_start_band)) * 100)
    : 0
  
  return (
    <Card className={className}>
      <CardHeader>
        <div className="flex items-center justify-between">
          <CardTitle className="text-base flex items-center gap-2">
            <TrendingUp className="h-4 w-4" />
            Band Score Trajectory
          </CardTitle>
          <Badge variant="outline">
            Target: Band {targetBand}
          </Badge>
        </div>
      </CardHeader>
      <CardContent className="space-y-6">
        {/* Main Message */}
        <div className="text-center py-2">
          <p className="text-lg font-medium">{trajectory.message}</p>
        </div>
        
        {/* Current vs Target */}
        <div className="flex items-center justify-around">
          <div className="text-center">
            <p className="text-3xl font-bold text-primary">
              {trajectory.overall_current_band.toFixed(1)}
            </p>
            <p className="text-xs text-muted-foreground">Current Band</p>
          </div>
          
          <div className="flex-1 mx-4">
            <Progress value={progressPercent} className="h-2" />
            <p className="text-xs text-center text-muted-foreground mt-1">
              {Math.round(progressPercent)}% to target
            </p>
          </div>
          
          <div className="text-center">
            <p className="text-3xl font-bold text-green-600">
              {targetBand.toFixed(1)}
            </p>
            <p className="text-xs text-muted-foreground">Target Band</p>
          </div>
        </div>
        
        {/* Projection */}
        {projectedDate && (
          <motion.div
            initial={{ opacity: 0, y: 10 }}
            animate={{ opacity: 1, y: 0 }}
            className="p-4 rounded-lg bg-green-500/10 border border-green-200"
          >
            <div className="flex items-center gap-2 mb-2">
              <Calendar className="h-4 w-4 text-green-600" />
              <span className="font-medium text-green-700">
                Projected: {projectedDate.toLocaleDateString('en-US', { 
                  month: 'short', 
                  day: 'numeric',
                  year: projectedDate.getFullYear() !== new Date().getFullYear() ? 'numeric' : undefined
                })}
              </span>
            </div>
            <p className="text-sm text-green-600">
              {weeksRemaining} week{weeksRemaining !== 1 ? 's' : ''} to reach your target at current pace
            </p>
          </motion.div>
        )}
        
        {/* Improvement Rate */}
        <div className="flex items-center justify-between text-sm">
          <span className="text-muted-foreground">Improvement rate:</span>
          <span className={cn(
            'font-medium',
            trajectory.overall_improvement_rate > 0.05 ? 'text-green-600' : 'text-yellow-600'
          )}>
            +{trajectory.overall_improvement_rate.toFixed(3)} band/week
          </span>
        </div>
        
        {/* Confidence */}
        <div className="flex items-center justify-between text-sm">
          <span className="text-muted-foreground">Confidence:</span>
          <div className="flex items-center gap-2">
            <Progress value={trajectory.confidence * 100} className="h-1 w-20" />
            <span className="text-muted-foreground">
              {Math.round(trajectory.confidence * 100)}%
            </span>
          </div>
        </div>
        
        {/* Skill Breakdown */}
        {trajectory.skill_trajectories.length > 0 && (
          <div className="space-y-3">
            <p className="text-sm font-medium">By Skill:</p>
            <div className="grid grid-cols-2 gap-2">
              {trajectory.skill_trajectories.map((skill) => (
                <SkillMiniCard key={skill.skill} skill={skill} />
              ))}
            </div>
          </div>
        )}
        
        {/* Recommendations */}
        {trajectory.recommendations.length > 0 && (
          <div className="space-y-2">
            <p className="text-sm font-medium">Recommendations:</p>
            <ul className="space-y-1">
              {trajectory.recommendations.slice(0, 2).map((rec, i) => (
                <li key={i} className="text-sm text-muted-foreground flex items-start gap-2">
                  <Target className="h-3 w-3 text-blue-500 mt-1 flex-shrink-0" />
                  {rec}
                </li>
              ))}
            </ul>
          </div>
        )}
      </CardContent>
    </Card>
  )
}

function SkillMiniCard({ skill }: { skill: SkillTrajectory }) {
  const trendColors = {
    improving: 'text-green-600',
    stable: 'text-yellow-600',
    declining: 'text-red-600',
  }
  
  return (
    <div className="p-2 rounded bg-muted/50 text-xs">
      <div className="flex items-center justify-between mb-1">
        <span className="capitalize">{skill.skill}</span>
        <span className={trendColors[skill.trend as keyof typeof trendColors]}>
          {skill.trend === 'improving' ? '↑' : skill.trend === 'declining' ? '↓' : '→'}
        </span>
      </div>
      <div className="flex items-center justify-between">
        <span className="font-medium">{skill.current_band.toFixed(1)}</span>
        <span className="text-muted-foreground">
          {skill.weeks_to_target ? `${skill.weeks_to_target}w` : '—'}
        </span>
      </div>
    </div>
  )
}
