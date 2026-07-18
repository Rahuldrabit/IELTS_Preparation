/**
 * ReadingAnalytics — aggregates raw telemetry events into per-interval summaries.
 *
 * Instead of uploading thousands of raw gaze points, this module produces
 * a compact ReadingAnalyticsSummary every N seconds.
 *
 * Design:
 *   - Accumulator pattern: consumes events, produces summaries on flush
 *   - Stateless between flush cycles (no leaking state)
 *   - Configurable aggregation interval
 *   - Reusable: accepts events via public methods (decoupled from ReadingTracker)
 */

import { Emitter } from '../core/Emitter'
import type { Fixation, ReadingAnalyticsSummary, Regression, TelemetryEvent } from '../types'

export interface ReadingAnalyticsConfig {
  /** How often to produce a summary (ms) */
  intervalMs: number
  /** Assumed average word width in pixels (for reading speed estimate) */
  avgWordWidthPx: number
}

const DEFAULT_CONFIG: ReadingAnalyticsConfig = {
  intervalMs: 1000,
  avgWordWidthPx: 60,
}

export interface ReadingAnalyticsEventMap {
  summary: ReadingAnalyticsSummary
}

export class ReadingAnalytics extends Emitter<ReadingAnalyticsEventMap> {
  private config: ReadingAnalyticsConfig
  private sessionId: string
  private intervalId: ReturnType<typeof setInterval> | null = null

  // Accumulators (reset each flush)
  private fixations: Fixation[] = []
  private regressions: Regression[] = []
  private paragraphTimeAccum = new Map<string, number>()
  private blinkCount = 0
  private totalWordsVisited = new Set<number>()
  private totalWordsInPassage = 0
  private startTime = 0

  constructor(sessionId: string, config: Partial<ReadingAnalyticsConfig> = {}) {
    super()
    this.sessionId = sessionId
    this.config = { ...DEFAULT_CONFIG, ...config }
  }

  // ─────────────────────────────────────────────
  //  Public API
  // ─────────────────────────────────────────────

  /** Set total word count of the passage (for skip rate calculation) */
  setTotalWords(count: number): void {
    this.totalWordsInPassage = count
  }

  /** Start periodic summary emission */
  start(): void {
    this.startTime = performance.now()
    this.intervalId = setInterval(() => this.flush(), this.config.intervalMs)
  }

  /** Stop and emit final summary */
  stop(): void {
    if (this.intervalId) {
      clearInterval(this.intervalId)
      this.intervalId = null
    }
    this.flush()
  }

  destroy(): void {
    this.stop()
    this.removeAllListeners()
  }

  // ── Event Ingestors ───────────────────────────

  /** Record a completed fixation */
  addFixation(fixation: Fixation): void {
    this.fixations.push(fixation)
    if (fixation.wordIndex !== null) {
      this.totalWordsVisited.add(fixation.wordIndex)
    }
  }

  /** Record a regression */
  addRegression(regression: Regression): void {
    this.regressions.push(regression)
  }

  /** Record time spent viewing a paragraph */
  addParagraphTime(paragraphId: string, durationMs: number): void {
    const current = this.paragraphTimeAccum.get(paragraphId) ?? 0
    this.paragraphTimeAccum.set(paragraphId, current + durationMs)
  }

  /** Record a blink */
  addBlink(): void {
    this.blinkCount++
  }

  /** Ingest a generic TelemetryEvent (delegates to appropriate accumulator) */
  ingest(event: TelemetryEvent): void {
    switch (event.type) {
      case 'fixation':
        this.addFixation(event.data as unknown as Fixation)
        break
      case 'regression':
        this.addRegression(event.data as unknown as Regression)
        break
      case 'blink':
        this.addBlink()
        break
      case 'paragraph_exit':
        if (event.data.paragraphId && event.data.dwellMs) {
          this.addParagraphTime(
            event.data.paragraphId as string,
            event.data.dwellMs as number,
          )
        }
        break
    }
  }

  // ─────────────────────────────────────────────
  //  Private — Aggregation
  // ─────────────────────────────────────────────

  private flush(): void {
    const now = performance.now()
    const elapsedSec = (now - this.startTime) / 1000

    const summary: ReadingAnalyticsSummary = {
      sessionId: this.sessionId,
      paragraphTime: Object.fromEntries(this.paragraphTimeAccum),
      fixationCount: this.fixations.length,
      regressionCount: this.regressions.length,
      skipRate: this.computeSkipRate(),
      blinkRate: elapsedSec > 0 ? (this.blinkCount / elapsedSec) * 60 : 0, // blinks/min
      focusScore: 0, // Filled by AttentionScore externally
      avgFixationDuration: this.computeAvgFixationDuration(),
      readingSpeedWpm: this.computeReadingSpeed(),
      timestamp: now,
    }

    this.emit('summary', summary)
    this.resetAccumulators()
  }

  private computeSkipRate(): number {
    if (this.totalWordsInPassage <= 0) return 0
    const visited = this.totalWordsVisited.size
    return Math.max(0, 1 - visited / this.totalWordsInPassage)
  }

  private computeAvgFixationDuration(): number {
    if (this.fixations.length === 0) return 0
    const total = this.fixations.reduce((sum, f) => sum + f.duration, 0)
    return total / this.fixations.length
  }

  private computeReadingSpeed(): number {
    // Estimate: total horizontal distance traveled by fixations / avgWordWidth → words
    // Time: sum of fixation durations
    if (this.fixations.length < 2) return 0

    let totalForwardPx = 0
    let totalTimeMs = 0

    for (let i = 1; i < this.fixations.length; i++) {
      const dx = this.fixations[i].x - this.fixations[i - 1].x
      if (dx > 0) totalForwardPx += dx // Only forward movement counts
      totalTimeMs += this.fixations[i].duration
    }

    if (totalTimeMs <= 0) return 0
    const wordsRead = totalForwardPx / this.config.avgWordWidthPx
    const minutes = totalTimeMs / 60000
    return minutes > 0 ? wordsRead / minutes : 0
  }

  private resetAccumulators(): void {
    this.fixations = []
    this.regressions = []
    this.paragraphTimeAccum.clear()
    this.blinkCount = 0
    // Note: totalWordsVisited is NOT reset (cumulative across session)
    this.startTime = performance.now()
  }
}
