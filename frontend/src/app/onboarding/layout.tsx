/**
 * Onboarding uses a clean layout without Sidebar or AI Panel.
 * This layout replaces the MainLayout for the /onboarding route.
 */
export default function OnboardingLayout({
  children,
}: {
  children: React.ReactNode
}) {
  return <>{children}</>
}
