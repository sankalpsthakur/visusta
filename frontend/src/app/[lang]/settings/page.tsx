'use client'

import { PageTransition } from '@/components/shared/page-transition'

export default function SettingsPage() {
  return (
    <PageTransition className="p-8">
      <div className="max-w-5xl">
        <h1 className="text-2xl font-semibold tracking-tight mb-1" style={{ color: 'var(--text-primary)' }}>
          Settings
        </h1>
        <p className="text-sm" style={{ color: 'var(--text-muted)' }}>
          Report language, sources, and preferences are configured per client under Client Settings.
        </p>
      </div>
    </PageTransition>
  )
}
