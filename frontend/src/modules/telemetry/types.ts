/**
 * Cognitive Telemetry Engine — Core Type Definitions
 *
 * Design principles:
 *   - Generic EventEmitter pattern for all observable subsystems
 *   - Interface segregation: small, composable contracts
 *   - Discriminated unions for event types (exhaustive pattern matching)
 *   - Serializable types (no class instances in data payloads)
 */

// ─────────────────────────────────────────────
//  Generic Infrastructure
// ─────────────────────────────────────────────

/** Type-safe event emitter contract. All CTE subsystems implement this. */
export interface IEmitter<TEventMap extends Record<string, any>> {
  on<K extends keyof TEventMap>(event: K, handler: (data: TEventMap[K]) => void): () => void
  off<K extends keyof TEventMap>(event: K, handler: (data: TEventMap[K]) => void): void
  emit<K extends keyof TEventMap>(event: K, data: TEventMap[K]): void
}

/** Lifecycle contract for startable/stoppable subsystems. */
export interface ILifecycle {
  start(): void | Promise<void>
  stop(): void
  destroy(): void
}

/** Combined contract for trackable subsystems. */
export interface ITracker extends ILifecycle {
  readonly active: boolean
}

// ─────────────────────────────────────────────
//  Geometry
// ─────────────────────────────────────────────

export interface Point2D {
  x: number
  y: number
}

export interface Point3D extends Point2D {
  z: number
}

export interface BoundingBox {
  x: number
  y: number
  width: number
  height: number
}

// ─────────────────────────────────────────────
//  Camera
// ─────────────────────────────────────────────

export type CameraStatus = 'idle' | 'requesting' | 'active' | 'denied' | 'error'

export interface CameraState {
  status: CameraStatus
  stream: MediaStream | null
  error: string | null
}

export interface CameraEventMap {
  stateChange: CameraState
  frame: { video: HTMLVideoElement; timestamp: number }
}

export interface CameraConfig {
  width: number
  height: number
  frameRate: number
  facingMode: 'user' | 'environment'
}

// ─────────────────────────────────────────────
//  Face Mesh
// ─────────────────────────────────────────────

export interface EyeLandmarks {
  leftIris: Point3D
  rightIris: Point3D
  leftEyeCorners: { inner: Point3D; outer: Point3D }
  rightEyeCorners: { inner: Point3D; outer: Point3D }
  leftEyeUpper: Point3D
  leftEyeLower: Point3D
  rightEyeUpper: Point3D
  rightEyeLower: Point3D
}

export interface FaceMeshResult {
  landmarks: EyeLandmarks | null
  fullMesh?: Point3D[] | null
  blinkDetected: boolean
  headPose: HeadPose | null
  timestamp: number
}

export interface HeadPose {
  pitch: number
  yaw: number
  roll: number
}

export interface FaceMeshProgress {
  /** Download stage: 'wasm' | 'model' | 'library' | 'initializing' */
  stage: string
  /** Progress percentage (0-100) */
  progress: number
  /** Estimated time remaining in ms */
  estimatedMs?: number
}

export interface FaceMeshEventMap {
  result: FaceMeshResult
  ready: void
  error: Error
  progress: FaceMeshProgress
}

// ─────────────────────────────────────────────
//  Calibration
// ─────────────────────────────────────────────

export interface CalibrationPoint {
  screenX: number
  screenY: number
  irisX: number
  irisY: number
  timestamp: number
}

export interface CalibrationMatrix {
  /** Polynomial coefficients: screenX = a0 + a1*ix + a2*iy + a3*ix² + a4*iy² */
  xCoeffs: number[]
  /** Polynomial coefficients: screenY = b0 + b1*ix + b2*iy + b3*ix² + b4*iy² */
  yCoeffs: number[]
  /** Fitting error (mean squared error in pixels) */
  mse: number
  /** Unix timestamp of calibration */
  calibratedAt: number
  /** Screen dimensions at calibration time */
  screenWidth: number
  screenHeight: number
}

export type CalibrationStatus = 'idle' | 'calibrating' | 'collecting' | 'complete' | 'failed'

export interface CalibrationState {
  status: CalibrationStatus
  currentPointIndex: number
  totalPoints: number
  collectedSamples: number
  samplesPerPoint: number
  matrix: CalibrationMatrix | null
  accuracy: number
}

export interface CalibrationEventMap {
  stateChange: CalibrationState
  pointComplete: { index: number; point: CalibrationPoint }
  complete: CalibrationMatrix
  failed: Error
}

// ─────────────────────────────────────────────
//  Gaze
// ─────────────────────────────────────────────

export interface GazePoint {
  x: number
  y: number
  timestamp: number
  confidence: number
}

export interface GazeEventMap {
  point: GazePoint
  fixationStart: Fixation
  fixationEnd: Fixation
  regression: Regression
  saccade: Saccade
  blink: { timestamp: number; duration: number }
}

export interface Fixation {
  id: string
  x: number
  y: number
  startTime: number
  endTime: number
  duration: number
  aoiId: string | null
  wordIndex: number | null
  paragraphId: string | null
}

export interface Regression {
  id: string
  fromX: number
  fromY: number
  toX: number
  toY: number
  timestamp: number
  distance: number
  fromAoiId: string | null
  toAoiId: string | null
  fromParagraphId: string | null
  toParagraphId: string | null
}

