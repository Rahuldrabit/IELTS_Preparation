'use client'

import { motion } from 'framer-motion'
import { Sparkles, ArrowRight, BookOpen, Headphones, Mic, PenTool } from 'lucide-react'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Badge } from '@/components/ui/badge'
import { fadeInUp, staggerItem } from '@/lib/animations'

const recommendations = [
  {
    id: 1,
    title: 'Focus on Speaking Fluency',
    description: 'Your vocabulary is strong. Practice speaking for 2 minutes without pauses.',
    skill: 'speaking',
    priority: 'high',
  },
  {
    id: 2,
    title: 'Review Conditionals',
    description: 'You\'ve made 5 mistakes with conditionals this week. Let\'s practice!',
    skill: 'grammar',
    priority: 'medium',
  },
  {
    id: 3,
    title: 'Listening: Connected Speech',
    description: 'Practice identifying contractions in the next listening exercise.',
    skill: 'listening',
    priority: 'low',
  },
]

const getSkillIcon = (skill: string) => {
  switch (skill) {
    case 'speaking': return Mic
    case 'reading': return BookOpen
    case 'listening': return Headphones
    case 'writing': return PenTool
    default: return BookOpen
  }
}

const getSkillColor = (skill: string) => {
  switch (skill) {
    case 'speaking': return 'bg-purple-100 text-purple-700'
    case 'reading': return 'bg-blue-100 text-blue-700'
    case 'listening': return 'bg-green-100 text-green-700'
    case 'writing': return 'bg-orange-100 text-orange-700'
    case 'grammar': return 'bg-pink-100 text-pink-700'
    default: return 'bg-gray-100 text-gray-700'
  }
}

export function AIRecommendationsWidget() {
  return (
    <motion.div variants={fadeInUp} initial="initial" animate="animate">
      <Card className="h-full border-primary/20">
        <CardHeader className="pb-3">
          <CardTitle className="text-base flex items-center gap-2">
            <Sparkles className="h-4 w-4 text-primary" />
            AI Recommendations
          </CardTitle>
        </CardHeader>
        <CardContent>
          <motion.ul 
            variants={staggerItem}
            initial="initial"
            animate="animate"
            className="space-y-3"
          >
            {recommendations.map((rec) => {
              const Icon = getSkillIcon(rec.skill)
              return (
                <motion.li
                  key={rec.id}
                  variants={staggerItem}
                  className="p-3 rounded-xl bg-primary/5 hover:bg-primary/10 transition-colors cursor-pointer group"
                >
                  <div className="flex items-start justify-between gap-2 mb-2">
                    <Badge className={getSkillColor(rec.skill)}>
                      <Icon className="h-3 w-3 mr-1" />
                      {rec.skill}
                    </Badge>
                    {rec.priority === 'high' && (
                      <Badge variant="destructive" className="text-[10px]">Urgent</Badge>
                    )}
                  </div>
                  <p className="font-medium text-sm mb-1">{rec.title}</p>
                  <p className="text-xs text-muted-foreground">{rec.description}</p>
                  <Button 
                    variant="ghost" 
                    size="sm" 
                    className="mt-2 w-full opacity-0 group-hover:opacity-100 transition-opacity"
                  >
                    Start Practice
                    <ArrowRight className="h-4 w-4 ml-2" />
                  </Button>
                </motion.li>
              )
            })}
          </motion.ul>
        </CardContent>
      </Card>
    </motion.div>
  )
}