'use client'

import { motion } from 'framer-motion'
import { Skeleton } from '@/components/ui/skeleton'
import { type EvidenceRecord } from '@/lib/api/hooks'
import { ExternalLink } from 'lucide-react'

function confidenceColor(confidence: number): string {
  if (confidence >= 0.9) return 'var(--severity-low)'
  if (confidence >= 0.7) return 'var(--severity-medium)'
  return 'var(--severity-critical)'
}

function MetaRow({ label, value, mono }: { label: string; value?: string | null; mono?: boolean }) {
  return (
    <div className="flex items-start gap-4 py-2.5" style={{ borderBottom: '1px solid var(--border-color)' }}>
      <span className="text-xs w-36 flex-shrink-0 pt-0.5" style={{ color: 'var(--text-muted)' }}>{label}</span>
      <span
        className="text-sm"
        style={{
          color: 'var(--text-primary)',
          fontFamily: mono ? 'var(--font-mono)' : undefined,
        }}
      >
        {value || '—'}
      </span>
    </div>
  )
}

interface EvidenceDetailProps {
  record: EvidenceRecord | undefined
  isLoading: boolean
  error: Error | null
}

export function EvidenceDetail({ record, isLoading, error }: EvidenceDetailProps) {
  if (isLoading) {
    return (
      <div>
        <Skeleton className="h-8 w-2/3 mb-2" style={{ background: 'var(--bg-elevated)' }} />
        <Skeleton className="h-4 w-1/3 mb-8" style={{ background: 'var(--bg-elevated)' }} />
        <div className="rounded-lg p-5" style={{ background: 'var(--bg-surface)', border: '1px solid var(--border-color)' }}>
          {[0, 1, 2, 3, 4].map((i) => (
            <div key={i} className="flex gap-4 py-2.5" style={{ borderBottom: '1px solid var(--border-color)' }}>
              <Skeleton className="h-3 w-28 mt-0.5" style={{ background: 'var(--bg-elevated)' }} />
              <Skeleton className="h-3 w-48" style={{ background: 'var(--bg-elevated)' }} />
            </div>
          ))}
        </div>
      </div>
    )
  }

  if (error) {
    return (
      <div className="text-sm" style={{ color: 'var(--severity-critical)' }}>
        Failed to load evidence record.
      </div>
    )
  }

  if (!record) return null

  return (
    <motion.div initial={{ opacity: 0, y: 6 }} animate={{ opacity: 1, y: 0 }}>
      <h2
        className="text-2xl font-semibold mb-1"
        style={{ color: 'var(--text-primary)', fontFamily: 'var(--font-display)' }}
      >
        {record.document_title || 'Untitled Document'}
      </h2>
      <div className="text-sm mb-8" style={{ color: 'var(--text-muted)' }}>
        Evidence ID{' '}
        <span style={{ fontFamily: 'var(--font-mono)' }}>{record.evidence_id}</span>
      </div>

      <div
        className="rounded-lg px-5 mb-6"
        style={{ background: 'var(--bg-surface)', border: '1px solid var(--border-color)' }}
      >
        <MetaRow label="Source" value={record.source_name} />
        <MetaRow label="Access date" value={record.access_date ? record.access_date.slice(0, 10) : undefined} mono />
        <MetaRow label="Topic" value={record.topic?.replace(/_/g, ' ')} />
        <MetaRow label="Related regulation" value={record.related_regulation_id} mono />
        <div className="flex items-start gap-4 py-2.5" style={{ borderBottom: '1px solid var(--border-color)' }}>
          <span className="text-xs w-36 flex-shrink-0 pt-0.5" style={{ color: 'var(--text-muted)' }}>Confidence</span>
          <span
            className="text-sm font-medium tabular-nums"
            style={{ color: confidenceColor(record.confidence ?? 0) }}
          >
            {record.confidence != null ? `${(record.confidence * 100).toFixed(0)}%` : '—'}
          </span>
        </div>
        <MetaRow label="Attached by" value={record.attached_by} />
      </div>

      {record.snippet && (
        <div
          className="rounded-lg p-5 mb-6"
          style={{ background: 'var(--bg-surface)', border: '1px solid var(--border-color)' }}
        >
          <div className="text-xs mb-2" style={{ color: 'var(--text-muted)' }}>Snippet</div>
          <p
            className="text-sm leading-relaxed"
            style={{
              color: 'var(--text-primary)',
              fontFamily: 'var(--font-display)',
              fontStyle: 'italic',
            }}
          >
            {record.snippet}
          </p>
        </div>
      )}

      <div
        className="rounded-lg p-5 mb-4"
        style={{ background: 'var(--bg-surface)', border: '1px solid var(--border-color)' }}
      >
        <div className="text-xs mb-2" style={{ color: 'var(--text-muted)' }}>Source URL</div>
        <a
          href={record.url}
          target="_blank"
          rel="noopener noreferrer"
          className="inline-flex items-center gap-1.5 text-sm transition-opacity hover:opacity-70 break-all"
          style={{ color: 'var(--brand-accent)' }}
        >
          {record.url}
          <ExternalLink className="w-3.5 h-3.5 flex-shrink-0" />
        </a>
      </div>

      {record.hash && (
        <div className="text-xs" style={{ color: 'var(--text-muted)', fontFamily: 'var(--font-mono)' }}>
          SHA256: {record.hash}
        </div>
      )}
    </motion.div>
  )
}
