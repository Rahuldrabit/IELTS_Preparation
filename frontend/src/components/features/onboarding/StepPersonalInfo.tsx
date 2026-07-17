'use client'

import { ArrowRight, SkipForward } from 'lucide-react'
import { Card, CardContent, CardFooter } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { useOnboardingStore } from '@/lib/store/onboardingStore'
import { useRouter } from 'next/navigation'

const LANGUAGES = [
  'Arabic', 'Bengali', 'Chinese (Mandarin)', 'Chinese (Cantonese)', 'French',
  'German', 'Hindi', 'Indonesian', 'Japanese', 'Korean', 'Malay', 'Nepali',
  'Persian (Farsi)', 'Portuguese', 'Punjabi', 'Russian', 'Spanish', 'Tamil',
  'Thai', 'Turkish', 'Urdu', 'Vietnamese', 'Other',
]

const EDUCATION_LEVELS = [
  { value: 'high_school', label: 'High School' },
  { value: 'bachelors', label: "Bachelor's Degree" },
  { value: 'masters', label: "Master's Degree" },
  { value: 'phd', label: 'PhD / Doctorate' },
  { value: 'other', label: 'Other' },
]

export function StepPersonalInfo() {
  const { stepOne, updateStepOne, nextStep, skipOnboarding } = useOnboardingStore()
  const router = useRouter()

  const handleSkip = async () => {
    await skipOnboarding()
    localStorage.setItem('onboarding_skipped', 'true')
    router.push('/')
  }

  return (
    <Card>
      <CardContent className="p-6 space-y-5">
        {/* Name */}
        <div className="space-y-1.5">
          <label className="text-sm font-medium" htmlFor="onb-name">
            Full Name
          </label>
          <Input
            id="onb-name"
            placeholder="Enter your name"
            value={stepOne.name}
            onChange={(e) => updateStepOne({ name: e.target.value })}
          />
          <p className="text-xs text-muted-foreground">
            We use your name to personalize feedback and motivational messages
          </p>
        </div>

        {/* Date of Birth */}
        <div className="space-y-1.5">
          <label className="text-sm font-medium" htmlFor="onb-dob">
            Date of Birth
          </label>
          <Input
            id="onb-dob"
            type="date"
            value={stepOne.dateOfBirth}
            onChange={(e) => updateStepOne({ dateOfBirth: e.target.value })}
          />
          <p className="text-xs text-muted-foreground">
            Helps us tailor content topics to your age group and life stage
          </p>
        </div>

        {/* Native Language */}
        <div className="space-y-1.5">
          <label className="text-sm font-medium" htmlFor="onb-language">
            Native Language
          </label>
          <select
            id="onb-language"
            value={stepOne.nativeLanguage}
            onChange={(e) => updateStepOne({ nativeLanguage: e.target.value })}
            className="flex h-10 w-full rounded-xl border border-input bg-background px-4 py-2 text-sm ring-offset-background focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2 transition-colors"
          >
            <option value="">Select your native language</option>
            {LANGUAGES.map((lang) => (
              <option key={lang} value={lang}>{lang}</option>
            ))}
          </select>
          <p className="text-xs text-muted-foreground">
            Your native language helps us focus on common interference patterns in grammar and pronunciation
          </p>
        </div>

        {/* Occupation */}
        <div className="space-y-1.5">
          <label className="text-sm font-medium" htmlFor="onb-occupation">
            Occupation
          </label>
          <Input
            id="onb-occupation"
            placeholder="e.g. Software Engineer, Nurse, Student"
            value={stepOne.occupation}
            onChange={(e) => updateStepOne({ occupation: e.target.value })}
          />
          <p className="text-xs text-muted-foreground">
            We choose relevant essay topics and speaking scenarios based on your field
          </p>
        </div>

        {/* Education Level */}
        <div className="space-y-1.5">
          <label className="text-sm font-medium" htmlFor="onb-education">
            Education Level
          </label>
          <select
            id="onb-education"
            value={stepOne.educationLevel}
            onChange={(e) => updateStepOne({ educationLevel: e.target.value })}
            className="flex h-10 w-full rounded-xl border border-input bg-background px-4 py-2 text-sm ring-offset-background focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2 transition-colors"
          >
            <option value="">Select your education level</option>
            {EDUCATION_LEVELS.map((level) => (
              <option key={level.value} value={level.value}>{level.label}</option>
            ))}
          </select>
          <p className="text-xs text-muted-foreground">
            Helps calibrate the academic vocabulary complexity in reading passages
          </p>
        </div>
      </CardContent>

      <CardFooter className="flex justify-between p-6 pt-0">
        <Button variant="ghost" onClick={handleSkip} className="text-muted-foreground">
          <SkipForward className="h-4 w-4 mr-1" />
          Skip for now
        </Button>
        <Button onClick={nextStep}>
          Next
          <ArrowRight className="h-4 w-4 ml-1" />
        </Button>
      </CardFooter>
    </Card>
  )
}
