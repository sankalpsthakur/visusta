'use client'

import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { apiDelete, apiGet, apiGetFile, apiPost, apiPut } from './client'

// Compose job polling
//
// Compose invokes an LLM that can take 15–30s, which exceeds Render's proxy
// timeout. The backend returns 202 + { job_id } immediately and we poll
// GET .../compose/{job_id} until status = done | failed.
const COMPOSE_POLL_INTERVAL_MS = 2_000
const COMPOSE_POLL_MAX_ATTEMPTS = 120 // ~4 minutes of safety margin

interface ComposeJobAccepted {
  job_id: string
  status: string
}

interface ComposeJobStatus {
  job_id: string
  status: 'pending' | 'running' | 'done' | 'failed'
  error?: string | null
  revision?: BackendRevisionDetail | null
}

type BackendDraftStatus =
  | 'composing'
  | 'review'
  | 'revision'
  | 'translating'
  | 'approval'
  | 'approved'
  | 'exported'
  | 'archived'

interface BackendTemplate {
  id: number
  current_version: number
}

interface BackendTemplateVersion {
  id: number
  version_number: number
}

interface BackendBlock {
  block_id?: string
  block_type?: string
  content?: unknown
  metadata?: Record<string, unknown>
}

interface BackendSection {
  section_id: string
  heading: string
  locale: string
  blocks: BackendBlock[]
  facts: string[]
  citations: string[]
  translation_status?: string | null
  approval_status?: string | null
}

interface BackendRevision {
  id: number
  draft_id: number
  revision_number: number
  authored_by?: string | null
  note?: string | null
  created_at: string
}

interface BackendRevisionDetail extends BackendRevision {
  sections: BackendSection[]
}

interface BackendDraft {
  id: number
  client_id: string
  template_version_id?: number | null
  title: string
  period?: string | null
  primary_locale: string
  status: BackendDraftStatus
  current_revision_id?: number | null
  created_by?: string | null
  created_at: string
  updated_at: string
}

interface BackendDraftDetail extends BackendDraft {
  current_revision?: BackendRevisionDetail | null
}

interface BackendChatMessage {
  id: number
  draft_id: number
  role: 'user' | 'assistant' | 'system'
  content: string
  section_id?: string | null
  revision_id?: number | null
  created_at: string
}

interface BackendApprovalState {
  id: number
  draft_id: number
  section_id: string
  status: 'approved' | 'rejected' | 'needs_revision'
  reviewer: string
  comment?: string | null
  revision_id?: number | null
  created_at: string
  updated_at: string
}

interface BackendExportJob {
  id: number
  draft_id: number
  revision_id?: number | null
  format: 'pdf' | 'docx'
  locale?: string | null
  status: 'pending' | 'processing' | 'completed' | 'failed'
  output_path?: string | null
  error?: string | null
  requested_by?: string | null
  created_at: string
  updated_at: string
}

export type DraftStatus = BackendDraftStatus
export type ApprovalStatus = 'pending' | 'approved' | 'rejected' | 'needs_revision'
export type TranslationStatus = 'pending' | 'original' | 'translated' | 'low_confidence' | 'failed'

export const DRAFT_STATUS_TRANSITIONS: Record<DraftStatus, DraftStatus[]> = {
  composing: ['review'],
  review: ['revision', 'translating', 'approval', 'archived'],
  revision: ['review'],
  translating: ['review', 'revision'],
  approval: ['approved', 'revision'],
  approved: ['exported', 'archived'],
  exported: ['archived'],
  archived: [],
}

export function getDraftStatusTransitions(status: DraftStatus): DraftStatus[] {
  return DRAFT_STATUS_TRANSITIONS[status] ?? []
}

export interface DraftBlock {
  block_id?: string
  type: 'paragraph' | 'heading' | 'bullet_list' | 'chart' | 'table' | string
  content: string
  metadata?: Record<string, unknown>
}

export interface DraftSection {
  section_id: string
  heading: string
  locale: string
  blocks: DraftBlock[]
  facts: string[]
  citations: string[]
  translation_status: TranslationStatus
  approval_status: ApprovalStatus
}

export interface DraftRevision {
  revision_id: number
  draft_id: number
  revision_number: number
  sections: DraftSection[]
  created_at: string
  created_by?: string
  summary: string
}

export interface ExportJobSummary {
  job_id: number
  format: 'pdf' | 'docx'
  status: 'pending' | 'processing' | 'completed' | 'failed'
  locale?: string
  error?: string
  created_at: string
}

