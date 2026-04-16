'use client'

import { motion } from 'framer-motion'
import { ArrowLeft, CheckSquare, GitBranch, Download, Archive } from 'lucide-react'
import { useState } from 'react'
import { StatusBadge } from '@/components/approval/status-badge'
import { getDraftStatusTransitions, type Draft, type DraftStatus } from '@/lib/api/draft-hooks'

interface DraftToolbarProps {
  draft: Draft
  onBack: () => void
  onStatusChange: (status: DraftStatus) => void
  onExport: () => void
  onCompose?: () => void
  onTranslate?: (locale: string) => void
  availableLocales?: Array<{ code: string; label: string }>
  isComposing?: boolean
  isTranslating?: boolean
  isUpdating?: boolean
}

const TRANSITION_LABELS: Record<DraftStatus, string> = {
  composing: 'Set to Composing',
  review: 'Submit for Review',
  revision: 'Request Revision',
  translating: 'Start Translation',
  approval: 'Submit for Approval',
  approved: 'Approve Draft',
  exported: 'Mark as Exported',
  archived: 'Archive Draft',
}

export function DraftToolbar({
  draft,
  onBack,
  onStatusChange,
  onExport,
  onCompose,
  onTranslate,
  availableLocales = [],
  isComposing,
  isTranslating,
  isUpdating,
}: DraftToolbarProps) {
  const [targetLocale, setTargetLocale] = useState(
    availableLocales.find((locale) => locale.code !== draft.locale)?.code ?? draft.locale,
  )
  const nextStatuses = getDraftStatusTransitions(draft.status)
  const translationOptions = availableLocales.filter((locale) => locale.code !== draft.locale)

  return (
    <div
      style={{
        display: 'flex',
        alignItems: 'center',
        gap: 10,
        padding: '10px 16px',
        borderBottom: '1px solid var(--border-subtle)',
        background: 'var(--bg-surface)',
      }}
    >
      {/* Back */}
      <motion.button
        whileHover={{ scale: 1.05 }}
        whileTap={{ scale: 0.95 }}
        onClick={onBack}
        style={{
          width: 32,
          height: 32,
          borderRadius: 8,
          border: '1px solid var(--border-subtle)',
          background: 'var(--bg-surface-raised)',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center',
          cursor: 'pointer',
          color: 'var(--text-secondary)',
        }}
      >
        <ArrowLeft size={14} />
      </motion.button>

      {/* Title + status */}
      <div style={{ flex: 1, minWidth: 0 }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
          <span
            style={{
              fontSize: 14,
              fontWeight: 600,
              color: 'var(--text-primary)',
              overflow: 'hidden',
              textOverflow: 'ellipsis',
              whiteSpace: 'nowrap',
            }}
          >
            {draft.title}
          </span>
          <StatusBadge status={draft.status} size="sm" />
        </div>
        <div style={{ fontSize: 11, color: 'var(--text-muted)' }}>
          {draft.period} · {draft.locale.toUpperCase()} · Rev {draft.current_revision}
        </div>
      </div>

      {/* Actions */}
      <div style={{ display: 'flex', gap: 6, alignItems: 'center' }}>
        {onCompose && (
          <motion.button
            whileHover={{ scale: 1.02 }}
            whileTap={{ scale: 0.98 }}
            disabled={isComposing}
            onClick={onCompose}
            style={{
              display: 'flex',
              alignItems: 'center',
              gap: 5,
              padding: '7px 14px',
              borderRadius: 8,
              border: '1px solid var(--border-subtle)',
              background: 'var(--bg-surface-raised)',
              color: 'var(--text-secondary)',
              fontSize: 12,
              cursor: isComposing ? 'not-allowed' : 'pointer',
              opacity: isComposing ? 0.6 : 1,
            }}
          >
            {isComposing ? 'Composing…' : 'Compose'}
          </motion.button>
        )}

        {onTranslate && translationOptions.length > 0 && (
          <>
            <select
              aria-label="Target translation language"
              value={targetLocale}
              onChange={(event) => setTargetLocale(event.target.value)}
              style={{
                padding: '7px 10px',
                borderRadius: 8,
                border: '1px solid var(--border-subtle)',
                background: 'var(--bg-surface-raised)',
                color: 'var(--text-secondary)',
                fontSize: 12,
              }}
            >
              {translationOptions.map((locale) => (
                <option key={locale.code} value={locale.code}>
                  {locale.label}
                </option>
              ))}
            </select>
            <motion.button
              whileHover={{ scale: 1.02 }}
              whileTap={{ scale: 0.98 }}
              disabled={isTranslating}
              onClick={() => onTranslate(targetLocale)}
              style={{
                display: 'flex',
                alignItems: 'center',
                gap: 5,
                padding: '7px 14px',
                borderRadius: 8,
                border: '1px solid var(--border-subtle)',
                background: 'var(--bg-surface-raised)',
                color: 'var(--text-secondary)',
                fontSize: 12,
                cursor: isTranslating ? 'not-allowed' : 'pointer',
                opacity: isTranslating ? 0.6 : 1,
              }}
            >
              {isTranslating ? 'Translating…' : 'Translate'}
            </motion.button>
          </>
        )}

        {nextStatuses.map((status) => (
          <motion.button
            key={status}
            whileHover={{ scale: 1.02 }}
            whileTap={{ scale: 0.98 }}
            disabled={isUpdating}
            onClick={() => onStatusChange(status)}
            style={{
              display: 'flex',
              alignItems: 'center',
              gap: 5,
              padding: '7px 14px',
              borderRadius: 8,
              border: status === 'approved' ? 'none' : '1px solid var(--border-subtle)',
              background: status === 'approved'
                ? '#22c55e'
                : status === 'archived'
                  ? 'var(--bg-surface)'
                  : 'var(--bg-surface-raised)',
              color: status === 'approved'
                ? '#fff'
                : status === 'archived'
                  ? 'var(--text-muted)'
                  : 'var(--text-secondary)',
              fontSize: 12,
              fontWeight: status === 'approved' ? 500 : 400,
              cursor: isUpdating ? 'not-allowed' : 'pointer',
              opacity: isUpdating ? 0.6 : 1,
            }}
          >
            {status === 'approved' && <CheckSquare size={12} />}
            {status === 'revision' && <GitBranch size={12} />}
            {status === 'archived' && <Archive size={12} />}
            {TRANSITION_LABELS[status]}
          </motion.button>
        ))}

        <motion.button
          whileHover={{ scale: 1.02 }}
          whileTap={{ scale: 0.98 }}
          onClick={onExport}
          style={{
            display: 'flex',
            alignItems: 'center',
            gap: 5,
            padding: '7px 14px',
            borderRadius: 8,
            border: '1px solid var(--border-subtle)',
            background: 'var(--bg-surface-raised)',
            color: 'var(--text-secondary)',
            fontSize: 12,
            cursor: 'pointer',
          }}
        >
          <Download size={12} />
          Export
        </motion.button>

      </div>
    </div>
  )
}
