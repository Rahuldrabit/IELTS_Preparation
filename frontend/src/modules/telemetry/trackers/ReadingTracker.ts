/**
 * ReadingTracker — orchestrates all reading-session telemetry subsystems.
 *
 * Composition over inheritance: composes CameraManager, FaceMesh, Calibration,
 * GazeEstimator, FixationDetector, RegressionDetector, AOIMapper,
 * MouseTracker, ScrollTracker, FocusTracker into a single lifecycle.
 *
 * Responsibilities:
 *   - Wire subsystems together (gaze → fixation → regression)
 *   - Emit unified TelemetryEvents for storage/upload
 *   - Respect config (which trackers are enabled)
 *   - Provide session-level start/stop
 */

import { Emitter } from '../core/Emitter'
import { CameraManager } from '../camera/CameraManager'
import { FaceMeshProcessor } from '../camera/FaceMesh'
import { CalibrationSystem } from '../camera/Calibration'
import { GazeEstimator } from '../gaze/GazeEstimator'
import { FixationDetector } from '../gaze/FixationDetector'
import { RegressionDetector } from '../gaze/RegressionDetector'
import { AOIMapper } from '../gaze/AOIMapper'
import { MouseTracker } from './MouseTracker'
import { ScrollTracker } from './ScrollTracker'
import { FocusTracker } from './FocusTracker'
import type {
  Fixation,
  GazePoint,
  ILifecycle,
  Regression,
  TelemetryConfig,
  TelemetryEvent,
  TelemetryEventType,
} from '../types'

export interface ReadingTrackerEventMap {
  event: TelemetryEvent
  gazePoint: GazePoint
  fixation: Fixation
  regression: Regression
}

export class ReadingTracker extends Emitter<ReadingTrackerEventMap> implements ILifecycle {
  // Subsystems
  readonly camera: CameraManager
  readonly faceMesh: FaceMeshProcessor
  readonly calibration: CalibrationSystem
  readonly gazeEstimator: GazeEstimator
  readonly fixationDetector: FixationDetector
  readonly regressionDetector: RegressionDetector
  readonly aoiMapper: AOIMapper
  readonly mouseTracker: MouseTracker
  readonly scrollTracker: ScrollTracker
  readonly focusTracker: FocusTracker

  private config: TelemetryConfig
  private sessionId: string
  private existingStream?: MediaStream
  private disposers: (() => void)[] = []
  private eventIdCounter = 0

  constructor(sessionId: string, config: TelemetryConfig, existingStream?: MediaStream) {
    super()
    this.sessionId = sessionId
    this.config = config

    // Instantiate subsystems
    this.camera = new CameraManager()
    this.faceMesh = new FaceMeshProcessor()
    this.calibration = new CalibrationSystem()
    this.aoiMapper = new AOIMapper()
    this.fixationDetector = new FixationDetector(
      { minDurationMs: config.fixationThresholdMs, maxDispersionPx: config.fixationDispersionPx },
      this.aoiMapper,
    )
    this.regressionDetector = new RegressionDetector()
    this.gazeEstimator = new GazeEstimator({ getMatrix: () => this.calibration.state.matrix })
    this.mouseTracker = new MouseTracker({ aoiResolver: (x, y) => this.aoiMapper.resolve(x, y).aoiId })
    this.scrollTracker = new ScrollTracker()
    this.focusTracker = new FocusTracker()
    this.existingStream = existingStream
  }

  // ─────────────────────────────────────────────
  //  Public API
  // ─────────────────────────────────────────────

  async start(): Promise<void> {
    // Wire up event chains
    this.wireGazePipeline()
    this.wireTrackers()

    // Start subsystems based on config
    if (this.config.gazeEnabled) {
      await this.faceMesh.start()
      await this.camera.start(this.existingStream)
    }

    this.aoiMapper.start()

    if (this.config.mouseEnabled) this.mouseTracker.start()
    if (this.config.scrollEnabled) this.scrollTracker.start()
    if (this.config.focusEnabled) this.focusTracker.start()

    this.fixationDetector.start()
    this.regressionDetector.start()
    this.gazeEstimator.start()

    this.pushEvent('session_start', {})
  }

