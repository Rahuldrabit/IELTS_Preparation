/**
 * FeatureToggleRow — a single feature toggle inside a SkillFeatureSection.
 * Handles boolean toggles and 2-option segmented controls (e.g. acousticLevel).
 */
'use client'

import { motion, AnimatePresence } from 'framer-motion'
import { type LucideIcon } from 'lucide-react'
import { Switch } from '@/components/ui/switch'
import { Badge } from '@/components/ui/badge'
import { cn } from '@/lib/utils'
import { useFeatureStore, type FeatureConfig } from '@/lib/store/featureStore'

// ─────────────────────────────────────────────
//  Types
// ─────────────────────────────────────────────

interface SegmentOption<T> {
  value: T
  label: string
}

interface FeatureToggleRowProps {
  skill: keyof FeatureConfig
  featureKey: string
  icon: LucideIcon
  title: string
  description: string
  badge?: 'Advanced' | 'Experimental'
  // For non-boolean features — renders segmented control instead of switch
  options?: SegmentOption<number>[]
  // Optional note shown below when auto-enabled by dependency
  autoEnabledNote?: string
}

// ─────────────────────────────────────────────
//  Component
// ─────────────────────────────────────────────

export function FeatureToggleRow({
  skill,
  featureKey,
  icon: Icon,
  title,
  description,
  badge,
  options,
  autoEnabledNote,
}: FeatureToggleRowProps) {
  const { features, setFeature } = useFeatureStore()
  const currentValue = (features[skill] as Record<string, unknown>)[featureKey]

  const handleToggle = (checked: boolean) => {
    setFeature(skill, featureKey as never, checked as never)
  }

  const handleSegment = (value: number) => {
    setFeature(skill, featureKey as never, value as never)
  }

  return (
    <div className="flex flex-col gap-1.5">
      <div className="flex items-center justify-between p-4 rounded-xl bg-muted/40 hover:bg-muted/60 transition-colors">
        {/* Left: icon + text */}
        <div className="flex items-center gap-3 flex-1 min-w-0">
          <div className="h-9 w-9 rounded-lg bg-background border border-border flex items-center justify-center shrink-0">
            <Icon className="h-4 w-4 text-muted-foreground" />
          </div>
          <div className="flex-1 min-w-0">
            <div className="flex items-center gap-2 flex-wrap">
              <span className="text-sm font-medium">{title}</span>
              {badge && (
                <Badge
                  variant="outline"
                  className={cn(
                    'text-xs',
                    badge === 'Advanced' && 'border-blue-300 text-blue-600 dark:text-blue-400',
                    badge === 'Experimental' && 'border-orange-300 text-orange-600 dark:text-orange-400'
                  )}
                >
                  {badge}
                </Badge>
              )}
            </div>
            <p className="text-xs text-muted-foreground mt-0.5 leading-relaxed">{description}</p>
          </div>
        </div>

        {/* Right: control */}
        <div className="ml-4 shrink-0">
          {options ? (
            // Segmented control for non-boolean (e.g. acousticLevel 1|2)
            <div className="flex items-center gap-1 p-1 bg-background border border-border rounded-lg">
              {options.map((opt) => (
                <button
                  key={opt.value}
                  onClick={() => handleSegment(opt.value)}
                  className={cn(
                    'px-2.5 py-1 rounded-md text-xs font-medium transition-all',
                    currentValue === opt.value
                      ? 'bg-primary text-primary-foreground shadow-sm'
                      : 'text-muted-foreground hover:text-foreground'
                  )}
                >
                  {opt.label}
                </button>
              ))}
            </div>
          ) : (
            <Switch
              checked={Boolean(currentValue)}
              onCheckedChange={handleToggle}
            />
          )}
        </div>
      </div>

      {/* Auto-enable note */}
      <AnimatePresence>
        {autoEnabledNote && Boolean(currentValue) && (
          <motion.p
            initial={{ height: 0, opacity: 0 }}
            animate={{ height: 'auto', opacity: 1 }}
            exit={{ height: 0, opacity: 0 }}
            className="text-xs text-amber-600 dark:text-amber-400 px-4 overflow-hidden"
          >
            {autoEnabledNote}
          </motion.p>
        )}
      </AnimatePresence>
    </div>
  )
}
