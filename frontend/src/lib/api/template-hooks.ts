'use client'

import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { apiDelete, apiGet, apiPost, apiPut } from './client'

type ReportType = 'monthly' | 'quarterly' | 'custom'

interface BackendTemplate {
  id: number
  name: string
  description?: string | null
  industry_profile_id?: number | null
  base_locale: string
  current_version: number
  is_published: boolean
  created_by?: string | null
  created_at: string
  updated_at: string
}

interface BackendTemplateVersion {
  id: number
  template_id: number
  version_number: number
  sections_json: Array<Record<string, unknown>>
  theme_tokens: Record<string, string>
  changelog_note?: string | null
  created_by?: string | null
  created_at: string
}

interface BackendTemplateOverride {
  client_id: string
  template_version_id: number
  overrides: Record<string, unknown>
  is_active?: boolean
}

export interface TemplateSection {
  section_id: string
  heading: string
  order: number
  prompt_template: string
  chart_types: string[]
  max_tokens: number
  required: boolean
}

export interface TemplateVersion {
  version_id: number
  template_id: number
  version_number: number
  sections: TemplateSection[]
  theme_tokens: Record<string, string>
  created_at: string
  created_by?: string
  changelog?: string
}

export interface Template {
  template_id: number
  display_name: string
  description: string
  industry_tags: string[]
  report_type: ReportType
  theme_tokens: Record<string, string>
  current_version: TemplateVersion
  version_count: number
  created_at: string
  updated_at: string
  base_locale: string
  is_system: boolean
  is_published: boolean
}

export interface ClientTemplateOverride {
  client_id: string
  template_id: number
  template_version_id: number
  overrides: Record<string, unknown>
  is_active: boolean
}

export interface CreateTemplatePayload {
  display_name: string
  description: string
  industry_tags?: string[]
  report_type?: ReportType
  base_locale?: string
  theme_tokens?: Record<string, string>
  sections?: Array<Omit<TemplateSection, 'section_id'> & { section_id?: string }>
}

export interface UpdateTemplateSectionsPayload {
  sections: TemplateSection[]
  changelog?: string
}

const DEFAULT_THEME_TOKENS: Record<string, string> = {
  '--brand-primary': '#1a1a2e',
  '--brand-accent': '#4f46e5',
  '--brand-accent-secondary': '#7c3aed',
  '--heading-font': 'Fraunces, serif',
  '--body-font': 'Inter, sans-serif',
  '--report-bg': '#ffffff',
  '--report-text': '#1a1a2e',
}

function inferReportType(name: string, description?: string | null): ReportType {
  const haystack = `${name} ${description ?? ''}`.toLowerCase()
  if (haystack.includes('monthly') || haystack.includes('month')) return 'monthly'
  if (haystack.includes('quarterly') || haystack.includes('quarter')) return 'quarterly'
  return 'custom'
}

function inferIndustryTags(template: BackendTemplate): string[] {
  if (!template.industry_profile_id) return []
  return [`industry_${template.industry_profile_id}`]
}

function normalizeSection(raw: Record<string, unknown>, index: number): TemplateSection {
  const chartTypes = Array.isArray(raw.chart_types)
    ? raw.chart_types.filter((value): value is string => typeof value === 'string')
    : []

  return {
    section_id: typeof raw.section_id === 'string' ? raw.section_id : `section_${index + 1}`,
    heading: typeof raw.heading === 'string' ? raw.heading : `Section ${index + 1}`,
    order: typeof raw.order === 'number' ? raw.order : index,
    prompt_template: typeof raw.prompt_template === 'string' ? raw.prompt_template : '',
    chart_types: chartTypes,
    max_tokens: typeof raw.max_tokens === 'number' ? raw.max_tokens : 1000,
    required: Boolean(raw.required),
  }
}

function defaultSections(): TemplateSection[] {
  return [
    {
      section_id: 'executive_summary',
      heading: 'Executive Summary',
      order: 0,
      prompt_template: 'Summarize the most important developments for the reporting period.',
      chart_types: [],
      max_tokens: 900,
      required: true,
    },
    {
      section_id: 'regulatory_changes',
      heading: 'Regulatory Changes',
      order: 1,
      prompt_template: 'Explain the most relevant regulatory changes and why they matter for this client.',
      chart_types: ['topic_distribution'],
      max_tokens: 1200,
      required: true,
    },
    {
      section_id: 'actions',
      heading: 'Recommended Actions',
      order: 2,
      prompt_template: 'List the recommended next steps, deadlines, and owners.',
      chart_types: [],
      max_tokens: 800,
      required: false,
    },
  ]
}

