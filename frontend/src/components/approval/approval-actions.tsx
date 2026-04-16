'use client'

import { useState } from 'react'
import { motion, AnimatePresence } from 'framer-motion'
import { CheckCircle, XCircle, RotateCcw, MessageSquare } from 'lucide-react'
import type { ApprovalActionPayload } from '@/lib/api/draft-hooks'

interface ApprovalActionsProps {
  sectionId?: string
  onAction: (payload: ApprovalActionPayload) => void
  isLoading?: boolean
  disabled?: boolean
}

export function ApprovalActions({ sectionId, onAction, isLoading, disabled }: ApprovalActionsProps) {
  const [showNoteInput, setShowNoteInput] = useState(false)
  const [pendingAction, setPendingAction] = useState<'reject' | 'request_revision' | null>(null)
  const [note, setNote] = useState('')

  function handleApprove() {
    onAction({ action: 'approve', section_id: sectionId })
    setShowNoteInput(false)
    setPendingAction(null)
    setNote('')
  }

  function handleOpenNote(action: 'reject' | 'request_revision') {
    setPendingAction(action)
    setShowNoteInput(true)
  }

  function handleSubmitNote() {
    if (!pendingAction) return
    onAction({ action: pendingAction, section_id: sectionId, note: note.trim() || undefined })
    setShowNoteInput(false)
    setPendingAction(null)
    setNote('')
  }

  function handleCancel() {
    setShowNoteInput(false)
    setPendingAction(null)
    setNote('')
  }

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: 8 }}>
      <div style={{ display: 'flex', gap: 8, alignItems: 'center' }}>
        <motion.button
          whileHover={{ scale: 1.03 }}
          whileTap={{ scale: 0.97 }}
          disabled={disabled || isLoading}
          onClick={handleApprove}
          style={{
            display: 'flex',
            alignItems: 'center',
            gap: 6,
            padding: '6px 14px',
            borderRadius: 8,
            border: '1px solid rgba(34,197,94,0.4)',
            background: 'rgba(34,197,94,0.1)',
            color: '#22c55e',
            fontSize: 13,
            fontWeight: 500,
            cursor: disabled || isLoading ? 'not-allowed' : 'pointer',
            opacity: disabled || isLoading ? 0.5 : 1,
          }}
        >
          <CheckCircle size={14} />
          Approve
        </motion.button>

        <motion.button
          whileHover={{ scale: 1.03 }}
          whileTap={{ scale: 0.97 }}
          disabled={disabled || isLoading}
          onClick={() => handleOpenNote('request_revision')}
          style={{
            display: 'flex',
            alignItems: 'center',
            gap: 6,
            padding: '6px 14px',
            borderRadius: 8,
            border: '1px solid rgba(249,115,22,0.4)',
            background: 'rgba(249,115,22,0.1)',
            color: '#f97316',
            fontSize: 13,
            fontWeight: 500,
            cursor: disabled || isLoading ? 'not-allowed' : 'pointer',
            opacity: disabled || isLoading ? 0.5 : 1,
          }}
        >
          <RotateCcw size={14} />
          Request revision
        </motion.button>

        <motion.button
          whileHover={{ scale: 1.03 }}
          whileTap={{ scale: 0.97 }}
          disabled={disabled || isLoading}
          onClick={() => handleOpenNote('reject')}
          style={{
            display: 'flex',
            alignItems: 'center',
            gap: 6,
            padding: '6px 14px',
            borderRadius: 8,
            border: '1px solid rgba(239,68,68,0.4)',
            background: 'rgba(239,68,68,0.1)',
            color: '#ef4444',
            fontSize: 13,
            fontWeight: 500,
            cursor: disabled || isLoading ? 'not-allowed' : 'pointer',
            opacity: disabled || isLoading ? 0.5 : 1,
          }}
        >
          <XCircle size={14} />
          Reject
        </motion.button>
      </div>

      <AnimatePresence>
        {showNoteInput && (
          <motion.div
            initial={{ opacity: 0, height: 0 }}
            animate={{ opacity: 1, height: 'auto' }}
            exit={{ opacity: 0, height: 0 }}
            style={{ overflow: 'hidden' }}
          >
            <div
              style={{
                display: 'flex',
                flexDirection: 'column',
                gap: 8,
                padding: 12,
                borderRadius: 8,
                background: 'var(--bg-surface-raised)',
                border: '1px solid var(--border-subtle)',
              }}
            >
              <div style={{ display: 'flex', alignItems: 'center', gap: 6, color: 'var(--text-secondary)', fontSize: 12 }}>
                <MessageSquare size={12} />
                {pendingAction === 'reject' ? 'Rejection reason' : 'Revision instructions'} (optional)
              </div>
              <textarea
                value={note}
                onChange={(e) => setNote(e.target.value)}
                placeholder="Add a note..."
                rows={3}
                style={{
                  width: '100%',
                  padding: '8px 10px',
                  borderRadius: 6,
                  border: '1px solid var(--border-subtle)',
                  background: 'var(--bg-surface)',
                  color: 'var(--text-primary)',
                  fontSize: 13,
                  resize: 'vertical',
                  boxSizing: 'border-box',
                }}
              />
              <div style={{ display: 'flex', gap: 8, justifyContent: 'flex-end' }}>
                <button
                  onClick={handleCancel}
                  style={{
                    padding: '5px 12px',
                    borderRadius: 6,
                    border: '1px solid var(--border-subtle)',
                    background: 'transparent',
                    color: 'var(--text-secondary)',
                    fontSize: 12,
                    cursor: 'pointer',
                  }}
                >
                  Cancel
                </button>
                <button
                  onClick={handleSubmitNote}
                  disabled={isLoading}
                  style={{
                    padding: '5px 12px',
                    borderRadius: 6,
                    border: 'none',
                    background: pendingAction === 'reject' ? '#ef4444' : '#f97316',
                    color: '#fff',
                    fontSize: 12,
                    fontWeight: 500,
                    cursor: isLoading ? 'not-allowed' : 'pointer',
                    opacity: isLoading ? 0.7 : 1,
                  }}
                >
                  {pendingAction === 'reject' ? 'Confirm reject' : 'Send revision request'}
                </button>
              </div>
            </div>
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  )
}
