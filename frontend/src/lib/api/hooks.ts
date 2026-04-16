'use client'

import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { apiGet, apiPost, apiPut, apiPostFile, apiDelete } from './client'

export interface HealthResponse {
  status: string
  last_screening_date: string | null
  config_status: string
  data_dir_exists: boolean
  changelog_count: number
  state_count: number
}

export interface TopicChangeStatus {
  changed_since_last: boolean
  level: string | null
  changes_detected: number
}

export interface ChangeEntry {
  regulation_id: string
  title: string
  topic: string
  change_type: string
  severity: string
  summary: string
  action_required: string
  current_status: string
  effective_date: string | null
  enforcement_date: string | null
  changes: Array<{
    field: string
    old: string
    new: string
    description: string
  }>
}

export interface ChangelogResponse {
  screening_period: string
  generated_date: string
  previous_period: string | null
  executive_summary: string
  total_regulations_tracked: number
  total_changes_detected: number
  topic_change_statuses: Record<string, TopicChangeStatus>
  new_regulations: ChangeEntry[]
  status_changes: ChangeEntry[]
  content_updates: ChangeEntry[]
  timeline_changes?: ChangeEntry[]
  metadata_updates?: ChangeEntry[]
  ended_regulations?: ChangeEntry[]
  carried_forward?: ChangeEntry[]
  critical_actions: ChangeEntry[]
}

export interface PeriodListResponse {
  periods: string[]
}

export function useClients() {
  return useQuery<unknown>({
    queryKey: ['clients'],
    queryFn: () => apiGet('/api/clients'),
    retry: false,
  })
}

export function useHealth() {
  return useQuery<HealthResponse>({
    queryKey: ['health'],
    queryFn: () => apiGet<HealthResponse>('/api/health'),
    refetchInterval: 30000,
    retry: false,
  })
}

export function useChangelogs(clientId: string) {
  return useQuery<PeriodListResponse>({
    queryKey: ['changelogs', clientId],
    queryFn: () => apiGet<PeriodListResponse>(`/api/clients/${clientId}/changelogs`),
    enabled: !!clientId,
    retry: false,
  })
}

export function useChangelog(clientId: string, period: string) {
  return useQuery<ChangelogResponse>({
    queryKey: ['changelog', clientId, period],
    queryFn: () => apiGet<ChangelogResponse>(`/api/clients/${clientId}/changelogs/${period}`),
    enabled: !!clientId && !!period,
    retry: false,
  })
}

export function useLatestChangelog(clientId: string) {
  const periodsQuery = useChangelogs(clientId)
  const latestPeriod = periodsQuery.data?.periods?.at(-1) ?? ''

  const changelogQuery = useChangelog(clientId, latestPeriod)

  return {
    data: changelogQuery.data,
    isLoading: periodsQuery.isLoading || (!!latestPeriod && changelogQuery.isLoading),
    error: periodsQuery.error ?? changelogQuery.error,
    latestPeriod,
  }
}

// Audit

export interface AuditFinding {
  severity: string  // uppercase from API: "CRITICAL" | "HIGH" | "MEDIUM" | "LOW"
  category: string
  location: string
  message: string
  evidence?: string
  gap_type?: string  // "regulatory" | "data_quality" | "code_health"
}

export interface AuditResponse {
  findings: AuditFinding[]
}

export function useAudit(clientId: string) {
  return useQuery<AuditResponse>({
    queryKey: ['audit', clientId],
    queryFn: () => apiGet<AuditResponse>(`/api/clients/${clientId}/audit`),
    enabled: !!clientId,
    retry: false,
  })
}

// Report generation

export interface ReportBlob {
  blobUrl: string
  filename: string
}

export function useGenerateMonthlyReport(clientId: string) {
  return useMutation<ReportBlob, Error, { period: string; preferences?: ReportPreferences }>({
    mutationFn: async ({ period, preferences }) => {
      const result = await apiPostFile(`/api/clients/${clientId}/reports/monthly`, { period, ...preferences })
      return {
        blobUrl: URL.createObjectURL(result.blob),
        filename: result.filename,
      }
    },
  })
}

