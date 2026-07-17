'use client'

import { useState, useEffect } from 'react'
import { motion, AnimatePresence } from 'framer-motion'
import { BookOpen, Headphones, Mic, PenTool, Sparkles, X, Loader2, ArrowRight } from 'lucide-react'
import { Button } from '@/components/ui/button'
import { Badge } from '@/components/ui/badge'
import { cn } from '@/lib/utils'
import { useRouter } from 'next/navigation'
import { profileApi, type JourneyRecommendation } from '@/lib/services/profile'

interface SkillPickerDialogProps {
  open: boolean
  onOpenChange: (open: boolean) => void
}

const SKILLS = [
  { id: 'reading', label: 'Reading', icon: BookOpen, color: 'bg-blue-500', lightColor: 'bg-blue-500/10 border-blue-200 text-blue-700' },
  { id: 'writing', label: 'Writing', icon: PenTool, color: 'bg-purple-500', lightColor: 'bg-purple-500/10 border-purple-200 text-purple-700' },
  { id: 'listening', label: 'Listening', icon: Headphones, color: 'bg-green-500', lightColor: 'bg-green-500/10 border-green-200 text-green-700' },
  { id: 'speaking', label: 'Speaking', icon: Mic, color: 'bg-orange-500', lightColor: 'bg-orange-500/10 border-orange-200 text-orange-700' },
] as const

