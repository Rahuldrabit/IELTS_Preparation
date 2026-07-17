'use client'

import { useState, useCallback, useEffect, useRef } from 'react'
import { motion, AnimatePresence } from 'framer-motion'
import {
  Mic, Square, RefreshCw, MessageCircle, AlertCircle,
  Loader2, Volume2, Sparkles, Zap, PenTool,
} from 'lucide-react'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Badge } from '@/components/ui/badge'
import { Input } from '@/components/ui/input'
import { cn } from '@/lib/utils'
import { useAudioRecorder } from '@/lib/hooks/useAudioRecorder'
import { speakingApi, type SpeakingFeedback, type SpeakingTopic } from '@/lib/services/speaking'
import { useFeature } from '@/lib/hooks/useFeature'
import { useSpeakingStore } from '@/lib/store/speakingStore'
import { useMutationEngine } from '@/lib/hooks/useMutationEngine'
import { MutationSection } from '@/components/features/speaking/MutationSection'
import { SessionFeatureBar } from '@/components/ui/SessionFeatureBar'
import { WorkspaceFeatureChipGroup } from '@/components/ui/WorkspaceFeatureChip'

// ─────────────────────────────────────────────
//  Criterion config
// ─────────────────────────────────────────────

const CRITERIA = [
  { key: 'fluency',       label: 'Fluency & Coherence',   color: 'text-blue-500',   stroke: 'text-blue-500' },
  { key: 'lexical',       label: 'Lexical Resource',       color: 'text-purple-500', stroke: 'text-purple-500' },
  { key: 'grammar',       label: 'Grammar',                color: 'text-orange-500', stroke: 'text-orange-500' },
  { key: 'pronunciation', label: 'Pronunciation',          color: 'text-green-500',  stroke: 'text-green-500' },
] as const

// ─────────────────────────────────────────────
//  Page
// ─────────────────────────────────────────────

