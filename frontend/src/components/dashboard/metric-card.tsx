'use client'

import { motion, Variants } from 'framer-motion'
import type { LucideIcon } from 'lucide-react'
import { AnimatedNumber } from '@/components/shared/animated-number'

export interface MetricCardProps {
  label: string
  value: number
  icon?: LucideIcon
  trend?: 'up' | 'down' | 'neutral'
  valueColor?: string
}

const cardVariants: Variants = {
  hidden: { opacity: 0, y: 20 },
  show: { opacity: 1, y: 0 },
}

export const metricGridVariants: Variants = {
  hidden: {},
  show: {
    transition: {
      staggerChildren: 0.08,
    },
  },
}

export function MetricCard({ label, value, icon: Icon, trend, valueColor }: MetricCardProps) {
  const color = valueColor ?? 'var(--text-primary)'

  return (
    <motion.div
      variants={cardVariants}
      className="rounded-lg p-6"
      style={{
        background: 'var(--bg-surface)',
        border: '1px solid var(--border)',
      }}
      whileHover={{ y: -2 }}
      transition={{ type: 'spring', stiffness: 300, damping: 20 }}
    >
      {Icon && (
        <div className="mb-3" style={{ color: 'var(--text-muted)' }}>
          <Icon size={16} />
        </div>
      )}
      <div className="text-xs mb-3" style={{ color: 'var(--text-muted)' }}>
        {label}
      </div>
      <div
        className="text-3xl font-semibold tabular-nums font-variant-numeric"
        style={{ color, fontVariantNumeric: 'tabular-nums' }}
      >
        <AnimatedNumber value={value} />
      </div>
      {trend && trend !== 'neutral' && (
        <div
          className="text-xs mt-2"
          style={{ color: trend === 'up' ? 'var(--severity-low)' : 'var(--severity-critical)' }}
        >
          {trend === 'up' ? '+ this period' : '- this period'}
        </div>
      )}
    </motion.div>
  )
}
