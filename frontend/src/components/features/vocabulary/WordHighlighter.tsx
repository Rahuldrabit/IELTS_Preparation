'use client'

import { useState, useCallback } from 'react'
import { motion, AnimatePresence } from 'framer-motion'
import { Bookmark, Check, Loader2, X } from 'lucide-react'
import { Button } from '@/components/ui/button'
import { cn } from '@/lib/utils'
import { vocabularyApi } from '@/lib/services/vocabulary'

interface WordHighlighterProps {
  text: string
  sourceType: 'reading' | 'listening'
  sourceId?: number
  paragraphIndex?: number
  onWordHarvested?: (word: string) => void
  savedWords?: Set<string>
  className?: string
}

interface WordPopup {
  word: string
  x: number
  y: number
  saving: boolean
  saved: boolean
}

export function WordHighlighter({
  text,
  sourceType,
  sourceId,
  paragraphIndex,
  onWordHarvested,
  savedWords = new Set(),
  className,
}: WordHighlighterProps) {
  const [popup, setPopup] = useState<WordPopup | null>(null)
  const [hoveredWord, setHoveredWord] = useState<string | null>(null)
  
  const handleWordClick = useCallback((word: string, event: React.MouseEvent) => {
    event.stopPropagation()
    
    // Position popup near the clicked word
    const rect = (event.target as HTMLElement).getBoundingClientRect()
    setPopup({
      word,
      x: rect.left + rect.width / 2,
      y: rect.top - 10,
      saving: false,
      saved: savedWords.has(word.toLowerCase()),
    })
  }, [savedWords])
  
  const handleSaveWord = async () => {
    if (!popup || popup.saving || popup.saved) return
    
    setPopup(prev => prev ? { ...prev, saving: true } : null)
    
    try {
      // Get context sentence (find the sentence containing this word)
      const sentence = getSentenceContaining(text, popup.word)
      
      await vocabularyApi.harvestWord({
        word: popup.word,
        context_sentence: sentence,
        source_type: sourceType,
        source_id: sourceId,
        paragraph_index: paragraphIndex,
      })
      
      setPopup(prev => prev ? { ...prev, saving: false, saved: true } : null)
      
      if (onWordHarvested) {
        onWordHarvested(popup.word)
      }
      
      // Auto-close after success
      setTimeout(() => setPopup(null), 1500)
      
    } catch (error) {
      console.error('Failed to save word:', error)
      setPopup(prev => prev ? { ...prev, saving: false } : null)
    }
  }
  
  const closePopup = () => {
    setPopup(null)
  }
  
  // Tokenize text into words and spaces
  const tokens = tokenizeText(text)
  
  return (
    <div className={cn('relative', className)}>
      <div className="leading-relaxed">
        {tokens.map((token, i) => {
          if (token.type === 'word') {
            const isSaved = savedWords.has(token.text.toLowerCase())
            const isHovered = hoveredWord === token.text.toLowerCase()
            
            return (
              <span
                key={i}
                className={cn(
                  'cursor-pointer transition-colors rounded px-0.5',
                  isSaved && 'bg-green-500/20 text-green-700',
                  !isSaved && isHovered && 'bg-primary/20',
                  !isSaved && !isHovered && 'hover:bg-primary/10'
                )}
                onClick={(e) => handleWordClick(token.text, e)}
                onMouseEnter={() => setHoveredWord(token.text.toLowerCase())}
                onMouseLeave={() => setHoveredWord(null)}
              >
                {token.text}
              </span>
            )
          } else {
            return <span key={i}>{token.text}</span>
          }
        })}
      </div>
      
      {/* Popup */}
      <AnimatePresence>
        {popup && (
          <motion.div
            initial={{ opacity: 0, y: 10, scale: 0.95 }}
            animate={{ opacity: 1, y: 0, scale: 1 }}
            exit={{ opacity: 0, y: 10, scale: 0.95 }}
            className="fixed z-50"
            style={{
              left: popup.x,
              top: popup.y,
              transform: 'translate(-50%, -100%)',
            }}
          >
            <div className="bg-white dark:bg-gray-800 rounded-lg shadow-lg border p-3 min-w-[150px]">
              <div className="flex items-center justify-between mb-2">
                <span className="font-medium text-sm capitalize">{popup.word}</span>
                <button
                  onClick={closePopup}
                  className="text-muted-foreground hover:text-foreground"
                >
                  <X className="h-4 w-4" />
                </button>
              </div>
              
              {popup.saved ? (
                <div className="flex items-center gap-2 text-green-600">
                  <Check className="h-4 w-4" />
                  <span className="text-sm">Saved!</span>
                </div>
              ) : (
                <Button
                  size="sm"
                  className="w-full"
                  onClick={handleSaveWord}
                  disabled={popup.saving}
                >
                  {popup.saving ? (
                    <>
                      <Loader2 className="h-3 w-3 mr-1 animate-spin" />
                      Saving...
                    </>
                  ) : (
                    <>
                      <Bookmark className="h-3 w-3 mr-1" />
                      Save to Deck
                    </>
                  )}
                </Button>
              )}
            </div>
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  )
}

// Helper to tokenize text into words and non-words
function tokenizeText(text: string): Array<{ type: 'word' | 'other'; text: string }> {
  const tokens: Array<{ type: 'word' | 'other'; text: string }> = []
  const regex = /(\b[a-zA-Z'-]+\b|[^a-zA-Z]+)/g
  let match
  
  while ((match = regex.exec(text)) !== null) {
    const isWord = /^[a-zA-Z'-]+$/.test(match[0])
    tokens.push({
      type: isWord ? 'word' : 'other',
      text: match[0],
    })
  }
  
  return tokens
}

// Helper to extract sentence containing a word
function getSentenceContaining(text: string, word: string): string {
  const sentences = text.split(/[.!?]+/)
  const lowerWord = word.toLowerCase()
  
  for (const sentence of sentences) {
    if (sentence.toLowerCase().includes(lowerWord)) {
      return sentence.trim()
    }
  }
  
  // Fallback: return surrounding context
  const index = text.toLowerCase().indexOf(lowerWord)
  if (index === -1) return text.slice(0, 100)
  
  const start = Math.max(0, index - 50)
  const end = Math.min(text.length, index + word.length + 50)
  return text.slice(start, end).trim()
}
