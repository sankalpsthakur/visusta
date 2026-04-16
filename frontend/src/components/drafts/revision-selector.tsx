'use client'

import { motion } from 'framer-motion'
import { History, Clock } from 'lucide-react'
import type { DraftRevision } from '@/lib/api/draft-hooks'

interface RevisionSelectorProps {
  revisions: DraftRevision[]
  currentRevision: number
  onSelect: (revision: DraftRevision) => void
}

function formatDate(ts: string): string {
  try {
    return new Date(ts).toLocaleString(undefined, { month: 'short', day: 'numeric', hour: '2-digit', minute: '2-digit' })
  } catch {
    return ts
  }
}

export function RevisionSelector({ revisions, currentRevision, onSelect }: RevisionSelectorProps) {
  const sorted = [...revisions].sort((a, b) => b.revision_number - a.revision_number)

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: 4 }}>
      <div style={{ display: 'flex', alignItems: 'center', gap: 6, padding: '0 4px', marginBottom: 6 }}>
        <History size={13} color="var(--text-muted)" />
        <span style={{ fontSize: 11, fontWeight: 500, color: 'var(--text-secondary)', textTransform: 'uppercase', letterSpacing: '0.05em' }}>
          Revisions
        </span>
      </div>

      {sorted.map((revision) => {
        const isCurrent = revision.revision_number === currentRevision
        return (
          <motion.div
            key={revision.revision_id}
            whileHover={{ x: 2 }}
            onClick={() => onSelect(revision)}
            style={{
              display: 'flex',
              flexDirection: 'column',
              gap: 3,
              padding: '8px 10px',
              borderRadius: 8,
              cursor: 'pointer',
              background: isCurrent ? 'rgba(var(--brand-accent-rgb),0.08)' : 'var(--bg-surface-raised)',
              border: isCurrent ? '1px solid rgba(var(--brand-accent-rgb),0.3)' : '1px solid var(--border-subtle)',
            }}
          >
            <div style={{ display: 'flex', alignItems: 'center', gap: 6 }}>
              <span style={{ fontSize: 12, fontWeight: isCurrent ? 600 : 400, color: isCurrent ? 'var(--brand-accent)' : 'var(--text-primary)' }}>
                Rev {revision.revision_number}
              </span>
              {isCurrent && (
                <span style={{ fontSize: 10, color: 'var(--brand-accent)', background: 'rgba(var(--brand-accent-rgb),0.12)', padding: '1px 6px', borderRadius: 999 }}>
                  Current
                </span>
              )}
            </div>
            {revision.summary && (
              <div style={{ fontSize: 11, color: 'var(--text-secondary)', overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>
                {revision.summary}
              </div>
            )}
            <div style={{ fontSize: 10, color: 'var(--text-muted)', display: 'flex', alignItems: 'center', gap: 3 }}>
              <Clock size={9} />
              {formatDate(revision.created_at)}
            </div>
          </motion.div>
        )
      })}
    </div>
  )
}
