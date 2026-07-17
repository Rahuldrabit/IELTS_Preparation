/**
 * SessionFeatureBar — compact feature toggle strip shown at the bottom of config panels.
 * Lets students override their global Feature Lab defaults for just the upcoming session.
 */
'use client'

import { type LucideIcon } from 'lucide-react'
import { Switch } from '@/components/ui/switch'
import { cn } from '@/lib/utils'
import { useFeatureStore, DEFAULT_FEATURES, type FeatureConfig } from '@/lib/store/featureStore'

// ─────────────────────────────────────────────
//  Types
// ─────────────────────────────────────────────

export interface FeatureBarItem {
  featureKey: string
  label: string
  icon: LucideIcon
  // For non-boolean features like acousticLevel
  options?: Array<{ value: number; label: string }>
}

interface SessionFeatureBarProps {
  skill: keyof FeatureConfig
  features: FeatureBarItem[]
  className?: string
}

// ─────────────────────────────────────────────
//  Component
// ─────────────────────────────────────────────

export function SessionFeatureBar({ skill, features, className }: SessionFeatureBarProps) {
  const { features: config, setFeature } = useFeatureStore()

  if (!features.length) return null

  const skillConfig = config[skill] as Record<string, unknown>
  const defaults = DEFAULT_FEATURES[skill] as Record<string, unknown>
  const hasOverrides = features.some((f) => skillConfig[f.featureKey] !== defaults[f.featureKey])

  return (
    <div className={cn('border-t pt-4 mt-2', className)}>
      <div className="flex items-center justify-between gap-4 flex-wrap">
        <span className="text-xs text-muted-foreground shrink-0">
          Session features
          {!hasOverrides && (
            <span className="ml-1 italic">(using saved defaults)</span>
          )}
        </span>

        <div className="flex items-center gap-4 flex-wrap">
          {features.map((item) => {
            const currentVal = skillConfig[item.featureKey]

            if (item.options) {
              // Segmented control for non-boolean (e.g. acousticLevel)
              return (
                <div key={item.featureKey} className="flex items-center gap-1.5">
                  <item.icon className="h-3.5 w-3.5 text-muted-foreground" />
                  <span className="text-xs text-muted-foreground">{item.label}:</span>
                  <div className="flex gap-0.5 p-0.5 bg-muted rounded-md">
                    {item.options.map((opt) => (
                      <button
                        key={opt.value}
                        onClick={() => setFeature(skill, item.featureKey as never, opt.value as never)}
                        className={cn(
                          'px-2 py-0.5 rounded text-xs font-medium transition-all',
                          currentVal === opt.value
                            ? 'bg-background shadow-sm text-foreground'
                            : 'text-muted-foreground hover:text-foreground'
                        )}
                      >
                        {opt.label}
                      </button>
                    ))}
                  </div>
                </div>
              )
            }

            return (
              <div key={item.featureKey} className="flex items-center gap-1.5">
                <item.icon className="h-3.5 w-3.5 text-muted-foreground" />
                <span className="text-xs text-muted-foreground">{item.label}</span>
                <Switch
                  checked={Boolean(currentVal)}
                  onCheckedChange={(checked) =>
                    setFeature(skill, item.featureKey as never, checked as never)
                  }
                  className="scale-75 origin-right"
                />
              </div>
            )
          })}
        </div>
      </div>
    </div>
  )
}
