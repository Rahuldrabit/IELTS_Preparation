'use client'

import { useState, useEffect } from 'react'
import { motion } from 'framer-motion'
import { Headphones, AlertTriangle, RefreshCw } from 'lucide-react'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Badge } from '@/components/ui/badge'
import { cn } from '@/lib/utils'
import { listeningApi, MishearingPair } from '@/lib/services/listening'

interface MishearingProfileCardProps {
  className?: string
}

export function MishearingProfileCard({ className }: MishearingProfileCardProps) {
  const [profile, setProfile] = useState<{
    total_attempts: number
    total_phonetic_confusions: number
    top_confusions: MishearingPair[]
  } | null>(null)
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    loadProfile()
  }, [])

  const loadProfile = async () => {
    setLoading(true)
    try {
      const result = await listeningApi.getDictationProfile()
      setProfile(result)
    } catch (error) {
      console.error('Failed to load mishearing profile:', error)
    } finally {
      setLoading(false)
    }
  }

  if (loading) {
    return (
      <Card className={cn('animate-pulse', className)}>
        <CardContent className="p-6">
          <div className="h-24 bg-muted rounded" />
        </CardContent>
      </Card>
    )
  }

  if (!profile || profile.total_attempts === 0) {
    return null
  }

  return (
    <Card className={className}>
      <CardHeader>
        <div className="flex items-center justify-between">
          <CardTitle className="text-base flex items-center gap-2">
            <Headphones className="h-4 w-4" />
            Mishearing Profile
          </CardTitle>
          <Badge variant="outline">
            {profile.total_attempts} attempts
          </Badge>
        </div>
      </CardHeader>
      <CardContent className="space-y-4">
        {profile.top_confusions.length === 0 ? (
          <div className="text-center py-4 text-muted-foreground">
            <p>No phonetic confusions detected yet.</p>
            <p className="text-sm">Keep practicing dictation to build your profile!</p>
          </div>
        ) : (
          <>
            <p className="text-sm text-muted-foreground">
              You frequently confuse these similar-sounding words:
            </p>
            
            <div className="space-y-2">
              {profile.top_confusions.slice(0, 5).map((conf, index) => (
                <motion.div
                  key={`${conf.expected}-${conf.typed}`}
                  initial={{ opacity: 0, x: -20 }}
                  animate={{ opacity: 1, x: 0 }}
                  transition={{ delay: index * 0.1 }}
                  className="flex items-center justify-between p-3 rounded-lg bg-muted/50"
                >
                  <div className="flex items-center gap-3">
                    <span className="font-mono text-sm">{conf.expected}</span>
                    <span className="text-muted-foreground">→</span>
                    <span className="font-mono text-sm text-orange-600">{conf.typed}</span>
                  </div>
                  <Badge variant="secondary" className="text-xs">
                    {conf.count}×
                  </Badge>
                </motion.div>
              ))}
            </div>

            {profile.total_phonetic_confusions > 5 && (
              <div className="flex items-start gap-2 p-3 rounded-lg bg-yellow-500/10 border border-yellow-200">
                <AlertTriangle className="h-4 w-4 text-yellow-600 mt-0.5" />
                <p className="text-sm text-yellow-700">
                  Focus on distinguishing similar sounds. Try listening exercises 
                  that specifically target minimal pairs (words that differ by one sound).
                </p>
              </div>
            )}
          </>
        )}
      </CardContent>
    </Card>
  )
}
