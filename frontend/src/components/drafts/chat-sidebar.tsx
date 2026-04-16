'use client'

import { useRef, useEffect } from 'react'
import { motion } from 'framer-motion'
import { MessageSquare, Loader2 } from 'lucide-react'
import { useChatMessages, useSendChatMessage } from '@/lib/api/draft-hooks'
import { ChatMessage } from './chat-message'
import { ApprovalComment } from '@/components/approval/approval-comment'

interface ChatSidebarProps {
  clientId: string
  draftId: string
  activeSectionId?: string
}

export function ChatSidebar({ clientId, draftId, activeSectionId }: ChatSidebarProps) {
  const { data: messages = [], isLoading } = useChatMessages(clientId, draftId)
  const sendMessage = useSendChatMessage(clientId, draftId)
  const bottomRef = useRef<HTMLDivElement>(null)

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [messages.length])

  function handleSend(content: string, sectionId?: string) {
    sendMessage.mutate({ content, section_id: sectionId ?? activeSectionId })
  }

  const filtered = activeSectionId
    ? messages.filter((m) => !m.section_id || m.section_id === activeSectionId)
    : messages

  return (
    <div
      style={{
        display: 'flex',
        flexDirection: 'column',
        height: '100%',
        borderRadius: 12,
        border: '1px solid var(--border-subtle)',
        background: 'var(--bg-surface)',
        overflow: 'hidden',
      }}
    >
      {/* Header */}
      <div
        style={{
          padding: '12px 16px',
          borderBottom: '1px solid var(--border-subtle)',
          display: 'flex',
          alignItems: 'center',
          gap: 8,
        }}
      >
        <MessageSquare size={14} color="var(--brand-accent)" />
        <span style={{ fontSize: 13, fontWeight: 500, color: 'var(--text-primary)' }}>
          AI assistant
        </span>
        {activeSectionId && (
          <span
            style={{
              fontSize: 11,
              color: 'var(--text-muted)',
              background: 'var(--bg-surface-raised)',
              padding: '1px 8px',
              borderRadius: 999,
              marginLeft: 'auto',
            }}
          >
            Section context
          </span>
        )}
      </div>

      {/* Messages */}
      <div
        style={{
          flex: 1,
          overflowY: 'auto',
          padding: '16px',
          display: 'flex',
          flexDirection: 'column',
          gap: 12,
        }}
      >
        {isLoading ? (
          <div style={{ display: 'flex', justifyContent: 'center', padding: 20 }}>
            <Loader2 size={18} color="var(--text-muted)" style={{ animation: 'spin 1s linear infinite' }} />
          </div>
        ) : filtered.length === 0 ? (
          <div style={{ textAlign: 'center', padding: '32px 0', color: 'var(--text-muted)' }}>
            <MessageSquare size={28} style={{ margin: '0 auto 8px', opacity: 0.3 }} />
            <div style={{ fontSize: 12 }}>Ask the AI to help refine this section</div>
          </div>
        ) : (
          filtered.map((msg) => <ChatMessage key={msg.message_id} message={msg} />)
        )}
        {sendMessage.isPending && (
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            style={{ display: 'flex', gap: 10, alignItems: 'center' }}
          >
            <div style={{ width: 28, height: 28, borderRadius: '50%', background: 'var(--bg-surface-raised)', border: '1px solid var(--border-subtle)', display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
              <Loader2 size={13} color="var(--text-muted)" style={{ animation: 'spin 1s linear infinite' }} />
            </div>
            <div style={{ fontSize: 12, color: 'var(--text-muted)', fontStyle: 'italic' }}>Thinking…</div>
          </motion.div>
        )}
        <div ref={bottomRef} />
      </div>

      {/* Input */}
      <div style={{ padding: '12px 16px', borderTop: '1px solid var(--border-subtle)' }}>
        <ApprovalComment
          onSubmit={handleSend}
          isLoading={sendMessage.isPending}
          sectionId={activeSectionId}
          placeholder="Ask the AI… (⌘↵ to send)"
        />
      </div>
    </div>
  )
}
