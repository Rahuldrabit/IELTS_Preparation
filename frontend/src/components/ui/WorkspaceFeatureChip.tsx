/**
 * WorkspaceFeatureChip — mid-session feature toggle shown in workspace toolbars.
 *
 * Turning a feature OFF shows a Radix Tooltip confirmation to prevent accidental data loss.
 * Turning a feature ON is immediate with no confirmation.
 */
'use client'

import { useState, useCallback } from 'react'
import * as TooltipPrimitive from '@radix-ui/react-tooltip'
import { type LucideIcon } from 'lucide-react'
import { Button } from '@/components/ui/button'
import { cn } from '@/lib/utils'
import { useFeatureStore, type FeatureConfig } from '@/lib/store/featureStore'
import { useFeature } from '@/lib/hooks/useFeature'

// ─────────────────────────────────────────────
//  Single Chip
// ─────────────────────────────────────────────

interface WorkspaceFeatureChipProps {
  skill: keyof FeatureConfig
  featureKey: string
  label: string
  icon: LucideIcon
  // Display-only read-only chip (non-boolean features like acousticLevel)
  readOnly?: boolean
  displayValue?: string
}

export function WorkspaceFeatureChip({
  skill,
  featureKey,
  label,
  icon: Icon,
  readOnly = false,
  displayValue,
}: WorkspaceFeatureChipProps) {
  const { setFeature } = useFeatureStore()
  const currentValue = useFeature(skill, featureKey as never)
  const isActive = Boolean(currentValue)
  const [confirmOpen, setConfirmOpen] = useState(false)

  const handleClick = useCallback(() => {
    if (readOnly) return

    if (isActive) {
      // Currently ON → show confirmation before disabling
      setConfirmOpen(true)
    } else {
      // Currently OFF → enable immediately
      setFeature(skill, featureKey as never, true as never)
    }
  }, [isActive, readOnly, skill, featureKey, setFeature])

  const handleConfirmDisable = useCallback(() => {
    setFeature(skill, featureKey as never, false as never)
    setConfirmOpen(false)
  }, [skill, featureKey, setFeature])

  const chipContent = (
    <button
      onClick={handleClick}
      disabled={readOnly}
      className={cn(
        'h-7 px-2.5 rounded-full text-xs font-medium flex items-center gap-1.5 border transition-all',
        isActive
          ? 'bg-primary/10 text-primary border-primary/20 hover:bg-primary/15'
          : 'bg-muted text-muted-foreground border-border hover:bg-muted/80',
        readOnly && 'cursor-default'
      )}
    >
      <Icon className="h-3 w-3" />
      <span>{displayValue ?? label}</span>
      {isActive && !readOnly && (
        <span className="h-1.5 w-1.5 rounded-full bg-primary ml-0.5" />
      )}
    </button>
  )

  if (readOnly) return chipContent

  return (
    <TooltipPrimitive.Provider delayDuration={0}>
      <TooltipPrimitive.Root open={confirmOpen} onOpenChange={setConfirmOpen}>
        <TooltipPrimitive.Trigger asChild>
          {chipContent}
        </TooltipPrimitive.Trigger>
        <TooltipPrimitive.Portal>
          <TooltipPrimitive.Content
            side="bottom"
            align="center"
            sideOffset={6}
            className="bg-card border border-border rounded-xl shadow-lg p-3 w-56 z-50"
          >
            <p className="text-xs font-semibold mb-1">⚠ Disable {label}?</p>
            <p className="text-xs text-muted-foreground mb-3">
              Data collected so far this session will still be submitted.
            </p>
            <div className="flex gap-2">
              <Button
                size="sm"
                variant="outline"
                className="flex-1 h-7 text-xs"
                onClick={() => setConfirmOpen(false)}
              >
                Cancel
              </Button>
              <Button
                size="sm"
                variant="destructive"
                className="flex-1 h-7 text-xs"
                onClick={handleConfirmDisable}
              >
                Disable
              </Button>
            </div>
            <TooltipPrimitive.Arrow className="fill-card" />
          </TooltipPrimitive.Content>
        </TooltipPrimitive.Portal>
      </TooltipPrimitive.Root>
    </TooltipPrimitive.Provider>
  )
}

// ─────────────────────────────────────────────
//  Chip Group (what pages actually import)
// ─────────────────────────────────────────────

export interface ChipConfig {
  featureKey: string
  label: string
  icon: LucideIcon
  readOnly?: boolean
  displayValue?: string
}

interface WorkspaceFeatureChipGroupProps {
  skill: keyof FeatureConfig
  chips: ChipConfig[]
  className?: string
}

export function WorkspaceFeatureChipGroup({ skill, chips, className }: WorkspaceFeatureChipGroupProps) {
  return (
    <div className={cn('flex items-center gap-1.5 flex-wrap', className)}>
      {chips.map((chip) => (
        <WorkspaceFeatureChip
          key={chip.featureKey}
          skill={skill}
          featureKey={chip.featureKey}
          label={chip.label}
          icon={chip.icon}
          readOnly={chip.readOnly}
          displayValue={chip.displayValue}
        />
      ))}
    </div>
  )
}
