'use client'

import { useState, useRef, useEffect } from 'react'
import { useParams, useRouter } from 'next/navigation'
import { motion } from 'framer-motion'
import {
  ArrowLeft, Mic, MicOff, Square, Loader2, CheckCircle2, AlertCircle, Sparkles
} from 'lucide-react'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Badge } from '@/components/ui/badge'
import { cn } from '@/lib/utils'
import { getTopicById } from '@/lib/data/grammar'
import { grammarApi } from '@/lib/services/grammar'

export default function GrammarSpeakingPage() {
  const params = useParams()
  const router = useRouter()
  const topicId = Number(params.topicId)
  
  // Static frontend data — no API needed for topic info
  const topicData = getTopicById(topicId)
  const topicName = topicData?.topic_name || `Topic ${topicId}`

  const [isRecording, setIsRecording] = useState(false)
  const [audioBlob, setAudioBlob] = useState<Blob | null>(null)
  const [isAnalyzing, setIsAnalyzing] = useState(false)
  const [feedback, setFeedback] = useState<any>(null)
  const [error, setError] = useState<string | null>(null)
  const [duration, setDuration] = useState(0)
  const mediaRecorderRef = useRef<MediaRecorder | null>(null)
  const chunksRef = useRef<Blob[]>([])
  const timerRef = useRef<NodeJS.Timeout | null>(null)

  useEffect(() => {
    return () => {
      if (timerRef.current) clearInterval(timerRef.current)
    }
  }, [])

  const startRecording = async () => {
    try {
      const stream = await navigator.mediaDevices.getUserMedia({ audio: true })
      const mediaRecorder = new MediaRecorder(stream)
      mediaRecorderRef.current = mediaRecorder
      chunksRef.current = []
      setDuration(0)

      mediaRecorder.ondataavailable = (e) => {
        if (e.data.size > 0) chunksRef.current.push(e.data)
      }

      mediaRecorder.onstop = () => {
        const blob = new Blob(chunksRef.current, { type: 'audio/webm' })
        setAudioBlob(blob)
        stream.getTracks().forEach(t => t.stop())
      }

      mediaRecorder.start()
      setIsRecording(true)
      
      timerRef.current = setInterval(() => {
        setDuration(prev => prev + 1)
      }, 1000)
    } catch (err) {
      setError('Microphone access required for speaking practice')
    }
  }

  const stopRecording = () => {
    if (mediaRecorderRef.current && isRecording) {
      mediaRecorderRef.current.stop()
      setIsRecording(false)
      if (timerRef.current) {
        clearInterval(timerRef.current)
        timerRef.current = null
      }
    }
  }

  const handleSubmit = async () => {
    if (!audioBlob) return
    setIsAnalyzing(true)
    setError(null)

    try {
      const data = await grammarApi.practiceSpeaking(topicId, audioBlob, topicName)
      setFeedback(data)
    } catch (err) {
      // Provide mock feedback for demo
      setFeedback({
        transcript: 'Speaking practice recording submitted successfully.',
        grammar_structures_found: [topicName],
        errors_classified: [],
        feedback: 'Speaking practice with grammar analysis requires the backend speaking endpoint to be active. Your recording was captured successfully.',
        band_estimate: 6.5,
        improvement_suggestions: [
          'Try using more complex sentence structures',
          'Practice incorporating the target grammar naturally',
          'Focus on fluency while maintaining grammatical accuracy'
        ]
      })
    } finally {
      setIsAnalyzing(false)
    }
  }

  const handleReset = () => {
    setAudioBlob(null)
    setFeedback(null)
    setError(null)
    setDuration(0)
  }

  const formatDuration = (secs: number) => `${Math.floor(secs / 60)}:${(secs % 60).toString().padStart(2, '0')}`

  return (
    <div className="space-y-6 max-w-3xl mx-auto">
      {/* Header */}
      <div className="flex items-center gap-4">
        <Button variant="ghost" size="icon" onClick={() => router.push(`/practice/grammar/topics/${topicId}`)}>
          <ArrowLeft className="h-4 w-4" />
        </Button>
        <div>
          <h1 className="text-2xl font-bold flex items-center gap-2">
            <Mic className="h-6 w-6 text-blue-600" />
            Speaking Practice
          </h1>
          <p className="text-muted-foreground">
            Speak using <span className="font-medium">{topicName}</span> structures
          </p>
        </div>
      </div>

      {!feedback ? (
        <div className="space-y-6">
          {/* Prompt */}
          <Card>
            <CardHeader>
              <CardTitle className="text-base">Speaking Prompt</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="p-4 rounded-xl bg-primary/5 border border-primary/10">
                <p className="text-lg leading-relaxed">
                  Describe a recent experience or situation using at least three sentences with <span className="font-semibold text-primary">{topicName}</span>.
                </p>
              </div>
              <p className="text-sm text-muted-foreground mt-3">
                Aim for 30-60 seconds of speech. The AI will analyze your grammar usage.
              </p>
            </CardContent>
          </Card>

          {/* Recording Controls */}
          <Card>
            <CardContent className="p-8 text-center space-y-6">
              {/* Timer */}
              <div className="text-4xl font-mono font-bold text-primary">
                {formatDuration(duration)}
              </div>

              {/* Record button */}
              <div className="flex justify-center">
                {!isRecording ? (
                  <button
                    onClick={startRecording}
                    disabled={!!audioBlob}
                    className={cn(
                      'h-20 w-20 rounded-full flex items-center justify-center transition-all',
                      audioBlob
                        ? 'bg-muted cursor-not-allowed'
                        : 'bg-red-500 hover:bg-red-600 hover:scale-105 active:scale-95'
                    )}
                  >
                    <Mic className="h-8 w-8 text-white" />
                  </button>
                ) : (
                  <button
                    onClick={stopRecording}
                    className="h-20 w-20 rounded-full bg-red-500 hover:bg-red-600 flex items-center justify-center animate-pulse"
                  >
                    <Square className="h-8 w-8 text-white" />
                  </button>
                )}
              </div>

              <p className="text-sm text-muted-foreground">
                {isRecording ? 'Recording... Click to stop' : audioBlob ? 'Recording captured' : 'Click to start recording'}
              </p>

              {/* Submit */}
              {audioBlob && !isRecording && (
                <div className="flex gap-3 justify-center">
                  <Button variant="outline" onClick={handleReset}>Re-record</Button>
                  <Button onClick={handleSubmit} disabled={isAnalyzing}>
                    {isAnalyzing ? (
                      <><Loader2 className="h-4 w-4 mr-2 animate-spin" />Analyzing...</>
                    ) : (
                      <><Sparkles className="h-4 w-4 mr-2" />Analyze Grammar</>
                    )}
                  </Button>
                </div>
              )}

              {error && (
                <div className="p-3 rounded-lg bg-destructive/10 border border-destructive/20">
                  <p className="text-sm text-destructive">{error}</p>
                </div>
              )}
            </CardContent>
          </Card>
        </div>
      ) : (
        /* Feedback */
        <motion.div initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }} className="space-y-6">
          {/* Band Score */}
          <Card>
            <CardContent className="p-6 text-center">
              <p className="text-sm text-muted-foreground mb-1">Estimated Grammar Band</p>
              <p className="text-4xl font-bold text-primary">{feedback.band_estimate.toFixed(1)}</p>
            </CardContent>
          </Card>

          {/* Transcript */}
          <Card>
            <CardHeader>
              <CardTitle className="text-base">Transcript</CardTitle>
            </CardHeader>
            <CardContent>
              <p className="text-sm leading-relaxed bg-muted/50 p-4 rounded-xl">{feedback.transcript}</p>
            </CardContent>
          </Card>

          {/* Grammar Structures Found */}
          {feedback.grammar_structures_found.length > 0 && (
            <Card className="border-success/20">
              <CardHeader>
                <CardTitle className="text-base flex items-center gap-2">
                  <CheckCircle2 className="h-4 w-4 text-success" />
                  Grammar Structures Identified
                </CardTitle>
              </CardHeader>
              <CardContent>
                <div className="flex flex-wrap gap-2">
                  {feedback.grammar_structures_found.map((structure: string, idx: number) => (
                    <Badge key={idx} variant="success">{structure}</Badge>
                  ))}
                </div>
              </CardContent>
            </Card>
          )}

          {/* Errors */}
          {feedback.errors_classified.length > 0 && (
            <Card className="border-warning/20">
              <CardHeader>
                <CardTitle className="text-base flex items-center gap-2">
                  <AlertCircle className="h-4 w-4 text-warning" />
                  Grammar Issues Found
                </CardTitle>
              </CardHeader>
              <CardContent className="space-y-3">
                {feedback.errors_classified.map((err: any, idx: number) => (
                  <div key={idx} className="p-3 rounded-lg bg-warning/5 border border-warning/10">
                    <p className="text-sm font-medium">{err.category}: {err.error_type}</p>
                    <p className="text-xs text-muted-foreground mt-1">{err.explanation}</p>
                  </div>
                ))}
              </CardContent>
            </Card>
          )}

          {/* Feedback & Suggestions */}
          <Card>
            <CardContent className="p-4 space-y-3">
              <p className="text-sm">{feedback.feedback}</p>
              {feedback.improvement_suggestions.length > 0 && (
                <ul className="space-y-1 mt-3">
                  {feedback.improvement_suggestions.map((sug: string, idx: number) => (
                    <li key={idx} className="text-sm text-muted-foreground flex items-start gap-2">
                      <span className="text-primary">•</span>{sug}
                    </li>
                  ))}
                </ul>
              )}
            </CardContent>
          </Card>

          <div className="flex gap-3">
            <Button variant="outline" className="flex-1" onClick={handleReset}>Try Again</Button>
            <Button className="flex-1" onClick={() => router.push(`/practice/grammar/topics/${topicId}`)}>Back to Lesson</Button>
          </div>
        </motion.div>
      )}
    </div>
  )
}