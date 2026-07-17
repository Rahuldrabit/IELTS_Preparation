'use client'

import { useState, useEffect, useCallback } from 'react'
import { motion, AnimatePresence } from 'framer-motion'
import { BookOpen, Search, Plus, Volume2, RotateCcw, Loader2 } from 'lucide-react'
import { Card, CardContent } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Badge } from '@/components/ui/badge'
import { cn } from '@/lib/utils'
import { staggerItem, staggerContainer } from '@/lib/animations'
import { vocabularyApi, type VocabularyCard, type VocabStats } from '@/lib/services/vocabulary'

const FILTERS = [
  { label: 'All', value: 'all' },
  { label: 'New', value: 'new' },
  { label: 'Learning', value: 'learning' },
  { label: 'Mastered', value: 'mastered' },
]

export default function VocabularyPage() {
  const [filter, setFilter] = useState('all')
  const [searchQuery, setSearchQuery] = useState('')
  const [words, setWords] = useState<VocabularyCard[]>([])
  const [stats, setStats] = useState<VocabStats | null>(null)
  const [loading, setLoading] = useState(true)
  const [flippedCards, setFlippedCards] = useState<Record<number, boolean>>({})
  const [reviewMode, setReviewMode] = useState(false)
  const [addingWord, setAddingWord] = useState(false)
  const [newWord, setNewWord] = useState('')

  // Fetch vocabulary from API
  const fetchWords = useCallback(async () => {
    try {
      const data = await vocabularyApi.getVocabulary({
        filter: filter !== 'all' ? filter : undefined,
        search: searchQuery || undefined,
      })
      setWords(data)
    } catch {
      // Silently fail — show empty state
      setWords([])
    }
  }, [filter, searchQuery])

  const fetchStats = useCallback(async () => {
    try {
      const data = await vocabularyApi.getStats()
      setStats(data)
    } catch {
      // ignore
    }
  }, [])

  useEffect(() => {
    setLoading(true)
    Promise.all([fetchWords(), fetchStats()]).finally(() => setLoading(false))
  }, [fetchWords, fetchStats])

  const toggleFlip = (wordId: number) => {
    setFlippedCards(prev => ({ ...prev, [wordId]: !prev[wordId] }))
  }

  const handleAddWord = async () => {
    if (!newWord.trim()) return
    setAddingWord(true)
    try {
      await vocabularyApi.addWord(newWord.trim())
      setNewWord('')
      fetchWords()
      fetchStats()
    } catch {
      // ignore
    } finally {
      setAddingWord(false)
    }
  }

  const handleReview = async (wordId: number, correct: boolean) => {
    try {
      await vocabularyApi.reviewWord(wordId, correct)
      fetchWords()
      fetchStats()
    } catch {
      // ignore
    }
  }

  if (loading) {
    return (
      <div className="flex items-center justify-center py-20">
        <Loader2 className="h-8 w-8 animate-spin text-primary" />
      </div>
    )
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <motion.div
        initial={{ opacity: 0, y: -20 }}
        animate={{ opacity: 1, y: 0 }}
        className="flex items-center justify-between"
      >
        <div>
          <h1 className="text-3xl font-bold mb-2">Vocabulary</h1>
          <p className="text-muted-foreground">
            Build your IELTS vocabulary with flashcards and spaced repetition
          </p>
        </div>
        <div className="flex gap-3">
          <Button
            variant={reviewMode ? 'default' : 'outline'}
            onClick={() => setReviewMode(!reviewMode)}
          >
            <RotateCcw className="h-4 w-4 mr-2" />
            Review Mode
          </Button>
        </div>
      </motion.div>

      {/* Add word + Filters and Search */}
      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ delay: 0.1 }}
      >
        <Card>
          <CardContent className="p-4 space-y-3">
            {/* Add word row */}
            <div className="flex gap-2">
              <Input
                placeholder="Add a new word..."
                value={newWord}
                onChange={(e) => setNewWord(e.target.value)}
                onKeyDown={(e) => e.key === 'Enter' && handleAddWord()}
                className="flex-1"
              />
              <Button onClick={handleAddWord} disabled={addingWord || !newWord.trim()}>
                {addingWord ? <Loader2 className="h-4 w-4 animate-spin" /> : <Plus className="h-4 w-4 mr-1" />}
                Add
              </Button>
            </div>
            {/* Search + filter row */}
            <div className="flex flex-col md:flex-row gap-4">
              <div className="relative flex-1">
                <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-muted-foreground" />
                <Input
                  placeholder="Search words..."
                  value={searchQuery}
                  onChange={(e) => setSearchQuery(e.target.value)}
                  className="pl-10"
                />
              </div>
              <div className="flex gap-2">
                {FILTERS.map((f) => (
                  <Button
                    key={f.value}
                    variant={filter === f.value ? 'default' : 'outline'}
                    size="sm"
                    onClick={() => setFilter(f.value)}
                  >
                    {f.label}
                  </Button>
                ))}
              </div>
            </div>
          </CardContent>
        </Card>
      </motion.div>

      {/* Stats */}
      {stats && (
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.2 }}
          className="grid grid-cols-3 gap-4"
        >
          <Card>
            <CardContent className="p-4 text-center">
              <p className="text-2xl font-bold text-primary">{stats.new}</p>
              <p className="text-sm text-muted-foreground">New Words</p>
            </CardContent>
          </Card>
          <Card>
            <CardContent className="p-4 text-center">
              <p className="text-2xl font-bold text-yellow-500">{stats.learning}</p>
              <p className="text-sm text-muted-foreground">Learning</p>
            </CardContent>
          </Card>
          <Card>
            <CardContent className="p-4 text-center">
              <p className="text-2xl font-bold text-green-500">{stats.mastered}</p>
              <p className="text-sm text-muted-foreground">Mastered</p>
            </CardContent>
          </Card>
        </motion.div>
      )}

      {/* Flashcards Grid */}
      <motion.div
        variants={staggerContainer}
        initial="initial"
        animate="animate"
        className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6"
      >
        <AnimatePresence mode="popLayout">
          {words.map((word) => (
            <motion.div
              key={word.id}
              variants={staggerItem}
              initial="initial"
              animate="animate"
              exit="exit"
              className="card-flip-container h-64 cursor-pointer"
              onClick={() => !reviewMode && toggleFlip(word.id)}
            >
              <div className={cn(
                "card-flip w-full h-full relative",
                flippedCards[word.id] && "flipped"
              )}>
                {/* Front */}
                <div className="card-front absolute inset-0">
                  <Card className="h-full">
                    <CardContent className="p-6 flex flex-col h-full">
                      <div className="flex items-start justify-between mb-4">
                        <Badge
                          variant={
                            word.mastery === 'new' ? 'default' :
                            word.mastery === 'learning' ? 'secondary' : 'outline'
                          }
                        >
                          {word.mastery}
                        </Badge>
                        {word.cefr && <Badge variant="outline">{word.cefr}</Badge>}
                      </div>

                      <div className="flex-1 flex flex-col items-center justify-center">
                        <h3 className="text-2xl font-bold mb-2">{word.word}</h3>
                        {word.pronunciation && (
                          <p className="text-sm text-muted-foreground mb-2">{word.pronunciation}</p>
                        )}
                        {word.meaning && (
                          <p className="text-sm text-center text-muted-foreground">{word.meaning}</p>
                        )}
                      </div>

                      {reviewMode ? (
                        <div className="flex gap-2 mt-4">
                          <Button
                            variant="outline"
                            size="sm"
                            className="flex-1 text-destructive"
                            onClick={(e) => { e.stopPropagation(); handleReview(word.id, false) }}
                          >
                            Forgot
                          </Button>
                          <Button
                            size="sm"
                            className="flex-1"
                            onClick={(e) => { e.stopPropagation(); handleReview(word.id, true) }}
                          >
                            Got it
                          </Button>
                        </div>
                      ) : (
                        <div className="flex items-center justify-center gap-2 mt-4">
                          <Button variant="ghost" size="icon" className="h-8 w-8">
                            <Volume2 className="h-4 w-4" />
                          </Button>
                          <span className="text-xs text-muted-foreground">Click to flip</span>
                        </div>
                      )}
                    </CardContent>
                  </Card>
                </div>

                {/* Back */}
                <div className="card-back absolute inset-0">
                  <Card className="h-full bg-primary text-primary-foreground">
                    <CardContent className="p-6 overflow-y-auto h-full">
                      <div className="space-y-4">
                        {word.definition && (
                          <div>
                            <p className="text-xs text-primary-foreground/70 mb-1">Definition</p>
                            <p className="text-sm">{word.definition}</p>
                          </div>
                        )}

                        {word.examples.length > 0 && (
                          <div>
                            <p className="text-xs text-primary-foreground/70 mb-1">Examples</p>
                            <ul className="space-y-1">
                              {word.examples.slice(0, 2).map((ex, i) => (
                                <li key={i} className="text-sm italic">• {ex}</li>
                              ))}
                            </ul>
                          </div>
                        )}

                        {word.synonyms.length > 0 && (
                          <div>
                            <p className="text-xs text-primary-foreground/70 mb-1">Synonyms</p>
                            <div className="flex flex-wrap gap-1">
                              {word.synonyms.slice(0, 3).map((syn, i) => (
                                <Badge key={i} variant="secondary" className="text-xs">
                                  {syn}
                                </Badge>
                              ))}
                            </div>
                          </div>
                        )}

                        {word.collocations.length > 0 && (
                          <div>
                            <p className="text-xs text-primary-foreground/70 mb-1">Collocations</p>
                            <div className="flex flex-wrap gap-1">
                              {word.collocations.slice(0, 2).map((col, i) => (
                                <Badge key={i} variant="secondary" className="text-xs">
                                  {col}
                                </Badge>
                              ))}
                            </div>
                          </div>
                        )}
                      </div>
                    </CardContent>
                  </Card>
                </div>
              </div>
            </motion.div>
          ))}
        </AnimatePresence>
      </motion.div>

      {words.length === 0 && !loading && (
        <div className="text-center py-12">
          <BookOpen className="h-12 w-12 mx-auto text-muted-foreground mb-4" />
          <p className="text-muted-foreground">No words found. Add some vocabulary to get started!</p>
        </div>
      )}
    </div>
  )
}
