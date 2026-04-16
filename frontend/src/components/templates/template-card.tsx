'use client'

import { motion } from 'framer-motion'
import { LayoutTemplate, Tag, Clock, FileText, ChevronRight } from 'lucide-react'
import type { Template } from '@/lib/api/template-hooks'

interface TemplateCardProps {
  template: Template
  onClick: (template: Template) => void
}

function formatDate(ts: string): string {
  try {
    return new Date(ts).toLocaleDateString(undefined, { month: 'short', day: 'numeric', year: 'numeric' })
  } catch {
    return ts
  }
}

export function TemplateCard({ template, onClick }: TemplateCardProps) {
  return (
    <motion.div
      whileHover={{ y: -2, boxShadow: '0 8px 24px rgba(0,0,0,0.12)' }}
      whileTap={{ scale: 0.98 }}
      onClick={() => onClick(template)}
      style={{
        padding: '18px 20px',
        borderRadius: 12,
        border: '1px solid var(--border-subtle)',
        background: 'var(--bg-surface)',
        cursor: 'pointer',
        display: 'flex',
        flexDirection: 'column',
        gap: 12,
        position: 'relative',
      }}
    >
      <div style={{ display: 'flex', alignItems: 'flex-start', gap: 12 }}>
        <div
          style={{
            width: 40,
            height: 40,
            borderRadius: 10,
            background: 'var(--bg-surface-raised)',
            border: '1px solid var(--border-subtle)',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            flexShrink: 0,
          }}
        >
          <LayoutTemplate size={18} color="var(--brand-accent)" />
        </div>

        <div style={{ flex: 1, minWidth: 0 }}>
          <div style={{ fontSize: 14, fontWeight: 600, color: 'var(--text-primary)', marginBottom: 2 }}>
            {template.display_name}
          </div>
          <div
            style={{
              fontSize: 12,
              color: 'var(--text-secondary)',
              overflow: 'hidden',
              display: '-webkit-box',
              WebkitLineClamp: 2,
              WebkitBoxOrient: 'vertical',
            }}
          >
            {template.description}
          </div>
        </div>
      </div>

      <div style={{ display: 'flex', flexWrap: 'wrap', gap: 6 }}>
        {template.industry_tags.map((tag) => (
          <span
            key={tag}
            style={{
              display: 'inline-flex',
              alignItems: 'center',
              gap: 4,
              fontSize: 11,
              color: 'var(--text-secondary)',
              background: 'var(--bg-surface-raised)',
              padding: '2px 8px',
              borderRadius: 999,
              border: '1px solid var(--border-subtle)',
            }}
          >
            <Tag size={9} />
            {tag}
          </span>
        ))}
        <span
          style={{
            display: 'inline-flex',
            alignItems: 'center',
            gap: 4,
            fontSize: 11,
            color: 'var(--brand-accent)',
            background: 'rgba(var(--brand-accent-rgb),0.08)',
            padding: '2px 8px',
            borderRadius: 999,
            border: '1px solid rgba(var(--brand-accent-rgb),0.2)',
          }}
        >
          {template.report_type}
        </span>
      </div>

      <div
        style={{
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'space-between',
          paddingTop: 8,
          borderTop: '1px solid var(--border-subtle)',
        }}
      >
        <div style={{ display: 'flex', gap: 14 }}>
          <span style={{ fontSize: 11, color: 'var(--text-muted)', display: 'flex', alignItems: 'center', gap: 4 }}>
            <FileText size={10} />
            {template.current_version.sections.length} sections
          </span>
          <span style={{ fontSize: 11, color: 'var(--text-muted)', display: 'flex', alignItems: 'center', gap: 4 }}>
            <Clock size={10} />
            v{template.current_version.version_number} · {formatDate(template.updated_at)}
          </span>
        </div>
        <ChevronRight size={14} color="var(--text-muted)" />
      </div>
    </motion.div>
  )
}
