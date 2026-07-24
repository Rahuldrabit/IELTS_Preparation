'use client'

import { useState, useEffect } from 'react'
import { motion, useAnimation, AnimatePresence } from 'framer-motion'
import { BrainCircuit, Target, Sparkles, Gift, TrendingUp, Users, Star, CheckCircle, Zap, BookOpen, Mic, PenLine, ChevronRight } from 'lucide-react'

// --- Data ---
const features = [
  {
    icon: BrainCircuit,
    color: 'from-violet-500 to-purple-600',
    bgColor: 'bg-violet-500/10',
    textColor: 'text-violet-400',
    title: 'AI In-Depth Evaluation',
    description: 'Instant Band Scores & detailed feedback on Writing and Speaking tasks.'
  },
  {
    icon: Target,
    color: 'from-blue-500 to-cyan-600',
    bgColor: 'bg-blue-500/10',
    textColor: 'text-blue-400',
    title: 'Custom Exam Generation',
    description: 'Unlimited personalized practice tests targeting your exact weak points.'
  },
  {
    icon: Sparkles,
    color: 'from-amber-500 to-orange-600',
    bgColor: 'bg-amber-500/10',
    textColor: 'text-amber-400',
    title: 'Personalized AI Guidance',
    description: 'A fully adaptive learning path built around your unique Error DNA.'
  },
  {
    icon: Gift,
    color: 'from-emerald-500 to-green-600',
    bgColor: 'bg-emerald-500/10',
    textColor: 'text-emerald-400',
    title: '2 Free Full Mock Tests',
    description: 'Two complete, fully-timed IELTS diagnostic tests, no credit card required.'
  }
]

const stats = [
  { value: 15000, suffix: '+', label: 'Active Students' },
  { value: 7.8, suffix: '', label: 'Avg. Band Score', decimals: 1 },
  { value: 94, suffix: '%', label: 'Pass Rate' },
]

const testimonial = {
  name: 'Rahul Sharma',
  university: 'University of Toronto',
  avatar: 'RS',
  band: '8.0',
  quote: 'I improved from Band 6.0 to 8.0 in just 6 weeks! The AI feedback was more precise than any human tutor I had.',
}

// --- Animated Counter ---
function AnimatedCounter({ value, suffix, decimals = 0 }: { value: number; suffix: string; decimals?: number }) {
  const [count, setCount] = useState(0)

  useEffect(() => {
    const duration = 2000
    const steps = 60
    const stepDuration = duration / steps
    const increment = value / steps
    let current = 0
    const timer = setInterval(() => {
      current += increment
      if (current >= value) {
        setCount(value)
        clearInterval(timer)
      } else {
        setCount(current)
      }
    }, stepDuration)
    return () => clearInterval(timer)
  }, [value])

  return <>{decimals > 0 ? count.toFixed(decimals) : Math.floor(count).toLocaleString()}{suffix}</>
}

// --- Live Score Preview Card ---
function LiveScoreCard() {
  const scores = [
    { label: 'Listening', value: 8.0, color: 'bg-violet-500' },
    { label: 'Reading', value: 7.5, color: 'bg-blue-500' },
    { label: 'Writing', value: 7.0, color: 'bg-amber-500' },
    { label: 'Speaking', value: 7.5, color: 'bg-emerald-500' },
  ]

  return (
    <motion.div
      initial={{ opacity: 0, x: 60 }}
      animate={{ opacity: 1, x: 0 }}
      transition={{ delay: 0.8, duration: 0.6, type: 'spring' }}
      className="absolute top-8 -right-4 w-52 bg-card/90 backdrop-blur-sm rounded-2xl border border-border/60 shadow-2xl p-4 z-20"
    >
      <div className="flex items-center justify-between mb-3">
        <span className="text-xs font-semibold text-muted-foreground uppercase tracking-wide">Band Prediction</span>
        <motion.span
          animate={{ opacity: [1, 0.4, 1] }}
          transition={{ repeat: Infinity, duration: 2 }}
          className="h-2 w-2 rounded-full bg-emerald-500"
        />
      </div>
      <div className="text-3xl font-black text-primary mb-3">7.5 <span className="text-sm font-normal text-muted-foreground">/ 9.0</span></div>
      <div className="space-y-2">
        {scores.map((s, i) => (
          <div key={i}>
            <div className="flex justify-between text-xs mb-1">
              <span className="text-muted-foreground">{s.label}</span>
              <span className="font-semibold">{s.value}</span>
            </div>
            <div className="h-1.5 rounded-full bg-muted overflow-hidden">
              <motion.div
                initial={{ width: 0 }}
                animate={{ width: `${(s.value / 9) * 100}%` }}
                transition={{ delay: 1.2 + i * 0.1, duration: 0.8 }}
                className={`h-full rounded-full ${s.color}`}
              />
            </div>
          </div>
        ))}
      </div>
    </motion.div>
  )
}

// --- Floating Notification Card ---
function FloatingNotification({ delay }: { delay: number }) {
  return (
    <motion.div
      initial={{ opacity: 0, y: 30, x: -30 }}
      animate={{ opacity: 1, y: 0, x: 0 }}
      transition={{ delay, duration: 0.6, type: 'spring' }}
      className="absolute bottom-16 -left-6 w-56 bg-card/90 backdrop-blur-sm rounded-2xl border border-border/60 shadow-2xl p-3 z-20"
    >
      <div className="flex items-start gap-3">
        <div className="h-9 w-9 rounded-xl bg-emerald-500/20 flex items-center justify-center flex-shrink-0">
          <CheckCircle className="h-5 w-5 text-emerald-500" />
        </div>
        <div>
          <p className="text-xs font-semibold">Essay graded!</p>
          <p className="text-xs text-muted-foreground mt-0.5">Task 2 · Band 7.0</p>
          <p className="text-xs text-emerald-500 mt-0.5 font-medium">+0.5 from last attempt</p>
        </div>
      </div>
    </motion.div>
  )
}


