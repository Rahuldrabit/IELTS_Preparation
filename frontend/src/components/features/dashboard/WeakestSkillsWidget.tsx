'use client'

import { motion } from 'framer-motion'
import { TrendingDown, ArrowRight } from 'lucide-react'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Progress } from '@/components/ui/progress'
import { useBandScores } from '@/lib/hooks/useProfile'
import { fadeInUp, staggerItem } from '@/lib/animations'

const skills = [
  { name: 'Speaking', value: 60, color: 'bg-purple-500' },
  { name: 'Vocabulary', value: 65, color: 'bg-pink-500' },
  { name: 'Writing', value: 65, color: 'bg-orange-500' },
  { name: 'Listening', value: 70, color: 'bg-green-500' },
  { name: 'Grammar', value: 70, color: 'bg-blue-500' },
  { name: 'Reading', value: 75, color: 'bg-indigo-500' },
].sort((a, b) => a.value - b.value)

export function WeakestSkillsWidget() {
  const { data: bandScores, isLoading } = useBandScores()

  // Use mock data if API not available, otherwise use real band scores
  const skillValues = skills.map(skill => {
    if (isLoading || !bandScores) return { ...skill }
    
    // Map skill names to band scores
    const score = (bandScores as any)[skill.name.toLowerCase()]
    return { ...skill, value: score ? Math.round(score) : skill.value }
  })

  return (
    <motion.div variants={fadeInUp} initial="initial" animate="animate">
      <Card className="h-full">
        <CardHeader className="pb-3">
          <CardTitle className="text-base flex items-center gap-2">
            <TrendingDown className="h-4 w-4 text-destructive" />
            Skills to Focus On
          </CardTitle>
        </CardHeader>
        <CardContent>
          <div className="space-y-4">
            {skillValues.slice(0, 4).map((skill, index) => (
              <motion.div
                key={skill.name}
                variants={staggerItem}
                className="space-y-2"
              >
                <div className="flex justify-between items-center">
                  <span className="text-sm font-medium">{skill.name}</span>
                  <span className="text-xs text-muted-foreground">{skill.value}%</span>
                </div>
                <Progress value={skill.value} className="h-2" />
              </motion.div>
            ))}
          </div>
          <Button variant="outline" className="w-full mt-4" size="sm">
            View All Skills
            <ArrowRight className="h-4 w-4 ml-2" />
          </Button>
        </CardContent>
      </Card>
    </motion.div>
  )
}