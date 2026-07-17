'use client'

import { useState, useEffect, useRef } from 'react'
import { motion } from 'framer-motion'
import { BookMarked, Loader2, Check, X } from 'lucide-react'
import { Button } from '@/components/ui/button'
import { vocabularyApi } from '@/lib/services/vocabulary'

interface VocabSelectionPopupProps {
  word: string
  position: { x: number; y: number }
  onClose: () => void
}

export function VocabSelectionPopup({ word, position, onClose }: VocabSelectionPopupProps) {
  const [status, setStatus] = useState<'idle' | 'saving' | 'saved' | 'error'>('idle')
  const [errorMsg, setErrorMsg] = useState('')
  const popupRef = useRef<HTMLDivElement>(null)

  // Close on click outside
  useEffect(() => {
    const handleClick = (e: MouseEvent) => {
      if (popupRef.current && !popupRef.current.contains(e.target as Node)) {
        onClose()
      }
    }
    const handleEscape = (e: KeyboardEvent) => {
      if (e.key === 'Escape') onClose()
    }
    document.addEventListener('mousedown', handleClick)
    document.addEventListener('keydown', handleEscape)
    return () => {
      document.removeEventListener('mousedown', handleClick)
      document.removeEventListener('keydown', handleEscape)
    }
  }, [onClose])

  const handleAdd = async () => {
    setStatus('saving')
    try {
      await vocabularyApi.addWord(word)
      setStatus('saved')
      setTimeout(onClose, 1200)
    } catch (err) {
      const msg = err instanceof Error ? err.message : 'Failed to add'
      if (msg.includes('already')) {
        setErrorMsg('Already in vocabulary')
      } else {
        setErrorMsg(msg)
      }
      setStatus('error')
      setTimeout(onClose, 2000)
    }
  }

  return (
    <motion.div
      ref={popupRef}
      initial={{ opacity: 0, y: 8, scale: 0.95 }}
      animate={{ opacity: 1, y: 0, scale: 1 }}
      exit={{ opacity: 0, y: 8, scale: 0.95 }}
      transition={{ duration: 0.15 }}
      style={{
        position: 'fixed',
        left: Math.min(position.x, window.innerWidth - 200),
        top: Math.max(position.y - 50, 10),
        zIndex: 9999,
      }}
      className="bg-card border border-border rounded-xl shadow-xl p-2 flex items-center gap-2"
    >
      {status === 'idle' && (
        <>
          <Button
            variant="ghost"
            size="sm"
            className="h-8 px-3 gap-1.5 text-sm"
            onClick={handleAdd}
          >
            <BookMarked className="h-3.5 w-3.5" />
            Add &quot;{word.length > 15 ? word.slice(0, 15) + '…' : word}&quot; to Vocabulary
          </Button>
          <Button variant="ghost" size="icon" className="h-6 w-6" onClick={onClose}>
            <X className="h-3 w-3" />
          </Button>
        </>
      )}
      {status === 'saving' && (
        <div className="flex items-center gap-2 px-3 py-1 text-sm text-muted-foreground">
          <Loader2 className="h-3.5 w-3.5 animate-spin" />
          Saving...
        </div>
      )}
      {status === 'saved' && (
        <div className="flex items-center gap-2 px-3 py-1 text-sm text-green-600">
          <Check className="h-3.5 w-3.5" />
          Added to vocabulary!
        </div>
      )}
      {status === 'error' && (
        <div className="flex items-center gap-2 px-3 py-1 text-sm text-destructive">
          <X className="h-3.5 w-3.5" />
          {errorMsg}
        </div>
      )}
    </motion.div>
  )
}
