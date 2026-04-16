'use client'

import { motion } from 'framer-motion'
import { CheckCircle, XCircle, RotateCcw, Clock, User } from 'lucide-react'
import type { DraftRevision } from '@/lib/api/draft-hooks'

interface TimelineEvent {
  id: string
  type: 'approved' | 'rejected' | 'revision' | 'submitted' | 'created'
  label: string
  actor?: string
  timestamp: string
  note?: string
}

interface ApprovalTimelineProps {
  revisions: DraftRevision[]
  createdAt: string
}

function eventIcon(type: TimelineEvent['type']) {
  const props = { size: 14, strokeWidth: 2 }
  switch (type) {
    case 'approved': return <CheckCircle {...props} color="#22c55e" />
    case 'rejected': return <XCircle {...props} color="#ef4444" />
    case 'revision': return <RotateCcw {...props} color="#f97316" />
    case 'submitted': return <Clock {...props} color="#3b82f6" />
    case 'created': return <User {...props} color="var(--text-muted)" />
  }
}

function iconBg(type: TimelineEvent['type']): string {
  switch (type) {
    case 'approved': return 'rgba(34,197,94,0.15)'
    case 'rejected': return 'rgba(239,68,68,0.15)'
    case 'revision': return 'rgba(249,115,22,0.15)'
    case 'submitted': return 'rgba(59,130,246,0.15)'
    case 'created': return 'var(--bg-surface-raised)'
  }
}

function formatTimestamp(ts: string): string {
  try {
    return new Date(ts).toLocaleString(undefined, {
      month: 'short', day: 'numeric', hour: '2-digit', minute: '2-digit',
    })
  } catch {
    return ts
  }
}

export function ApprovalTimeline({ revisions, createdAt }: ApprovalTimelineProps) {
  const events: TimelineEvent[] = [
    {
      id: 'created',
      type: 'created' as const,
      label: 'Draft created',
      timestamp: createdAt,
    },
    ...revisions.map((rev) => ({
      id: String(rev.revision_id),
      type: 'revision' as const,
      label: `Revision ${rev.revision_number} created`,
      actor: rev.created_by,
      timestamp: rev.created_at,
      note: rev.summary,
    })),
  ].sort((a, b) => new Date(a.timestamp).getTime() - new Date(b.timestamp).getTime())

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: 0 }}>
      {events.map((event, i) => (
        <motion.div
          key={event.id}
          initial={{ opacity: 0, x: -8 }}
          animate={{ opacity: 1, x: 0 }}
          transition={{ delay: i * 0.05 }}
          style={{ display: 'flex', gap: 12, position: 'relative' }}
        >
          {/* Connector line */}
          {i < events.length - 1 && (
            <div
              style={{
                position: 'absolute',
                left: 15,
                top: 32,
                bottom: 0,
                width: 1,
                background: 'var(--border-subtle)',
              }}
            />
          )}

          {/* Icon */}
          <div
            style={{
              width: 32,
              height: 32,
              borderRadius: '50%',
              background: iconBg(event.type),
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              flexShrink: 0,
              marginTop: 2,
              border: '1px solid var(--border-subtle)',
            }}
          >
            {eventIcon(event.type)}
          </div>

          {/* Content */}
          <div style={{ paddingBottom: 20, flex: 1 }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: 8, flexWrap: 'wrap' }}>
              <span style={{ fontSize: 13, fontWeight: 500, color: 'var(--text-primary)' }}>
                {event.label}
              </span>
              {event.actor && (
                <span style={{ fontSize: 11, color: 'var(--text-muted)' }}>by {event.actor}</span>
              )}
            </div>
            <div style={{ fontSize: 11, color: 'var(--text-muted)', marginTop: 2 }}>
              {formatTimestamp(event.timestamp)}
            </div>
            {event.note && (
              <div
                style={{
                  marginTop: 6,
                  padding: '6px 10px',
                  borderRadius: 6,
                  background: 'var(--bg-surface-raised)',
                  fontSize: 12,
                  color: 'var(--text-secondary)',
                  borderLeft: '2px solid var(--border-subtle)',
                }}
              >
                {event.note}
              </div>
            )}
          </div>
        </motion.div>
      ))}
    </div>
  )
}
