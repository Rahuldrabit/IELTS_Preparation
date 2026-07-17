/**
 * TrapAlertBadge — shows the adversarial trap type on a question card.
 *
 * Rendered inside QuestionSection when a question has a trap_type tag
 * in its question_evaluation metadata (set by AdversarialDistractorAgent).
 *
 * On first render, the badge is collapsed to just an icon.
 * Clicking it expands a tooltip explaining the trap.
 */
'use client'

import { useState } from 'react'
import { motion, AnimatePresence } from 'framer-motion'
import { ShieldAlert, ChevronDown } from 'lucide-react'
import { cn } from '@/lib/utils'
import { TRAP_LABELS } from '@/lib/services/reading-adversarial'

interface TrapAlertBadgeProps {
  trapType: string
  className?: string
}

export function TrapAlertBadge({ trapType, className }: TrapAlertBadgeProps) {
  const [expanded, setExpanded] = useState(false)
  const meta = TRAP_LABELS[trapType]

  if (!meta) return null

  return (
    <div className={cn('inline-block', className)}>
      <button
        onClick={() => setExpanded(v => !v)}
        className={cn(
          'flex items-center gap-1.5 px-2 py-0.5 rounded-full text-xs font-medium border transition-all',
          meta.color,
        )}
      >
        <ShieldAlert className="h-3 w-3 shrink-0" />
        <span>⚠ Trap: {meta.label}</span>
        <ChevronDown className={cn('h-3 w-3 transition-transform', expanded && 'rotate-180')} />
      </button>

      <AnimatePresence>
        {expanded && (
          <motion.div
            initial={{ opacity: 0, y: -4, height: 0 }}
            animate={{ opacity: 1, y: 0, height: 'auto' }}
            exit={{ opacity: 0, y: -4, height: 0 }}
            className="overflow-hidden"
          >
            <p className={cn(
              'mt-1.5 text-xs leading-relaxed px-2.5 py-2 rounded-lg border',
              meta.color,
            )}>
              {meta.description}
            </p>
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  )
}
