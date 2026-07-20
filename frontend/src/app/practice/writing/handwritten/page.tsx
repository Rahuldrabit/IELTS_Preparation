'use client'

import { useState, useRef } from 'react'
import { motion, AnimatePresence } from 'framer-motion'
import {
  Upload,
  Camera,
  FileText,
  Loader2,
  Check,
  AlertTriangle,
  RotateCcw,
  Send,
  ChevronRight,
} from 'lucide-react'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Badge } from '@/components/ui/badge'
import { Progress } from '@/components/ui/progress'
import { cn } from '@/lib/utils'
import { writingApi } from '@/lib/services/writing'

type Phase = 'upload' | 'extracting' | 'preview' | 'scoring' | 'result'

interface ExtractedText {
  text: string
  word_count: number
  confidence: number
  warnings: string[]
}

interface ScoreResult {
  extracted_text: string
  word_count: number
  extraction_confidence: number
  task_response: number
  coherence: number
  lexical: number
  grammar: number
  overall: number
  feedback: Record<string, string>
  corrections: Array<{
    incorrect: string
    correct: string
    explanation: string
    type: string
  }>
  warnings: string[]
}

export default function HandwrittenUploadPage() {
  const [phase, setPhase] = useState<Phase>('upload')
  const [file, setFile] = useState<File | null>(null)
  const [previewUrl, setPreviewUrl] = useState<string | null>(null)
  const [extractedText, setExtractedText] = useState<ExtractedText | null>(null)
  const [editedText, setEditedText] = useState('')
  const [scoreResult, setScoreResult] = useState<ScoreResult | null>(null)
  const [error, setError] = useState<string | null>(null)
  
  const fileInputRef = useRef<HTMLInputElement>(null)
  
  const handleFileSelect = (e: React.ChangeEvent<HTMLInputElement>) => {
    const selectedFile = e.target.files?.[0]
    if (!selectedFile) return
    
    // Validate file type
    const allowedTypes = ['image/jpeg', 'image/png', 'image/webp']
    if (!allowedTypes.includes(selectedFile.type)) {
      setError('Please upload a JPEG, PNG, or WebP image')
      return
    }
    
    setFile(selectedFile)
    setPreviewUrl(URL.createObjectURL(selectedFile))
    setError(null)
  }
  
  const handleExtract = async () => {
    if (!file) return
    
    setPhase('extracting')
    setError(null)
    
    try {
      const result = await writingApi.extractHandwritten(file)
      
      setExtractedText(result)
      setEditedText(result.text)
      setPhase('preview')
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Extraction failed')
      setPhase('upload')
    }
  }
  
  const handleScore = async () => {
    if (!file) return
    
    setPhase('scoring')
    setError(null)
    
    try {
      const result = await writingApi.submitHandwritten(1, file, editedText)
      setScoreResult(result)
      setPhase('result')
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Scoring failed')
      setPhase('preview')
    }
  }
  
  const handleReset = () => {
    setPhase('upload')
    setFile(null)
    setPreviewUrl(null)
    setExtractedText(null)
    setEditedText('')
    setScoreResult(null)
    setError(null)
  }
  
  return (
    <div className="container max-w-4xl mx-auto py-8 px-4">
      {/* Header */}
      <motion.div
        initial={{ opacity: 0, y: -20 }}
        animate={{ opacity: 1, y: 0 }}
        className="mb-8"
      >
        <div className="flex items-center gap-3 mb-2">
          <Camera className="h-8 w-8 text-orange-500" />
          <h1 className="text-3xl font-bold">Handwritten Essay Upload</h1>
        </div>
        <p className="text-muted-foreground">
          Take a photo of your handwritten essay and get AI-powered feedback instantly.
        </p>
      </motion.div>
      
      <AnimatePresence mode="wait">
        {/* Upload Phase */}
        {phase === 'upload' && (
          <motion.div
            key="upload"
            initial={{ opacity: 0, scale: 0.95 }}
            animate={{ opacity: 1, scale: 1 }}
            exit={{ opacity: 0, scale: 0.95 }}
          >
            <Card>
              <CardContent className="py-12">
                <div
                  onClick={() => fileInputRef.current?.click()}
                  className={cn(
                    'border-2 border-dashed rounded-lg p-12 text-center cursor-pointer transition-colors',
                    file ? 'border-green-500 bg-green-500/5' : 'border-muted-foreground/30 hover:border-primary'
                  )}
                >
                  <input
                    ref={fileInputRef}
                    type="file"
                    accept="image/jpeg,image/png,image/webp"
                    onChange={handleFileSelect}
                    className="hidden"
                  />
                  
                  {file ? (
                    <>
                      <Check className="h-16 w-16 mx-auto text-green-500 mb-4" />
                      <p className="text-lg font-medium mb-2">{file.name}</p>
                      <p className="text-sm text-muted-foreground">
                        Click to change or continue to extract text
                      </p>
                    </>
                  ) : (
                    <>
                      <Upload className="h-16 w-16 mx-auto text-muted-foreground mb-4" />
                      <p className="text-lg font-medium mb-2">
                        Drop your essay photo here
                      </p>
                      <p className="text-sm text-muted-foreground">
                        or click to browse (JPEG, PNG, WebP)
                      </p>
                    </>
                  )}
                </div>
                
                {error && (
                  <div className="mt-4 p-4 rounded-lg bg-red-500/10 border border-red-200">
                    <p className="text-sm text-red-700">{error}</p>
                  </div>
                )}
                
                {file && (
                  <div className="mt-6 flex justify-center gap-4">
                    <Button variant="outline" onClick={handleReset}>
                      <RotateCcw className="h-4 w-4 mr-2" />
                      Clear
                    </Button>
                    <Button size="lg" onClick={handleExtract}>
                      Extract Text
                      <ChevronRight className="h-4 w-4 ml-2" />
                    </Button>
                  </div>
                )}
              </CardContent>
            </Card>
          </motion.div>
        )}
        
        {/* Extracting Phase */}
        {phase === 'extracting' && (
          <motion.div
            key="extracting"
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            exit={{ opacity: 0, y: -20 }}
          >
            <Card>
              <CardContent className="py-12 text-center">
                <Loader2 className="h-16 w-16 mx-auto text-primary animate-spin mb-4" />
                <h2 className="text-2xl font-bold mb-2">Extracting Text...</h2>
                <p className="text-muted-foreground">
                  Reading your handwritten essay using AI vision
                </p>
              </CardContent>
            </Card>
          </motion.div>
        )}
        
        {/* Preview Phase */}
        {phase === 'preview' && extractedText && (
          <motion.div
            key="preview"
            initial={{ opacity: 0, x: 50 }}
            animate={{ opacity: 1, x: 0 }}
            exit={{ opacity: 0, x: -50 }}
            className="space-y-6"
          >
            {/* Confidence Warning */}
            {extractedText.confidence < 0.8 && (
              <div className="p-4 rounded-lg bg-yellow-500/10 border border-yellow-200">
                <div className="flex items-start gap-2">
                  <AlertTriangle className="h-5 w-5 text-yellow-600 mt-0.5" />
                  <div>
                    <p className="font-medium text-yellow-700">Low Extraction Confidence</p>
                    <p className="text-sm text-yellow-600">
                      Please verify the extracted text is correct before submitting for scoring.
                    </p>
                  </div>
                </div>
              </div>
            )}
            
            {/* Image Preview + Extracted Text */}
            <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
              {/* Image */}
              {previewUrl && (
                <Card>
                  <CardHeader>
                    <CardTitle className="text-base">Original Image</CardTitle>
                  </CardHeader>
                  <CardContent>
                    <img
                      src={previewUrl}
                      alt="Uploaded essay"
                      className="w-full rounded-lg"
                    />
                  </CardContent>
                </Card>
              )}
              
              {/* Extracted Text */}
              <Card>
                <CardHeader>
                  <div className="flex items-center justify-between">
                    <CardTitle className="text-base">Extracted Text</CardTitle>
                    <Badge variant="outline">
                      {extractedText.word_count} words
                    </Badge>
                  </div>
                </CardHeader>
                <CardContent>
                  <textarea
                    value={editedText}
                    onChange={(e) => setEditedText(e.target.value)}
                    className="w-full min-h-[300px] p-4 rounded-lg border bg-background resize-none focus:outline-none focus:ring-2 focus:ring-primary"
                    placeholder="Edit extracted text if needed..."
                  />
                  
                  {/* Warnings */}
                  {extractedText.warnings.length > 0 && (
                    <div className="mt-4 space-y-1">
                      {extractedText.warnings.map((warning, i) => (
                        <p key={i} className="text-xs text-muted-foreground">
                          ⚠️ {warning}
                        </p>
                      ))}
                    </div>
                  )}
                </CardContent>
              </Card>
            </div>
            
            {/* Actions */}
            <div className="flex justify-between">
              <Button variant="ghost" onClick={handleReset}>
                <RotateCcw className="h-4 w-4 mr-2" />
                Start Over
              </Button>
              <Button size="lg" onClick={handleScore}>
                Get Feedback
                <Send className="h-4 w-4 ml-2" />
              </Button>
            </div>
          </motion.div>
        )}
        
        {/* Scoring Phase */}
        {phase === 'scoring' && (
          <motion.div
            key="scoring"
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            exit={{ opacity: 0, y: -20 }}
          >
            <Card>
              <CardContent className="py-12 text-center">
                <Loader2 className="h-16 w-16 mx-auto text-primary animate-spin mb-4" />
                <h2 className="text-2xl font-bold mb-2">Scoring Essay...</h2>
                <p className="text-muted-foreground">
                  Analyzing your writing against IELTS criteria
                </p>
              </CardContent>
            </Card>
          </motion.div>
        )}
        
        {/* Result Phase */}
        {phase === 'result' && scoreResult && (
          <motion.div
            key="result"
            initial={{ opacity: 0, scale: 0.95 }}
            animate={{ opacity: 1, scale: 1 }}
            exit={{ opacity: 0, scale: 0.95 }}
            className="space-y-6"
          >
            {/* Band Score Header */}
            <Card className="bg-gradient-to-r from-primary to-secondary text-white">
              <CardContent className="py-8 text-center">
                <p className="text-white/80 mb-2">Overall Band Score</p>
                <p className="text-6xl font-bold">{scoreResult.overall.toFixed(1)}</p>
              </CardContent>
            </Card>
            
            {/* Criteria Scores */}
            <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
              {[
                { label: 'Task Response', value: scoreResult.task_response },
                { label: 'Coherence', value: scoreResult.coherence },
                { label: 'Lexical', value: scoreResult.lexical },
                { label: 'Grammar', value: scoreResult.grammar },
              ].map((criterion) => (
                <Card key={criterion.label}>
                  <CardContent className="py-4 text-center">
                    <p className="text-sm text-muted-foreground mb-1">{criterion.label}</p>
                    <p className="text-2xl font-bold">{criterion.value.toFixed(1)}</p>
                  </CardContent>
                </Card>
              ))}
            </div>
            
            {/* Corrections */}
            {scoreResult.corrections.length > 0 && (
              <Card>
                <CardHeader>
                  <CardTitle className="text-base">Corrections</CardTitle>
                </CardHeader>
                <CardContent>
                  <div className="space-y-2">
                    {scoreResult.corrections.map((correction, i) => (
                      <div key={i} className="p-3 rounded-lg bg-muted">
                        <p className="text-sm">
                          <span className="line-through text-red-600">{correction.incorrect}</span>
                          {' → '}
                          <span className="text-green-600 font-medium">{correction.correct}</span>
                        </p>
                        <p className="text-xs text-muted-foreground mt-1">{correction.explanation}</p>
                      </div>
                    ))}
                  </div>
                </CardContent>
              </Card>
            )}
            
            {/* Actions */}
            <div className="flex justify-center">
              <Button size="lg" onClick={handleReset}>
                <RotateCcw className="h-4 w-4 mr-2" />
                Upload Another Essay
              </Button>
            </div>
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  )
}
