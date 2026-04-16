'use client'

import { PageTransition } from '@/components/shared/page-transition'

export default function AuditPage() {
  return (
    <PageTransition className="p-8">
      <div className="max-w-5xl">
        <h1 className="text-2xl font-semibold tracking-tight mb-1" style={{ color: 'var(--text-primary)' }}>
          Audit
        </h1>
        <p className="text-sm" style={{ color: 'var(--text-muted)' }}>
          Gap analysis findings — coming in Wave 2
        </p>
      </div>
    </PageTransition>
  )
}