export default function SpeakingPage() {
  // ── Feature flags ─────────────────────────────
  const mutationEngineOn = useFeature('speaking', 'mutationEngine')

  // ── Mutation store + engine (only used when flag is on) ──
  const speakingStore  = useSpeakingStore()
  const { generateMutations } = useMutationEngine()

  // ── Local state for basic recording flow ─────
  const [phase, setPhase]       = useState<'config' | 'recording' | 'analyzing' | 'results'>('config')
  const [feedback, setFeedback] = useState<SpeakingFeedback | null>(null)
  const [error, setError]       = useState<string | null>(null)
  const [topic, setTopic]       = useState<SpeakingTopic | null>(null)
  const [customTopic, setCustomTopic] = useState('')
  const [isGeneratingTopic, setIsGeneratingTopic] = useState(false)

  const {
    isRecording,
    secondsRemaining,
    audioBlob,
    startRecording,
    stopRecording,
    reset: resetRecorder,
    error: recorderError,
  } = useAudioRecorder({ maxDuration: 30 })

  const [audioLevels, setAudioLevels] = useState<number[]>(Array(20).fill(10))
  const animFrameRef = useRef<number>(0)

  // Animate waveform bars while recording
  useEffect(() => {
    if (isRecording) {
      const animate = () => {
        setAudioLevels(Array.from({ length: 20 }, () => Math.random() * 80 + 10))
        animFrameRef.current = requestAnimationFrame(animate)
      }
      animFrameRef.current = requestAnimationFrame(animate)
    } else {
      cancelAnimationFrame(animFrameRef.current)
      setAudioLevels(Array(20).fill(10))
    }
    return () => cancelAnimationFrame(animFrameRef.current)
  }, [isRecording])

  // Auto-stop when timer reaches 0
  useEffect(() => {
    if (secondsRemaining === 0 && isRecording) stopRecording()
  }, [secondsRemaining, isRecording, stopRecording])

  // Submit for analysis when recording stops and blob is ready
  useEffect(() => {
    if (audioBlob && !isRecording && phase === 'recording') {
      submitRecording(audioBlob)
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [audioBlob, isRecording])

  const submitRecording = useCallback(async (blob: Blob) => {
    setPhase('analyzing')
    setError(null)
    try {
      const result = await speakingApi.transcribe(blob)
      setFeedback(result)
      setPhase('results')

      // If mutation engine is on, kick off generation automatically after 500ms
      if (mutationEngineOn) {
        speakingStore.setBasicFeedback(result)
        speakingStore.setPhase('results')
        setTimeout(() => {
          generateMutations(result.transcript, result.band)
        }, 500)
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to analyse recording.')
      setPhase('recording')
    }
  }, [mutationEngineOn, speakingStore, generateMutations])

  const handleTryAgain = useCallback(() => {
    setPhase('config')
    setFeedback(null)
    setError(null)
    setTopic(null)
    setCustomTopic('')
    resetRecorder()
    if (mutationEngineOn) speakingStore.reset()
  }, [resetRecorder, mutationEngineOn, speakingStore])

  const handleGenerateTopic = useCallback(async () => {
    setIsGeneratingTopic(true)
    setError(null)
    try {
      const generated = await speakingApi.generateTopic(2)
      setTopic(generated)
      setPhase('recording')
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to generate topic')
    } finally {
      setIsGeneratingTopic(false)
    }
  }, [])

  const handleFreeTopic = useCallback(() => {
    const topicText = customTopic.trim() || 'Speak freely about any topic of your choice.'
    setTopic({
      part: 2,
      topic: topicText,
      bullet_points: [],
    })
    setPhase('recording')
  }, [customTopic])

  const formatTime = (seconds: number) => {
    const mins = Math.floor(seconds / 60)
    const secs = seconds % 60
    return `${mins}:${secs.toString().padStart(2, '0')}`
  }

  // ─────────────────────────────────────────────
  //  Render
  // ─────────────────────────────────────────────

  return (
    <div className="space-y-6">
      {/* Header */}
      <motion.div initial={{ opacity: 0, y: -20 }} animate={{ opacity: 1, y: 0 }}>
        <div className="flex items-center justify-between flex-wrap gap-3">
          <div>
            <h1 className="text-3xl font-bold mb-1">Speaking Practice</h1>
            <p className="text-muted-foreground">
              Record a 30-second response and get instant AI feedback
            </p>
          </div>

          {/* Workspace feature chips */}
          {phase === 'recording' && (
            <WorkspaceFeatureChipGroup
              skill="speaking"
              chips={[
                { featureKey: 'mutationEngine',  label: 'Mutations',    icon: Zap },
                { featureKey: 'workletRecorder', label: 'HD Recorder',  icon: Mic },
              ]}
            />
          )}
        </div>
      </motion.div>

      <AnimatePresence mode="wait">
        {/* ── Config Phase ── */}
        {phase === 'config' && (
          <motion.div
            key="config"
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            exit={{ opacity: 0, y: -20 }}
            className="space-y-6"
          >
            <Card className="max-w-2xl mx-auto">
              <CardHeader>
                <div className="flex items-center gap-3">
                  <div className="h-12 w-12 rounded-xl bg-primary/10 flex items-center justify-center">
                    <Mic className="h-6 w-6 text-primary" />
                  </div>
                  <div>
                    <CardTitle className="text-xl">Speaking Practice</CardTitle>
                    <p className="text-sm text-muted-foreground">
                      Generate a topic or speak about anything you want
                    </p>
                  </div>
                </div>
              </CardHeader>
              <CardContent className="space-y-6">
                {/* Generate AI Topic */}
                <Button
                  onClick={handleGenerateTopic}
                  disabled={isGeneratingTopic}
                  className="w-full"
                  size="lg"
                >
                  {isGeneratingTopic ? (
                    <><Loader2 className="h-4 w-4 mr-2 animate-spin" />Generating Topic…</>
                  ) : (
                    <><Sparkles className="h-4 w-4 mr-2" />Generate IELTS Cue Card</>
                  )}
                </Button>

                <div className="flex items-center gap-3">
                  <div className="flex-1 h-px bg-border" />
                  <span className="text-xs text-muted-foreground">or</span>
                  <div className="flex-1 h-px bg-border" />
                </div>

                {/* Free Topic */}
                <div className="space-y-3">
                  <Input
                    placeholder="Type your own topic (or leave blank to free-speak)"
                    value={customTopic}
                    onChange={(e) => setCustomTopic(e.target.value)}
                  />
                  <Button
                    onClick={handleFreeTopic}
                    variant="outline"
                    className="w-full"
                    size="lg"
                  >
                    <PenTool className="h-4 w-4 mr-2" />
                    {customTopic.trim() ? 'Speak About This Topic' : 'Free Speak (No Topic)'}
                  </Button>
                </div>

                <SessionFeatureBar
                  skill="speaking"
                  features={[
                    { featureKey: 'mutationEngine',  label: 'Mutation Engine', icon: Zap },
                    { featureKey: 'workletRecorder', label: 'HD Recorder',     icon: Mic },
                  ]}
                />
              </CardContent>
            </Card>
          </motion.div>
        )}

        {/* ── Recording / Analyzing ── */}
        {(phase === 'recording' || phase === 'analyzing') && (
          <motion.div
            key="recording"
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            exit={{ opacity: 0, y: -20 }}
            className="space-y-6"
          >
            {/* Cue Card */}
            <Card>
              <CardHeader className="pb-3">
                <div className="flex items-center justify-between">
                  <CardTitle className="text-base">
                    {topic?.part === 1 ? 'Part 1: Question' : topic?.part === 3 ? 'Part 3: Discussion' : 'Part 2: Cue Card'}
                  </CardTitle>
                  <Badge variant="outline">30 seconds</Badge>
                </div>
              </CardHeader>
              <CardContent>
                <div className="p-4 rounded-xl bg-muted/50">
                  <p className="leading-relaxed font-medium mb-2">{topic?.topic}</p>
                  {topic?.bullet_points && topic.bullet_points.length > 0 && (
                    <ul className="space-y-1 text-sm text-muted-foreground ml-4">
                      {topic.bullet_points.map((point, i) => (
                        <li key={i} className="list-disc">{point}</li>
                      ))}
                    </ul>
                  )}
                  {topic?.follow_up && (
                    <p className="text-sm text-muted-foreground mt-3 italic">
                      Follow-up: {topic.follow_up}
                    </p>
                  )}
                </div>
              </CardContent>
            </Card>

            {/* Recording interface */}
            <Card className={cn(
              'relative overflow-hidden transition-all',
              isRecording && 'border-primary shadow-lg shadow-primary/20'
            )}>
              {isRecording && (
                <div className="absolute inset-0 bg-primary/5 animate-pulse pointer-events-none" />
              )}
              <CardContent className="p-8">
                <div className="flex flex-col items-center gap-8">
                  {/* Waveform */}
                  <div className="flex items-center justify-center gap-1 h-20">
                    {audioLevels.map((level, i) => (
                      <motion.div
                        key={i}
                        animate={{ height: isRecording ? level : 10 }}
                        transition={{ duration: 0.1 }}
                        className={cn('w-2 rounded-full', isRecording ? 'bg-primary' : 'bg-muted')}
                      />
                    ))}
                  </div>

                  {/* Timer */}
                  <div className="text-center">
                    <p className={cn(
                      'text-4xl font-mono font-bold',
                      phase === 'analyzing' ? 'text-primary' : isRecording ? 'text-primary' : 'text-muted-foreground'
                    )}>
                      {phase === 'analyzing'
                        ? <Loader2 className="inline h-10 w-10 animate-spin" />
                        : formatTime(secondsRemaining)
                      }
                    </p>
                    <p className="text-sm text-muted-foreground mt-2">
                      {phase === 'analyzing'
                        ? 'Analysing…'
                        : isRecording
                        ? `Recording… (${30 - secondsRemaining}s elapsed)`
                        : 'Press the button to start recording'}
                    </p>
                  </div>

                  {/* Record button */}
                  {phase === 'recording' && !isRecording && (
                    <motion.button
                      whileHover={{ scale: 1.05 }}
                      whileTap={{ scale: 0.95 }}
                      onClick={startRecording}
                      className="h-20 w-20 rounded-full bg-primary hover:bg-primary/90 flex items-center justify-center shadow-lg"
                    >
                      <Mic className="h-8 w-8 text-white" />
                    </motion.button>
                  )}

                  {isRecording && (
                    <motion.button
                      whileHover={{ scale: 1.05 }}
                      whileTap={{ scale: 0.95 }}
                      onClick={stopRecording}
                      className="h-20 w-20 rounded-full bg-destructive hover:bg-destructive/90 flex items-center justify-center shadow-lg"
                    >
                      <Square className="h-8 w-8 text-white" />
                    </motion.button>
                  )}
                </div>
              </CardContent>
            </Card>
          </motion.div>
        )}

        {/* ── Results ── */}
        {phase === 'results' && feedback && (
          <motion.div
            key="results"
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            exit={{ opacity: 0, y: -20 }}
            className="space-y-6"
          >
            {/* Transcript */}
            <Card>
              <CardHeader className="pb-3">
                <CardTitle className="text-base flex items-center gap-2">
                  <Volume2 className="h-4 w-4" />
                  Your Transcript
                </CardTitle>
              </CardHeader>
              <CardContent>
                <p className="text-sm leading-relaxed bg-muted/50 p-4 rounded-xl">
                  {feedback.transcript || '(No transcript available)'}
                </p>
              </CardContent>
            </Card>

            {/* Score card */}
            <Card>
              <CardContent className="p-6">
                <div className="flex items-center justify-between mb-6">
                  <h3 className="text-xl font-semibold">Your Score</h3>
                  <Badge variant="default" className="text-lg px-4 py-1">
                    Band {feedback.band.toFixed(1)}
                  </Badge>
                </div>

                <div className="grid grid-cols-2 md:grid-cols-4 gap-6">
                  {CRITERIA.map((item) => {
                    const value = feedback[item.key as keyof SpeakingFeedback] as number
                    return (
                      <div key={item.key} className="text-center">
                        <div className="relative h-24 w-24 mx-auto mb-2">
                          <svg className="h-24 w-24 transform -rotate-90">
                            <circle cx="48" cy="48" r="40" stroke="currentColor"
                              strokeWidth="8" fill="none" className="text-muted" />
                            <circle cx="48" cy="48" r="40" stroke="currentColor"
                              strokeWidth="8" fill="none" strokeLinecap="round"
                              className={item.stroke}
                              strokeDasharray={`${(value / 9) * 251} 251`} />
                          </svg>
                          <div className="absolute inset-0 flex items-center justify-center">
                            <span className="text-xl font-bold">{value.toFixed(1)}</span>
                          </div>
                        </div>
                        <p className="text-sm text-muted-foreground">{item.label}</p>
                      </div>
                    )
                  })}
                </div>
              </CardContent>
            </Card>

            {/* Suggestions */}
            <Card>
              <CardHeader>
                <CardTitle className="text-base flex items-center gap-2">
                  <MessageCircle className="h-4 w-4" />
                  Improvement Suggestions
                </CardTitle>
              </CardHeader>
              <CardContent>
                <ul className="space-y-3">
                  {feedback.suggestions.map((suggestion, i) => (
                    <li key={i} className="flex items-start gap-3">
                      <div className="flex h-6 w-6 items-center justify-center rounded-full bg-primary/10 shrink-0 mt-0.5">
                        <span className="text-xs font-medium text-primary">{i + 1}</span>
                      </div>
                      <p className="text-sm">{suggestion}</p>
                    </li>
                  ))}
                </ul>
              </CardContent>
            </Card>

            {/* Mutation Engine section — gated by feature flag */}
            {mutationEngineOn && <MutationSection />}

            {/* Actions */}
            <div className="flex gap-3">
              <Button onClick={handleTryAgain} className="flex-1">
                <RefreshCw className="h-4 w-4 mr-2" />
                Try Again
              </Button>
            </div>
          </motion.div>
        )}
      </AnimatePresence>

      {/* Error state */}
      {(error || recorderError) && (
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          className="p-4 rounded-xl bg-destructive/10 border border-destructive/20"
        >
          <div className="flex items-center gap-3">
            <AlertCircle className="h-5 w-5 text-destructive" />
            <div>
              <p className="font-medium text-destructive">Error</p>
              <p className="text-sm text-muted-foreground">{error ?? recorderError}</p>
            </div>
          </div>
        </motion.div>
      )}
    </div>
  )
}
