'use client'

import { useEffect, useRef } from 'react'
import { useMotionValue, useSpring, motion, useTransform } from 'framer-motion'

interface AnimatedNumberProps {
  value: number
  suffix?: string
  className?: string
  duration?: number
}

export function AnimatedNumber({
  value,
  suffix = '',
  className = '',
  duration = 800,
}: AnimatedNumberProps) {
  const motionValue = useMotionValue(0)
  const spring = useSpring(motionValue, {
    damping: 30,
    stiffness: 200,
    duration,
  })
  const displayValue = useTransform(spring, (v) => Math.round(v).toString())
  const hasAnimated = useRef(false)

  useEffect(() => {
    if (!hasAnimated.current) {
      hasAnimated.current = true
      motionValue.set(value)
    } else {
      motionValue.set(value)
    }
  }, [value, motionValue])

  return (
    <span className={`tabular-nums ${className}`}>
      <motion.span>{displayValue}</motion.span>
      {suffix && <span>{suffix}</span>}
    </span>
  )
}
