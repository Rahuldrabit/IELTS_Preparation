/**
 * ScrollTracker — tracks scroll direction, velocity, and visible paragraphs.
 *
 * Design:
 *   - Throttled scroll events (passive listener)
 *   - Computes velocity (px/s) from delta between events
 *   - Detects which paragraphs are in viewport via IntersectionObserver
 *   - Emits paragraph enter/exit with dwell timing
 *   - Target can be window or a specific scrollable container
 */

import { Emitter } from '../core/Emitter'
import type { ITracker, ScrollEventMap, ScrollEventData } from '../types'

export interface ScrollTrackerConfig {
  /** Throttle interval for scroll events (ms) */
  throttleMs: number
  /** CSS selector for paragraph elements to observe */
  paragraphSelector: string
  /** Scroll container (default: window/document) */
  container?: HTMLElement
  /** IntersectionObserver threshold */
  intersectionThreshold: number
}

const DEFAULT_CONFIG: ScrollTrackerConfig = {
  throttleMs: 100,
  paragraphSelector: '[data-cte-paragraph]',
  intersectionThreshold: 0.5,
}

export class ScrollTracker extends Emitter<ScrollEventMap> implements ITracker {
  private config: ScrollTrackerConfig
  private _active = false
  private lastScrollTop = 0
  private lastScrollTime = 0
  private lastEmit = 0
  private visibleParagraphs = new Set<string>()
  private paragraphEntryTimes = new Map<string, number>()
  private scrollHandler: (() => void) | null = null
  private intersectionObserver: IntersectionObserver | null = null

  constructor(config: Partial<ScrollTrackerConfig> = {}) {
    super()
    this.config = { ...DEFAULT_CONFIG, ...config }
  }

  // ─────────────────────────────────────────────
  //  Public API
  // ─────────────────────────────────────────────

  get active(): boolean {
    return this._active
  }

  /** Get currently visible paragraph IDs */
  getVisibleParagraphs(): string[] {
    return Array.from(this.visibleParagraphs)
  }

  start(): void {
    if (this._active) return
    this._active = true

    const scrollTarget = this.config.container ?? window
    this.lastScrollTop = this.getScrollTop()
    this.lastScrollTime = performance.now()

    this.scrollHandler = this.onScroll.bind(this)
    scrollTarget.addEventListener('scroll', this.scrollHandler, { passive: true })

    this.setupIntersectionObserver()
  }

  stop(): void {
    if (!this._active) return
    this._active = false

    const scrollTarget = this.config.container ?? window
    if (this.scrollHandler) {
      scrollTarget.removeEventListener('scroll', this.scrollHandler)
      this.scrollHandler = null
    }

    this.intersectionObserver?.disconnect()
    this.intersectionObserver = null
    this.visibleParagraphs.clear()
    this.paragraphEntryTimes.clear()
  }

  destroy(): void {
    this.stop()
    this.removeAllListeners()
  }

  configure(config: Partial<ScrollTrackerConfig>): void {
    const wasActive = this._active
    if (wasActive) this.stop()
    this.config = { ...this.config, ...config }
    if (wasActive) this.start()
  }

  // ─────────────────────────────────────────────
  //  Private — Scroll Handler
  // ─────────────────────────────────────────────

  private onScroll(): void {
    const now = performance.now()
    if (now - this.lastEmit < this.config.throttleMs) return
    this.lastEmit = now

    const scrollTop = this.getScrollTop()
    const dt = now - this.lastScrollTime
    const dy = scrollTop - this.lastScrollTop

    const velocity = dt > 0 ? Math.abs(dy) / (dt / 1000) : 0
    const direction: 'up' | 'down' = dy >= 0 ? 'down' : 'up'

    const event: ScrollEventData = {
      scrollTop,
      scrollLeft: this.getScrollLeft(),
      timestamp: now,
      direction,
      velocity,
      visibleParagraphs: Array.from(this.visibleParagraphs),
    }

    this.emit('scroll', event)

    this.lastScrollTop = scrollTop
    this.lastScrollTime = now
  }

  // ─────────────────────────────────────────────
  //  Private — Intersection Observer (paragraph visibility)
  // ─────────────────────────────────────────────

  private setupIntersectionObserver(): void {
    const root = this.config.container ?? null

    this.intersectionObserver = new IntersectionObserver(
      (entries) => {
        const now = performance.now()

        for (const entry of entries) {
          const el = entry.target as HTMLElement
          const paragraphId = el.dataset.cteParagraph
          if (!paragraphId) continue

          if (entry.isIntersecting) {
            if (!this.visibleParagraphs.has(paragraphId)) {
              this.visibleParagraphs.add(paragraphId)
              this.paragraphEntryTimes.set(paragraphId, now)
              this.emit('paragraphEnter', { paragraphId, timestamp: now })
            }
          } else {
            if (this.visibleParagraphs.has(paragraphId)) {
              this.visibleParagraphs.delete(paragraphId)
              const entryTime = this.paragraphEntryTimes.get(paragraphId) ?? now
              const dwellMs = now - entryTime
              this.paragraphEntryTimes.delete(paragraphId)
              this.emit('paragraphExit', { paragraphId, timestamp: now, dwellMs })
            }
          }
        }
      },
      { root, threshold: this.config.intersectionThreshold }
    )

    // Observe all paragraph elements
    document.querySelectorAll<HTMLElement>(this.config.paragraphSelector).forEach((el) => {
      this.intersectionObserver!.observe(el)
    })
  }

  // ─────────────────────────────────────────────
  //  Private — Helpers
  // ─────────────────────────────────────────────

  private getScrollTop(): number {
    if (this.config.container) return this.config.container.scrollTop
    return window.scrollY ?? document.documentElement.scrollTop ?? 0
  }

  private getScrollLeft(): number {
    if (this.config.container) return this.config.container.scrollLeft
    return window.scrollX ?? document.documentElement.scrollLeft ?? 0
  }
}
