'use client'

import { useState } from 'react'
import { motion, AnimatePresence } from 'framer-motion'
import { Sparkles, X, ArrowRight } from 'lucide-react'
import { Button } from '@/components/ui/button'
import { useRouter } from 'next/navigation'

interface OnboardingBannerProps {
  show: boolean
}

export function OnboardingBanner({ show }: OnboardingBannerProps) {
  const [dismissed, setDismissed] = useState(false)
  const router = useRouter()

  const handleComplete = () => {
    // Clear the skip flag so the guard redirects to onboarding
    localStorage.removeItem('onboarding_skipped')
    router.push('/onboarding')
  }

  const handleDismiss = () => {
    setDismissed(true)
  }

  return (
    <AnimatePresence>
      {show && !dismissed && (
        <motion.div
          initial={{ opacity: 0, y: -10, height: 0 }}
          animate={{ opacity: 1, y: 0, height: 'auto' }}
          exit={{ opacity: 0, y: -10, height: 0 }}
          transition={{ duration: 0.3 }}
          className="mb-6"
        >
          <div className="flex items-center justify-between gap-4 p-4 rounded-xl bg-primary/5 border border-primary/20">
            <div className="flex items-center gap-3">
              <div className="h-9 w-9 rounded-full bg-primary/10 flex items-center justify-center shrink-0">
                <Sparkles className="h-4 w-4 text-primary" />
              </div>
              <div>
                <p className="text-sm font-medium">Complete your profile for personalized recommendations</p>
                <p className="text-xs text-muted-foreground">
                  Help Uma understand your goals to create a tailored learning plan
                </p>
              </div>
            </div>
            <div className="flex items-center gap-2 shrink-0">
              <Button size="sm" onClick={handleComplete}>
                Complete Setup
                <ArrowRight className="h-3.5 w-3.5 ml-1" />
              </Button>
              <Button
                variant="ghost"
                size="icon"
                onClick={handleDismiss}
                className="h-8 w-8 text-muted-foreground"
              >
                <X className="h-4 w-4" />
                <span className="sr-only">Dismiss</span>
              </Button>
            </div>
          </div>
        </motion.div>
      )}
    </AnimatePresence>
  )
}
