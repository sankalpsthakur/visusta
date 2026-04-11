'use client'

import { motion } from 'framer-motion'
import type { LucideIcon } from 'lucide-react'

interface EmptyStateProps {
  icon: LucideIcon
  title: string
  description?: string
  action?: {
    label: string
    onClick: () => void
  }
}

export function EmptyState({ icon: Icon, title, description, action }: EmptyStateProps) {
  return (
    <motion.div
      initial={{ opacity: 0, y: 8 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.25, ease: 'easeOut' }}
      className="rounded-lg p-10 flex flex-col items-center gap-3 text-center"
      style={{
        background: 'var(--bg-surface)',
        border: '1px solid var(--border-color)',
      }}
    >
      <div
        className="w-10 h-10 rounded-full flex items-center justify-center"
        style={{ background: 'var(--bg-elevated)' }}
      >
        <Icon className="w-5 h-5" style={{ color: 'var(--text-muted)' }} />
      </div>
      <div>
        <p className="text-sm font-medium mb-1" style={{ color: 'var(--text-primary)' }}>
          {title}
        </p>
        {description && (
          <p className="text-xs max-w-xs" style={{ color: 'var(--text-muted)' }}>
            {description}
          </p>
        )}
      </div>
      {action && (
        <motion.button
          onClick={action.onClick}
          className="text-xs px-4 py-1.5 rounded font-medium mt-1"
          style={{ background: 'var(--brand)', color: 'var(--brand-contrast)' }}
          whileHover={{ opacity: 0.85 }}
          whileTap={{ scale: 0.97 }}
        >
          {action.label}
        </motion.button>
      )}
    </motion.div>
  )
}
