'use client'

import { useEffect } from 'react'
import { useRouter } from 'next/navigation'
import { motion } from 'framer-motion'
import { ArrowLeft, GitBranch, CheckCircle2, AlertCircle, Clock } from 'lucide-react'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Badge } from '@/components/ui/badge'
import { Progress } from '@/components/ui/progress'
import { cn } from '@/lib/utils'
import { useGrammarStore } from '@/lib/store/grammarStore'

export default function KnowledgeGraphPage() {
  const router = useRouter()
  const { knowledgeGraph, isLoading, fetchKnowledgeGraph } = useGrammarStore()

  useEffect(() => {
    fetchKnowledgeGraph()
  }, [fetchKnowledgeGraph])

  if (isLoading && !knowledgeGraph) {
    return (
      <div className="flex items-center justify-center h-32">
        <GitBranch className="h-6 w-6 text-primary animate-pulse" />
      </div>
    )
  }

  // Group nodes by module
  const nodesByModule: Record<string, Array<{ topic_id: number; topic_name: string; module: string; mastery: number; confidence: number; recent_performance?: number[]; last_reviewed?: string; prerequisites: number[] }>> = {}
  if (knowledgeGraph) {
    knowledgeGraph.nodes.forEach(node => {
      if (!nodesByModule[node.module]) nodesByModule[node.module] = []
      nodesByModule[node.module].push(node)
    })
  }

  const getMasteryColor = (mastery: number) => {
    if (mastery >= 80) return 'text-green-600 bg-green-500/10 border-green-500/20'
    if (mastery >= 50) return 'text-amber-600 bg-amber-500/10 border-amber-500/20'
    if (mastery >= 20) return 'text-orange-600 bg-orange-500/10 border-orange-500/20'
    return 'text-red-600 bg-red-500/10 border-red-500/20'
  }

  const getConfidenceLabel = (confidence: number) => {
    if (confidence >= 0.8) return 'High'
    if (confidence >= 0.5) return 'Medium'
    if (confidence >= 0.2) return 'Low'
    return 'Very Low'
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center gap-4">
        <Button variant="ghost" size="icon" onClick={() => router.push('/practice/grammar')}>
          <ArrowLeft className="h-4 w-4" />
        </Button>
        <div>
          <h1 className="text-2xl font-bold flex items-center gap-2">
            <GitBranch className="h-6 w-6 text-primary" />
            Grammar Knowledge Graph
          </h1>
          <p className="text-muted-foreground">
            Your mastery of each grammar topic at a glance
          </p>
        </div>
      </div>

      {/* Summary */}
      <Card>
        <CardContent className="p-4">
          <div className="grid grid-cols-3 gap-4 text-center">
            <div>
              <p className="text-2xl font-bold text-green-600">
                {knowledgeGraph?.nodes.filter(n => n.mastery >= 80).length || 0}
              </p>
              <p className="text-xs text-muted-foreground">Mastered</p>
            </div>
            <div>
              <p className="text-2xl font-bold text-amber-600">
                {knowledgeGraph?.nodes.filter(n => n.mastery >= 20 && n.mastery < 80).length || 0}
              </p>
              <p className="text-xs text-muted-foreground">In Progress</p>
            </div>
            <div>
              <p className="text-2xl font-bold text-red-600">
                {knowledgeGraph?.nodes.filter(n => n.mastery < 20).length || 0}
              </p>
              <p className="text-xs text-muted-foreground">Not Started</p>
            </div>
          </div>
        </CardContent>
      </Card>

      {/* Graph by Module */}
      {Object.entries(nodesByModule).map(([moduleName, nodes], moduleIdx) => (
        <motion.div
          key={moduleName}
          initial={{ opacity: 0, y: 10 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: moduleIdx * 0.05 }}
        >
          <Card>
            <CardHeader className="pb-3">
              <CardTitle className="text-base">{moduleName}</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-3">
                {nodes.map((node) => (
                  <div
                    key={node.topic_id}
                    className={cn(
                      'p-4 rounded-xl border transition-all hover:shadow-sm cursor-pointer',
                      getMasteryColor(node.mastery)
                    )}
                    onClick={() => router.push(`/practice/grammar/topics/${node.topic_id}`)}
                  >
                    <div className="flex items-start justify-between mb-2">
                      <h4 className="font-medium text-sm">{node.topic_name}</h4>
                      {node.mastery >= 80 ? (
                        <CheckCircle2 className="h-4 w-4 text-green-600 shrink-0" />
                      ) : node.mastery < 20 ? (
                        <AlertCircle className="h-4 w-4 text-red-500 shrink-0" />
                      ) : (
                        <Clock className="h-4 w-4 text-amber-500 shrink-0" />
                      )}
                    </div>
                    <Progress value={node.mastery} className="h-2 mb-2" />
                    <div className="flex items-center justify-between text-xs">
                      <span>{node.mastery}% mastery</span>
                      <Badge variant="outline" className="text-[10px] px-1.5 py-0">
                        Confidence: {getConfidenceLabel(node.confidence)}
                      </Badge>
                    </div>
                    {node.last_reviewed && (
                      <p className="text-[10px] text-muted-foreground mt-1">
                        Last: {new Date(node.last_reviewed).toLocaleDateString()}
                      </p>
                    )}
                  </div>
                ))}
              </div>
            </CardContent>
          </Card>
        </motion.div>
      ))}
    </div>
  )
}