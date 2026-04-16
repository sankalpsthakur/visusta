'use client'

import { use, useState } from 'react'
import { AnimatePresence, motion } from 'framer-motion'
import { Plus, Radio, Tag } from 'lucide-react'
import { useSources, useUpdateSources } from '@/lib/api/hooks'
import {
  useKeywordBundles,
  useKeywordRules,
  useCreateKeywordRule,
  useUpdateKeywordRule,
  useDeleteKeywordRule,
  useSourceProposals,
  useActOnProposal,
  useSuggestSourceProposals,
} from '@/lib/api/source-hooks'
import { SourceTable } from '@/components/sources/source-table'
import { SourceForm } from '@/components/sources/source-form'
import { KeywordBundles } from '@/components/sources/keyword-bundles'
import { KeywordEditor } from '@/components/sources/keyword-editor'
import { ProposalQueue } from '@/components/sources/proposal-queue'
import { ImpactPreview } from '@/components/sources/impact-preview'
import { PageTransition } from '@/components/shared/page-transition'
import type { SourceConfig } from '@/lib/api/hooks'
import type { SourceProposal } from '@/lib/api/source-hooks'

type Tab = 'sources' | 'keywords' | 'proposals'

interface SourcesPageProps {
  params: Promise<{ clientId: string; lang: string }>
}

