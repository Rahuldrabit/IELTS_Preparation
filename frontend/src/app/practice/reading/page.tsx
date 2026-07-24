'use client'

import { useState, useCallback, useEffect, useRef } from 'react'
import { useSearchParams, useRouter } from 'next/navigation'
import { motion, AnimatePresence } from 'framer-motion'
import { Clock, Send, Loader2, AlertCircle, Activity, Brain, Play } from 'lucide-react'
import { Button } from '@/components/ui/button'
import { useReadingStore, useIsAllAnswered } from '@/lib/store/readingStore'
import { readingApi, type GenerateReadingRequest, type QuestionTelemetryData } from '@/lib/services/reading'
import { adversarialApi, type StudentWeaknessProfile } from '@/lib/services/reading-adversarial'
import { profileApi } from '@/lib/services/profile'
import { GenerationConfigPanel } from '@/components/features/reading/GenerationConfigPanel'
import { PassagePane } from '@/components/features/reading/PassagePane'
import { QuestionsPanel } from '@/components/features/reading/QuestionSection'
import { ReviewPanel } from '@/components/features/reading/ReviewPanel'
import { VocabSelectionPopup } from '@/components/features/reading/VocabSelectionPopup'
import { useFeature } from '@/lib/hooks/useFeature'
import { useReadingTelemetry } from '@/lib/hooks/useReadingTelemetry'
import { WorkspaceFeatureChipGroup } from '@/components/ui/WorkspaceFeatureChip'
import {
  useTelemetry,
  useCalibration,
  useGazeDebug,
  GazeDebugOverlay,
  CalibrationOverlay,
  CameraPermission,
  EyeTrackingSetupModal,
  type ReadingTracker,
} from '@/modules/telemetry'

// ─────────────────────────────────────────────
//  Timer Hook
// ─────────────────────────────────────────────

function useTimer(initialSeconds: number) {
  const [seconds, setSeconds] = useState(initialSeconds)
  const [isRunning, setIsRunning] = useState(false)
  const intervalRef = useRef<NodeJS.Timeout | null>(null)

  useEffect(() => {
    if (isRunning && seconds > 0) {
      intervalRef.current = setInterval(() => {
        setSeconds((s) => (s <= 1 ? (setIsRunning(false), 0) : s - 1))
      }, 1000)
    }
    return () => { if (intervalRef.current) clearInterval(intervalRef.current) }
  }, [isRunning, seconds])

  const start = useCallback(() => setIsRunning(true), [])
  const pause = useCallback(() => setIsRunning(false), [])
  const resetTimer = useCallback(() => { setIsRunning(false); setSeconds(initialSeconds) }, [initialSeconds])

  const formatted = `${Math.floor(seconds / 60).toString().padStart(2, '0')}:${(seconds % 60).toString().padStart(2, '0')}`
  return { seconds, formatted, isRunning, start, pause, reset: resetTimer }
}

// ─────────────────────────────────────────────
//  Page Component
// ─────────────────────────────────────────────

