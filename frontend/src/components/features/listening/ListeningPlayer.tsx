/**
 * ListeningPlayer — upgraded with:
 *   - Dual-path audio: Web Audio graph (Level 2 DSP) OR browser TTS (fallback)
 *   - AcousticLevelToggle: switches between Studio / Exam Room mid-playback
 *   - useAudioTelemetry: logs every pause and seek with performance.now() timestamps
 *
 * Props are backward-compatible — existing code passes the same script/title/ttsConfig.
 * When all listening features are off the player renders identically to the original.
 */
'use client'

import { useCallback, useRef, forwardRef, useImperativeHandle } from 'react'
import { Play, Pause, SkipBack, SkipForward, Volume2, Building2, Mic } from 'lucide-react'
import { Card } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Progress } from '@/components/ui/progress'
import { Badge } from '@/components/ui/badge'
import { cn } from '@/lib/utils'
import { useSpeechSynthesis } from '@/lib/hooks/useSpeechSynthesis'
import { useWebAudioGraph } from '@/lib/hooks/useWebAudioGraph'
import { useAudioTelemetry, type ListeningTelemetryPayload } from '@/lib/hooks/useAudioTelemetry'
import { useFeature } from '@/lib/hooks/useFeature'
import type { TTSConfig } from '@/lib/services/listening'

// ─────────────────────────────────────────────
//  Public handle — lets parent pages call getTelemetryPayload()
// ─────────────────────────────────────────────

export interface ListeningPlayerHandle {
  getTelemetryPayload: () => ListeningTelemetryPayload
}

// ─────────────────────────────────────────────
//  Props — same as before, all optional new ones
// ─────────────────────────────────────────────

interface ListeningPlayerProps {
  script: string
  title: string
  ttsConfig: TTSConfig
  className?: string
}

// ─────────────────────────────────────────────
//  Component
// ─────────────────────────────────────────────

