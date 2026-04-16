'use client'

import { motion } from 'framer-motion'
import { BookOpen } from 'lucide-react'
import type { Draft, DraftSection } from '@/lib/api/draft-hooks'

interface DocumentViewerProps {
  draft: Draft
  selectedSectionId: string | null
  onSelectSection: (sectionId: string) => void
}

function BlockContent({ block }: { block: DraftSection['blocks'][number] }) {
  switch (block.type) {
    case 'heading':
      return <h3 style={{ fontSize: 16, fontWeight: 600, color: 'var(--text-primary)', margin: '16px 0 8px' }}>{block.content}</h3>
    case 'bullet_list':
      return (
        <ul style={{ margin: '0 0 8px', paddingLeft: 20 }}>
          {block.content.split('\n').filter(Boolean).map((item, i) => (
            <li key={i} style={{ fontSize: 13, color: 'var(--text-secondary)', lineHeight: 1.7 }}>{item}</li>
          ))}
        </ul>
      )
    default:
      return (
        <p style={{ fontSize: 13, color: 'var(--text-secondary)', lineHeight: 1.8, margin: '0 0 10px' }}>
          {block.content || <em style={{ color: 'var(--text-muted)', fontSize: 12 }}>Empty paragraph</em>}
        </p>
      )
  }
}

export function DocumentViewer({ draft, selectedSectionId, onSelectSection }: DocumentViewerProps) {
  return (
    <div
      style={{
        flex: 1,
        overflowY: 'auto',
        padding: '32px',
        background: 'var(--bg-surface)',
        borderRadius: 12,
        border: '1px solid var(--border-subtle)',
      }}
    >
      {/* Document header */}
      <div style={{ marginBottom: 32, paddingBottom: 20, borderBottom: '2px solid var(--border-subtle)' }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: 8, marginBottom: 8 }}>
          <BookOpen size={16} color="var(--brand-accent)" />
          <span style={{ fontSize: 11, fontWeight: 600, color: 'var(--brand-accent)', textTransform: 'uppercase', letterSpacing: '0.06em' }}>
            {draft.period} · {draft.locale.toUpperCase()}
          </span>
        </div>
        <h1 style={{ fontSize: 24, fontWeight: 700, color: 'var(--text-primary)', letterSpacing: '-0.02em', margin: 0 }}>
          {draft.title}
        </h1>
      </div>

      {/* Sections */}
      <div style={{ display: 'flex', flexDirection: 'column', gap: 0 }}>
        {draft.sections.map((section) => {
          const isSelected = section.section_id === selectedSectionId
          return (
            <motion.div
              key={section.section_id}
              onClick={() => onSelectSection(section.section_id)}
              style={{
                padding: '20px 16px',
                borderRadius: 8,
                cursor: 'pointer',
                background: isSelected ? 'rgba(var(--brand-accent-rgb),0.05)' : 'transparent',
                border: isSelected ? '1px solid rgba(var(--brand-accent-rgb),0.15)' : '1px solid transparent',
                marginBottom: 4,
                transition: 'background 0.12s, border-color 0.12s',
              }}
              whileHover={{ background: 'rgba(var(--brand-accent-rgb),0.03)' }}
            >
              <h2
                style={{
                  fontSize: 17,
                  fontWeight: 600,
                  color: isSelected ? 'var(--brand-accent)' : 'var(--text-primary)',
                  marginBottom: 14,
                  letterSpacing: '-0.01em',
                }}
              >
                {section.heading}
              </h2>

              {section.blocks.length === 0 ? (
                <p style={{ fontSize: 13, color: 'var(--text-muted)', fontStyle: 'italic' }}>
                  No content yet — click to edit
                </p>
              ) : (
                section.blocks.map((block, i) => <BlockContent key={i} block={block} />)
              )}

              {section.citations.length > 0 && (
                <div style={{ marginTop: 10, paddingTop: 8, borderTop: '1px solid var(--border-subtle)' }}>
                  <div style={{ fontSize: 10, fontWeight: 600, color: 'var(--text-muted)', textTransform: 'uppercase', letterSpacing: '0.06em', marginBottom: 4 }}>
                    Citations
                  </div>
                  {section.citations.map((citation, i) => {
                    // Runtime shape is {label, url?} for new revisions and a plain string
                    // for legacy revisions; the declared TS type in draft-hooks stays
                    // as string[] because that file is out of scope for this change.
                    const c = citation as unknown as string | { label: string; url?: string | null }
                    const label = typeof c === 'string' ? c : c.label
                    const url = typeof c === 'string' ? null : c.url ?? null
                    return (
                      <div key={i} style={{ fontSize: 11, color: 'var(--text-muted)', fontFamily: 'monospace', marginBottom: 2 }}>
                        {i + 1}.{' '}
                        {url ? (
                          <a
                            href={url}
                            target="_blank"
                            rel="noopener noreferrer"
                            onClick={(event) => event.stopPropagation()}
                            style={{ color: 'var(--brand-accent)', textDecoration: 'underline' }}
                          >
                            {label}
                          </a>
                        ) : (
                          <span>{label}</span>
                        )}
                      </div>
                    )
                  })}
                </div>
              )}
            </motion.div>
          )
        })}
      </div>
    </div>
  )
}
