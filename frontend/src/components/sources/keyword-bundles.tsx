'use client'

import { motion } from 'framer-motion'
import { Tag, ChevronRight, Hash } from 'lucide-react'
import type { KeywordBundle } from '@/lib/api/source-hooks'

interface KeywordBundlesProps {
  bundles: KeywordBundle[]
  selectedBundle: string | null
  onSelect: (bundleName: string) => void
  onAdd: () => void
}

export function KeywordBundles({ bundles, selectedBundle, onSelect, onAdd }: KeywordBundlesProps) {
  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: 4 }}>
      <div style={{ fontSize: 10, fontWeight: 600, color: 'var(--text-muted)', textTransform: 'uppercase', letterSpacing: '0.06em', padding: '0 4px', marginBottom: 6 }}>
        Keyword bundles ({bundles.length})
      </div>

      {bundles.map((bundle) => {
        const isSelected = bundle.bundle_name === selectedBundle
        return (
          <motion.div
            key={bundle.bundle_name}
            whileHover={{ x: 2 }}
            onClick={() => onSelect(bundle.bundle_name)}
            style={{
              display: 'flex',
              alignItems: 'center',
              gap: 8,
              padding: '8px 10px',
              borderRadius: 8,
              cursor: 'pointer',
              background: isSelected ? 'rgba(var(--brand-accent-rgb),0.08)' : 'var(--bg-surface-raised)',
              border: isSelected ? '1px solid rgba(var(--brand-accent-rgb),0.3)' : '1px solid var(--border-subtle)',
            }}
          >
            <Tag size={13} color={isSelected ? 'var(--brand-accent)' : 'var(--text-muted)'} />
            <div style={{ flex: 1, minWidth: 0 }}>
              <div style={{ fontSize: 13, fontWeight: isSelected ? 500 : 400, color: isSelected ? 'var(--brand-accent)' : 'var(--text-primary)', overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>
                {bundle.bundle_name.replace(/_/g, ' ')}
              </div>
              <div style={{ fontSize: 10, color: 'var(--text-muted)' }}>
                {bundle.active_count}/{bundle.rule_count} rules active
              </div>
            </div>
            <ChevronRight size={12} color="var(--text-muted)" />
          </motion.div>
        )
      })}

      <motion.button
        whileHover={{ scale: 1.01 }}
        whileTap={{ scale: 0.99 }}
        onClick={onAdd}
        style={{
          display: 'flex',
          alignItems: 'center',
          gap: 6,
          padding: '8px 10px',
          borderRadius: 8,
          border: '1px dashed var(--border-subtle)',
          background: 'transparent',
          color: 'var(--text-muted)',
          fontSize: 12,
          cursor: 'pointer',
          marginTop: 4,
        }}
      >
        <Hash size={12} />
        New bundle
      </motion.button>
    </div>
  )
}
