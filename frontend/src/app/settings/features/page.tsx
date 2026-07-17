/**
 * /settings/features — Feature Lab
 * Dedicated route for managing all advanced feature flags.
 * Students set their global defaults here; config panels allow per-session overrides.
 */
'use client'

import { motion } from 'framer-motion'
import {
  BookOpen, Headphones, Mic, PenTool,
  Activity, Brain, Lock, Zap, Sparkles, Mic2,
  RotateCcw, FlaskConical,
} from 'lucide-react'
import { Button } from '@/components/ui/button'
import { useFeatureStore } from '@/lib/store/featureStore'
import { useActiveFeatureCount } from '@/lib/hooks/useFeature'
import { useFeatureSync } from '@/lib/hooks/useFeatureSync'
import { SkillFeatureSection } from '@/components/features/settings/SkillFeatureSection'
import { FeatureToggleRow } from '@/components/features/settings/FeatureToggleRow'

// ─────────────────────────────────────────────
//  Page
// ─────────────────────────────────────────────

export default function FeatureLabPage() {
  const { resetToDefaults } = useFeatureStore()
  const activeCount = useActiveFeatureCount()

  // Mount sync so changes on this page propagate to backend
  useFeatureSync()

  return (
    <div className="space-y-6 max-w-2xl mx-auto">
      {/* Header */}
      <motion.div initial={{ opacity: 0, y: -16 }} animate={{ opacity: 1, y: 0 }}>
        <div className="flex items-center gap-3 mb-2">
          <div className="h-12 w-12 rounded-xl bg-primary/10 flex items-center justify-center">
            <FlaskConical className="h-6 w-6 text-primary" />
          </div>
          <div>
            <h1 className="text-2xl font-bold">Feature Lab</h1>
            <p className="text-sm text-muted-foreground">
              Control which advanced tools activate during your practice sessions
            </p>
          </div>
        </div>

        {/* Active count summary */}
        <div className="flex items-center justify-between p-3 rounded-xl bg-muted/50 mt-4">
          <span className="text-sm text-muted-foreground">
            <span className="font-semibold text-foreground">{activeCount}</span> of 8 features active
          </span>
          <Button
            variant="ghost"
            size="sm"
            onClick={resetToDefaults}
            className="text-muted-foreground hover:text-foreground gap-1.5"
          >
            <RotateCcw className="h-3.5 w-3.5" />
            Reset all to defaults
          </Button>
        </div>
      </motion.div>

      {/* Reading */}
      <motion.div initial={{ opacity: 0, y: 16 }} animate={{ opacity: 1, y: 0 }} transition={{ delay: 0.05 }}>
        <SkillFeatureSection
          title="Reading"
          icon={BookOpen}
          accentColor="text-blue-500"
          accentBg="bg-blue-500/10"
        >
          <FeatureToggleRow
            skill="reading"
            featureKey="telemetry"
            icon={Activity}
            title="Time & Friction Tracking"
            description="Records how long you spend per question and how many times you re-read a paragraph. Adds a brief analysis step after you submit."
          />
          <FeatureToggleRow
            skill="reading"
            featureKey="confidenceFlags"
            icon={Brain}
            title="Uma Confidence Insights"
            description='Flags correct answers you hesitated on as "Low Confidence Wins" with a specific drill recommendation. Requires Telemetry.'
            badge="Advanced"
            autoEnabledNote="Reading Telemetry was automatically enabled — Confidence Flags requires it."
          />
        </SkillFeatureSection>
      </motion.div>

      {/* Writing */}
      <motion.div initial={{ opacity: 0, y: 16 }} animate={{ opacity: 1, y: 0 }} transition={{ delay: 0.1 }}>
        <SkillFeatureSection
          title="Writing"
          icon={PenTool}
          accentColor="text-orange-500"
          accentBg="bg-orange-500/10"
        >
          <FeatureToggleRow
            skill="writing"
            featureKey="scaffoldMode"
            icon={Lock}
            title="Band Booster Scaffold"
            description="Locks each sentence until it reaches your target band. Builds muscle memory but slows down writing sessions."
            badge="Advanced"
          />
          <FeatureToggleRow
            skill="writing"
            featureKey="liveEvaluation"
            icon={Zap}
            title="Live AI Evaluation"
            description="Sends each sentence to AI as you type (800ms delay). Requires an active backend. Automatically enables Scaffold Mode."
            badge="Experimental"
          />
        </SkillFeatureSection>
      </motion.div>

      {/* Listening */}
      <motion.div initial={{ opacity: 0, y: 16 }} animate={{ opacity: 1, y: 0 }} transition={{ delay: 0.15 }}>
        <SkillFeatureSection
          title="Listening"
          icon={Headphones}
          accentColor="text-green-500"
          accentBg="bg-green-500/10"
        >
          <FeatureToggleRow
            skill="listening"
            featureKey="acousticLevel"
            icon={Headphones}
            title="Acoustic Environment"
            description="Level 1: clean studio recording. Level 2: simulates exam hall echo and older headphones via Web Audio DSP."
            options={[
              { value: 1, label: 'Level 1 — Studio' },
              { value: 2, label: 'Level 2 — Exam Room' },
            ]}
          />
          <FeatureToggleRow
            skill="listening"
            featureKey="telemetry"
            icon={Activity}
            title="Playback Telemetry"
            description="Logs every pause and rewind with millisecond timestamps for post-session hesitation analysis."
          />
        </SkillFeatureSection>
      </motion.div>

      {/* Speaking */}
      <motion.div initial={{ opacity: 0, y: 16 }} animate={{ opacity: 1, y: 0 }} transition={{ delay: 0.2 }}>
        <SkillFeatureSection
          title="Speaking"
          icon={Mic}
          accentColor="text-purple-500"
          accentBg="bg-purple-500/10"
        >
          <FeatureToggleRow
            skill="speaking"
            featureKey="mutationEngine"
            icon={Sparkles}
            title="Language Mutation Engine"
            description="After your recording, generates three upgraded versions of your response for shadowing practice. Adds ~10s."
            badge="Advanced"
          />
          <FeatureToggleRow
            skill="speaking"
            featureKey="workletRecorder"
            icon={Mic2}
            title="High-Fidelity Recorder"
            description="Uses AudioWorklet for 16kHz mono recording with real-time fluency metrics. Requires a modern browser (Chrome/Edge)."
            badge="Experimental"
          />
        </SkillFeatureSection>
      </motion.div>

      {/* Footer note */}
      <p className="text-xs text-muted-foreground text-center pb-4">
        Changes are saved automatically and synced to your profile.
        You can also override features per-session from the config panels.
      </p>
    </div>
  )
}
