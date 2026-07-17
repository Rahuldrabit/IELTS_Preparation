/**
 * CouncilVerdict — displays the full Council of Judges breakdown.
 *
 * Shows the three sub-agent verdicts as expandable cards, then
 * the Chief Examiner's reconciliation and priority improvements.
 * Replaces the plain band score display when a council_report is present.
 */
'use client'

import { useState } from 'react'
import { motion, AnimatePresence } from 'framer-motion'
import {
  ChevronDown, BookOpen, Code2, GitBranch, Crown,
  CheckCircle2, AlertTriangle, TrendingUp, ArrowRight,
} from 'lucide-react'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Badge } from '@/components/ui/badge'
import { cn } from '@/lib/utils'
import type { CouncilReport } from '@/lib/services/writing'

// ─────────────────────────────────────────────
//  Helpers
// ─────────────────────────────────────────────

function bandColor(band: number): string {
  if (band >= 8)   return 'text-green-600 dark:text-green-400'
  if (band >= 7)   return 'text-blue-600 dark:text-blue-400'
  if (band >= 6)   return 'text-amber-600 dark:text-amber-400'
  return 'text-red-500'
}

function bandBg(band: number): string {
  if (band >= 8)   return 'bg-green-50 dark:bg-green-950/20 border-green-200 dark:border-green-800'
  if (band >= 7)   return 'bg-blue-50 dark:bg-blue-950/20 border-blue-200 dark:border-blue-800'
  if (band >= 6)   return 'bg-amber-50 dark:bg-amber-950/20 border-amber-200 dark:border-amber-800'
  return 'bg-red-50 dark:bg-red-950/20 border-red-200 dark:border-red-800'
}

// ─────────────────────────────────────────────
//  Sub-agent card
// ─────────────────────────────────────────────

