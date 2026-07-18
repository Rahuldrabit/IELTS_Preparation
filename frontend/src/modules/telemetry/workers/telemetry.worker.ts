/**
 * Telemetry Web Worker — offloads MediaPipe FaceLandmarker processing.
 *
 * Runs in a separate thread to avoid blocking React rendering.
 * Receives video frames as ImageBitmap, processes with FaceLandmarker,
 * posts back eye landmarks + blink detection results.
 *
 * Message protocol (discriminated unions defined in types.ts):
 *   Main → Worker: 'init' | 'process_frame' | 'destroy'
 *   Worker → Main: 'ready' | 'result' | 'error'
 */

/// <reference lib="webworker" />

import type { WorkerInMessage, WorkerOutMessage, EyeLandmarks, HeadPose, Point3D } from '../types'

// ─────────────────────────────────────────────
//  Landmark Indices
// ─────────────────────────────────────────────

const LM = {
  LEFT_IRIS: 468,
  RIGHT_IRIS: 473,
  LEFT_EYE_INNER: 133,
  LEFT_EYE_OUTER: 33,
  RIGHT_EYE_INNER: 362,
  RIGHT_EYE_OUTER: 263,
  LEFT_EYE_UPPER: 159,
  LEFT_EYE_LOWER: 145,
  RIGHT_EYE_UPPER: 386,
  RIGHT_EYE_LOWER: 374,
} as const

const EAR_THRESHOLD = 0.2
const BLINK_FRAMES = 2

// ─────────────────────────────────────────────
//  Worker State
// ─────────────────────────────────────────────

let landmarker: unknown = null
let blinkCounter = 0

// ─────────────────────────────────────────────
//  Message Handler
// ─────────────────────────────────────────────

self.onmessage = async (e: MessageEvent<WorkerInMessage>) => {
  const msg = e.data

  switch (msg.type) {
    case 'init':
      await initialize(msg.payload.modelUrl, msg.payload.wasmUrl)
      break
    case 'process_frame':
      processFrame(msg.payload.imageData, msg.payload.timestamp)
      break
    case 'destroy':
      destroy()
      break
  }
}

// ─────────────────────────────────────────────
//  Initialization
// ─────────────────────────────────────────────

async function initialize(modelUrl: string, wasmUrl: string): Promise<void> {
  try {
    // Import MediaPipe in worker context
    const { FaceLandmarker, FilesetResolver } = await import('@mediapipe/tasks-vision')

    const fileset = await FilesetResolver.forVisionTasks(wasmUrl)

    landmarker = await FaceLandmarker.createFromOptions(fileset, {
      baseOptions: {
        modelAssetPath: modelUrl,
        delegate: 'GPU',
      },
      runningMode: 'VIDEO',
      numFaces: 1,
      outputFaceBlendshapes: false,
      outputFacialTransformationMatrixes: true,
    })

    post({ type: 'ready' })
  } catch (err) {
    const error = err instanceof Error ? err : new Error(String(err))
    post({ type: 'error', payload: { message: error.message, stack: error.stack } })
  }
}

// ─────────────────────────────────────────────
//  Frame Processing
// ─────────────────────────────────────────────

function processFrame(imageBitmap: ImageBitmap, timestamp: number): void {
  if (!landmarker) return

  try {
    // eslint-disable-next-line @typescript-eslint/no-explicit-any
    const results = (landmarker as any).detectForVideo(imageBitmap, timestamp)

    // Release the ImageBitmap to free GPU memory
    imageBitmap.close()

    if (!results?.faceLandmarks?.length) {
      post({
        type: 'result',
        payload: { landmarks: null, blinkDetected: false, headPose: null, timestamp },
      })
      return
    }

    const raw = results.faceLandmarks[0]
    const landmarks = extractEyeLandmarks(raw)
    const blinkDetected = detectBlink(raw)
    const headPose = extractHeadPose(results.facialTransformationMatrixes)

    post({
      type: 'result',
      payload: { landmarks, blinkDetected, headPose, timestamp },
    })
  } catch (err) {
    const error = err instanceof Error ? err : new Error(String(err))
    post({ type: 'error', payload: { message: error.message, stack: error.stack } })
  }
}

// ─────────────────────────────────────────────
//  Cleanup
// ─────────────────────────────────────────────

function destroy(): void {
  if (landmarker) {
    // eslint-disable-next-line @typescript-eslint/no-explicit-any
    (landmarker as any).close?.()
    landmarker = null
  }
}

// ─────────────────────────────────────────────
//  Landmark Extraction (duplicated from FaceMesh for worker isolation)
// ─────────────────────────────────────────────

function extractEyeLandmarks(raw: Array<{ x: number; y: number; z: number }>): EyeLandmarks {
  const p = (idx: number): Point3D => ({ x: raw[idx].x, y: raw[idx].y, z: raw[idx].z })

  return {
    leftIris: p(LM.LEFT_IRIS),
    rightIris: p(LM.RIGHT_IRIS),
    leftEyeCorners: { inner: p(LM.LEFT_EYE_INNER), outer: p(LM.LEFT_EYE_OUTER) },
    rightEyeCorners: { inner: p(LM.RIGHT_EYE_INNER), outer: p(LM.RIGHT_EYE_OUTER) },
    leftEyeUpper: p(LM.LEFT_EYE_UPPER),
    leftEyeLower: p(LM.LEFT_EYE_LOWER),
    rightEyeUpper: p(LM.RIGHT_EYE_UPPER),
    rightEyeLower: p(LM.RIGHT_EYE_LOWER),
  }
}

function detectBlink(raw: Array<{ x: number; y: number; z: number }>): boolean {
  const leftEAR = ear(raw[LM.LEFT_EYE_UPPER], raw[LM.LEFT_EYE_LOWER], raw[LM.LEFT_EYE_INNER], raw[LM.LEFT_EYE_OUTER])
  const rightEAR = ear(raw[LM.RIGHT_EYE_UPPER], raw[LM.RIGHT_EYE_LOWER], raw[LM.RIGHT_EYE_INNER], raw[LM.RIGHT_EYE_OUTER])
  const avg = (leftEAR + rightEAR) / 2
  const closed = avg < EAR_THRESHOLD

  if (closed) {
    blinkCounter++
    return false
  }
  if (blinkCounter >= BLINK_FRAMES) {
    blinkCounter = 0
    return true
  }
  blinkCounter = 0
  return false
}

function ear(
  upper: { x: number; y: number },
  lower: { x: number; y: number },
  inner: { x: number; y: number },
  outer: { x: number; y: number },
): number {
  const v = Math.hypot(upper.x - lower.x, upper.y - lower.y)
  const h = Math.hypot(inner.x - outer.x, inner.y - outer.y)
  return h > 0 ? v / h : 0
}

function extractHeadPose(matrices?: Array<{ data: Float32Array }>): HeadPose | null {
  if (!matrices?.length) return null
  const m = matrices[0].data
  if (!m || m.length < 16) return null
  const R = 180 / Math.PI
  return {
    pitch: Math.asin(-m[6]) * R,
    yaw: Math.atan2(m[2], m[10]) * R,
    roll: Math.atan2(m[4], m[5]) * R,
  }
}

// ─────────────────────────────────────────────
//  Typed postMessage helper
// ─────────────────────────────────────────────

function post(msg: WorkerOutMessage): void {
  self.postMessage(msg)
}
