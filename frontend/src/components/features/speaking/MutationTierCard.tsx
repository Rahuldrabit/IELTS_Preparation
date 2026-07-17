/**
 * MutationTierCard — displays one language mutation tier as a selectable card.
 *
 * Shows: band badge, upgraded text, 3 key-change bullets,
 * a "▶ Hear Reference" TTS button, and a "Practice This" select button.
 */
'use client'

import { useCallback } from 'react'
import { motion } from 'framer-motion'
import { Play, ArrowRight, CheckCircle2 } from 'lucide-react'
import { Card, CardContent, CardHeader } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Badge } from '@/components/ui/badge'
import { cn } from '@/lib/utils'
import { useSpeechSynthesis } from '@/lib/hooks/useSpeechSynthesis'
import type { MutationTier } from '@/lib/services/speaking'

// ─────────────────────────────────────────────
//  Band colour map
// ─────────────────────────────────────────────

const BAND_COLORS: Record<number, string> = {
  6.5: 'bg-blue-100 text-blue-700 dark:bg-blue-900/40 dark:text-blue-300 border-blue-300 dark:border-blue-700',
  7.5: 'bg-purple-100 text-purple-700 dark:bg-purple-900/40 dark:text-purple-300 border-purple-300 dark:border-purple-700',
  8.5: 'bg-amber-100 text-amber-700 dark:bg-amber-900/40 dark:text-amber-300 border-amber-300 dark:border-amber-700',
}

// ─────────────────────────────────────────────
//  Props
// ─────────────────────────────────────────────

interface MutationTierCardProps {
  tier: MutationTier
  selected: boolean
  onSelect: () => void
}

// ─────────────────────────────────────────────
//  Component
// ─────────────────────────────────────────────

export function MutationTierCard({ tier, selected, onSelect }: MutationTierCardProps) {
  const tts = useSpeechSynthesis()

  const handleHear = useCallback(() => {
    if (tts.isPlaying) {
      tts.stop()
    } else {
      tts.speak(tier.text, { lang: 'en-GB', rate: 0.9 })
    }
  }, [tts, tier.text])

  const badgeClass = BAND_COLORS[tier.target_band] ?? 'bg-muted text-muted-foreground'

  return (
    <motion.div
      whileHover={{ y: -2 }}
      transition={{ duration: 0.15 }}
    >
      <Card className={cn(
        'h-full flex flex-col cursor-pointer transition-all duration-200',
        selected
          ? 'border-primary bg-primary/5 shadow-md ring-1 ring-primary/30'
          : 'hover:border-primary/40 hover:shadow-sm'
      )}>
        <CardHeader className="pb-3">
          {/* Band badge */}
          <div className="flex items-center justify-between">
            <Badge variant="outline" className={cn('text-xs font-semibold', badgeClass)}>
              {tier.band_label}
            </Badge>
            {selected && <CheckCircle2 className="h-4 w-4 text-primary" />}
          </div>
        </CardHeader>

        <CardContent className="flex flex-col gap-4 flex-1">
          {/* Upgraded response text */}
          <p className="text-sm leading-relaxed flex-1">
            {tier.text}
          </p>

          {/* Key changes */}
          <ul className="space-y-1">
            {tier.key_changes.map((change, i) => (
              <li key={i} className="flex items-start gap-1.5 text-xs text-muted-foreground">
                <ArrowRight className="h-3 w-3 mt-0.5 shrink-0 text-primary/60" />
                {change}
              </li>
            ))}
          </ul>

          {/* Audio hint */}
          {tier.audio_hints && (
            <p className="text-xs text-muted-foreground italic border-l-2 border-primary/30 pl-2">
              {tier.audio_hints}
            </p>
          )}

          {/* Actions */}
          <div className="flex gap-2 mt-auto">
            <Button
              variant="outline"
              size="sm"
              className="flex-1 gap-1.5"
              onClick={handleHear}
            >
              <Play className="h-3.5 w-3.5" />
              {tts.isPlaying ? 'Stop' : 'Hear'}
            </Button>
            <Button
              size="sm"
              className="flex-1"
              onClick={onSelect}
              variant={selected ? 'default' : 'outline'}
            >
              {selected ? 'Selected' : 'Practice This'}
            </Button>
          </div>
        </CardContent>
      </Card>
    </motion.div>
  )
}
