'use client'

import { motion } from 'framer-motion'
import { BookOpen, Volume2, ArrowRight } from 'lucide-react'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Badge } from '@/components/ui/badge'
import { useDueVocabulary } from '@/lib/hooks/useVocabulary'
import { fadeInUp, staggerItem } from '@/lib/animations'

export function VocabularyReviewWidget() {
  const { data: dueVocab, isLoading } = useDueVocabulary()

  const reviewWords = isLoading
    ? []
    : (dueVocab || []).filter(v => v.mastery === 'learning').slice(0, 3)

  return (
    <motion.div variants={fadeInUp} initial="initial" animate="animate">
      <Card className="h-full">
        <CardHeader className="pb-3">
          <CardTitle className="text-base flex items-center gap-2">
            <BookOpen className="h-4 w-4 text-primary" />
            Vocabulary Review
            <Badge variant="secondary" className="ml-auto text-xs">
              {reviewWords.length} due
            </Badge>
          </CardTitle>
        </CardHeader>
        <CardContent>
          <div className="space-y-3">
            {reviewWords.map((word) => (
              <motion.div
                key={word.id}
                variants={staggerItem}
                className="flex items-center justify-between p-3 rounded-xl bg-muted/50 hover:bg-muted transition-colors"
              >
                <div>
                  <p className="font-medium text-sm">{word.word}</p>
                  <p className="text-xs text-muted-foreground">{word.meaning}</p>
                </div>
                <Button variant="ghost" size="icon" className="h-8 w-8 shrink-0">
                  <Volume2 className="h-4 w-4" />
                </Button>
              </motion.div>
            ))}
          </div>
          <Button variant="outline" className="w-full mt-4" size="sm">
            Start Review
            <ArrowRight className="h-4 w-4 ml-2" />
          </Button>
        </CardContent>
      </Card>
    </motion.div>
  )
}