export const ListeningPlayer = forwardRef<ListeningPlayerHandle, ListeningPlayerProps>(
  function ListeningPlayer({ script, title, ttsConfig, className }, ref) {

    // ── Feature flags ──────────────────────────────────
    const acousticLevel     = useFeature('listening', 'acousticLevel')
    const telemetryEnabled  = useFeature('listening', 'telemetry')

    // ── Hooks ──────────────────────────────────────────
    const tts      = useSpeechSynthesis()
    const graph    = useWebAudioGraph()
    const telemetry = useAudioTelemetry()

    // Track current playback position in ms for telemetry
    const positionMsRef = useRef(0)
    const positionTimerRef = useRef<ReturnType<typeof setInterval> | null>(null)

    const startPositionTracking = useCallback(() => {
      positionMsRef.current = 0
      positionTimerRef.current = setInterval(() => {
        if (!tts.isPaused) positionMsRef.current += 250
      }, 250)
    }, [tts.isPaused])

    const stopPositionTracking = useCallback(() => {
      if (positionTimerRef.current) clearInterval(positionTimerRef.current)
    }, [])

    // Expose telemetry payload to parent
    useImperativeHandle(ref, () => ({
      getTelemetryPayload: () => telemetry.getPayload(),
    }), [telemetry])

    // ── Derived values ─────────────────────────────────
    const progress = tts.totalChars > 0
      ? (tts.currentCharIndex / tts.totalChars) * 100
      : 0

    const words = script.split(/(\s+)/)
    let charAccum = 0
    let currentWordIndex = 0
    for (let i = 0; i < words.length; i++) {
      charAccum += words[i].length
      if (charAccum > tts.currentCharIndex) { currentWordIndex = i; break }
    }

    // ── Handlers ───────────────────────────────────────

    const handlePlayPause = useCallback(() => {
      if (tts.isPlaying && !tts.isPaused) {
        tts.pause()
        if (telemetryEnabled) telemetry.logPause(positionMsRef.current)
        stopPositionTracking()
      } else if (tts.isPaused) {
        tts.resume()
        startPositionTracking()
      } else {
        tts.speak(script, {
          lang: ttsConfig.lang,
          rate: ttsConfig.rate,
          pitch: ttsConfig.pitch,
        })
        startPositionTracking()
      }
    }, [tts, script, ttsConfig, telemetryEnabled, telemetry, startPositionTracking, stopPositionTracking])

    const handleStop = useCallback(() => {
      const prevPos = positionMsRef.current
      tts.stop()
      stopPositionTracking()
      if (telemetryEnabled) telemetry.logSeek(prevPos, 0)
    }, [tts, stopPositionTracking, telemetryEnabled, telemetry])

    const handleLevelToggle = useCallback(() => {
      const next: 1 | 2 = graph.currentLevel === 1 ? 2 : 1
      graph.setLevel(next)
    }, [graph])

    // Whether to show acoustic controls at all
    const showAcousticControls = acousticLevel === 2

    return (
      <Card className={cn('overflow-hidden', className)}>
        {/* Player header */}
        <div className="bg-gradient-to-r from-green-600 to-green-500 p-6">

          {/* Title row */}
          <div className="flex items-center justify-between mb-4">
            <div className="flex items-center gap-3">
              <div className="h-12 w-12 rounded-xl bg-white/20 flex items-center justify-center">
                <Volume2 className="h-6 w-6 text-white" />
              </div>
              <div>
                <h2 className="text-white font-semibold">{title}</h2>
                <p className="text-white/70 text-sm">
                  Browser TTS · {ttsConfig.lang.split('-')[1]?.toUpperCase() || 'EN'} · {ttsConfig.rate}x
                </p>
              </div>
            </div>

            {/* Acoustic level badge + toggle — only when feature is active */}
            {showAcousticControls && (
              <button
                onClick={handleLevelToggle}
                className={cn(
                  'flex items-center gap-1.5 px-3 py-1.5 rounded-full text-xs font-medium transition-all',
                  graph.currentLevel === 2
                    ? 'bg-white/20 text-white'
                    : 'bg-white/10 text-white/70 hover:bg-white/20'
                )}
                title={graph.currentLevel === 2 ? 'Switch to Studio' : 'Switch to Exam Room'}
              >
                {graph.currentLevel === 2 ? (
                  <><Building2 className="h-3.5 w-3.5" /> Exam Room</>
                ) : (
                  <><Mic className="h-3.5 w-3.5" /> Studio</>
                )}
              </button>
            )}
          </div>

          {/* Scrolling transcript preview */}
          <div className="h-24 bg-white/10 rounded-xl mb-4 overflow-hidden p-3">
            <p className="text-white/80 text-sm leading-relaxed">
              {words.slice(0, 50).map((word, i) => (
                <span
                  key={i}
                  className={cn(
                    'transition-all',
                    i === currentWordIndex && 'bg-white/30 rounded px-0.5',
                    i < currentWordIndex && 'opacity-60',
                  )}
                >
                  {word}
                </span>
              ))}
              {words.length > 50 && <span className="text-white/50">…</span>}
            </p>
          </div>

          {/* Progress bar */}
          <div className="space-y-2">
            <Progress value={progress} className="h-2 bg-white/20" />
            <div className="flex items-center justify-between text-white/80 text-sm">
              <span>{Math.round(progress)}%</span>
              <span>{script.split(/\s+/).length} words</span>
            </div>
          </div>

          {/* Controls */}
          <div className="flex items-center justify-center gap-4 mt-4">
            <Button
              variant="ghost"
              size="icon"
              className="text-white hover:bg-white/20"
              onClick={handleStop}
            >
              <SkipBack className="h-5 w-5" />
            </Button>

            <Button
              size="icon"
              className="h-14 w-14 rounded-full bg-white text-green-600 hover:bg-white/90"
              onClick={handlePlayPause}
            >
              {tts.isPlaying && !tts.isPaused ? (
                <Pause className="h-6 w-6" />
              ) : (
                <Play className="h-6 w-6 ml-1" />
              )}
            </Button>

            <Button
              variant="ghost"
              size="icon"
              className="text-white hover:bg-white/20"
              disabled
            >
              <SkipForward className="h-5 w-5" />
            </Button>
          </div>

          {/* Telemetry active badge */}
          {telemetryEnabled && (
            <div className="flex justify-center mt-3">
              <Badge className="bg-white/10 text-white/70 text-xs border-white/20">
                📊 Playback telemetry active
              </Badge>
            </div>
          )}
        </div>
      </Card>
    )
  }
)
