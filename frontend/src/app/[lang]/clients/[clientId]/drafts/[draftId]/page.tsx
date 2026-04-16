'use client'

import { use, useEffect, useState } from 'react'
import { AnimatePresence, motion } from 'framer-motion'
import {
  useComposeDraft,
  useDraft,
  useDraftRevisions,
  useTranslateDraft,
  useUpdateDraftSection,
  useUpdateDraftStatus,
  useExportDraft,
  useApprovalAction,
} from '@/lib/api/draft-hooks'
import { DraftToolbar } from '@/components/drafts/draft-toolbar'
import { DraftSection } from '@/components/drafts/draft-section'
import { SectionEditor } from '@/components/drafts/section-editor'
import { ChatSidebar } from '@/components/drafts/chat-sidebar'
import { DocumentViewer } from '@/components/drafts/document-viewer'
import { RevisionSelector } from '@/components/drafts/revision-selector'
import { RevisionDiff } from '@/components/drafts/revision-diff'
import { ApprovalActions } from '@/components/approval/approval-actions'
import { ApprovalTimeline } from '@/components/approval/approval-timeline'
import { ExportMenu } from '@/components/drafts/export-menu'
import type { DraftStatus, DraftRevision, SectionEditPayload } from '@/lib/api/draft-hooks'
import { LOCALE_LABELS, SUPPORTED_LOCALES } from '@/lib/i18n/locales'
import { useLocalePath } from '@/lib/i18n/navigation'
import { useRouter } from 'next/navigation'
import { Loader2, Layers, GitCompare, Clock } from 'lucide-react'

type RightPanel = 'chat' | 'revisions' | 'diff' | 'history'

interface PageProps {
  params: Promise<{ lang: string; clientId: string; draftId: string }>
}

