'use client'

import { motion, AnimatePresence } from 'framer-motion'
import { useOnboardingStore } from '@/lib/store/onboardingStore'
import { StepPersonalInfo } from './StepPersonalInfo'
import { StepIELTSGoals } from './StepIELTSGoals'
import { StepStudyPreferences } from './StepStudyPreferences'
import { StepPlanSummary } from './StepPlanSummary'
import { ProgressBar } from './ProgressBar'

const slideVariants = {
  enter: (direction: number) => ({
    x: direction > 0 ? 300 : -300,
    opacity: 0,
  }),
  center: {
    x: 0,
    opacity: 1,
  },
  exit: (direction: number) => ({
    x: direction < 0 ? 300 : -300,
    opacity: 0,
  }),
}

export function OnboardingWizard() {
  const { currentStep } = useOnboardingStore()

  // Direction for animation (1 = forward, -1 = backward)
  const direction = 1

  return (
    <div className="space-y-8">
      {/* Header */}
      <div className="text-center">
        <motion.h1
          initial={{ opacity: 0, y: -10 }}
          animate={{ opacity: 1, y: 0 }}
          className="text-3xl font-bold bg-gradient-to-r from-primary to-primary/70 bg-clip-text text-transparent"
        >
          Welcome to AI IELTS Tutor
        </motion.h1>
        <motion.p
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          transition={{ delay: 0.2 }}
          className="text-muted-foreground mt-2"
        >
          {currentStep === 'plan'
            ? 'Your personalized plan is ready'
            : 'Help us personalize your learning journey'}
        </motion.p>
      </div>

      {/* Progress Bar */}
      {currentStep !== 'plan' && <ProgressBar />}

      {/* Step Content */}
      <AnimatePresence mode="wait" custom={direction}>
        <motion.div
          key={currentStep}
          custom={direction}
          variants={slideVariants}
          initial="enter"
          animate="center"
          exit="exit"
          transition={{ type: 'spring', stiffness: 300, damping: 30 }}
        >
          {currentStep === 1 && <StepPersonalInfo />}
          {currentStep === 2 && <StepIELTSGoals />}
          {currentStep === 3 && <StepStudyPreferences />}
          {currentStep === 'plan' && <StepPlanSummary />}
        </motion.div>
      </AnimatePresence>
    </div>
  )
}