export interface Draft {
  draft_id: number
  client_id: string
  template_id?: number
  title: string
  period: string
  locale: string
  status: DraftStatus
  sections: DraftSection[]
  revision_count: number
  current_revision: number
  created_at: string
  updated_at: string
  assigned_to?: string
  approval_summary: Record<ApprovalStatus, number>
  export_jobs: ExportJobSummary[]
}

export interface DraftListItem {
  draft_id: number
  client_id: string
  title: string
  period: string
  locale: string
  status: DraftStatus
  revision_count: number
  updated_at: string
  assigned_to?: string
}

export interface ChatMessage {
  message_id: number
  draft_id: number
  role: 'user' | 'assistant' | 'system'
  content: string
  section_id?: string
  created_at: string
}

export interface CreateDraftPayload {
  template_id: string | number
  title: string
  period: string
  locale: string
}

export interface SectionEditPayload {
  blocks?: DraftBlock[]
  facts?: string[]
  citations?: string[]
  revision_note?: string
}

export interface ChatMessagePayload {
  content: string
  section_id?: string
}

export interface ApprovalActionPayload {
  action: 'approve' | 'reject' | 'request_revision'
  section_id?: string
  note?: string
}

export interface ExportResult {
  url: string
  filename: string
}

function sleep(ms: number): Promise<void> {
  return new Promise((resolve) => window.setTimeout(resolve, ms))
}

function serializeContent(content: unknown): string {
  if (typeof content === 'string') return content
  if (content == null) return ''
  try {
    return JSON.stringify(content, null, 2)
  } catch {
    return String(content)
  }
}

function mapBlock(block: BackendBlock, index: number): DraftBlock {
  return {
    block_id: block.block_id ?? `block_${index + 1}`,
    type: block.block_type ?? 'paragraph',
    content: serializeContent(block.content),
    metadata: block.metadata ?? {},
  }
}

function mapSection(section: BackendSection): DraftSection {
  const translationStatus = section.translation_status ?? (section.locale === 'en' ? 'original' : 'translated')
  const approvalStatus = (section.approval_status ?? 'pending') as ApprovalStatus

  return {
    section_id: section.section_id,
    heading: section.heading,
    locale: section.locale,
    blocks: (section.blocks ?? []).map(mapBlock),
    facts: section.facts ?? [],
    citations: section.citations ?? [],
    translation_status: translationStatus as TranslationStatus,
    approval_status: approvalStatus,
  }
}

function mapRevision(revision: BackendRevisionDetail): DraftRevision {
  return {
    revision_id: revision.id,
    draft_id: revision.draft_id,
    revision_number: revision.revision_number,
    sections: (revision.sections ?? []).map(mapSection),
    created_at: revision.created_at,
    created_by: revision.authored_by ?? undefined,
    summary: revision.note ?? '',
  }
}

function buildApprovalSummary(sections: DraftSection[]): Record<ApprovalStatus, number> {
  return sections.reduce<Record<ApprovalStatus, number>>(
    (summary, section) => {
      summary[section.approval_status] += 1
      return summary
    },
    { pending: 0, approved: 0, rejected: 0, needs_revision: 0 },
  )
}

function mapExportJob(job: BackendExportJob): ExportJobSummary {
  return {
    job_id: job.id,
    format: job.format,
    status: job.status,
    locale: job.locale ?? undefined,
    error: job.error ?? undefined,
    created_at: job.created_at,
  }
}

function mapDraftListItem(draft: BackendDraft, revisionCount: number): DraftListItem {
  return {
    draft_id: draft.id,
    client_id: draft.client_id,
    title: draft.title,
    period: draft.period ?? '',
    locale: draft.primary_locale,
    status: draft.status,
    revision_count: revisionCount,
    updated_at: draft.updated_at,
    assigned_to: draft.created_by ?? undefined,
  }
}