export interface Saccade {
  fromX: number
  fromY: number
  toX: number
  toY: number
  timestamp: number
  duration: number
  amplitude: number
  direction: 'forward' | 'backward' | 'up' | 'down'
}

// ─────────────────────────────────────────────
//  Area of Interest (AOI)
// ─────────────────────────────────────────────

export type AOIType = 'word' | 'sentence' | 'paragraph' | 'question' | 'option' | 'custom'

export interface AOI {
  id: string
  type: AOIType
  rect: BoundingBox
  meta: AOIMeta
}

export interface AOIMeta {
  wordIndex?: number
  sentenceIndex?: number
  paragraphId?: string
  questionId?: number
  optionIndex?: number
  text?: string
  [key: string]: unknown
}

export interface AOIHit {
  aoi: AOI
  distance: number
}

// ─────────────────────────────────────────────
//  Mouse / Scroll / Focus Trackers
// ─────────────────────────────────────────────

export interface MouseEventData {
  x: number
  y: number
  timestamp: number
  type: 'move' | 'click' | 'dblclick' | 'select'
  aoiId: string | null
}

export interface MouseEventMap {
  move: MouseEventData
  click: MouseEventData
  select: TextSelectionData
}

export interface TextSelectionData {
  text: string
  startOffset: number
  endOffset: number
  paragraphId: string | null
  timestamp: number
}

export interface ScrollEventData {
  scrollTop: number
  scrollLeft: number
  timestamp: number
  direction: 'up' | 'down'
  velocity: number
  visibleParagraphs: string[]
}

export interface ScrollEventMap {
  scroll: ScrollEventData
  paragraphEnter: { paragraphId: string; timestamp: number }
  paragraphExit: { paragraphId: string; timestamp: number; dwellMs: number }
}

export interface FocusEventData {
  focused: boolean
  timestamp: number
  reason: 'visibility' | 'blur' | 'focus'
}

export interface FocusEventMap {
  change: FocusEventData
}

// ─────────────────────────────────────────────
//  Telemetry Events (unified event bus)
// ─────────────────────────────────────────────

export type TelemetryEventType =
  | 'fixation'
  | 'regression'
  | 'saccade'
  | 'blink'
  | 'mouse_move'
  | 'mouse_click'
  | 'text_select'
  | 'scroll'
  | 'paragraph_enter'
  | 'paragraph_exit'
  | 'question_focus'
  | 'answer_change'
  | 'focus_lost'
  | 'focus_gained'
  | 'session_start'
  | 'session_end'

export interface TelemetryEvent<T extends TelemetryEventType = TelemetryEventType> {
  id: string
  type: T
  timestamp: number
  sessionId: string
  data: Record<string, unknown>
}

// ─────────────────────────────────────────────
//  Session & Config
// ─────────────────────────────────────────────

export type TelemetrySkill = 'reading' | 'listening'

export interface TelemetrySession {
  id: string
  userId: number
  skill: TelemetrySkill
  backendSessionId: number | null
  startedAt: number
  endedAt: number | null
  calibrationId: string | null
  config: TelemetryConfig
}

export interface TelemetryConfig {
  gazeEnabled: boolean
  mouseEnabled: boolean
  scrollEnabled: boolean
  focusEnabled: boolean
  uploadIntervalMs: number
  debugOverlay: boolean
  fixationThresholdMs: number
  fixationDispersionPx: number
  gazeSamplingRate: number
  /** Max events buffered locally before force-flush */
  maxBufferSize: number
  /** Retry attempts for failed uploads */
  uploadRetryAttempts: number
}

export const DEFAULT_CONFIG: TelemetryConfig = {
  gazeEnabled: true,
  mouseEnabled: true,
  scrollEnabled: true,
  focusEnabled: true,
  uploadIntervalMs: 2000,
  debugOverlay: false,
  fixationThresholdMs: 150,
  fixationDispersionPx: 30,
  gazeSamplingRate: 30,
  maxBufferSize: 500,
  uploadRetryAttempts: 3,
}

// ─────────────────────────────────────────────
//  Analytics Summaries
// ─────────────────────────────────────────────

export interface ReadingAnalyticsSummary {
  sessionId: string
  paragraphTime: Record<string, number>
  fixationCount: number
  regressionCount: number
  skipRate: number
  blinkRate: number
  focusScore: number
  avgFixationDuration: number
  readingSpeedWpm: number
  timestamp: number
}

export interface ListeningAnalyticsSummary {
  sessionId: string
  audioTimestamp: number
  lookingAt: string | null
  currentQuestionId: number | null
  gazeDuration: number
  audioGazeAlignment: number
  timestamp: number
}

// ─────────────────────────────────────────────
//  Upload Payload
// ─────────────────────────────────────────────

export interface TelemetryUploadPayload {
  sessionId: string
  timestamp: number
  summary: ReadingAnalyticsSummary | ListeningAnalyticsSummary
  events: TelemetryEvent[]
}

// ─────────────────────────────────────────────
//  Worker Messages (discriminated union)
// ─────────────────────────────────────────────

export type WorkerInMessage =
  | { type: 'init'; payload: { modelUrl: string; wasmUrl: string } }
  | { type: 'process_frame'; payload: { imageData: ImageBitmap; timestamp: number } }
  | { type: 'destroy' }

export type WorkerOutMessage =
  | { type: 'ready' }
  | { type: 'result'; payload: FaceMeshResult }
  | { type: 'error'; payload: { message: string; stack?: string } }
