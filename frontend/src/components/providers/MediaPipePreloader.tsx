'use client'

/**
 * MediaPipePreloader — Thin React wrapper for cold-start model download.
 *
 * Renders nothing. Triggers background download of MediaPipe assets
 * as soon as the app mounts. Delegates all logic to the reusable
 * `@/modules/telemetry/preload` utility.
 *
 * Place once in the root layout — it's idempotent and deduplicates calls.
 */

import { useEffect } from 'react'
import { schedulePreload } from '@/modules/telemetry/preload'

export function MediaPipePreloader() {
  useEffect(() => {
    schedulePreload()
  }, [])

  return null
}
