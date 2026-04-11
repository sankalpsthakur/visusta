'use client'

import { motion } from 'framer-motion'
import { TimelineEntry, TimelineEntryData } from './timeline-entry'

interface RegulatoryTimelineProps {
  entries: TimelineEntryData[]
  clientId: string
}

const containerVariants = {
  hidden: {},
  show: {
    transition: {
      staggerChildren: 0.08,
    },
  },
}

export function RegulatoryTimeline({ entries }: RegulatoryTimelineProps) {
  if (entries.length === 0) {
    return (
      <div
        className="rounded-lg p-6 text-center"
        style={{
          background: 'var(--bg-surface)',
          border: '1px solid var(--border-color)',
        }}
      >
        <p className="text-sm" style={{ color: 'var(--text-muted)' }}>
          No regulatory changes to display
        </p>
      </div>
    )
  }

  return (
    <div
      className="rounded-lg p-5"
      style={{
        background: 'var(--bg-surface)',
        border: '1px solid var(--border-color)',
        maxHeight: '480px',
        overflowY: 'auto',
      }}
    >
      <div className="relative">
        {/* Vertical timeline line */}
        <div
          className="absolute left-[7px] top-2 bottom-2 w-px"
          style={{ background: 'var(--border-color)' }}
        />

        <motion.div
          variants={containerVariants}
          initial="hidden"
          animate="show"
        >
          {entries.map((entry) => (
            <TimelineEntry key={entry.id} entry={entry} />
          ))}
        </motion.div>
      </div>
    </div>
  )
}
