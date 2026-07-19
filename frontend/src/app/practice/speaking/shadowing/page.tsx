'use client'

import { useState, useEffect } from 'react'
import { motion, AnimatePresence } from 'framer-motion'
import {
  Mic,
  MicOff,
  Play,
  Square,
  RotateCcw,
  ChevronRight,
  ChevronLeft,
  Check,
  X,
  AlertTriangle,
  Volume2,
  Loader2,
  Award,
  Target,
} from 'lucide-react'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Badge } from '@/components/ui/badge'
import { Progress } from '@/components/ui/progress'
import { cn } from '@/lib/utils'
import { useShadowingSession } from '@/lib/hooks/useShadowingSession'

type Phase = 'config' | 'listening' | 'recording' | 'assessing' | 'result'

export default function ShadowingPage() {
  const {
    model,
    currentTier,
    currentTierIndex,
    isPlaying,
    isRecording,
    hasRecording,
    isAssessing,
    lastAttempt,
    attempts,
    error,
    loadModel,
    startShadowing,
    stopShadowing,
    assessRecording,
    advanceToNextTier,
    retryTier,
  } = useShadowingSession()
  
  const [phase, setPhase] = useState<Phase>('config')
  const [topic, setTopic] = useState('technology')
  const [loading, setLoading] = useState(false)
  
  // Load model on mount
  useEffect(() => {
    handleStart()
  }, [])
  
  const handleStart = async () => {
    setLoading(true)
    try {
      await loadModel(topic, 2)
    } catch (err) {
      console.error('Failed to load model:', err)
    } finally {
      setLoading(false)
    }
  }
  
  const handleStartShadowing = async () => {
    setPhase('recording')
    await startShadowing()
  }
  
  const handleStopShadowing = () => {
    stopShadowing()
    setPhase('assessing')
  }
  
  const handleAssess = async () => {
    try {
      await assessRecording()
      setPhase('result')
    } catch (err) {
      console.error('Assessment failed:', err)
      setPhase('recording')
    }
  }
  
  const handleNext = () => {
    const advanced = advanceToNextTier()
    if (advanced) {
      setPhase('listening')
    } else {
      // Session complete
      setPhase('config')
    }
  }
  
  const handleRetry = () => {
    retryTier()
    setPhase('listening')
  }
  
  // Auto-assess when recording stops
  useEffect(() => {
    if (phase === 'assessing' && hasRecording) {
      handleAssess()
    }
  }, [phase, hasRecording])
  
  // Pass criteria
  const passCriteria = model?.pass_criteria || { phoneme_threshold: 0.75, rhythm_threshold: 0.70 }
  
  return (
    <div className="container max-w-4xl mx-auto py-8 px-4">
      {/* Header */}
      <motion.div
        initial={{ opacity: 0, y: -20 }}
        animate={{ opacity: 1, y: 0 }}
        className="mb-8"
      >
        <div className="flex items-center gap-3 mb-2">
          <Mic className="h-8 w-8 text-purple-500" />
          <h1 className="text-3xl font-bold">Shadowing Practice</h1>
        </div>
        <p className="text-muted-foreground">
          Listen to the model answer and speak along simultaneously. Match the rhythm, pace, and intonation.
        </p>
      </motion.div>
      
      <AnimatePresence mode="wait">
        {/* Config/Loading Phase */}
        {phase === 'config' && (
          <motion.div
            key="config"
            initial={{ opacity: 0, scale: 0.95 }}
            animate={{ opacity: 1, scale: 1 }}
            exit={{ opacity: 0, scale: 0.95 }}
          >
            <Card>
              <CardContent className="py-12 text-center">
                {loading ? (
                  <>
                    <Loader2 className="h-16 w-16 mx-auto text-muted-foreground animate-spin mb-4" />
                    <h2 className="text-2xl font-bold mb-2">Preparing your session...</h2>
                    <p className="text-muted-foreground">
                      Generating model answers at different band levels
                    </p>
                  </>
                ) : model ? (
                  <>
                    <Award className="h-16 w-16 mx-auto text-green-500 mb-4" />
                    <h2 className="text-2xl font-bold mb-2">Session Complete!</h2>
                    <p className="text-muted-foreground mb-2">
                      You completed {attempts.length} attempts across {model.mutation_tiers.length} tiers
                    </p>
                    <p className="text-sm text-muted-foreground mb-6">
                      Best scores: Phoneme {Math.max(...attempts.map(a => a.phoneme_accuracy))} | 
                      Rhythm {Math.max(...attempts.map(a => a.rhythm_score))}
                    </p>
                    <Button size="lg" onClick={handleStart}>
                      Start New Session
                    </Button>
                  </>
                ) : (
                  <>
                    <Mic className="h-16 w-16 mx-auto text-muted-foreground mb-4" />
                    <h2 className="text-2xl font-bold mb-2">Ready for Shadowing?</h2>
                    <p className="text-muted-foreground mb-6 max-w-md mx-auto">
                      You'll hear a model answer at three difficulty levels. 
                      Speak along and try to match the pronunciation, rhythm, and pace.
                    </p>
                    <Button size="lg" onClick={handleStart} disabled={loading}>
                      <Play className="h-4 w-4 mr-2" />
                      Start Shadowing
                    </Button>
                  </>
                )}
              </CardContent>
            </Card>
          </motion.div>
        )}
        
        {/* Listening Phase */}
        {phase === 'listening' && currentTier && (
          <motion.div
            key="listening"
            initial={{ opacity: 0, x: 50 }}
            animate={{ opacity: 1, x: 0 }}
            exit={{ opacity: 0, x: -50 }}
          >
            {/* Tier Progress */}
            <div className="mb-6">
              <div className="flex items-center justify-between mb-2">
                <span className="text-sm text-muted-foreground">Tier Progress</span>
                <span className="text-sm font-medium">
                  {currentTierIndex + 1} of {model?.mutation_tiers.length}
                </span>
              </div>
              <div className="flex gap-2">
                {model?.mutation_tiers.map((tier, i) => (
                  <div
                    key={tier.tier}
                    className={cn(
                      'flex-1 h-2 rounded-full',
                      i < currentTierIndex
                        ? 'bg-green-500'
                        : i === currentTierIndex
                        ? 'bg-purple-500'
                        : 'bg-muted'
                    )}
                  />
                ))}
              </div>
            </div>
            
            {/* Current Tier Card */}
            <Card className="mb-6">
              <CardHeader>
                <div className="flex items-center justify-between">
                  <CardTitle className="text-base flex items-center gap-2">
                    <Target className="h-4 w-4" />
                    {currentTier.band_label}
                  </CardTitle>
                  <Badge variant="outline">Target: Band {currentTier.target_band}</Badge>
                </div>
              </CardHeader>
              <CardContent className="space-y-4">
                {/* Model Text */}
                <div className="p-4 rounded-lg bg-muted/50">
                  <p className="text-sm text-muted-foreground mb-1">Model Answer:</p>
                  <p className="font-medium">{currentTier.text}</p>
                </div>
                
                {/* Key Changes */}
                <div className="space-y-2">
                  <p className="text-sm font-medium">Key Changes from Previous:</p>
                  <ul className="space-y-1">
                    {currentTier.key_changes.map((change, i) => (
                      <li key={i} className="text-sm text-muted-foreground flex items-start gap-2">
                        <Check className="h-3 w-3 text-green-500 mt-1 flex-shrink-0" />
                        {change}
                      </li>
                    ))}
                  </ul>
                </div>
                
                {/* Audio Hints */}
                <div className="p-3 rounded-lg bg-purple-500/10 border border-purple-200">
                  <p className="text-sm text-purple-700">
                    <Volume2 className="h-4 w-4 inline mr-1" />
                    <strong>Audio Hint:</strong> {currentTier.audio_hints}
                  </p>
                </div>
                
                {/* Pass Criteria */}
                <div className="flex gap-4 text-sm">
                  <span className="text-muted-foreground">
                    Pass criteria: Phoneme ≥{Math.round(passCriteria.phoneme_threshold * 100)}% | 
                    Rhythm ≥{Math.round(passCriteria.rhythm_threshold * 100)}%
                  </span>
                </div>
              </CardContent>
            </Card>
            
            {/* Action Buttons */}
            <div className="flex justify-center gap-4">
              <Button variant="outline" size="lg" onClick={() => {}}>
                <Volume2 className="h-4 w-4 mr-2" />
                Listen First
              </Button>
              <Button size="lg" onClick={handleStartShadowing}>
                <Mic className="h-4 w-4 mr-2" />
                Start Shadowing
              </Button>
            </div>
          </motion.div>
        )}
        
        {/* Recording Phase */}
        {phase === 'recording' && currentTier && (
          <motion.div
            key="recording"
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            exit={{ opacity: 0, y: -20 }}
          >
            <Card>
              <CardHeader>
                <CardTitle className="text-base flex items-center gap-2">
                  {isRecording ? (
                    <>
                      <motion.div
                        animate={{ scale: [1, 1.2, 1] }}
                        transition={{ repeat: Infinity, duration: 1 }}
                      >
                        <Mic className="h-5 w-5 text-red-500" />
                      </motion.div>
                      Recording...
                    </>
                  ) : (
                    <>
                      <Volume2 className="h-5 w-5 text-green-500" />
                      Playing Model...
                    </>
                  )}
                </CardTitle>
              </CardHeader>
              <CardContent className="py-8 text-center">
                <motion.div
                  animate={{ 
                    scale: isRecording ? [1, 1.05, 1] : 1,
                    opacity: isPlaying || isRecording ? 1 : 0.5
                  }}
                  transition={{ repeat: isRecording ? Infinity : 0, duration: 1.5 }}
                >
                  <div className={cn(
                    'w-32 h-32 mx-auto rounded-full flex items-center justify-center mb-6',
                    isRecording ? 'bg-red-500/20' : 'bg-green-500/20'
                  )}>
                    {isRecording ? (
                      <Mic className="h-16 w-16 text-red-500" />
                    ) : (
                      <Volume2 className="h-16 w-16 text-green-500" />
                    )}
                  </div>
                </motion.div>
                
                <p className="text-lg mb-2">
                  {isRecording ? 'Speak along with the model!' : 'Listen and prepare to speak...'}
                </p>
                <p className="text-sm text-muted-foreground mb-6">
                  Match the rhythm, pace, and intonation as closely as possible
                </p>
                
                {/* Model Text (Reference) */}
                <div className="p-4 rounded-lg bg-muted max-w-2xl mx-auto mb-6">
                  <p className="text-sm">{currentTier.text}</p>
                </div>
                
                <Button
                  variant="destructive"
                  size="lg"
                  onClick={handleStopShadowing}
                  disabled={!isRecording && !isPlaying}
                >
                  <Square className="h-4 w-4 mr-2" />
                  Stop & Assess
                </Button>
              </CardContent>
            </Card>
          </motion.div>
        )}
        
        {/* Result Phase */}
        {phase === 'result' && lastAttempt && currentTier && (
          <motion.div
            key="result"
            initial={{ opacity: 0, scale: 0.95 }}
            animate={{ opacity: 1, scale: 1 }}
            exit={{ opacity: 0, scale: 0.95 }}
          >
            {/* Result Card */}
            <Card className="mb-6">
              <CardHeader>
                <div className="flex items-center justify-between">
                  <CardTitle className="text-base flex items-center gap-2">
                    {lastAttempt.passed ? (
                      <>
                        <Check className="h-5 w-5 text-green-500" />
                        Passed!
                      </>
                    ) : (
                      <>
                        <AlertTriangle className="h-5 w-5 text-yellow-500" />
                        Keep Practicing
                      </>
                    )}
                  </CardTitle>
                  <Badge variant={lastAttempt.passed ? 'success' : 'secondary'}>
                    Tier {lastAttempt.tier}
                  </Badge>
                </div>
              </CardHeader>
              <CardContent className="space-y-6">
                {/* Score Metrics */}
                <div className="grid grid-cols-3 gap-4">
                  <ScoreCard
                    label="Phoneme Accuracy"
                    value={lastAttempt.phoneme_accuracy}
                    threshold={passCriteria.phoneme_threshold}
                  />
                  <ScoreCard
                    label="Rhythm Score"
                    value={lastAttempt.rhythm_score}
                    threshold={passCriteria.rhythm_threshold}
                  />
                  <ScoreCard
                    label="Connected Speech"
                    value={lastAttempt.connected_speech_score}
                    threshold={0.7}
                  />
                </div>
                
                {/* Overall Score */}
                <div className="text-center">
                  <p className="text-sm text-muted-foreground">Overall Similarity</p>
                  <p className="text-4xl font-bold">
                    {Math.round(lastAttempt.overall_similarity * 100)}%
                  </p>
                </div>
                
                {/* Feedback */}
                <div className="p-4 rounded-lg bg-muted">
                  <p className="text-sm">{lastAttempt.feedback}</p>
                </div>
                
                {/* Specific Errors */}
                {lastAttempt.specific_errors.length > 0 && (
                  <div className="space-y-2">
                    <p className="text-sm font-medium">Areas to Improve:</p>
                    <ul className="space-y-1">
                      {lastAttempt.specific_errors.map((err, i) => (
                        <li key={i} className="text-sm text-muted-foreground flex items-start gap-2">
                          <AlertTriangle className="h-3 w-3 text-yellow-500 mt-1 flex-shrink-0" />
                          {err}
                        </li>
                      ))}
                    </ul>
                  </div>
                )}
                
                {/* Navigation */}
                <div className="flex justify-between items-center pt-4">
                  <Button variant="ghost" onClick={handleRetry}>
                    <RotateCcw className="h-4 w-4 mr-2" />
                    Try Again
                  </Button>
                  
                  <Button onClick={handleNext}>
                    {lastAttempt.passed ? (
                      <>
                        Next Tier
                        <ChevronRight className="h-4 w-4 ml-2" />
                      </>
                    ) : (
                      <>
                        Retry Tier
                        <RotateCcw className="h-4 w-4 ml-2" />
                      </>
                    )}
                  </Button>
                </div>
              </CardContent>
            </Card>
            
            {/* Attempts History */}
            {attempts.length > 1 && (
              <Card>
                <CardHeader>
                  <CardTitle className="text-base">Attempt History</CardTitle>
                </CardHeader>
                <CardContent>
                  <div className="space-y-2">
                    {attempts.slice(-5).map((attempt, i) => (
                      <div
                        key={i}
                        className="flex items-center justify-between p-2 rounded bg-muted/50"
                      >
                        <span className="text-sm">
                          Tier {attempt.tier} - Attempt {attempts.indexOf(attempt) + 1}
                        </span>
                        <div className="flex gap-4 text-xs text-muted-foreground">
                          <span>P: {Math.round(attempt.phoneme_accuracy * 100)}%</span>
                          <span>R: {Math.round(attempt.rhythm_score * 100)}%</span>
                          {attempt.passed && <Check className="h-3 w-3 text-green-500" />}
                        </div>
                      </div>
                    ))}
                  </div>
                </CardContent>
              </Card>
            )}
          </motion.div>
        )}
      </AnimatePresence>
      
      {/* Error Display */}
      {error && (
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          className="mt-4 p-4 rounded-lg bg-red-500/10 border border-red-200"
        >
          <p className="text-sm text-red-700">{error}</p>
        </motion.div>
      )}
    </div>
  )
}

// Score card component
function ScoreCard({ label, value, threshold }: { label: string; value: number; threshold: number }) {
  const passed = value >= threshold
  const percentage = Math.round(value * 100)
  
  return (
    <div className="text-center p-3 rounded-lg bg-muted/50">
      <p className="text-xs text-muted-foreground mb-1">{label}</p>
      <p className={cn(
        'text-2xl font-bold',
        passed ? 'text-green-600' : 'text-yellow-600'
      )}>
        {percentage}%
      </p>
      <Progress value={percentage} className="h-1 mt-2" />
    </div>
  )
}
