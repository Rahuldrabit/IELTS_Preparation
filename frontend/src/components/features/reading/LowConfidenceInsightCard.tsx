/**
 * LowConfidenceInsightCard
 * Displays Uma's insight for questions marked as "Low Confidence Win".
 * Shows confidence metrics alongside the AI-generated insight.
 */
'use client'

import { useMemo } from 'react'
import { motion } from 'framer-motion'
import { Brain, Clock, RotateCw, Scroll } from 'lucide-react'
import { Card } from '@/components/ui/card'
import { Badge } from '@/components/ui/badge'
import { useFeature } from '@/lib/hooks/useFeature'
import { useReadingStore } from '@/lib/store/readingStore'
import type { QuestionExplanation } from '@/lib/services/reading'

// ─────────────────────────────────────────────
//  Props
// ─────────────────────────────────────────────

interface LowConfidenceInsightCardProps {
  result: QuestionExplanation
  className?: string
}

// ─────────────────────────────────────────────
//  Component
// ─────────────────────────────────────────────

export function LowConfidenceInsightCard({ result, className }: LowConfidenceInsightCardProps) {
  const confidenceFlagsEnabled = useFeature('reading', 'confidenceFlags')
  const telemetryMap = useReadingStore((s) => s.telemetryMap)
  
  const telemetryData = useMemo(() => {
    return telemetryMap?.[String(result.question_id)]
  }, [telemetryMap, result.question_id])

  if (!confidenceFlagsEnabled || !telemetryData || !result.low_confidence_insight) {
    return null
  }

  // Convert milliseconds to minutes:seconds
  const formatTime = (ms: number) => {
    const minutes = Math.floor(ms / 60000)
    const seconds = Math.floor((ms % 60000) / 1000)
    return `${minutes}m ${seconds}s`
  }

  return (
    <motion.div
      initial={{ opacity: 0, y: 8 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.3 }}
    >
      <Card className="bg-amber-50/50 dark:bg-amber-950/20 border-amber-200 dark:border-amber-800 p-5 rounded-xl">
        {/* Header */}
        <div className="flex items-center gap-2 mb-3">
          <div className="h-8 w-8 rounded-lg bg-amber-100 dark:bg-amber-900 flex items-center justify-center">
            <Brain className="h-4 w-4 text-amber-600 dark:text-amber-400" />
          </div>
          <div>
            <p className="font-semibold text-amber-700 dark:text-amber-400 text-sm">
              Uma's Insight — Low Confidence Win
            </p>
          </div>
        </div>

        {/* Insight text */}
        <p className="text-sm leading-relaxed text-amber-800 dark:text-amber-300 mb-4">
          {result.low_confidence_insight}
        </p>

        {/* Stats row */}
        <div className="flex flex-wrap gap-2">
          <Badge variant="outline" className="text-amber-600 dark:text-amber-400 border-amber-300 dark:border-amber-700">
            <Clock className="h-3 w-3 mr-1" />
            {formatTime(telemetryData.time_to_answer_ms)}
          </Badge>
          
          {telemetryData.correction_count > 0 && (
            <Badge variant="outline" className="text-amber-600 dark:text-amber-400 border-amber-300 dark:border-amber-700">
              <RotateCw className="h-3 w-3 mr-1" />
              {telemetryData.correction_count} correction{telemetryData.correction_count > 1 ? 's' : ''}
            </Badge>
          )}

          {telemetryData.passage_friction_count > 0 && (
            <Badge variant="outline" className="text-amber-600 dark:text-amber-400 border-amber-300 dark:border-amber-700">
              <Scroll className="h-3 w-3 mr-1" />
              {telemetryData.passage_friction_count} scroll{telemetryData.passage_friction_count > 1 ? 'backs' : ''}
            </Badge>
          )}
        </div>
      </Card>
    </motion.div>
  )
}
