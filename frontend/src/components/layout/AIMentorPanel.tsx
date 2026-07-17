'use client'

import { useEffect, useState } from 'react'
import { usePathname } from 'next/navigation'
import { motion, AnimatePresence } from 'framer-motion'
import { Sparkles, ChevronRight, MessageCircle, Lightbulb, Target, TrendingUp, X, Minimize2, Maximize2 } from 'lucide-react'
import { cn } from '@/lib/utils'
import { useUIStore } from '@/lib/store'
import { getAIMentorMessages, aiMentorMessages } from '@/lib/mock-data/ai-mentor'
import { Button } from '@/components/ui/button'
import { Card } from '@/components/ui/card'
import { Badge } from '@/components/ui/badge'
import { typingIndicator, slideInRight } from '@/lib/animations'

export function AIMentorPanel() {
  const pathname = usePathname()
  const { aiPanelCollapsed, toggleAIPanel } = useUIStore()
  const [isTyping, setIsTyping] = useState(true)
  const [messages, setMessages] = useState(getAIMentorMessages('dashboard'))

  // Get page context from pathname
  const getPageContext = () => {
    const path = pathname
    if (path === '/') return 'dashboard'
    if (path.startsWith('/journey')) return 'journey'
    if (path.startsWith('/practice/reading')) return 'reading'
    if (path.startsWith('/practice/listening')) return 'listening'
    if (path.startsWith('/practice/speaking')) return 'speaking'
    if (path.startsWith('/practice/writing')) return 'writing'
    if (path.startsWith('/practice/vocabulary')) return 'vocabulary'
    if (path.startsWith('/practice/grammar')) return 'grammar'
    if (path.startsWith('/import')) return 'import'
    if (path.startsWith('/insights')) return 'insights'
    if (path.startsWith('/settings')) return 'settings'
    return 'dashboard'
  }

  useEffect(() => {
    const context = getPageContext()
    setMessages(getAIMentorMessages(context))
    
    // Simulate AI typing
    setIsTyping(true)
    const timer = setTimeout(() => setIsTyping(false), 2000)
    return () => clearTimeout(timer)
  }, [pathname])

  const getTypeIcon = (type: string) => {
    switch (type) {
      case 'greeting': return <MessageCircle className="h-4 w-4" />
      case 'hint': return <Lightbulb className="h-4 w-4" />
      case 'strategy': return <Target className="h-4 w-4" />
      case 'feedback': return <TrendingUp className="h-4 w-4" />
      case 'recommendation': return <Sparkles className="h-4 w-4" />
      default: return <Sparkles className="h-4 w-4" />
    }
  }

  return (
    <motion.aside
      initial={false}
      animate={{ 
        width: aiPanelCollapsed ? 0 : 360,
        opacity: aiPanelCollapsed ? 0 : 1
      }}
      transition={{ duration: 0.3, ease: 'easeInOut' }}
      className="fixed right-0 top-0 z-40 h-screen overflow-hidden border-l border-border bg-card"
    >
      <div className="flex h-full w-[360px] flex-col">
        {/* Header */}
        <div className="flex h-16 items-center justify-between border-b border-border px-4">
          <div className="flex items-center gap-3">
            <div className="flex h-10 w-10 items-center justify-center rounded-full bg-gradient-to-br from-primary to-secondary">
              <Sparkles className="h-5 w-5 text-white" />
            </div>
            <div>
              <h2 className="font-semibold">AI Mentor</h2>
              <p className="text-xs text-muted-foreground">Always here to help</p>
            </div>
          </div>
          <Button 
            variant="ghost" 
            size="icon" 
            onClick={toggleAIPanel}
            className="shrink-0"
          >
            <Minimize2 className="h-4 w-4" />
          </Button>
        </div>

        {/* Messages */}
        <div className="flex-1 overflow-y-auto p-4">
          <div className="space-y-4">
            <AnimatePresence mode="popLayout">
              {messages.map((message, index) => (
                <motion.div
                  key={message.id}
                  variants={slideInRight}
                  initial="initial"
                  animate="animate"
                  exit="exit"
                  transition={{ delay: index * 0.1 }}
                >
                  <Card className="p-4">
                    <div className="flex items-start gap-3">
                      <div className={cn(
                        "flex h-8 w-8 items-center justify-center rounded-lg shrink-0",
                        message.type === 'greeting' && "bg-primary/10 text-primary",
                        message.type === 'hint' && "bg-warning/10 text-warning",
                        message.type === 'strategy' && "bg-secondary/10 text-secondary",
                        message.type === 'feedback' && "bg-success/10 text-success",
                        message.type === 'recommendation' && "bg-primary/10 text-primary"
                      )}>
                        {getTypeIcon(message.type)}
                      </div>
                      <div className="flex-1 min-w-0">
                        <Badge variant="outline" className="mb-2 text-[10px] capitalize">
                          {message.type}
                        </Badge>
                        <p className="text-sm text-foreground leading-relaxed">
                          {message.content}
                        </p>
                        {message.actions && (
                          <div className="mt-3 flex flex-wrap gap-2">
                            {message.actions.map((action, i) => (
                              <Button 
                                key={i} 
                                variant="outline" 
                                size="sm" 
                                className="text-xs h-7"
                              >
                                {action.label}
                                <ChevronRight className="h-3 w-3 ml-1" />
                              </Button>
                            ))}
                          </div>
                        )}
                      </div>
                    </div>
                  </Card>
                </motion.div>
              ))}

              {/* Typing indicator */}
              {isTyping && (
                <motion.div
                  initial={{ opacity: 0, y: 10 }}
                  animate={{ opacity: 1, y: 0 }}
                  className="flex items-center gap-2 text-sm text-muted-foreground"
                >
                  <div className="flex gap-1">
                    <motion.span
                      variants={typingIndicator}
                      initial="initial"
                      animate="animate"
                      className="h-2 w-2 rounded-full bg-primary"
                    />
                    <motion.span
                      variants={typingIndicator}
                      initial="initial"
                      animate="animate"
                      transition={{ delay: 0.1 }}
                      className="h-2 w-2 rounded-full bg-primary"
                    />
                    <motion.span
                      variants={typingIndicator}
                      initial="initial"
                      animate="animate"
                      transition={{ delay: 0.2 }}
                      className="h-2 w-2 rounded-full bg-primary"
                    />
                  </div>
                  <span>AI is thinking...</span>
                </motion.div>
              )}
            </AnimatePresence>
          </div>
        </div>

        {/* Quick actions */}
        <div className="border-t border-border p-4">
          <div className="space-y-2">
            <Button variant="outline" className="w-full justify-start" size="sm">
              <MessageCircle className="h-4 w-4 mr-2" />
              Ask a question
            </Button>
            <Button variant="outline" className="w-full justify-start" size="sm">
              <Lightbulb className="h-4 w-4 mr-2" />
              Get a hint
            </Button>
          </div>
        </div>
      </div>
    </motion.aside>
  )
}