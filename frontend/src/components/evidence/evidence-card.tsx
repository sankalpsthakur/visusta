'use client'

import Link from 'next/link'
import { type EvidenceRecord } from '@/lib/api/hooks'

function confidenceColor(confidence: number): string {
  if (confidence >= 0.9) return 'var(--severity-low)'
  if (confidence >= 0.7) return 'var(--severity-medium)'
  return 'var(--severity-critical)'
}

interface EvidenceCardProps {
  record: EvidenceRecord
  clientId: string
}

export function EvidenceCard({ record, clientId }: EvidenceCardProps) {
  return (
    <Link
      href={`/clients/${clientId}/evidence/${record.evidence_id}`}
      className="block rounded-lg p-4 transition-opacity hover:opacity-80"
      style={{ background: 'var(--bg-surface)', border: '1px solid var(--border-color)' }}
    >
      <div
        className="text-sm font-medium mb-1 line-clamp-2"
        style={{ color: 'var(--text-primary)', fontFamily: 'var(--font-display)' }}
      >
        {record.document_title || 'Untitled'}
      </div>

      <div className="flex items-center gap-2 mb-2">
        {record.source_name && (
          <span
            className="text-xs px-1.5 py-0.5 rounded font-medium"
            style={{
              background: 'color-mix(in srgb, var(--brand-accent) 12%, transparent)',
              color: 'var(--brand-accent)',
              border: '1px solid color-mix(in srgb, var(--brand-accent) 25%, transparent)',
            }}
          >
            {record.source_name}
          </span>
        )}
        {record.topic && (
          <span
            className="text-xs px-1.5 py-0.5 rounded"
            style={{
              background: 'var(--bg-elevated)',
              color: 'var(--text-muted)',
              fontFamily: 'var(--font-mono)',
            }}
          >
            {record.topic.replace(/_/g, ' ')}
          </span>
        )}
      </div>

      <div className="flex items-center justify-between">
        <span
          className="text-xs tabular-nums"
          style={{ color: 'var(--text-muted)', fontFamily: 'var(--font-mono)' }}
        >
          {record.access_date ? record.access_date.slice(0, 10) : '—'}
        </span>
        <span
          className="inline-block w-2 h-2 rounded-full"
          style={{ background: confidenceColor(record.confidence ?? 0) }}
          title={`Confidence: ${((record.confidence ?? 0) * 100).toFixed(0)}%`}
        />
      </div>

      {record.url && (
        <div
          className="text-xs mt-2 truncate"
          style={{ color: 'var(--text-muted)' }}
        >
          {record.url}
        </div>
      )}
    </Link>
  )
}
