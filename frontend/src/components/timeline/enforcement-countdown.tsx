'use client'

import { useEffect } from 'react'
import { useMotionValue, useSpring, motion, useTransform } from 'framer-motion'

interface EnforcementCountdownProps {
  enforcementDate: string
}

function getDaysUntil(dateStr: string): number {
  const target = new Date(dateStr)
  const now = new Date()
  const diff = target.getTime() - now.getTime()
  return Math.ceil(diff / (1000 * 60 * 60 * 24))
}

function getCountdownColor(days: number): string {
  if (days < 30) return 'var(--severity-critical)'
  if (days < 90) return 'var(--severity-medium)'
  return 'var(--severity-low)'
}

export function EnforcementCountdown({ enforcementDate }: EnforcementCountdownProps) {
  const days = getDaysUntil(enforcementDate)
  const color = getCountdownColor(days)

  const motionValue = useMotionValue(0)
  const spring = useSpring(motionValue, { damping: 30, stiffness: 200 })
  const displayValue = useTransform(spring, (v) => Math.round(v).toString())

  useEffect(() => {
    motionValue.set(days)
  }, [days, motionValue])

  const isPulsing = days < 30

  return (
    <span
      className="inline-flex items-center gap-1 text-xs tabular-nums"
      style={{ color }}
    >
      <motion.span
        animate={isPulsing ? { opacity: [1, 0.4, 1] } : {}}
        transition={isPulsing ? { duration: 1.5, repeat: Infinity, ease: 'easeInOut' } : {}}
        className="font-semibold"
      >
        <motion.span>{displayValue}</motion.span>
      </motion.span>
      <span style={{ color: 'var(--text-muted)' }}>days until enforcement</span>
    </span>
  )
}
