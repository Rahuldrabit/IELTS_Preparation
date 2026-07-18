'use client'

import { useRouter } from 'next/navigation'
import { motion } from 'framer-motion'
import { Trophy, Target, TrendingUp, Brain, BookOpen, AlertCircle } from 'lucide-react'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Badge } from '@/components/ui/badge'
import { Progress } from '@/components/ui/progress'
import type { DiagnosticReport } from '@/lib/services/mocktest'

interface Props {
  report: DiagnosticReport | null
  mockTestId: number
}

export function DiagnosticReportView({ report, mockTestId }: Props) {
  const router = useRouter()

  if (!report) {
    return (
      <div className="flex flex-col items-center justify-center min-h-[400px] gap-4">
        <AlertCircle className="h-10 w-10 text-muted-foreground" />
        <p className="text-muted-foreground">No diagnostic report available</p>
        <Button onClick={() => router.push('/practice/mock-test')}>
          Back to Mock Tests
        </Button>
      </div>
    )
  }

  return (
    <div className="space-y-6 max-w-4xl mx-auto">
      {/* Overall Band */}
      <motion.div initial={{ opacity: 0, scale: 0.9 }} animate={{ opacity: 1, scale: 1 }}>
        <Card className="border-primary/30 bg-primary/5">
          <CardContent className="p-8 text-center">
            <Trophy className="h-12 w-12 text-primary mx-auto mb-4" />
            <p className="text-sm text-muted-foreground mb-2">Overall Band Score</p>
            <p className="text-5xl font-bold text-primary mb-4">{report.overall_band}</p>
            {report.target_band_gap !== null && report.target_band_gap > 0 && (
              <p className="text-sm text-muted-foreground">
                {report.target_band_gap} bands from your target
              </p>
            )}
          </CardContent>
        </Card>
      </motion.div>

      {/* Per-skill breakdown */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
        {[
          { label: 'Listening', band: report.listening_band, color: 'text-green-500' },
          { label: 'Reading', band: report.reading_band, color: 'text-blue-500' },
          { label: 'Writing', band: report.writing_band, color: 'text-orange-500' },
          { label: 'Speaking', band: report.speaking_band, color: 'text-purple-500' },
        ].map((skill) => (
          <Card key={skill.label}>
            <CardContent className="p-4 text-center">
              <p className="text-xs text-muted-foreground mb-1">{skill.label}</p>
              <p className={`text-2xl font-bold ${skill.color}`}>{skill.band}</p>
            </CardContent>
          </Card>
        ))}
      </div>

      {/* Summary */}
      <Card>
        <CardHeader>
          <CardTitle className="text-base flex items-center gap-2">
            <Brain className="h-4 w-4" /> AI Analysis Summary
          </CardTitle>
        </CardHeader>
        <CardContent>
          <p className="text-sm leading-relaxed">{report.summary_text}</p>
        </CardContent>
      </Card>

      {/* Vocabulary & Grammar */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        <Card>
          <CardHeader>
            <CardTitle className="text-base flex items-center gap-2">
              <BookOpen className="h-4 w-4" /> Vocabulary
            </CardTitle>
          </CardHeader>
          <CardContent className="space-y-3">
            <div className="flex items-center justify-between">
              <span className="text-sm">CEFR Level</span>
              <Badge variant="outline">{report.vocabulary_analysis.cefr_level}</Badge>
            </div>
            <div>
              <div className="flex items-center justify-between text-sm mb-1">
                <span>Lexical Diversity</span>
                <span>{report.vocabulary_analysis.lexical_diversity_score}%</span>
              </div>
              <Progress value={report.vocabulary_analysis.lexical_diversity_score} />
            </div>
            <div>
              <div className="flex items-center justify-between text-sm mb-1">
                <span>Academic Words</span>
                <span>{report.vocabulary_analysis.academic_word_percentage}%</span>
              </div>
              <Progress value={report.vocabulary_analysis.academic_word_percentage} />
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle className="text-base flex items-center gap-2">
              <Target className="h-4 w-4" /> Grammar
            </CardTitle>
          </CardHeader>
          <CardContent className="space-y-3">
            <div className="flex items-center justify-between">
              <span className="text-sm">Error Rate</span>
              <Badge variant="outline">{report.grammar_analysis.error_rate} per 100 words</Badge>
            </div>
            <div className="text-sm space-y-1">
              <p className="font-medium">Sentence Complexity:</p>
              <div className="flex gap-2">
                <Badge variant="secondary">Simple: {report.grammar_analysis.sentence_complexity.simple}%</Badge>
                <Badge variant="secondary">Compound: {report.grammar_analysis.sentence_complexity.compound}%</Badge>
                <Badge variant="secondary">Complex: {report.grammar_analysis.sentence_complexity.complex}%</Badge>
              </div>
            </div>
            {report.grammar_analysis.common_mistakes.length > 0 && (
              <div className="text-sm">
                <p className="font-medium mb-1">Common Mistakes:</p>
                <ul className="list-disc list-inside text-muted-foreground">
                  {report.grammar_analysis.common_mistakes.map((m, i) => (
                    <li key={i}>{m}</li>
                  ))}
                </ul>
              </div>
            )}
          </CardContent>
        </Card>
      </div>

      {/* Strengths & Weaknesses */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        <Card>
          <CardHeader>
            <CardTitle className="text-base text-green-600">Strengths</CardTitle>
          </CardHeader>
          <CardContent>
            <ul className="space-y-2">
              {report.top_strengths.map((s, i) => (
                <li key={i} className="flex items-start gap-2 text-sm">
                  <TrendingUp className="h-4 w-4 text-green-500 shrink-0 mt-0.5" />
                  {s}
                </li>
              ))}
            </ul>
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle className="text-base text-red-600">Areas to Improve</CardTitle>
          </CardHeader>
          <CardContent>
            <ul className="space-y-2">
              {report.key_weaknesses.map((w, i) => (
                <li key={i} className="flex items-start gap-2 text-sm">
                  <Target className="h-4 w-4 text-red-500 shrink-0 mt-0.5" />
                  {w}
                </li>
              ))}
            </ul>
          </CardContent>
        </Card>
      </div>

      {/* Recommendations */}
      <Card>
        <CardHeader>
          <CardTitle className="text-base">Recommended Next Steps</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div>
              <p className="text-sm font-medium mb-2">Focus Areas:</p>
              <ul className="space-y-1">
                {report.recommended_focus_areas.map((area, i) => (
                  <li key={i} className="text-sm text-muted-foreground">• {area}</li>
                ))}
              </ul>
            </div>
            <div>
              <p className="text-sm font-medium mb-2">Study Plan Adjustments:</p>
              <ul className="space-y-1">
                {report.study_plan_adjustments.map((adj, i) => (
                  <li key={i} className="text-sm text-muted-foreground">• {adj}</li>
                ))}
              </ul>
            </div>
          </div>
          {report.estimated_weeks_to_target && (
            <div className="mt-4 p-3 rounded-lg bg-primary/5 border border-primary/20">
              <p className="text-sm">
                Estimated time to target: <strong>{report.estimated_weeks_to_target} weeks</strong> with consistent practice
              </p>
            </div>
          )}
        </CardContent>
      </Card>

      {/* Question Type Breakdown */}
      {report.question_type_breakdown.length > 0 && (
        <Card>
          <CardHeader>
            <CardTitle className="text-base">Question Type Accuracy</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="space-y-3">
              {report.question_type_breakdown.map((qt) => (
                <div key={qt.question_type} className="flex items-center gap-3">
                  <span className="text-sm w-48 shrink-0">{qt.question_type.replace(/_/g, ' ')}</span>
                  <Progress value={qt.accuracy_percent} className="flex-1" />
                  <span className="text-sm font-mono w-20 text-right">
                    {qt.correct}/{qt.total} ({qt.accuracy_percent.toFixed(0)}%)
                  </span>
                </div>
              ))}
            </div>
          </CardContent>
        </Card>
      )}

      {/* Actions */}
      <div className="flex gap-3 justify-center pb-8">
        <Button variant="outline" onClick={() => router.push('/practice/mock-test')}>
          Back to Mock Tests
        </Button>
        <Button onClick={() => router.push('/practice')}>
          Start Practicing Weak Areas
        </Button>
      </div>
    </div>
  )
}
