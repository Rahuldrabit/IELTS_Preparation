'use client'

import { motion } from 'framer-motion'
import { CheckCircle2, Circle, ArrowRight } from 'lucide-react'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { useRoadmap, useCompleteTask } from '@/lib/hooks/useProfile'
import { fadeInUp, staggerItem } from '@/lib/animations'

export function DailyRoadmapWidget() {
  const { data: roadmap, isLoading } = useRoadmap()
  const completeTask = useCompleteTask()

  const handleComplete = async (taskId: number) => {
    await completeTask.mutateAsync(taskId)
  }

  if (isLoading) {
    return (
      <Card className="h-full">
        <CardHeader className="pb-3">
          <CardTitle className="text-base">Today's Roadmap</CardTitle>
        </CardHeader>
        <CardContent>
          <p className="text-muted-foreground">Loading...</p>
        </CardContent>
      </Card>
    )
  }

  if (!roadmap) return null

  return (
    <motion.div variants={fadeInUp} initial="initial" animate="animate">
      <Card className="h-full">
        <CardHeader className="pb-3">
          <CardTitle className="text-base flex items-center gap-2">
            Today's Roadmap
            <span className="text-xs font-normal text-muted-foreground ml-auto">
              {roadmap.tasks.filter(t => t.completed).length}/{roadmap.tasks.length} completed
            </span>
          </CardTitle>
        </CardHeader>
        <CardContent>
          <motion.ul 
            variants={staggerItem}
            initial="initial"
            animate="animate"
            className="space-y-3"
          >
            {roadmap.tasks.map((task, index) => (
              <motion.li
                key={task.id}
                variants={staggerItem}
                className="flex items-center gap-3"
              >
                {task.completed ? (
                  <CheckCircle2 className="h-5 w-5 text-success shrink-0" />
                ) : (
                  <Circle className="h-5 w-5 text-muted-foreground/40 shrink-0" />
                )}
                <span className={`text-sm ${task.completed ? 'text-muted-foreground line-through' : ''}`}>
                  {task.title}
                </span>
                <span className={`ml-auto text-xs px-2 py-0.5 rounded-full capitalize ${
                  task.skill === 'reading' ? 'bg-blue-100 text-blue-700' :
                  task.skill === 'listening' ? 'bg-green-100 text-green-700' :
                  task.skill === 'speaking' ? 'bg-purple-100 text-purple-700' :
                  task.skill === 'writing' ? 'bg-orange-100 text-orange-700' :
                  task.skill === 'vocabulary' ? 'bg-pink-100 text-pink-700' :
                  'bg-gray-100 text-gray-700'
                }`}>
                  {task.skill}
                </span>
              </motion.li>
            ))}
          </motion.ul>
        </CardContent>
      </Card>
    </motion.div>
  )
}