export default function SourcesPage({ params }: SourcesPageProps) {
  const { clientId } = use(params)

  const { data: sources = [], isLoading: sourcesLoading } = useSources(clientId)
  const updateSources = useUpdateSources(clientId)

  const { data: bundles = [] } = useKeywordBundles(clientId)
  const [selectedBundle, setSelectedBundle] = useState<string | null>(null)
  const { data: rules = [] } = useKeywordRules(clientId, selectedBundle ?? undefined)
  const createRule = useCreateKeywordRule(clientId)
  const updateRule = useUpdateKeywordRule(clientId)
  const deleteRule = useDeleteKeywordRule(clientId)

  const { data: proposals = [] } = useSourceProposals(clientId)
  const actOnProposal = useActOnProposal(clientId)
  const suggestProposals = useSuggestSourceProposals(clientId)
  const [actingProposalId, setActingProposalId] = useState<string | number | null>(null)
  const [previewProposal, setPreviewProposal] = useState<SourceProposal | null>(null)

  const [tab, setTab] = useState<Tab>('sources')
  const [editingSource, setEditingSource] = useState<SourceConfig | null>(null)
  const [showAddSource, setShowAddSource] = useState(false)
  const [deletingSourceId, setDeletingSourceId] = useState<string | null>(null)

  async function handleSaveSource(data: Omit<SourceConfig, 'id'> & { id?: string }) {
    const isExistingSource = Boolean(data.id && sources.some((source) => source.id === data.id))

    if (isExistingSource) {
      const updated = sources.map((s) => (s.id === data.id ? { ...s, ...data } as SourceConfig : s))
      await updateSources.mutateAsync(updated)
    } else {
      const newSource: SourceConfig = {
        id: data.id ?? `src_${Date.now()}`,
        display_name: data.display_name,
        url: data.url,
        frequency: data.frequency,
        source_type: data.source_type,
      }
      await updateSources.mutateAsync([...sources, newSource])
    }
    setEditingSource(null)
    setShowAddSource(false)
  }

  async function handleDeleteSource(sourceId: string) {
    setDeletingSourceId(sourceId)
    try {
      await updateSources.mutateAsync(sources.filter((s) => s.id !== sourceId))
    } finally {
      setDeletingSourceId(null)
    }
  }

  async function handleProposalAction(proposalId: string | number, action: import('@/lib/api/source-hooks').ProposalAction) {
    setActingProposalId(proposalId)
    try {
      await actOnProposal.mutateAsync({ proposalId, action })
    } finally {
      setActingProposalId(null)
    }
  }

  const TABS: { id: Tab; label: string; icon: React.ReactNode; count?: number }[] = [
    { id: 'sources', label: 'Sources', icon: <Radio size={13} />, count: sources.length },
    { id: 'keywords', label: 'Keywords', icon: <Tag size={13} />, count: bundles.length },
    { id: 'proposals', label: 'Proposals', icon: <Plus size={13} />, count: proposals.filter((p) => p.status === 'pending').length || undefined },
  ]

  return (
    <PageTransition className="p-8">
      <div style={{ maxWidth: 1000 }}>
        {/* Header */}
        <div style={{ marginBottom: 24 }}>
          <h1 style={{ fontSize: 22, fontWeight: 600, letterSpacing: '-0.02em', color: 'var(--text-primary)', marginBottom: 4 }}>
            Sources & Keywords
          </h1>
          <p style={{ fontSize: 13, color: 'var(--text-muted)' }}>
            Configure regulatory data sources and keyword matching rules.
          </p>
        </div>

        {/* Tabs */}
        <div style={{ display: 'flex', gap: 2, marginBottom: 20, borderBottom: '1px solid var(--border-subtle)' }}>
          {TABS.map((t) => (
            <motion.button
              key={t.id}
              whileHover={{ scale: 1.01 }}
              onClick={() => setTab(t.id)}
              style={{
                display: 'flex',
                alignItems: 'center',
                gap: 6,
                padding: '9px 14px',
                borderRadius: '8px 8px 0 0',
                border: 'none',
                borderBottom: tab === t.id ? '2px solid var(--brand-accent)' : '2px solid transparent',
                background: 'transparent',
                color: tab === t.id ? 'var(--brand-accent)' : 'var(--text-secondary)',
                fontSize: 13,
                fontWeight: tab === t.id ? 500 : 400,
                cursor: 'pointer',
              }}
            >
              {t.icon}
              {t.label}
              {t.count !== undefined && (
                <span
                  style={{
                    fontSize: 10,
                    fontWeight: 600,
                    background: tab === t.id ? 'rgba(var(--brand-accent-rgb),0.15)' : 'var(--bg-surface-raised)',
                    color: tab === t.id ? 'var(--brand-accent)' : 'var(--text-muted)',
                    padding: '1px 6px',
                    borderRadius: 999,
                  }}
                >
                  {t.count}
                </span>
              )}
            </motion.button>
          ))}
        </div>

        {/* Tab content */}
        <AnimatePresence mode="wait">
          {tab === 'sources' && (
            <motion.div
              key="sources"
              initial={{ opacity: 0, y: 4 }}
              animate={{ opacity: 1, y: 0 }}
              exit={{ opacity: 0 }}
              style={{ display: 'flex', flexDirection: 'column', gap: 16 }}
            >
              <div style={{ display: 'flex', justifyContent: 'flex-end' }}>
                <motion.button
                  whileHover={{ scale: 1.02 }}
                  whileTap={{ scale: 0.98 }}
                  onClick={() => setShowAddSource(true)}
                  style={{
                    display: 'flex',
                    alignItems: 'center',
                    gap: 6,
                    padding: '8px 16px',
                    borderRadius: 9,
                    border: 'none',
                    background: 'var(--brand-accent)',
                    color: '#fff',
                    fontSize: 13,
                    fontWeight: 500,
                    cursor: 'pointer',
                  }}
                >
                  <Plus size={14} />
                  Add source
                </motion.button>
              </div>

              <AnimatePresence>
                {(showAddSource || editingSource) && (
                  <SourceForm
                    key={editingSource?.id ?? 'new'}
                    initial={editingSource ?? undefined}
                    onSave={handleSaveSource}
                    onCancel={() => { setShowAddSource(false); setEditingSource(null) }}
                    isSaving={updateSources.isPending}
                  />
                )}
              </AnimatePresence>

              {sourcesLoading ? (
                <div style={{ display: 'flex', flexDirection: 'column', gap: 8 }}>
                  {Array.from({ length: 4 }).map((_, i) => (
                    <div key={i} style={{ height: 52, borderRadius: 8, background: 'var(--bg-surface-raised)', animation: 'pulse 1.5s ease-in-out infinite' }} />
                  ))}
                </div>
              ) : (
                <SourceTable
                  sources={sources}
                  onEdit={(source) => setEditingSource(source)}
                  onDelete={handleDeleteSource}
                  isDeleting={deletingSourceId ?? undefined}
                />
              )}
            </motion.div>
          )}

          {tab === 'keywords' && (
            <motion.div
              key="keywords"
              initial={{ opacity: 0, y: 4 }}
              animate={{ opacity: 1, y: 0 }}
              exit={{ opacity: 0 }}
              style={{ display: 'grid', gridTemplateColumns: '220px 1fr', gap: 20 }}
            >
              <KeywordBundles
                bundles={bundles}
                selectedBundle={selectedBundle}
                onSelect={setSelectedBundle}
                onAdd={() => {
                  const name = prompt('Bundle name:')
                  if (name) setSelectedBundle(name.trim().toLowerCase().replace(/\s+/g, '_'))
                }}
              />

              <div
                style={{
                  padding: '20px 24px',
                  borderRadius: 12,
                  border: '1px solid var(--border-subtle)',
                  background: 'var(--bg-surface)',
                  minHeight: 300,
                }}
              >
                {selectedBundle ? (
                  <KeywordEditor
                    bundleName={selectedBundle}
                    rules={rules.filter((r) => r.bundle_name === selectedBundle)}
                    onCreateRule={(payload) => createRule.mutate(payload)}
                    onToggleRule={(ruleId, enabled) => updateRule.mutate({ ruleId, payload: { enabled } })}
                    onDeleteRule={(ruleId) => deleteRule.mutate(ruleId)}
                    isSaving={createRule.isPending || updateRule.isPending}
                  />
                ) : (
                  <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'center', height: 200, color: 'var(--text-muted)', fontSize: 13 }}>
                    Select a bundle to view rules
                  </div>
                )}
              </div>
            </motion.div>
          )}

          {tab === 'proposals' && (
            <motion.div
              key="proposals"
              initial={{ opacity: 0, y: 4 }}
              animate={{ opacity: 1, y: 0 }}
              exit={{ opacity: 0 }}
            >
              <div style={{ display: 'flex', justifyContent: 'flex-end', marginBottom: 12 }}>
                <motion.button
                  whileHover={{ scale: 1.02 }}
                  whileTap={{ scale: 0.98 }}
                  onClick={() => suggestProposals.mutate()}
                  disabled={suggestProposals.isPending}
                  style={{
                    display: 'flex',
                    alignItems: 'center',
                    gap: 6,
                    padding: '8px 16px',
                    borderRadius: 9,
                    border: '1px solid var(--border-subtle)',
                    background: 'var(--bg-surface)',
                    color: 'var(--text-secondary)',
                    fontSize: 13,
                    fontWeight: 500,
                    cursor: suggestProposals.isPending ? 'not-allowed' : 'pointer',
                    opacity: suggestProposals.isPending ? 0.7 : 1,
                    marginLeft: 'auto',
                  }}
                >
                  <Plus size={14} />
                  {suggestProposals.isPending ? 'Scouting…' : 'Scout sources'}
                </motion.button>
              </div>
              <ProposalQueue
                proposals={proposals}
                onAction={handleProposalAction}
                onPreview={setPreviewProposal}
                isActing={actingProposalId ?? undefined}
              />
            </motion.div>
          )}
        </AnimatePresence>
      </div>

      {/* Impact preview overlay */}
      <AnimatePresence>
        {previewProposal && (
          <>
            <motion.div
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              exit={{ opacity: 0 }}
              onClick={() => setPreviewProposal(null)}
              style={{ position: 'fixed', inset: 0, background: 'rgba(0,0,0,0.4)', zIndex: 999 }}
            />
            <ImpactPreview
              proposal={previewProposal}
              clientId={clientId}
              onClose={() => setPreviewProposal(null)}
            />
          </>
        )}
      </AnimatePresence>
    </PageTransition>
  )
}