function mapDraft(
  draft: BackendDraftDetail,
  revisions: DraftRevision[],
  exports: BackendExportJob[],
  approvals: BackendApprovalState[],
): Draft {
  const currentRevision = draft.current_revision ? mapRevision(draft.current_revision) : null
  const sections = currentRevision?.sections ?? []
  const activeLocale = sections[0]?.locale ?? draft.primary_locale
  const approvalSummary = buildApprovalSummary(sections)

  for (const approval of approvals) {
    const key = approval.status as ApprovalStatus
    if (key in approvalSummary) {
      approvalSummary[key] += 0
    }
  }

  return {
    draft_id: draft.id,
    client_id: draft.client_id,
    template_id: draft.template_version_id ?? undefined,
    title: draft.title,
    period: draft.period ?? '',
    locale: activeLocale,
    status: draft.status,
    sections,
    revision_count: revisions.length,
    current_revision: currentRevision?.revision_number ?? 0,
    created_at: draft.created_at,
    updated_at: draft.updated_at,
    assigned_to: draft.created_by ?? undefined,
    approval_summary: approvalSummary,
    export_jobs: exports.map(mapExportJob),
  }
}

async function resolveTemplateVersionId(templateId: string | number): Promise<number> {
  const [template, versions] = await Promise.all([
    apiGet<BackendTemplate>(`/api/templates/${templateId}`),
    apiGet<BackendTemplateVersion[]>(`/api/templates/${templateId}/versions`),
  ])
  const currentVersion =
    versions.find((version) => version.version_number === template.current_version) ??
    versions[versions.length - 1]

  if (!currentVersion) {
    throw new Error(`Template ${templateId} has no available version`)
  }

  return currentVersion.id
}

async function fetchRevisionMetadata(clientId: string, draftId: string): Promise<BackendRevision[]> {
  return apiGet<BackendRevision[]>(`/api/clients/${clientId}/drafts/${draftId}/revisions`)
}

async function fetchRevisionDetails(clientId: string, draftId: string): Promise<DraftRevision[]> {
  const revisions = await fetchRevisionMetadata(clientId, draftId)
  const details = await Promise.all(
    revisions.map((revision) =>
      apiGet<BackendRevisionDetail>(`/api/clients/${clientId}/drafts/${draftId}/revisions/${revision.id}`),
    ),
  )
  return details.map(mapRevision)
}

async function fetchExportJobs(clientId: string, draftId: string): Promise<BackendExportJob[]> {
  return apiGet<BackendExportJob[]>(`/api/clients/${clientId}/drafts/${draftId}/exports`)
}

async function fetchApprovals(clientId: string, draftId: string): Promise<BackendApprovalState[]> {
  return apiGet<BackendApprovalState[]>(`/api/clients/${clientId}/drafts/${draftId}/approvals`)
}

async function pollExportUntilReady(clientId: string, draftId: string, jobId: number): Promise<BackendExportJob> {
  for (let attempt = 0; attempt < 40; attempt += 1) {
    const job = await apiGet<BackendExportJob>(`/api/clients/${clientId}/drafts/${draftId}/exports/${jobId}`)
    if (job.status === 'completed') return job
    if (job.status === 'failed') {
      throw new Error(job.error ?? 'Export job failed')
    }
    await sleep(500)
  }

  throw new Error('Export job timed out before completion')
}

export function useDrafts(clientId: string) {
  return useQuery<DraftListItem[]>({
    queryKey: ['drafts', clientId],
    queryFn: async () => {
      const drafts = await apiGet<BackendDraft[]>(`/api/clients/${clientId}/drafts`)
      const revisionCounts = await Promise.all(
        drafts.map(async (draft) => (await fetchRevisionMetadata(clientId, String(draft.id))).length),
      )
      return drafts.map((draft, index) => mapDraftListItem(draft, revisionCounts[index]))
    },
    enabled: !!clientId,
    retry: false,
  })
}

export function useDraft(clientId: string, draftId: string) {
  return useQuery<Draft>({
    queryKey: ['draft', clientId, draftId],
    queryFn: async () => {
      const [draft, revisions, exports, approvals] = await Promise.all([
        apiGet<BackendDraftDetail>(`/api/clients/${clientId}/drafts/${draftId}`),
        fetchRevisionDetails(clientId, draftId),
        fetchExportJobs(clientId, draftId),
        fetchApprovals(clientId, draftId),
      ])
      return mapDraft(draft, revisions, exports, approvals)
    },
    enabled: !!clientId && !!draftId,
    retry: false,
  })
}

export function useDraftRevisions(clientId: string, draftId: string) {
  return useQuery<DraftRevision[]>({
    queryKey: ['draft-revisions', clientId, draftId],
    queryFn: () => fetchRevisionDetails(clientId, draftId),
    enabled: !!clientId && !!draftId,
    retry: false,
  })
}

