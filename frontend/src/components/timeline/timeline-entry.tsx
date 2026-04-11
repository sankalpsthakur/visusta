'use client'

import { motion } from 'framer-motion'
import { SeverityBadge, Severity } from '@/components/shared/severity-badge'
import { EnforcementCountdown } from './enforcement-countdown'
import { MilestoneMarker } from './milestone-marker'

export interface TimelineEntryData {
  id: string
  date: string
  regulationId: string
  title: string
  changeType: string
  severity: Severity
  summary?: string
  topic: string
  effectiveDate?: string
  enforcementDate?: string
}

interface TimelineEntryProps {
  entry: TimelineEntryData
}

const CHANGE_TYPE_LABELS: Record<string, string> = {
  regulation_removed: 'removed',
  amendment: 'amended',
  new_regulation: 'new',
  status_change: 'status',
  content_update: 'updated',
  timeline_change: 'timeline',
}

function severityDotColor(severity: Severity): string {
  switch (severity) {
    case 'critical': return 'var(--severity-critical)'
    case 'high': return 'var(--severity-high)'
    case 'medium': return 'var(--severity-medium)'
    case 'low': return 'var(--severity-low)'
  }
}

export function TimelineEntry({ entry }: TimelineEntryProps) {
  const dotColor = severityDotColor(entry.severity)
  const changeLabel = CHANGE_TYPE_LABELS[entry.changeType] ?? entry.changeType.replace(/_/g, ' ')

  return (
    <motion.div
      initial={{ opacity: 0, x: 40 }}
      whileInView={{ opacity: 1, x: 0 }}
      viewport={{ once: true }}
      transition={{ duration: 0.3, ease: 'easeOut' }}
      className="relative flex gap-6 pb-8"
    >
      {/* Dot on the timeline line */}
      <div className="relative flex-shrink-0 w-4 flex justify-center">
        <div
          className="w-2.5 h-2.5 rounded-full mt-1.5 flex-shrink-0 z-10"
          style={{
            background: dotColor,
            boxShadow: `0 0 0 3px var(--bg-primary), 0 0 0 4px ${dotColor}40`,
          }}
        />
      </div>

      {/* Content */}
      <div className="flex-1 min-w-0 pb-2">
        <div className="flex items-center gap-2 mb-1 flex-wrap">
          <span
            className="text-xs tabular-nums"
            style={{ color: 'var(--text-muted)', fontFamily: 'var(--font-mono)' }}
          >
            {entry.date}
          </span>
          <span
            className="text-xs px-1.5 py-0.5 rounded"
            style={{
              background: 'var(--bg-elevated)',
              color: 'var(--text-muted)',
              border: '1px solid var(--border-color)',
              fontFamily: 'var(--font-mono)',
            }}
          >
            {changeLabel}
          </span>
          <SeverityBadge severity={entry.severity} />
        </div>

        <div
          className="text-xs mb-0.5"
          style={{ color: 'var(--text-muted)', fontFamily: 'var(--font-mono)' }}
        >
          {entry.regulationId}
        </div>

        <div
          className="text-sm font-medium mb-1"
          style={{ color: 'var(--text-primary)' }}
        >
          {entry.title}
        </div>

        {entry.summary && (
          <div className="text-xs mb-2" style={{ color: 'var(--text-muted)' }}>
            {entry.summary}
          </div>
        )}

        {/* Milestone markers */}
        {(entry.effectiveDate || entry.enforcementDate) && (
          <div className="flex items-center gap-3 mt-2">
            {entry.effectiveDate && (
              <div className="flex items-center gap-1.5">
                <MilestoneMarker date={entry.effectiveDate} type="effective" />
                <span className="text-xs" style={{ color: 'var(--text-muted)' }}>
                  effective {entry.effectiveDate}
                </span>
              </div>
            )}
            {entry.enforcementDate && (
              <div className="flex items-center gap-1.5">
                <MilestoneMarker date={entry.enforcementDate} type="enforcement" />
                <EnforcementCountdown enforcementDate={entry.enforcementDate} />
              </div>
            )}
          </div>
        )}
      </div>
    </motion.div>
  )
}
