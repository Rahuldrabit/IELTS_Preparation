/**
 * FixationDetector — I-DT (dispersion-threshold identification) algorithm.
 *
 * Standard eye-tracking algorithm:
 *   1. Maintain a sliding window of gaze points
 *   2. If window duration >= minDuration AND dispersion <= maxDispersion → fixation
 *   3. Expand fixation window until dispersion exceeds threshold
 *   4. Emit fixation with centroid, duration, AOI mapping
 *
 * Design:
 *   - Configurable thresholds (adapt to calibration accuracy)
 *   - Emits fixationStart/fixationEnd on Emitter
 *   - Generates unique IDs for correlation
 *   - AOI lookup delegated to injectable mapper
 */

import { Emitter } from '../core/Emitter'
import type { Fixation, GazePoint, ILifecycle } from '../types'

export interface FixationDetectorConfig {
  /** Minimum fixation duration in ms */
  minDurationMs: number
  /** Maximum dispersion in pixels (manhattan: dx + dy) */
  maxDispersionPx: number
}

const DEFAULT_CONFIG: FixationDetectorConfig = {
  minDurationMs: 150,
  maxDispersionPx: 30,
}

export interface FixationEventMap {
  fixationStart: Fixation
  fixationEnd: Fixation
}

/** Optional AOI resolver injected for hit-testing */
export interface IAOIResolver {
  resolve(x: number, y: number): { aoiId: string | null; wordIndex: number | null; paragraphId: string | null }
}

export class FixationDetector extends Emitter<FixationEventMap> implements ILifecycle {
  private config: FixationDetectorConfig
  private window: GazePoint[] = []
  private currentFixation: Fixation | null = null
  private aoiResolver: IAOIResolver | null = null
  private idCounter = 0
  private _active = false

  constructor(config: Partial<FixationDetectorConfig> = {}, aoiResolver?: IAOIResolver) {
    super()
    this.config = { ...DEFAULT_CONFIG, ...config }
    this.aoiResolver = aoiResolver ?? null
  }

  // ─────────────────────────────────────────────
  //  Public API
  // ─────────────────────────────────────────────

  get active(): boolean {
    return this._active
  }

  start(): void {
    this._active = true
    this.window = []
    this.currentFixation = null
  }

  stop(): void {
    // Finalize any in-progress fixation
    if (this.currentFixation) {
      this.endFixation()
    }
    this._active = false
  }

  destroy(): void {
    this.stop()
    this.removeAllListeners()
  }

  /** Inject or replace AOI resolver at runtime */
  setAOIResolver(resolver: IAOIResolver): void {
    this.aoiResolver = resolver
  }

  configure(config: Partial<FixationDetectorConfig>): void {
    this.config = { ...this.config, ...config }
  }

  /**
   * Feed a new gaze point into the detector.
   * Call this for every valid gaze point from GazeEstimator.
   */
  addPoint(point: GazePoint): void {
    if (!this._active) return

    this.window.push(point)

    // Ensure window has at least 2 points
    if (this.window.length < 2) return

    const dispersion = this.computeDispersion()
    const duration = this.windowDuration()

    if (dispersion <= this.config.maxDispersionPx) {
      // Points are clustered — potential fixation
      if (duration >= this.config.minDurationMs && !this.currentFixation) {
        this.startFixation()
      }
      // If already in fixation, it just grows (window keeps expanding)
    } else {
      // Dispersion exceeded — end fixation if active
      if (this.currentFixation) {
        this.endFixation()
      }
      // Remove oldest point and retry
      this.window.shift()
    }
  }

  // ─────────────────────────────────────────────
  //  Private — Fixation Lifecycle
  // ─────────────────────────────────────────────

  private startFixation(): void {
    const centroid = this.centroid()
    const aoi = this.aoiResolver?.resolve(centroid.x, centroid.y)

    this.currentFixation = {
      id: this.nextId(),
      x: centroid.x,
      y: centroid.y,
      startTime: this.window[0].timestamp,
      endTime: this.window[this.window.length - 1].timestamp,
      duration: this.windowDuration(),
      aoiId: aoi?.aoiId ?? null,
      wordIndex: aoi?.wordIndex ?? null,
      paragraphId: aoi?.paragraphId ?? null,
    }

    this.emit('fixationStart', this.currentFixation)
  }

  private endFixation(): void {
    if (!this.currentFixation) return

    const centroid = this.centroid()
    const aoi = this.aoiResolver?.resolve(centroid.x, centroid.y)

    this.currentFixation = {
      ...this.currentFixation,
      x: centroid.x,
      y: centroid.y,
      endTime: this.window[this.window.length - 1]?.timestamp ?? this.currentFixation.endTime,
      duration: (this.window[this.window.length - 1]?.timestamp ?? this.currentFixation.endTime) - this.currentFixation.startTime,
      aoiId: aoi?.aoiId ?? this.currentFixation.aoiId,
      wordIndex: aoi?.wordIndex ?? this.currentFixation.wordIndex,
      paragraphId: aoi?.paragraphId ?? this.currentFixation.paragraphId,
    }

    this.emit('fixationEnd', this.currentFixation)
    this.currentFixation = null
    this.window = []
  }

  // ─────────────────────────────────────────────
  //  Private — Math
  // ─────────────────────────────────────────────

  /** Manhattan dispersion: (maxX - minX) + (maxY - minY) */
  private computeDispersion(): number {
    let minX = Infinity, maxX = -Infinity
    let minY = Infinity, maxY = -Infinity

    for (const p of this.window) {
      if (p.x < minX) minX = p.x
      if (p.x > maxX) maxX = p.x
      if (p.y < minY) minY = p.y
      if (p.y > maxY) maxY = p.y
    }

    return (maxX - minX) + (maxY - minY)
  }

  private windowDuration(): number {
    if (this.window.length < 2) return 0
    return this.window[this.window.length - 1].timestamp - this.window[0].timestamp
  }

  private centroid(): { x: number; y: number } {
    const n = this.window.length
    if (n === 0) return { x: 0, y: 0 }
    let sx = 0, sy = 0
    for (const p of this.window) { sx += p.x; sy += p.y }
    return { x: sx / n, y: sy / n }
  }

  private nextId(): string {
    return `fix_${++this.idCounter}_${Date.now()}`
  }
}