export function useDraftRevision(clientId: string, draftId: string, revisionNumber: number) {
  return useQuery<DraftRevision>({
    queryKey: ['draft-revision', clientId, draftId, revisionNumber],
    queryFn: async () => {
      const revisions = await fetchRevisionMetadata(clientId, draftId)
      const matchedRevision = revisions.find((revision) => revision.revision_number === revisionNumber)
      if (!matchedRevision) {
        throw new Error(`Revision ${revisionNumber} not found`)
      }
      const detail = await apiGet<BackendRevisionDetail>(
        `/api/clients/${clientId}/drafts/${draftId}/revisions/${matchedRevision.id}`,
      )
      return mapRevision(detail)
    },
    enabled: !!clientId && !!draftId && revisionNumber >= 0,
    retry: false,
  })
}

export function useChatMessages(clientId: string, draftId: string) {
  return useQuery<ChatMessage[]>({
    queryKey: ['draft-chat', clientId, draftId],
    queryFn: async () => {
      const messages = await apiGet<BackendChatMessage[]>(`/api/clients/${clientId}/drafts/${draftId}/chat`)
      return messages.map((message) => ({
        message_id: message.id,
        draft_id: message.draft_id,
        role: message.role,
        content: message.content,
        section_id: message.section_id ?? undefined,
        created_at: message.created_at,
      }))
    },
    enabled: !!clientId && !!draftId,
    retry: false,
  })
}

export function useCreateDraft(clientId: string) {
  const qc = useQueryClient()

  return useMutation({
    mutationFn: async (payload: CreateDraftPayload) => {
      const templateVersionId = await resolveTemplateVersionId(payload.template_id)
      const draft = await apiPost<BackendDraft>(`/api/clients/${clientId}/drafts`, {
        title: payload.title,
        template_version_id: templateVersionId,
        period: payload.period,
        primary_locale: payload.locale,
        created_by: 'web',
      })
      // Compose is triggered separately from the draft studio — the LLM call
      // takes 15-30s which exceeds proxy/fetch timeouts when chained inline.
      return mapDraftListItem(draft, 0)
    },
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ['drafts', clientId] })
    },
  })
}

export function useComposeDraft(clientId: string, draftId: string) {
  const qc = useQueryClient()

  return useMutation({
    mutationFn: async (): Promise<BackendRevisionDetail> => {
      const accepted = await apiPost<ComposeJobAccepted>(
        `/api/clients/${clientId}/drafts/${draftId}/compose`,
      )
      // Poll until the background task finishes. isPending stays true on the
      // mutation for the entire duration — the Compose button keeps showing
      // "Composing…" and the hook's onSuccess still fires once with the
      // fully-composed revision.
      for (let attempt = 0; attempt < COMPOSE_POLL_MAX_ATTEMPTS; attempt += 1) {
        await sleep(COMPOSE_POLL_INTERVAL_MS)
        const status = await apiGet<ComposeJobStatus>(
          `/api/clients/${clientId}/drafts/${draftId}/compose/${accepted.job_id}`,
        )
        if (status.status === 'done' && status.revision) {
          return status.revision
        }
        if (status.status === 'failed') {
          throw new Error(status.error || 'Compose failed')
        }
      }
      throw new Error('Compose timed out after 4 minutes')
    },
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ['draft', clientId, draftId] })
      qc.invalidateQueries({ queryKey: ['drafts', clientId] })
      qc.invalidateQueries({ queryKey: ['draft-revisions', clientId, draftId] })
    },
  })
}

export function useTranslateDraft(clientId: string, draftId: string) {
  const qc = useQueryClient()

  return useMutation({
    mutationFn: (locale: string) =>
      apiPost<BackendRevisionDetail>(
        `/api/clients/${clientId}/drafts/${draftId}/translate?target_locale=${encodeURIComponent(locale)}`,
      ),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ['draft', clientId, draftId] })
      qc.invalidateQueries({ queryKey: ['drafts', clientId] })
      qc.invalidateQueries({ queryKey: ['draft-revisions', clientId, draftId] })
    },
  })
}

export function useUpdateDraftSection(clientId: string, draftId: string) {
  const qc = useQueryClient()

  return useMutation({
    mutationFn: ({ sectionId, payload }: { sectionId: string; payload: SectionEditPayload }) =>
      apiPut<DraftSection>(`/api/clients/${clientId}/drafts/${draftId}/sections/${sectionId}`, payload),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ['draft', clientId, draftId] })
      qc.invalidateQueries({ queryKey: ['drafts', clientId] })
      qc.invalidateQueries({ queryKey: ['draft-revisions', clientId, draftId] })
    },
  })
}

