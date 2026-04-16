'use client'

import { motion, AnimatePresence } from 'framer-motion'
import { CheckCircle, XCircle, Pause, ExternalLink, Loader2 } from 'lucide-react'
import type { SourceProposal, ProposalAction } from '@/lib/api/source-hooks'

interface ProposalQueueProps {
  proposals: SourceProposal[]
  onAction: (proposalId: string | number, action: ProposalAction) => void
  onPreview: (proposal: SourceProposal) => void
  isActing?: string | number
}

const STATUS_STYLE: Record<string, { color: string; bg: string; label: string }> = {
  pending: { color: '#f59e0b', bg: 'rgba(245,158,11,0.1)', label: 'Pending' },
  approved: { color: '#22c55e', bg: 'rgba(34,197,94,0.1)', label: 'Approved' },
  rejected: { color: '#ef4444', bg: 'rgba(239,68,68,0.1)', label: 'Rejected' },
  paused: { color: 'var(--text-muted)', bg: 'var(--bg-surface-raised)', label: 'Paused' },
}

export function ProposalQueue({ proposals, onAction, onPreview, isActing }: ProposalQueueProps) {
  const pending = proposals.filter((p) => p.status === 'pending')
  const reviewed = proposals.filter((p) => p.status !== 'pending')

  if (proposals.length === 0) {
    return (
      <div style={{ textAlign: 'center', padding: '32px 0', color: 'var(--text-muted)', fontSize: 13 }}>
        No source proposals
      </div>
    )
  }

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: 12 }}>
      {pending.length > 0 && (
        <div>
          <div style={{ fontSize: 11, fontWeight: 600, color: 'var(--text-muted)', textTransform: 'uppercase', letterSpacing: '0.06em', marginBottom: 8 }}>
            Pending review ({pending.length})
          </div>
          <div style={{ display: 'flex', flexDirection: 'column', gap: 8 }}>
            <AnimatePresence>
              {pending.map((proposal) => (
                <ProposalRow
                  key={proposal.proposal_id}
                  proposal={proposal}
                  onAction={onAction}
                  onPreview={onPreview}
                  isActing={isActing === proposal.proposal_id}
                />
              ))}
            </AnimatePresence>
          </div>
        </div>
      )}

      {reviewed.length > 0 && (
        <div>
          <div style={{ fontSize: 11, fontWeight: 600, color: 'var(--text-muted)', textTransform: 'uppercase', letterSpacing: '0.06em', marginBottom: 8 }}>
            Reviewed ({reviewed.length})
          </div>
          <div style={{ display: 'flex', flexDirection: 'column', gap: 6, opacity: 0.7 }}>
            {reviewed.map((proposal) => (
              <ProposalRow
                key={proposal.proposal_id}
                proposal={proposal}
                onAction={onAction}
                onPreview={onPreview}
                isActing={isActing === proposal.proposal_id}
                compact
              />
            ))}
          </div>
        </div>
      )}
    </div>
  )
}

function ProposalRow({
  proposal,
  onAction,
  onPreview,
  isActing,
  compact,
}: {
  proposal: SourceProposal
  onAction: (proposalId: string | number, action: ProposalAction) => void
  onPreview: (proposal: SourceProposal) => void
  isActing: boolean
  compact?: boolean
}) {
  const statusStyle = STATUS_STYLE[proposal.status] ?? STATUS_STYLE.pending
  const isPending = proposal.status === 'pending'

  return (
    <motion.div
      layout
      initial={{ opacity: 0, y: 4 }}
      animate={{ opacity: 1, y: 0 }}
      exit={{ opacity: 0, height: 0 }}
      style={{
        padding: compact ? '8px 12px' : '12px 14px',
        borderRadius: 10,
        border: '1px solid var(--border-subtle)',
        background: 'var(--bg-surface)',
        display: 'flex',
        flexDirection: 'column',
        gap: compact ? 4 : 8,
      }}
    >
      <div style={{ display: 'flex', alignItems: 'flex-start', gap: 10 }}>
        <div style={{ flex: 1, minWidth: 0 }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: 8, marginBottom: 2 }}>
            <span style={{ fontSize: 13, fontWeight: 500, color: 'var(--text-primary)', overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>
              {proposal.source_name}
            </span>
            <span
              style={{
                fontSize: 10,
                fontWeight: 500,
                color: statusStyle.color,
                background: statusStyle.bg,
                padding: '1px 7px',
                borderRadius: 999,
                flexShrink: 0,
              }}
            >
              {statusStyle.label}
            </span>
          </div>
          {!compact && (
            <div style={{ fontSize: 12, color: 'var(--text-secondary)', lineHeight: 1.5 }}>
              {proposal.snippet}
            </div>
          )}
          <div style={{ display: 'flex', gap: 10, marginTop: 2 }}>
            <span style={{ fontSize: 10, color: 'var(--text-muted)' }}>{proposal.topic}</span>
            <span style={{ fontSize: 10, color: 'var(--text-muted)' }}>{proposal.jurisdiction}</span>
            <span style={{ fontSize: 10, color: 'var(--text-muted)' }}>{Math.round(proposal.confidence * 100)}% confidence</span>
          </div>
        </div>

        <div style={{ display: 'flex', gap: 6, alignItems: 'center', flexShrink: 0 }}>
          <motion.button
            aria-label={`Preview impact for ${proposal.source_name}`}
            whileHover={{ scale: 1.05 }}
            onClick={() => onPreview(proposal)}
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
              color: 'var(--text-muted)',
            }}
          >
            <ExternalLink size={12} />
          </motion.button>

          {isPending && (
            <>
              {isActing ? (
                <Loader2 size={16} color="var(--text-muted)" style={{ animation: 'spin 1s linear infinite' }} />
              ) : (
                <>
                  <motion.button
                    aria-label={`Approve ${proposal.source_name}`}
                    whileHover={{ scale: 1.05 }}
                    onClick={() => onAction(proposal.proposal_id, 'approve')}
                    style={{ width: 28, height: 28, borderRadius: 7, border: '1px solid rgba(34,197,94,0.4)', background: 'rgba(34,197,94,0.1)', display: 'flex', alignItems: 'center', justifyContent: 'center', cursor: 'pointer', color: '#22c55e' }}
                  >
                    <CheckCircle size={13} />
                  </motion.button>
                  <motion.button
                    aria-label={`Pause ${proposal.source_name}`}
                    whileHover={{ scale: 1.05 }}
                    onClick={() => onAction(proposal.proposal_id, 'pause')}
                    style={{ width: 28, height: 28, borderRadius: 7, border: '1px solid var(--border-subtle)', background: 'var(--bg-surface-raised)', display: 'flex', alignItems: 'center', justifyContent: 'center', cursor: 'pointer', color: 'var(--text-muted)' }}
                  >
                    <Pause size={12} />
                  </motion.button>
                  <motion.button
                    aria-label={`Reject ${proposal.source_name}`}
                    whileHover={{ scale: 1.05 }}
                    onClick={() => onAction(proposal.proposal_id, 'reject')}
                    style={{ width: 28, height: 28, borderRadius: 7, border: '1px solid rgba(239,68,68,0.3)', background: 'rgba(239,68,68,0.06)', display: 'flex', alignItems: 'center', justifyContent: 'center', cursor: 'pointer', color: '#ef4444' }}
                  >
                    <XCircle size={13} />
                  </motion.button>
                </>
              )}
            </>
          )}
        </div>
      </div>
    </motion.div>
  )
}
