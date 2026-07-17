'use client'

import { motion } from 'framer-motion'
import { TrendingUp, ArrowRight } from 'lucide-react'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { mockProgress } from '@/lib/mock-data/user'
import { fadeInUp } from '@/lib/animations'

export function WeeklyProgressWidget() {
  const maxBand = Math.max(...mockProgress.map(p => p.band))
  const minBand = Math.min(...mockProgress.map(p => p.band))
  const range = maxBand - minBand

  return (
    <motion.div variants={fadeInUp} initial="initial" animate="animate">
      <Card className="h-full">
        <CardHeader className="pb-3">
          <CardTitle className="text-base flex items-center gap-2">
            <TrendingUp className="h-4 w-4 text-success" />
            Weekly Progress
          </CardTitle>
        </CardHeader>
        <CardContent>
          <div className="flex items-end gap-2 h-32">
            {mockProgress.map((week, index) => {
              const height = ((week.band - minBand) / (range || 1)) * 100
              return (
                <motion.div
                  key={week.week}
                  initial={{ height: 0 }}
                  animate={{ height: `${Math.max(height, 10)}%` }}
                  transition={{ delay: index * 0.1, duration: 0.5 }}
                  className="flex-1 flex flex-col items-center gap-2"
                >
                  <div className="w-full bg-primary/80 rounded-t-lg relative group">
                    <div className="absolute bottom-full mb-2 left-1/2 -translate-x-1/2 bg-primary text-white text-xs px-2 py-1 rounded opacity-0 group-hover:opacity-100 transition-opacity whitespace-nowrap">
                      {week.band}
                    </div>
                  </div>
                  <span className="text-[10px] text-muted-foreground -rotate-45 origin-center">
                    {week.week.replace('Week ', 'W')}
                  </span>
                </motion.div>
              )
            })}
          </div>
          <Button variant="outline" className="w-full mt-4" size="sm">
            View Details
            <ArrowRight className="h-4 w-4 ml-2" />
          </Button>
        </CardContent>
      </Card>
    </motion.div>
  )
}