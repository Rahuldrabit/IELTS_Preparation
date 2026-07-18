/**
 * FocusTracker — tracks tab visibility and window focus state.
 *
 * Important for telemetry accuracy: if user switches tabs or loses focus,
 * gaze data is invalid and should be marked/discarded.
 *
 * Design:
 *   - Uses Page Visibility API (document.hidden / visibilitychange)
 *   - Also tracks window blur/focus events
 *   - Emits single FocusEventData with reason
 *   - Computable: total time focused vs unfocused
 */

import { Emitter } from '../core/Emitter'
import type { FocusEventMap, ITracker } from '../types'

export class FocusTracker extends Emitter<FocusEventMap> implements ITracker {
  private _active = false
  private _focused = true
  private boundVisibility: (() => void) | null = null
  private boundBlur: (() => void) | null = null
  private boundFocus: (() => void) | null = null

  // Metrics
  private focusStartTime = 0
  private totalFocusedMs = 0
  private totalUnfocusedMs = 0

  // ─────────────────────────────────────────────
  //  Public API
  // ─────────────────────────────────────────────

  get active(): boolean {
    return this._active
  }

  get focused(): boolean {
    return this._focused
  }

  /** Total time user was focused (ms) since start */
  get totalFocused(): number {
    if (this._focused) {
      return this.totalFocusedMs + (performance.now() - this.focusStartTime)
    }
    return this.totalFocusedMs
  }

  /** Total time user was unfocused (ms) since start */
  get totalUnfocused(): number {
    if (!this._focused) {
      return this.totalUnfocusedMs + (performance.now() - this.focusStartTime)
    }
    return this.totalUnfocusedMs
  }

  /** Focus ratio (0-1) */
  get focusRatio(): number {
    const total = this.totalFocused + this.totalUnfocused
    return total > 0 ? this.totalFocused / total : 1
  }

  start(): void {
    if (this._active) return
    this._active = true
    this._focused = !document.hidden
    this.focusStartTime = performance.now()
    this.totalFocusedMs = 0
    this.totalUnfocusedMs = 0

    this.boundVisibility = this.onVisibilityChange.bind(this)
    this.boundBlur = this.onBlur.bind(this)
    this.boundFocus = this.onFocus.bind(this)

    document.addEventListener('visibilitychange', this.boundVisibility)
    window.addEventListener('blur', this.boundBlur)
    window.addEventListener('focus', this.boundFocus)
  }

  stop(): void {
    if (!this._active) return
    this._active = false

    // Accumulate final interval
    this.accumulateTime()

    if (this.boundVisibility) document.removeEventListener('visibilitychange', this.boundVisibility)
    if (this.boundBlur) window.removeEventListener('blur', this.boundBlur)
    if (this.boundFocus) window.removeEventListener('focus', this.boundFocus)

    this.boundVisibility = null
    this.boundBlur = null
    this.boundFocus = null
  }

  destroy(): void {
    this.stop()
    this.removeAllListeners()
  }

  // ─────────────────────────────────────────────
  //  Private
  // ─────────────────────────────────────────────

  private onVisibilityChange(): void {
    const focused = !document.hidden
    this.transition(focused, 'visibility')
  }

  private onBlur(): void {
    this.transition(false, 'blur')
  }

  private onFocus(): void {
    this.transition(true, 'focus')
  }

  private transition(focused: boolean, reason: 'visibility' | 'blur' | 'focus'): void {
    if (focused === this._focused) return

    this.accumulateTime()
    this._focused = focused
    this.focusStartTime = performance.now()

    this.emit('change', { focused, timestamp: performance.now(), reason })
  }

  private accumulateTime(): void {
    const elapsed = performance.now() - this.focusStartTime
    if (this._focused) {
      this.totalFocusedMs += elapsed
    } else {
      this.totalUnfocusedMs += elapsed
    }
  }
}
