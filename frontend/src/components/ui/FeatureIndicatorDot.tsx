/**
 * FeatureIndicatorDot — a 3px dot shown on nav items when advanced features are active.
 * Positioned absolute top-right relative to its parent (which must be `relative`).
 */
'use client'

import { cn } from '@/lib/utils'

interface FeatureIndicatorDotProps {
  active: boolean
  className?: string
}

export function FeatureIndicatorDot({ active, className }: FeatureIndicatorDotProps) {
  if (!active) return null

  return (
    <span
      aria-hidden="true"
      className={cn(
        'absolute top-0.5 right-0.5 h-2 w-2 rounded-full bg-primary',
        'ring-2 ring-card',   // white halo separates dot from icon background
        className
      )}
    />
  )
}