function AgentCard({
  title, icon: Icon, band, color, children,
}: {
  title: string
  icon: React.ElementType
  band: number
  color: string
  children: React.ReactNode
}) {
  const [open, setOpen] = useState(false)

  return (
    <div className={cn('rounded-xl border p-4', bandBg(band))}>
      <button
        className="flex w-full items-center justify-between"
        onClick={() => setOpen((v) => !v)}
      >
        <div className="flex items-center gap-2">
          <Icon className={cn('h-4 w-4', color)} />
          <span className="font-medium text-sm">{title}</span>
        </div>
        <div className="flex items-center gap-3">
          <span className={cn('text-xl font-bold', bandColor(band))}>
            {band.toFixed(1)}
          </span>
          <ChevronDown className={cn(
            'h-4 w-4 text-muted-foreground transition-transform',
            open && 'rotate-180'
          )} />
        </div>
      </button>

      <AnimatePresence>
        {open && (
          <motion.div
            initial={{ height: 0, opacity: 0 }}
            animate={{ height: 'auto', opacity: 1 }}
            exit={{ height: 0, opacity: 0 }}
            transition={{ duration: 0.2 }}
            className="overflow-hidden"
          >
            <div className="pt-4 space-y-3">
              {children}
            </div>
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  )
}

// ─────────────────────────────────────────────
//  Tag list row
// ─────────────────────────────────────────────

function TagRow({ label, items, variant = 'default' }: {
  label: string
  items: string[]
  variant?: 'good' | 'warn' | 'default'
}) {
  if (!items.length) return null
  const tagClass = cn(
    'text-xs px-2 py-0.5 rounded-full border',
    variant === 'good'    && 'bg-green-100 dark:bg-green-900/30 text-green-700 dark:text-green-300 border-green-300',
    variant === 'warn'    && 'bg-red-100 dark:bg-red-900/30 text-red-700 dark:text-red-300 border-red-300',
    variant === 'default' && 'bg-muted text-muted-foreground border-border',
  )
  return (
    <div>
      <p className="text-xs text-muted-foreground mb-1.5">{label}</p>
      <div className="flex flex-wrap gap-1.5">
        {items.map((item, i) => (
          <span key={i} className={tagClass}>{item}</span>
        ))}
      </div>
    </div>
  )
}

// ─────────────────────────────────────────────
//  Main component
// ─────────────────────────────────────────────

interface CouncilVerdictProps {
  report: CouncilReport
}

export function CouncilVerdict({ report }: CouncilVerdictProps) {
  const { lexical, syntax, cohesion, chief } = report

  return (
    <div className="space-y-5">
      {/* Chief Examiner headline */}
      <div className={cn('rounded-xl border p-5', bandBg(chief.overall_band))}>
        <div className="flex items-center gap-3 mb-4">
          <div className="h-10 w-10 rounded-full bg-primary/10 flex items-center justify-center">
            <Crown className="h-5 w-5 text-primary" />
          </div>
          <div>
            <p className="font-semibold">Chief Examiner's Verdict</p>
            <p className="text-xs text-muted-foreground">Reconciled from 3 specialist agents</p>
          </div>
          <div className="ml-auto text-right">
            <p className="text-xs text-muted-foreground">Overall Band</p>
            <p className={cn('text-3xl font-bold', bandColor(chief.overall_band))}>
              {chief.overall_band.toFixed(1)}
            </p>
          </div>
        </div>

        {/* 4-criterion bar */}
        <div className="grid grid-cols-4 gap-2 text-center mb-4">
          {[
            { label: 'Task Response', val: chief.task_response },
            { label: 'Coherence',     val: chief.coherence },
            { label: 'Lexical',       val: chief.lexical },
            { label: 'Grammar',       val: chief.grammar },
          ].map(({ label, val }) => (
            <div key={label} className="p-2 rounded-lg bg-background/60">
              <p className={cn('text-lg font-bold', bandColor(val))}>{val.toFixed(1)}</p>
              <p className="text-[10px] text-muted-foreground leading-tight">{label}</p>
            </div>
          ))}
        </div>

        {/* Target band result */}
        <div className={cn(
          'flex items-center gap-2 p-2.5 rounded-lg text-sm',
          chief.meets_target_band
            ? 'bg-green-100 dark:bg-green-900/30 text-green-700 dark:text-green-400'
            : 'bg-amber-100 dark:bg-amber-900/30 text-amber-700 dark:text-amber-400'
        )}>
          {chief.meets_target_band
            ? <CheckCircle2 className="h-4 w-4 shrink-0" />
            : <AlertTriangle className="h-4 w-4 shrink-0" />
          }
          {chief.meets_target_band
            ? 'This essay meets your target band.'
            : 'This essay falls below your target band.'}
        </div>

        {/* Reconciliation note (shown only when meaningful) */}
        {chief.reconciliation_note && (
          <p className="mt-3 text-xs text-muted-foreground italic leading-relaxed">
            {chief.reconciliation_note}
          </p>
        )}
      </div>

      {/* Priority improvements */}
      {chief.priority_improvements.length > 0 && (
        <div className="space-y-2">
          <p className="text-sm font-medium flex items-center gap-2">
            <TrendingUp className="h-4 w-4 text-primary" />
            Top Improvements
          </p>
          {chief.priority_improvements.map((tip, i) => (
            <div key={i} className="flex items-start gap-2 p-3 rounded-xl bg-muted/50 text-sm">
              <ArrowRight className="h-3.5 w-3.5 mt-0.5 shrink-0 text-primary" />
              {tip}
            </div>
          ))}
        </div>
      )}

      {/* Sub-agent cards */}
      <div className="space-y-2">
        <p className="text-xs font-medium text-muted-foreground uppercase tracking-wider">
          Agent Breakdowns (click to expand)
        </p>

        {/* Lexical Tracker */}
        <AgentCard
          title="Lexical Tracker Agent"
          icon={BookOpen}
          band={lexical.band}
          color="text-purple-500"
        >
          <p className="text-xs text-muted-foreground">{lexical.explanation}</p>
          <TagRow label="Strong collocations"  items={lexical.strong_collocations} variant="good" />
          <TagRow label="Words to upgrade"     items={lexical.weak_vocabulary}      variant="warn" />
          <TagRow label="Overused words"        items={lexical.repetition_offenders} variant="warn" />
          <p className="text-xs text-muted-foreground">
            CEFR level detected: <strong>{lexical.cefr_level_detected}</strong>
          </p>
        </AgentCard>

        {/* Syntax Auditor */}
        <AgentCard
          title="Syntax Auditor Agent"
          icon={Code2}
          band={syntax.band}
          color="text-blue-500"
        >
          <p className="text-xs text-muted-foreground">{syntax.explanation}</p>
          <p className="text-xs text-muted-foreground">
            Dominant structure: <strong>{syntax.dominant_structure}</strong>
          </p>
          <TagRow label="Advanced structures found" items={syntax.advanced_structures_found} variant="good" />
          <TagRow label="Grammar errors"            items={syntax.grammar_errors}             variant="warn" />
        </AgentCard>

        {/* Rhetoric & Cohesion */}
        <AgentCard
          title="Rhetoric & Cohesion Agent"
          icon={GitBranch}
          band={cohesion.band}
          color="text-orange-500"
        >
          <p className="text-xs text-muted-foreground">{cohesion.explanation}</p>
          <p className="text-xs text-muted-foreground">
            Paragraph structure: <strong>{cohesion.paragraph_structure}</strong>
          </p>
          <TagRow label="Cohesive devices used" items={cohesion.cohesive_devices_used} variant="good" />
          <TagRow label="Logical gaps"           items={cohesion.logical_gaps}           variant="warn" />
        </AgentCard>
      </div>
    </div>
  )
}
