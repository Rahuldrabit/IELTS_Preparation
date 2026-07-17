/**
 * SocraticHintPanel — multi-turn Socratic Debugging Agent UI.
 *
 * Appears below a wrong-answer card in ReviewPanel when the student
 * clicks "Guide me to the answer". Runs an interactive dialogue
 * without ever revealing the correct answer directly.
 *
 * Conversation loop:
 *   1. Agent asks a guiding question (hint_level 1–3)
 *   2. Student types their reasoning
 *   3. Agent evaluates cognitive shift, responds or confirms breakthrough
 *   4. On breakthrough_confirmed → celebrates + shows a "See answer" button
 *   5. On next_action === "reveal_answer" → shows the answer with explanation
 */
'use client'

import { useState, useRef, useEffect, useCallback } from 'react'
import { motion, AnimatePresence } from 'framer-motion'
import { Brain, Send, Loader2, CheckCircle2, ChevronDown, Lightbulb } from 'lucide-react'
import { Button } from '@/components/ui/button'
import { cn } from '@/lib/utils'
import { socraticApi, type SocraticTurn, type SocraticHintRequest } from '@/lib/services/reading-socratic'
import type { QuestionExplanation } from '@/lib/services/reading'

// ─────────────────────────────────────────────
//  Props
// ─────────────────────────────────────────────

interface SocraticHintPanelProps {
  result: QuestionExplanation
  passageExcerpt: string        // Relevant paragraph text from the passage
  sessionId: number
}

// ─────────────────────────────────────────────
//  Bubble
// ─────────────────────────────────────────────

function Bubble({ role, text }: { role: 'agent' | 'student'; text: string }) {
  const isAgent = role === 'agent'
  return (
    <div className={cn('flex gap-2', isAgent ? 'justify-start' : 'justify-end')}>
      {isAgent && (
        <div className="h-7 w-7 rounded-full bg-primary/10 flex items-center justify-center shrink-0 mt-0.5">
          <Brain className="h-3.5 w-3.5 text-primary" />
        </div>
      )}
      <div className={cn(
        'max-w-[85%] rounded-xl px-3.5 py-2.5 text-sm leading-relaxed',
        isAgent
          ? 'bg-muted text-foreground rounded-tl-none'
          : 'bg-primary text-primary-foreground rounded-tr-none'
      )}>
        {text}
      </div>
    </div>
  )
}

// ─────────────────────────────────────────────
//  Component
// ─────────────────────────────────────────────

