'use client'

import { motion } from 'framer-motion'
import { TrendingUp, BookOpen, Loader2, X } from 'lucide-react'
import { useProposalImpact } from '@/lib/api/source-hooks'
import type { SourceProposal } from '@/lib/api/source-hooks'

interface ImpactPreviewProps {
  proposal: SourceProposal
  clientId: string
  onClose: () => void
}

export function ImpactPreview({ proposal, clientId, onClose }: ImpactPreviewProps) {
  const { data: impact, isLoading, error } = useProposalImpact(clientId, proposal.proposal_id)

  return (
    <motion.div
      initial={{ opacity: 0, scale: 0.95 }}
      animate={{ opacity: 1, scale: 1 }}
      exit={{ opacity: 0, scale: 0.95 }}
      style={{
        position: 'fixed',
        top: '50%',
        left: '50%',
        transform: 'translate(-50%, -50%)',
        background: 'var(--bg-surface)',
        borderRadius: 16,
        border: '1px solid var(--border-subtle)',
        boxShadow: '0 24px 60px rgba(0,0,0,0.2)',
        zIndex: 1000,
        width: 480,
        maxHeight: '80vh',
        overflow: 'hidden',
        display: 'flex',
        flexDirection: 'column',
      }}
    >
      {/* Header */}
      <div style={{ padding: '20px 24px', borderBottom: '1px solid var(--border-subtle)', display: 'flex', alignItems: 'center', gap: 10 }}>
        <TrendingUp size={16} color="var(--brand-accent)" />
        <div style={{ flex: 1 }}>
          <div style={{ fontSize: 14, fontWeight: 600, color: 'var(--text-primary)' }}>Impact preview</div>
          <div style={{ fontSize: 12, color: 'var(--text-muted)' }}>{proposal.source_name}</div>
        </div>
        <button aria-label="Close impact preview" onClick={onClose} style={{ background: 'none', border: 'none', cursor: 'pointer', color: 'var(--text-muted)' }}>
          <X size={16} />
        </button>
      </div>

      {/* Body */}
      <div style={{ overflowY: 'auto', padding: '20px 24px', flex: 1 }}>
        {isLoading && (
          <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'center', padding: '32px 0' }}>
            <Loader2 size={20} color="var(--text-muted)" style={{ animation: 'spin 1s linear infinite' }} />
          </div>
        )}

        {error && (
          <div style={{ color: '#ef4444', fontSize: 13 }}>
            {error instanceof Error ? error.message : 'Failed to load impact data'}
          </div>
        )}

        {impact && (
          <div style={{ display: 'flex', flexDirection: 'column', gap: 20 }}>
            {/* Stats */}
            <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 12 }}>
              <div
                style={{
                  padding: '16px',
                  borderRadius: 10,
                  background: 'var(--bg-surface-raised)',
                  border: '1px solid var(--border-subtle)',
                }}
              >
                <div style={{ fontSize: 24, fontWeight: 700, color: 'var(--brand-accent)', marginBottom: 4 }}>
                  {impact.estimated_matches.toLocaleString()}
                </div>
                <div style={{ fontSize: 12, color: 'var(--text-muted)' }}>Estimated matches</div>
              </div>
              <div
                style={{
                  padding: '16px',
                  borderRadius: 10,
                  background: 'var(--bg-surface-raised)',
                  border: '1px solid var(--border-subtle)',
                }}
              >
                <div style={{ fontSize: 24, fontWeight: 700, color: impact.coverage_delta > 0 ? '#22c55e' : '#ef4444', marginBottom: 4 }}>
                  {impact.coverage_delta > 0 ? '+' : ''}{(impact.coverage_delta * 100).toFixed(1)}%
                </div>
                <div style={{ fontSize: 12, color: 'var(--text-muted)' }}>Coverage change</div>
              </div>
            </div>

            {/* Sample regulations */}
            {impact.sample_regulations.length > 0 && (
              <div>
                <div style={{ display: 'flex', alignItems: 'center', gap: 6, marginBottom: 8 }}>
                  <BookOpen size={13} color="var(--text-muted)" />
                  <span style={{ fontSize: 12, fontWeight: 500, color: 'var(--text-secondary)' }}>
                    Sample matches ({impact.sample_regulations.length})
                  </span>
                </div>
                <div style={{ display: 'flex', flexDirection: 'column', gap: 6 }}>
                  {impact.sample_regulations.map((reg) => (
                    <div
                      key={reg.regulation_id}
                      style={{
                        padding: '10px 12px',
                        borderRadius: 8,
                        border: '1px solid var(--border-subtle)',
                        background: 'var(--bg-surface-raised)',
                      }}
                    >
                      <div style={{ fontSize: 13, fontWeight: 500, color: 'var(--text-primary)', marginBottom: 2 }}>
                        {reg.title}
                      </div>
                      <div style={{ fontSize: 11, color: 'var(--text-muted)' }}>
                        {reg.regulation_id} · {reg.topic}
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            )}
          </div>
        )}
      </div>
    </motion.div>
  )
}