export function useGenerateQuarterlyReport(clientId: string) {
  return useMutation<ReportBlob, Error, { quarter: number; year: number; preferences?: ReportPreferences }>({
    mutationFn: async ({ quarter, year, preferences }) => {
      const result = await apiPostFile(`/api/clients/${clientId}/reports/quarterly`, { quarter, year, ...preferences })
      return {
        blobUrl: URL.createObjectURL(result.blob),
        filename: result.filename,
      }
    },
  })
}

// Client CRUD

export interface FacilityConfig {
  name: string
  jurisdiction: string
}

export interface SourceConfig {
  id: string
  display_name: string
  url?: string
  frequency: string
  source_type: string
}

export interface Thresholds {
  critical_enforcement_window_days: number
  min_confidence: number
  min_sources_per_entry: number
}

export interface ReportPreferences {
  tone: string
  depth: string
  chart_mix: string[]
  section_order: string[]
}

export interface ClientConfig {
  client_id: string
  display_name: string
  facilities: FacilityConfig[]
  allowed_countries: string[]
  required_topics: string[]
  branding?: { primary_color: string; accent_color: string }
  sources: SourceConfig[]
  thresholds: Thresholds
  report_preferences: ReportPreferences
}

export interface CreateClientPayload {
  client_id: string
  display_name: string
  facilities: FacilityConfig[]
  allowed_countries: string[]
  required_topics: string[]
}

export function useClient(clientId: string) {
  return useQuery<ClientConfig>({
    queryKey: ['client', clientId],
    queryFn: () => apiGet<ClientConfig>(`/api/clients/${clientId}`),
    enabled: !!clientId,
    retry: false,
  })
}

export function useUpdateClient(clientId: string) {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: (updates: Partial<ClientConfig>) =>
      apiPut<ClientConfig>(`/api/clients/${clientId}`, updates),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['client', clientId] })
      queryClient.invalidateQueries({ queryKey: ['clients'] })
    },
  })
}

export function useCreateClient() {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: (payload: CreateClientPayload) =>
      apiPost<ClientConfig>('/api/clients', payload),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['clients'] })
    },
  })
}

// Sources

export function useSources(clientId: string) {
  return useQuery<SourceConfig[]>({
    queryKey: ['sources', clientId],
    queryFn: () => apiGet<SourceConfig[]>(`/api/clients/${clientId}/sources`),
    enabled: !!clientId,
    retry: false,
  })
}

export function useUpdateSources(clientId: string) {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: (sources: SourceConfig[]) =>
      apiPut<SourceConfig[]>(`/api/clients/${clientId}/sources`, sources),
    onSuccess: (sources) => {
      queryClient.setQueryData(['sources', clientId], sources)
      queryClient.invalidateQueries({ queryKey: ['sources', clientId] })
      queryClient.invalidateQueries({ queryKey: ['client', clientId] })
      queryClient.invalidateQueries({ queryKey: ['clients'] })
    },
  })
}

// Thresholds

export function useThresholds(clientId: string) {
  return useQuery<Thresholds>({
    queryKey: ['thresholds', clientId],
    queryFn: () => apiGet<Thresholds>(`/api/clients/${clientId}/thresholds`),
    enabled: !!clientId,
    retry: false,
  })
}

export function useUpdateThresholds(clientId: string) {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: (thresholds: Thresholds) =>
      apiPut<Thresholds>(`/api/clients/${clientId}/thresholds`, thresholds),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['thresholds', clientId] })
      queryClient.invalidateQueries({ queryKey: ['client', clientId] })
      queryClient.invalidateQueries({ queryKey: ['clients'] })
    },
  })
}

// Evidence

export interface EvidenceRecord {
  evidence_id: string
  client_id: string
  source_id: string
  source_name: string
  url: string
  access_date: string
  document_title: string
  snippet: string
  hash: string
  attached_by: string
  confidence: number
  topic: string
  related_regulation_id: string
}

