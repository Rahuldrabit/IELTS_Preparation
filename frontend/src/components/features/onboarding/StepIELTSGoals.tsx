'use client'

import { ArrowLeft, ArrowRight, SkipForward } from 'lucide-react'
import { Card, CardContent, CardFooter } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { useOnboardingStore } from '@/lib/store/onboardingStore'
import { useRouter } from 'next/navigation'
import { cn } from '@/lib/utils'

const BAND_SCORES = [4.0, 4.5, 5.0, 5.5, 6.0, 6.5, 7.0, 7.5, 8.0, 8.5, 9.0]

const REASONS = [
  { value: 'immigration', label: 'Immigration (PR / Visa)' },
  { value: 'university', label: 'University Admission' },
  { value: 'career', label: 'Career / Professional Development' },
  { value: 'personal', label: 'Personal Goal' },
  { value: 'other', label: 'Other' },
]

export function StepIELTSGoals() {
  const { stepTwo, updateStepTwo, prevStep, nextStep, skipOnboarding } = useOnboardingStore()
  const router = useRouter()

  const handleSkip = async () => {
    await skipOnboarding()
    localStorage.setItem('onboarding_skipped', 'true')
    router.push('/')
  }

  return (
    <Card>
      <CardContent className="p-6 space-y-5">
        {/* Current Band */}
        <div className="space-y-2">
          <label className="text-sm font-medium">
            Current Band Score (estimate)
          </label>
          <div className="flex flex-wrap gap-2">
            {BAND_SCORES.map((band) => (
              <button
                key={band}
                type="button"
                onClick={() => updateStepTwo({ currentBand: band })}
                className={cn(
                  'h-9 px-3 rounded-lg border text-sm font-medium transition-all',
                  stepTwo.currentBand === band
                    ? 'bg-primary text-primary-foreground border-primary shadow-sm'
                    : 'bg-background border-input hover:bg-accent hover:text-accent-foreground'
                )}
              >
                {band}
              </button>
            ))}
          </div>
          <p className="text-xs text-muted-foreground">
            Your starting point helps us calibrate initial difficulty and track progress
          </p>
        </div>

        {/* Target Band */}
        <div className="space-y-2">
          <label className="text-sm font-medium">
            Target Band Score
          </label>
          <div className="flex flex-wrap gap-2">
            {BAND_SCORES.filter((b) => b >= 5.5).map((band) => (
              <button
                key={band}
                type="button"
                onClick={() => updateStepTwo({ targetBand: band })}
                className={cn(
                  'h-9 px-3 rounded-lg border text-sm font-medium transition-all',
                  stepTwo.targetBand === band
                    ? 'bg-primary text-primary-foreground border-primary shadow-sm'
                    : 'bg-background border-input hover:bg-accent hover:text-accent-foreground'
                )}
              >
                {band}
              </button>
            ))}
          </div>
          <p className="text-xs text-muted-foreground">
            Your target band lets us calibrate pacing and set milestone goals
          </p>
        </div>

        {/* Exam Date */}
        <div className="space-y-1.5">
          <label className="text-sm font-medium" htmlFor="onb-exam-date">
            Exam Date (if scheduled)
          </label>
          <Input
            id="onb-exam-date"
            type="date"
            value={stepTwo.examDate}
            onChange={(e) => updateStepTwo({ examDate: e.target.value })}
            min={new Date().toISOString().split('T')[0]}
          />
          <p className="text-xs text-muted-foreground">
            Exam date helps us create urgency-based scheduling and countdown milestones
          </p>
        </div>

        {/* IELTS Module */}
        <div className="space-y-2">
          <label className="text-sm font-medium">IELTS Module</label>
          <div className="flex gap-3">
            {(['academic', 'general'] as const).map((module) => (
              <button
                key={module}
                type="button"
                onClick={() => updateStepTwo({ ieltsModule: module })}
                className={cn(
                  'flex-1 h-12 rounded-xl border text-sm font-medium transition-all',
                  stepTwo.ieltsModule === module
                    ? 'bg-primary text-primary-foreground border-primary shadow-sm'
                    : 'bg-background border-input hover:bg-accent hover:text-accent-foreground'
                )}
              >
                {module === 'academic' ? 'Academic' : 'General Training'}
              </button>
            ))}
          </div>
          <p className="text-xs text-muted-foreground">
            Academic and General Training have different Writing Task 1 formats — we adapt accordingly
          </p>
        </div>

        {/* Reason for IELTS */}
        <div className="space-y-1.5">
          <label className="text-sm font-medium" htmlFor="onb-reason">
            Why are you taking IELTS?
          </label>
          <select
            id="onb-reason"
            value={stepTwo.reasonForIelts}
            onChange={(e) => updateStepTwo({ reasonForIelts: e.target.value })}
            className="flex h-10 w-full rounded-xl border border-input bg-background px-4 py-2 text-sm ring-offset-background focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2 transition-colors"
          >
            <option value="">Select your reason</option>
            {REASONS.map((reason) => (
              <option key={reason.value} value={reason.value}>{reason.label}</option>
            ))}
          </select>
          <p className="text-xs text-muted-foreground">
            Your goal helps us prioritize relevant content — immigration needs higher listening, university needs academic writing
          </p>
        </div>
      </CardContent>

      <CardFooter className="flex justify-between p-6 pt-0">
        <div className="flex gap-2">
          <Button variant="outline" onClick={prevStep}>
            <ArrowLeft className="h-4 w-4 mr-1" />
            Back
          </Button>
          <Button variant="ghost" onClick={handleSkip} className="text-muted-foreground">
            <SkipForward className="h-4 w-4 mr-1" />
            Skip for now
          </Button>
        </div>
        <Button onClick={nextStep}>
          Next
          <ArrowRight className="h-4 w-4 ml-1" />
        </Button>
      </CardFooter>
    </Card>
  )
}
