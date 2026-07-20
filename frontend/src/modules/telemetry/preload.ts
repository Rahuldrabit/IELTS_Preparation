/**
 * MediaPipe Preloader — Robust cold-start model download utility.
 *
 * Pure async module (no React dependency). Handles:
 *   - Backend health check → immediate download if backend is live
 *   - Fallback to idle-time CDN download if backend is unreachable
 *   - LocalStorage-based cache detection (skip re-download)
 *   - Singleton deduplication (multiple calls share one download)
 *   - Silent failure (non-blocking, non-critical)
 *
 * Strategy:
 *   1. schedulePreload() is called on app mount (layout.tsx)
 *   2. Check localStorage — if already cached, skip entirely
 *   3. Ping backend /health (fast, <1s timeout)
 *      → Backend live: start download immediately (user is likely to use features)
 *      → Backend down: defer to requestIdleCallback (don't waste bandwidth)
 *   4. Download: JS library → WASM → model → init → close → mark cached
 *   5. Next eye-tracking session loads from browser cache instantly
 *
 * Usage:
 *   import { schedulePreload, preloadMediaPipe, isModelCached } from '@/modules/telemetry/preload'
 *
 *   schedulePreload()              // Auto: checks backend, decides timing
 *   await preloadMediaPipe()       // Imperative: download now
 *   isModelCached()                // Check if already warm
 *   getPreloadStatus()             // 'idle' | 'downloading' | 'cached' | 'failed'
 *   invalidateModelCache()         // Force re-download next time
 */

// ─────────────────────────────────────────────
//  Constants (single source of truth)
// ─────────────────────────────────────────────

export const MEDIAPIPE_WASM_URL = 'https://cdn.jsdelivr.net/npm/@mediapipe/tasks-vision@0.10.18/wasm'
export const MEDIAPIPE_MODEL_URL =
  'https://storage.googleapis.com/mediapipe-models/face_landmarker/face_landmarker/float16/1/face_landmarker.task'

const CACHE_KEY = `cte_facemesh_cached_${MEDIAPIPE_MODEL_URL}`
const API_BASE = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'
const HEALTH_TIMEOUT_MS = 2_000

// ─────────────────────────────────────────────
//  Public API
// ─────────────────────────────────────────────

/** Returns true if the model was previously downloaded successfully. */
export function isModelCached(): boolean {
  if (typeof window === 'undefined') return false
  try {
    return localStorage.getItem(CACHE_KEY) === 'true'
  } catch {
    return false
  }
}

/** Clear the cache flag (forces re-download on next preload). */
export function invalidateModelCache(): void {
  if (typeof window === 'undefined') return
  try {
    localStorage.removeItem(CACHE_KEY)
  } catch {
    // noop
  }
}

export type PreloadStatus = 'idle' | 'checking' | 'downloading' | 'cached' | 'failed'

/** Singleton state so multiple callers don't trigger parallel downloads. */
let _status: PreloadStatus = 'idle'
let _promise: Promise<void> | null = null

export function getPreloadStatus(): PreloadStatus {
  return _status
}

/**
 * Download MediaPipe library, WASM runtime, and face landmark model.
 * Idempotent — safe to call multiple times. Returns immediately if cached.
 * Deduplicates concurrent calls (shares the same Promise).
 */
export function preloadMediaPipe(): Promise<void> {
  if (_status === 'cached' || isModelCached()) {
    _status = 'cached'
    return Promise.resolve()
  }

  if (_promise) return _promise

  _promise = _doPreload()
  return _promise
}

/**
 * Smart preload scheduler:
 *   - If model is cached → no-op
 *   - Pings backend /health (2s timeout)
 *     → Backend alive: start download immediately
 *     → Backend unreachable: defer to browser idle time
 *
 * This ensures fastest possible warm-up when the system is fully running,
 * and graceful degradation when backend is offline.
 */
export function schedulePreload(): void {
  if (typeof window === 'undefined') return
  if (isModelCached()) {
    _status = 'cached'
    return
  }

  _status = 'checking'
  _checkBackendThenPreload()
}

// ─────────────────────────────────────────────
//  Internal — Backend Health Check
// ─────────────────────────────────────────────

async function _checkBackendThenPreload(): Promise<void> {
  const backendAlive = await _isBackendAlive()

  if (backendAlive) {
    // Backend is live → user likely to use eye tracking soon, download now
    console.debug('[CTE:Preload] Backend alive — starting immediate download')
    preloadMediaPipe()
  } else {
    // Backend not reachable — defer to idle time (don't block anything)
    console.debug('[CTE:Preload] Backend unreachable — deferring to idle time')
    _scheduleIdle()
  }
}

/**
 * Fast health ping with timeout. Returns true if backend responds 200.
 * Uses AbortController for clean timeout handling.
 */
async function _isBackendAlive(): Promise<boolean> {
  try {
    const controller = new AbortController()
    const timeout = setTimeout(() => controller.abort(), HEALTH_TIMEOUT_MS)

    const response = await fetch(`${API_BASE}/health`, {
      method: 'GET',
      signal: controller.signal,
      // No credentials needed for health check
      cache: 'no-store',
    })

    clearTimeout(timeout)
    return response.ok
  } catch {
    // Network error, timeout, or aborted — backend is not reachable
    return false
  }
}

// ─────────────────────────────────────────────
//  Internal — Idle Scheduling
// ─────────────────────────────────────────────

function _scheduleIdle(): void {
  const run = () => { preloadMediaPipe() }

  if (typeof window.requestIdleCallback === 'function') {
    window.requestIdleCallback(run, { timeout: 15_000 })
  } else {
    setTimeout(run, 5_000)
  }
}

// ─────────────────────────────────────────────
//  Internal — Model Download
// ─────────────────────────────────────────────

async function _doPreload(): Promise<void> {
  _status = 'downloading'

  try {
    // 1. Dynamic import — downloads the JS bundle
    const { FaceLandmarker, FilesetResolver } = await import('@mediapipe/tasks-vision')

    // 2. WASM runtime download
    const fileset = await FilesetResolver.forVisionTasks(MEDIAPIPE_WASM_URL)

    // 3. Model download + GPU init
    const landmarker = await FaceLandmarker.createFromOptions(fileset, {
      baseOptions: {
        modelAssetPath: MEDIAPIPE_MODEL_URL,
        delegate: 'GPU',
      },
      runningMode: 'VIDEO',
      numFaces: 1,
      outputFaceBlendshapes: false,
      outputFacialTransformationMatrixes: false,
    })

    // 4. Cleanup — we only needed to warm the browser cache
    landmarker.close()

    // 5. Mark cached
    try {
      localStorage.setItem(CACHE_KEY, 'true')
    } catch {
      // Storage full or blocked — still counts as success for this session
    }

    _status = 'cached'
    console.debug('[CTE:Preload] Model downloaded and cached successfully')
  } catch (err) {
    _status = 'failed'
    _promise = null // Allow retry on next call
    console.debug('[CTE:Preload] Download failed (non-critical):', err)
  }
}
