/**
 * RegressionDetector — detects backward saccades (re-reading behavior).
 *
 * A regression occurs when gaze moves backward (right-to-left in LTR text)
 * between fixations. This is a key indicator of comprehension difficulty.
 *
 * Design:
 *   - Analyzes sequential fixation pairs
 *   - Configurable direction (LTR/RTL reading)
 *   - Minimum distance threshold (filters micro-regressions)
 *   - Emits Regression events with from/to AOI context
 */

import { Emitter } from '../core/Emitter'
import type { Fixation, ILifecycle, Regression } from '../types'

export interface RegressionDetectorConfig {
  /** Reading direction: 'ltr' or 'rtl' */
  readingDirection: 'ltr' | 'rtl'
  /** Minimum horizontal distance (px) to count as regression */
  minDistancePx: number
  /** Minimum vertical tolerance (px) — regressions on same line */
  lineTolerancePx: number
}

const DEFAULT_CONFIG: RegressionDetectorConfig = {
  readingDirection: 'ltr',
  minDistancePx: 50,
  lineTolerancePx: 40,
}

export interface RegressionEventMap {
  regression: Regression
}

export class RegressionDetector extends Emitter<RegressionEventMap> implements ILifecycle {
  private config: RegressionDetectorConfig
  private lastFixation: Fixation | null = null
  private idCounter = 0
  private _active = false

  constructor(config: Partial<RegressionDetectorConfig> = {}) {
    super()
    this.config = { ...DEFAULT_CONFIG, ...config }
  }

  // ─────────────────────────────────────────────
  //  Public API
  // ─────────────────────────────────────────────

  get active(): boolean {
    return this._active
  }

  start(): void {
    this._active = true
    this.lastFixation = null
  }

  stop(): void {
    this._active = false
    this.lastFixation = null
  }

  destroy(): void {
    this.stop()
    this.removeAllListeners()
  }

  configure(config: Partial<RegressionDetectorConfig>): void {
    this.config = { ...this.config, ...config }
  }

  /**
   * Feed a completed fixation. Compares to previous to detect regressions.
   */
  addFixation(fixation: Fixation): void {
    if (!this._active) return

    if (this.lastFixation) {
      const regression = this.detect(this.lastFixation, fixation)
      if (regression) {
        this.emit('regression', regression)
      }
    }

    this.lastFixation = fixation
  }

  // ─────────────────────────────────────────────
  //  Private
  // ─────────────────────────────────────────────

  private detect(prev: Fixation, curr: Fixation): Regression | null {
    const dx = curr.x - prev.x
    const dy = curr.y - prev.y

    // Check if on approximately the same line (within tolerance)
    const sameLine = Math.abs(dy) <= this.config.lineTolerancePx

    // Check if movement is backward relative to reading direction
    const isBackward = this.config.readingDirection === 'ltr' ? dx < 0 : dx > 0
    const distance = Math.abs(dx)

    // Also detect cross-line regressions (jumping back up)
    const isUpwardJump = dy < -this.config.lineTolerancePx

    const isRegression = (sameLine && isBackward && distance >= this.config.minDistancePx) || isUpwardJump

    if (!isRegression) return null

    return {
      id: `reg_${++this.idCounter}_${Date.now()}`,
      fromX: prev.x,
      fromY: prev.y,
      toX: curr.x,
      toY: curr.y,
      timestamp: curr.startTime,
      distance: Math.hypot(dx, dy),
      fromAoiId: prev.aoiId,
      toAoiId: curr.aoiId,
      fromParagraphId: prev.paragraphId,
      toParagraphId: curr.paragraphId,
    }
  }
}
