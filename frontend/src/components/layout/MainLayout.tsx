'use client'

import { ReactNode } from 'react'
import { usePathname } from 'next/navigation'
import { motion } from 'framer-motion'
import { Sidebar } from './Sidebar'
import { AIMentorPanel } from './AIMentorPanel'
import { useUIStore } from '@/lib/store'
import { useFeatureSync } from '@/lib/hooks/useFeatureSync'
import { useOnboardingGuard } from '@/lib/hooks/useOnboardingGuard'
import { OnboardingBanner } from '@/components/features/onboarding/OnboardingBanner'
import { useAuthStore } from '@/lib/store/useAuthStore'
import { useEffect } from 'react'
import { useRouter } from 'next/navigation'

interface MainLayoutProps {
  children: ReactNode
}

export function MainLayout({ children }: MainLayoutProps) {
  const { sidebarCollapsed, aiPanelCollapsed } = useUIStore()
  const pathname = usePathname()
  const { isChecking, shouldShowBanner } = useOnboardingGuard()
  const { token, user } = useAuthStore()
  const router = useRouter()

  // Protect routes and redirect logged-in users away from auth pages
  useEffect(() => {
    const isAuthPage = pathname === '/login' || pathname === '/signup'
    
    if (!token && !isAuthPage) {
      router.push('/login')
    } else if (token && isAuthPage) {
      router.push('/')
    }
  }, [token, pathname, router])

  // Mount the debounced backend sync once at app root
  useFeatureSync()

  const isAuthPage = pathname === '/login' || pathname === '/signup'

  // Full-screen pages (Auth & Onboarding)
  if (pathname.startsWith('/onboarding') || isAuthPage) {
    return <>{children}</>
  }

  // Show nothing while checking onboarding status (prevents flash)
  if (isChecking || !token) {
    return (
      <div className="min-h-screen bg-background flex items-center justify-center">
        <div className="animate-pulse text-muted-foreground">Loading...</div>
      </div>
    )
  }

  return (
    <div className="min-h-screen bg-background">
      <Sidebar />
      <AIMentorPanel />
      
      <motion.main
        initial={false}
        animate={{ 
          marginLeft: sidebarCollapsed ? 80 : 280,
          marginRight: aiPanelCollapsed ? 0 : 360
        }}
        transition={{ duration: 0.3, ease: 'easeInOut' }}
        className="min-h-screen"
      >
        <div className="p-6 lg:p-8">
          <OnboardingBanner show={shouldShowBanner} />
          {children}
        </div>
      </motion.main>
    </div>
  )
}