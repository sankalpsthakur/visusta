'use client'

import { motion, Variants } from 'framer-motion'
import { SeverityBadge } from '@/components/shared/severity-badge'
import type { Severity } from '@/components/shared/severity-badge'
import type { TopicChangeStatus } from '@/lib/api/hooks'

const TOPIC_LABELS: Record<string, string> = {
  ghg: 'GHG',
  packaging: 'Packaging',
  water: 'Water',
  waste: 'Waste',
  social_human_rights: 'Social / Human Rights',
}

const STATUS_LEVEL_TO_SEVERITY: Record<string, Severity> = {
  law_passed: 'critical',
  enforcement_active: 'critical',
  amendment_in_progress: 'high',
  consultation_open: 'medium',
  proposed: 'low',
}

function levelToSeverity(level: string | null): Severity {
  if (!level) return 'low'
  return STATUS_LEVEL_TO_SEVERITY[level] ?? 'medium'
}

export interface TopicStatusCardProps {
  topic: string
  status: TopicChangeStatus
}

const cardVariants: Variants = {
  hidden: { opacity: 0, y: 20 },
  show: { opacity: 1, y: 0 },
}

export const topicGridVariants: Variants = {
  hidden: {},
  show: {
    transition: {
      staggerChildren: 0.08,
    },
  },
}

export function TopicStatusCard({ topic, status }: TopicStatusCardProps) {
  const label = TOPIC_LABELS[topic] ?? topic
  const changed = status.changed_since_last
  const severity = changed ? levelToSeverity(status.level) : undefined

  return (
    <motion.div
      variants={cardVariants}
      className="rounded-lg p-5"
      style={{
        background: 'var(--bg-surface)',
        border: `1px solid ${changed ? 'var(--border)' : 'var(--border)'}`,
      }}
      whileHover={{ y: -2 }}
      transition={{ type: 'spring', stiffness: 300, damping: 20 }}
    >
      <div className="flex items-start justify-between gap-2 mb-3">
        <span
          className="text-sm font-medium"
          style={{ color: 'var(--text-primary)' }}
        >
          {label}
        </span>
        <span
          className="text-xs px-1.5 py-0.5 rounded flex-shrink-0"
          style={{
            color: changed ? 'var(--severity-high)' : 'var(--severity-low)',
            background: changed
              ? 'rgba(245, 127, 23, 0.1)'
              : 'rgba(76, 175, 80, 0.1)',
            fontFamily: 'var(--font-mono)',
            letterSpacing: '0.05em',
            fontSize: '10px',
          }}
        >
          {changed ? 'CHANGED' : 'UNCHANGED'}
        </span>
      </div>

      <div className="flex items-center justify-between">
        {severity ? (
          <SeverityBadge severity={severity} />
        ) : (
          <span className="text-xs" style={{ color: 'var(--text-muted)' }}>
            No change
          </span>
        )}
        {status.changes_detected > 0 && (
          <span
            className="text-xs tabular-nums"
            style={{ color: 'var(--text-muted)', fontVariantNumeric: 'tabular-nums' }}
          >
            {status.changes_detected} {status.changes_detected === 1 ? 'change' : 'changes'}
          </span>
        )}
      </div>
    </motion.div>
  )
}
