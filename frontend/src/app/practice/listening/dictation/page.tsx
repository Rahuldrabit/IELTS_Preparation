'use client'

import { useState, useCallback, useRef, useEffect } from 'react'
import { motion, AnimatePresence } from 'framer-motion'
import {
  Play,
  Pause,
  RotateCcw,
  Send,
  Loader2,
  Headphones,
  Check,
  X,
  AlertTriangle,
  Volume2,
  VolumeX,
  ChevronRight,
  ChevronLeft,
} from 'lucide-react'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Badge } from '@/components/ui/badge'
import { Progress } from '@/components/ui/progress'
import { cn } from '@/lib/utils'
import {
  listeningApi,
  DictationContentResponse,
  DictationScoreResponse,
  DictationSegment,
  WordDiff,
} from '@/lib/services/listening'

type Phase = 'config' | 'playing' | 'typing' | 'result'

export default function DictationPage() {
  const [phase, setPhase] = useState<Phase>('config')
  const [loading, setLoading] = useState(false)
  const [content, setContent] = useState<DictationContentResponse | null>(null)
  const [currentSegmentIndex, setCurrentSegmentIndex] = useState(0)
  const [typedText, setTypedText] = useState('')
  const [scoreResult, setScoreResult] = useState<DictationScoreResponse | null>(null)
  const [isPlaying, setIsPlaying] = useState(false)
  const [completedSegments, setCompletedSegments] = useState<Set<number>>(new Set())
  
  const utteranceRef = useRef<SpeechSynthesisUtterance | null>(null)

  const currentSegment = content?.segments[currentSegmentIndex]

  // Generate dictation content
  const handleStart = async () => {
    setLoading(true)
    try {
      const result = await listeningApi.generateDictation({
        section: 2,
        accent: 'british',
        speed: 'normal',
        topic: 'everyday life',
      })
      setContent(result)
      setCurrentSegmentIndex(0)
      setCompletedSegments(new Set())
      setPhase('playing')
    } catch (error) {
      console.error('Failed to generate dictation:', error)
    } finally {
      setLoading(false)
    }
  }

  // Play current segment using Web Speech API
  const playSegment = useCallback(() => {
    if (!currentSegment || typeof window === 'undefined') return

    const utterance = new SpeechSynthesisUtterance(currentSegment.text)
    utterance.lang = content?.tts_config.lang || 'en-GB'
    utterance.rate = content?.tts_config.rate || 0.9
    utterance.pitch = content?.tts_config.pitch || 1.0

    // Select voice
    const voices = window.speechSynthesis.getVoices()
    const langPrefix = utterance.lang.split('-')[0]
    const voice = voices.find(v => v.lang.startsWith(langPrefix))
    if (voice) utterance.voice = voice

    utterance.onstart = () => setIsPlaying(true)
    utterance.onend = () => {
      setIsPlaying(false)
      setPhase('typing')
    }
    utterance.onerror = () => setIsPlaying(false)

    utteranceRef.current = utterance
    window.speechSynthesis.speak(utterance)
  }, [currentSegment, content])

  const stopPlayback = useCallback(() => {
    if (typeof window !== 'undefined') {
      window.speechSynthesis.cancel()
      setIsPlaying(false)
    }
  }, [])

  // Replay segment
  const handleReplay = () => {
    stopPlayback()
    setPhase('playing')
    setTimeout(() => playSegment(), 100)
  }

  // Submit answer
  const handleSubmit = async () => {
    if (!content || !currentSegment) return

    setLoading(true)
    try {
      const result = await listeningApi.scoreDictation({
        segment_id: currentSegment.id,
        session_id: content.session_id,
        target_text: currentSegment.text,
        typed_text: typedText,
      })
      setScoreResult(result)
      setCompletedSegments(prev => new Set([...prev, currentSegment.id]))
      setPhase('result')
    } catch (error) {
      console.error('Failed to score dictation:', error)
    } finally {
      setLoading(false)
    }
  }

  // Next segment
  const handleNext = () => {
    if (!content) return
    
    setTypedText('')
    setScoreResult(null)
    
    if (currentSegmentIndex < content.segments.length - 1) {
      setCurrentSegmentIndex(prev => prev + 1)
      setPhase('playing')
      setTimeout(() => playSegment(), 100)
    } else {
      // All done
      setPhase('config')
    }
  }

  // Previous segment
  const handlePrevious = () => {
    if (currentSegmentIndex > 0) {
      stopPlayback()
      setTypedText('')
      setScoreResult(null)
      setCurrentSegmentIndex(prev => prev - 1)
      setPhase('playing')
      setTimeout(() => playSegment(), 100)
    }
  }

  // Auto-play when entering playing phase
  useEffect(() => {
    if (phase === 'playing' && currentSegment) {
      // Wait for voices to load
      const timer = setTimeout(() => {
        playSegment()
      }, 300)
      return () => clearTimeout(timer)
    }
  }, [phase, currentSegmentIndex])

  // Cleanup
  useEffect(() => {
    return () => {
      stopPlayback()
    }
  }, [stopPlayback])

  // Progress calculation
  const progress = content
    ? (completedSegments.size / content.total_segments) * 100
    : 0

  return (
    <div className="container max-w-4xl mx-auto py-8 px-4">
      {/* Header */}
      <motion.div
        initial={{ opacity: 0, y: -20 }}
        animate={{ opacity: 1, y: 0 }}
        className="mb-8"
      >
        <div className="flex items-center gap-3 mb-2">
          <Headphones className="h-8 w-8 text-green-500" />
          <h1 className="text-3xl font-bold">Dictation Practice</h1>
        </div>
        <p className="text-muted-foreground">
          Listen to each sentence and type what you hear. This trains your listening accuracy and spelling.
        </p>
      </motion.div>

      <AnimatePresence mode="wait">
        {/* Config Phase */}
        {phase === 'config' && (
          <motion.div
            key="config"
            initial={{ opacity: 0, scale: 0.95 }}
            animate={{ opacity: 1, scale: 1 }}
            exit={{ opacity: 0, scale: 0.95 }}
          >
            <Card>
              <CardContent className="py-12 text-center">
                {content ? (
                  <>
                    <Check className="h-16 w-16 mx-auto text-green-500 mb-4" />
                    <h2 className="text-2xl font-bold mb-2">Session Complete!</h2>
                    <p className="text-muted-foreground mb-6">
                      You completed {completedSegments.size} of {content.total_segments} segments
                    </p>
                    <Button size="lg" onClick={handleStart}>
                      Start New Session
                    </Button>
                  </>
                ) : (
                  <>
                    <Headphones className="h-16 w-16 mx-auto text-muted-foreground mb-4" />
                    <h2 className="text-2xl font-bold mb-2">Ready for Dictation?</h2>
                    <p className="text-muted-foreground mb-6 max-w-md mx-auto">
                      Each sentence will be read aloud. Listen carefully, then type exactly what you heard.
                      You can replay the audio as many times as needed.
                    </p>
                    <Button size="lg" onClick={handleStart} disabled={loading}>
                      {loading ? (
                        <>
                          <Loader2 className="h-4 w-4 mr-2 animate-spin" />
                          Generating...
                        </>
                      ) : (
                        <>
                          <Play className="h-4 w-4 mr-2" />
                          Start Dictation
                        </>
                      )}
                    </Button>
                  </>
                )}
              </CardContent>
            </Card>
          </motion.div>
        )}

        {/* Playing Phase */}
        {phase === 'playing' && currentSegment && (
          <motion.div
            key="playing"
            initial={{ opacity: 0, x: 50 }}
            animate={{ opacity: 1, x: 0 }}
            exit={{ opacity: 0, x: -50 }}
          >
            <Card>
              <CardHeader>
                <div className="flex items-center justify-between">
                  <CardTitle className="text-base">
                    Segment {currentSegmentIndex + 1} of {content?.total_segments}
                  </CardTitle>
                  <Badge variant="outline">
                    {currentSegment.word_count} words
                  </Badge>
                </div>
                <Progress value={progress} className="h-2 mt-2" />
              </CardHeader>
              <CardContent className="py-12 text-center">
                <motion.div
                  animate={{ scale: isPlaying ? [1, 1.05, 1] : 1 }}
                  transition={{ repeat: isPlaying ? Infinity : 0, duration: 1 }}
                >
                  {isPlaying ? (
                    <Volume2 className="h-20 w-20 mx-auto text-green-500 mb-6" />
                  ) : (
                    <VolumeX className="h-20 w-20 mx-auto text-muted-foreground mb-6" />
                  )}
                </motion.div>
                
                <p className="text-xl mb-6">
                  {isPlaying ? 'Listen carefully...' : 'Press play to hear the sentence'}
                </p>

                <div className="flex justify-center gap-4">
                  <Button variant="outline" size="lg" onClick={handleReplay}>
                    <RotateCcw className="h-4 w-4 mr-2" />
                    Replay
                  </Button>
                  <Button 
                    size="lg" 
                    onClick={() => {
                      stopPlayback()
                      setPhase('typing')
                    }}
                  >
                    Ready to Type
                    <ChevronRight className="h-4 w-4 ml-2" />
                  </Button>
                </div>
              </CardContent>
            </Card>
          </motion.div>
        )}

        {/* Typing Phase */}
        {phase === 'typing' && currentSegment && (
          <motion.div
            key="typing"
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            exit={{ opacity: 0, y: -20 }}
          >
            <Card>
              <CardHeader>
                <div className="flex items-center justify-between">
                  <CardTitle className="text-base">
                    Type what you heard
                  </CardTitle>
                  <div className="flex gap-2">
                    <Button variant="ghost" size="sm" onClick={handleReplay}>
                      <Volume2 className="h-4 w-4 mr-1" />
                      Replay
                    </Button>
                  </div>
                </div>
              </CardHeader>
              <CardContent className="space-y-6">
                <div className="bg-muted rounded-lg p-4">
                  <p className="text-sm text-muted-foreground mb-1">
                    Segment {currentSegmentIndex + 1} • {currentSegment.word_count} words
                  </p>
                </div>

                <textarea
                  value={typedText}
                  onChange={(e) => setTypedText(e.target.value)}
                  placeholder="Type exactly what you heard..."
                  className="w-full min-h-[150px] p-4 rounded-lg border bg-background resize-none focus:outline-none focus:ring-2 focus:ring-primary"
                  autoFocus
                />

                <div className="flex justify-between items-center">
                  <Button variant="ghost" onClick={handlePrevious} disabled={currentSegmentIndex === 0}>
                    <ChevronLeft className="h-4 w-4 mr-1" />
                    Previous
                  </Button>
                  
                  <Button 
                    onClick={handleSubmit} 
                    disabled={!typedText.trim() || loading}
                  >
                    {loading ? (
                      <>
                        <Loader2 className="h-4 w-4 mr-2 animate-spin" />
                        Checking...
                      </>
                    ) : (
                      <>
                        Check Answer
                        <Send className="h-4 w-4 ml-2" />
                      </>
                    )}
                  </Button>
                </div>
              </CardContent>
            </Card>
          </motion.div>
        )}

        {/* Result Phase */}
        {phase === 'result' && scoreResult && currentSegment && (
          <motion.div
            key="result"
            initial={{ opacity: 0, scale: 0.95 }}
            animate={{ opacity: 1, scale: 1 }}
            exit={{ opacity: 0, scale: 0.95 }}
          >
            <Card>
              <CardHeader>
                <div className="flex items-center justify-between">
                  <CardTitle className="text-base flex items-center gap-2">
                    {scoreResult.accuracy >= 0.8 ? (
                      <Check className="h-5 w-5 text-green-500" />
                    ) : (
                      <AlertTriangle className="h-5 w-5 text-yellow-500" />
                    )}
                    Result: {Math.round(scoreResult.accuracy * 100)}% accuracy
                  </CardTitle>
                  <Badge variant={scoreResult.accuracy >= 0.8 ? 'success' : 'secondary'}>
                    {scoreResult.correct_words}/{scoreResult.total_words} words
                  </Badge>
                </div>
              </CardHeader>
              <CardContent className="space-y-6">
                {/* Word-by-word diff */}
                <div className="space-y-2">
                  <p className="text-sm font-medium">Word-by-word comparison:</p>
                  <div className="flex flex-wrap gap-2">
                    {scoreResult.word_diffs.map((diff, i) => (
                      <WordDiffBadge key={i} diff={diff} />
                    ))}
                  </div>
                </div>

                {/* Phonetic confusions */}
                {scoreResult.phonetic_confusions.length > 0 && (
                  <div className="p-4 rounded-lg bg-yellow-500/10 border border-yellow-200">
                    <p className="text-sm font-medium mb-2">
                      🎧 Phonetic confusions detected:
                    </p>
                    {scoreResult.phonetic_confusions.map((conf, i) => (
                      <p key={i} className="text-sm text-muted-foreground">
                        You typed <strong>{conf.typed}</strong> instead of <strong>{conf.expected}</strong>
                      </p>
                    ))}
                  </div>
                )}

                {/* Correct answer */}
                <div className="p-4 rounded-lg bg-muted">
                  <p className="text-sm text-muted-foreground mb-1">Correct text:</p>
                  <p className="font-medium">{currentSegment.text}</p>
                </div>

                {/* Navigation */}
                <div className="flex justify-between items-center pt-4">
                  <Button variant="ghost" onClick={handleReplay}>
                    <RotateCcw className="h-4 w-4 mr-2" />
                    Try Again
                  </Button>
                  
                  <Button onClick={handleNext}>
                    {currentSegmentIndex < (content?.total_segments || 0) - 1 ? (
                      <>
                        Next Segment
                        <ChevronRight className="h-4 w-4 ml-2" />
                      </>
                    ) : (
                      <>
                        Finish
                        <Check className="h-4 w-4 ml-2" />
                      </>
                    )}
                  </Button>
                </div>
              </CardContent>
            </Card>
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  )
}

// Word diff badge component
function WordDiffBadge({ diff }: { diff: WordDiff }) {
  const bgColors = {
    correct: 'bg-green-500/10 text-green-700 border-green-200',
    missing: 'bg-red-500/10 text-red-700 border-red-200',
    extra: 'bg-gray-500/10 text-gray-700 border-gray-200',
    substituted: diff.is_phonetic_confusion
      ? 'bg-yellow-500/10 text-yellow-700 border-yellow-200'
      : 'bg-orange-500/10 text-orange-700 border-orange-200',
  }

  return (
    <Badge
      variant="outline"
      className={cn('text-xs', bgColors[diff.status])}
      title={diff.status === 'substituted' ? `Expected: ${diff.expected}` : undefined}
    >
      {diff.status === 'missing' && <X className="h-3 w-3 mr-1" />}
      {diff.status === 'substituted' ? diff.user_input : diff.word}
      {diff.status === 'substituted' && diff.is_phonetic_confusion && ' 🎧'}
    </Badge>
  )
}
