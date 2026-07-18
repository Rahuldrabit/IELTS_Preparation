'use client'

import { motion } from 'framer-motion'
import Link from 'next/link'
import { BookOpen, Headphones, Mic, PenTool, BookMarked, FileText, ArrowRight, Clock, TrendingUp, Trophy } from 'lucide-react'
import { Card, CardContent } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Badge } from '@/components/ui/badge'
import { fadeInUp, staggerItem, staggerContainer } from '@/lib/animations'
import { cn } from '@/lib/utils'

const skills = [
  {
    id: 'reading',
    name: 'Reading',
    description: 'Improve reading comprehension with IELTS passages',
    icon: BookOpen,
    color: 'from-blue-500 to-blue-600',
    bgColor: 'bg-blue-500/10',
    textColor: 'text-blue-600',
    currentLevel: 7.0,
    recentActivity: '2 passages today',
    href: '/practice/reading',
  },
  {
    id: 'listening',
    name: 'Listening',
    description: 'Practice with various accents and audio formats',
    icon: Headphones,
    color: 'from-green-500 to-green-600',
    bgColor: 'bg-green-500/10',
    textColor: 'text-green-600',
    currentLevel: 6.5,
    recentActivity: '1 test today',
    href: '/practice/listening',
  },
  {
    id: 'speaking',
    name: 'Speaking',
    description: 'Practice speaking with AI feedback',
    icon: Mic,
    color: 'from-purple-500 to-purple-600',
    bgColor: 'bg-purple-500/10',
    textColor: 'text-purple-600',
    currentLevel: 6.0,
    recentActivity: 'Recorded 3 times',
    href: '/practice/speaking',
  },
  {
    id: 'writing',
    name: 'Writing',
    description: 'Get instant feedback on your essays',
    icon: PenTool,
    color: 'from-orange-500 to-orange-600',
    bgColor: 'bg-orange-500/10',
    textColor: 'text-orange-600',
    currentLevel: 6.5,
    recentActivity: '1 essay submitted',
    href: '/practice/writing',
  },
  {
    id: 'vocabulary',
    name: 'Vocabulary',
    description: 'Build your IELTS vocabulary with flashcards',
    icon: BookMarked,
    color: 'from-pink-500 to-pink-600',
    bgColor: 'bg-pink-500/10',
    textColor: 'text-pink-600',
    currentLevel: 65,
    recentActivity: '10 words reviewed',
    href: '/practice/vocabulary',
  },
  {
    id: 'grammar',
    name: 'Grammar',
    description: 'Master grammar with personalized exercises',
    icon: FileText,
    color: 'from-indigo-500 to-indigo-600',
    bgColor: 'bg-indigo-500/10',
    textColor: 'text-indigo-600',
    currentLevel: 70,
    recentActivity: 'Drilled conditionals',
    href: '/practice/grammar',
  },
]

export default function PracticePage() {
  return (
    <div className="space-y-6">
      {/* Header */}
      <motion.div
        initial={{ opacity: 0, y: -20 }}
        animate={{ opacity: 1, y: 0 }}
      >
        <h1 className="text-3xl font-bold mb-2">Practice Center</h1>
        <p className="text-muted-foreground">
          Choose a skill to practice and improve your IELTS score
        </p>
      </motion.div>

      {/* Mock Test CTA */}
      <motion.div initial={{ opacity: 0, y: 10 }} animate={{ opacity: 1, y: 0 }}>
        <Link href="/practice/mock-test">
          <Card className="hover:shadow-lg transition-all duration-300 group cursor-pointer overflow-hidden border-primary/20 bg-gradient-to-r from-primary/5 to-primary/10">
            <CardContent className="p-6">
              <div className="flex items-center gap-4">
                <div className="h-14 w-14 rounded-xl bg-primary/10 flex items-center justify-center shrink-0">
                  <Trophy className="h-7 w-7 text-primary" />
                </div>
                <div className="flex-1">
                  <h3 className="text-lg font-semibold mb-1">Full Mock Test</h3>
                  <p className="text-sm text-muted-foreground">
                    Simulate the complete IELTS exam with real timing and AI evaluation
                  </p>
                </div>
                <Button className="shrink-0 group-hover:shadow-md transition-shadow">
                  Take Test
                  <ArrowRight className="h-4 w-4 ml-2 group-hover:translate-x-1 transition-transform" />
                </Button>
              </div>
            </CardContent>
          </Card>
        </Link>
      </motion.div>

      {/* Skills Grid */}
      <motion.div
        variants={staggerContainer}
        initial="initial"
        animate="animate"
        className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6"
      >
        {skills.map((skill) => (
          <motion.div key={skill.id} variants={staggerItem}>
            <Link href={skill.href}>
              <Card className="h-full hover:shadow-lg transition-all duration-300 group cursor-pointer overflow-hidden">
                {/* Gradient background on hover */}
                <div className={cn("absolute inset-0 opacity-0 group-hover:opacity-10 transition-opacity bg-gradient-to-br", skill.color)} />
                
                <CardContent className="p-6 relative">
                  <div className="flex items-start justify-between mb-4">
                    <div className={cn("h-14 w-14 rounded-xl flex items-center justify-center", skill.bgColor)}>
                      <skill.icon className={cn("h-7 w-7", skill.textColor)} />
                    </div>
                    <Badge variant="outline" className="shrink-0">
                      {typeof skill.currentLevel === 'number' && skill.currentLevel < 10 
                        ? `Band ${skill.currentLevel}` 
                        : `${skill.currentLevel}%`
                      }
                    </Badge>
                  </div>

                  <h3 className="text-xl font-semibold mb-2">{skill.name}</h3>
                  <p className="text-sm text-muted-foreground mb-4">{skill.description}</p>

                  <div className="flex items-center gap-4 text-xs text-muted-foreground mb-4">
                    <div className="flex items-center gap-1">
                      <Clock className="h-3 w-3" />
                      {skill.recentActivity}
                    </div>
                    <div className="flex items-center gap-1">
                      <TrendingUp className="h-3 w-3" />
                      Improving
                    </div>
                  </div>

                  <Button className="w-full group-hover:shadow-md transition-shadow">
                    Start Practice
                    <ArrowRight className="h-4 w-4 ml-2 group-hover:translate-x-1 transition-transform" />
                  </Button>
                </CardContent>
              </Card>
            </Link>
          </motion.div>
        ))}
      </motion.div>
    </div>
  )
}