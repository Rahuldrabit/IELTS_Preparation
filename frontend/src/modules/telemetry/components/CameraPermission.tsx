/**
 * CameraPermission — user-facing permission request and status UI.
 *
 * Shows contextual UI based on camera state:
 *   - idle/requesting: prompt with explanation of why camera is needed
 *   - denied: instructions to enable camera in browser settings
 *   - error: error message with retry option
 *   - active: nothing (component hides itself)
 */
'use client'

import { Camera, AlertCircle, Settings, RefreshCw } from 'lucide-react'
import { motion } from 'framer-motion'
import type { CameraStatus } from '../types'

export interface CameraPermissionProps {
  status: CameraStatus
  error: string | null
  onRequestPermission: () => void
  onSkip?: () => void
}

export function CameraPermission({ status, error, onRequestPermission, onSkip }: CameraPermissionProps) {
  if (status === 'active') return null

  return (
    <motion.div
      className="rounded-xl border border-border bg-card p-6 space-y-4"
      initial={{ opacity: 0, y: 10 }}
      animate={{ opacity: 1, y: 0 }}
    >
      {/* Idle / Requesting */}
      {(status === 'idle' || status === 'requesting') && (
        <>
          <div className="flex items-center gap-3">
            <div className="h-10 w-10 rounded-lg bg-blue-500/10 flex items-center justify-center">
              <Camera className="h-5 w-5 text-blue-500" />
            </div>
            <div>
              <h3 className="font-medium text-sm">Enable Eye Tracking</h3>
              <p className="text-xs text-muted-foreground">
                Camera access helps track your reading patterns for personalized coaching.
              </p>
            </div>
          </div>

          <div className="text-xs text-muted-foreground space-y-1 pl-13">
            <p>Your video is processed entirely on your device.</p>
            <p>No images are stored or sent to any server.</p>
          </div>

          <div className="flex items-center gap-3">
            <button
              onClick={onRequestPermission}
              disabled={status === 'requesting'}
              className="px-4 py-2 bg-primary text-primary-foreground rounded-lg text-sm font-medium hover:bg-primary/90 disabled:opacity-50 transition-colors"
            >
              {status === 'requesting' ? 'Requesting...' : 'Enable Camera'}
            </button>
            {onSkip && (
              <button
                onClick={onSkip}
                className="px-4 py-2 text-sm text-muted-foreground hover:text-foreground transition-colors"
              >
                Skip for now
              </button>
            )}
          </div>
        </>
      )}

      {/* Denied */}
      {status === 'denied' && (
        <>
          <div className="flex items-center gap-3">
            <div className="h-10 w-10 rounded-lg bg-yellow-500/10 flex items-center justify-center">
              <Settings className="h-5 w-5 text-yellow-500" />
            </div>
            <div>
              <h3 className="font-medium text-sm">Camera Access Blocked</h3>
              <p className="text-xs text-muted-foreground">
                Eye tracking requires camera permission.
              </p>
            </div>
          </div>

          <div className="text-xs text-muted-foreground space-y-1">
            <p>To enable:</p>
            <ol className="list-decimal pl-4 space-y-0.5">
              <li>Click the camera/lock icon in your browser address bar</li>
              <li>Set Camera to &quot;Allow&quot;</li>
              <li>Refresh this page</li>
            </ol>
          </div>

          {onSkip && (
            <button
              onClick={onSkip}
              className="px-4 py-2 text-sm text-muted-foreground hover:text-foreground transition-colors"
            >
              Continue without eye tracking
            </button>
          )}
        </>
      )}

      {/* Error */}
      {status === 'error' && (
        <>
          <div className="flex items-center gap-3">
            <div className="h-10 w-10 rounded-lg bg-red-500/10 flex items-center justify-center">
              <AlertCircle className="h-5 w-5 text-red-500" />
            </div>
            <div>
              <h3 className="font-medium text-sm">Camera Error</h3>
              <p className="text-xs text-muted-foreground">{error ?? 'An unexpected error occurred.'}</p>
            </div>
          </div>

          <div className="flex items-center gap-3">
            <button
              onClick={onRequestPermission}
              className="px-4 py-2 bg-primary text-primary-foreground rounded-lg text-sm font-medium hover:bg-primary/90 transition-colors flex items-center gap-2"
            >
              <RefreshCw className="h-3.5 w-3.5" />
              Retry
            </button>
            {onSkip && (
              <button
                onClick={onSkip}
                className="px-4 py-2 text-sm text-muted-foreground hover:text-foreground transition-colors"
              >
                Continue without eye tracking
              </button>
            )}
          </div>
        </>
      )}
    </motion.div>
  )
}