function mapVersion(raw: BackendTemplateVersion): TemplateVersion {
  return {
    version_id: raw.id,
    template_id: raw.template_id,
    version_number: raw.version_number,
    sections: (raw.sections_json ?? []).map((section, index) => normalizeSection(section, index)),
    theme_tokens: { ...DEFAULT_THEME_TOKENS, ...(raw.theme_tokens ?? {}) },
    created_at: raw.created_at,
    created_by: raw.created_by ?? undefined,
    changelog: raw.changelog_note ?? undefined,
  }
}

function emptyVersion(templateId: number, versionNumber: number, baseLocale: string): TemplateVersion {
  return {
    version_id: 0,
    template_id: templateId,
    version_number: versionNumber,
    sections: defaultSections().map((section) => ({
      ...section,
      prompt_template: `${section.prompt_template} (${baseLocale.toUpperCase()})`,
    })),
    theme_tokens: { ...DEFAULT_THEME_TOKENS },
    created_at: new Date().toISOString(),
  }
}

function mapTemplate(raw: BackendTemplate, versions: BackendTemplateVersion[]): Template {
  const mappedVersions = versions.map(mapVersion)
  const currentVersion =
    mappedVersions.find((version) => version.version_number === raw.current_version) ??
    mappedVersions[mappedVersions.length - 1] ??
    emptyVersion(raw.id, raw.current_version || 1, raw.base_locale)

  return {
    template_id: raw.id,
    display_name: raw.name,
    description: raw.description ?? '',
    industry_tags: inferIndustryTags(raw),
    report_type: inferReportType(raw.name, raw.description),
    theme_tokens: currentVersion.theme_tokens,
    current_version: currentVersion,
    version_count: mappedVersions.length || 1,
    created_at: raw.created_at,
    updated_at: raw.updated_at,
    base_locale: raw.base_locale,
    is_system: false,
    is_published: raw.is_published,
  }
}

async function fetchTemplateVersions(templateId: number | string): Promise<BackendTemplateVersion[]> {
  return apiGet<BackendTemplateVersion[]>(`/api/templates/${templateId}/versions`)
}

async function fetchTemplateDetail(templateId: number | string): Promise<Template> {
  const [template, versions] = await Promise.all([
    apiGet<BackendTemplate>(`/api/templates/${templateId}`),
    fetchTemplateVersions(templateId),
  ])
  return mapTemplate(template, versions)
}

function sanitizeSections(
  sections?: Array<Omit<TemplateSection, 'section_id'> & { section_id?: string }>,
): TemplateSection[] {
  const base = sections && sections.length > 0
    ? sections
    : defaultSections()

  return base.map((section, index) => ({
    section_id: section.section_id ?? `section_${index + 1}`,
    heading: section.heading,
    order: typeof section.order === 'number' ? section.order : index,
    prompt_template: section.prompt_template,
    chart_types: section.chart_types ?? [],
    max_tokens: section.max_tokens ?? 1000,
    required: Boolean(section.required),
  }))
}

async function resolveTemplateVersionId(templateId: number | string): Promise<number | undefined> {
  const [template, versions] = await Promise.all([
    apiGet<BackendTemplate>(`/api/templates/${templateId}`),
    fetchTemplateVersions(templateId),
  ])
  return versions.find((version) => version.version_number === template.current_version)?.id
}

export function useTemplates() {
  return useQuery<Template[]>({
    queryKey: ['templates'],
    queryFn: async () => {
      const templates = await apiGet<BackendTemplate[]>('/api/templates')
      const versions = await Promise.all(
        templates.map((template) => fetchTemplateVersions(template.id)),
      )
      return templates.map((template, index) => mapTemplate(template, versions[index]))
    },
    retry: false,
  })
}

export function useTemplate(templateId: string) {
  return useQuery<Template>({
    queryKey: ['template', templateId],
    queryFn: () => fetchTemplateDetail(templateId),
    enabled: !!templateId,
    retry: false,
  })
}