  stop(): void {
    this.pushEvent('session_end', {
      totalFocusedMs: this.focusTracker.totalFocused,
      totalUnfocusedMs: this.focusTracker.totalUnfocused,
    })

    // Tear down in reverse order
    this.gazeEstimator.stop()
    this.regressionDetector.stop()
    this.fixationDetector.stop()
    this.focusTracker.stop()
    this.scrollTracker.stop()
    this.mouseTracker.stop()
    this.aoiMapper.stop()
    this.camera.stop()

    // Dispose subscriptions
    this.disposers.forEach((d) => d())
    this.disposers = []
  }

  destroy(): void {
    this.stop()
    this.camera.destroy()
    this.faceMesh.destroy()
    this.calibration.destroy()
    this.gazeEstimator.destroy()
    this.fixationDetector.destroy()
    this.regressionDetector.destroy()
    this.aoiMapper.destroy()
    this.mouseTracker.destroy()
    this.scrollTracker.destroy()
    this.focusTracker.destroy()
    this.removeAllListeners()
  }

  // ─────────────────────────────────────────────
  //  Private — Wiring
  // ─────────────────────────────────────────────

  private wireGazePipeline(): void {
    if (!this.config.gazeEnabled) return

    // Camera frame → FaceMesh processing
    const d1 = this.camera.on('frame', ({ video, timestamp }) => {
      if (!this.focusTracker.focused) return // Skip when tab not visible
      const result = this.faceMesh.process(video, timestamp)
      if (!result?.landmarks) return

      // FaceMesh result → GazeEstimator
      const gazePoint = this.gazeEstimator.estimate(result.landmarks, result.headPose, timestamp)
      if (!gazePoint) return

      this.emit('gazePoint', gazePoint)

      // Gaze point → Fixation detector
      this.fixationDetector.addPoint(gazePoint)

      // Blink event
      if (result.blinkDetected) {
        this.pushEvent('blink', { timestamp })
      }
    })
    this.disposers.push(d1)

    // Fixation → Regression detection + event emission
    const d2 = this.fixationDetector.on('fixationEnd', (fixation) => {
      this.emit('fixation', fixation)
      this.regressionDetector.addFixation(fixation)
      this.pushEvent('fixation', {
        x: fixation.x,
        y: fixation.y,
        duration: fixation.duration,
        aoiId: fixation.aoiId,
        wordIndex: fixation.wordIndex,
        paragraphId: fixation.paragraphId,
      })
    })
    this.disposers.push(d2)

    // Regression events
    const d3 = this.regressionDetector.on('regression', (reg) => {
      this.emit('regression', reg)
      this.pushEvent('regression', {
        fromX: reg.fromX,
        fromY: reg.fromY,
        toX: reg.toX,
        toY: reg.toY,
        distance: reg.distance,
        fromParagraphId: reg.fromParagraphId,
        toParagraphId: reg.toParagraphId,
      })
    })
    this.disposers.push(d3)
  }

  private wireTrackers(): void {
    if (this.config.mouseEnabled) {
      const d1 = this.mouseTracker.on('click', (data) => {
        this.pushEvent('mouse_click', { x: data.x, y: data.y, aoiId: data.aoiId })
      })
      const d2 = this.mouseTracker.on('select', (data) => {
        this.pushEvent('text_select', {
          text: data.text,
          paragraphId: data.paragraphId,
        })
      })
      this.disposers.push(d1, d2)
    }

    if (this.config.scrollEnabled) {
      const d1 = this.scrollTracker.on('paragraphEnter', (data) => {
        this.pushEvent('paragraph_enter', data)
      })
      const d2 = this.scrollTracker.on('paragraphExit', (data) => {
        this.pushEvent('paragraph_exit', data)
      })
      this.disposers.push(d1, d2)
    }

    if (this.config.focusEnabled) {
      const d1 = this.focusTracker.on('change', (data) => {
        this.pushEvent(data.focused ? 'focus_gained' : 'focus_lost', { reason: data.reason })
      })
      this.disposers.push(d1)
    }
  }

  // ─────────────────────────────────────────────
  //  Private — Event Generation
  // ─────────────────────────────────────────────

  private pushEvent(type: TelemetryEventType, data: Record<string, unknown>): void {
    const event: TelemetryEvent = {
      id: `${this.sessionId}_${++this.eventIdCounter}`,
      type,
      timestamp: performance.now(),
      sessionId: this.sessionId,
      data,
    }
    this.emit('event', event)
  }
}