export default function ReadingPage() {
  const router = useRouter()

  // Store state
  const {
    phase,
    setPhase,
    setPassage,
    sessionId,
    title,
    paragraphs,
    questionGroups,
    answers,
    setAnswer,
    reviewResults,
    score,
    bandEstimate,
    setReviewResults,
    error,
    setError,
    reset,
    loadFromSession,
    setTelemetryMap,
  } = useReadingStore()

  // Feature flags
  const telemetryEnabled = useFeature('reading', 'telemetry')

  // Telemetry hook — stored in a ref so it never triggers re-renders
  const telemetryRef = useRef(useReadingTelemetry())

  const isAllAnswered = useIsAllAnswered()
  const [isSubmitting, setIsSubmitting] = useState(false)
  const [highlightedParagraphId, setHighlightedParagraphId] = useState<string | null>(null)

  // Timer (20 minutes) — only starts on user click
  const timer = useTimer(20 * 60)

  // Vocabulary selection popup state
  const [vocabSelection, setVocabSelection] = useState<{
    word: string
    position: { x: number; y: number }
  } | null>(null)

  // ── Eye Tracking (CTE) ──────────────────────
  const [eyeTrackingEnabled, setEyeTrackingEnabled] = useState(false)
  const [showCalibration, setShowCalibration] = useState(false)
  const [cameraStatus, setCameraStatus] = useState<'idle' | 'requesting' | 'active' | 'denied' | 'error'>('idle')
  const [setupModalOpen, setSetupModalOpen] = useState(false)
  const [forceRecalibrate, setForceRecalibrate] = useState(false)
  const [activeStream, setActiveStream] = useState<MediaStream | null>(null)

  const cte = useTelemetry({
    skill: 'reading',
    sessionId: sessionId ? `reading_${sessionId}` : 'reading_0',
    config: {
      gazeEnabled: eyeTrackingEnabled,
      debugOverlay: true,
    },
    totalWords: paragraphs.reduce((sum, p) => sum + p.text.split(/\s+/).length, 0),
  })

  const calibration = useCalibration()

  const gazeDebug = useGazeDebug({
    tracker: cte.tracker as ReadingTracker | null,
    enabled: cte.status === 'active' && eyeTrackingEnabled,
  })

  // Bridge: FaceMesh iris data → calibration system during calibration
  const [currentIrisPosition, setCurrentIrisPosition] = useState<{ x: number; y: number } | null>(null)
  const [faceMeshReady, setFaceMeshReady] = useState(false)
  const [downloadProgress, setDownloadProgress] = useState<{ stage: string; progress: number } | null>(null)

  useEffect(() => {
    if (!showCalibration || cte.status !== 'active') return

    const tracker = cte.tracker as ReadingTracker | null
    if (!tracker) return

    // Listen for FaceMesh results (already being produced by ReadingTracker pipeline)
    const disposeResult = tracker.faceMesh.on('result', (result) => {
      if (result.landmarks) {
        setFaceMeshReady(true)
        // Average both irises for calibration
        const irisX = (result.landmarks.leftIris.x + result.landmarks.rightIris.x) / 2
        const irisY = (result.landmarks.leftIris.y + result.landmarks.rightIris.y) / 2
        setCurrentIrisPosition({ x: irisX, y: irisY })
      }
    })

    // Listen for download progress
    const disposeProgress = tracker.faceMesh.on('progress', (progress) => {
      setDownloadProgress({ stage: progress.stage, progress: progress.progress })
    })

    return () => {
      disposeResult()
      disposeProgress()
      setFaceMeshReady(false)
      setCurrentIrisPosition(null)
      setDownloadProgress(null)
    }
  }, [showCalibration, cte.status, cte.tracker])

  const handleOpenSetup = useCallback((force = false) => {
    setForceRecalibrate(force)
    setSetupModalOpen(true)
  }, [])

  const handleSetupComplete = useCallback(async (mediaStream: MediaStream) => {
    setSetupModalOpen(false)
    setActiveStream(mediaStream)
    setCameraStatus('active')
    setEyeTrackingEnabled(true)

    const stored = await calibration.loadStored()
    if (!stored || forceRecalibrate) {
      setShowCalibration(true)
      calibration.startCalibration()
    }
  }, [calibration, forceRecalibrate])

  const handleSetupCancel = useCallback(() => {
    setSetupModalOpen(false)
  }, [])

  /** Immediately stop all eye tracking — works at any phase */
  const handleStopEyeTracking = useCallback(() => {
    // Stop CTE tracker if running
    if (cte.status === 'active' || cte.status === 'starting') {
      cte.stop()
    }
    // Dismiss calibration overlay
    if (showCalibration) {
      setShowCalibration(false)
      calibration.cancel()
    }
    if (activeStream) {
      activeStream.getTracks().forEach((t) => t.stop())
      setActiveStream(null)
    }
    // Reset all state
    setEyeTrackingEnabled(false)
    setCameraStatus('idle')
    setFaceMeshReady(false)
    setCurrentIrisPosition(null)
    setDownloadProgress(null)
  }, [cte, showCalibration, calibration, activeStream])

  // Pre-warm handled globally by MediaPipePreloader in layout.tsx

  const handleCalibrationCancel = useCallback(() => {
    setShowCalibration(false)
    calibration.cancel()
    // Stop everything when user cancels calibration
    handleStopEyeTracking()
  }, [calibration, handleStopEyeTracking])

  // When calibration completes, dismiss overlay (CTE is already running)
  useEffect(() => {
    if (calibration.state.status === 'complete' && showCalibration) {
      setShowCalibration(false)
    }
  }, [calibration.state.status, showCalibration])

  // Stop CTE on unmount or phase change to review
  useEffect(() => {
    if (phase === 'review' && cte.status === 'active') {
      cte.stop()
    }
  }, [phase, cte])

  // Weakness profile for adversarial mode — derived from review results when available
  const [weaknessProfile, setWeaknessProfile] = useState<StudentWeaknessProfile | null>(null)

  // Derive weakness profile from completed review results
  useEffect(() => {
    if (!reviewResults) return
    const wrongTypes = reviewResults
      .filter(r => !r.is_correct)
      .map(r => r.mistake_type)
      .filter(Boolean)
    const lowConfidenceTopics = reviewResults
      .filter(r => r.confidence_flag === 'low_confidence_win')
      .map(r => r.evidence_paragraph_id)
      .filter(Boolean)
    const avgTimeMs = Object.values(
      telemetryRef.current.getPayload()
    ).reduce((sum, t) => sum + t.timeToAnswerMs, 0) / (reviewResults.length || 1)

    setWeaknessProfile({
      wrong_question_types:             wrongTypes,
      distractor_patterns_fallen_for:   wrongTypes,    // Mirrors mistake types for now
      low_confidence_win_topics:        lowConfidenceTopics,
      avg_time_per_question_ms:         avgTimeMs,
      target_band:                      7.0,
    })
  }, [reviewResults])

  // Detect ?session_id= and ?auto= query params
  const searchParams = useSearchParams()
  const importedSessionId = searchParams.get('session_id')
  const autoMode = searchParams.get('auto')

  useEffect(() => {
    if (importedSessionId && phase === 'config') {
      const sid = Number(importedSessionId)
      if (!Number.isNaN(sid)) {
        loadFromSession(0, sid)
        readingApi.getSessionPassage(sid).then(setPassage).catch((err) => {
          setError(err instanceof Error ? err.message : 'Failed to load imported passage.')
        })
      }
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [importedSessionId])

  // Auto-generate AI test when ?auto=ai (from onboarding/AI journey)
  const autoTriggeredRef = useRef(false)
  useEffect(() => {
    if (autoMode === 'ai' && phase === 'config' && !autoTriggeredRef.current) {
      autoTriggeredRef.current = true
      const topic = searchParams.get('topic') || 'general'
      const difficulty = searchParams.get('difficulty') || 'intermediate'
      const questionType = searchParams.get('question_type') || 'TRUE_FALSE_NOT_GIVEN'
      handleGenerate({
        difficulty,
        vocabulary_level: 'academic',
        grammar_complexity: 'mixed',
        topic,
        passage_length_words: 600,
        question_types: [
          { type: questionType, count: 4 },
          { type: 'MULTIPLE_CHOICE', count: 3 },
          { type: 'FILL_BLANK', count: 3 },
        ],
      })
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [autoMode, phase])

  // Cleanup telemetry on unmount
  useEffect(() => {
    return () => {
      if (telemetryEnabled) {
        const payload = telemetryRef.current.getPayload()
        if (Object.keys(payload).length > 0) setTelemetryMap(payload)
      }
    }
  }, [telemetryEnabled, setTelemetryMap])

  // ─────────────────────────────────────────────
  //  Handlers
  // ─────────────────────────────────────────────

  const handleGenerate = useCallback(async (config: GenerateReadingRequest) => {
    setPhase('loading')
    setError(null)
    try {
      const response = await readingApi.generate(config)
      setPassage(response)
      timer.reset()
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to generate test. Check your GEMINI_API_KEY.')
    }
  }, [setPhase, setPassage, setError, timer])

  // Adversarial mode: generate targeted trap test then redirect to workspace
  const handleGenerateAdversarial = useCallback(async (
    profile: StudentWeaknessProfile,
    questionType: string,
  ) => {
    setPhase('loading')
    setError(null)
    try {
      const result = await adversarialApi.generateSession({
        weakness_profile: profile,
        question_type: questionType,
        num_questions: 4,
      })
      // Load the newly created session directly into the reading workspace
      loadFromSession(result.passage_id, result.session_id)
      await readingApi.getSessionPassage(result.session_id).then(setPassage)
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to generate adversarial test.')
      setPhase('config')
    }
  }, [setPhase, setError, loadFromSession, setPassage])

  const handleSubmit = useCallback(async () => {
    if (!sessionId || !isAllAnswered) return
    setIsSubmitting(true)
    timer.pause()
    try {
      const answerArray = Object.entries(answers).map(([questionId, answer]) => ({
        question_id: Number(questionId),
        answer,
      }))

      // Build telemetry payload if enabled
      const telemetryPayload: Record<string, QuestionTelemetryData> = {}
      if (telemetryEnabled) {
        Object.entries(telemetryRef.current.getPayload()).forEach(([key, value]) => {
          telemetryPayload[key] = {
            time_to_answer_ms:        value.timeToAnswerMs,
            correction_count:         value.correctionCount,
            answer_history:           value.answerHistory,
            passage_friction_count:   value.passageFrictionCount,
            paragraph_scroll_events:  value.paragraphScrollEvents,
          }
        })
      }

      const response = await readingApi.submitAndAnalyze(sessionId, answerArray, telemetryPayload)
      setReviewResults(response.results, response.score, response.band_estimate)

      // Fire-and-forget: refresh Uma's intervention with updated reading telemetry
      if (telemetryEnabled && response.results) {
        const wrongTypes = response.results
          .filter(r => !r.is_correct)
          .map(r => r.mistake_type)
          .filter(Boolean)
        const lowConfWins = response.results.filter(r => r.confidence_flag === 'low_confidence_win').length
        const avgTimeMs = Object.values(telemetryPayload).reduce(
          (sum, t) => sum + t.time_to_answer_ms, 0
        ) / (response.results.length || 1)
        const avgFriction = Object.values(telemetryPayload).reduce(
          (sum, t) => sum + t.passage_friction_count, 0
        ) / (response.results.length || 1)

        profileApi.refreshUmaIntervention({
          reading_band:                    response.band_estimate,
          reading_sessions:                1,
          reading_wrong_question_types:    wrongTypes,
          reading_avg_time_per_question_ms: avgTimeMs,
          reading_low_confidence_wins:     lowConfWins,
          reading_passage_friction_avg:    avgFriction,
        }).catch(() => {/* silent — Uma refresh is background only */})
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to submit answers')
    } finally {
      setIsSubmitting(false)
    }
  }, [sessionId, answers, isAllAnswered, setReviewResults, setError, telemetryEnabled, timer])

  const handleHighlightParagraph = useCallback((paragraphId: string) => {
    setHighlightedParagraphId(paragraphId)
    document.getElementById(`paragraph-${paragraphId}`)?.scrollIntoView({ behavior: 'smooth', block: 'center' })
  }, [])

  const handleTryAgain = useCallback(() => { reset(); timer.reset() }, [reset, timer])

  // Handle text selection in passage for vocabulary
  const handleTextSelect = useCallback((text: string) => {
    const selection = window.getSelection()
    if (!selection || !selection.rangeCount) return
    const word = text.trim()
    if (!word || word.split(/\s+/).length > 3) return
    const range = selection.getRangeAt(0)
    const rect = range.getBoundingClientRect()
    setVocabSelection({ word, position: { x: rect.left + rect.width / 2, y: rect.top - 10 } })
  }, [])

  const handleCloseVocabPopup = useCallback(() => setVocabSelection(null), [])

  // ─────────────────────────────────────────────
  //  Render
  // ─────────────────────────────────────────────

  return (
    <div className="space-y-6">
      <AnimatePresence mode="wait">

        {/* Phase: Config */}
        {phase === 'config' && (
          <GenerationConfigPanel
            onGenerate={handleGenerate}
            onGenerateAdversarial={handleGenerateAdversarial}
            weaknessProfile={weaknessProfile}
          />
        )}

        {/* Phase: Loading */}
        {phase === 'loading' && (
          <motion.div
            key="loading"
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            className="flex flex-col items-center justify-center py-20"
          >
            <Loader2 className="h-12 w-12 animate-spin text-primary mb-4" />
            <p className="text-lg font-medium">Generating your IELTS test...</p>
            <p className="text-sm text-muted-foreground">AI is creating a personalised passage</p>
          </motion.div>
        )}

        {/* Phase: Workspace (also shows review inside) */}
        {(phase === 'workspace' || phase === 'review') && (
          <motion.div
            key="workspace"
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            className="space-y-6"
          >
            {/* Toolbar */}
            <div className="flex items-center justify-between flex-wrap gap-3">
              <div className="flex items-center gap-4">
                <h2 className="text-xl font-semibold">{title}</h2>
                <span className="text-sm text-muted-foreground">
                  {paragraphs.length} paragraphs
                  {' • '}
                  {questionGroups.reduce((s, g) => s + g.questions.length, 0)} questions
                </span>
              </div>
              <div className="flex items-center gap-3">
                <WorkspaceFeatureChipGroup
                  skill="reading"
                  chips={[
                    { featureKey: 'telemetry',       label: 'Telemetry',    icon: Activity },
                    { featureKey: 'confidenceFlags', label: 'Uma Insights', icon: Brain },
                  ]}
                />
                {/* Eye Tracking Toggle */}
                {cte.status === 'idle' && cameraStatus === 'idle' && (
                  <Button
                    variant="outline"
                    size="sm"
                    className="gap-1.5 text-xs"
                    onClick={() => handleOpenSetup(false)}
                  >
                    <span className="relative flex h-2 w-2">
                      <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-green-400 opacity-75" />
                      <span className="relative inline-flex rounded-full h-2 w-2 bg-green-500" />
                    </span>
                    Eye Tracking
                    {/* Show cached indicator if model is likely cached */}
                    {(() => {
                      if (typeof window === 'undefined') return null
                      const cacheKey = `cte_facemesh_cached_https://storage.googleapis.com/mediapipe-models/face_landmarker/face_landmarker/float16/1/face_landmarker.task`
                      const isCached = localStorage.getItem(cacheKey) === 'true'
                      return isCached ? (
                        <span className="ml-1 text-[10px] bg-green-100 text-green-700 px-1 py-0.5 rounded">
                          Cached
                        </span>
                      ) : null
                    })()}
                  </Button>
                )}
                {(cameraStatus === 'requesting' || (cameraStatus === 'active' && cte.status !== 'active')) && (
                  <div className="flex items-center gap-2">
                    <Button
                      variant="outline"
                      size="sm"
                      className="gap-1.5 text-xs"
                      onClick={handleStopEyeTracking}
                      title="Click to cancel"
                    >
                      <Loader2 className="h-3 w-3 animate-spin" />
                      {cameraStatus === 'requesting' ? 'Allow Camera...' : 'Starting Gaze...'}
                      <span className="ml-1 text-[10px] text-muted-foreground">✕</span>
                    </Button>
                  </div>
                )}
                {cte.status === 'active' && (
                  <div className="flex items-center gap-2">
                    <Button
                      variant="outline"
                      size="sm"
                      className="gap-1.5 text-xs border-blue-500/50 text-blue-600 hover:bg-blue-500/10 transition-colors"
                      onClick={() => handleOpenSetup(true)}
                      title="Click to recalibrate eye tracking"
                    >
                      Recalibrate
                    </Button>
                    <Button
                      variant="outline"
                      size="sm"
                      className="group gap-1.5 text-xs border-green-500/50 text-green-600 hover:border-red-500/50 hover:bg-red-500/10 hover:text-red-600 transition-colors"
                      onClick={handleStopEyeTracking}
                      title="Click to turn off eye tracking"
                    >
                      <span className="relative flex h-2 w-2 group-hover:hidden">
                        <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-green-400 opacity-75" />
                        <span className="relative inline-flex rounded-full h-2 w-2 bg-green-500" />
                      </span>
                      <span className="hidden group-hover:inline-block w-2 h-2 text-[10px] leading-none">✕</span>
                      <span className="group-hover:hidden">Gaze Active</span>
                      <span className="hidden group-hover:inline">Stop Tracking</span>
                    </Button>
                  </div>
                )}
                {cameraStatus === 'denied' && (
                  <Button
                    variant="outline"
                    size="sm"
                    className="gap-1.5 text-xs border-yellow-500/50 text-yellow-600"
                    onClick={() => handleOpenSetup(false)}
                    title="Camera access was denied. Click to retry."
                  >
                    Camera Denied
                  </Button>
                )}
                {(cte.status === 'error' || cameraStatus === 'error') && (
                  <Button
                    variant="outline"
                    size="sm"
                    className="gap-1.5 text-xs border-red-500/50 text-red-600"
                    onClick={() => handleOpenSetup(false)}
                  >
                    Retry Eye Tracking
                  </Button>
                )}
                {/* Timer with Start button */}
                <div className="flex items-center gap-2 px-4 py-2 rounded-xl bg-muted">
                  {!timer.isRunning && timer.seconds === 20 * 60 ? (
                    <Button variant="ghost" size="sm" className="h-7 px-2 gap-1" onClick={timer.start}>
                      <Play className="h-3.5 w-3.5" />
                      <span className="text-sm font-medium">Start Timer</span>
                    </Button>
                  ) : (
                    <button onClick={timer.isRunning ? timer.pause : timer.start} className="flex items-center gap-2">
                      <Clock className={`h-4 w-4 ${timer.seconds <= 60 ? 'text-destructive' : 'text-muted-foreground'}`} />
                      <span className={`font-mono text-sm ${timer.seconds <= 60 ? 'text-destructive font-bold' : ''}`}>
                        {timer.formatted}
                      </span>
                    </button>
                  )}
                </div>
              </div>
            </div>

            {/* Main workspace — split scroll panels */}
            <div className="grid grid-cols-1 lg:grid-cols-2 gap-6 h-[calc(100vh-12rem)]">
              {/* Passage — independently scrollable */}
              <div id="passage-section" className="overflow-y-auto rounded-xl">
                <PassagePane
                  title={title}
                  paragraphs={paragraphs}
                  highlightedParagraphId={highlightedParagraphId}
                  onTextSelect={handleTextSelect}
                  onParagraphEntered={
                    telemetryEnabled
                      ? (pid, ts) => telemetryRef.current.onParagraphEntered(pid, ts)
                      : undefined
                  }
                  onParagraphExited={
                    telemetryEnabled
                      ? (pid, ts) => telemetryRef.current.onParagraphExited(pid, ts)
                      : undefined
                  }
                />
              </div>

              {/* Right panel — Questions OR Review Analysis */}
              <div className="overflow-y-auto rounded-xl space-y-4 pr-1">
                {phase === 'review' && reviewResults ? (
                  <ReviewPanel
                    results={reviewResults}
                    score={score!}
                    bandEstimate={bandEstimate!}
                    sessionId={sessionId!}
                    paragraphs={paragraphs}
                    onHighlightParagraph={handleHighlightParagraph}
                    onTryAgain={handleTryAgain}
                  />
                ) : (
                  <>
                    <QuestionsPanel
                      groups={questionGroups}
                      answers={answers}
                      submitted={false}
                      onAnswer={(qId, answer) => {
                        if (telemetryEnabled) telemetryRef.current.onAnswerChange(qId, answer)
                        setAnswer(qId, answer)
                      }}
                      onQuestionFocus={(qId) => {
                        if (telemetryEnabled) telemetryRef.current.onQuestionFocus(qId)
                      }}
                    />

                    <div className="sticky bottom-0 bg-background/95 backdrop-blur-sm pt-3 pb-1">
                      <Button
                        onClick={handleSubmit}
                        disabled={!isAllAnswered || isSubmitting}
                        className="w-full"
                        size="lg"
                      >
                        {isSubmitting ? (
                          <><Loader2 className="h-4 w-4 mr-2 animate-spin" />Analyzing...</>
                        ) : (
                          <><Send className="h-4 w-4 mr-2" />Submit Answers</>
                        )}
                      </Button>
                    </div>
                  </>
                )}
              </div>
            </div>
          </motion.div>
        )}

      </AnimatePresence>

      {/* Vocabulary selection popup */}
      <AnimatePresence>
        {vocabSelection && (
          <VocabSelectionPopup
            word={vocabSelection.word}
            position={vocabSelection.position}
            onClose={handleCloseVocabPopup}
          />
        )}
      </AnimatePresence>

      {/* Error banner */}
      {error && (
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          className="p-4 rounded-xl bg-destructive/10 border border-destructive/20"
        >
          <div className="flex items-center gap-3">
            <AlertCircle className="h-5 w-5 text-destructive" />
            <div>
              <p className="font-medium text-destructive">Error</p>
              <p className="text-sm text-muted-foreground">{error}</p>
            </div>
          </div>
        </motion.div>
      )}

      {/* ── CTE Overlays ── */}

      <EyeTrackingSetupModal
        isOpen={setupModalOpen}
        onClose={handleSetupCancel}
        onComplete={handleSetupComplete}
        cte={cte}
      />

      {/* Calibration overlay (full-screen) */}
      {showCalibration && (
        <CalibrationOverlay
          state={calibration.state}
          currentTarget={calibration.currentTarget}
          targets={calibration.targets}
          onConfirmLooking={calibration.confirmLooking}
          onAddSample={calibration.addSample}
          onCancel={handleCalibrationCancel}
          irisPosition={currentIrisPosition}
          cameraReady={faceMeshReady}
          stream={activeStream}
          cteTracker={cte.tracker}
        />
      )}

      {/* Gaze debug overlay (shows gaze dot, trail, fixation heatmap) */}
      {cte.status === 'active' && eyeTrackingEnabled && (
        <GazeDebugOverlay
          trail={gazeDebug.trail}
          fixations={gazeDebug.fixations}
          regressionCount={gazeDebug.regressionCount}
          visible={true}
        />
      )}
    </div>
  )
}
