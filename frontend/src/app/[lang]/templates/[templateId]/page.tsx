'use client'

import { useState, use } from 'react'
import { motion, AnimatePresence } from 'framer-motion'
import { ArrowLeft, Save, History, Palette, Tag, Layers } from 'lucide-react'
import { useTemplate, useTemplateVersions, useUpdateTemplateSections, useUpdateTemplateTheme } from '@/lib/api/template-hooks'
import { SectionList } from '@/components/templates/section-list'
import { SectionEditor } from '@/components/templates/section-editor'
import { ThemeTokens } from '@/components/templates/theme-tokens'
import { IndustryOverlayPicker } from '@/components/templates/industry-overlay-picker'
import { VersionControls } from '@/components/templates/version-controls'
import { PageTransition } from '@/components/shared/page-transition'
import type { TemplateSection, TemplateVersion } from '@/lib/api/template-hooks'
import { useLocalePath } from '@/lib/i18n/navigation'
import { useRouter } from 'next/navigation'

type Tab = 'sections' | 'theme' | 'tags' | 'history'

interface PageProps {
  params: Promise<{ lang: string; templateId: string }>
}

export default function TemplateEditorPage({ params }: PageProps) {
  const { templateId } = use(params)
  const localePath = useLocalePath()
  const router = useRouter()

  const { data: template, isLoading, error } = useTemplate(templateId)
  const { data: versions = [] } = useTemplateVersions(templateId)
  const updateSections = useUpdateTemplateSections(templateId)
  const updateTheme = useUpdateTemplateTheme(templateId)

  const [activeTab, setActiveTab] = useState<Tab>('sections')
  const [sections, setSections] = useState<TemplateSection[] | null>(null)
  const [selectedSectionId, setSelectedSectionId] = useState<string | null>(null)
  const [changelog, setChangelog] = useState('')
  const [pendingVersion, setPendingVersion] = useState<TemplateVersion | null>(null)

  const liveSections = sections ?? template?.current_version.sections ?? []
  const selectedSection = liveSections.find((s) => s.section_id === selectedSectionId) ?? null
  const readOnly = pendingVersion !== null

  function handleSectionUpdate(updated: TemplateSection) {
    setSections((prev) => {
      const base = prev ?? template?.current_version.sections ?? []
      return base.map((s) => (s.section_id === updated.section_id ? updated : s))
    })
  }

  function handleReorder(reordered: TemplateSection[]) {
    setSections(reordered.map((s, i) => ({ ...s, order: i })))
  }

  function handleAddSection() {
    const newSection: TemplateSection = {
      section_id: `new_${Date.now()}`,
      heading: 'New Section',
      order: liveSections.length,
      prompt_template: '',
      chart_types: [],
      max_tokens: 1000,
      required: false,
    }
    setSections([...liveSections, newSection])
    setSelectedSectionId(newSection.section_id)
  }

  function handleDeleteSection(sectionId: string) {
    setSections(liveSections.filter((s) => s.section_id !== sectionId))
    if (selectedSectionId === sectionId) setSelectedSectionId(null)
  }

  async function handleSaveSections() {
    if (!sections) return
    await updateSections.mutateAsync({ sections, changelog })
    setSections(null)
    setChangelog('')
  }

  const hasSectionChanges = sections !== null

  const TABS: { id: Tab; label: string; icon: React.ReactNode }[] = [
    { id: 'sections', label: 'Sections', icon: <Layers size={14} /> },
    { id: 'theme', label: 'Theme', icon: <Palette size={14} /> },
    { id: 'tags', label: 'Industry tags', icon: <Tag size={14} /> },
    { id: 'history', label: 'History', icon: <History size={14} /> },
  ]

  if (isLoading) {
    return (
      <PageTransition className="p-8">
        <div style={{ display: 'flex', flexDirection: 'column', gap: 16 }}>
          {Array.from({ length: 3 }).map((_, i) => (
            <div key={i} style={{ height: 60, borderRadius: 10, background: 'var(--bg-surface-raised)', animation: 'pulse 1.5s ease-in-out infinite' }} />
          ))}
        </div>
      </PageTransition>
    )
  }

  if (error || !template) {
    return (
      <PageTransition className="p-8">
        <div style={{ color: '#b91c1c', fontSize: 14 }}>
          {error instanceof Error ? error.message : 'Template not found'}
        </div>
      </PageTransition>
    )
  }

  return (
    <PageTransition className="p-8">
      <div style={{ maxWidth: 1100 }}>
        {/* Header */}
        <div style={{ display: 'flex', alignItems: 'flex-start', gap: 12, marginBottom: 24 }}>
          <motion.button
            whileHover={{ scale: 1.05 }}
            whileTap={{ scale: 0.95 }}
            onClick={() => router.push(localePath('/templates'))}
            style={{
              width: 36,
              height: 36,
              borderRadius: 9,
              border: '1px solid var(--border-subtle)',
              background: 'var(--bg-surface-raised)',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              cursor: 'pointer',
              flexShrink: 0,
              marginTop: 2,
            }}
          >
            <ArrowLeft size={15} color="var(--text-secondary)" />
          </motion.button>

          <div style={{ flex: 1 }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: 10, marginBottom: 2 }}>
              <h1 style={{ fontSize: 20, fontWeight: 600, letterSpacing: '-0.02em', color: 'var(--text-primary)' }}>
                {template.display_name}
              </h1>
              <span
                style={{
                  fontSize: 11,
                  fontWeight: 500,
                  color: 'var(--brand-accent)',
                  background: 'rgba(var(--brand-accent-rgb),0.1)',
                  padding: '2px 8px',
                  borderRadius: 999,
                  border: '1px solid rgba(var(--brand-accent-rgb),0.2)',
                  textTransform: 'capitalize',
                }}
              >
                {template.report_type}
              </span>
              {pendingVersion && (
                <>
                  <span style={{ fontSize: 11, color: '#f59e0b', background: 'rgba(245,158,11,0.12)', padding: '2px 8px', borderRadius: 999 }}>
                    Viewing v{pendingVersion.version_number}
                  </span>
                  <motion.button
                    whileHover={{ scale: 1.03 }}
                    whileTap={{ scale: 0.97 }}
                    onClick={() => { setPendingVersion(null); setSections(null); setSelectedSectionId(null); }}
                    style={{
                      fontSize: 11,
                      fontWeight: 500,
                      color: 'var(--brand-accent)',
                      background: 'rgba(var(--brand-accent-rgb),0.08)',
                      padding: '2px 10px',
                      borderRadius: 999,
                      border: '1px solid rgba(var(--brand-accent-rgb),0.25)',
                      cursor: 'pointer',
                    }}
                  >
                    Return to current
                  </motion.button>
                </>
              )}
            </div>
            <p style={{ fontSize: 12, color: 'var(--text-muted)' }}>{template.description}</p>
          </div>

          {hasSectionChanges && !readOnly && (
            <div style={{ display: 'flex', gap: 8, alignItems: 'center' }}>
              <input
                aria-label="Template version changelog"
                value={changelog}
                onChange={(e) => setChangelog(e.target.value)}
                placeholder="Describe changes…"
                style={{
                  padding: '7px 12px',
                  borderRadius: 8,
                  border: '1px solid var(--border-subtle)',
                  background: 'var(--bg-surface-raised)',
                  color: 'var(--text-primary)',
                  fontSize: 13,
                  width: 220,
                }}
              />
              <motion.button
                whileHover={{ scale: 1.02 }}
                whileTap={{ scale: 0.98 }}
                onClick={handleSaveSections}
                disabled={updateSections.isPending}
                style={{
                  display: 'flex',
                  alignItems: 'center',
                  gap: 6,
                  padding: '8px 16px',
                  borderRadius: 8,
                  border: 'none',
                  background: 'var(--brand-accent)',
                  color: '#fff',
                  fontSize: 13,
                  fontWeight: 500,
                  cursor: updateSections.isPending ? 'not-allowed' : 'pointer',
                  opacity: updateSections.isPending ? 0.7 : 1,
                }}
              >
                <Save size={13} />
                {updateSections.isPending ? 'Saving…' : 'Save version'}
              </motion.button>
            </div>
          )}
        </div>

        {/* Tabs */}
        <div
          style={{
            display: 'flex',
            gap: 2,
            marginBottom: 20,
            borderBottom: '1px solid var(--border-subtle)',
            paddingBottom: 0,
          }}
        >
          {TABS.map((tab) => (
            <motion.button
              key={tab.id}
              whileHover={{ scale: 1.01 }}
              onClick={() => setActiveTab(tab.id)}
              style={{
                display: 'flex',
                alignItems: 'center',
                gap: 6,
                padding: '8px 14px',
                borderRadius: '8px 8px 0 0',
                border: 'none',
                borderBottom: activeTab === tab.id ? '2px solid var(--brand-accent)' : '2px solid transparent',
                background: 'transparent',
                color: activeTab === tab.id ? 'var(--brand-accent)' : 'var(--text-secondary)',
                fontSize: 13,
                fontWeight: activeTab === tab.id ? 500 : 400,
                cursor: 'pointer',
              }}
            >
              {tab.icon}
              {tab.label}
            </motion.button>
          ))}
        </div>

        {/* Tab content */}
        <AnimatePresence mode="wait">
          {activeTab === 'sections' && (
            <motion.div
              key="sections"
              initial={{ opacity: 0, y: 4 }}
              animate={{ opacity: 1, y: 0 }}
              exit={{ opacity: 0 }}
              style={{ display: 'grid', gridTemplateColumns: '240px 1fr', gap: 20 }}
            >
              <SectionList
                sections={liveSections}
                selectedSectionId={selectedSectionId}
                onSelect={(s) => setSelectedSectionId(s.section_id)}
                onReorder={handleReorder}
                onDelete={handleDeleteSection}
                onAdd={handleAddSection}
                readOnly={readOnly}
              />
              <div
                style={{
                  padding: '20px 24px',
                  borderRadius: 12,
                  border: '1px solid var(--border-subtle)',
                  background: 'var(--bg-surface)',
                  minHeight: 400,
                }}
              >
                {selectedSection ? (
                  <SectionEditor
                    key={selectedSection.section_id}
                    section={selectedSection}
                    onSave={handleSectionUpdate}
                    readOnly={readOnly}
                  />
                ) : (
                  <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'center', height: '100%', color: 'var(--text-muted)', fontSize: 13 }}>
                    Select a section to edit
                  </div>
                )}
              </div>
            </motion.div>
          )}

          {activeTab === 'theme' && (
            <motion.div
              key="theme"
              initial={{ opacity: 0, y: 4 }}
              animate={{ opacity: 1, y: 0 }}
              exit={{ opacity: 0 }}
              style={{ padding: '20px 24px', borderRadius: 12, border: '1px solid var(--border-subtle)', background: 'var(--bg-surface)' }}
            >
              <ThemeTokens
                key={JSON.stringify(pendingVersion?.theme_tokens ?? template.theme_tokens)}
                tokens={pendingVersion?.theme_tokens ?? template.theme_tokens}
                onSave={(tokens) => updateTheme.mutateAsync(tokens)}
                isSaving={updateTheme.isPending}
                readOnly={readOnly}
              />
            </motion.div>
          )}

          {activeTab === 'tags' && (
            <motion.div
              key="tags"
              initial={{ opacity: 0, y: 4 }}
              animate={{ opacity: 1, y: 0 }}
              exit={{ opacity: 0 }}
              style={{ padding: '20px 24px', borderRadius: 12, border: '1px solid var(--border-subtle)', background: 'var(--bg-surface)' }}
            >
              <div style={{ display: 'flex', flexDirection: 'column', gap: 12 }}>
                <div style={{ fontSize: 12, color: 'var(--text-muted)', background: 'var(--bg-surface-raised)', padding: '8px 12px', borderRadius: 8, border: '1px solid var(--border-subtle)' }}>
                  Industry tags are managed via industry profiles and cannot be edited directly.
                </div>
                <IndustryOverlayPicker
                  selected={template.industry_tags}
                  onChange={() => {}}
                  readOnly={true}
                />
              </div>
            </motion.div>
          )}

          {activeTab === 'history' && (
            <motion.div
              key="history"
              initial={{ opacity: 0, y: 4 }}
              animate={{ opacity: 1, y: 0 }}
              exit={{ opacity: 0 }}
              style={{ padding: '20px 24px', borderRadius: 12, border: '1px solid var(--border-subtle)', background: 'var(--bg-surface)' }}
            >
              <VersionControls
                versions={versions}
                currentVersionNumber={template.current_version.version_number}
                onSelectVersion={(v) => {
                  if (v.version_number === template.current_version.version_number) {
                    setPendingVersion(null)
                    setSections(null)
                    setActiveTab('sections')
                    return
                  }
                  setPendingVersion(v)
                  setSections(v.sections)
                  setActiveTab('sections')
                }}
              />
            </motion.div>
          )}
        </AnimatePresence>
      </div>
    </PageTransition>
  )
}