export function useSendChatMessage(clientId: string, draftId: string) {
  const qc = useQueryClient()

  return useMutation({
    mutationFn: async (payload: ChatMessagePayload) => {
      const response = await apiPost<BackendChatMessage>(`/api/clients/${clientId}/drafts/${draftId}/chat`, {
        role: 'user',
        content: payload.content,
        section_id: payload.section_id,
      })
      return {
        message_id: response.id,
        draft_id: response.draft_id,
        role: response.role,
        content: response.content,
        section_id: response.section_id ?? undefined,
        created_at: response.created_at,
      } satisfies ChatMessage
    },
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ['draft-chat', clientId, draftId] })
      qc.invalidateQueries({ queryKey: ['draft', clientId, draftId] })
      qc.invalidateQueries({ queryKey: ['draft-revisions', clientId, draftId] })
      qc.invalidateQueries({ queryKey: ['drafts', clientId] })
    },
  })
}

export function useUpdateDraftStatus(clientId: string, draftId: string) {
  const qc = useQueryClient()

  return useMutation({
    mutationFn: async (status: DraftStatus) => {
      if (status === 'archived') {
        await apiDelete(`/api/clients/${clientId}/drafts/${draftId}`)
        return null
      }

      return apiPost<BackendDraft>(
        `/api/clients/${clientId}/drafts/${draftId}/transition?target_status=${encodeURIComponent(status)}`,
      )
    },
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ['draft', clientId, draftId] })
      qc.invalidateQueries({ queryKey: ['drafts', clientId] })
      qc.invalidateQueries({ queryKey: ['draft-revisions', clientId, draftId] })
    },
  })
}

export function useApprovalAction(clientId: string, draftId: string) {
  const qc = useQueryClient()

  return useMutation({
    mutationFn: (payload: ApprovalActionPayload) => {
      if (!payload.section_id) {
        throw new Error('A section must be selected before approving or rejecting')
      }

      const status =
        payload.action === 'approve'
          ? 'approved'
          : payload.action === 'reject'
            ? 'rejected'
            : 'needs_revision'

      return apiPost<BackendApprovalState>(`/api/clients/${clientId}/drafts/${draftId}/approve`, {
        section_id: payload.section_id,
        status,
        reviewer: 'web-reviewer',
        comment: payload.note,
      })
    },
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ['draft', clientId, draftId] })
      qc.invalidateQueries({ queryKey: ['drafts', clientId] })
      qc.invalidateQueries({ queryKey: ['draft-revisions', clientId, draftId] })
    },
  })
}

export function useDeleteDraft(clientId: string) {
  const qc = useQueryClient()

  return useMutation({
    mutationFn: (draftId: string | number) => apiDelete(`/api/clients/${clientId}/drafts/${draftId}`),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ['drafts', clientId] })
    },
  })
}

export function useExportDraft(clientId: string, draftId: string) {
  return useMutation({
    mutationFn: async (format: 'pdf' | 'docx' | 'json') => {
      if (format === 'json') {
        const draft = await apiGet<BackendDraftDetail>(`/api/clients/${clientId}/drafts/${draftId}`)
        const blob = new Blob([JSON.stringify(draft, null, 2)], { type: 'application/json' })
        return {
          url: URL.createObjectURL(blob),
          filename: `${draft.title.toLowerCase().replace(/[^a-z0-9]+/g, '-') || `draft-${draftId}`}.json`,
        } satisfies ExportResult
      }

      let job = await apiPost<BackendExportJob>(`/api/clients/${clientId}/drafts/${draftId}/exports`, {
        format,
        requested_by: 'web',
      })

      if (job.status !== 'completed') {
        job = await pollExportUntilReady(clientId, draftId, job.id)
      }

      const file = await apiGetFile(`/api/clients/${clientId}/drafts/${draftId}/exports/${job.id}/download`)
      const fallbackFilename = `${format === 'pdf' ? 'report' : 'draft'}.${format}`
      const filename = file.filename.toLowerCase().endsWith(`.${format}`)
        ? file.filename
        : fallbackFilename

      return {
        url: URL.createObjectURL(file.blob),
        filename,
      } satisfies ExportResult
    },
  })
}
