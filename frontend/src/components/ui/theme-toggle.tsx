'use client'

import { Moon, Sun } from 'lucide-react'
import { useUIStore } from '@/lib/store'
import { Button } from '@/components/ui/button'
import { motion } from 'framer-motion'

export function ThemeToggle() {
  const theme = useUIStore((state) => state.theme)
  const setTheme = useUIStore((state) => state.setTheme)

  const toggleTheme = () => {
    setTheme(theme === 'light' ? 'dark' : 'light')
  }

  return (
    <Button
      variant="ghost"
      size="icon"
      onClick={toggleTheme}
      className="relative"
    >
      <motion.div
        initial={false}
        animate={{ 
          rotate: theme === 'dark' ? 180 : 0,
          scale: theme === 'dark' ? 0 : 1
        }}
        transition={{ duration: 0.3 }}
        className="absolute"
      >
        <Sun className="h-5 w-5" />
      </motion.div>
      <motion.div
        initial={false}
        animate={{ 
          rotate: theme === 'light' ? -180 : 0,
          scale: theme === 'light' ? 0 : 1
        }}
        transition={{ duration: 0.3 }}
        className="absolute"
      >
        <Moon className="h-5 w-5" />
      </motion.div>
      <span className="sr-only">Toggle theme</span>
    </Button>
  )
}