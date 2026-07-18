'use client'

import { useState, useEffect, useCallback } from 'react'
import { useRouter } from 'next/navigation'
import { motion } from 'framer-motion'
import {
  Play, Clock, Trophy, History, Loader2, AlertCircle,
  Headphones, BookOpen, PenTool, Mic,
} from 'lucide-react'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Badge } from '@/components/ui/badge'
import { cn } from '@/lib/utils'
import { mocktestApi, type MockTestHistoryItem, type ImportedTestSummary } from '@/lib/services/mocktest'
import { useMockTestStore } from '@/lib/store/mockTestStore'

const SECTIONS_INFO = [
  { type: 'listening', icon: Headphones, label: 'Listening', time: '30 min', color: 'text-green-500', bg: 'bg-green-500/10' },
  { type: 'reading', icon: BookOpen, label: 'Reading', time: '60 min', color: 'text-blue-500', bg: 'bg-blue-500/10' },
  { type: 'writing', icon: PenTool, label: 'Writing', time: '60 min', color: 'text-orange-500', bg: 'bg-orange-500/10' },
  { type: 'speaking', icon: Mic, label: 'Speaking', time: '15 min', color: 'text-purple-500', bg: 'bg-purple-500/10' },
]

export default function MockTestLobbyPage() {
  const router = useRouter()
  const { setTestData, reset } = useMockTestStore()
  const [history, setHistory] = useState<MockTestHistoryItem[]>([])
  const [importedTests, setImportedTests] = useState<ImportedTestSummary[]>([])
  const [isLoading, setIsLoading] = useState(true)
  const [startingId, setStartingId] = useState<string | null>(null) // tracks which button is loading
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    loadData()
  }, [])

  const loadData = async () => {
    try {
      const [historyData, imported] = await Promise.all([
        mocktestApi.getHistory(5),
        mocktestApi.getImportedTests(),
      ])
      setHistory(historyData)
      setImportedTests(imported)
    } catch (err) {
      setError('Failed to load mock test data. Is the backend running?')
    } finally {
      setIsLoading(false)
    }
  }

  // Check if user has completed all pre-built tests
  const completedTestTypes = history
    .filter((t) => t.status === 'completed' && t.test_type === 'imported')
    .length

  const allPreBuiltDone = completedTestTypes >= importedTests.length && importedTests.length > 0

  const startTest = useCallback(async (testId: string, mode: 'imported' | 'generated') => {
    setStartingId(testId)
    setError(null)
    reset()
    try {
      let testData
      if (mode === 'imported') {
        testData = await mocktestApi.startImportedTest(testId)
      } else {
        testData = await mocktestApi.startTest('generated')
      }
      setTestData(testData)
      router.push(`/practice/mock-test/${testData.id}`)
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to start mock test')
      setStartingId(null)
    }
  }, [reset, setTestData, router])

  const handleStartMockTest = useCallback(async () => {
    setStartingId('main')
    setError(null)
    reset()
    try {
      let testData
      if (allPreBuiltDone) {
        // All pre-built done → generate with AI
        testData = await mocktestApi.startTest('generated')
      } else {
        // Pick a random pre-built test
        const randomIndex = Math.floor(Math.random() * importedTests.length)
        const randomTest = importedTests[randomIndex]
        testData = await mocktestApi.startImportedTest(randomTest.id)
      }
      setTestData(testData)
      router.push(`/practice/mock-test/${testData.id}`)
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to start mock test')
      setStartingId(null)
    }
  }, [reset, setTestData, router, importedTests, allPreBuiltDone])

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
      <motion.div initial={{ opacity: 0, y: -20 }} animate={{ opacity: 1, y: 0 }}>
        <h1 className="text-3xl font-bold mb-2">Full Mock Test</h1>
        <p className="text-muted-foreground">
          Simulate the complete IELTS exam experience with real timing and AI evaluation
        </p>
      </motion.div>

      {/* Start Mock Test — main button */}
      <Card className="border-primary/30 bg-primary/5">
        <CardContent className="p-6">
          <div className="flex items-center gap-4">
            <div className="h-14 w-14 rounded-xl bg-primary/10 flex items-center justify-center shrink-0">
              <Trophy className="h-7 w-7 text-primary" />
            </div>
            <div className="flex-1">
              <h3 className="text-lg font-semibold mb-1">Start a Full Mock Test</h3>
              <p className="text-sm text-muted-foreground">
                {allPreBuiltDone
                  ? 'AI-generated test with fresh content and progressive difficulty'
                  : 'Take the complete IELTS simulation with progressive difficulty'}
              </p>
            </div>
            <Button
              onClick={handleStartMockTest}
              disabled={startingId !== null}
              size="lg"
              className="shrink-0"
            >
              {startingId === 'main' ? (
                <Loader2 className="h-4 w-4 mr-2 animate-spin" />
              ) : (
                <Play className="h-4 w-4 mr-2" />
              )}
              Start Mock Test
            </Button>
          </div>
        </CardContent>
      </Card>

      {/* Test Structure Overview */}
      <Card>
        <CardHeader>
          <CardTitle className="text-lg flex items-center gap-2">
            <Clock className="h-5 w-5" />
            Test Structure — 2h 45min Total
          </CardTitle>
        </CardHeader>
        <CardContent>
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
            {SECTIONS_INFO.map((section) => (
              <div
                key={section.type}
                className="flex flex-col items-center gap-2 p-4 rounded-xl border bg-muted/30"
              >
                <div className={cn('h-10 w-10 rounded-lg flex items-center justify-center', section.bg)}>
                  <section.icon className={cn('h-5 w-5', section.color)} />
                </div>
                <span className="font-medium text-sm">{section.label}</span>
                <span className="text-xs text-muted-foreground">{section.time}</span>
              </div>
            ))}
          </div>
          <div className="mt-4 p-3 rounded-lg bg-muted/50 text-sm text-muted-foreground">
            <p>
              Each section has progressive difficulty. Timer auto-submits with a 5-minute
              warning and 30-second grace period. Sections switch automatically.
            </p>
          </div>
        </CardContent>
      </Card>

      {/* Pre-built Mock Tests */}
      {importedTests.length > 0 && (
        <Card>
          <CardHeader>
            <CardTitle className="text-lg flex items-center gap-2">
              <BookOpen className="h-5 w-5" />
              Pre-built Mock Tests
            </CardTitle>
          </CardHeader>
          <CardContent className="space-y-3">
            {importedTests.map((test) => (
              <div
                key={test.id}
                className="flex items-center justify-between p-4 rounded-lg border hover:bg-muted/50 transition-colors"
              >
                <div>
                  <p className="font-medium text-sm">{test.title}</p>
                  <p className="text-xs text-muted-foreground">{test.description}</p>
                  <div className="flex gap-2 mt-1">
                    {test.has_reading && <Badge variant="outline" className="text-xs">Reading</Badge>}
                    {test.has_writing && <Badge variant="outline" className="text-xs">Writing</Badge>}
                    {test.has_speaking && <Badge variant="outline" className="text-xs">Speaking</Badge>}
                    {test.has_listening && <Badge variant="outline" className="text-xs">Listening</Badge>}
                  </div>
                </div>
                <Button
                  variant="outline"
                  onClick={() => startTest(test.id, 'imported')}
                  disabled={startingId !== null}
                >
                  {startingId === test.id ? (
                    <Loader2 className="h-4 w-4 animate-spin" />
                  ) : (
                    <Play className="h-4 w-4 mr-1" />
                  )}
                  Start
                </Button>
              </div>
            ))}
          </CardContent>
        </Card>
      )}

      {/* Recent History */}
      {history.length > 0 && (
        <Card>
          <CardHeader>
            <div className="flex items-center justify-between">
              <CardTitle className="text-lg flex items-center gap-2">
                <History className="h-5 w-5" />
                Recent Mock Tests
              </CardTitle>
              <Button
                variant="ghost"
                size="sm"
                onClick={() => router.push('/practice/mock-test/history')}
              >
                View All
              </Button>
            </div>
          </CardHeader>
          <CardContent>
            <div className="space-y-3">
              {history.map((test) => (
                <div
                  key={test.id}
                  className="flex items-center justify-between p-3 rounded-lg border hover:bg-muted/50 cursor-pointer transition-colors"
                  onClick={() => router.push(`/practice/mock-test/${test.id}`)}
                >
                  <div className="flex items-center gap-3">
                    <div className={cn(
                      'h-8 w-8 rounded-full flex items-center justify-center',
                      test.status === 'completed' ? 'bg-green-500/10' : 'bg-yellow-500/10'
                    )}>
                      {test.status === 'completed' ? (
                        <Trophy className="h-4 w-4 text-green-500" />
                      ) : (
                        <Clock className="h-4 w-4 text-yellow-500" />
                      )}
                    </div>
                    <div>
                      <p className="text-sm font-medium">Mock Test</p>
                      <p className="text-xs text-muted-foreground">
                        {new Date(test.started_at).toLocaleDateString()}
                      </p>
                    </div>
                  </div>
                  <div className="flex items-center gap-3">
                    {test.overall_band && (
                      <Badge variant="outline" className="font-mono">
                        Band {test.overall_band}
                      </Badge>
                    )}
                    <Badge variant={test.status === 'completed' ? 'default' : 'secondary'}>
                      {test.status}
                    </Badge>
                  </div>
                </div>
              ))}
            </div>
          </CardContent>
        </Card>
      )}

      {/* Error */}
      {error && (
        <div className="p-4 rounded-xl bg-destructive/10 border border-destructive/20 flex items-center gap-3">
          <AlertCircle className="h-5 w-5 text-destructive" />
          <p className="text-sm text-destructive">{error}</p>
        </div>
      )}
    </div>
  )
}
