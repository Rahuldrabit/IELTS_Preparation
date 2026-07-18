'use client'

import { useEffect } from 'react'
import { useRouter } from 'next/navigation'
import { motion } from 'framer-motion'
import { ArrowLeft, StickyNote, Trash2, AlertCircle, BookOpen } from 'lucide-react'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Badge } from '@/components/ui/badge'
import { useGrammarStore } from '@/lib/store/grammarStore'

export default function GrammarNotesPage() {
  const router = useRouter()
  const { notes, isLoading, fetchGrammarNotes, dismissNote } = useGrammarStore()

  useEffect(() => {
    fetchGrammarNotes()
  }, [fetchGrammarNotes])

  const visibleNotes = notes.filter(n => !n.is_dismissed)

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center gap-4">
        <Button variant="ghost" size="icon" onClick={() => router.push('/practice/grammar')}>
          <ArrowLeft className="h-4 w-4" />
        </Button>
        <div>
          <h1 className="text-2xl font-bold flex items-center gap-2">
            <StickyNote className="h-6 w-6 text-amber-500" />
            Grammar Notes
          </h1>
          <p className="text-muted-foreground">
            Auto-generated notes from your repeated mistakes
          </p>
        </div>
      </div>

      {isLoading ? (
        <div className="flex items-center justify-center h-32">
          <BookOpen className="h-6 w-6 text-primary animate-pulse" />
        </div>
      ) : visibleNotes.length === 0 ? (
        <Card>
          <CardContent className="p-8 text-center">
            <StickyNote className="h-12 w-12 text-muted-foreground mx-auto mb-3" />
            <h3 className="font-medium mb-1">No grammar notes yet</h3>
            <p className="text-sm text-muted-foreground">
              Notes are auto-generated when you make 3 or more mistakes in the same grammar category.
              Keep practicing and notes will appear here!
            </p>
          </CardContent>
        </Card>
      ) : (
        <div className="space-y-4">
          {visibleNotes.map((note, idx) => (
            <motion.div
              key={note.id}
              initial={{ opacity: 0, y: 10 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ delay: idx * 0.05 }}
            >
              <Card className="border-amber-500/20">
                <CardContent className="p-5">
                  <div className="flex items-start justify-between gap-4">
                    <div className="flex items-start gap-3 flex-1">
                      <AlertCircle className="h-5 w-5 text-amber-500 shrink-0 mt-0.5" />
                      <div className="space-y-2 flex-1">
                        <div className="flex items-center gap-2">
                          <h3 className="font-medium">{note.title}</h3>
                          <Badge variant="outline" className="text-xs">
                            {new Date(note.created_at).toLocaleDateString()}
                          </Badge>
                        </div>
                        <p className="text-sm text-muted-foreground whitespace-pre-line">{note.content}</p>
                        
                        {note.mistake_pattern && (
                          <div className="p-2 rounded-lg bg-destructive/5 border border-destructive/10">
                            <p className="text-xs text-muted-foreground">Mistake pattern:</p>
                            <p className="text-sm text-destructive">{note.mistake_pattern}</p>
                          </div>
                        )}
                        
                        {note.correction && (
                          <div className="p-2 rounded-lg bg-success/5 border border-success/10">
                            <p className="text-xs text-muted-foreground">Correction:</p>
                            <p className="text-sm text-green-700 dark:text-green-400">{note.correction}</p>
                          </div>
                        )}
                      </div>
                    </div>
                    <Button
                      variant="ghost"
                      size="icon"
                      onClick={() => dismissNote(note.id)}
                      className="shrink-0"
                    >
                      <Trash2 className="h-4 w-4 text-muted-foreground" />
                    </Button>
                  </div>
                </CardContent>
              </Card>
            </motion.div>
          ))}
        </div>
      )}
    </div>
  )
}