export function useEvidence(clientId: string) {
  return useQuery({
    queryKey: ['evidence', clientId],
    queryFn: () => apiGet<{ evidence: EvidenceRecord[]; total: number }>(`/api/clients/${clientId}/evidence`),
    enabled: !!clientId,
    retry: false,
  })
}

export function useEvidenceRecord(clientId: string, evidenceId: string) {
  return useQuery({
    queryKey: ['evidence', clientId, evidenceId],
    queryFn: () => apiGet<EvidenceRecord>(`/api/clients/${clientId}/evidence/${evidenceId}`),
    enabled: !!clientId && !!evidenceId,
    retry: false,
  })
}

export function useCreateEvidence(clientId: string) {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: (body: Partial<EvidenceRecord> & { url: string }) =>
      apiPost<EvidenceRecord>(`/api/clients/${clientId}/evidence`, body),
    onSuccess: () => qc.invalidateQueries({ queryKey: ['evidence', clientId] }),
  })
}

export function useDeleteEvidence(clientId: string) {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: (evidenceId: string) =>
      apiDelete(`/api/clients/${clientId}/evidence/${evidenceId}`),
    onSuccess: () => qc.invalidateQueries({ queryKey: ['evidence', clientId] }),
  })
}

export function useUploadEvidence(clientId: string) {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: async (formData: FormData) => {
      const res = await fetch(`/api/clients/${clientId}/evidence/upload`, {
        method: 'POST',
        body: formData,
      })
      if (!res.ok) {
        const text = await res.text()
        throw new Error(text || `Upload failed: ${res.status}`)
      }
      return res.json() as Promise<EvidenceRecord>
    },
    onSuccess: () => qc.invalidateQueries({ queryKey: ['evidence', clientId] }),
  })
}

// Screening

export function useRunScreening(clientId: string) {
  const queryClient = useQueryClient()
  return useMutation<{ period: string; status: string }, Error, { period: string }>({
    mutationFn: ({ period }) =>
      apiPost<{ period: string; status: string }>(`/api/clients/${clientId}/screening/run`, { period }),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['changelogs', clientId] })
    },
  })
}

// Report preferences

export function usePreferences(clientId: string) {
  return useQuery<ReportPreferences>({
    queryKey: ['preferences', clientId],
    queryFn: () => apiGet<ReportPreferences>(`/api/clients/${clientId}/preferences`),
    enabled: !!clientId,
    retry: false,
  })
}

export function useUpdatePreferences(clientId: string) {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: (preferences: ReportPreferences) =>
      apiPut<ReportPreferences>(`/api/clients/${clientId}/preferences`, preferences),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['preferences', clientId] })
      queryClient.invalidateQueries({ queryKey: ['client', clientId] })
      queryClient.invalidateQueries({ queryKey: ['clients'] })
    },
  })
}

// ── Locale settings ──────────────────────────────────────────────────────────

export interface LocaleOption {
  code: string
  name: string
  native_name: string
  is_active: boolean
}

export interface ClientLocaleSettings {
  client_id: string
  primary_locale: string
  enabled_locales: string[]
  fallback_locale: string
  updated_at?: string
}

export function useLocales() {
  return useQuery<LocaleOption[]>({
    queryKey: ['locales'],
    queryFn: () => apiGet<LocaleOption[]>('/api/locales'),
    retry: false,
  })
}

export function useClientLocaleSettings(clientId: string) {
  return useQuery<ClientLocaleSettings>({
    queryKey: ['locale-settings', clientId],
    queryFn: () => apiGet<ClientLocaleSettings>(`/api/clients/${clientId}/locale-settings`),
    enabled: !!clientId,
    retry: false,
  })
}

export function useUpdateClientLocaleSettings(clientId: string) {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: (settings: Partial<ClientLocaleSettings>) =>
      apiPut<ClientLocaleSettings>(`/api/clients/${clientId}/locale-settings`, settings),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['locale-settings', clientId] })
    },
  })
}
