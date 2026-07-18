/**
 * MouseTracker — throttled mouse position, click, and text selection tracking.
 *
 * Design:
 *   - Throttled mousemove (configurable interval) to avoid event flood
 *   - Click and double-click with AOI resolution
 *   - Text selection detection (mouseup after drag)
 *   - Implements ITracker for consistent lifecycle
 *   - All coordinates are viewport-relative (clientX/clientY)
 */

import { Emitter } from '../core/Emitter'
import type { ITracker, MouseEventMap, MouseEventData, TextSelectionData } from '../types'

export interface MouseTrackerConfig {
  /** Throttle interval for mousemove events (ms) */
  throttleMs: number
  /** Optional AOI resolver for mapping mouse pos to AOI */
  aoiResolver?: (x: number, y: number) => string | null
  /** Target element to attach listeners (default: document) */
  target?: HTMLElement | Document
}

const DEFAULT_CONFIG: MouseTrackerConfig = {
  throttleMs: 50,
}

export class MouseTracker extends Emitter<MouseEventMap> implements ITracker {
  private config: MouseTrackerConfig
  private _active = false
  private lastMoveEmit = 0
  private boundHandlers: {
    move: (e: MouseEvent) => void
    click: (e: MouseEvent) => void
    dblclick: (e: MouseEvent) => void
    mouseup: (e: MouseEvent) => void
  } | null = null

  constructor(config: Partial<MouseTrackerConfig> = {}) {
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
    if (this._active) return
    this._active = true

    const target = this.config.target ?? document

    this.boundHandlers = {
      move: this.onMouseMove.bind(this),
      click: this.onClick.bind(this),
      dblclick: this.onDblClick.bind(this),
      mouseup: this.onMouseUp.bind(this),
    }

    target.addEventListener('mousemove', this.boundHandlers.move as EventListener, { passive: true })
    target.addEventListener('click', this.boundHandlers.click as EventListener, { passive: true })
    target.addEventListener('dblclick', this.boundHandlers.dblclick as EventListener, { passive: true })
    target.addEventListener('mouseup', this.boundHandlers.mouseup as EventListener, { passive: true })
  }

  stop(): void {
    if (!this._active || !this.boundHandlers) return
    this._active = false

    const target = this.config.target ?? document
    target.removeEventListener('mousemove', this.boundHandlers.move as EventListener)
    target.removeEventListener('click', this.boundHandlers.click as EventListener)
    target.removeEventListener('dblclick', this.boundHandlers.dblclick as EventListener)
    target.removeEventListener('mouseup', this.boundHandlers.mouseup as EventListener)
    this.boundHandlers = null
  }

  destroy(): void {
    this.stop()
    this.removeAllListeners()
  }

  configure(config: Partial<MouseTrackerConfig>): void {
    this.config = { ...this.config, ...config }
  }

  // ─────────────────────────────────────────────
  //  Private — Event Handlers
  // ─────────────────────────────────────────────

  private onMouseMove(e: MouseEvent): void {
    const now = performance.now()
    if (now - this.lastMoveEmit < this.config.throttleMs) return
    this.lastMoveEmit = now

    this.emit('move', this.buildEvent(e, 'move'))
  }

  private onClick(e: MouseEvent): void {
    this.emit('click', this.buildEvent(e, 'click'))
  }

  private onDblClick(e: MouseEvent): void {
    this.emit('click', this.buildEvent(e, 'dblclick'))
  }

  private onMouseUp(_e: MouseEvent): void {
    // Check for text selection
    const selection = window.getSelection()
    if (!selection || selection.isCollapsed || !selection.toString().trim()) return

    const text = selection.toString()
    const range = selection.getRangeAt(0)

    // Find paragraph context
    let paragraphId: string | null = null
    const container = range.startContainer.parentElement
    const paraEl = container?.closest<HTMLElement>('[data-cte-paragraph]')
    if (paraEl) {
      paragraphId = paraEl.dataset.cteParagraph ?? null
    }

    const selData: TextSelectionData = {
      text,
      startOffset: range.startOffset,
      endOffset: range.endOffset,
      paragraphId,
      timestamp: performance.now(),
    }

    this.emit('select', selData)
  }

  // ─────────────────────────────────────────────
  //  Private — Helpers
  // ─────────────────────────────────────────────

  private buildEvent(e: MouseEvent, type: MouseEventData['type']): MouseEventData {
    const aoiId = this.config.aoiResolver?.(e.clientX, e.clientY) ?? null
    return {
      x: e.clientX,
      y: e.clientY,
      timestamp: performance.now(),
      type,
      aoiId,
    }
  }
}
