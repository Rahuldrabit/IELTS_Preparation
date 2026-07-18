'use client'

import { motion } from 'framer-motion'
import { AlertCircle, ArrowRight } from 'lucide-react'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Badge } from '@/components/ui/badge'
import { useGrammarTopics } from '@/lib/hooks/useGrammar'
import { fadeInUp, staggerItem } from '@/lib/animations'

interface GrammarMistakeSchema {
  id: number
  incorrect_sentence: string
  correct_sentence: string
  explanation: string
  date: string
}

export function RecentMistakesWidget() {
  const { data: topics, isLoading } = useGrammarTopics()
  
  const allMistakes = isLoading
    ? []
    : (topics || []).reduce((acc: GrammarMistakeSchema[], topic: any) => {
        if (topic.mistakes) {
          acc.push(...topic.mistakes.slice(0, 1))
        }
        return acc
      }, [] as GrammarMistakeSchema[])

  const recentMistakes = allMistakes.slice(0, 3)

  return (
    <motion.div variants={fadeInUp} initial="initial" animate="animate">
      <Card className="h-full">
        <CardHeader className="pb-3">
          <CardTitle className="text-base flex items-center gap-2">
            <AlertCircle className="h-4 w-4 text-warning" />
            Recent Mistakes
          </CardTitle>
        </CardHeader>
        <CardContent>
          <div className="space-y-3">
            {recentMistakes.length > 0 ? recentMistakes.map((mistake) => {
              const skill = 'Grammar'
              return (
                <motion.div
                  key={mistake.id}
                  variants={staggerItem}
                  className="p-3 rounded-xl border border-destructive/20 bg-destructive/5"
                >
                  <div className="flex items-start justify-between gap-2 mb-2">
                    <Badge variant="outline" className="text-xs">
                      {skill}
                    </Badge>
                  </div>
                  <p className="text-sm text-destructive font-medium line-through">
                    {mistake.incorrect_sentence}
                  </p>
                  <p className="text-sm text-success font-medium mt-1">
                    → {mistake.correct_sentence}
                  </p>
                  <p className="text-xs text-muted-foreground mt-2">
                    {mistake.explanation}
                  </p>
                </motion.div>
              )
            }) : (
              <div className="text-center py-4 text-muted-foreground">
                No mistakes recorded yet
              </div>
            )}
          </div>
          <Button variant="outline" className="w-full mt-4" size="sm">
            View All Mistakes
            <ArrowRight className="h-4 w-4 ml-2" />
          </Button>
        </CardContent>
      </Card>
    </motion.div>
  )
}