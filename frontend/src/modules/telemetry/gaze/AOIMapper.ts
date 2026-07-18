/**
 * AOIMapper — maps gaze coordinates to Areas of Interest (DOM elements).
 *
 * Responsibilities:
 *   - Register AOIs from DOM elements via data attributes
 *   - Spatial hit-testing (point-in-rect)
 *   - Auto-refresh on resize/scroll (viewport-relative rects)
 *   - Priority: word > sentence > paragraph > question > option
 *   - Implements IAOIResolver interface for FixationDetector
 *
 * DOM conventions:
 *   [data-cte-paragraph="A"]    → paragraph AOI
 *   [data-cte-word="42"]        → word AOI
 *   [data-cte-question="7"]     → question AOI
 *   [data-cte-option="7-2"]     → option AOI (questionId-optionIdx)
 */

import type { AOI, AOIHit, AOIMeta, AOIType, BoundingBox } from '../types'
import type { IAOIResolver } from './FixationDetector'

export interface AOIMapperConfig {
  /** CSS selector prefix for auto-discovery */
  selectorPrefix: string
  /** Debounce interval (ms) for resize/scroll refresh */
  refreshDebounceMs: number
  /** Padding added around each AOI rect (px) for fuzzy matching */
  hitPaddingPx: number
}

const DEFAULT_CONFIG: AOIMapperConfig = {
  selectorPrefix: '[data-cte-',
  refreshDebounceMs: 200,
  hitPaddingPx: 5,
}

export class AOIMapper implements IAOIResolver {
  private config: AOIMapperConfig
  private aoiMap = new Map<string, AOI>()
  private refreshTimer: ReturnType<typeof setTimeout> | null = null
  private resizeObserver: ResizeObserver | null = null
  private scrollHandler: (() => void) | null = null

  constructor(config: Partial<AOIMapperConfig> = {}) {
    this.config = { ...DEFAULT_CONFIG, ...config }
  }

  // ─────────────────────────────────────────────
  //  Public API
  // ─────────────────────────────────────────────

  /** Begin observing DOM for AOI changes */
  start(): void {
    this.refresh()
    this.observeResize()
    this.observeScroll()
  }

  /** Stop observing and clear all AOIs */
  stop(): void {
    this.aoiMap.clear()
    this.resizeObserver?.disconnect()
    this.resizeObserver = null
    if (this.scrollHandler) {
      window.removeEventListener('scroll', this.scrollHandler, true)
      this.scrollHandler = null
    }
    if (this.refreshTimer) {
      clearTimeout(this.refreshTimer)
      this.refreshTimer = null
    }
  }

  destroy(): void {
    this.stop()
  }

  /** Manually register an AOI (for programmatic use) */
  register(aoi: AOI): void {
    this.aoiMap.set(aoi.id, aoi)
  }

  /** Remove an AOI by ID */
  unregister(id: string): void {
    this.aoiMap.delete(id)
  }

  /** Get all registered AOIs */
  getAll(): AOI[] {
    return Array.from(this.aoiMap.values())
  }

  /** Get AOI by ID */
  get(id: string): AOI | undefined {
    return this.aoiMap.get(id)
  }

  /** Force refresh all AOI bounding boxes from DOM */
  refresh(): void {
    this.aoiMap.clear()
    this.scanDOM()
  }

  /**
   * Hit-test: find all AOIs containing the given point.
   * Returns sorted by priority (word > paragraph > question).
   */
  hitTest(x: number, y: number): AOIHit[] {
    const hits: AOIHit[] = []

    for (const aoi of this.aoiMap.values()) {
      const rect = aoi.rect
      const pad = this.config.hitPaddingPx

      if (
        x >= rect.x - pad &&
        x <= rect.x + rect.width + pad &&
        y >= rect.y - pad &&
        y <= rect.y + rect.height + pad
      ) {
        const cx = rect.x + rect.width / 2
        const cy = rect.y + rect.height / 2
        const distance = Math.hypot(x - cx, y - cy)
        hits.push({ aoi, distance })
      }
    }

    // Sort by type priority, then by distance
    return hits.sort((a, b) => {
      const pa = TYPE_PRIORITY[a.aoi.type] ?? 99
      const pb = TYPE_PRIORITY[b.aoi.type] ?? 99
      if (pa !== pb) return pa - pb
      return a.distance - b.distance
    })
  }

