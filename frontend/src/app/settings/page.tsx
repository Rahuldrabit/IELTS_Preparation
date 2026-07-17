'use client'

import { useState, useEffect } from 'react'
import { motion } from 'framer-motion'
import { Settings, User, Bell, Shield, Trash2, Save, Check, Loader2 } from 'lucide-react'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Badge } from '@/components/ui/badge'
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs'
import { profileApi } from '@/lib/services/profile'
import { fadeInUp } from '@/lib/animations'

export default function SettingsPage() {
  const [saved, setSaved] = useState(false)
  const [saving, setSaving] = useState(false)
  const [loading, setLoading] = useState(true)
  const [profile, setProfile] = useState({
    name: '',
    email: '',
    currentBand: 5.5,
    targetBand: 7.0,
    examDate: '',
    dailyGoal: 5,
  })

  useEffect(() => {
    profileApi.getProfile().then((data) => {
      setProfile({
        name: data.name || '',
        email: data.email || '',
        currentBand: data.current_band,
        targetBand: data.target_band,
        examDate: data.exam_date || '',
        dailyGoal: data.daily_goal,
      })
    }).catch(() => {}).finally(() => setLoading(false))
  }, [])

  const handleSave = async () => {
    setSaving(true)
    try {
      await profileApi.updateProfile({
        name: profile.name,
        target_band: profile.targetBand,
        exam_date: profile.examDate || undefined,
        daily_goal: profile.dailyGoal,
      })
      setSaved(true)
      setTimeout(() => setSaved(false), 2000)
    } catch {
      // silently fail
    } finally {
      setSaving(false)
    }
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <motion.div
        initial={{ opacity: 0, y: -20 }}
        animate={{ opacity: 1, y: 0 }}
      >
        <h1 className="text-3xl font-bold mb-2">Settings</h1>
        <p className="text-muted-foreground">
          Manage your profile, preferences, and account settings
        </p>
      </motion.div>

      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ delay: 0.1 }}
      >
        <Tabs defaultValue="profile" className="space-y-6">
          <TabsList className="grid w-full max-w-md grid-cols-4">
            <TabsTrigger value="profile" className="gap-2">
              <User className="h-4 w-4" />
              Profile
            </TabsTrigger>
            <TabsTrigger value="preferences" className="gap-2">
              <Settings className="h-4 w-4" />
              Preferences
            </TabsTrigger>
            <TabsTrigger value="notifications" className="gap-2">
              <Bell className="h-4 w-4" />
              Notifications
            </TabsTrigger>
            <TabsTrigger value="account" className="gap-2">
              <Shield className="h-4 w-4" />
              Account
            </TabsTrigger>
          </TabsList>

          {/* Profile Tab */}
          <TabsContent value="profile">
            <Card>
              <CardHeader>
                <CardTitle>Profile Information</CardTitle>
              </CardHeader>
              <CardContent className="space-y-6">
                {/* Avatar */}
                <div className="flex items-center gap-6">
                  <div className="h-20 w-20 rounded-full bg-gradient-to-br from-primary to-secondary flex items-center justify-center text-white text-2xl font-bold">
                    {profile.name[0]}
                  </div>
                  <div>
                    <Button variant="outline" size="sm">Change Avatar</Button>
                    <p className="text-xs text-muted-foreground mt-2">JPG, PNG. Max 2MB</p>
                  </div>
                </div>

                {/* Form */}
                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                  <div className="space-y-2">
                    <label className="text-sm font-medium">Name</label>
                    <Input
                      value={profile.name}
                      onChange={(e) => setProfile({ ...profile, name: e.target.value })}
                    />
                  </div>
                  <div className="space-y-2">
                    <label className="text-sm font-medium">Email</label>
                    <Input
                      type="email"
                      value={profile.email}
                      onChange={(e) => setProfile({ ...profile, email: e.target.value })}
                    />
                  </div>
                  <div className="space-y-2">
                    <label className="text-sm font-medium">Current Band</label>
                    <Input
                      type="number"
                      step="0.5"
                      min="1"
                      max="9"
                      value={profile.currentBand}
                      onChange={(e) => setProfile({ ...profile, currentBand: parseFloat(e.target.value) })}
                    />
                  </div>
                  <div className="space-y-2">
                    <label className="text-sm font-medium">Target Band</label>
                    <Input
                      type="number"
                      step="0.5"
                      min="1"
                      max="9"
                      value={profile.targetBand}
                      onChange={(e) => setProfile({ ...profile, targetBand: parseFloat(e.target.value) })}
                    />
                  </div>
                  <div className="space-y-2">
                    <label className="text-sm font-medium">Exam Date</label>
                    <Input
                      type="date"
                      value={profile.examDate}
                      onChange={(e) => setProfile({ ...profile, examDate: e.target.value })}
                    />
                  </div>
                  <div className="space-y-2">
                    <label className="text-sm font-medium">Daily Goal (tasks)</label>
                    <Input
                      type="number"
                      min="1"
                      max="10"
                      value={profile.dailyGoal}
                      onChange={(e) => setProfile({ ...profile, dailyGoal: parseInt(e.target.value) })}
                    />
                  </div>
                </div>

                <Button onClick={handleSave} disabled={saving} className="w-full md:w-auto">
                  {saved ? (
                    <>
                      <Check className="h-4 w-4 mr-2" />
                      Saved!
                    </>
                  ) : saving ? (
                    <>
                      <Loader2 className="h-4 w-4 mr-2 animate-spin" />
                      Saving...
                    </>
                  ) : (
                    <>
                      <Save className="h-4 w-4 mr-2" />
                      Save Changes
                    </>
                  )}
                </Button>
              </CardContent>
            </Card>
          </TabsContent>

          {/* Preferences Tab */}
          <TabsContent value="preferences">
            <Card>
              <CardHeader>
                <CardTitle>Learning Preferences</CardTitle>
              </CardHeader>
              <CardContent className="space-y-6">
                <div className="space-y-4">
                  {[
                    { id: 'difficulty', label: 'Difficulty Level', options: ['Easy', 'Medium', 'Hard'], current: 'Medium' },
                    { id: 'accent', label: 'Listening Accent', options: ['British', 'American', 'Australian', 'Mixed'], current: 'British' },
                    { id: 'pacing', label: 'Speaking Pace', options: ['Slow', 'Normal', 'Fast'], current: 'Normal' },
                  ].map((pref) => (
                    <div key={pref.id} className="flex items-center justify-between p-4 rounded-xl bg-muted/50">
                      <div>
                        <p className="font-medium">{pref.label}</p>
                        <p className="text-sm text-muted-foreground">Current: {pref.current}</p>
                      </div>
                      <div className="flex gap-2">
                        {pref.options.map((opt) => (
                          <Button
                            key={opt}
                            variant={pref.current === opt ? 'default' : 'outline'}
                            size="sm"
                          >
                            {opt}
                          </Button>
                        ))}
                      </div>
                    </div>
                  ))}
                </div>
              </CardContent>
            </Card>
          </TabsContent>

          {/* Notifications Tab */}
          <TabsContent value="notifications">
            <Card>
              <CardHeader>
                <CardTitle>Notification Settings</CardTitle>
              </CardHeader>
              <CardContent className="space-y-4">
                {[
                  { id: 'daily', label: 'Daily Reminder', desc: 'Get reminded to practice every day', enabled: true },
                  { id: 'vocab', label: 'Vocabulary Review', desc: 'Remind me when words are due for review', enabled: true },
                  { id: 'progress', label: 'Progress Updates', desc: 'Weekly summary of your progress', enabled: false },
                  { id: 'achievements', label: 'Achievements', desc: 'Celebrate when you hit milestones', enabled: true },
                ].map((notif) => (
                  <div key={notif.id} className="flex items-center justify-between p-4 rounded-xl bg-muted/50">
                    <div>
                      <p className="font-medium">{notif.label}</p>
                      <p className="text-sm text-muted-foreground">{notif.desc}</p>
                    </div>
                    <Button
                      variant={notif.enabled ? 'default' : 'outline'}
                      size="sm"
                    >
                      {notif.enabled ? 'On' : 'Off'}
                    </Button>
                  </div>
                ))}
              </CardContent>
            </Card>
          </TabsContent>

          {/* Account Tab */}
          <TabsContent value="account">
            <Card>
              <CardHeader>
                <CardTitle>Account Management</CardTitle>
              </CardHeader>
              <CardContent className="space-y-6">
                <div className="p-4 rounded-xl bg-muted/50">
                  <h4 className="font-medium mb-2">Change Password</h4>
                  <div className="space-y-3 max-w-md">
                    <Input type="password" placeholder="Current password" />
                    <Input type="password" placeholder="New password" />
                    <Input type="password" placeholder="Confirm new password" />
                    <Button>Update Password</Button>
                  </div>
                </div>

                <div className="p-4 rounded-xl bg-muted/50">
                  <h4 className="font-medium mb-2">Export Data</h4>
                  <p className="text-sm text-muted-foreground mb-3">
                    Download all your progress, vocabulary, and practice history
                  </p>
                  <Button variant="outline">Export All Data</Button>
                </div>

                <div className="p-4 rounded-xl border border-destructive/20 bg-destructive/5">
                  <h4 className="font-medium text-destructive mb-2">Danger Zone</h4>
                  <p className="text-sm text-muted-foreground mb-3">
                    Permanently delete your account and all associated data
                  </p>
                  <Button variant="destructive">
                    <Trash2 className="h-4 w-4 mr-2" />
                    Delete Account
                  </Button>
                </div>
              </CardContent>
            </Card>
          </TabsContent>
        </Tabs>
      </motion.div>
    </div>
  )
}