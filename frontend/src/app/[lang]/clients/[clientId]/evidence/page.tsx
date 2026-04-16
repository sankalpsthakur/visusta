'use client'

import { use, useState } from 'react'
import { PageTransition } from '@/components/shared/page-transition'
import { ErrorBoundary } from '@/components/shared/error-boundary'
import { EvidenceUpload } from '@/components/evidence/evidence-upload'
import { EvidenceTable } from '@/components/evidence/evidence-table'
import { useEvidence } from '@/lib/api/hooks'

interface EvidencePageProps {
  params: Promise<{ clientId: string }>
}

export default function EvidencePage({ params }: EvidencePageProps) {
  const { clientId } = use(params)
  const { data, isLoading } = useEvidence(clientId)
  const [search, setSearch] = useState('')
  const [sourceFilter, setSourceFilter] = useState('')

  const records = data?.evidence ?? []
  const sources = Array.from(new Set(records.map((r) => r.source_name).filter(Boolean)))

  const filtered = records.filter((r) => {
    const matchSearch =
      !search ||
      r.document_title?.toLowerCase().includes(search.toLowerCase()) ||
      r.snippet?.toLowerCase().includes(search.toLowerCase())
    const matchSource = !sourceFilter || r.source_name === sourceFilter
    return matchSearch && matchSource
  })

  return (
    <PageTransition className="p-8">
      <div className="max-w-5xl">
        <div className="mb-6">
          <h2
            className="text-2xl font-semibold mb-1"
            style={{ color: 'var(--text-primary)', fontFamily: 'var(--font-display)' }}
          >
            Evidence Layer
          </h2>
          <p className="text-sm" style={{ color: 'var(--text-muted)' }}>
            Source records backing every report claim
          </p>
        </div>

        <ErrorBoundary>
          <EvidenceUpload clientId={clientId} />
        </ErrorBoundary>

        <div className="flex gap-3 mb-4">
          <input
            type="text"
            placeholder="Search documents…"
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            className="flex-1 text-sm px-3 py-2 rounded outline-none"
            style={{
              background: 'var(--bg-surface)',
              border: '1px solid var(--border-color)',
              color: 'var(--text-primary)',
            }}
          />
          <select
            value={sourceFilter}
            onChange={(e) => setSourceFilter(e.target.value)}
            className="text-sm px-3 py-2 rounded outline-none"
            style={{
              background: 'var(--bg-surface)',
              border: '1px solid var(--border-color)',
              color: sourceFilter ? 'var(--text-primary)' : 'var(--text-muted)',
            }}
          >
            <option value="">All sources</option>
            {sources.map((s) => (
              <option key={s} value={s}>{s}</option>
            ))}
          </select>
        </div>

        <ErrorBoundary>
          <EvidenceTable records={filtered} clientId={clientId} isLoading={isLoading} />
        </ErrorBoundary>
      </div>
    </PageTransition>
  )
}
