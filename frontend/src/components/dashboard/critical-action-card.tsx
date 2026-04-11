'use client'

import { motion, Variants } from 'framer-motion'
import type { ChangeEntry } from '@/lib/api/hooks'

const DAYS_90 = 90 * 24 * 60 * 60 * 1000

function isWithin90Days(dateStr: string | null): boolean {
  if (!dateStr) return false
  const target = new Date(dateStr).getTime()
  const now = Date.now()
  const diff = target - now
  return diff >= 0 && diff <= DAYS_90
}

const cardVariants: Variants = {
  hidden: { opacity: 0, x: -12 },
  show: { opacity: 1, x: 0 },
}

export const criticalActionsVariants: Variants = {
  hidden: {},
  show: {
    transition: {
      staggerChildren: 0.08,
    },
  },
}

interface CriticalActionCardProps {
  entry: ChangeEntry
}

export function CriticalActionCard({ entry }: CriticalActionCardProps) {
  const urgent = isWithin90Days(entry.enforcement_date)

  return (
    <motion.div
      variants={cardVariants}
      className="rounded-lg p-5 pl-4 relative overflow-hidden"
      style={{
        background: 'var(--bg-surface)',
        border: '1px solid var(--border)',
        borderLeft: '4px solid var(--severity-critical)',
        boxShadow: urgent
          ? '0 0 12px rgba(198, 40, 40, 0.2), inset 0 0 12px rgba(198, 40, 40, 0.04)'
          : undefined,
      }}
      whileHover={{ y: -2 }}
      transition={{ type: 'spring', stiffness: 300, damping: 20 }}
    >
      {urgent && (
        <motion.div
          className="absolute inset-0 pointer-events-none rounded-lg"
          style={{
            background: 'rgba(198, 40, 40, 0.04)',
          }}
          animate={{ opacity: [0.4, 0.8, 0.4] }}
          transition={{ duration: 2, repeat: Infinity, ease: 'easeInOut' }}
        />
      )}

      <div className="relative">
        <div className="flex items-start justify-between gap-3 mb-2">
          <span
            className="text-xs tabular-nums"
            style={{
              color: 'var(--text-muted)',
              fontFamily: 'var(--font-mono)',
              fontVariantNumeric: 'tabular-nums',
            }}
          >
            {entry.regulation_id}
          </span>
          {urgent && (
            <span
              className="text-xs flex-shrink-0"
              style={{ color: 'var(--severity-critical)', fontFamily: 'var(--font-mono)' }}
            >
              ENFORCEMENT IMMINENT
            </span>
          )}
        </div>

        <p
          className="text-sm font-medium mb-2"
          style={{ color: 'var(--text-primary)' }}
        >
          {entry.title}
        </p>

        <p
          className="text-xs mb-3"
          style={{ color: 'var(--text-muted)', lineHeight: '1.5' }}
        >
          {entry.summary}
        </p>

        {entry.action_required && (
          <div
            className="text-xs p-2.5 rounded"
            style={{
              background: 'var(--bg-elevated)',
              color: 'var(--text-primary)',
              borderLeft: '2px solid var(--severity-critical)',
            }}
          >
            <span style={{ color: 'var(--text-muted)' }}>Action: </span>
            {entry.action_required}
          </div>
        )}

        {entry.enforcement_date && (
          <div className="mt-2 text-xs" style={{ color: 'var(--text-muted)' }}>
            Enforcement:{' '}
            <span
              style={{
                color: urgent ? 'var(--severity-critical)' : 'var(--text-primary)',
                fontFamily: 'var(--font-mono)',
              }}
            >
              {entry.enforcement_date}
            </span>
          </div>
        )}
      </div>
    </motion.div>
  )
}
