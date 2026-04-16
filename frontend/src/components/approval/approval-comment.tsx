'use client'

import { useState } from 'react'
import { motion } from 'framer-motion'
import { Send, User } from 'lucide-react'

interface ApprovalCommentProps {
  onSubmit: (comment: string, sectionId?: string) => void
  isLoading?: boolean
  sectionId?: string
  placeholder?: string
}

export function ApprovalComment({ onSubmit, isLoading, sectionId, placeholder }: ApprovalCommentProps) {
  const [value, setValue] = useState('')

  function handleSubmit(e: React.FormEvent) {
    e.preventDefault()
    const trimmed = value.trim()
    if (!trimmed) return
    onSubmit(trimmed, sectionId)
    setValue('')
  }

  return (
    <form onSubmit={handleSubmit}>
      <div
        style={{
          display: 'flex',
          gap: 10,
          alignItems: 'flex-end',
          padding: '10px 12px',
          borderRadius: 10,
          border: '1px solid var(--border-subtle)',
          background: 'var(--bg-surface-raised)',
        }}
      >
        <div
          style={{
            width: 28,
            height: 28,
            borderRadius: '50%',
            background: 'var(--bg-surface)',
            border: '1px solid var(--border-subtle)',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            flexShrink: 0,
          }}
        >
          <User size={13} color="var(--text-muted)" />
        </div>

        <textarea
          value={value}
          onChange={(e) => setValue(e.target.value)}
          onKeyDown={(e) => {
            if (e.key === 'Enter' && (e.metaKey || e.ctrlKey)) {
              e.preventDefault()
              const trimmed = value.trim()
              if (trimmed) {
                onSubmit(trimmed, sectionId)
                setValue('')
              }
            }
          }}
          placeholder={placeholder ?? 'Add a comment… (⌘↵ to send)'}
          rows={2}
          style={{
            flex: 1,
            background: 'transparent',
            border: 'none',
            outline: 'none',
            resize: 'none',
            fontSize: 13,
            color: 'var(--text-primary)',
            lineHeight: 1.5,
            padding: 0,
          }}
        />

        <motion.button
          type="submit"
          whileHover={{ scale: 1.05 }}
          whileTap={{ scale: 0.95 }}
          disabled={!value.trim() || isLoading}
          style={{
            width: 32,
            height: 32,
            borderRadius: 8,
            border: 'none',
            background: value.trim() && !isLoading ? 'var(--brand-accent)' : 'var(--bg-surface)',
            color: value.trim() && !isLoading ? '#fff' : 'var(--text-muted)',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            cursor: !value.trim() || isLoading ? 'not-allowed' : 'pointer',
            flexShrink: 0,
            transition: 'background 0.15s, color 0.15s',
          }}
        >
          <Send size={13} />
        </motion.button>
      </div>
    </form>
  )
}
