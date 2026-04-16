'use client'

import { useState } from 'react'
import { motion, AnimatePresence } from 'framer-motion'
import { ChevronDown, ChevronRight, Edit3, BookOpen } from 'lucide-react'
import { StatusBadge } from '@/components/approval/status-badge'
import type { DraftSection as DraftSectionType } from '@/lib/api/draft-hooks'

interface DraftSectionProps {
  section: DraftSectionType
  isSelected: boolean
  onSelect: () => void
  onEdit: () => void
}

export function DraftSection({ section, isSelected, onSelect, onEdit }: DraftSectionProps) {
  const [expanded, setExpanded] = useState(false)

  return (
    <motion.div
      layout
      style={{
        borderRadius: 10,
        border: isSelected ? '1px solid rgba(var(--brand-accent-rgb),0.3)' : '1px solid var(--border-subtle)',
        background: isSelected ? 'rgba(var(--brand-accent-rgb),0.04)' : 'var(--bg-surface)',
        overflow: 'hidden',
      }}
    >
      {/* Header row */}
      <div
        onClick={onSelect}
        style={{
          display: 'flex',
          alignItems: 'center',
          gap: 10,
          padding: '12px 14px',
          cursor: 'pointer',
        }}
      >
        <motion.button
          onClick={(e) => { e.stopPropagation(); setExpanded(!expanded) }}
          style={{ background: 'none', border: 'none', cursor: 'pointer', padding: 0, display: 'flex', alignItems: 'center', color: 'var(--text-muted)' }}
        >
          {expanded ? <ChevronDown size={14} /> : <ChevronRight size={14} />}
        </motion.button>

        <BookOpen size={13} color="var(--text-muted)" />

        <span style={{ fontSize: 13, fontWeight: 500, color: 'var(--text-primary)', flex: 1 }}>
          {section.heading}
        </span>

        <StatusBadge status={section.approval_status} size="sm" />

        <motion.button
          whileHover={{ scale: 1.08 }}
          whileTap={{ scale: 0.92 }}
          onClick={(e) => { e.stopPropagation(); onEdit() }}
          style={{
            width: 28,
            height: 28,
            borderRadius: 7,
            border: '1px solid var(--border-subtle)',
            background: 'var(--bg-surface-raised)',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            cursor: 'pointer',
            color: 'var(--text-secondary)',
          }}
        >
          <Edit3 size={12} />
        </motion.button>
      </div>

      {/* Expanded content preview */}
      <AnimatePresence>
        {expanded && (
          <motion.div
            initial={{ opacity: 0, height: 0 }}
            animate={{ opacity: 1, height: 'auto' }}
            exit={{ opacity: 0, height: 0 }}
            style={{ overflow: 'hidden' }}
          >
            <div
              style={{
                padding: '0 14px 14px 14px',
                borderTop: '1px solid var(--border-subtle)',
                display: 'flex',
                flexDirection: 'column',
                gap: 8,
              }}
            >
              {section.blocks.length === 0 ? (
                <p style={{ fontSize: 12, color: 'var(--text-muted)', margin: '10px 0 0', fontStyle: 'italic' }}>
                  No content yet
                </p>
              ) : (
                section.blocks.slice(0, 3).map((block, i) => (
                  <div
                    key={i}
                    style={{
                      fontSize: 12,
                      color: 'var(--text-secondary)',
                      lineHeight: 1.6,
                      overflow: 'hidden',
                      display: '-webkit-box',
                      WebkitLineClamp: 3,
                      WebkitBoxOrient: 'vertical',
                    }}
                  >
                    {block.content}
                  </div>
                ))
              )}

              {section.citations.length > 0 && (
                <div style={{ fontSize: 11, color: 'var(--text-muted)', marginTop: 4 }}>
                  {section.citations.length} citation{section.citations.length !== 1 ? 's' : ''}
                </div>
              )}
            </div>
          </motion.div>
        )}
      </AnimatePresence>
    </motion.div>
  )
}
