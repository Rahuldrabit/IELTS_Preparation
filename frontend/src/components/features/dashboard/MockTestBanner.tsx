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
        <CardContent className="p-5">
          <div className="flex items-center gap-4">
            <div className="h-12 w-12 rounded-xl bg-primary/10 flex items-center justify-center shrink-0">
              <Trophy className="h-6 w-6 text-primary" />
            </div>
            <div className="flex-1">
              <h3 className="font-semibold mb-0.5">Take Your Diagnostic Mock Test</h3>
              <p className="text-xs text-muted-foreground">
                Understand your current IELTS level with a full timed assessment
              </p>
            </div>
            <Button
              size="sm"
              onClick={() => router.push('/practice/mock-test')}
              className="shrink-0"
            >
              Start
              <ArrowRight className="h-3 w-3 ml-1" />
            </Button>
          </div>
        </CardContent>
      </Card>
    </motion.div>
  )
}
