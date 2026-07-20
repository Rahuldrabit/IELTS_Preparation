/**
 * Cognitive Telemetry Engine (CTE) — Public API
 *
 * Usage in a page component:
 *
 *   import { useTelemetry, useGaze, useCalibration, GazeDebugOverlay, CalibrationOverlay, CameraPermission } from '@/modules/telemetry'
 *
 *   function ReadingPage() {
 *     const { start, stop, status, tracker } = useTelemetry({ skill: 'reading', sessionId: '...' })
 *     const { point } = useGaze({ tracker })
 *     const { trail, fixations, regressionCount } = useGazeDebug({ tracker })
 *     const cal = useCalibration()
 *     ...
 *   }
 */

// Types
export * from './types'

// Core
export { Emitter } from './core'

// Camera
export { CameraManager, FaceMeshProcessor, CalibrationSystem, applyCalibration } from './camera'

// Gaze
export { GazeEstimator, FixationDetector, RegressionDetector, AOIMapper } from './gaze'
export type { ICalibrationProvider, GazeEstimatorConfig, IAOIResolver, FixationDetectorConfig, RegressionDetectorConfig, AOIMapperConfig } from './gaze'

// Trackers
export { MouseTracker, ScrollTracker, FocusTracker, ReadingTracker, ListeningTracker } from './trackers'

// Analytics
export { ReadingAnalytics, computeAttentionScore, stdDev, coefficientOfVariation } from './analytics'
export type { AttentionInput, AttentionResult, AttentionWeights, ReadingAnalyticsConfig } from './analytics'

// Storage
export { IndexedDBStore, TelemetryUploader } from './storage'

// Workers
export { WorkerBridge } from './workers/WorkerBridge'

// Hooks
export { useTelemetry, useCalibration, useGaze, useGazeDebug } from './hooks'
export type { UseTelemetryOptions, UseTelemetryReturn, TelemetryStatus, UseCalibrationReturn, UseGazeOptions, UseGazeReturn, UseGazeDebugOptions, UseGazeDebugReturn } from './hooks'

// Components
export { CalibrationOverlay, GazeDebugOverlay, CameraPermission, EyeTrackingSetupModal } from './components'
export type { CalibrationOverlayProps, GazeDebugOverlayProps, CameraPermissionProps } from './components'

// Preload
export { schedulePreload, preloadMediaPipe, isModelCached, invalidateModelCache, getPreloadStatus } from './preload'
export type { PreloadStatus } from './preload'
