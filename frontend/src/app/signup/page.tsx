'use client'

import { useState } from 'react'
import { useRouter } from 'next/navigation'
import Link from 'next/link'
import { motion } from 'framer-motion'
import { Mail, Lock, User as UserIcon, Building2, ArrowRight, Loader2, CheckCircle2 } from 'lucide-react'
import { useAuthStore } from '@/lib/store/useAuthStore'
import { api } from '@/lib/services/api-client'
import { Button } from '@/components/ui/button'
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '@/components/ui/card'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import { Progress } from '@/components/ui/progress'
import { ThemeToggle } from '@/components/ui/theme-toggle'
import { AuthShowcase } from '@/components/features/auth/AuthShowcase'

// Basic password strength calculation
const calculatePasswordStrength = (password: string) => {
  let score = 0
  if (!password) return 0
  if (password.length > 7) score += 25
  if (password.match(/[a-z]+/)) score += 25
  if (password.match(/[A-Z]+/)) score += 25
  if (password.match(/[0-9]+/)) score += 25
  if (password.match(/[$@#&!]+/)) score += 25
  return Math.min(100, score)
}

export default function SignupPage() {
  const router = useRouter()
  const { setAuth } = useAuthStore()
  
  const [name, setName] = useState(process.env.NODE_ENV === 'development' ? 'Test User' : '')
  const [universityName, setUniversityName] = useState(process.env.NODE_ENV === 'development' ? 'Test University' : '')
  const [email, setEmail] = useState(process.env.NODE_ENV === 'development' ? 'test@example.com' : '')
  const [verifyEmail, setVerifyEmail] = useState(process.env.NODE_ENV === 'development' ? 'test@example.com' : '')
  const [password, setPassword] = useState(process.env.NODE_ENV === 'development' ? 'TestPassword123!' : '')
  const [confirmPassword, setConfirmPassword] = useState(process.env.NODE_ENV === 'development' ? 'TestPassword123!' : '')
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState('')

  const passwordStrength = calculatePasswordStrength(password)
  const isMediumStrength = passwordStrength >= 50
  
  const getStrengthColor = (score: number) => {
    if (score === 0) return 'bg-muted'
    if (score < 50) return 'bg-destructive'
    if (score < 75) return 'bg-yellow-500'
    return 'bg-success'
  }

  const handleSignup = async (e: React.FormEvent) => {
    e.preventDefault()
    setError('')
    
    if (email !== verifyEmail) {
      setError('Email addresses do not match.')
      return
    }
    
    if (password !== confirmPassword) {
      setError('Passwords do not match.')
      return
    }
    
    if (!isMediumStrength) {
      setError('Password must be at least medium strength (8+ chars, mix of letters and numbers).')
      return
    }

    setLoading(true)
    try {
      const data = await api.post<{ access_token: string, user: any }>('/api/auth/signup', {
        name,
        university_name: universityName,
        email,
        password
      }, { skipAuth: true })
      
      setAuth(data.user, data.access_token)
      router.push('/')
    } catch (err: any) {
      setError(err.message || 'Failed to create account')
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="min-h-screen grid lg:grid-cols-2 relative bg-background">
      <div className="absolute top-4 right-4 z-50">
        <ThemeToggle />
      </div>
      
      {/* Left side: Marketing Showcase */}
      <AuthShowcase />

      {/* Right side: Signup Form */}
      <div className="flex items-center justify-center p-8 py-12">
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.5 }}
          className="w-full max-w-lg"
        >
          <div className="space-y-6">
            <div className="space-y-2 text-center lg:text-left">
              <h1 className="text-3xl font-bold tracking-tight">Create an account</h1>
              <p className="text-muted-foreground">
                Join the AI IELTS Tutor community and boost your band score
              </p>
            </div>
            
            <form onSubmit={handleSignup} className="space-y-4">
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                <div className="space-y-2">
                  <Label htmlFor="name">Full Name</Label>
                  <div className="relative">
                    <UserIcon className="absolute left-3 top-3 h-4 w-4 text-muted-foreground" />
                    <Input
                      id="name"
                      placeholder="John Doe"
                      className="pl-9"
                      value={name}
                      onChange={(e) => setName(e.target.value)}
                      required
                    />
                  </div>
                </div>
                <div className="space-y-2">
                  <Label htmlFor="university">University Name (Optional)</Label>
                  <div className="relative">
                    <Building2 className="absolute left-3 top-3 h-4 w-4 text-muted-foreground" />
                    <Input
                      id="university"
                      placeholder="Oxford University"
                      className="pl-9"
                      value={universityName}
                      onChange={(e) => setUniversityName(e.target.value)}
                    />
                  </div>
                </div>
              </div>

              <div className="space-y-2">
                <Label htmlFor="email">Email</Label>
                <div className="relative">
                  <Mail className="absolute left-3 top-3 h-4 w-4 text-muted-foreground" />
                  <Input
                    id="email"
                    type="email"
                    placeholder="name@example.com"
                    className="pl-9"
                    value={email}
                    onChange={(e) => setEmail(e.target.value)}
                    required
                  />
                </div>
              </div>

              <div className="space-y-2">
                <Label htmlFor="verifyEmail">Verify Email</Label>
                <div className="relative">
                  <Mail className="absolute left-3 top-3 h-4 w-4 text-muted-foreground" />
                  <Input
                    id="verifyEmail"
                    type="email"
                    placeholder="Re-enter your email"
                    className="pl-9"
                    value={verifyEmail}
                    onChange={(e) => setVerifyEmail(e.target.value)}
                    required
                  />
                  {email && verifyEmail && email === verifyEmail && (
                    <CheckCircle2 className="absolute right-3 top-3 h-4 w-4 text-success" />
                  )}
                </div>
              </div>

              <div className="space-y-2">
                <Label htmlFor="password">Password</Label>
                <div className="relative">
                  <Lock className="absolute left-3 top-3 h-4 w-4 text-muted-foreground" />
                  <Input
                    id="password"
                    type="password"
                    placeholder="Create a strong password"
                    className="pl-9"
                    value={password}
                    onChange={(e) => setPassword(e.target.value)}
                    required
                  />
                </div>
                {/* Password Strength Meter */}
                {password && (
                  <div className="space-y-1 mt-2">
                    <div className="flex justify-between text-xs">
                      <span className="text-muted-foreground">Password strength</span>
                      <span className={passwordStrength < 50 ? 'text-destructive' : passwordStrength < 75 ? 'text-yellow-500' : 'text-success'}>
                        {passwordStrength < 50 ? 'Weak' : passwordStrength < 75 ? 'Medium' : 'Strong'}
                      </span>
                    </div>
                    <Progress 
                      value={passwordStrength} 
                      className="h-1.5" 
                      indicatorClassName={getStrengthColor(passwordStrength)} 
                    />
                  </div>
                )}
              </div>

              <div className="space-y-2">
                <Label htmlFor="confirmPassword">Re-enter Password</Label>
                <div className="relative">
                  <Lock className="absolute left-3 top-3 h-4 w-4 text-muted-foreground" />
                  <Input
                    id="confirmPassword"
                    type="password"
                    placeholder="Confirm your password"
                    className="pl-9"
                    value={confirmPassword}
                    onChange={(e) => setConfirmPassword(e.target.value)}
                    required
                  />
                  {password && confirmPassword && password === confirmPassword && (
                    <CheckCircle2 className="absolute right-3 top-3 h-4 w-4 text-success" />
                  )}
                </div>
              </div>

              {error && (
                <div className="text-sm text-destructive text-center font-medium bg-destructive/10 p-2 rounded-md">
                  {error}
                </div>
              )}

              <Button type="submit" className="w-full mt-4" disabled={loading || !isMediumStrength || email !== verifyEmail || password !== confirmPassword}>
                {loading ? <Loader2 className="mr-2 h-4 w-4 animate-spin" /> : 'Create Account'}
                {!loading && <ArrowRight className="ml-2 h-4 w-4" />}
              </Button>
            </form>

            <div className="mt-6">
              <div className="relative">
                <div className="absolute inset-0 flex items-center">
                  <span className="w-full border-t border-border" />
                </div>
                <div className="relative flex justify-center text-xs uppercase">
                  <span className="bg-card px-2 text-muted-foreground">
                    Or continue with
                  </span>
                </div>
              </div>

              <div className="mt-6">
                <Button variant="outline" className="w-full" onClick={() => alert('Google auth requires Client ID setup!')}>
                  <svg className="mr-2 h-4 w-4" viewBox="0 0 24 24">
                    <path
                      d="M22.56 12.25c0-.78-.07-1.53-.2-2.25H12v4.26h5.92c-.26 1.37-1.04 2.53-2.21 3.31v2.77h3.57c2.08-1.92 3.28-4.74 3.28-8.09z"
                      fill="#4285F4"
                    />
                    <path
                      d="M12 23c2.97 0 5.46-.98 7.28-2.66l-3.57-2.77c-.98.66-2.23 1.06-3.71 1.06-2.86 0-5.29-1.93-6.16-4.53H2.18v2.84C3.99 20.53 7.7 23 12 23z"
                      fill="#34A853"
                    />
                    <path
                      d="M5.84 14.09c-.22-.66-.35-1.36-.35-2.09s.13-1.43.35-2.09V7.07H2.18C1.43 8.55 1 10.22 1 12s.43 3.45 1.18 4.93l2.85-2.22.81-.62z"
                      fill="#FBBC05"
                    />
                    <path
                      d="M12 5.38c1.62 0 3.06.56 4.21 1.64l3.15-3.15C17.45 2.09 14.97 1 12 1 7.7 1 3.99 3.47 2.18 7.07l3.66 2.84c.87-2.6 3.3-4.53 6.16-4.53z"
                      fill="#EA4335"
                    />
                  </svg>
                  Google
                </Button>
              </div>
            </div>

            <p className="mt-8 text-center text-sm text-muted-foreground">
              Already have an account?{' '}
              <Link href="/login" className="font-semibold text-primary hover:underline">
                Sign in
              </Link>
            </p>
          </div>
        </motion.div>
      </div>
    </div>
  )
}

