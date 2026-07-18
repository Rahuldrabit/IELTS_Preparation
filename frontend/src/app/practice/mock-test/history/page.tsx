'use client'

import { useState, useEffect } from 'react'
import { useRouter } from 'next/navigation'
import { motion } from 'framer-motion'
import {
  History, Trophy, Clock, TrendingUp, ArrowLeft,
  Loader2, AlertCircle,
} from 'lucide-react'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Badge } from '@/components/ui/badge'
import { cn } from '@/lib/utils'
import { mocktestApi, type MockTestHistoryItem } from '@/lib/services/mocktest'

export default function MockTestHistoryPage() {
  const router = useRouter()
  const [history, setHistory] = useState<MockTestHistoryItem[]>([])
  const [isLoading, setIsLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    loadHistory()
  }, [])

  const loadHistory = async () => {
    try {
      const data = await mocktestApi.getHistory(50)
      setHistory(data)
    } catch (err) {
      setError('Failed to load history')
    } finally {
      setIsLoading(false)
    }
  }

  const completedTests = history.filter((t) => t.status === 'completed')
  const bandScores = completedTests
    .filter((t) => t.overall_band)
    .map((t) => ({ date: t.started_at, band: t.overall_band! }))

  if (isLoading) {
    return (
      <div className="flex items-center justify-center min-h-[400px]">
        <Loader2 className="h-8 w-8 animate-spin text-muted-foreground" />
      </div>
    )
  }

  return (
    <div className="space-y-6 max-w-4xl mx-auto">
      {/* Header */}
      <div className="flex items-center gap-3">
        <Button variant="ghost" size="icon" onClick={() => router.push('/practice/mock-test')}>
          <ArrowLeft className="h-5 w-5" />
        </Button>
        <div>
          <h1 className="text-2xl font-bold">Mock Test History</h1>
          <p className="text-sm text-muted-foreground">
            {completedTests.length} completed test{completedTests.length !== 1 ? 's' : ''}
          </p>
        </div>
      </div>

      {/* Progress Chart (simple visual) */}
      {bandScores.length >= 2 && (
        <Card>
          <CardHeader>
            <CardTitle className="text-base flex items-center gap-2">
              <TrendingUp className="h-4 w-4" /> Band Score Progress
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="flex items-end gap-2 h-32">
              {bandScores.map((score, idx) => {
                const height = ((score.band - 3) / 6) * 100 // Scale 3-9 to 0-100%
                return (
                  <div key={idx} className="flex-1 flex flex-col items-center gap-1">
                    <span className="text-xs font-mono">{score.band}</span>
                    <div
                      className={cn(
                        'w-full rounded-t-md transition-all',
                        idx === bandScores.length - 1
                          ? 'bg-primary'
                          : 'bg-primary/40'
                      )}
                      style={{ height: `${Math.max(height, 10)}%` }}
                    />
                    <span className="text-[10px] text-muted-foreground">
                      {new Date(score.date).toLocaleDateString(undefined, { month: 'short', day: 'numeric' })}
                    </span>
                  </div>
                )
              })}
            </div>
          </CardContent>
        </Card>
      )}

      {/* Test List */}
      {history.length === 0 ? (
        <Card>
          <CardContent className="p-12 text-center">
            <History className="h-12 w-12 text-muted-foreground mx-auto mb-4" />
            <p className="text-muted-foreground mb-4">No mock tests taken yet</p>
            <Button onClick={() => router.push('/practice/mock-test')}>
              Take Your First Test
            </Button>
          </CardContent>
        </Card>
      ) : (
        <div className="space-y-3">
          {history.map((test, idx) => (
            <motion.div
              key={test.id}
              initial={{ opacity: 0, y: 10 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ delay: idx * 0.05 }}
            >
              <Card
                className="hover:shadow-md transition-all cursor-pointer"
                onClick={() => router.push(`/practice/mock-test/${test.id}`)}
              >
                <CardContent className="p-4">
                  <div className="flex items-center justify-between">
                    <div className="flex items-center gap-4">
                      <div className={cn(
                        'h-10 w-10 rounded-full flex items-center justify-center',
                        test.status === 'completed'
                          ? 'bg-green-500/10'
                          : test.status === 'in_progress'
                            ? 'bg-yellow-500/10'
                            : 'bg-muted'
                      )}>
                        {test.status === 'completed' ? (
                          <Trophy className="h-5 w-5 text-green-500" />
                        ) : (
                          <Clock className="h-5 w-5 text-yellow-500" />
                        )}
                      </div>
                      <div>
                        <p className="font-medium">
                          {test.test_type === 'baseline' ? 'Baseline Diagnostic' : 'Practice Mock Test'}
                        </p>
                        <p className="text-sm text-muted-foreground">
                          {new Date(test.started_at).toLocaleDateString(undefined, {
                            weekday: 'short', year: 'numeric', month: 'short', day: 'numeric'
                          })}
                          {test.total_time_seconds && (
                            <> &middot; {Math.round(test.total_time_seconds / 60)} min</>
                          )}
                        </p>
                      </div>
                    </div>

                    <div className="flex items-center gap-3">
                      {test.status === 'completed' && (
                        <div className="flex gap-2 text-xs">
                          {test.listening_band && <Badge variant="outline">L:{test.listening_band}</Badge>}
                          {test.reading_band && <Badge variant="outline">R:{test.reading_band}</Badge>}
                          {test.writing_band && <Badge variant="outline">W:{test.writing_band}</Badge>}
                          {test.speaking_band && <Badge variant="outline">S:{test.speaking_band}</Badge>}
                        </div>
                      )}
                      {test.overall_band && (
                        <Badge className="text-base px-3 py-1 font-bold">
                          {test.overall_band}
                        </Badge>
                      )}
                      <Badge variant={
                        test.status === 'completed' ? 'default' :
                        test.status === 'in_progress' ? 'secondary' : 'destructive'
                      }>
                        {test.status}
                      </Badge>
                    </div>
                  </div>
                </CardContent>
              </Card>
            </motion.div>
          ))}
        </div>
      )}

      {error && (
        <div className="p-4 rounded-xl bg-destructive/10 border border-destructive/20 flex items-center gap-3">
          <AlertCircle className="h-5 w-5 text-destructive" />
          <p className="text-sm text-destructive">{error}</p>
        </div>
      )}
    </div>
  )
}
