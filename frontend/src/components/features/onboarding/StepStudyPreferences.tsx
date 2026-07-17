'use client'

import { ArrowLeft, Sparkles, SkipForward, Loader2 } from 'lucide-react'
import { Card, CardContent, CardFooter } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { useOnboardingStore } from '@/lib/store/onboardingStore'
import { useRouter } from 'next/navigation'
import { cn } from '@/lib/utils'

const SKILLS = [
  { id: 'reading', label: 'Reading', emoji: '📖' },
  { id: 'writing', label: 'Writing', emoji: '✍️' },
  { id: 'listening', label: 'Listening', emoji: '🎧' },
  { id: 'speaking', label: 'Speaking', emoji: '🗣️' },
]

const HOURS_OPTIONS = [1, 2, 3, 4, 5, 6]
const GOAL_OPTIONS = [2, 3, 4, 5, 6, 7, 8, 10]

export function StepStudyPreferences() {
  const {
    stepThree,
    updateStepThree,
    prevStep,
    submitOnboarding,
    isSubmitting,
    error,
    skipOnboarding,
  } = useOnboardingStore()
  const router = useRouter()

  const handleSkip = async () => {
    await skipOnboarding()
    localStorage.setItem('onboarding_skipped', 'true')
    router.push('/')
  }

  const toggleSkill = (skillId: string) => {
    const current = stepThree.focusSkills
    if (current.includes(skillId)) {
      updateStepThree({ focusSkills: current.filter((s) => s !== skillId) })
    } else {
      updateStepThree({ focusSkills: [...current, skillId] })
    }
  }

  return (
    <Card>
      <CardContent className="p-6 space-y-5">
        {/* Focus Skills */}
        <div className="space-y-2">
          <label className="text-sm font-medium">
            Which skills do you want to focus on?
          </label>
          <div className="grid grid-cols-2 gap-3">
            {SKILLS.map((skill) => {
              const isSelected = stepThree.focusSkills.includes(skill.id)
              return (
                <button
                  key={skill.id}
                  type="button"
                  onClick={() => toggleSkill(skill.id)}
                  className={cn(
                    'flex items-center gap-3 p-4 rounded-xl border text-sm font-medium transition-all text-left',
                    isSelected
                      ? 'bg-primary/10 border-primary text-primary shadow-sm'
                      : 'bg-background border-input hover:bg-accent hover:text-accent-foreground'
                  )}
                >
                  <span className="text-xl">{skill.emoji}</span>
                  <span>{skill.label}</span>
                  {isSelected && (
                    <span className="ml-auto text-xs bg-primary text-primary-foreground px-2 py-0.5 rounded-full">
                      Selected
                    </span>
                  )}
                </button>
              )
            })}
          </div>
          <p className="text-xs text-muted-foreground">
            We prioritize your weakest or most important skills in daily roadmaps and recommendations
          </p>
        </div>

        {/* Study Hours Per Day */}
        <div className="space-y-2">
          <label className="text-sm font-medium">
            How many hours can you study per day?
          </label>
          <div className="flex flex-wrap gap-2">
            {HOURS_OPTIONS.map((hours) => (
              <button
                key={hours}
                type="button"
                onClick={() => updateStepThree({ studyHoursPerDay: hours })}
                className={cn(
                  'h-10 px-4 rounded-lg border text-sm font-medium transition-all',
                  stepThree.studyHoursPerDay === hours
                    ? 'bg-primary text-primary-foreground border-primary shadow-sm'
                    : 'bg-background border-input hover:bg-accent hover:text-accent-foreground'
                )}
              >
                {hours}h
              </button>
            ))}
          </div>
          <p className="text-xs text-muted-foreground">
            This sets the volume of content and practice sessions generated each day
          </p>
        </div>

        {/* Daily Goal */}
        <div className="space-y-2">
          <label className="text-sm font-medium">
            Daily task goal
          </label>
          <div className="flex flex-wrap gap-2">
            {GOAL_OPTIONS.map((goal) => (
              <button
                key={goal}
                type="button"
                onClick={() => updateStepThree({ dailyGoal: goal })}
                className={cn(
                  'h-10 px-4 rounded-lg border text-sm font-medium transition-all',
                  stepThree.dailyGoal === goal
                    ? 'bg-primary text-primary-foreground border-primary shadow-sm'
                    : 'bg-background border-input hover:bg-accent hover:text-accent-foreground'
                )}
              >
                {goal} tasks
              </button>
            ))}
          </div>
          <p className="text-xs text-muted-foreground">
            Your daily goal keeps you on track — Uma will remind you if you fall behind
          </p>
        </div>

        {/* Error message */}
        {error && (
          <div className="p-3 rounded-lg bg-destructive/10 border border-destructive/20 text-destructive text-sm">
            {error}
          </div>
        )}
      </CardContent>

      <CardFooter className="flex justify-between p-6 pt-0">
        <div className="flex gap-2">
          <Button variant="outline" onClick={prevStep} disabled={isSubmitting}>
            <ArrowLeft className="h-4 w-4 mr-1" />
            Back
          </Button>
          <Button
            variant="ghost"
            onClick={handleSkip}
            disabled={isSubmitting}
            className="text-muted-foreground"
          >
            <SkipForward className="h-4 w-4 mr-1" />
            Skip for now
          </Button>
        </div>
        <Button onClick={submitOnboarding} disabled={isSubmitting} size="lg">
          {isSubmitting ? (
            <>
              <Loader2 className="h-4 w-4 mr-1 animate-spin" />
              Generating Plan...
            </>
          ) : (
            <>
              Generate My Plan
              <Sparkles className="h-4 w-4 ml-1" />
            </>
          )}
        </Button>
      </CardFooter>
    </Card>
  )
}
