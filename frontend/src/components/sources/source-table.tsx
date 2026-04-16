'use client'

import { motion } from 'framer-motion'
import { ExternalLink, Edit3, Trash2 } from 'lucide-react'
import type { SourceConfig } from '@/lib/api/hooks'

interface SourceTableProps {
  sources: SourceConfig[]
  onEdit: (source: SourceConfig) => void
  onDelete: (sourceId: string) => void
  isDeleting?: string
}

const FREQUENCY_BADGE = {
  daily: { color: '#22c55e', bg: 'rgba(34,197,94,0.1)' },
  weekly: { color: '#3b82f6', bg: 'rgba(59,130,246,0.1)' },
  monthly: { color: '#f59e0b', bg: 'rgba(245,158,11,0.1)' },
}

export function SourceTable({ sources, onEdit, onDelete, isDeleting }: SourceTableProps) {
  if (sources.length === 0) {
    return (
      <div style={{ padding: '32px 0', textAlign: 'center', color: 'var(--text-muted)', fontSize: 13 }}>
        No sources configured
      </div>
    )
  }

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: 2 }}>
      {/* Header */}
      <div
        style={{
          display: 'grid',
          gridTemplateColumns: '1fr 120px 120px 140px 80px',
          gap: 12,
          padding: '8px 12px',
          borderRadius: 6,
          background: 'var(--bg-surface-raised)',
          fontSize: 11,
          fontWeight: 600,
          color: 'var(--text-muted)',
          textTransform: 'uppercase',
          letterSpacing: '0.05em',
        }}
      >
        <span>Source</span>
        <span>Type</span>
        <span>Frequency</span>
        <span>URL</span>
        <span style={{ textAlign: 'right' }}>Actions</span>
      </div>

      {sources.map((source) => {
        const freqStyle = FREQUENCY_BADGE[source.frequency as keyof typeof FREQUENCY_BADGE] ?? FREQUENCY_BADGE.weekly
        return (
          <motion.div
            key={source.id}
            layout
            style={{
              display: 'grid',
              gridTemplateColumns: '1fr 120px 120px 140px 80px',
              gap: 12,
              padding: '10px 12px',
              borderRadius: 8,
              border: '1px solid var(--border-subtle)',
              background: 'var(--bg-surface)',
              alignItems: 'center',
              opacity: isDeleting === source.id ? 0.5 : 1,
            }}
          >
            <div>
              <div style={{ fontSize: 13, fontWeight: 500, color: 'var(--text-primary)' }}>{source.display_name}</div>
              <div style={{ fontSize: 11, color: 'var(--text-muted)', fontFamily: 'monospace' }}>{source.id}</div>
            </div>

            <span style={{ fontSize: 12, color: 'var(--text-secondary)', textTransform: 'capitalize' }}>
              {source.source_type.replace(/_/g, ' ')}
            </span>

            <span
              style={{
                fontSize: 11,
                fontWeight: 500,
                color: freqStyle.color,
                background: freqStyle.bg,
                padding: '2px 8px',
                borderRadius: 999,
                display: 'inline-block',
              }}
            >
              {source.frequency}
            </span>

            <div style={{ overflow: 'hidden' }}>
              {source.url ? (
                <a
                  href={source.url}
                  target="_blank"
                  rel="noopener noreferrer"
                  style={{
                    fontSize: 11,
                    color: 'var(--brand-accent)',
                    display: 'flex',
                    alignItems: 'center',
                    gap: 4,
                    overflow: 'hidden',
                    textOverflow: 'ellipsis',
                    whiteSpace: 'nowrap',
                    textDecoration: 'none',
                  }}
                >
                  <ExternalLink size={10} />
                  {source.url.replace(/^https?:\/\//, '').slice(0, 30)}
                </a>
              ) : (
                <span style={{ fontSize: 11, color: 'var(--text-muted)' }}>—</span>
              )}
            </div>

            <div style={{ display: 'flex', gap: 6, justifyContent: 'flex-end' }}>
              <motion.button
                whileHover={{ scale: 1.08 }}
                whileTap={{ scale: 0.92 }}
                onClick={() => onEdit(source)}
                style={{
                  width: 28,
                  height: 28,
                  borderRadius: 7,
                  border: '1px solid var(--border-subtle)',
                  background: 'var(--bg-surface-raised)',
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'center',
                  cursor: 'pointer',
                  color: 'var(--text-secondary)',
                }}
              >
                <Edit3 size={12} />
              </motion.button>
              <motion.button
                whileHover={{ scale: 1.08 }}
                whileTap={{ scale: 0.92 }}
                onClick={() => onDelete(source.id)}
                disabled={isDeleting === source.id}
                style={{
                  width: 28,
                  height: 28,
                  borderRadius: 7,
                  border: '1px solid rgba(239,68,68,0.3)',
                  background: 'rgba(239,68,68,0.06)',
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'center',
                  cursor: isDeleting === source.id ? 'not-allowed' : 'pointer',
                  color: '#ef4444',
                }}
              >
                <Trash2 size={12} />
              </motion.button>
            </div>
          </motion.div>
        )
      })}
    </div>
  )
}
