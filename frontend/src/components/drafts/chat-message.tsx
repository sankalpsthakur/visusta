'use client'

import { motion } from 'framer-motion'
import { User, Bot } from 'lucide-react'
import type { ChatMessage as ChatMessageType } from '@/lib/api/draft-hooks'

interface ChatMessageProps {
  message: ChatMessageType
}

function formatTime(ts: string): string {
  try {
    return new Date(ts).toLocaleTimeString(undefined, { hour: '2-digit', minute: '2-digit' })
  } catch {
    return ts
  }
}

export function ChatMessage({ message }: ChatMessageProps) {
  const isUser = message.role === 'user'

  return (
    <motion.div
      initial={{ opacity: 0, y: 6 }}
      animate={{ opacity: 1, y: 0 }}
      style={{
        display: 'flex',
        gap: 10,
        flexDirection: isUser ? 'row-reverse' : 'row',
        alignItems: 'flex-start',
      }}
    >
      {/* Avatar */}
      <div
        style={{
          width: 28,
          height: 28,
          borderRadius: '50%',
          background: isUser ? 'rgba(var(--brand-accent-rgb),0.15)' : 'var(--bg-surface-raised)',
          border: '1px solid var(--border-subtle)',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center',
          flexShrink: 0,
        }}
      >
        {isUser ? (
          <User size={13} color="var(--brand-accent)" />
        ) : (
          <Bot size={13} color="var(--text-secondary)" />
        )}
      </div>

      {/* Bubble */}
      <div style={{ maxWidth: '75%', display: 'flex', flexDirection: 'column', gap: 4, alignItems: isUser ? 'flex-end' : 'flex-start' }}>
        <div
          style={{
            padding: '9px 13px',
            borderRadius: isUser ? '12px 4px 12px 12px' : '4px 12px 12px 12px',
            background: isUser ? 'rgba(var(--brand-accent-rgb),0.12)' : 'var(--bg-surface-raised)',
            border: '1px solid var(--border-subtle)',
            fontSize: 13,
            color: 'var(--text-primary)',
            lineHeight: 1.6,
            whiteSpace: 'pre-wrap',
          }}
        >
          {message.content}
        </div>

        <div style={{ fontSize: 10, color: 'var(--text-muted)' }}>
          {formatTime(message.created_at)}
          {message.section_id && (
            <span style={{ marginLeft: 6, color: 'var(--brand-accent)' }}>
              · {message.section_id}
            </span>
          )}
        </div>
      </div>
    </motion.div>
  )
}
