'use client'

import { useEffect, useCallback, useState } from 'react'
import { useParams, useRouter } from 'next/navigation'
import { motion, AnimatePresence } from 'framer-motion'
import { Loader2, AlertCircle } from 'lucide-react'
import { Button } from '@/components/ui/button'
import { useMockTestStore } from '@/lib/store/mockTestStore'
import { mocktestApi } from '@/lib/services/mocktest'
import { GlobalTimer } from '@/components/features/mock-test/GlobalTimer'
import { MockTestListeningSection } from '@/components/features/mock-test/ListeningSection'
import { MockTestReadingSection } from '@/components/features/mock-test/ReadingSection'
import { MockTestWritingSection } from '@/components/features/mock-test/WritingSection'
import { MockTestSpeakingSection } from '@/components/features/mock-test/SpeakingSection'
import { DiagnosticReportView } from '@/components/features/mock-test/DiagnosticReport'

const SECTION_LABELS: Record<string, string> = {
  listening: 'Listening',
  reading: 'Reading',
  writing: 'Writing',
  speaking: 'Speaking',
}

export default function MockTestActivePage() {
  const params = useParams()
  const router = useRouter()
  const mockTestId = Number(params.id)

  const {
    phase,
    mockTestId: storeTestId,
    currentContent,
    timer,
    isLoading,
    error,
    listeningAnswers,
    readingAnswers,
    writingAnswers,
    speakingAnswers,
    diagnosticReport,
    setTestData,
    setPhase,
    setCurrentContent,
    setLoading,
    setError,
    advanceToNextSection,
    setDiagnosticReport,
    setSectionBand,
  } = useMockTestStore()

  const [sectionStartTime, setSectionStartTime] = useState<number>(Date.now())

  // Load test data if not already in store
  useEffect(() => {
    if (storeTestId !== mockTestId) {
      loadTestData()
    } else if (phase === 'lobby' && !currentContent) {
      // Store has data but we haven't started a section yet
      loadTestData()
    }
  }, [mockTestId, storeTestId, phase, currentContent])

  const loadTestData = async () => {
    setLoading(true)
    try {
      const detail = await mocktestApi.getDetail(mockTestId)
      setTestData({
        id: detail.id,
        test_type: detail.test_type,
        status: detail.status as 'in_progress' | 'completed' | 'abandoned',
        overall_band: detail.overall_band,
        listening_band: detail.listening_band,
        reading_band: detail.reading_band,
        writing_band: detail.writing_band,
        speaking_band: detail.speaking_band,
        started_at: detail.started_at,
        finished_at: detail.finished_at,
        total_time_seconds: detail.total_time_seconds,
        sections: detail.sections.map((s) => ({
          id: s.id,
          section_type: s.section_type as 'listening' | 'reading' | 'writing' | 'speaking',
          section_order: s.section_order,
          status: s.status as 'pending' | 'in_progress' | 'completed' | 'skipped',
          time_allocated_seconds: s.time_allocated_seconds,
          time_spent_seconds: s.time_spent_seconds,
          started_at: s.started_at,
          finished_at: s.finished_at,
          band_estimate: s.band_estimate,
          difficulty_config: s.difficulty_config as any,
        })),
      })

      // If test is completed, show report
      if (detail.status === 'completed' && detail.diagnostic_report) {
        setDiagnosticReport(detail.diagnostic_report)
        return
      }

      // Find next pending section and start it
      const nextSection = detail.sections.find((s) => s.status === 'pending' || s.status === 'in_progress')
      if (nextSection) {
        const sectionIndex = detail.sections.findIndex((s) => s.section_type === nextSection.section_type)
        useMockTestStore.getState().setCurrentSectionIndex(sectionIndex >= 0 ? sectionIndex : 0)
        await startSectionFlow(nextSection.section_type)
      } else {
        // All done, trigger evaluation
        setPhase('evaluating')
        await triggerEvaluation()
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to load mock test')
    } finally {
      setLoading(false)
    }
  }

  const startSectionFlow = async (sectionType: string) => {
    setLoading(true)
    try {
      const response = await mocktestApi.startSection(mockTestId, sectionType)
      setCurrentContent(response.content_data)
      setPhase(sectionType as any)
      setSectionStartTime(Date.now())
    } catch (err) {
      setError(err instanceof Error ? err.message : `Failed to start ${sectionType} section`)
    } finally {
      setLoading(false)
    }
  }

  const handleSectionSubmit = useCallback(async () => {
    const currentPhase = useMockTestStore.getState().phase
    const timeSpent = Math.floor((Date.now() - sectionStartTime) / 1000)

    // Determine which answers to submit
    let answers: Record<string, string> = {}
    if (currentPhase === 'listening') {
      answers = useMockTestStore.getState().listeningAnswers
    } else if (currentPhase === 'reading') {
      answers = useMockTestStore.getState().readingAnswers
    } else if (currentPhase === 'writing') {
      answers = useMockTestStore.getState().writingAnswers
    } else if (currentPhase === 'speaking') {
      // Flatten speaking answers
      const speakingData = useMockTestStore.getState().speakingAnswers
      answers = Object.entries(speakingData).reduce((acc, [partKey, partAnswers]) => {
        Object.entries(partAnswers).forEach(([qKey, val]) => {
          acc[`${partKey}_${qKey}`] = val
        })
        return acc
      }, {} as Record<string, string>)
    }

    try {
      const result = await mocktestApi.submitSection(
        mockTestId,
        currentPhase,
        answers,
        timeSpent
      )

      if (result.band_estimate) {
        setSectionBand(currentPhase as any, result.band_estimate)
      }

      if (result.all_sections_complete) {
        // All done → evaluate
        setPhase('evaluating')
        await triggerEvaluation()
      } else {
        // Move to next section
        advanceToNextSection()
        const nextPhase = useMockTestStore.getState().phase
        if (nextPhase !== 'evaluating' && nextPhase !== 'report') {
          await startSectionFlow(nextPhase)
        }
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to submit section')
    }
  }, [mockTestId, sectionStartTime, advanceToNextSection, setSectionBand, setPhase])

  const triggerEvaluation = async () => {
    try {
      const result = await mocktestApi.evaluate(mockTestId)
      setDiagnosticReport(result.diagnostic_report)
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Evaluation failed')
      setPhase('report')
    }
  }

  const handleTimerExpired = useCallback(() => {
    handleSectionSubmit()
  }, [handleSectionSubmit])

  // Get time for current section
  const getCurrentSectionTime = (): number => {
    const state = useMockTestStore.getState()
    const section = state.sections.find(
      (s) => s.section_type === state.phase
    )
    return section?.time_allocated_seconds || 3600
  }

  // ─────────────────────────────────────────────
  //  Render
  // ─────────────────────────────────────────────

  if (isLoading) {
    return (
      <div className="flex flex-col items-center justify-center min-h-[500px] gap-4">
        <Loader2 className="h-10 w-10 animate-spin text-primary" />
        <p className="text-muted-foreground">
          {phase === 'lobby' ? 'Loading test...' : `Preparing ${SECTION_LABELS[phase] || phase}...`}
        </p>
      </div>
    )
  }

  if (error) {
    return (
      <div className="max-w-2xl mx-auto mt-12">
        <div className="p-6 rounded-xl bg-destructive/10 border border-destructive/20">
          <div className="flex items-center gap-3 mb-4">
            <AlertCircle className="h-6 w-6 text-destructive" />
            <h3 className="font-semibold text-destructive">Error</h3>
          </div>
          <p className="text-sm text-muted-foreground mb-4">{error}</p>
          <Button variant="outline" onClick={() => router.push('/practice/mock-test')}>
            Back to Mock Test Lobby
          </Button>
        </div>
      </div>
    )
  }

  // Evaluating state
  if (phase === 'evaluating') {
    return (
      <div className="flex flex-col items-center justify-center min-h-[500px] gap-4">
        <Loader2 className="h-10 w-10 animate-spin text-primary" />
        <h2 className="text-xl font-semibold">Evaluating Your Performance</h2>
        <p className="text-muted-foreground text-center max-w-md">
          AI is analyzing your responses across all sections to generate
          a comprehensive diagnostic report...
        </p>
      </div>
    )
  }

  // Report phase
  if (phase === 'report') {
    return <DiagnosticReportView report={diagnosticReport} mockTestId={mockTestId} />
  }

  // Active section phases
  const isActiveSection = ['listening', 'reading', 'writing', 'speaking'].includes(phase)

  return (
    <div className="space-y-4">
      {/* Global Timer — always visible during active sections */}
      {isActiveSection && currentContent && (
        <GlobalTimer
          totalSeconds={getCurrentSectionTime()}
          sectionLabel={SECTION_LABELS[phase]}
          onExpired={handleTimerExpired}
        />
      )}

      {/* Section Content */}
      <AnimatePresence mode="wait">
        {phase === 'listening' && currentContent && (
          <motion.div
            key="listening"
            initial={{ opacity: 0, x: 50 }}
            animate={{ opacity: 1, x: 0 }}
            exit={{ opacity: 0, x: -50 }}
          >
            <MockTestListeningSection
              content={currentContent}
              onSubmit={handleSectionSubmit}
            />
          </motion.div>
        )}

        {phase === 'reading' && currentContent && (
          <motion.div
            key="reading"
            initial={{ opacity: 0, x: 50 }}
            animate={{ opacity: 1, x: 0 }}
            exit={{ opacity: 0, x: -50 }}
          >
            <MockTestReadingSection
              content={currentContent}
              onSubmit={handleSectionSubmit}
            />
          </motion.div>
        )}

        {phase === 'writing' && currentContent && (
          <motion.div
            key="writing"
            initial={{ opacity: 0, x: 50 }}
            animate={{ opacity: 1, x: 0 }}
            exit={{ opacity: 0, x: -50 }}
          >
            <MockTestWritingSection
              content={currentContent}
              onSubmit={handleSectionSubmit}
            />
          </motion.div>
        )}

        {phase === 'speaking' && currentContent && (
          <motion.div
            key="speaking"
            initial={{ opacity: 0, x: 50 }}
            animate={{ opacity: 1, x: 0 }}
            exit={{ opacity: 0, x: -50 }}
          >
            <MockTestSpeakingSection
              content={currentContent}
              onSubmit={handleSectionSubmit}
            />
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  )
}
