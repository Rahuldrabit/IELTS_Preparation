'use client'

import { useRef, useEffect, useCallback } from 'react'
import { motion } from 'framer-motion'
import { FileText, Highlighter, BookOpen, Volume2 } from 'lucide-react'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { cn } from '@/lib/utils'

// ─────────────────────────────────────────────
//  Props
// ─────────────────────────────────────────────

interface Paragraph {
  paragraph_id: string
  text: string
}

interface PassagePaneProps {
  title: string
  paragraphs: Paragraph[]
  highlightedParagraphId?: string | null
  onTextSelect?: (text: string) => void
  onParagraphEntered?: (paragraphId: string, timestamp: number) => void
  onParagraphExited?: (paragraphId: string, timestamp: number) => void
}

// ─────────────────────────────────────────────
//  Component
// ─────────────────────────────────────────────

export function PassagePane({
  title,
  paragraphs,
  highlightedParagraphId,
  onTextSelect,
  onParagraphEntered,
  onParagraphExited,
}: PassagePaneProps) {
  const paragraphRefs = useRef<Record<string, HTMLParagraphElement | null>>({})
  const entryTimestamps = useRef<Map<string, number>>(new Map())

  // Scroll to highlighted paragraph
  useEffect(() => {
    if (highlightedParagraphId && paragraphRefs.current[highlightedParagraphId]) {
      paragraphRefs.current[highlightedParagraphId]?.scrollIntoView({
        behavior: 'smooth',
        block: 'center',
      })
    }
  }, [highlightedParagraphId])

  // IntersectionObserver for paragraph visibility tracking
  useEffect(() => {
    if (!onParagraphEntered || !onParagraphExited) return

    const observer = new IntersectionObserver(
      (entries) => {
        const now = performance.now()
        entries.forEach((entry) => {
          const paragraphId = entry.target.getAttribute('data-paragraph-id')
          if (!paragraphId) return

          if (entry.isIntersecting && entry.intersectionRatio >= 0.5) {
            entryTimestamps.current.set(paragraphId, now)
            onParagraphEntered(paragraphId, now)
          } else if (!entry.isIntersecting) {
            const entryTime = entryTimestamps.current.get(paragraphId)
            if (entryTime) {
              onParagraphExited(paragraphId, now)
            }
          }
        })
      },
      { threshold: [0, 0.5, 1.0] }
    )

    const elements = Object.values(paragraphRefs.current)
    elements.forEach((el) => el && observer.observe(el))

    return () => observer.disconnect()
  }, [onParagraphEntered, onParagraphExited])

  // Handle text selection
  const handleMouseUp = () => {
    const selection = window.getSelection()
    if (selection && selection.toString().trim() && onTextSelect) {
      onTextSelect(selection.toString())
    }
  }

  return (
    <Card className="h-full">
      <CardHeader className="pb-3">
        <CardTitle className="text-base flex items-center gap-2">
          <FileText className="h-4 w-4" />
          Passage
        </CardTitle>
        <p className="text-sm text-muted-foreground">{title}</p>
      </CardHeader>
      <CardContent>
        <div
          className="prose prose-sm max-w-none leading-loose"
          onMouseUp={handleMouseUp}
        >
          {paragraphs.map((para) => (
            <p
              key={para.paragraph_id}
              ref={(el) => {
                paragraphRefs.current[para.paragraph_id] = el
              }}
              id={`paragraph-${para.paragraph_id}`}
              data-paragraph-id={para.paragraph_id}
              className={cn(
                'mb-4 text-foreground/90 transition-all duration-300',
                highlightedParagraphId === para.paragraph_id &&
                  'bg-amber-100 dark:bg-amber-900/30 -mx-2 px-2 py-1 rounded'
              )}
            >
              <span className="text-xs font-mono text-muted-foreground mr-2">
                [{para.paragraph_id}]
              </span>
              {para.text}
            </p>
          ))}
        </div>
      </CardContent>
    </Card>
  )
}

// ─────────────────────────────────────────────
//  Floating Toolbar for Text Selection
// ─────────────────────────────────────────────

interface TextSelectionToolbarProps {
  selectedText: string
  position: { x: number; y: number }
  onHighlight?: () => void
  onDictionary?: () => void
  onListen?: () => void
  onClose: () => void
}

export function TextSelectionToolbar({
  selectedText,
  position,
  onHighlight,
  onDictionary,
  onListen,
  onClose,
}: TextSelectionToolbarProps) {
  return (
    <motion.div
      initial={{ opacity: 0, y: 10 }}
      animate={{ opacity: 1, y: 0 }}
      exit={{ opacity: 0, y: 10 }}
      style={{
        position: 'fixed',
        left: position.x,
        top: position.y,
        transform: 'translate(-50%, -100%)',
      }}
      className="bg-card border border-border rounded-xl shadow-lg p-2 flex items-center gap-1 z-50"
    >
      <Button variant="ghost" size="sm" onClick={onHighlight}>
        <Highlighter className="h-4 w-4 mr-1" />
        Highlight
      </Button>
      <Button variant="ghost" size="sm" onClick={onDictionary}>
        <BookOpen className="h-4 w-4 mr-1" />
        Dictionary
      </Button>
      <Button variant="ghost" size="sm" onClick={onListen}>
        <Volume2 className="h-4 w-4 mr-1" />
        Listen
      </Button>
    </motion.div>
  )
}
