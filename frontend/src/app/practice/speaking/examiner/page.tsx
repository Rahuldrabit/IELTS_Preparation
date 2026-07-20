'use client'

import { useState, useRef, useEffect } from 'react'
import { motion, AnimatePresence } from 'framer-motion'
import {
  MessageCircle,
  Send,
  RotateCcw,
  Mic,
  MicOff,
  Loader2,
  Award,
  ChevronRight,
  User,
  Bot,
} from 'lucide-react'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Badge } from '@/components/ui/badge'
import { speakingApi } from '@/lib/services/speaking'
import { cn } from '@/lib/utils'

interface Message {
  id: string
  role: 'examiner' | 'student'
  content: string
  timestamp: Date
}

interface SessionState {
  session_id: string
  part: number
  topic: string
  messages: Message[]
  turn_count: number
  max_turns: number
  estimated_band?: number
  feedback?: string
}

export default function ExaminerChatPage() {
  const [part, setPart] = useState(1)
  const [topic, setTopic] = useState<string | null>(null)
  const [topics, setTopics] = useState<{ part1_topics: string[]; part3_topics: string[] } | null>(null)
  const [session, setSession] = useState<SessionState | null>(null)
  const [messages, setMessages] = useState<Message[]>([])
  const [input, setInput] = useState('')
  const [loading, setLoading] = useState(false)
  const [sessionEnded, setSessionEnded] = useState(false)
  
  const messagesEndRef = useRef<HTMLDivElement>(null)
  const inputRef = useRef<HTMLInputElement>(null)
  
  // Load topics on mount
  useEffect(() => {
    loadTopics()
  }, [])
  
  // Scroll to bottom on new messages
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [messages])
  
  const loadTopics = async () => {
    try {
      const data = await speakingApi.getExaminerTopics()
      setTopics(data)
    } catch (error) {
      console.error('Failed to load topics:', error)
    }
  }
  
  const startSession = async (selectedTopic?: string) => {
    setLoading(true)
    try {
      const data = await speakingApi.createExaminerSession({
        part,
        topic: (selectedTopic || topic) as string,
      })
      setSession(data.session_state)
      setMessages([{
        id: '1',
        role: 'examiner',
        content: data.opening_message,
        timestamp: new Date(),
      }])
      setSessionEnded(false)
      setInput('')
    } catch (error) {
      console.error('Failed to start session:', error)
    } finally {
      setLoading(false)
    }
  }
  
  const sendMessage = async () => {
    if (!input.trim() || !session || loading) return
    
    const studentMessage = input.trim()
    setInput('')
    
    // Add student message to UI immediately
    const studentMsg: Message = {
      id: `student-${Date.now()}`,
      role: 'student',
      content: studentMessage,
      timestamp: new Date(),
    }
    setMessages(prev => [...prev, studentMsg])
    
    setLoading(true)
    try {
      const data = await speakingApi.chatExaminer({
        session_id: session.session_id,
        message: studentMessage,
        session_state: session,
      })
      
      // Update session state
      setSession(data.session_state)
      
      // Add examiner message
      const examinerMsg: Message = {
        id: `examiner-${Date.now()}`,
        role: 'examiner',
        content: data.examiner_message,
        timestamp: new Date(),
      }
      setMessages(prev => [...prev, examinerMsg])
      
      if (data.is_session_end) {
        setSessionEnded(true)
      }
    } catch (error) {
      console.error('Failed to send message:', error)
      // Remove the student message if failed
      setMessages(prev => prev.filter(m => m.id !== studentMsg.id))
    } finally {
      setLoading(false)
      inputRef.current?.focus()
    }
  }
  
  const handleKeyPress = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault()
      sendMessage()
    }
  }
  
  const resetSession = () => {
    setSession(null)
    setMessages([])
    setSessionEnded(false)
    setInput('')
  }
  
  return (
    <div className="container max-w-3xl mx-auto py-8 px-4">
      {/* Header */}
      <motion.div
        initial={{ opacity: 0, y: -20 }}
        animate={{ opacity: 1, y: 0 }}
        className="mb-6"
      >
        <div className="flex items-center gap-3 mb-2">
          <MessageCircle className="h-8 w-8 text-blue-500" />
          <h1 className="text-3xl font-bold">AI Examiner Chat</h1>
        </div>
        <p className="text-muted-foreground">
          Practice IELTS Speaking Part 1 & 3 with our AI examiner. Get natural follow-up questions based on your answers.
        </p>
      </motion.div>
      
      <AnimatePresence mode="wait">
        {/* Session Setup */}
        {!session && (
          <motion.div
            key="setup"
            initial={{ opacity: 0, scale: 0.95 }}
            animate={{ opacity: 1, scale: 1 }}
            exit={{ opacity: 0, scale: 0.95 }}
          >
            <Card>
              <CardHeader>
                <CardTitle>Start a Practice Session</CardTitle>
              </CardHeader>
              <CardContent className="space-y-6">
                {/* Part Selection */}
                <div className="space-y-2">
                  <label className="text-sm font-medium">Speaking Part</label>
                  <div className="flex gap-4">
                    <Button
                      variant={part === 1 ? 'default' : 'outline'}
                      onClick={() => setPart(1)}
                    >
                      Part 1 - Familiar Topics
                    </Button>
                    <Button
                      variant={part === 3 ? 'default' : 'outline'}
                      onClick={() => setPart(3)}
                    >
                      Part 3 - Discussion
                    </Button>
                  </div>
                </div>
                
                {/* Topic Selection */}
                <div className="space-y-2">
                  <label className="text-sm font-medium">Topic (optional)</label>
                  <div className="flex flex-wrap gap-2">
                    {topics && (part === 1 ? topics.part1_topics : topics.part3_topics).slice(0, 8).map((t) => (
                      <Badge
                        key={t}
                        variant={topic === t ? 'default' : 'outline'}
                        className="cursor-pointer"
                        onClick={() => setTopic(t)}
                      >
                        {t}
                      </Badge>
                    ))}
                  </div>
                  {topic && (
                    <Button variant="ghost" size="sm" onClick={() => setTopic(null)}>
                      Clear selection
                    </Button>
                  )}
                </div>
                
                {/* Start Button */}
                <Button
                  size="lg"
                  className="w-full"
                  onClick={() => startSession()}
                  disabled={loading}
                >
                  {loading ? (
                    <>
                      <Loader2 className="h-4 w-4 mr-2 animate-spin" />
                      Starting...
                    </>
                  ) : (
                    <>
                      <MessageCircle className="h-4 w-4 mr-2" />
                      Start Practice Session
                    </>
                  )}
                </Button>
              </CardContent>
            </Card>
          </motion.div>
        )}
        
        {/* Chat Interface */}
        {session && (
          <motion.div
            key="chat"
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            exit={{ opacity: 0, y: -20 }}
            className="space-y-4"
          >
            {/* Session Info */}
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-2">
                <Badge variant="outline">Part {session.part}</Badge>
                <Badge variant="secondary">{session.topic}</Badge>
              </div>
              <div className="text-sm text-muted-foreground">
                Turn {session.turn_count}/{session.max_turns}
              </div>
            </div>
            
            {/* Messages */}
            <Card className="min-h-[400px] flex flex-col">
              <CardContent className="flex-1 overflow-y-auto p-4 space-y-4">
                {messages.map((msg, i) => (
                  <motion.div
                    key={msg.id}
                    initial={{ opacity: 0, y: 10 }}
                    animate={{ opacity: 1, y: 0 }}
                    transition={{ delay: i * 0.05 }}
                    className={cn(
                      'flex gap-3',
                      msg.role === 'student' ? 'justify-end' : 'justify-start'
                    )}
                  >
                    {msg.role === 'examiner' && (
                      <div className="w-8 h-8 rounded-full bg-blue-500 flex items-center justify-center flex-shrink-0">
                        <Bot className="h-4 w-4 text-white" />
                      </div>
                    )}
                    
                    <div
                      className={cn(
                        'max-w-[80%] rounded-lg p-3',
                        msg.role === 'examiner'
                          ? 'bg-muted'
                          : 'bg-primary text-primary-foreground'
                      )}
                    >
                      <p className="text-sm">{msg.content}</p>
                    </div>
                    
                    {msg.role === 'student' && (
                      <div className="w-8 h-8 rounded-full bg-green-500 flex items-center justify-center flex-shrink-0">
                        <User className="h-4 w-4 text-white" />
                      </div>
                    )}
                  </motion.div>
                ))}
                
                {loading && (
                  <motion.div
                    initial={{ opacity: 0 }}
                    animate={{ opacity: 1 }}
                    className="flex gap-3"
                  >
                    <div className="w-8 h-8 rounded-full bg-blue-500 flex items-center justify-center">
                      <Bot className="h-4 w-4 text-white" />
                    </div>
                    <div className="bg-muted rounded-lg p-3">
                      <Loader2 className="h-4 w-4 animate-spin" />
                    </div>
                  </motion.div>
                )}
                
                <div ref={messagesEndRef} />
              </CardContent>
              
              {/* Input */}
              <div className="border-t p-4">
                {sessionEnded ? (
                  <div className="text-center space-y-4">
                    {session.estimated_band && (
                      <div className="flex items-center justify-center gap-2">
                        <Award className="h-6 w-6 text-yellow-500" />
                        <span className="text-2xl font-bold">Band {session.estimated_band}</span>
                      </div>
                    )}
                    {session.feedback && (
                      <p className="text-sm text-muted-foreground">{session.feedback}</p>
                    )}
                    <Button onClick={resetSession}>
                      <RotateCcw className="h-4 w-4 mr-2" />
                      Start New Session
                    </Button>
                  </div>
                ) : (
                  <div className="flex gap-2">
                    <input
                      ref={inputRef}
                      type="text"
                      value={input}
                      onChange={(e) => setInput(e.target.value)}
                      onKeyPress={handleKeyPress}
                      placeholder="Type your answer..."
                      className="flex-1 px-4 py-2 rounded-lg border bg-background focus:outline-none focus:ring-2 focus:ring-primary"
                      disabled={loading}
                      autoFocus
                    />
                    <Button onClick={sendMessage} disabled={!input.trim() || loading}>
                      <Send className="h-4 w-4" />
                    </Button>
                  </div>
                )}
              </div>
            </Card>
            
            {/* Actions */}
            {!sessionEnded && (
              <div className="flex justify-between">
                <Button variant="ghost" size="sm" onClick={resetSession}>
                  <RotateCcw className="h-4 w-4 mr-2" />
                  End Session
                </Button>
                <div className="text-xs text-muted-foreground">
                  Tip: Try to expand your answers with reasons and examples
                </div>
              </div>
            )}
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  )
}