export default function DraftStudioPage({ params }: PageProps) {
  const { clientId, draftId } = use(params)
  const localePath = useLocalePath()
  const router = useRouter()

  const { data: draft, isLoading, error } = useDraft(clientId, draftId)
  const { data: revisions = [] } = useDraftRevisions(clientId, draftId)
  const composeDraft = useComposeDraft(clientId, draftId)
  const translateDraft = useTranslateDraft(clientId, draftId)
  const updateSection = useUpdateDraftSection(clientId, draftId)
  const updateStatus = useUpdateDraftStatus(clientId, draftId)
  const exportDraft = useExportDraft(clientId, draftId)
  const approvalAction = useApprovalAction(clientId, draftId)

  const [selectedSectionId, setSelectedSectionId] = useState<string | null>(null)
  const [editingSectionId, setEditingSectionId] = useState<string | null>(null)
  const [rightPanel, setRightPanel] = useState<RightPanel>('chat')
  const [showExportMenu, setShowExportMenu] = useState(false)
  const [diffRevision, setDiffRevision] = useState<DraftRevision | null>(null)

  const selectedSection = draft?.sections.find((s) => s.section_id === selectedSectionId) ?? null
  const editingSection = draft?.sections.find((s) => s.section_id === editingSectionId) ?? null

  useEffect(() => {
    if (!draft?.sections.length) {
      return
    }

    const hasSelectedSection = selectedSectionId
      ? draft.sections.some((section) => section.section_id === selectedSectionId)
      : false

    if (!hasSelectedSection) {
      setSelectedSectionId(draft.sections[0]?.section_id ?? null)
    }
  }, [draft?.sections, selectedSectionId])

  async function handleExport(format: 'pdf' | 'docx' | 'json') {
    const result = await exportDraft.mutateAsync(format)
    const link = document.createElement('a')
    link.href = result.url
    link.download = result.filename
    link.rel = 'noopener'
    document.body.appendChild(link)
    link.click()
    link.remove()
  }

  function handleSaveSection(sectionId: string, payload: SectionEditPayload) {
    updateSection.mutate({ sectionId, payload })
    setEditingSectionId(null)
  }

  const PANELS: { id: RightPanel; icon: React.ReactNode; label: string }[] = [
    { id: 'chat', icon: <Layers size={13} />, label: 'AI' },
    { id: 'revisions', icon: <Clock size={13} />, label: 'History' },
    { id: 'diff', icon: <GitCompare size={13} />, label: 'Diff' },
  ]

  if (isLoading) {
    return (
      <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'center', height: '100vh' }}>
        <Loader2 size={24} color="var(--text-muted)" style={{ animation: 'spin 1s linear infinite' }} />
      </div>
    )
  }

  if (error || !draft) {
    return (
      <div style={{ padding: 32, color: '#b91c1c', fontSize: 14 }}>
        {error instanceof Error ? error.message : 'Draft not found'}
      </div>
    )
  }

  return (
    <div style={{ display: 'flex', flexDirection: 'column', height: '100%' }}>
      {/* Toolbar */}
      <div style={{ position: 'relative' }}>
        <DraftToolbar
          draft={draft}
          onBack={() => router.push(localePath(`/clients/${clientId}/drafts`))}
          onStatusChange={(status: DraftStatus) => updateStatus.mutate(status)}
          onExport={() => setShowExportMenu(true)}
          onCompose={() => composeDraft.mutate()}
          onTranslate={(locale) => translateDraft.mutate(locale)}
          availableLocales={SUPPORTED_LOCALES.map((locale) => ({
            code: locale,
            label: LOCALE_LABELS[locale],
          }))}
          isComposing={composeDraft.isPending}
          isTranslating={translateDraft.isPending}
          isUpdating={updateStatus.isPending}
        />
        <div style={{ position: 'absolute', top: 8, right: 60 }}>
          <ExportMenu
            isOpen={showExportMenu}
            onClose={() => setShowExportMenu(false)}
            onExport={handleExport}
          />
        </div>
      </div>

      {/* Main layout */}
      <div style={{ flex: 1, display: 'grid', gridTemplateColumns: '240px 1fr 320px', overflow: 'hidden' }}>
        {/* Left panel: section list */}
        <div
          style={{
            overflowY: 'auto',
            padding: '16px 12px',
            borderRight: '1px solid var(--border-subtle)',
            display: 'flex',
            flexDirection: 'column',
            gap: 6,
          }}
        >
          <div style={{ fontSize: 10, fontWeight: 600, color: 'var(--text-muted)', textTransform: 'uppercase', letterSpacing: '0.06em', padding: '0 4px', marginBottom: 4 }}>
            Sections
          </div>
          {draft.sections.map((section) => (
            <DraftSection
              key={section.section_id}
              section={section}
              isSelected={selectedSectionId === section.section_id}
              onSelect={() => { setSelectedSectionId(section.section_id); setEditingSectionId(null) }}
              onEdit={() => setEditingSectionId(section.section_id)}
            />
          ))}
        </div>

        {/* Center: document or editor */}
        <div style={{ overflowY: 'auto', padding: '16px 20px' }}>
          <AnimatePresence mode="wait">
            {editingSection ? (
              <motion.div
                key="editor"
                initial={{ opacity: 0 }}
                animate={{ opacity: 1 }}
                exit={{ opacity: 0 }}
                style={{
                  padding: '20px 24px',
                  borderRadius: 12,
                  border: '1px solid var(--border-subtle)',
                  background: 'var(--bg-surface)',
                }}
              >
                <SectionEditor
                  section={editingSection}
                  onSave={handleSaveSection}
                  isSaving={updateSection.isPending}
                />
              </motion.div>
            ) : (
              <motion.div
                key="doc"
                initial={{ opacity: 0 }}
                animate={{ opacity: 1 }}
                exit={{ opacity: 0 }}
                style={{ height: '100%' }}
              >
                <DocumentViewer
                  draft={draft}
                  selectedSectionId={selectedSectionId}
                  onSelectSection={(id) => setSelectedSectionId(id)}
                />
              </motion.div>
            )}
          </AnimatePresence>

          {/* Approval actions when in approval status */}
          {draft.status === 'approval' && selectedSection && (
            <motion.div
              initial={{ opacity: 0, y: 8 }}
              animate={{ opacity: 1, y: 0 }}
              style={{ marginTop: 16, padding: '16px 20px', borderRadius: 12, border: '1px solid var(--border-subtle)', background: 'var(--bg-surface)' }}
            >
              <div style={{ fontSize: 12, fontWeight: 500, color: 'var(--text-muted)', marginBottom: 10 }}>
                Section approval
              </div>
              <ApprovalActions
                sectionId={selectedSection.section_id}
                onAction={(payload) => approvalAction.mutate(payload)}
                isLoading={approvalAction.isPending}
              />
            </motion.div>
          )}
        </div>

        {/* Right panel */}
        <div
          style={{
            borderLeft: '1px solid var(--border-subtle)',
            display: 'flex',
            flexDirection: 'column',
            overflow: 'hidden',
          }}
        >
          {/* Panel tabs */}
          <div
            style={{
              display: 'flex',
              borderBottom: '1px solid var(--border-subtle)',
              padding: '0 12px',
            }}
          >
            {PANELS.map((panel) => (
              <motion.button
                key={panel.id}
                whileTap={{ scale: 0.97 }}
                onClick={() => setRightPanel(panel.id)}
                style={{
                  display: 'flex',
                  alignItems: 'center',
                  gap: 5,
                  padding: '10px 12px',
                  border: 'none',
                  borderBottom: rightPanel === panel.id ? '2px solid var(--brand-accent)' : '2px solid transparent',
                  background: 'transparent',
                  color: rightPanel === panel.id ? 'var(--brand-accent)' : 'var(--text-muted)',
                  fontSize: 12,
                  fontWeight: rightPanel === panel.id ? 500 : 400,
                  cursor: 'pointer',
                }}
              >
                {panel.icon}
                {panel.label}
              </motion.button>
            ))}
          </div>

          {/* Panel content */}
          <div style={{ flex: 1, overflowY: 'auto', padding: 12 }}>
            <AnimatePresence mode="wait">
              {rightPanel === 'chat' && (
                <motion.div
                  key="chat"
                  initial={{ opacity: 0 }}
                  animate={{ opacity: 1 }}
                  exit={{ opacity: 0 }}
                  style={{ height: '100%' }}
                >
                  <ChatSidebar
                    clientId={clientId}
                    draftId={draftId}
                    activeSectionId={selectedSectionId ?? undefined}
                  />
                </motion.div>
              )}

              {rightPanel === 'revisions' && (
                <motion.div
                  key="revisions"
                  initial={{ opacity: 0 }}
                  animate={{ opacity: 1 }}
                  exit={{ opacity: 0 }}
                >
                  <RevisionSelector
                    revisions={revisions}
                    currentRevision={draft.current_revision}
                    onSelect={(rev) => {
                      setDiffRevision(rev)
                      setRightPanel('diff')
                    }}
                  />
                </motion.div>
              )}

              {rightPanel === 'diff' && (
                <motion.div
                  key="diff"
                  initial={{ opacity: 0 }}
                  animate={{ opacity: 1 }}
                  exit={{ opacity: 0 }}
                >
                  {diffRevision ? (
                    <RevisionDiff
                      revision={diffRevision}
                      previousRevision={
                        revisions.find((r) => r.revision_number === diffRevision.revision_number - 1) ?? null
                      }
                    />
                  ) : (
                    <div style={{ textAlign: 'center', padding: '32px 0', color: 'var(--text-muted)', fontSize: 12 }}>
                      Select a revision from History to view diff
                    </div>
                  )}
                </motion.div>
              )}

              {rightPanel === 'history' && (
                <motion.div
                  key="history"
                  initial={{ opacity: 0 }}
                  animate={{ opacity: 1 }}
                  exit={{ opacity: 0 }}
                >
                  <ApprovalTimeline revisions={revisions} createdAt={draft.created_at} />
                </motion.div>
              )}
            </AnimatePresence>
          </div>
        </div>
      </div>
    </div>
  )
}
