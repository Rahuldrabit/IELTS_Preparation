'use client'

import { motion } from 'framer-motion'
import { HeroCard } from '@/components/features/dashboard/HeroCard'
import { DailyRoadmapWidget } from '@/components/features/dashboard/DailyRoadmapWidget'
import { WeakestSkillsWidget } from '@/components/features/dashboard/WeakestSkillsWidget'
import { VocabularyReviewWidget } from '@/components/features/dashboard/VocabularyReviewWidget'
import { RecentMistakesWidget } from '@/components/features/dashboard/RecentMistakesWidget'
import { WeeklyProgressWidget } from '@/components/features/dashboard/WeeklyProgressWidget'
import { AIRecommendationsWidget } from '@/components/features/dashboard/AIRecommendationsWidget'
import { UmaInterventionCard } from '@/components/features/dashboard/UmaInterventionCard'
import { staggerContainer } from '@/lib/animations'

export default function DashboardPage() {
  return (
    <div className="space-y-6">
      {/* Hero Section */}
      <HeroCard />

      {/* Uma Intervention — full width when present */}
      <UmaInterventionCard />

      {/* Widgets Grid */}
      <motion.div
        variants={staggerContainer}
        initial="initial"
        animate="animate"
        className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6"
      >
        <DailyRoadmapWidget />
        <WeakestSkillsWidget />
        <VocabularyReviewWidget />
        <RecentMistakesWidget />
        <WeeklyProgressWidget />
        <AIRecommendationsWidget />
      </motion.div>
    </div>
  )
}