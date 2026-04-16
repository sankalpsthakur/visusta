'use client'

import { motion } from 'framer-motion'
import { FileText, Clock, Globe, ChevronRight } from 'lucide-react'
import { StatusBadge } from '@/components/approval/status-badge'
import type { DraftListItem } from '@/lib/api/draft-hooks'

interface DraftCardProps {
  draft: DraftListItem
  onClick: (draft: DraftListItem) => void
}

function formatDate(ts: string): string {
  try {
    return new Date(ts).toLocaleDateString(undefined, { month: 'short', day: 'numeric', year: 'numeric' })
  } catch {
    return ts
  }
}

export function DraftCard({ draft, onClick }: DraftCardProps) {
  return (
    <motion.div
      whileHover={{ y: -2, boxShadow: '0 8px 24px rgba(0,0,0,0.1)' }}
      whileTap={{ scale: 0.98 }}
      onClick={() => onClick(draft)}
      style={{
        padding: '16px 18px',
        borderRadius: 12,
        border: '1px solid var(--border-subtle)',
        background: 'var(--bg-surface)',
        cursor: 'pointer',
        display: 'flex',
        flexDirection: 'column',
        gap: 10,
      }}
    >
      <div style={{ display: 'flex', alignItems: 'flex-start', gap: 10 }}>
        <div
          style={{
            width: 36,
            height: 36,
            borderRadius: 9,
            background: 'var(--bg-surface-raised)',
            border: '1px solid var(--border-subtle)',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            flexShrink: 0,
          }}
        >
          <FileText size={16} color="var(--text-secondary)" />
        </div>

        <div style={{ flex: 1, minWidth: 0 }}>
          <div
            style={{
              fontSize: 14,
              fontWeight: 600,
              color: 'var(--text-primary)',
              overflow: 'hidden',
              textOverflow: 'ellipsis',
              whiteSpace: 'nowrap',
              marginBottom: 2,
            }}
          >
            {draft.title}
          </div>
          <div style={{ fontSize: 12, color: 'var(--text-muted)' }}>{draft.period}</div>
        </div>

        <StatusBadge status={draft.status} size="sm" />
      </div>

      <div
        style={{
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'space-between',
          paddingTop: 8,
          borderTop: '1px solid var(--border-subtle)',
        }}
      >
        <div style={{ display: 'flex', gap: 12 }}>
          <span style={{ fontSize: 11, color: 'var(--text-muted)', display: 'flex', alignItems: 'center', gap: 4 }}>
            <Globe size={10} />
            {draft.locale.toUpperCase()}
          </span>
          <span style={{ fontSize: 11, color: 'var(--text-muted)', display: 'flex', alignItems: 'center', gap: 4 }}>
            <Clock size={10} />
            {formatDate(draft.updated_at)}
          </span>
          <span style={{ fontSize: 11, color: 'var(--text-muted)' }}>
            {draft.revision_count} rev{draft.revision_count !== 1 ? 's' : ''}
          </span>
        </div>
        <ChevronRight size={13} color="var(--text-muted)" />
      </div>
    </motion.div>
  )
}