export function SocraticHintPanel({ result, passageExcerpt, sessionId }: SocraticHintPanelProps) {
  const [open, setOpen]         = useState(false)
  const [started, setStarted]   = useState(false)
  const [isLoading, setLoading] = useState(false)
  const [input, setInput]       = useState('')
  const [revealAnswer, setRevealAnswer] = useState(false)

  const [turns, setTurns]     = useState<SocraticTurn[]>([])
  const [lastResponse, setLastResponse] = useState<Awaited<ReturnType<typeof socraticApi.getHint>> | null>(null)

  const bottomRef = useRef<HTMLDivElement>(null)

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [turns, isLoading])

  const sendRequest = useCallback(async (studentReply?: string) => {
    setLoading(true)

    const updatedHistory: SocraticTurn[] = studentReply
      ? [...turns, { role: 'student', text: studentReply }]
      : turns

    const request: SocraticHintRequest = {
      question_text:        result.question_id.toString() + ': ' + result.user_answer,
      correct_answer:       result.correct_answer,
      user_answer:          result.user_answer,
      passage_excerpt:      passageExcerpt,
      question_type:        result.mistake_type ?? 'TRUE_FALSE_NOT_GIVEN',
      conversation_history: updatedHistory,
    }

    try {
      const res = await socraticApi.getHint(sessionId, request)
      setLastResponse(res)

      const newTurns: SocraticTurn[] = [
        ...updatedHistory,
        { role: 'agent', text: res.hint_text },
      ]
      setTurns(newTurns)
    } catch {
      setTurns((prev) => [
        ...prev,
        { role: 'agent', text: 'Sorry, I had trouble generating a hint. Please try again.' },
      ])
    } finally {
      setLoading(false)
    }
  }, [turns, result, passageExcerpt, sessionId])

  const handleStart = useCallback(() => {
    setStarted(true)
    sendRequest()
  }, [sendRequest])

  const handleSend = useCallback(() => {
    if (!input.trim() || isLoading) return
    const reply = input.trim()
    setInput('')
    sendRequest(reply)
  }, [input, isLoading, sendRequest])

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && !e.shiftKey) { e.preventDefault(); handleSend() }
  }

  const breakthrough = lastResponse?.breakthrough_confirmed
  const needsReveal  = lastResponse?.next_action === 'reveal_answer'

  return (
    <div className="mt-3">
      {/* Toggle button */}
      <button
        onClick={() => { setOpen((v) => !v); if (!started && !open) handleStart() }}
        className="flex items-center gap-2 text-sm text-primary hover:text-primary/80 transition-colors font-medium"
      >
        <Brain className="h-4 w-4" />
        Guide me to the answer
        <ChevronDown className={cn('h-3.5 w-3.5 transition-transform', open && 'rotate-180')} />
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
            <div className="mt-3 rounded-xl border bg-card overflow-hidden">
              {/* Header */}
              <div className="flex items-center gap-2 px-4 py-3 border-b bg-muted/30">
                <Brain className="h-4 w-4 text-primary" />
                <span className="text-sm font-medium">Uma — Socratic Tutor</span>
                {lastResponse && (
                  <span className="ml-auto text-xs text-muted-foreground">
                    Hint {lastResponse.hint_level} of 3
                  </span>
                )}
              </div>

              {/* Conversation */}
              <div className="p-4 space-y-3 max-h-72 overflow-y-auto">
                {!started && (
                  <p className="text-sm text-muted-foreground text-center py-4">
                    I will guide you to the answer through questions — without telling you directly.
                  </p>
                )}

                {turns.map((turn, i) => (
                  <Bubble key={i} role={turn.role} text={turn.text} />
                ))}

                {isLoading && (
                  <div className="flex items-center gap-2 text-muted-foreground text-sm">
                    <Loader2 className="h-3.5 w-3.5 animate-spin" />
                    Uma is thinking…
                  </div>
                )}

                {/* Breakthrough banner */}
                {breakthrough && (
                  <motion.div
                    initial={{ opacity: 0, scale: 0.96 }}
                    animate={{ opacity: 1, scale: 1 }}
                    className="p-3 rounded-xl bg-green-50 dark:bg-green-950/30 border border-green-200 dark:border-green-800 flex items-center gap-2"
                  >
                    <CheckCircle2 className="h-5 w-5 text-green-500 shrink-0" />
                    <p className="text-sm text-green-700 dark:text-green-400 font-medium">
                      You found it! Your reasoning is correct.
                    </p>
                  </motion.div>
                )}

                {/* Reveal answer prompt */}
                {needsReveal && !revealAnswer && !breakthrough && (
                  <div className="text-center pt-1">
                    <Button
                      variant="outline"
                      size="sm"
                      className="text-xs gap-1.5"
                      onClick={() => setRevealAnswer(true)}
                    >
                      <Lightbulb className="h-3 w-3" />
                      Show me the answer
                    </Button>
                  </div>
                )}

                {revealAnswer && (
                  <div className="p-3 rounded-xl bg-blue-50 dark:bg-blue-950/30 border border-blue-200 dark:border-blue-800">
                    <p className="text-xs text-muted-foreground mb-1">Correct answer</p>
                    <p className="text-sm font-semibold text-blue-700 dark:text-blue-300">
                      {result.correct_answer}
                    </p>
                    {result.why_wrong && (
                      <p className="text-xs text-muted-foreground mt-2 leading-relaxed">
                        {result.why_wrong}
                      </p>
                    )}
                  </div>
                )}

                <div ref={bottomRef} />
              </div>

              {/* Input */}
              {!breakthrough && !revealAnswer && started && (
                <div className="flex items-center gap-2 p-3 border-t">
                  <input
                    type="text"
                    value={input}
                    onChange={(e) => setInput(e.target.value)}
                    onKeyDown={handleKeyDown}
                    placeholder="Share your reasoning…"
                    disabled={isLoading}
                    className="flex-1 text-sm bg-muted rounded-lg px-3 py-2 focus:outline-none focus:ring-1 focus:ring-ring disabled:opacity-50"
                  />
                  <Button
                    size="icon"
                    className="h-9 w-9 shrink-0"
                    onClick={handleSend}
                    disabled={!input.trim() || isLoading}
                  >
                    <Send className="h-4 w-4" />
                  </Button>
                </div>
              )}
            </div>
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  )
}
