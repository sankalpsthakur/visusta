'use client'

import { use, useState } from 'react'
import { motion, AnimatePresence } from 'framer-motion'
import { Plus, Search, FileText } from 'lucide-react'
import { useDrafts, useCreateDraft } from '@/lib/api/draft-hooks'
import { useTemplates } from '@/lib/api/template-hooks'
import { useClientLocaleSettings } from '@/lib/api/hooks'
import { DraftCard } from '@/components/drafts/draft-card'
import { StatusBadge } from '@/components/approval/status-badge'
import { PageTransition } from '@/components/shared/page-transition'
import type { DraftListItem, DraftStatus, CreateDraftPayload } from '@/lib/api/draft-hooks'
import { LOCALE_LABELS, SUPPORTED_LOCALES } from '@/lib/i18n/locales'
import { useLocalePath } from '@/lib/i18n/navigation'
import { useRouter } from 'next/navigation'

const STATUS_FILTERS: DraftStatus[] = ['composing', 'review', 'revision', 'approval', 'approved', 'exported', 'archived']

interface DraftsPageProps {
  params: Promise<{ clientId: string; lang: string }>
}

export default function DraftsPage({ params }: DraftsPageProps) {
  const { clientId } = use(params)
  const localePath = useLocalePath()
  const router = useRouter()

  const { data: drafts = [], isLoading, error } = useDrafts(clientId)
  const { data: templates = [] } = useTemplates()
  const { data: localeSettings } = useClientLocaleSettings(clientId)
  const createDraft = useCreateDraft(clientId)

  const [search, setSearch] = useState('')
  const [statusFilter, setStatusFilter] = useState<DraftStatus | 'all'>('all')
  const [showCreateModal, setShowCreateModal] = useState(false)
  const [newDraft, setNewDraft] = useState<Partial<CreateDraftPayload>>({ locale: 'en', period: new Date().toISOString().slice(0, 7) })

  const filtered = drafts.filter((d) => {
    const matchSearch = !search || d.title.toLowerCase().includes(search.toLowerCase()) || d.period.includes(search)
    const matchStatus = statusFilter === 'all' || d.status === statusFilter
    return matchSearch && matchStatus
  })

  function handleDraftClick(draft: DraftListItem) {
    router.push(localePath(`/clients/${clientId}/drafts/${draft.draft_id}`))
  }

  async function handleCreate() {
    if (!newDraft.template_id || !newDraft.title || !newDraft.period || !newDraft.locale) return
    const draft = await createDraft.mutateAsync(newDraft as CreateDraftPayload)
    setShowCreateModal(false)
    router.push(localePath(`/clients/${clientId}/drafts/${draft.draft_id}`))
  }

  return (
    <PageTransition className="p-8">
      <div style={{ maxWidth: 1000 }}>
        {/* Header */}
        <div style={{ display: 'flex', alignItems: 'flex-start', justifyContent: 'space-between', marginBottom: 24 }}>
          <div>
            <h1 style={{ fontSize: 22, fontWeight: 600, letterSpacing: '-0.02em', color: 'var(--text-primary)', marginBottom: 4 }}>
              Drafts
            </h1>
            <p style={{ fontSize: 13, color: 'var(--text-muted)' }}>
              Compose and manage regulatory intelligence reports.
            </p>
          </div>
          <motion.button
            whileHover={{ scale: 1.02 }}
            whileTap={{ scale: 0.98 }}
            onClick={() => {
              setNewDraft({ locale: localeSettings?.primary_locale ?? 'en', period: new Date().toISOString().slice(0, 7) })
              setShowCreateModal(true)
            }}
            style={{
              display: 'flex',
              alignItems: 'center',
              gap: 7,
              padding: '9px 18px',
              borderRadius: 10,
              border: 'none',
              background: 'var(--brand-accent)',
              color: '#fff',
              fontSize: 13,
              fontWeight: 500,
              cursor: 'pointer',
            }}
          >
            <Plus size={15} />
            New draft
          </motion.button>
        </div>

        {/* Filters */}
        <div style={{ display: 'flex', gap: 10, marginBottom: 20, flexWrap: 'wrap', alignItems: 'center' }}>
          <div
            style={{
              display: 'flex',
              alignItems: 'center',
              gap: 8,
              padding: '8px 12px',
              borderRadius: 10,
              border: '1px solid var(--border-subtle)',
              background: 'var(--bg-surface-raised)',
              flex: 1,
              maxWidth: 280,
            }}
          >
            <Search size={14} color="var(--text-muted)" />
            <input
              value={search}
              onChange={(e) => setSearch(e.target.value)}
              placeholder="Search drafts…"
              style={{ border: 'none', background: 'transparent', outline: 'none', fontSize: 13, color: 'var(--text-primary)', flex: 1 }}
            />
          </div>

          <motion.button
            whileTap={{ scale: 0.97 }}
            onClick={() => setStatusFilter('all')}
            style={{
              padding: '7px 12px',
              borderRadius: 8,
              border: statusFilter === 'all' ? '1px solid rgba(var(--brand-accent-rgb),0.4)' : '1px solid var(--border-subtle)',
              background: statusFilter === 'all' ? 'rgba(var(--brand-accent-rgb),0.1)' : 'var(--bg-surface-raised)',
              color: statusFilter === 'all' ? 'var(--brand-accent)' : 'var(--text-secondary)',
              fontSize: 12,
              cursor: 'pointer',
              fontWeight: statusFilter === 'all' ? 500 : 400,
            }}
          >
            All
          </motion.button>

          {STATUS_FILTERS.map((status) => (
            <motion.button
              key={status}
              whileTap={{ scale: 0.97 }}
              onClick={() => setStatusFilter(status === statusFilter ? 'all' : status)}
              style={{
                padding: '5px 10px',
                borderRadius: 8,
                border: 'none',
                background: 'transparent',
                cursor: 'pointer',
              }}
            >
              <StatusBadge status={status} size="sm" />
            </motion.button>
          ))}
        </div>

        {/* Grid */}
        {isLoading && (
          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(280px, 1fr))', gap: 14 }}>
            {Array.from({ length: 6 }).map((_, i) => (
              <div key={i} style={{ height: 140, borderRadius: 12, background: 'var(--bg-surface-raised)', border: '1px solid var(--border-subtle)', animation: 'pulse 1.5s ease-in-out infinite' }} />
            ))}
          </div>
        )}

        {error && (
          <div style={{ padding: '16px 20px', borderRadius: 10, border: '1px solid rgba(239,68,68,0.3)', background: 'rgba(239,68,68,0.06)', color: '#b91c1c', fontSize: 13 }}>
            Failed to load drafts: {error instanceof Error ? error.message : 'Unknown error'}
          </div>
        )}

        {!isLoading && !error && (
          <AnimatePresence mode="wait">
            {filtered.length === 0 ? (
              <motion.div
                key="empty"
                initial={{ opacity: 0 }}
                animate={{ opacity: 1 }}
                exit={{ opacity: 0 }}
                style={{ textAlign: 'center', padding: '60px 0', color: 'var(--text-muted)' }}
              >
                <FileText size={36} style={{ margin: '0 auto 12px', opacity: 0.4 }} />
                <div style={{ fontSize: 14, fontWeight: 500, marginBottom: 4 }}>
                  {search || statusFilter !== 'all' ? 'No drafts match your filter' : 'No drafts yet'}
                </div>
                <div style={{ fontSize: 12 }}>Create a draft to start composing a report</div>
              </motion.div>
            ) : (
              <motion.div
                key="grid"
                initial={{ opacity: 0 }}
                animate={{ opacity: 1 }}
                exit={{ opacity: 0 }}
                style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(280px, 1fr))', gap: 14 }}
              >
                {filtered.map((draft) => (
                  <DraftCard key={draft.draft_id} draft={draft} onClick={handleDraftClick} />
                ))}
              </motion.div>
            )}
          </AnimatePresence>
        )}
      </div>

      {/* Create draft modal */}
      <AnimatePresence>
        {showCreateModal && (
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            style={{
              position: 'fixed',
              inset: 0,
              background: 'rgba(0,0,0,0.5)',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              zIndex: 1000,
            }}
            onClick={(e) => e.target === e.currentTarget && setShowCreateModal(false)}
          >
            <motion.div
              initial={{ opacity: 0, scale: 0.95 }}
              animate={{ opacity: 1, scale: 1 }}
              exit={{ opacity: 0, scale: 0.95 }}
              style={{
                background: 'var(--bg-surface)',
                borderRadius: 16,
                border: '1px solid var(--border-subtle)',
                padding: '28px 32px',
                width: 480,
                boxShadow: '0 24px 60px rgba(0,0,0,0.2)',
              }}
            >
              <h2 style={{ fontSize: 17, fontWeight: 600, color: 'var(--text-primary)', marginBottom: 20 }}>
                New draft
              </h2>

              <div style={{ display: 'flex', flexDirection: 'column', gap: 14 }}>
                <div>
                  <label style={{ fontSize: 12, fontWeight: 500, color: 'var(--text-muted)', display: 'block', marginBottom: 5 }}>Title</label>
                  <input
                    aria-label="Draft title"
                    value={newDraft.title ?? ''}
                    onChange={(e) => setNewDraft((p) => ({ ...p, title: e.target.value }))}
                    placeholder="e.g. February 2026 Monthly Report"
                    style={{ width: '100%', padding: '8px 12px', borderRadius: 8, border: '1px solid var(--border-subtle)', background: 'var(--bg-surface-raised)', color: 'var(--text-primary)', fontSize: 13, boxSizing: 'border-box' }}
                  />
                </div>

                <div>
                  <label style={{ fontSize: 12, fontWeight: 500, color: 'var(--text-muted)', display: 'block', marginBottom: 5 }}>Template</label>
                  {templates.length === 0 ? (
                    <div
                      role="note"
                      aria-label="No templates available"
                      style={{
                        width: '100%',
                        padding: '8px 12px',
                        borderRadius: 8,
                        border: '1px solid var(--border-subtle)',
                        background: 'var(--bg-surface-raised)',
                        color: 'var(--text-secondary)',
                        fontSize: 13,
                        boxSizing: 'border-box',
                        display: 'flex',
                        alignItems: 'center',
                        justifyContent: 'space-between',
                        gap: 10,
                      }}
                    >
                      <span>No templates available yet.</span>
                      <a
                        href={localePath('/templates')}
                        style={{ color: 'var(--brand-accent)', fontSize: 13, fontWeight: 500, textDecoration: 'none' }}
                      >
                        Create one →
                      </a>
                    </div>
                  ) : (
                    <select
                      aria-label="Draft template"
                      value={newDraft.template_id ?? ''}
                      onChange={(e) => setNewDraft((p) => ({ ...p, template_id: e.target.value }))}
                      style={{ width: '100%', padding: '8px 12px', borderRadius: 8, border: '1px solid var(--border-subtle)', background: 'var(--bg-surface-raised)', color: 'var(--text-primary)', fontSize: 13, boxSizing: 'border-box' }}
                    >
                      <option value="">Select template…</option>
                      {templates.map((t) => (
                        <option key={t.template_id} value={t.template_id}>{t.display_name}</option>
                      ))}
                    </select>
                  )}
                </div>

                <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 10 }}>
                  <div>
                    <label style={{ fontSize: 12, fontWeight: 500, color: 'var(--text-muted)', display: 'block', marginBottom: 5 }}>Period</label>
                    <input
                      aria-label="Draft period"
                      type="text"
                      placeholder="e.g. 2026-04 or Q2-2026"
                      value={newDraft.period ?? ''}
                      onChange={(e) => setNewDraft((p) => ({ ...p, period: e.target.value }))}
                      style={{ width: '100%', padding: '8px 12px', borderRadius: 8, border: '1px solid var(--border-subtle)', background: 'var(--bg-surface-raised)', color: 'var(--text-primary)', fontSize: 13, boxSizing: 'border-box' }}
                    />
                  </div>
                  <div>
                    <label style={{ fontSize: 12, fontWeight: 500, color: 'var(--text-muted)', display: 'block', marginBottom: 5 }}>Language</label>
                    <select
                      aria-label="Draft language"
                      value={newDraft.locale ?? 'en'}
                      onChange={(e) => setNewDraft((p) => ({ ...p, locale: e.target.value }))}
                      style={{ width: '100%', padding: '8px 12px', borderRadius: 8, border: '1px solid var(--border-subtle)', background: 'var(--bg-surface-raised)', color: 'var(--text-primary)', fontSize: 13, boxSizing: 'border-box' }}
                    >
                      {SUPPORTED_LOCALES.map((locale) => (
                        <option key={locale} value={locale}>
                          {LOCALE_LABELS[locale]}
                        </option>
                      ))}
                    </select>
                  </div>
                </div>
              </div>

              <div style={{ display: 'flex', gap: 8, justifyContent: 'flex-end', marginTop: 24 }}>
                <button
                  onClick={() => setShowCreateModal(false)}
                  style={{ padding: '8px 16px', borderRadius: 8, border: '1px solid var(--border-subtle)', background: 'transparent', color: 'var(--text-secondary)', fontSize: 13, cursor: 'pointer' }}
                >
                  Cancel
                </button>
                <motion.button
                  whileHover={{ scale: 1.02 }}
                  whileTap={{ scale: 0.98 }}
                  onClick={handleCreate}
                  disabled={createDraft.isPending || !newDraft.template_id || !newDraft.title}
                  style={{
                    padding: '8px 20px',
                    borderRadius: 8,
                    border: 'none',
                    background: 'var(--brand-accent)',
                    color: '#fff',
                    fontSize: 13,
                    fontWeight: 500,
                    cursor: createDraft.isPending ? 'not-allowed' : 'pointer',
                    opacity: createDraft.isPending ? 0.7 : 1,
                  }}
                >
                  {createDraft.isPending ? 'Creating…' : 'Create draft'}
                </motion.button>
              </div>
            </motion.div>
          </motion.div>
        )}
      </AnimatePresence>
    </PageTransition>
  )
}
