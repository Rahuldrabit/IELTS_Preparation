'use client'

import { OnboardingWizard } from '@/components/features/onboarding/OnboardingWizard'

export default function OnboardingPage() {
  return (
    <div className="min-h-screen bg-gradient-to-br from-background via-background to-primary/5 flex items-center justify-center p-4">
      <div className="w-full max-w-2xl">
        <OnboardingWizard />
      </div>
    </div>
  )
}