export function useTemplateVersions(templateId: string) {
  return useQuery<TemplateVersion[]>({
    queryKey: ['template-versions', templateId],
    queryFn: async () => (await fetchTemplateVersions(templateId)).map(mapVersion),
    enabled: !!templateId,
    retry: false,
  })
}

export function useCreateTemplate() {
  const qc = useQueryClient()

  return useMutation({
    mutationFn: async (payload: CreateTemplatePayload) => {
      const template = await apiPost<BackendTemplate>('/api/templates', {
        name: payload.display_name,
        description: payload.description,
        base_locale: payload.base_locale ?? 'en',
      })

      const sections = sanitizeSections(payload.sections)
      await apiPost<BackendTemplateVersion>(`/api/templates/${template.id}/versions`, {
        sections_json: sections,
        theme_tokens: { ...DEFAULT_THEME_TOKENS, ...(payload.theme_tokens ?? {}) },
        changelog_note: 'Initial template version',
        created_by: 'web',
      })

      return fetchTemplateDetail(template.id)
    },
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ['templates'] })
    },
  })
}

export function useUpdateTemplateSections(templateId: string) {
  const qc = useQueryClient()

  return useMutation({
    mutationFn: async (payload: UpdateTemplateSectionsPayload) => {
      const response = await apiPut<BackendTemplateVersion>(`/api/templates/${templateId}/sections`, {
        sections: payload.sections,
        changelog: payload.changelog,
        created_by: 'web',
      })
      return mapVersion(response)
    },
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ['template', templateId] })
      qc.invalidateQueries({ queryKey: ['template-versions', templateId] })
      qc.invalidateQueries({ queryKey: ['templates'] })
    },
  })
}

export function useUpdateTemplateTheme(templateId: string) {
  const qc = useQueryClient()

  return useMutation({
    mutationFn: async (tokens: Record<string, string>) => {
      await apiPut<BackendTemplate>(`/api/templates/${templateId}/theme`, {
        tokens,
        changelog: 'Theme update',
        created_by: 'web',
      })
      return fetchTemplateDetail(templateId)
    },
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ['template', templateId] })
      qc.invalidateQueries({ queryKey: ['template-versions', templateId] })
      qc.invalidateQueries({ queryKey: ['templates'] })
    },
  })
}

export function useDeleteTemplate() {
  const qc = useQueryClient()

  return useMutation({
    mutationFn: (templateId: string | number) => apiDelete(`/api/templates/${templateId}`),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ['templates'] })
    },
  })
}

export function useClientTemplateOverride(clientId: string, templateId: string) {
  return useQuery<ClientTemplateOverride>({
    queryKey: ['template-override', clientId, templateId],
    queryFn: async () => {
      const versionId = await resolveTemplateVersionId(templateId)
      if (!versionId) {
        return {
          client_id: clientId,
          template_id: Number(templateId),
          template_version_id: 0,
          overrides: {},
          is_active: false,
        }
      }
      const response = await apiGet<BackendTemplateOverride>(
        `/api/templates/${templateId}/versions/${versionId}/overrides/${clientId}`,
      )
      return {
        client_id: response.client_id,
        template_id: Number(templateId),
        template_version_id: response.template_version_id,
        overrides: response.overrides ?? {},
        is_active: Boolean(response.is_active),
      }
    },
    enabled: !!clientId && !!templateId,
    retry: false,
  })
}

export function useUpsertClientTemplateOverride(clientId: string, templateId: string) {
  const qc = useQueryClient()

  return useMutation({
    mutationFn: async (payload: Partial<ClientTemplateOverride>) => {
      const versionId = await resolveTemplateVersionId(templateId)
      if (!versionId) {
        throw new Error('Template has no current version to override')
      }

      const overrides = payload.overrides ?? {}
      const response = await apiPut<BackendTemplateOverride>(
        `/api/templates/${templateId}/versions/${versionId}/overrides/${clientId}`,
        overrides,
      )

      return {
        client_id: response.client_id,
        template_id: Number(templateId),
        template_version_id: response.template_version_id,
        overrides: response.overrides ?? {},
        is_active: Boolean(response.is_active),
      }
    },
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ['template-override', clientId, templateId] })
    },
  })
}