export function SkillPickerDialog({ open, onOpenChange }: SkillPickerDialogProps) {
  const router = useRouter()
  const [recommendation, setRecommendation] = useState<JourneyRecommendation | null>(null)
  const [selectedSkill, setSelectedSkill] = useState<string | null>(null)
  const [loading, setLoading] = useState(false)
  const [checkingOnboarding, setCheckingOnboarding] = useState(true)

  useEffect(() => {
    if (!open) return

    setCheckingOnboarding(true)
    setLoading(true)

    async function init() {
      try {
        // Check onboarding first
        const { completed } = await profileApi.getOnboardingStatus()
        if (!completed) {
          // Redirect to onboarding
          onOpenChange(false)
          router.push('/onboarding')
          return
        }

        // Fetch recommendation
        const rec = await profileApi.getJourneyRecommendation()
        setRecommendation(rec)
        setSelectedSkill(rec.skill)
      } catch {
        // If API fails, default to reading
        setSelectedSkill('reading')
      } finally {
        setCheckingOnboarding(false)
        setLoading(false)
      }
    }

    init()
  }, [open, router, onOpenChange])

  const handleStart = () => {
    if (!selectedSkill) return

    // Build query params based on recommendation or defaults
    const params = new URLSearchParams({ auto: 'ai' })

    if (recommendation && selectedSkill === recommendation.skill) {
      // Use the AI-personalized params
      params.set('topic', recommendation.topic)
      params.set('difficulty', recommendation.difficulty)
      params.set('question_type', recommendation.question_type)
    }

    onOpenChange(false)
    router.push(`/practice/${selectedSkill}?${params.toString()}`)
  }

  if (!open) return null

  return (
    <AnimatePresence>
      {open && (
        <>
          {/* Backdrop */}
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            className="fixed inset-0 z-50 bg-black/50"
            onClick={() => onOpenChange(false)}
          />

          {/* Dialog */}
          <motion.div
            initial={{ opacity: 0, scale: 0.95, y: 20 }}
            animate={{ opacity: 1, scale: 1, y: 0 }}
            exit={{ opacity: 0, scale: 0.95, y: 20 }}
            transition={{ type: 'spring', duration: 0.3 }}
            className="fixed inset-0 z-50 flex items-center justify-center p-4"
            onClick={(e) => e.stopPropagation()}
          >
            <div className="w-full max-w-lg rounded-2xl border border-border bg-card shadow-xl">
              {/* Header */}
              <div className="flex items-center justify-between p-6 pb-2">
                <div>
                  <h2 className="text-xl font-bold">Start Your Practice</h2>
                  <p className="text-sm text-muted-foreground mt-1">
                    Choose a skill to practice
                  </p>
                </div>
                <Button
                  variant="ghost"
                  size="sm"
                  onClick={() => onOpenChange(false)}
                  className="h-8 w-8 p-0 rounded-full"
                >
                  <X className="h-4 w-4" />
                </Button>
              </div>

              {/* Content */}
              <div className="p-6 pt-4">
                {loading || checkingOnboarding ? (
                  <div className="flex items-center justify-center py-12">
                    <Loader2 className="h-6 w-6 animate-spin text-primary" />
                    <span className="ml-2 text-sm text-muted-foreground">
                      Loading your recommendation...
                    </span>
                  </div>
                ) : (
                  <div className="space-y-4">
                    {/* AI Recommendation note */}
                    {recommendation && (
                      <motion.div
                        initial={{ opacity: 0, y: -10 }}
                        animate={{ opacity: 1, y: 0 }}
                        className="flex items-start gap-3 p-3 rounded-xl bg-primary/5 border border-primary/20"
                      >
                        <Sparkles className="h-5 w-5 text-primary shrink-0 mt-0.5" />
                        <div>
                          <p className="text-sm font-medium text-primary">AI Recommendation</p>
                          <p className="text-xs text-muted-foreground mt-0.5">
                            {recommendation.reason}
                          </p>
                        </div>
                      </motion.div>
                    )}

                    {/* Skill grid */}
                    <div className="grid grid-cols-2 gap-3">
                      {SKILLS.map((skill) => {
                        const Icon = skill.icon
                        const isRecommended = recommendation?.skill === skill.id
                        const isSelected = selectedSkill === skill.id

                        return (
                          <button
                            key={skill.id}
                            onClick={() => setSelectedSkill(skill.id)}
                            className={cn(
                              'relative flex flex-col items-center gap-3 p-5 rounded-xl border-2 transition-all',
                              'hover:shadow-md hover:scale-[1.02] active:scale-[0.98]',
                              isSelected
                                ? 'border-primary bg-primary/5 shadow-md'
                                : 'border-border hover:border-primary/30'
                            )}
                          >
                            {isRecommended && (
                              <Badge
                                variant="default"
                                className="absolute -top-2 -right-2 text-[10px] px-2 py-0.5"
                              >
                                AI Pick
                              </Badge>
                            )}
                            <div className={cn(
                              'h-12 w-12 rounded-xl flex items-center justify-center',
                              isSelected ? skill.color : 'bg-muted'
                            )}>
                              <Icon className={cn(
                                'h-6 w-6',
                                isSelected ? 'text-white' : 'text-muted-foreground'
                              )} />
                            </div>
                            <span className={cn(
                              'font-medium text-sm',
                              isSelected ? 'text-primary' : 'text-foreground'
                            )}>
                              {skill.label}
                            </span>
                          </button>
                        )
                      })}
                    </div>

                    {/* Personalization info */}
                    {recommendation && selectedSkill === recommendation.skill && (
                      <motion.div
                        initial={{ opacity: 0, height: 0 }}
                        animate={{ opacity: 1, height: 'auto' }}
                        className="text-xs text-muted-foreground bg-muted/50 rounded-lg p-3 space-y-1"
                      >
                        <p><span className="font-medium">Topic:</span> {recommendation.topic}</p>
                        <p><span className="font-medium">Difficulty:</span> {recommendation.difficulty}</p>
                        <p><span className="font-medium">Focus:</span> {recommendation.question_type.replace(/_/g, ' ')}</p>
                      </motion.div>
                    )}
                  </div>
                )}
              </div>

              {/* Footer */}
              {!loading && !checkingOnboarding && (
                <div className="p-6 pt-2">
                  <Button
                    size="lg"
                    className="w-full"
                    onClick={handleStart}
                    disabled={!selectedSkill}
                  >
                    Start Practice
                    <ArrowRight className="ml-2 h-4 w-4" />
                  </Button>
                </div>
              )}
            </div>
          </motion.div>
        </>
      )}
    </AnimatePresence>
  )
}
