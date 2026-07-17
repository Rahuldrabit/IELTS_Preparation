/**
 * SkillFeatureSection — collapsible card for one skill's feature toggles.
 */
'use client'

import { useState } from 'react'
import { motion, AnimatePresence } from 'framer-motion'
import { ChevronDown, type LucideIcon } from 'lucide-react'
import { Card, CardContent, CardHeader } from '@/components/ui/card'
import { cn } from '@/lib/utils'

// ─────────────────────────────────────────────
//  Props
// ─────────────────────────────────────────────

interface SkillFeatureSectionProps {
  title: string
  icon: LucideIcon
  accentColor: string         // Tailwind class, e.g. 'text-blue-500'
  accentBg: string            // e.g. 'bg-blue-500/10'
  children: React.ReactNode
  defaultOpen?: boolean
}

// ─────────────────────────────────────────────
//  Component
// ─────────────────────────────────────────────

export function SkillFeatureSection({
  title,
  icon: Icon,
  accentColor,
  accentBg,
  children,
  defaultOpen = true,
}: SkillFeatureSectionProps) {
  const [open, setOpen] = useState(defaultOpen)

  return (
    <Card>
      <CardHeader
        className="cursor-pointer select-none"
        onClick={() => setOpen((v) => !v)}
      >
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-3">
            <div className={cn('h-9 w-9 rounded-xl flex items-center justify-center', accentBg)}>
              <Icon className={cn('h-5 w-5', accentColor)} />
            </div>
            <span className="font-semibold">{title}</span>
          </div>
          <ChevronDown
            className={cn(
              'h-4 w-4 text-muted-foreground transition-transform duration-200',
              open && 'rotate-180'
            )}
          />
        </div>
      </CardHeader>

      <AnimatePresence initial={false}>
        {open && (
          <motion.div
            initial={{ height: 0, opacity: 0 }}
            animate={{ height: 'auto', opacity: 1 }}
            exit={{ height: 0, opacity: 0 }}
            transition={{ duration: 0.2 }}
          >
            <CardContent className="pt-0 space-y-2">
              {children}
            </CardContent>
          </motion.div>
        )}
      </AnimatePresence>
    </Card>
  )
}
