/**
 * SentenceCanvas — read-only essay view for the Band Booster Scaffold.
 *
 * Renders each SentenceSeg as a colored <span>:
 *   - Active locked (current)  → red wavy underline, left highlight border
 *   - Locked not yet reached   → muted/dimmed
 *   - Unlocked (passed)        → green
 *   - Unevaluated              → normal foreground
 *
 * The canvas is pointer-events-none — students only type in SandboxEditor.
 * Uses framer-motion layout animation so color transitions are smooth.
 */
'use client'

import { motion } from 'framer-motion'
import { cn } from '@/lib/utils'
import { useWritingStore } from '@/lib/store/writingStore'

export function SentenceCanvas() {
  const { segmentedSentences, activeLockedIndex } = useWritingStore()

  if (!segmentedSentences.length) {
    return (
      <div className="h-full flex items-center justify-center text-sm text-muted-foreground italic p-6">
        Your essay will appear here sentence by sentence.
      </div>
    )
  }

  return (
    <div className="p-4 leading-loose text-sm pointer-events-none select-none">
      {segmentedSentences.map((seg, i) => {
        const isActive    = i === activeLockedIndex
        const isPast      = !seg.isLocked
        const isFuture    = seg.isLocked && i > (activeLockedIndex ?? -1)

        return (
          <motion.span
            key={i}
            layout
            transition={{ duration: 0.3 }}
            className={cn(
              'inline mr-1 rounded transition-colors duration-300',
              isPast   && 'text-green-600 dark:text-green-400',
              isFuture && 'text-muted-foreground opacity-50',
              isActive && [
                'text-destructive',
                'underline decoration-wavy decoration-destructive/60',
                'bg-destructive/5 px-0.5 py-0.5',
              ]
            )}
          >
            {seg.text}
          </motion.span>
        )
      })}
    </div>
  )
}