export function AuthShowcase() {
  return (
    <div className="hidden lg:flex flex-col justify-center w-full min-h-screen p-10 xl:p-14 relative overflow-hidden bg-gradient-to-br from-slate-950 via-slate-900 to-slate-950">

      {/* Deep background glow orbs */}
      <div className="absolute inset-0 overflow-hidden pointer-events-none">
        <div className="absolute -top-1/4 -left-1/4 w-[600px] h-[600px] bg-primary/15 rounded-full blur-[120px]" />
        <div className="absolute -bottom-1/4 -right-1/4 w-[500px] h-[500px] bg-blue-600/10 rounded-full blur-[100px]" />
        <div className="absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 w-[300px] h-[300px] bg-violet-600/10 rounded-full blur-[80px]" />
      </div>

      {/* Subtle grid overlay */}
      <div
        className="absolute inset-0 opacity-[0.03]"
        style={{
          backgroundImage: 'linear-gradient(rgba(255,255,255,0.5) 1px, transparent 1px), linear-gradient(90deg, rgba(255,255,255,0.5) 1px, transparent 1px)',
          backgroundSize: '40px 40px'
        }}
      />

      {/* Floating UI Cards */}
      <div className="relative z-10 max-w-md mx-auto w-full">
        <LiveScoreCard />
        <FloatingNotification delay={1.2} />

        {/* Hero Text */}
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.6 }}
          className="mb-10"
        >
          <h1 className="text-4xl xl:text-5xl font-black tracking-tight text-white leading-tight mb-4">
            Achieve Your
            <span className="block bg-gradient-to-r from-primary via-violet-400 to-blue-400 bg-clip-text text-transparent">
              Target Band Score
            </span>
            Faster Than Ever
          </h1>
          <p className="text-slate-400 text-base leading-relaxed">
            The world's most advanced AI-powered IELTS learning system. Adaptive, personalized, and proven.
          </p>
        </motion.div>

        {/* Stats Row */}
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.4, duration: 0.5 }}
          className="grid grid-cols-3 gap-3 mb-10"
        >
          {stats.map((stat, i) => (
            <div key={i} className="rounded-xl bg-white/5 border border-white/10 p-3 text-center backdrop-blur-sm">
              <p className="text-xl xl:text-2xl font-black text-white">
                <AnimatedCounter value={stat.value} suffix={stat.suffix} decimals={(stat as any).decimals} />
              </p>
              <p className="text-xs text-slate-400 mt-0.5">{stat.label}</p>
            </div>
          ))}
        </motion.div>

        {/* Feature List */}
        <div className="space-y-3 mb-10">
          {features.map((feature, idx) => {
            const Icon = feature.icon
            return (
              <motion.div
                key={idx}
                initial={{ opacity: 0, x: -20 }}
                animate={{ opacity: 1, x: 0 }}
                transition={{ delay: 0.5 + idx * 0.1, duration: 0.5 }}
                className="flex items-center gap-4 rounded-xl bg-white/[0.04] border border-white/[0.08] p-4 hover:bg-white/[0.07] hover:border-white/20 transition-all group cursor-default"
              >
                <div className={`flex-shrink-0 h-10 w-10 rounded-xl ${feature.bgColor} flex items-center justify-center`}>
                  <Icon className={`h-5 w-5 ${feature.textColor}`} />
                </div>
                <div className="flex-1 min-w-0">
                  <p className="text-sm font-semibold text-white">{feature.title}</p>
                  <p className="text-xs text-slate-400 mt-0.5 leading-relaxed">{feature.description}</p>
                </div>
                <ChevronRight className="h-4 w-4 text-slate-600 group-hover:text-slate-400 transition-colors flex-shrink-0" />
              </motion.div>
            )
          })}
        </div>

        {/* Testimonial */}
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 1.0, duration: 0.6 }}
          className="rounded-2xl bg-white/[0.04] border border-white/[0.08] p-5 backdrop-blur-sm"
        >
          <div className="flex items-center gap-1 mb-3">
            {[...Array(5)].map((_, i) => (
              <Star key={i} className="h-4 w-4 fill-amber-400 text-amber-400" />
            ))}
          </div>
          <p className="text-sm text-slate-300 leading-relaxed mb-4 italic">"{testimonial.quote}"</p>
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-3">
              <div className="h-9 w-9 rounded-full bg-gradient-to-br from-primary to-violet-600 flex items-center justify-center text-xs font-bold text-white">
                {testimonial.avatar}
              </div>
              <div>
                <p className="text-sm font-semibold text-white">{testimonial.name}</p>
                <p className="text-xs text-slate-400">{testimonial.university}</p>
              </div>
            </div>
            <div className="text-right">
              <p className="text-xs text-slate-500">Achieved</p>
              <p className="text-lg font-black text-emerald-400">Band {testimonial.band}</p>
            </div>
          </div>
        </motion.div>
      </div>
    </div>
  )
}
