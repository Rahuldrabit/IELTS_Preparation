'use client'

import { useState, useEffect } from 'react'
import { useRouter } from 'next/navigation'
import { motion } from 'framer-motion'
import { Trophy, ArrowRight, Loader2 } from 'lucide-react'
import { Card, CardContent } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Badge } from '@/components/ui/badge'
import { mocktestApi, type BaselineStatus } from '@/lib/services/mocktest'

export function MockTestBanner() {
  const router = useRouter()
  const [status, setStatus] = useState<BaselineStatus | null>(null)
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    mocktestApi.getBaselineStatus()
      .then(setStatus)
      .catch(() => {})
      .finally(() => setLoading(false))
  }, [])

  if (loading || !status) return null

  // If baseline is done, show latest score widget
  if (status.has_completed_baseline) {
    return (
      <motion.div initial={{ opacity: 0, y: 10 }} animate={{ opacity: 1, y: 0 }}>
        <Card
          className="cursor-pointer hover:shadow-md transition-all"
          onClick={() => router.push('/practice/mock-test')}
        >
          <CardContent className="p-4">
            <div className="flex items-center gap-3">
              <div className="h-10 w-10 rounded-lg bg-primary/10 flex items-center justify-center">
                <Trophy className="h-5 w-5 text-primary" />
              </div>
              <div className="flex-1">
                <p className="text-sm font-medium">Mock Test Score</p>
                <p className="text-xs text-muted-foreground">Your baseline assessment</p>
              </div>
              {status.baseline_band && (
                <Badge className="text-lg px-3 py-1 font-bold">
                  {status.baseline_band}
                </Badge>
              )}
            </div>
          </CardContent>
        </Card>
      </motion.div>
    )
  }

  // No baseline — show prominent CTA
  return (
    <motion.div initial={{ opacity: 0, y: 10 }} animate={{ opacity: 1, y: 0 }}>
      <Card className="border-primary/30 bg-gradient-to-r from-primary/5 to-primary/10">
        <CardContent className="p-6">
          <div className="flex flex-col sm:flex-row sm:items-center gap-6">
            <div className="h-14 w-14 rounded-2xl bg-primary/10 flex items-center justify-center shrink-0 shadow-inner">
              <span className="text-2xl">🎁</span>
            </div>
            <div className="flex-1 space-y-1">
              <h3 className="text-lg font-bold text-primary">Take Your FREE Diagnostic Mock Test</h3>
              <p className="text-sm text-muted-foreground">
                Understand your current IELTS level with a full timed assessment to personalize your AI tutor's plan.
              </p>
            </div>
            <Button
              size="lg"
              onClick={() => router.push('/practice/mock-test')}
              className="shrink-0 font-bold shadow-lg shadow-primary/20 hover:scale-105 transition-transform"
            >
              Start Free Test
              <ArrowRight className="h-3 w-3 ml-1" />
            </Button>
          </div>
        </CardContent>
      </Card>
    </motion.div>
  )
}