  /**
   * IAOIResolver implementation for FixationDetector.
   */
  resolve(x: number, y: number): { aoiId: string | null; wordIndex: number | null; paragraphId: string | null } {
    const hits = this.hitTest(x, y)
    if (hits.length === 0) return { aoiId: null, wordIndex: null, paragraphId: null }

    const top = hits[0].aoi
    // Also find paragraph (might be a different hit)
    const paraHit = hits.find((h) => h.aoi.type === 'paragraph')

    return {
      aoiId: top.id,
      wordIndex: top.meta.wordIndex ?? null,
      paragraphId: paraHit?.aoi.meta.paragraphId ?? top.meta.paragraphId ?? null,
    }
  }

  // ─────────────────────────────────────────────
  //  Private — DOM Scanning
  // ─────────────────────────────────────────────

  private scanDOM(): void {
    // Paragraphs
    document.querySelectorAll<HTMLElement>('[data-cte-paragraph]').forEach((el) => {
      const id = el.dataset.cteParagraph!
      this.registerElement(el, `para_${id}`, 'paragraph', { paragraphId: id })
    })

    // Words
    document.querySelectorAll<HTMLElement>('[data-cte-word]').forEach((el) => {
      const idx = parseInt(el.dataset.cteWord!, 10)
      const paraId = el.closest<HTMLElement>('[data-cte-paragraph]')?.dataset.cteParagraph
      this.registerElement(el, `word_${idx}`, 'word', {
        wordIndex: idx,
        paragraphId: paraId,
        text: el.textContent ?? undefined,
      })
    })

    // Questions
    document.querySelectorAll<HTMLElement>('[data-cte-question]').forEach((el) => {
      const qid = parseInt(el.dataset.cteQuestion!, 10)
      this.registerElement(el, `q_${qid}`, 'question', { questionId: qid })
    })

    // Options
    document.querySelectorAll<HTMLElement>('[data-cte-option]').forEach((el) => {
      const raw = el.dataset.cteOption! // e.g. "7-2"
      const [qid, optIdx] = raw.split('-').map(Number)
      this.registerElement(el, `opt_${raw}`, 'option', { questionId: qid, optionIndex: optIdx })
    })
  }

  private registerElement(el: HTMLElement, id: string, type: AOIType, meta: AOIMeta): void {
    const rect = el.getBoundingClientRect()
    this.aoiMap.set(id, {
      id,
      type,
      rect: { x: rect.x, y: rect.y, width: rect.width, height: rect.height },
      meta,
    })
  }

  // ─────────────────────────────────────────────
  //  Private — Observers
  // ─────────────────────────────────────────────

  private observeResize(): void {
    this.resizeObserver = new ResizeObserver(() => {
      this.debouncedRefresh()
    })
    this.resizeObserver.observe(document.body)
  }

  private observeScroll(): void {
    this.scrollHandler = () => this.debouncedRefresh()
    window.addEventListener('scroll', this.scrollHandler, { capture: true, passive: true })
  }

  private debouncedRefresh(): void {
    if (this.refreshTimer) clearTimeout(this.refreshTimer)
    this.refreshTimer = setTimeout(() => this.refresh(), this.config.refreshDebounceMs)
  }
}

// ─────────────────────────────────────────────
//  Constants
// ─────────────────────────────────────────────

const TYPE_PRIORITY: Record<AOIType, number> = {
  word: 0,
  sentence: 1,
  paragraph: 2,
  option: 3,
  question: 4,
  custom: 5,
}
