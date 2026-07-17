'use client'

import { motion } from 'framer-motion'
import { User, Target, BookOpen, Check } from 'lucide-react'
import { useOnboardingStore, type OnboardingStep } from '@/lib/store/onboardingStore'
import { cn } from '@/lib/utils'

const steps = [
  { number: 1 as const, label: 'Personal Info', icon: User },
  { number: 2 as const, label: 'IELTS Goals', icon: Target },
  { number: 3 as const, label: 'Study Plan', icon: BookOpen },
]

export function ProgressBar() {
  const { currentStep } = useOnboardingStore()
  const currentStepNum = typeof currentStep === 'number' ? currentStep : 4

  return (
    <div className="flex items-center justify-between">
      {steps.map((step, index) => {
        const isCompleted = currentStepNum > step.number
        const isCurrent = currentStep === step.number
        const Icon = step.icon

        return (
          <div key={step.number} className="flex items-center flex-1">
            {/* Step circle */}
            <div className="flex flex-col items-center gap-1.5">
              <motion.div
                initial={false}
                animate={{
                  scale: isCurrent ? 1.1 : 1,
                  backgroundColor: isCompleted || isCurrent
                    ? 'hsl(var(--primary))'
                    : 'hsl(var(--muted))',
                }}
                transition={{ duration: 0.3 }}
                className={cn(
                  'h-10 w-10 rounded-full flex items-center justify-center transition-colors',
                  (isCompleted || isCurrent) ? 'text-primary-foreground' : 'text-muted-foreground'
                )}
              >
                {isCompleted ? (
                  <Check className="h-5 w-5" />
                ) : (
                  <Icon className="h-5 w-5" />
                )}
              </motion.div>
              <span
                className={cn(
                  'text-xs font-medium',
                  isCurrent ? 'text-primary' : 'text-muted-foreground'
                )}
              >
                {step.label}
              </span>
            </div>

            {/* Connector line */}
            {index < steps.length - 1 && (
              <div className="flex-1 mx-3 h-0.5 rounded-full bg-muted overflow-hidden">
                <motion.div
                  initial={false}
                  animate={{ width: isCompleted ? '100%' : '0%' }}
                  transition={{ duration: 0.4 }}
                  className="h-full bg-primary rounded-full"
                />
              </div>
            )}
          </div>
        )
      })}
    </div>
  )
}
