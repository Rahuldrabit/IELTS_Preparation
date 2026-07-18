'use client'

import Link from 'next/link'
import { usePathname } from 'next/navigation'
import { motion, AnimatePresence } from 'framer-motion'
import { 
  LayoutDashboard, 
  Map, 
  GraduationCap, 
  BookOpen, 
  Headphones, 
  Mic, 
  PenTool, 
  BookMarked,
  FileText,
  BarChart3,
  Settings,
  ChevronDown,
  Sparkles,
  FlaskConical,
  Trophy,
} from 'lucide-react'
import { cn } from '@/lib/utils'
import { useUIStore } from '@/lib/store'
import { useState } from 'react'
import { ThemeToggle } from '@/components/ui/theme-toggle'
import { FeatureIndicatorDot } from '@/components/ui/FeatureIndicatorDot'
import { useHasActiveFeatures } from '@/lib/hooks/useFeature'

// Skill key map: href → featureStore skill key
const SKILL_MAP: Record<string, 'reading' | 'listening' | 'speaking' | 'writing'> = {
  '/practice/reading': 'reading',
  '/practice/listening': 'listening',
  '/practice/speaking': 'speaking',
  '/practice/writing': 'writing',
}

const navigation = [
  { name: 'Dashboard', href: '/', icon: LayoutDashboard },
  { name: 'AI Journey', href: '/journey', icon: Map },
  { 
    name: 'Practice Center', 
    icon: GraduationCap,
    children: [
      { name: 'Mock Test', href: '/practice/mock-test', icon: Trophy },
      { name: 'Reading', href: '/practice/reading', icon: BookOpen },
      { name: 'Listening', href: '/practice/listening', icon: Headphones },
      { name: 'Speaking', href: '/practice/speaking', icon: Mic },
      { name: 'Writing', href: '/practice/writing', icon: PenTool },
      { name: 'Vocabulary', href: '/practice/vocabulary', icon: BookMarked },
      { name: 'Grammar', href: '/practice/grammar', icon: FileText },
    ]
  },
  { name: 'AI Exam Import', href: '/import', icon: Sparkles },
  { name: 'AI Insights', href: '/insights', icon: BarChart3 },
  { name: 'Settings', href: '/settings', icon: Settings },
]

function NavChildItem({ child }: { child: { name: string; href: string; icon: React.ElementType } }) {
  const pathname = usePathname()
  const skill = SKILL_MAP[child.href]
  const hasActive = useHasActiveFeatures(skill)

  return (
    <li>
      <Link
        href={child.href}
        className={cn(
          "flex items-center gap-3 rounded-lg px-3 py-2 text-sm transition-colors",
          pathname === child.href
            ? "bg-primary/10 text-primary font-medium"
            : "text-muted-foreground hover:bg-accent hover:text-accent-foreground"
        )}
      >
        <span className="relative">
          <child.icon className="h-4 w-4" />
          {skill && <FeatureIndicatorDot active={hasActive} />}
        </span>
        <span>{child.name}</span>
      </Link>
    </li>
  )
}

export function Sidebar() {
  const pathname = usePathname()
  const { sidebarCollapsed, toggleSidebar } = useUIStore()
  const [expandedMenu, setExpandedMenu] = useState<string | null>('Practice Center')

  return (
    <motion.aside
      initial={false}
      animate={{ width: sidebarCollapsed ? 80 : 280 }}
      transition={{ duration: 0.3, ease: 'easeInOut' }}
      className="fixed left-0 top-0 z-40 h-screen border-r border-border bg-card"
    >
      <div className="flex h-full flex-col">
        {/* Logo */}
        <div className="flex h-16 items-center justify-center border-b border-border px-4">
          <Link href="/" className="flex items-center gap-3">
            <div className="flex h-10 w-10 items-center justify-center rounded-xl bg-primary">
              <Sparkles className="h-6 w-6 text-primary-foreground" />
            </div>
            {!sidebarCollapsed && (
              <motion.span 
                initial={{ opacity: 0 }}
                animate={{ opacity: 1 }}
                className="text-xl font-bold"
              >
                IELTS AI
              </motion.span>
            )}
          </Link>
        </div>

        {/* Navigation */}
        <nav className="flex-1 overflow-y-auto py-4">
          <ul className="space-y-1 px-3">
            {navigation.map((item) => (
              <li key={item.name}>
                {item.children ? (
                  <div>
                    <button
                      onClick={() => setExpandedMenu(expandedMenu === item.name ? null : item.name)}
                      className={cn(
                        "flex w-full items-center justify-between rounded-xl px-3 py-2.5 text-sm font-medium transition-colors",
                        "text-muted-foreground hover:bg-accent hover:text-accent-foreground"
                      )}
                    >
                      <div className="flex items-center gap-3">
                        <item.icon className="h-5 w-5 shrink-0" />
                        {!sidebarCollapsed && <span>{item.name}</span>}
                      </div>
                      {!sidebarCollapsed && (
                        <ChevronDown 
                          className={cn(
                            "h-4 w-4 transition-transform", 
                            expandedMenu === item.name && "rotate-180"
                          )} 
                        />
                      )}
                    </button>
                    <AnimatePresence initial={false}>
                      {!sidebarCollapsed && expandedMenu === item.name && (
                        <motion.ul
                          key={item.name}
                          initial={{ opacity: 0, height: 0 }}
                          animate={{ opacity: 1, height: 'auto' }}
                          exit={{ opacity: 0, height: 0 }}
                          transition={{ duration: 0.2, ease: 'easeInOut' }}
                          className="mt-1 space-y-1 overflow-hidden pl-4"
                        >
                          {item.children.map((child) => (
                            <NavChildItem key={child.name} child={child} />
                          ))}
                        </motion.ul>
                      )}
                    </AnimatePresence>
                  </div>
                ) : (
                  <Link
                    href={item.href}
                    className={cn(
                      "flex items-center gap-3 rounded-xl px-3 py-2.5 text-sm font-medium transition-colors",
                      pathname === item.href
                        ? "bg-primary/10 text-primary"
                        : "text-muted-foreground hover:bg-accent hover:text-accent-foreground"
                    )}
                  >
                    <item.icon className="h-5 w-5 shrink-0" />
                    {!sidebarCollapsed && <span>{item.name}</span>}
                  </Link>
                )}
              </li>
            ))}
          </ul>
        </nav>

        {/* Theme Toggle */}
        <div className="border-t border-border p-3">
          <div className="flex items-center justify-center">
            <ThemeToggle />
          </div>
        </div>

        {/* Feature Lab shortcut */}
        <div className="border-t border-border px-3 py-2">
          <Link
            href="/settings/features"
            className="flex items-center gap-2 rounded-lg px-3 py-2 text-xs text-muted-foreground hover:bg-accent hover:text-accent-foreground transition-colors"
          >
            <FlaskConical className="h-4 w-4 shrink-0" />
            {!sidebarCollapsed && <span>Feature Lab</span>}
          </Link>
        </div>

        {/* Collapse button */}
        <div className="border-t border-border p-3">
          <button
            onClick={toggleSidebar}
            className="flex w-full items-center justify-center rounded-xl px-3 py-2 text-sm text-muted-foreground hover:bg-accent hover:text-accent-foreground transition-colors"
          >
            {sidebarCollapsed ? (
              <ChevronDown className="h-5 w-5 rotate-90" />
            ) : (
              <>
                <ChevronDown className="h-4 w-4 mr-2" />
                <span>Collapse</span>
              </>
            )}
          </button>
        </div>
      </div>
    </motion.aside>
  )
}