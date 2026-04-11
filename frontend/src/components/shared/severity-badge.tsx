'use client'

import { motion } from 'framer-motion'
import { AlertTriangle, CheckCircle, Info } from 'lucide-react'

const SEVERITY_CONFIG = {
  critical: {
    icon: <AlertTriangle className="w-3.5 h-3.5" />,
    tint: 'var(--severity-critical)',
    ink: 'var(--severity-critical-ink)',
  },
  high: {
    icon: <AlertTriangle className="w-3.5 h-3.5" />,
    tint: 'var(--severity-high)',
    ink: 'var(--severity-high-ink)',
  },
  medium: {
    icon: <Info className="w-3.5 h-3.5" />,
    tint: 'var(--severity-medium)',
    ink: 'var(--severity-medium-ink)',
  },
  low: {
    icon: <CheckCircle className="w-3.5 h-3.5" />,
    tint: 'var(--severity-low)',
    ink: 'var(--severity-low-ink)',
  },
}

export type Severity = keyof typeof SEVERITY_CONFIG

interface SeverityBadgeProps {
  severity: Severity
}

const badgeStyle = (tint: string, ink: string) => ({
  color: ink,
  background: `color-mix(in srgb, ${tint} 15%, transparent)`,
  border: `1px solid color-mix(in srgb, ${tint} 35%, transparent)`,
})

export function SeverityBadge({ severity }: SeverityBadgeProps) {
  const config = SEVERITY_CONFIG[severity]
  const style = badgeStyle(config.tint, config.ink)

  if (severity === 'critical') {
    return (
      <motion.span
        className="inline-flex items-center gap-1 text-xs px-2 py-0.5 rounded"
        style={style}
        animate={{ scale: [1, 1.05, 1], opacity: [1, 0.85, 1] }}
        transition={{ duration: 2, repeat: Infinity, ease: 'easeInOut' }}
      >
        {config.icon}
        {severity}
      </motion.span>
    )
  }

  return (
    <span
      className="inline-flex items-center gap-1 text-xs px-2 py-0.5 rounded"
      style={style}
    >
      {config.icon}
      {severity}
    </span>
  )
}
