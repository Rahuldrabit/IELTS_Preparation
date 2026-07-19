'use client'

import { motion } from 'framer-motion'
import { Calendar, Flame, Target, Clock, TrendingUp } from 'lucide-react'
import { StudyPlanCard } from '@/components/features/journey/StudyPlanCard'
import { BandTrajectoryCard } from '@/components/features/insights/BandTrajectoryCard'

export default function StudyPlanPage() {
  return (
    <div className="space-y-6">
      {/* Header */}
      <motion.div
        initial={{ opacity: 0, y: -20 }}
        animate={{ opacity: 1, y: 0 }}
      >
        <h1 className="text-3xl font-bold mb-2">Your Study Plan</h1>
        <p className="text-muted-foreground">
          A personalized weekly schedule based on your progress and goals
        </p>
      </motion.div>
      
      {/* Main Content */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Study Plan - Takes 2 columns */}
        <motion.div
          initial={{ opacity: 0, x: -20 }}
          animate={{ opacity: 1, x: 0 }}
          transition={{ delay: 0.1 }}
          className="lg:col-span-2"
        >
          <StudyPlanCard />
        </motion.div>
        
        {/* Sidebar */}
        <div className="space-y-6">
          {/* Band Trajectory */}
          <motion.div
            initial={{ opacity: 0, x: 20 }}
            animate={{ opacity: 1, x: 0 }}
            transition={{ delay: 0.2 }}
          >
            <BandTrajectoryCard />
          </motion.div>
          
          {/* Tips Card */}
          <motion.div
            initial={{ opacity: 0, x: 20 }}
            animate={{ opacity: 1, x: 0 }}
            transition={{ delay: 0.3 }}
            className="p-6 rounded-lg bg-muted"
          >
            <h3 className="font-medium mb-3">Study Tips</h3>
            <ul className="space-y-2 text-sm text-muted-foreground">
              <li className="flex items-start gap-2">
                <Clock className="h-4 w-4 mt-0.5 flex-shrink-0" />
                <span>Practice at the same time each day to build a habit</span>
              </li>
              <li className="flex items-start gap-2">
                <Target className="h-4 w-4 mt-0.5 flex-shrink-0" />
                <span>Focus on weak areas before the exam</span>
              </li>
              <li className="flex items-start gap-2">
                <TrendingUp className="h-4 w-4 mt-0.5 flex-shrink-0" />
                <span>Review mistakes regularly to avoid repeating them</span>
              </li>
              <li className="flex items-start gap-2">
                <Flame className="h-4 w-4 mt-0.5 flex-shrink-0" />
                <span>Maintain your streak for consistent progress</span>
              </li>
            </ul>
          </motion.div>
        </div>
      </div>
    </div>
  )
}
