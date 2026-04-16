'use client'

import { useState } from 'react'
import { motion, AnimatePresence } from 'framer-motion'
import { Plus, Search, LayoutTemplate } from 'lucide-react'
import { useCreateTemplate, useTemplates } from '@/lib/api/template-hooks'
import { TemplateCard } from '@/components/templates/template-card'
import { PageTransition } from '@/components/shared/page-transition'
import type { Template } from '@/lib/api/template-hooks'
import { LOCALE_LABELS, SUPPORTED_LOCALES } from '@/lib/i18n/locales'
import { useLocalePath } from '@/lib/i18n/navigation'
import { useRouter } from 'next/navigation'

export default function TemplatesPage() {
  const { data: templates, isLoading, error } = useTemplates()
  const createTemplate = useCreateTemplate()
  const [search, setSearch] = useState('')
  const [reportTypeFilter, setReportTypeFilter] = useState<string>('all')
  const [showCreateModal, setShowCreateModal] = useState(false)
  const [newTemplate, setNewTemplate] = useState({
    display_name: '',
    description: '',
    base_locale: 'en',
  })
  const localePath = useLocalePath()
  const router = useRouter()

  const filtered = (templates ?? []).filter((t) => {
    const matchSearch =
      !search ||
      t.display_name.toLowerCase().includes(search.toLowerCase()) ||
      t.description.toLowerCase().includes(search.toLowerCase()) ||
      t.industry_tags.some((tag) => tag.includes(search.toLowerCase()))
    const matchType = reportTypeFilter === 'all' || t.report_type === reportTypeFilter
    return matchSearch && matchType
  })

  function handleSelect(template: Template) {
    router.push(localePath(`/templates/${template.template_id}`))
  }

  async function handleCreateTemplate() {
    if (!newTemplate.display_name.trim()) return

    const template = await createTemplate.mutateAsync({
      display_name: newTemplate.display_name.trim(),
      description: newTemplate.description.trim(),
      base_locale: newTemplate.base_locale,
    })

    setShowCreateModal(false)
    setNewTemplate({ display_name: '', description: '', base_locale: 'en' })
    router.push(localePath(`/templates/${template.template_id}`))
  }

  return (
    <PageTransition className="p-8">
      <div style={{ maxWidth: 1100 }}>
        {/* Header */}
        <div style={{ display: 'flex', alignItems: 'flex-start', justifyContent: 'space-between', marginBottom: 28 }}>
          <div>
            <h1
              style={{ fontSize: 22, fontWeight: 600, letterSpacing: '-0.02em', color: 'var(--text-primary)', marginBottom: 4 }}
            >
              Templates
            </h1>
            <p style={{ fontSize: 13, color: 'var(--text-muted)' }}>
              Manage report structure, prompts, and branding for generated documents.
            </p>
          </div>

          <motion.button
            whileHover={{ scale: 1.02 }}
            whileTap={{ scale: 0.98 }}
            onClick={() => setShowCreateModal(true)}
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
            New template
          </motion.button>
        </div>

        {/* Filters */}
        <div style={{ display: 'flex', gap: 10, marginBottom: 20, alignItems: 'center' }}>
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
              maxWidth: 320,
            }}
          >
            <Search size={14} color="var(--text-muted)" />
            <input
              value={search}
              onChange={(e) => setSearch(e.target.value)}
              placeholder="Search templates…"
              style={{ border: 'none', background: 'transparent', outline: 'none', fontSize: 13, color: 'var(--text-primary)', flex: 1 }}
            />
          </div>

          {(['all', 'monthly', 'quarterly', 'custom'] as const).map((type) => (
            <motion.button
              key={type}
              whileHover={{ scale: 1.02 }}
              whileTap={{ scale: 0.98 }}
              onClick={() => setReportTypeFilter(type)}
              style={{
                padding: '7px 14px',
                borderRadius: 8,
                border: reportTypeFilter === type ? '1px solid rgba(var(--brand-accent-rgb),0.4)' : '1px solid var(--border-subtle)',
                background: reportTypeFilter === type ? 'rgba(var(--brand-accent-rgb),0.1)' : 'var(--bg-surface-raised)',
                color: reportTypeFilter === type ? 'var(--brand-accent)' : 'var(--text-secondary)',
                fontSize: 12,
                fontWeight: reportTypeFilter === type ? 500 : 400,
                cursor: 'pointer',
                textTransform: 'capitalize',
              }}
            >
              {type}
            </motion.button>
          ))}
        </div>

        {/* Content */}
        {isLoading && (
          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(300px, 1fr))', gap: 16 }}>
            {Array.from({ length: 6 }).map((_, i) => (
              <div
                key={i}
                style={{
                  height: 180,
                  borderRadius: 12,
                  background: 'var(--bg-surface-raised)',
                  border: '1px solid var(--border-subtle)',
                  animation: 'pulse 1.5s ease-in-out infinite',
                }}
              />
            ))}
          </div>
        )}

        {error && (
          <div
            style={{
              padding: '20px 24px',
              borderRadius: 12,
              border: '1px solid rgba(239,68,68,0.3)',
              background: 'rgba(239,68,68,0.06)',
              color: '#b91c1c',
              fontSize: 13,
            }}
          >
            Failed to load templates: {error instanceof Error ? error.message : 'Unknown error'}
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
                style={{
                  textAlign: 'center',
                  padding: '60px 0',
                  color: 'var(--text-muted)',
                }}
              >
                <LayoutTemplate size={36} style={{ margin: '0 auto 12px', opacity: 0.4 }} />
                <div style={{ fontSize: 14, fontWeight: 500, marginBottom: 4 }}>
                  {search ? 'No templates match your search' : 'No templates yet'}
                </div>
                <div style={{ fontSize: 12 }}>
                  {search ? 'Try a different search term' : 'Create your first template to get started'}
                </div>
              </motion.div>
            ) : (
              <motion.div
                key="grid"
                initial={{ opacity: 0 }}
                animate={{ opacity: 1 }}
                exit={{ opacity: 0 }}
                style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(300px, 1fr))', gap: 16 }}
              >
                {filtered.map((template) => (
                  <TemplateCard key={template.template_id} template={template} onClick={handleSelect} />
                ))}
              </motion.div>
            )}
          </AnimatePresence>
        )}
      </div>

      <AnimatePresence>
        {showCreateModal && (
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            onClick={(event) => {
              if (event.target === event.currentTarget) setShowCreateModal(false)
            }}
            style={{
              position: 'fixed',
              inset: 0,
              background: 'rgba(0,0,0,0.45)',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              zIndex: 1000,
            }}
          >
            <motion.div
              initial={{ opacity: 0, scale: 0.96 }}
              animate={{ opacity: 1, scale: 1 }}
              exit={{ opacity: 0, scale: 0.96 }}
              style={{
                width: 480,
                borderRadius: 16,
                border: '1px solid var(--border-subtle)',
                background: 'var(--bg-surface)',
                boxShadow: '0 24px 60px rgba(0,0,0,0.2)',
                padding: '24px 28px',
              }}
            >
              <h2 style={{ fontSize: 18, fontWeight: 600, color: 'var(--text-primary)', marginBottom: 6 }}>
                Create template
              </h2>
              <p style={{ fontSize: 13, color: 'var(--text-muted)', marginBottom: 18 }}>
                Start with a default section structure, then tailor prompts, charts, and theme tokens in the editor.
              </p>

              <div style={{ display: 'flex', flexDirection: 'column', gap: 14 }}>
                <div>
                  <label style={{ display: 'block', fontSize: 12, fontWeight: 500, color: 'var(--text-muted)', marginBottom: 6 }}>
                    Template name
                  </label>
                  <input
                    aria-label="Template name"
                    value={newTemplate.display_name}
                    onChange={(event) =>
                      setNewTemplate((current) => ({ ...current, display_name: event.target.value }))
                    }
                    placeholder="e.g. EU Packaging Quarterly"
                    style={{
                      width: '100%',
                      padding: '9px 12px',
                      borderRadius: 8,
                      border: '1px solid var(--border-subtle)',
                      background: 'var(--bg-surface-raised)',
                      color: 'var(--text-primary)',
                      fontSize: 13,
                      boxSizing: 'border-box',
                    }}
                  />
                </div>

                <div>
                  <label style={{ display: 'block', fontSize: 12, fontWeight: 500, color: 'var(--text-muted)', marginBottom: 6 }}>
                    Description
                  </label>
                  <textarea
                    aria-label="Template description"
                    value={newTemplate.description}
                    onChange={(event) =>
                      setNewTemplate((current) => ({ ...current, description: event.target.value }))
                    }
                    rows={4}
                    placeholder="What kind of report should this template generate?"
                    style={{
                      width: '100%',
                      padding: '9px 12px',
                      borderRadius: 8,
                      border: '1px solid var(--border-subtle)',
                      background: 'var(--bg-surface-raised)',
                      color: 'var(--text-primary)',
                      fontSize: 13,
                      lineHeight: 1.6,
                      resize: 'vertical',
                      boxSizing: 'border-box',
                    }}
                  />
                </div>

                <div>
                  <label style={{ display: 'block', fontSize: 12, fontWeight: 500, color: 'var(--text-muted)', marginBottom: 6 }}>
                    Base language
                  </label>
                  <select
                    aria-label="Template base language"
                    value={newTemplate.base_locale}
                    onChange={(event) =>
                      setNewTemplate((current) => ({ ...current, base_locale: event.target.value }))
                    }
                    style={{
                      width: '100%',
                      padding: '9px 12px',
                      borderRadius: 8,
                      border: '1px solid var(--border-subtle)',
                      background: 'var(--bg-surface-raised)',
                      color: 'var(--text-primary)',
                      fontSize: 13,
                      boxSizing: 'border-box',
                    }}
                  >
                    {SUPPORTED_LOCALES.map((locale) => (
                      <option key={locale} value={locale}>
                        {LOCALE_LABELS[locale]}
                      </option>
                    ))}
                  </select>
                </div>
              </div>

              <div style={{ display: 'flex', justifyContent: 'flex-end', gap: 8, marginTop: 22 }}>
                <button
                  onClick={() => setShowCreateModal(false)}
                  style={{
                    padding: '8px 14px',
                    borderRadius: 8,
                    border: '1px solid var(--border-subtle)',
                    background: 'transparent',
                    color: 'var(--text-secondary)',
                    fontSize: 13,
                    cursor: 'pointer',
                  }}
                >
                  Cancel
                </button>
                <motion.button
                  whileHover={{ scale: 1.02 }}
                  whileTap={{ scale: 0.98 }}
                  onClick={handleCreateTemplate}
                  disabled={createTemplate.isPending || !newTemplate.display_name.trim()}
                  style={{
                    padding: '8px 16px',
                    borderRadius: 8,
                    border: 'none',
                    background: 'var(--brand-accent)',
                    color: '#fff',
                    fontSize: 13,
                    fontWeight: 500,
                    cursor: createTemplate.isPending ? 'not-allowed' : 'pointer',
                    opacity: createTemplate.isPending ? 0.7 : 1,
                  }}
                >
                  {createTemplate.isPending ? 'Creating…' : 'Create template'}
                </motion.button>
              </div>
            </motion.div>
          </motion.div>
        )}
      </AnimatePresence>
    </PageTransition>
  )
}
