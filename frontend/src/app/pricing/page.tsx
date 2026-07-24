'use client'

import { useState } from 'react'
import { motion, AnimatePresence } from 'framer-motion'
import { Check, X, Sparkles, MessageCircle, ArrowRight } from 'lucide-react'
import { ThemeToggle } from '@/components/ui/theme-toggle'
import Link from 'next/link'

const WHATSAPP_NUMBER = '+880 17XX-XXXXXX' // TODO: Update with actual WhatsApp Number

const plans = [
  {
    name: 'Free Trial',
    price: '0',
    duration: '2 Days',
    description: 'Perfect to test the waters and experience AI precision.',
    features: [
      '2 Free Full Mock Tests',
      'AI In-Depth Evaluation (2 tests)',
      'Basic Performance Analytics',
      'Community Support'
    ],
    limitations: [
      'Custom Exam Generation',
      'Advanced Error DNA Path',
      'Unlimited AI Scoring'
    ],
    buttonText: 'Current Plan',
    highlighted: false,
    disabled: true
  },
  {
    name: 'Pro 15 Days',
    price: '5',
    duration: '15 Days',
    description: 'A focused sprint to maximize your band score before the exam.',
    features: [
      'Unlimited Full Mock Tests',
      'Instant AI Writing & Speaking Evaluation',
      'Custom Exam Generation',
      'Advanced Error DNA Path',
      'Priority Support'
    ],
    limitations: [],
    buttonText: 'Upgrade for $5',
    highlighted: false,
    disabled: false,
    planId: '15_days'
  },
  {
    name: 'Pro 2 Months',
    price: '15',
    duration: '2 Months',
    description: 'Complete mastery. Everything you need to guarantee a Band 8.0+',
    features: [
      'Everything in 15 Days, plus:',
      'Extended access for deep practice',
      'Historical progress tracking',
      'AI guided study planner',
      '1-on-1 WhatsApp Support'
    ],
    limitations: [],
    buttonText: 'Upgrade for $15',
    highlighted: true,
    disabled: false,
    planId: '2_months'
  }
]

