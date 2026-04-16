'use client'

import { motion } from 'framer-motion'
import { GitCompare, Plus, Minus } from 'lucide-react'
import type { DraftRevision, DraftSection } from '@/lib/api/draft-hooks'

interface RevisionDiffProps {
  revision: DraftRevision
  previousRevision: DraftRevision | null
}

function diffBlocks(
  prev: DraftSection | undefined,
  curr: DraftSection
): { type: 'added' | 'removed' | 'changed' | 'same'; content: string }[] {
  if (!prev) {
    return curr.blocks.map((b) => ({ type: 'added', content: b.content }))
  }

  const result: { type: 'added' | 'removed' | 'changed' | 'same'; content: string }[] = []
  const maxLen = Math.max(prev.blocks.length, curr.blocks.length)

  for (let i = 0; i < maxLen; i++) {
    const p = prev.blocks[i]
    const c = curr.blocks[i]

    if (!p && c) {
      result.push({ type: 'added', content: c.content })
    } else if (p && !c) {
      result.push({ type: 'removed', content: p.content })
    } else if (p && c) {
      if (p.content === c.content) {
        result.push({ type: 'same', content: c.content })
      } else {
        result.push({ type: 'removed', content: p.content })
        result.push({ type: 'added', content: c.content })
      }
    }
  }

  return result
}

export function RevisionDiff({ revision, previousRevision }: RevisionDiffProps) {
  const changedSections = revision.sections.filter((curr) => {
    if (!previousRevision) return true
    const prev = previousRevision.sections.find((s) => s.section_id === curr.section_id)
    if (!prev) return true
    return JSON.stringify(prev.blocks) !== JSON.stringify(curr.blocks)
  })

  if (changedSections.length === 0) {
    return (
      <div style={{ textAlign: 'center', padding: '32px 0', color: 'var(--text-muted)' }}>
        <GitCompare size={28} style={{ margin: '0 auto 8px', opacity: 0.3 }} />
        <div style={{ fontSize: 13 }}>No changes detected</div>
      </div>
    )
  }

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: 20 }}>
      <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
        <GitCompare size={15} color="var(--text-secondary)" />
        <span style={{ fontSize: 13, fontWeight: 500, color: 'var(--text-primary)' }}>
          Changes in revision {revision.revision_number}
          {previousRevision && ` vs rev ${previousRevision.revision_number}`}
        </span>
      </div>

      {changedSections.map((curr) => {
        const prev = previousRevision?.sections.find((s) => s.section_id === curr.section_id)
        const diffs = diffBlocks(prev, curr)

        return (
          <motion.div
            key={curr.section_id}
            initial={{ opacity: 0, y: 4 }}
            animate={{ opacity: 1, y: 0 }}
          >
            <div
              style={{
                fontSize: 12,
                fontWeight: 600,
                color: 'var(--text-secondary)',
                marginBottom: 8,
                textTransform: 'uppercase',
                letterSpacing: '0.04em',
              }}
            >
              {curr.heading}
            </div>

            <div
              style={{
                borderRadius: 8,
                border: '1px solid var(--border-subtle)',
                overflow: 'hidden',
                fontFamily: 'monospace',
                fontSize: 12,
              }}
            >
              {diffs.map((diff, i) => {
                if (diff.type === 'same') return null
                return (
                  <div
                    key={i}
                    style={{
                      display: 'flex',
                      gap: 10,
                      padding: '6px 12px',
                      background: diff.type === 'added' ? 'rgba(34,197,94,0.08)' : 'rgba(239,68,68,0.08)',
                      borderRadius: 4,
                    }}
                  >
                    <div style={{ flexShrink: 0, color: diff.type === 'added' ? '#22c55e' : '#ef4444', display: 'flex', alignItems: 'flex-start', paddingTop: 2 }}>
                      {diff.type === 'added' ? <Plus size={11} /> : <Minus size={11} />}
                    </div>
                    <div style={{ color: diff.type === 'added' ? 'rgba(34,197,94,0.9)' : 'rgba(239,68,68,0.9)', lineHeight: 1.5, flex: 1, wordBreak: 'break-word' }}>
                      {diff.content}
                    </div>
                  </div>
                )
              })}
            </div>
          </motion.div>
        )
      })}
    </div>
  )
}
