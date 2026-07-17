/**
 * MutationSection — collapsible "Upgrade Your Response" section shown
 * below basic speaking feedback when the mutationEngine feature is on.
 *
 * Phases handled internally:
 *   generating_mutations → spinner
 *   selecting_tier       → three MutationTierCard
 *   shadowing | assessing → ShadowingAssessment
 *   complete             → success banner + "Practice Another Tier" button
 */
'use client'

import { useState } from 'react'
import { motion, AnimatePresence } from 'framer-motion'
import { Zap, ChevronDown, CheckCircle2, Loader2 } from 'lucide-react'
import { Button } from '@/components/ui/button'
import { cn } from '@/lib/utils'
import { useSpeakingStore, useSelectedTier } from '@/lib/store/speakingStore'
import { MutationTierCard } from './MutationTierCard'
import { ShadowingAssessment } from './ShadowingAssessment'

export function MutationSection() {
  const [expanded, setExpanded] = useState(false)

  const {
    phase,
    mutationResponse,
    selectedTierIndex,
    assessmentResult,
    selectTier,
    setPhase,
    setAssessmentResult,
    setError,
  } = useSpeakingStore()

  const selectedTier = useSelectedTier()

  const isGenerating = phase === 'generating_mutations'
  const isSelecting  = phase === 'selecting_tier'
  const isShadowing  = phase === 'shadowing' || phase === 'assessing'
  const isComplete   = phase === 'complete'

  const handleSelectTier = (index: number) => {
    selectTier(index)
    setPhase('shadowing')
  }

  const handleBackToTiers = () => {
    selectTier(null as unknown as number)
    setAssessmentResult(null as unknown as any)
    setError(null)
    setPhase('selecting_tier')
  }

  const handlePracticeAnother = () => {
    selectTier(null as unknown as number)
    setAssessmentResult(null as unknown as any)
    setPhase('selecting_tier')
  }

  return (
    <div className="mt-6">
      {/* Collapsible header */}
      <button
        onClick={() => setExpanded((v) => !v)}
        className="flex items-center gap-2 text-sm font-medium text-primary hover:text-primary/80 transition-colors"
      >
        <Zap className="h-4 w-4" />
        Upgrade Your Response
        {isGenerating && <Loader2 className="h-3.5 w-3.5 animate-spin ml-1" />}
        <ChevronDown className={cn(
          'h-4 w-4 transition-transform duration-200',
          expanded && 'rotate-180'
        )} />
      </button>

      <AnimatePresence>
        {expanded && (
          <motion.div
            initial={{ height: 0, opacity: 0 }}
            animate={{ height: 'auto', opacity: 1 }}
            exit={{ height: 0, opacity: 0 }}
            transition={{ duration: 0.25 }}
            className="overflow-hidden"
          >
            <div className="pt-4 space-y-4">

              {/* Generating spinner */}
              {isGenerating && (
                <div className="flex items-center gap-3 p-4 rounded-xl bg-muted/50">
                  <Loader2 className="h-5 w-5 animate-spin text-primary" />
                  <p className="text-sm text-muted-foreground">
                    Generating three upgraded versions of your response…
                  </p>
                </div>
              )}

              {/* Tier selection */}
              {isSelecting && mutationResponse && (
                <div className="space-y-3">
                  <p className="text-sm text-muted-foreground">
                    Select a tier to practise. Each version upgrades your original response to a higher band.
                  </p>
                  <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                    {mutationResponse.tiers.map((tier, i) => (
                      <MutationTierCard
                        key={i}
                        tier={tier}
                        selected={selectedTierIndex === i}
                        onSelect={() => handleSelectTier(i)}
                      />
                    ))}
                  </div>
                </div>
              )}

              {/* Shadowing step */}
              {isShadowing && selectedTier && (
                <ShadowingAssessment
                  targetTier={selectedTier}
                  onBack={handleBackToTiers}
                />
              )}

              {/* Complete success */}
              {isComplete && selectedTier && (
                <motion.div
                  initial={{ opacity: 0, scale: 0.96 }}
                  animate={{ opacity: 1, scale: 1 }}
                  className="p-6 rounded-xl bg-green-50 dark:bg-green-950/20 border border-green-200 dark:border-green-800 text-center"
                >
                  <CheckCircle2 className="h-12 w-12 text-green-500 mx-auto mb-3" />
                  <h3 className="font-semibold text-green-700 dark:text-green-400 text-lg">
                    Band {selectedTier.target_band} Patterns Locked In
                  </h3>
                  <p className="text-sm text-muted-foreground mt-2">
                    You've successfully replicated the target speech patterns for {selectedTier.band_label}.
                  </p>
                  {assessmentResult && (
                    <p className="text-sm font-medium mt-2">
                      Overall similarity: {Math.round(assessmentResult.overall_similarity * 100)}%
                    </p>
                  )}
                  <Button
                    variant="outline"
                    size="sm"
                    className="mt-4"
                    onClick={handlePracticeAnother}
                  >
                    Practice Another Tier
                  </Button>
                </motion.div>
              )}

            </div>
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  )
}