export default function PricingPage() {
  const [selectedPlan, setSelectedPlan] = useState<string | null>(null)

  return (
    <div className="min-h-screen bg-background relative overflow-hidden pb-20">
      {/* Navbar space */}
      <div className="absolute top-4 right-4 z-50">
        <ThemeToggle />
      </div>
      <div className="absolute top-4 left-4 z-50">
        <Link href="/" className="font-bold text-xl tracking-tight text-primary">
          IELTS Tutor
        </Link>
      </div>

      {/* Background Decorators */}
      <div className="absolute top-[-10%] left-[-10%] w-[600px] h-[600px] bg-primary/10 rounded-full blur-[120px] pointer-events-none" />
      <div className="absolute top-[40%] right-[-10%] w-[500px] h-[500px] bg-blue-500/10 rounded-full blur-[100px] pointer-events-none" />

      <div className="max-w-7xl mx-auto px-4 pt-32 relative z-10">
        <div className="text-center max-w-3xl mx-auto mb-16">
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.5 }}
          >
            <h1 className="text-4xl md:text-5xl font-black tracking-tight mb-6">
              Simple pricing for <span className="text-primary">serious results.</span>
            </h1>
            <p className="text-lg text-muted-foreground">
              Every account starts with a free 2-day trial including 2 complete mock tests. 
              Upgrade to Pro to unlock unlimited AI evaluation and custom exam generation.
            </p>
          </motion.div>
        </div>

        <div className="grid md:grid-cols-3 gap-8 max-w-6xl mx-auto">
          {plans.map((plan, idx) => (
            <motion.div
              key={plan.name}
              initial={{ opacity: 0, y: 30 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ delay: idx * 0.15, duration: 0.6, type: 'spring' }}
              className={`relative flex flex-col rounded-3xl p-8 shadow-xl ${
                plan.highlighted 
                  ? 'bg-primary text-primary-foreground border-2 border-primary ring-4 ring-primary/20 scale-105 z-10' 
                  : 'bg-card border border-border/50'
              }`}
            >
              {plan.highlighted && (
                <div className="absolute -top-4 left-1/2 -translate-x-1/2 bg-gradient-to-r from-amber-400 to-orange-500 text-white text-xs font-bold px-3 py-1 rounded-full flex items-center shadow-lg">
                  <Sparkles className="w-3 h-3 mr-1" /> Most Popular
                </div>
              )}
              
              <div className="mb-6">
                <h3 className={`text-xl font-bold mb-2 ${plan.highlighted ? 'text-primary-foreground' : 'text-foreground'}`}>
                  {plan.name}
                </h3>
                <div className="flex items-baseline gap-2">
                  <span className="text-4xl font-black">${plan.price}</span>
                  <span className={`text-sm ${plan.highlighted ? 'text-primary-foreground/80' : 'text-muted-foreground'}`}>
                    / {plan.duration}
                  </span>
                </div>
                <p className={`mt-4 text-sm ${plan.highlighted ? 'text-primary-foreground/90' : 'text-muted-foreground'}`}>
                  {plan.description}
                </p>
              </div>

              <div className="flex-1 space-y-4 mb-8">
                {plan.features.map(feature => (
                  <div key={feature} className="flex items-start gap-3">
                    <Check className={`w-5 h-5 shrink-0 ${plan.highlighted ? 'text-primary-foreground' : 'text-primary'}`} />
                    <span className="text-sm">{feature}</span>
                  </div>
                ))}
                {plan.limitations.map(limit => (
                  <div key={limit} className="flex items-start gap-3">
                    <X className="w-5 h-5 shrink-0 text-muted-foreground/50" />
                    <span className="text-sm text-muted-foreground/50 line-through">{limit}</span>
                  </div>
                ))}
              </div>

              <button
                disabled={plan.disabled}
                onClick={() => setSelectedPlan(plan.name)}
                className={`w-full py-4 rounded-xl font-bold transition-all flex justify-center items-center gap-2 ${
                  plan.disabled
                    ? 'bg-muted text-muted-foreground cursor-not-allowed'
                    : plan.highlighted
                      ? 'bg-background text-primary hover:bg-background/90 shadow-lg'
                      : 'bg-primary text-primary-foreground hover:bg-primary/90 shadow-lg hover:shadow-primary/25'
                }`}
              >
                {plan.buttonText} {!plan.disabled && <ArrowRight className="w-4 h-4" />}
              </button>
            </motion.div>
          ))}
        </div>
      </div>

      {/* Payment Modal */}
      <AnimatePresence>
        {selectedPlan && (
          <div className="fixed inset-0 z-[100] flex items-center justify-center p-4">
            <motion.div 
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              exit={{ opacity: 0 }}
              onClick={() => setSelectedPlan(null)}
              className="absolute inset-0 bg-background/80 backdrop-blur-sm"
            />
            <motion.div
              initial={{ opacity: 0, scale: 0.95, y: 20 }}
              animate={{ opacity: 1, scale: 1, y: 0 }}
              exit={{ opacity: 0, scale: 0.95, y: 20 }}
              className="relative w-full max-w-md bg-card border border-border shadow-2xl rounded-3xl p-8 overflow-hidden"
            >
              <button 
                onClick={() => setSelectedPlan(null)}
                className="absolute top-4 right-4 p-2 rounded-full hover:bg-muted transition-colors"
              >
                <X className="w-5 h-5 text-muted-foreground" />
              </button>
              
              <div className="w-12 h-12 bg-green-500/10 rounded-2xl flex items-center justify-center mb-6">
                <MessageCircle className="w-6 h-6 text-green-500" />
              </div>

              <h2 className="text-2xl font-bold mb-2">Manual Verification</h2>
              <p className="text-muted-foreground mb-8">
                To activate your <strong>{selectedPlan}</strong> subscription, please text us directly on WhatsApp. We will process your request instantly.
              </p>

              <div className="bg-muted/50 rounded-2xl p-6 border border-border text-center mb-8">
                <p className="text-sm text-muted-foreground mb-2">Send us a message at</p>
                <p className="text-3xl font-black tracking-tight text-primary">{WHATSAPP_NUMBER}</p>
              </div>

              <div className="space-y-4">
                <p className="text-sm font-medium text-center">What happens next?</p>
                <ol className="text-sm text-muted-foreground space-y-3 pl-4 list-decimal list-inside">
                  <li>Message us your registered email address.</li>
                  <li>We will share the exact payment details (e.g. bKash).</li>
                  <li>Once paid, your account unlocks immediately!</li>
                </ol>
              </div>
            </motion.div>
          </div>
        )}
      </AnimatePresence>
    </div>
  )
}
