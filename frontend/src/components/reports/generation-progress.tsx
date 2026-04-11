'use client'

import { motion, AnimatePresence } from 'framer-motion'

interface GenerationProgressProps {
  isGenerating: boolean
}

export function GenerationProgress({ isGenerating }: GenerationProgressProps) {
  return (
    <AnimatePresence>
      {isGenerating && (
        <motion.div
          initial={{ opacity: 0, y: 4 }}
          animate={{ opacity: 1, y: 0 }}
          exit={{ opacity: 0, y: -4 }}
          transition={{ duration: 0.2 }}
          className="w-full"
        >
          <motion.p
            className="text-xs mb-2"
            style={{ color: 'var(--text-muted)' }}
            animate={{ opacity: [0.5, 1, 0.5] }}
            transition={{ duration: 2, repeat: Infinity, ease: 'easeInOut' }}
          >
            Generating report...
          </motion.p>

          {/* Progress bar track */}
          <div
            className="w-full h-1 rounded-full overflow-hidden"
            style={{ background: 'var(--bg-elevated)' }}
          >
            {/* Animated bar */}
            <motion.div
              className="h-full rounded-full relative overflow-hidden"
              style={{ background: 'var(--brand)', originX: 0 }}
              animate={{ width: ['20%', '85%', '20%'] }}
              transition={{
                duration: 2.4,
                repeat: Infinity,
                ease: [0.4, 0, 0.2, 1],
              }}
            >
              {/* Shimmer overlay */}
              <div
                style={{
                  position: 'absolute',
                  inset: 0,
                  background:
                    'linear-gradient(90deg, transparent 0%, color-mix(in srgb, var(--brand-accent) 30%, transparent) 50%, transparent 100%)',
                  animation: 'shimmer 1.4s infinite',
                }}
              />
            </motion.div>
          </div>
        </motion.div>
      )}
    </AnimatePresence>
  )
}
