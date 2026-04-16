'use client'

import Link from 'next/link'
import { motion, AnimatePresence } from 'framer-motion'
import { Skeleton } from '@/components/ui/skeleton'
import { EmptyState } from '@/components/shared/empty-state'
import { useDeleteEvidence, type EvidenceRecord } from '@/lib/api/hooks'
import { useLocale } from '@/lib/i18n/dictionary-context'
import { FileText, Trash2 } from 'lucide-react'

function confidenceColor(confidence: number): string {
  if (confidence >= 0.9) return 'var(--severity-low)'
  if (confidence >= 0.7) return 'var(--severity-medium)'
  return 'var(--severity-critical)'
}

function ConfidenceDot({ confidence }: { confidence: number }) {
  return (
    <span
      className="inline-block w-2 h-2 rounded-full"
      style={{ background: confidenceColor(confidence), flexShrink: 0 }}
      title={`Confidence: ${(confidence * 100).toFixed(0)}%`}
    />
  )
}

function TopicPill({ topic }: { topic: string }) {
  return (
    <span
      className="text-xs px-2 py-0.5 rounded"
      style={{
        background: 'var(--bg-elevated)',
        color: 'var(--brand-accent)',
        border: '1px solid var(--border-color)',
        fontFamily: 'var(--font-mono)',
      }}
    >
      {topic.replace(/_/g, ' ')}
    </span>
  )
}

function SourceBadge({ name }: { name: string }) {
  return (
    <span
      className="text-xs px-2 py-0.5 rounded font-medium"
      style={{
        background: 'color-mix(in srgb, var(--brand-accent) 12%, transparent)',
        color: 'var(--brand-accent)',
        border: '1px solid color-mix(in srgb, var(--brand-accent) 25%, transparent)',
      }}
    >
      {name}
    </span>
  )
}

function RowSkeleton({ i }: { i: number }) {
  return (
    <div
      className="grid grid-cols-[1fr_auto_auto_auto_auto_auto] gap-4 px-5 py-4 items-center"
      style={{ borderTop: i > 0 ? '1px solid var(--border-color)' : undefined }}
    >
      <Skeleton className="h-4 w-3/4" style={{ background: 'var(--bg-elevated)' }} />
      <Skeleton className="h-5 w-20 rounded" style={{ background: 'var(--bg-elevated)' }} />
      <Skeleton className="h-5 w-16 rounded" style={{ background: 'var(--bg-elevated)' }} />
      <Skeleton className="h-3 w-20" style={{ background: 'var(--bg-elevated)' }} />
      <Skeleton className="w-2 h-2 rounded-full" style={{ background: 'var(--bg-elevated)' }} />
      <Skeleton className="h-6 w-12 rounded" style={{ background: 'var(--bg-elevated)' }} />
    </div>
  )
}

function EvidenceRow({ record, clientId }: { record: EvidenceRecord; clientId: string }) {
  const deleteEvidence = useDeleteEvidence(clientId)
  const locale = useLocale()

  return (
    <motion.div
      variants={{ hidden: { opacity: 0, x: -8 }, show: { opacity: 1, x: 0, transition: { duration: 0.18 } } }}
      className="grid grid-cols-[1fr_auto_auto_auto_auto_auto] gap-4 px-5 py-4 items-center"
      style={{ borderTop: '1px solid var(--border-color)' }}
    >
      <Link
        href={`/${locale}/clients/${clientId}/evidence/${record.evidence_id}`}
        className="text-sm font-medium transition-opacity hover:opacity-70 line-clamp-1"
        style={{ color: 'var(--text-primary)', fontFamily: 'var(--font-display)' }}
      >
        {record.document_title || 'Untitled'}
      </Link>
      <SourceBadge name={record.source_name || '—'} />
      <TopicPill topic={record.topic || 'unknown'} />
      <span
        className="text-xs tabular-nums"
        style={{ color: 'var(--text-muted)', fontFamily: 'var(--font-mono)', whiteSpace: 'nowrap' }}
      >
        {record.access_date ? record.access_date.slice(0, 10) : '—'}
      </span>
      <ConfidenceDot confidence={record.confidence ?? 0} />
      <div className="flex items-center gap-2">
        <Link
          href={`/${locale}/clients/${clientId}/evidence/${record.evidence_id}`}
          className="text-xs px-2 py-1 rounded transition-opacity hover:opacity-70"
          style={{
            background: 'var(--bg-elevated)',
            color: 'var(--text-muted)',
            border: '1px solid var(--border-color)',
          }}
        >
          View
        </Link>
        <button
          onClick={() => deleteEvidence.mutate(record.evidence_id)}
          disabled={deleteEvidence.isPending}
          className="p-1 rounded transition-opacity hover:opacity-70"
          style={{ color: 'var(--severity-critical)' }}
          title="Delete evidence"
        >
          <Trash2 className="w-3.5 h-3.5" />
        </button>
      </div>
    </motion.div>
  )
}

interface EvidenceTableProps {
  records: EvidenceRecord[]
  clientId: string
  isLoading: boolean
}

export function EvidenceTable({ records, clientId, isLoading }: EvidenceTableProps) {
  return (
    <div className="rounded-lg overflow-hidden" style={{ border: '1px solid var(--border-color)' }}>
      <div
        className="grid grid-cols-[1fr_auto_auto_auto_auto_auto] gap-4 px-5 py-3 text-xs font-medium"
        style={{
          background: 'var(--bg-elevated)',
          color: 'var(--text-muted)',
          borderBottom: '1px solid var(--border-color)',
        }}
      >
        <span>Document</span>
        <span>Source</span>
        <span>Topic</span>
        <span>Access Date</span>
        <span>Conf.</span>
        <span>Actions</span>
      </div>

      <AnimatePresence mode="wait">
        {isLoading ? (
          <motion.div
            key="skeletons"
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            style={{ background: 'var(--bg-surface)' }}
          >
            {[0, 1, 2, 3, 4].map((i) => <RowSkeleton key={i} i={i} />)}
          </motion.div>
        ) : records.length === 0 ? (
          <motion.div
            key="empty"
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            className="py-10"
            style={{ background: 'var(--bg-surface)' }}
          >
            <EmptyState
              icon={FileText}
              title="No evidence records"
              description="Add a URL above to ingest the first evidence record."
            />
          </motion.div>
        ) : (
          <motion.div
            key="rows"
            initial="hidden"
            animate="show"
            variants={{ hidden: {}, show: { transition: { staggerChildren: 0.04 } } }}
            style={{ background: 'var(--bg-surface)' }}
          >
            {records.map((record) => (
              <EvidenceRow key={record.evidence_id} record={record} clientId={clientId} />
            ))}
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  )
}
