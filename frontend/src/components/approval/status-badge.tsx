'use client'

import { motion } from 'framer-motion'
import type { ApprovalStatus, DraftStatus } from '@/lib/api/draft-hooks'

type Status = ApprovalStatus | DraftStatus

const STATUS_CONFIG: Record<string, { label: string; color: string; bg: string }> = {
  // ApprovalStatus
  pending: { label: 'Pending', color: 'var(--text-secondary)', bg: 'var(--bg-surface-raised)' },
  approved: { label: 'Approved', color: '#22c55e', bg: 'rgba(34,197,94,0.12)' },
  rejected: { label: 'Rejected', color: '#ef4444', bg: 'rgba(239,68,68,0.12)' },
  skipped: { label: 'Skipped', color: 'var(--text-muted)', bg: 'var(--bg-surface-raised)' },
  // DraftStatus
  composing: { label: 'Composing', color: 'var(--brand-accent)', bg: 'rgba(var(--brand-accent-rgb),0.12)' },
  review: { label: 'Review', color: '#f59e0b', bg: 'rgba(245,158,11,0.12)' },
  revision: { label: 'Revision', color: '#f97316', bg: 'rgba(249,115,22,0.12)' },
  translating: { label: 'Translating', color: '#8b5cf6', bg: 'rgba(139,92,246,0.12)' },
  approval: { label: 'Approval', color: '#3b82f6', bg: 'rgba(59,130,246,0.12)' },
  exported: { label: 'Exported', color: '#10b981', bg: 'rgba(16,185,129,0.12)' },
  archived: { label: 'Archived', color: 'var(--text-muted)', bg: 'var(--bg-surface-raised)' },
}

interface StatusBadgeProps {
  status: Status
  size?: 'sm' | 'md'
  className?: string
}

export function StatusBadge({ status, size = 'md', className }: StatusBadgeProps) {
  const config = STATUS_CONFIG[status] ?? STATUS_CONFIG.pending
  const padding = size === 'sm' ? '2px 8px' : '4px 12px'
  const fontSize = size === 'sm' ? '11px' : '12px'

  return (
    <motion.span
      initial={{ opacity: 0, scale: 0.9 }}
      animate={{ opacity: 1, scale: 1 }}
      className={className}
      style={{
        display: 'inline-flex',
        alignItems: 'center',
        gap: 6,
        padding,
        borderRadius: 999,
        fontSize,
        fontWeight: 500,
        letterSpacing: '0.02em',
        color: config.color,
        background: config.bg,
        whiteSpace: 'nowrap',
      }}
    >
      <span
        style={{
          width: 6,
          height: 6,
          borderRadius: '50%',
          background: config.color,
          flexShrink: 0,
        }}
      />
      {config.label}
    </motion.span>
  )
}
