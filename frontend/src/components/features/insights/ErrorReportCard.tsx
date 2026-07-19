'use client'

import { useState, useEffect } from 'react'
import { motion, AnimatePresence } from 'framer-motion'
import { 
  Dna, 
  AlertTriangle, 
  ChevronDown, 
  ChevronUp, 
  Target, 
  Lightbulb,
  Play,
  RefreshCw,
  TrendingUp
} from 'lucide-react'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Badge } from '@/components/ui/badge'
import { cn } from '@/lib/utils'
import { 
  analyticsApi, 
  WeeklyErrorReport, 
  ErrorSignature,
  MicroExerciseSet 
} from '@/lib/services/analytics'
import { agentApi, SignatureItem } from '@/lib/services/agent'

interface ErrorReportCardProps {
  className?: string
}

const severityColors = {
  low: 'bg-green-500/10 text-green-600 border-green-200',
  medium: 'bg-yellow-500/10 text-yellow-600 border-yellow-200',
  high: 'bg-red-500/10 text-red-600 border-red-200',
}

const skillColors: Record<string, string> = {
  reading: 'text-blue-500',
  listening: 'text-green-500',
  writing: 'text-purple-500',
  speaking: 'text-orange-500',
  grammar: 'text-pink-500',
}

export function ErrorReportCard({ className }: ErrorReportCardProps) {
  const [report, setReport] = useState<WeeklyErrorReport | null>(null)
  const [signatures, setSignatures] = useState<ErrorSignature[]>([])
  const [loading, setLoading] = useState(true)
  const [running, setRunning] = useState(false)
  const [expandedSignature, setExpandedSignature] = useState<string | null>(null)
  const [exercises, setExercises] = useState<MicroExerciseSet | null>(null)
  const [loadingExercises, setLoadingExercises] = useState(false)

  useEffect(() => {
    loadReport()
  }, [])

  const loadReport = async () => {
    setLoading(true)
    try {
      const [reportData, signaturesData] = await Promise.all([
        analyticsApi.getErrorReport(),
        analyticsApi.getErrorSignatures(),
      ])
      setReport(reportData)
      setSignatures(signaturesData)
    } catch (error) {
      console.error('Failed to load error report:', error)
    } finally {
      setLoading(false)
    }
  }

  const runAnalysis = async () => {
    setRunning(true)
    try {
      await analyticsApi.runErrorReport()
      await loadReport()
    } catch (error) {
      console.error('Failed to run analysis:', error)
    } finally {
      setRunning(false)
    }
  }

  const loadExercises = async (signature: ErrorSignature) => {
    setLoadingExercises(true)
    try {
      // Convert ErrorSignature to SignatureItem format
      const sigItem: SignatureItem = {
        skill: signature.skill,
        question_type: signature.question_type || undefined,
        error_type: signature.error_type || undefined,
        pattern_label: signature.pattern_label,
        pattern_key: signature.pattern_key,
        severity: signature.severity,
        occurrences: signature.occurrences,
        evidence: signature.example_refs || [],
        recommendation: '',
      }
      
      const result = await agentApi.generateMicroExercises(sigItem, 5)
      setExercises(result)
    } catch (error) {
      console.error('Failed to load exercises:', error)
    } finally {
      setLoadingExercises(false)
    }
  }

  if (loading) {
    return (
      <Card className={cn('animate-pulse', className)}>
        <CardContent className="p-6">
          <div className="h-32 bg-muted rounded" />
        </CardContent>
      </Card>
    )
  }

  if (!report && signatures.length === 0) {
    return (
      <Card className={className}>
        <CardHeader>
          <CardTitle className="text-base flex items-center gap-2">
            <Dna className="h-4 w-4" />
            Error DNA
          </CardTitle>
        </CardHeader>
        <CardContent className="text-center py-8">
          <AlertTriangle className="h-12 w-12 mx-auto text-muted-foreground mb-4" />
          <p className="text-muted-foreground mb-4">
            No error analysis yet. Complete some practice sessions first!
          </p>
          <Button onClick={runAnalysis} disabled={running}>
            {running ? (
              <>
                <RefreshCw className="h-4 w-4 mr-2 animate-spin" />
                Analyzing...
              </>
            ) : (
              <>
                <Play className="h-4 w-4 mr-2" />
                Run Analysis
              </>
            )}
          </Button>
        </CardContent>
      </Card>
    )
  }

  return (
    <Card className={className}>
      <CardHeader>
        <div className="flex items-center justify-between">
          <CardTitle className="text-base flex items-center gap-2">
            <Dna className="h-4 w-4" />
            Error DNA
          </CardTitle>
          <Button 
            variant="ghost" 
            size="sm" 
            onClick={runAnalysis} 
            disabled={running}
          >
            {running ? (
              <RefreshCw className="h-4 w-4 animate-spin" />
            ) : (
              <RefreshCw className="h-4 w-4" />
            )}
          </Button>
        </div>
      </CardHeader>
      <CardContent className="space-y-6">
        {/* Headline */}
        {report && (
          <motion.div
            initial={{ opacity: 0, y: 10 }}
            animate={{ opacity: 1, y: 0 }}
            className="p-4 rounded-lg bg-gradient-to-r from-primary/5 to-secondary/5 border"
          >
            <p className="font-medium text-lg">{report.headline}</p>
            <p className="text-sm text-muted-foreground mt-2">
              {report.insight_text}
            </p>
          </motion.div>
        )}

        {/* Top Signatures */}
        <div className="space-y-3">
          <h3 className="text-sm font-medium flex items-center gap-2">
            <AlertTriangle className="h-4 w-4 text-orange-500" />
            Top Error Patterns
          </h3>
          
          {signatures.slice(0, 5).map((sig, index) => (
            <motion.div
              key={sig.id}
              initial={{ opacity: 0, x: -20 }}
              animate={{ opacity: 1, x: 0 }}
              transition={{ delay: index * 0.1 }}
            >
              <div
                className={cn(
                  'p-3 rounded-lg border cursor-pointer transition-all',
                  expandedSignature === sig.pattern_key 
                    ? 'border-primary bg-primary/5' 
                    : 'hover:border-muted-foreground/30'
                )}
                onClick={() => {
                  setExpandedSignature(
                    expandedSignature === sig.pattern_key ? null : sig.pattern_key
                  )
                  setExercises(null)
                }}
              >
                <div className="flex items-start justify-between">
                  <div className="flex-1">
                    <div className="flex items-center gap-2">
                      <span className={cn(
                        'text-xs font-medium uppercase',
                        skillColors[sig.skill] || 'text-muted-foreground'
                      )}>
                        {sig.skill}
                      </span>
                      <Badge 
                        variant="outline" 
                        className={cn('text-xs', severityColors[sig.severity])}
                      >
                        {sig.severity}
                      </Badge>
                      <Badge variant="secondary" className="text-xs">
                        {sig.occurrences}×
                      </Badge>
                    </div>
                    <p className="font-medium mt-1">{sig.pattern_label}</p>
                  </div>
                  {expandedSignature === sig.pattern_key ? (
                    <ChevronUp className="h-4 w-4 text-muted-foreground" />
                  ) : (
                    <ChevronDown className="h-4 w-4 text-muted-foreground" />
                  )}
                </div>

                <AnimatePresence>
                  {expandedSignature === sig.pattern_key && (
                    <motion.div
                      initial={{ height: 0, opacity: 0 }}
                      animate={{ height: 'auto', opacity: 1 }}
                      exit={{ height: 0, opacity: 0 }}
                      className="overflow-hidden"
                    >
                      <div className="mt-3 pt-3 border-t space-y-3">
                        {sig.question_type && (
                          <p className="text-xs text-muted-foreground">
                            Question type: <span className="font-mono">{sig.question_type}</span>
                          </p>
                        )}

                        {/* Practice Button */}
                        <Button
                          size="sm"
                          className="w-full"
                          onClick={(e) => {
                            e.stopPropagation()
                            loadExercises(sig)
                          }}
                          disabled={loadingExercises}
                        >
                          {loadingExercises ? (
                            <>
                              <RefreshCw className="h-4 w-4 mr-2 animate-spin" />
                              Generating...
                            </>
                          ) : (
                            <>
                              <Target className="h-4 w-4 mr-2" />
                              Practice Fix
                            </>
                          )}
                        </Button>

                        {/* Exercises */}
                        {exercises && exercises.pattern_key === sig.pattern_key && (
                          <div className="mt-4 space-y-3">
                            <div className="flex items-center gap-2 text-sm font-medium">
                              <Lightbulb className="h-4 w-4 text-yellow-500" />
                              Strategy: {exercises.strategy_tip}
                            </div>
                            
                            {exercises.exercises.slice(0, 3).map((ex, i) => (
                              <div key={ex.id} className="p-3 rounded bg-muted/50 text-sm">
                                <p className="font-medium">
                                  {i + 1}. {ex.question}
                                </p>
                                {ex.options && (
                                  <div className="mt-2 space-y-1">
                                    {ex.options.map((opt, j) => (
                                      <p key={j} className="text-muted-foreground">
                                        {String.fromCharCode(65 + j)}. {opt}
                                      </p>
                                    ))}
                                  </div>
                                )}
                                <p className="mt-2 text-xs text-green-600">
                                  ✓ {ex.correct_answer}
                                </p>
                              </div>
                            ))}
                          </div>
                        )}
                      </div>
                    </motion.div>
                  )}
                </AnimatePresence>
              </div>
            </motion.div>
          ))}
        </div>

        {/* Recommended Focus */}
        {report && (
          <div className="p-4 rounded-lg bg-gradient-to-r from-green-500/10 to-blue-500/10 border border-green-200">
            <div className="flex items-center gap-2 text-sm font-medium mb-1">
              <TrendingUp className="h-4 w-4 text-green-600" />
              Recommended Focus
            </div>
            <p className="text-sm">{report.recommended_focus}</p>
            <p className="text-xs text-muted-foreground mt-1">
              Pattern: {report.weak_pattern_identified}
            </p>
          </div>
        )}
      </CardContent>
    </Card>
  )
}
