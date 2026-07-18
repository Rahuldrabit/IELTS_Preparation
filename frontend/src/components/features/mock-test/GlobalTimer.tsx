'use client'

import { useEffect, useRef, useCallback } from 'react'
import { motion, AnimatePresence } from 'framer-motion'
import { Clock, AlertTriangle } from 'lucide-react'
import { cn } from '@/lib/utils'
import { useMockTestStore, useMockTestTimer } from '@/lib/store/mockTestStore'

interface GlobalTimerProps {
  /** Total time for this section in seconds */
  totalSeconds: number
  /** Called when 5 minutes remain */
  onWarning?: () => void
  /** Called when timer hits 0 (grace period starts) */
  onGracePeriodStart?: () => void
  /** Called when grace period (30s) expires — trigger auto-submit */
  onExpired?: () => void
  /** Pause the timer externally */
  isPaused?: boolean
  /** Section label shown next to timer */
  sectionLabel?: string
}

export function GlobalTimer({
  totalSeconds,
  onWarning,
  onGracePeriodStart,
  onExpired,
  isPaused = false,
  sectionLabel,
}: GlobalTimerProps) {
  const { timer, setTimer, tickTimer } = useMockTestStore()
  const intervalRef = useRef<NodeJS.Timeout | null>(null)
  const warningFiredRef = useRef(false)
  const graceFiredRef = useRef(false)
  const expiredFiredRef = useRef(false)

  // Initialize timer when totalSeconds changes
  useEffect(() => {
    setTimer({
      totalSeconds,
      remainingSeconds: totalSeconds,
      isWarning: false,
      isGracePeriod: false,
      isRunning: true,
    })
    warningFiredRef.current = false
    graceFiredRef.current = false
    expiredFiredRef.current = false

    // Persist start time to localStorage for crash recovery
    localStorage.setItem(
      'mocktest_timer_start',
      JSON.stringify({ totalSeconds, startedAt: Date.now() })
    )

    return () => {
      if (intervalRef.current) clearInterval(intervalRef.current)
    }
  }, [totalSeconds, setTimer])

  // Tick every second
  useEffect(() => {
    if (isPaused) {
      if (intervalRef.current) clearInterval(intervalRef.current)
      return
    }

    intervalRef.current = setInterval(() => {
      tickTimer()
    }, 1000)

    return () => {
      if (intervalRef.current) clearInterval(intervalRef.current)
    }
  }, [isPaused, tickTimer])

  // Fire callbacks on state changes
  useEffect(() => {
    if (timer.isWarning && !warningFiredRef.current) {
      warningFiredRef.current = true
      onWarning?.()
    }
    if (timer.remainingSeconds <= 0 && !graceFiredRef.current) {
      graceFiredRef.current = true
      onGracePeriodStart?.()
    }
    if (timer.remainingSeconds <= -30 && !expiredFiredRef.current) {
      expiredFiredRef.current = true
      onExpired?.()
    }
  }, [timer.remainingSeconds, timer.isWarning, onWarning, onGracePeriodStart, onExpired])

  // Format time display
  const displaySeconds = Math.max(timer.remainingSeconds, 0)
  const hours = Math.floor(displaySeconds / 3600)
  const minutes = Math.floor((displaySeconds % 3600) / 60)
  const seconds = displaySeconds % 60

  const timeString = hours > 0
    ? `${hours}:${minutes.toString().padStart(2, '0')}:${seconds.toString().padStart(2, '0')}`
    : `${minutes.toString().padStart(2, '0')}:${seconds.toString().padStart(2, '0')}`

  // Progress percentage
  const progress = totalSeconds > 0
    ? Math.max(0, (timer.remainingSeconds / totalSeconds) * 100)
    : 0

  // Grace period countdown
  const graceRemaining = timer.isGracePeriod
    ? Math.max(0, 30 + timer.remainingSeconds)
    : 0

  return (
    <div className="relative">
      {/* Main timer bar */}
      <div
        className={cn(
          'flex items-center gap-3 px-4 py-2 rounded-xl border transition-all duration-300',
          timer.isGracePeriod
            ? 'bg-red-500/20 border-red-500/50 animate-pulse'
            : timer.isWarning
              ? 'bg-yellow-500/10 border-yellow-500/30'
              : 'bg-muted/50 border-border'
        )}
      >
        {/* Icon */}
        {timer.isGracePeriod || timer.isWarning ? (
          <AlertTriangle className={cn(
            'h-5 w-5',
            timer.isGracePeriod ? 'text-red-500' : 'text-yellow-500'
          )} />
        ) : (
          <Clock className="h-5 w-5 text-muted-foreground" />
        )}

        {/* Section label */}
        {sectionLabel && (
          <span className="text-sm font-medium text-muted-foreground">
            {sectionLabel}
          </span>
        )}

        {/* Time display */}
        <span
          className={cn(
            'font-mono text-lg font-bold tabular-nums',
            timer.isGracePeriod
              ? 'text-red-500'
              : timer.isWarning
                ? 'text-yellow-500'
                : 'text-foreground'
          )}
        >
          {timer.isGracePeriod ? `+${graceRemaining}s` : timeString}
        </span>

        {/* Progress bar */}
        <div className="flex-1 h-2 bg-muted rounded-full overflow-hidden ml-2">
          <motion.div
            className={cn(
              'h-full rounded-full transition-colors duration-300',
              timer.isGracePeriod
                ? 'bg-red-500'
                : timer.isWarning
                  ? 'bg-yellow-500'
                  : progress > 50
                    ? 'bg-green-500'
                    : 'bg-blue-500'
            )}
            style={{ width: `${progress}%` }}
            transition={{ duration: 0.3 }}
          />
        </div>

        {/* Pause indicator */}
        {isPaused && (
          <span className="text-xs text-muted-foreground ml-2">PAUSED</span>
        )}
      </div>

      {/* Warning overlay */}
      <AnimatePresence>
        {timer.isWarning && !timer.isGracePeriod && (
          <motion.div
            initial={{ opacity: 0, y: -10 }}
            animate={{ opacity: 1, y: 0 }}
            exit={{ opacity: 0, y: -10 }}
            className="absolute top-full left-0 right-0 mt-1 z-10"
          >
            <div className="px-3 py-1.5 rounded-lg bg-yellow-500/10 border border-yellow-500/30 text-sm text-yellow-600 dark:text-yellow-400 text-center">
              5 minutes remaining — finish up your answers
            </div>
          </motion.div>
        )}

        {timer.isGracePeriod && (
          <motion.div
            initial={{ opacity: 0, y: -10 }}
            animate={{ opacity: 1, y: 0 }}
            exit={{ opacity: 0, y: -10 }}
            className="absolute top-full left-0 right-0 mt-1 z-10"
          >
            <div className="px-3 py-1.5 rounded-lg bg-red-500/20 border border-red-500/40 text-sm text-red-600 dark:text-red-400 text-center font-medium">
              Time&apos;s up! {graceRemaining}s grace period — answers will auto-submit
            </div>
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  )
}
