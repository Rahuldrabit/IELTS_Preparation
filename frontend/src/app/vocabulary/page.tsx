'use client'

import { useState, useEffect } from 'react'
import { motion, AnimatePresence } from 'framer-motion'
import { vocabularyApi } from '@/lib/services/vocabulary'
import {
  BookOpen,
  Search,
  Filter,
  Bookmark,
  Check,
  X,
  RotateCcw,
  ChevronRight,
  Volume2,
  Loader2,
  Clock,
} from 'lucide-react'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Badge } from '@/components/ui/badge'
import { Progress } from '@/components/ui/progress'
import { cn } from '@/lib/utils'

interface VocabWord {
  id: number
  word: string
  context_sentence?: string
  source_type?: string
  pronunciation?: string
  definition?: string
  ai_definition?: string
  examples: string[]
  synonyms: string[]
  saved_at?: string
  mastery: string
  next_review?: string
}

interface VocabStats {
  new: number
  learning: number
  mastered: number
  total: number
}

export default function VocabularyPage() {
  const [words, setWords] = useState<VocabWord[]>([])
  const [stats, setStats] = useState<VocabStats | null>(null)
  const [loading, setLoading] = useState(true)
  const [filter, setFilter] = useState<'all' | 'new' | 'learning' | 'mastered'>('all')
  const [search, setSearch] = useState('')
  const [reviewMode, setReviewMode] = useState(false)
  const [currentReviewIndex, setCurrentReviewIndex] = useState(0)
  const [showDefinition, setShowDefinition] = useState(false)
  
  useEffect(() => {
    loadVocabulary()
    loadStats()
  }, [filter, search])
  
  const loadVocabulary = async () => {
    setLoading(true)
    try {
      const response = await vocabularyApi.getVocabulary({ filter, search })
      setWords(response)
    } catch (error) {
      console.error('Failed to load vocabulary:', error)
    } finally {
      setLoading(false)
    }
  }
  
  const loadStats = async () => {
    try {
      const data = await vocabularyApi.getStats()
      setStats(data)
    } catch (error) {
      console.error('Failed to load stats:', error)
    }
  }
  
  const startReview = async () => {
    try {
      const dueWords = await vocabularyApi.getDueVocabulary()
      if (dueWords.length > 0) {
        setWords(dueWords)
        setReviewMode(true)
        setCurrentReviewIndex(0)
        setShowDefinition(false)
      }
    } catch (error) {
      console.error('Failed to load due words:', error)
    }
  }
  
  const submitReview = async (correct: boolean) => {
    if (!words[currentReviewIndex]) return
    
    try {
      await vocabularyApi.reviewWord(words[currentReviewIndex].id, correct)
      
      // Move to next word or end review
      if (currentReviewIndex < words.length - 1) {
        setCurrentReviewIndex(prev => prev + 1)
        setShowDefinition(false)
      } else {
        setReviewMode(false)
        loadVocabulary()
        loadStats()
      }
    } catch (error) {
      console.error('Failed to submit review:', error)
    }
  }
  
  const currentWord = reviewMode ? words[currentReviewIndex] : null
  
  return (
    <div className="container max-w-4xl mx-auto py-8 px-4">
      {/* Header */}
      <motion.div
        initial={{ opacity: 0, y: -20 }}
        animate={{ opacity: 1, y: 0 }}
        className="mb-8"
      >
        <div className="flex items-center gap-3 mb-2">
          <BookOpen className="h-8 w-8 text-indigo-500" />
          <h1 className="text-3xl font-bold">Vocabulary Deck</h1>
        </div>
        <p className="text-muted-foreground">
          Words you've saved from reading and listening practice
        </p>
      </motion.div>
      
      <AnimatePresence mode="wait">
        {/* Review Mode */}
        {reviewMode && currentWord ? (
          <motion.div
            key="review"
            initial={{ opacity: 0, x: 50 }}
            animate={{ opacity: 1, x: 0 }}
            exit={{ opacity: 0, x: -50 }}
          >
            <Card className="min-h-[400px]">
              <CardHeader>
                <div className="flex items-center justify-between">
                  <CardTitle>Review: {currentReviewIndex + 1} of {words.length}</CardTitle>
                  <Button variant="ghost" size="sm" onClick={() => setReviewMode(false)}>
                    <X className="h-4 w-4 mr-1" />
                    Exit
                  </Button>
                </div>
                <Progress 
                  value={((currentReviewIndex + 1) / words.length) * 100} 
                  className="h-2 mt-2" 
                />
              </CardHeader>
              <CardContent className="py-8 text-center">
                {/* Word */}
                <motion.div
                  key={currentWord.id}
                  initial={{ opacity: 0, y: 20 }}
                  animate={{ opacity: 1, y: 0 }}
                >
                  <h2 className="text-4xl font-bold mb-2 capitalize">{currentWord.word}</h2>
                  {currentWord.pronunciation && (
                    <p className="text-muted-foreground mb-4">{currentWord.pronunciation}</p>
                  )}
                  
                  {/* Context Sentence */}
                  {currentWord.context_sentence && (
                    <div className="mb-6 p-4 rounded-lg bg-muted max-w-2xl mx-auto">
                      <p className="text-sm">
                        <span className="text-muted-foreground">Context: </span>
                        {currentWord.context_sentence.split(currentWord.word).map((part, i, arr) => (
                          <span key={i}>
                            {part}
                            {i < arr.length - 1 && (
                              <strong className="text-primary">{currentWord.word}</strong>
                            )}
                          </span>
                        ))}
                      </p>
                    </div>
                  )}
                  
                  {/* Show/Hide Definition */}
                  {!showDefinition ? (
                    <Button size="lg" onClick={() => setShowDefinition(true)}>
                      Show Definition
                    </Button>
                  ) : (
                    <motion.div
                      initial={{ opacity: 0, y: 10 }}
                      animate={{ opacity: 1, y: 0 }}
                      className="space-y-4"
                    >
                      {/* AI Definition */}
                      {currentWord.ai_definition && (
                        <div className="mb-4">
                          <p className="text-sm text-muted-foreground mb-1">Definition in context:</p>
                          <p className="text-lg">{currentWord.ai_definition}</p>
                        </div>
                      )}
                      
                      {/* Examples */}
                      {currentWord.examples.length > 0 && (
                        <div className="text-left max-w-lg mx-auto">
                          <p className="text-sm font-medium mb-2">Examples:</p>
                          <ul className="space-y-1">
                            {currentWord.examples.slice(0, 2).map((ex, i) => (
                              <li key={i} className="text-sm text-muted-foreground">
                                • {ex}
                              </li>
                            ))}
                          </ul>
                        </div>
                      )}
                      
                      {/* Synonyms */}
                      {currentWord.synonyms.length > 0 && (
                        <div className="flex flex-wrap justify-center gap-2">
                          {currentWord.synonyms.slice(0, 4).map((syn, i) => (
                            <Badge key={i} variant="outline">{syn}</Badge>
                          ))}
                        </div>
                      )}
                      
                      {/* Review Buttons */}
                      <div className="flex justify-center gap-4 pt-6">
                        <Button
                          variant="outline"
                          size="lg"
                          onClick={() => submitReview(false)}
                        >
                          <X className="h-4 w-4 mr-2" />
                          Again
                        </Button>
                        <Button
                          size="lg"
                          onClick={() => submitReview(true)}
                        >
                          <Check className="h-4 w-4 mr-2" />
                          Got It
                        </Button>
                      </div>
                    </motion.div>
                  )}
                </motion.div>
              </CardContent>
            </Card>
          </motion.div>
        ) : (
          /* Normal View */
          <motion.div
            key="list"
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            className="space-y-6"
          >
            {/* Stats */}
            {stats && (
              <div className="grid grid-cols-4 gap-4">
                {[
                  { label: 'New', value: stats.new, color: 'text-blue-500' },
                  { label: 'Learning', value: stats.learning, color: 'text-yellow-500' },
                  { label: 'Mastered', value: stats.mastered, color: 'text-green-500' },
                  { label: 'Total', value: stats.total, color: 'text-primary' },
                ].map((stat) => (
                  <Card key={stat.label}>
                    <CardContent className="py-4 text-center">
                      <p className={cn('text-2xl font-bold', stat.color)}>{stat.value}</p>
                      <p className="text-xs text-muted-foreground">{stat.label}</p>
                    </CardContent>
                  </Card>
                ))}
              </div>
            )}
            
            {/* Actions */}
            <div className="flex flex-wrap items-center justify-between gap-4">
              <div className="flex items-center gap-2">
                <div className="relative">
                  <Search className="h-4 w-4 absolute left-3 top-1/2 -translate-y-1/2 text-muted-foreground" />
                  <input
                    type="text"
                    placeholder="Search words..."
                    value={search}
                    onChange={(e) => setSearch(e.target.value)}
                    className="pl-10 pr-4 py-2 rounded-lg border bg-background focus:outline-none focus:ring-2 focus:ring-primary"
                  />
                </div>
                
                <div className="flex rounded-lg border overflow-hidden">
                  {(['all', 'new', 'learning', 'mastered'] as const).map((f) => (
                    <button
                      key={f}
                      onClick={() => setFilter(f)}
                      className={cn(
                        'px-4 py-2 text-sm capitalize',
                        filter === f ? 'bg-primary text-primary-foreground' : 'bg-background hover:bg-muted'
                      )}
                    >
                      {f}
                    </button>
                  ))}
                </div>
              </div>
              
              <Button onClick={startReview} disabled={loading || words.length === 0}>
                <RotateCcw className="h-4 w-4 mr-2" />
                Review Due
              </Button>
            </div>
            
            {/* Word List */}
            {loading ? (
              <div className="text-center py-12">
                <Loader2 className="h-8 w-8 mx-auto animate-spin text-muted-foreground" />
              </div>
            ) : words.length === 0 ? (
              <Card>
                <CardContent className="py-12 text-center">
                  <Bookmark className="h-12 w-12 mx-auto text-muted-foreground mb-4" />
                  <p className="text-lg font-medium mb-2">No words saved yet</p>
                  <p className="text-sm text-muted-foreground">
                    Click on words while practicing reading or listening to save them to your deck
                  </p>
                </CardContent>
              </Card>
            ) : (
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                {words.map((word, i) => (
                  <motion.div
                    key={word.id}
                    initial={{ opacity: 0, y: 20 }}
                    animate={{ opacity: 1, y: 0 }}
                    transition={{ delay: i * 0.05 }}
                  >
                    <Card className="hover:shadow-md transition-shadow">
                      <CardContent className="py-4">
                        <div className="flex items-start justify-between mb-2">
                          <div>
                            <h3 className="font-medium capitalize">{word.word}</h3>
                            {word.pronunciation && (
                              <p className="text-xs text-muted-foreground">{word.pronunciation}</p>
                            )}
                          </div>
                          <div className="flex items-center gap-2">
                            {word.source_type && (
                              <Badge variant="outline" className="text-xs">
                                {word.source_type}
                              </Badge>
                            )}
                            <Badge 
                              variant={
                                word.mastery === 'mastered' ? 'success' : 
                                word.mastery === 'learning' ? 'secondary' : 'outline'
                              }
                            >
                              {word.mastery}
                            </Badge>
                          </div>
                        </div>
                        
                        {/* Context */}
                        {word.context_sentence && (
                          <p className="text-sm text-muted-foreground mb-2 line-clamp-2">
                            "{word.context_sentence}"
                          </p>
                        )}
                        
                        {/* Definition */}
                        <p className="text-sm line-clamp-2">
                          {word.ai_definition || word.definition}
                        </p>
                        
                        {/* Synonyms */}
                        {word.synonyms.length > 0 && (
                          <div className="flex flex-wrap gap-1 mt-2">
                            {word.synonyms.slice(0, 3).map((syn, j) => (
                              <Badge key={j} variant="secondary" className="text-xs">
                                {syn}
                              </Badge>
                            ))}
                          </div>
                        )}
                      </CardContent>
                    </Card>
                  </motion.div>
                ))}
              </div>
            )}
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  )
}
