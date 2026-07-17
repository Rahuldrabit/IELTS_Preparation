'use client'

import { useState, useEffect } from 'react'
import { motion } from 'framer-motion'
import { Lock, CheckCircle2, ChevronDown, Target, BookOpen, Headphones, Mic, PenTool, BookMarked, Loader2 } from 'lucide-react'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Progress } from '@/components/ui/progress'
import { Badge } from '@/components/ui/badge'
import { cn } from '@/lib/utils'
import { staggerItem, staggerContainer } from '@/lib/animations'
import { profileApi, type Milestone } from '@/lib/services/profile'
import { SkillPickerDialog } from '@/components/features/journey/SkillPickerDialog'

const skillIcons = {
  grammar: BookMarked,
  vocabulary: BookMarked,
  reading: BookOpen,
  listening: Headphones,
  speaking: Mic,
  writing: PenTool,
}

const skillColors = {
  grammar: 'bg-pink-500',
  vocabulary: 'bg-purple-500',
  reading: 'bg-blue-500',
  listening: 'bg-green-500',
  speaking: 'bg-orange-500',
  writing: 'bg-yellow-500',
}

export default function JourneyPage() {
  const [expandedMilestone, setExpandedMilestone] = useState<string | null>(null)
  const [milestones, setMilestones] = useState<Milestone[]>([])
  const [loading, setLoading] = useState(true)
  const [currentBand, setCurrentBand] = useState(5.5)
  const [targetBand, setTargetBand] = useState(7.0)
  const [skillPickerOpen, setSkillPickerOpen] = useState(false)

  useEffect(() => {
    async function load() {
      try {
        const [ms, profile] = await Promise.all([
          profileApi.getMilestones(),
          profileApi.getProfile(),
        ])
        setMilestones(ms)
        setCurrentBand(profile.current_band)
        setTargetBand(profile.target_band)
        // Expand the current milestone by default
        const current = ms.find(m => m.status === 'current')
        if (current) setExpandedMilestone(String(current.id))
      } catch {
        // silently fail
      } finally {
        setLoading(false)
      }
    }
    load()
  }, [])

  if (loading) {
    return (
      <div className="flex items-center justify-center py-20">
        <Loader2 className="h-8 w-8 animate-spin text-primary" />
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
        <h1 className="text-3xl font-bold mb-2">AI Learning Journey</h1>
        <p className="text-muted-foreground">
          Your personalized roadmap from {currentBand} to {targetBand}
        </p>
      </motion.div>

      {/* Progress summary */}
      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ delay: 0.1 }}
      >
        <Card>
          <CardContent className="p-6">
            <div className="flex items-center justify-between mb-4">
              <div className="flex items-center gap-3">
                <div className="flex h-12 w-12 items-center justify-center rounded-xl bg-primary/10">
                  <Target className="h-6 w-6 text-primary" />
                </div>
                <div>
                  <p className="text-sm text-muted-foreground">Overall Progress</p>
                  <p className="text-2xl font-bold">
                    {Math.round(((currentBand - 5) / (targetBand - 5)) * 100)}%
                  </p>
                </div>
              </div>
              <div className="text-right">
                <p className="text-sm text-muted-foreground">Current</p>
                <p className="text-xl font-semibold">Band {currentBand}</p>
              </div>
            </div>
            <Progress value={((currentBand - 5) / (targetBand - 5)) * 100} className="h-3" />
          </CardContent>
        </Card>
      </motion.div>

      {/* Milestone Timeline */}
      <div className="relative">
        {/* Connection line */}
        <div className="absolute left-8 top-0 bottom-0 w-0.5 bg-border" />

        <motion.div
          variants={staggerContainer}
          initial="initial"
          animate="animate"
          className="space-y-6"
        >
          {milestones.map((milestone, index) => {
            const isExpanded = expandedMilestone === String(milestone.id)
            const Icon = milestone.status === 'locked' ? Lock : milestone.status === 'completed' ? CheckCircle2 : Target
            
            return (
              <motion.div
                key={milestone.id}
                variants={staggerItem}
                className="relative pl-20"
              >
                {/* Timeline dot */}
                <div className={cn(
                  "absolute left-4 top-6 flex h-10 w-10 items-center justify-center rounded-full border-4 border-background",
                  milestone.status === 'completed' && "bg-success text-white",
                  milestone.status === 'current' && "bg-primary text-white",
                  milestone.status === 'locked' && "bg-muted text-muted-foreground"
                )}>
                  <Icon className="h-4 w-4" />
                </div>

                {/* Milestone Card */}
                <Card className={cn(
                  "transition-all",
                  milestone.status === 'current' && "border-primary/50 shadow-lg shadow-primary/10",
                  milestone.status === 'locked' && "opacity-60"
                )}>
                  <CardHeader className="pb-3">
                    <div className="flex items-center justify-between">
                      <div className="flex items-center gap-3">
                        <span className="text-2xl font-bold">Band {milestone.band}</span>
                        <Badge variant={milestone.status === 'current' ? 'default' : 'secondary'}>
                          {milestone.status}
                        </Badge>
                      </div>
                      <Button
                        variant="ghost"
                        size="sm"
                        onClick={() => setExpandedMilestone(isExpanded ? null : String(milestone.id))}
                      >
                        <ChevronDown className={cn("h-4 w-4 transition-transform", isExpanded && "rotate-180")} />
                      </Button>
                    </div>
                    <CardTitle className="text-base">{milestone.title}</CardTitle>
                    <p className="text-sm text-muted-foreground">{milestone.description}</p>
                  </CardHeader>

                  {/* Expanded content */}
                  {isExpanded && (
                    <motion.div
                      initial={{ height: 0, opacity: 0 }}
                      animate={{ height: 'auto', opacity: 1 }}
                      className="px-6 pb-6"
                    >
                      <div className="grid grid-cols-2 md:grid-cols-3 gap-4">
                        {Object.entries(milestone.skills).map(([skill, value]) => {
                          const SkillIcon = skillIcons[skill as keyof typeof skillIcons]
                          const colorClass = skillColors[skill as keyof typeof skillColors]
                          return (
                            <div
                              key={skill}
                              className="p-3 rounded-xl bg-muted/50"
                            >
                              <div className="flex items-center gap-2 mb-2">
                                <div className={cn("h-6 w-6 rounded-lg flex items-center justify-center", colorClass)}>
                                  <SkillIcon className="h-3 w-3 text-white" />
                                </div>
                                <span className="text-sm font-medium capitalize">{skill}</span>
                              </div>
                              <Progress value={value} className="h-2" />
                              <p className="text-xs text-muted-foreground mt-1">{value}% mastery</p>
                            </div>
                          )
                        })}
                      </div>
                      {milestone.status !== 'completed' && (
                        <Button className="w-full mt-4" onClick={() => setSkillPickerOpen(true)}>
                          Start This Level
                        </Button>
                      )}
                    </motion.div>
                  )}
                </Card>
              </motion.div>
            )
          })}
        </motion.div>
      </div>

      <SkillPickerDialog open={skillPickerOpen} onOpenChange={setSkillPickerOpen} />
    </div>
  )
}