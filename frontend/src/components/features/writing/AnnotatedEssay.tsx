'use client'

import { useState } from 'react'
import { cn } from '@/lib/utils'
import { AlertCircle, Lightbulb } from 'lucide-react'
import type { InlineCorrection } from '@/lib/services/writing'

// ─────────────────────────────────────────────
//  Props
// ─────────────────────────────────────────────

interface AnnotatedEssayProps {
  essay: string
  corrections: InlineCorrection[]
}

// ─────────────────────────────────────────────
//  Component
// ─────────────────────────────────────────────

export function AnnotatedEssay({ essay, corrections }: AnnotatedEssayProps) {
  const [hoveredIndex, setHoveredIndex] = useState<number | null>(null)

  if (!corrections || corrections.length === 0) {
    return (
      <div className="p-4 rounded-xl border bg-background text-sm leading-relaxed whitespace-pre-wrap">
        {essay}
      </div>
    )
  }

  // Sort corrections by position in essay (longest incorrect text first to avoid partial matches)
  const sortedCorrections = [...corrections].sort((a, b) => b.incorrect.length - a.incorrect.length)

  // Build annotated text by replacing corrections with highlighted spans
  const segments: Array<{
    text: string
    isCorrection: boolean
    correction?: InlineCorrection
    index?: number
  }> = []

  let remaining = essay

  for (const correction of sortedCorrections) {
    const idx = remaining.indexOf(correction.incorrect)
    if (idx === -1) continue

    // Add text before the correction
    if (idx > 0) {
      segments.push({ text: remaining.slice(0, idx), isCorrection: false })
    }

    // Add the correction
    segments.push({
      text: correction.incorrect,
      isCorrection: true,
      correction,
      index: corrections.indexOf(correction),
    })

    // Update remaining text
    remaining = remaining.slice(idx + correction.incorrect.length)
  }

  // Add any remaining text
  if (remaining.length > 0) {
    segments.push({ text: remaining, isCorrection: false })
  }

  const errorColors: Record<string, string> = {
    grammar: 'bg-destructive/15 border-destructive/30 text-destructive',
    vocabulary: 'bg-yellow-100 dark:bg-yellow-900/20 border-yellow-300 dark:border-yellow-700 text-yellow-800 dark:text-yellow-200',
    punctuation: 'bg-blue-100 dark:bg-blue-900/20 border-blue-300 dark:border-blue-700 text-blue-800 dark:text-blue-200',
    spelling: 'bg-purple-100 dark:bg-purple-900/20 border-purple-300 dark:border-purple-700 text-purple-800 dark:text-purple-200',
  }

  return (
    <div className="relative">
      <div className="p-4 rounded-xl border bg-background text-sm leading-relaxed whitespace-pre-wrap">
        {segments.map((seg, i) =>
          seg.isCorrection && seg.correction ? (
            <span
              key={i}
              className={cn(
                'relative px-0.5 rounded-sm border-b-2 cursor-pointer transition-all',
                errorColors[seg.correction.error_type] || errorColors.grammar,
                hoveredIndex === seg.index && 'ring-2 ring-ring'
              )}
              onMouseEnter={() => setHoveredIndex(seg.index!)}
              onMouseLeave={() => setHoveredIndex(null)}
            >
              <span className="line-through opacity-70">{seg.text}</span>
              <span className="ml-1 font-medium no-underline">{seg.correction.correct}</span>
            </span>
          ) : (
            <span key={i}>{seg.text}</span>
          )
        )}
      </div>

      {/* Tooltip for hovered correction */}
      {hoveredIndex !== null && corrections[hoveredIndex] && (
        <div className="absolute z-50 mt-1 p-3 rounded-lg bg-card border shadow-lg text-sm max-w-xs">
          <div className="flex items-start gap-2">
            {corrections[hoveredIndex].error_type === 'grammar' || corrections[hoveredIndex].error_type === 'spelling' || corrections[hoveredIndex].error_type === 'punctuation' ? (
              <AlertCircle className="h-4 w-4 text-destructive shrink-0 mt-0.5" />
            ) : (
              <Lightbulb className="h-4 w-4 text-yellow-500 shrink-0 mt-0.5" />
            )}
            <div>
              <p className="text-xs text-muted-foreground mb-1">
                {corrections[hoveredIndex].error_type}
              </p>
              <p className="text-xs">{corrections[hoveredIndex].explanation}</p>
            </div>
          </div>
        </div>
      )}
    </div>
  )
}
