'use client'

import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { apiDelete, apiGet, apiPost, apiPut } from './client'

export type KeywordMatchMode = 'exact' | 'fuzzy' | 'regex'
export type ProposalAction = 'approve' | 'reject' | 'pause'
export type ProposalStatus = 'pending' | 'approved' | 'rejected' | 'paused'

interface BackendKeywordRule {
  id: number
  client_id: string
  phrase: string
  locale: string
  weight: number
  category?: string | null
  is_active: boolean
  created_at: string
  updated_at: string
}

interface BackendSourceProposal {
  id: number
  client_id: string
  url: string
  title?: string | null
  publisher?: string | null
  rationale?: string | null
  status: ProposalStatus
  proposed_by: string
  reviewed_by?: string | null
  reviewed_at?: string | null
  created_at: string
  updated_at: string
}

export interface KeywordRule {
  rule_id: number
  client_id: string
  bundle_name: string
  keywords: string[]
  match_mode: KeywordMatchMode
  topics: string[]
  jurisdictions: string[]
  weight: number
  enabled: boolean
  created_at: string
  updated_at: string
}

export interface KeywordBundle {
  bundle_name: string
  rules: KeywordRule[]
  rule_count: number
  active_count: number
}

export interface SourceProposal {
  proposal_id: number
  client_id: string
  source_id: string
  source_name: string
  url: string
  proposed_at: string
  status: ProposalStatus
  confidence: number
  snippet: string
  topic: string
  jurisdiction: string
  review_note?: string
  reviewed_by?: string
  reviewed_at?: string
}

export interface ImpactPreview {
  proposal_id: number
  estimated_matches: number
  sample_regulations: Array<{
    regulation_id: string
    title: string
    topic: string
  }>
  coverage_delta: number
}

export interface CreateKeywordRulePayload {
  bundle_name: string
  keywords: string[]
  match_mode: KeywordMatchMode
  topics: string[]
  jurisdictions: string[]
  weight?: number
}

export interface UpdateKeywordRulePayload {
  keywords?: string[]
  match_mode?: KeywordMatchMode
  topics?: string[]
  jurisdictions?: string[]
  weight?: number
  enabled?: boolean
}

function normalizeBundleName(category?: string | null, locale?: string): string {
  if (category && category.trim()) return category.trim().toLowerCase().replace(/\s+/g, '_')
  if (locale) return `locale_${locale.toLowerCase()}`
  return 'general'
}

function mapKeywordRule(rule: BackendKeywordRule): KeywordRule {
  const bundleName = normalizeBundleName(rule.category, rule.locale)
  return {
    rule_id: rule.id,
    client_id: rule.client_id,
    bundle_name: bundleName,
    keywords: [rule.phrase],
    match_mode: 'exact',
    topics: rule.category ? [rule.category] : [],
    jurisdictions: [rule.locale.toUpperCase()],
    weight: rule.weight,
    enabled: rule.is_active,
    created_at: rule.created_at,
    updated_at: rule.updated_at,
  }
}

function groupKeywordBundles(rules: KeywordRule[]): KeywordBundle[] {
  const bundles = new Map<string, KeywordBundle>()

  for (const rule of rules) {
    const bundle = bundles.get(rule.bundle_name) ?? {
      bundle_name: rule.bundle_name,
      rules: [],
      rule_count: 0,
      active_count: 0,
    }
    bundle.rules.push(rule)
    bundle.rule_count += 1
    if (rule.enabled) bundle.active_count += 1
    bundles.set(rule.bundle_name, bundle)
  }

  return Array.from(bundles.values()).sort((a, b) => a.bundle_name.localeCompare(b.bundle_name))
}

function inferSourceName(proposal: BackendSourceProposal): string {
  if (proposal.title?.trim()) return proposal.title.trim()
  try {
    return new URL(proposal.url).hostname
  } catch {
    return proposal.url
  }
}

function inferJurisdiction(url: string): string {
  try {
    const hostname = new URL(url).hostname.toLowerCase()
    if (hostname.endsWith('.eu')) return 'EU'
    if (hostname.endsWith('.de')) return 'DE'
    if (hostname.endsWith('.fr')) return 'FR'
    if (hostname.endsWith('.it')) return 'IT'
    if (hostname.endsWith('.es')) return 'ES'
    return hostname.split('.').pop()?.toUpperCase() ?? 'EU'
  } catch {
    return 'EU'
  }
}

function mapSourceProposal(proposal: BackendSourceProposal): SourceProposal {
  return {
    proposal_id: proposal.id,
    client_id: proposal.client_id,
    source_id: String(proposal.id),
    source_name: inferSourceName(proposal),
    url: proposal.url,
    proposed_at: proposal.created_at,
    status: proposal.status,
    confidence: proposal.rationale ? 0.82 : 0.65,
    snippet: proposal.rationale?.trim() || 'Suggested for broader regulatory coverage.',
    topic: proposal.publisher?.trim() || 'Regulatory source',
    jurisdiction: inferJurisdiction(proposal.url),
    review_note: undefined,
    reviewed_by: proposal.reviewed_by ?? undefined,
    reviewed_at: proposal.reviewed_at ?? undefined,
  }
}

async function fetchKeywordRules(clientId: string): Promise<KeywordRule[]> {
  const response = await apiGet<BackendKeywordRule[]>(`/api/clients/${clientId}/keywords`)
  return response.map(mapKeywordRule)
}

export function useKeywordBundles(clientId: string) {
  return useQuery<KeywordBundle[]>({
    queryKey: ['keyword-bundles', clientId],
    queryFn: async () => groupKeywordBundles(await fetchKeywordRules(clientId)),
    enabled: !!clientId,
    retry: false,
  })
}

export function useKeywordRules(clientId: string, bundleName?: string) {
  return useQuery<KeywordRule[]>({
    queryKey: ['keyword-rules', clientId, bundleName ?? 'all'],
    queryFn: async () => {
      const rules = await fetchKeywordRules(clientId)
      return bundleName ? rules.filter((rule) => rule.bundle_name === bundleName) : rules
    },
    enabled: !!clientId,
    retry: false,
  })
}

export function useCreateKeywordRule(clientId: string) {
  const qc = useQueryClient()

  return useMutation({
    mutationFn: async (payload: CreateKeywordRulePayload) => {
      const created = await Promise.all(
        payload.keywords.map((keyword) =>
          apiPost<BackendKeywordRule>(`/api/clients/${clientId}/keywords`, {
            phrase: keyword,
            locale: payload.jurisdictions[0]?.toLowerCase() || 'en',
            weight: payload.weight ?? 1,
            category: payload.bundle_name,
          }),
        ),
      )
      return mapKeywordRule(created[0])
    },
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ['keyword-rules', clientId] })
      qc.invalidateQueries({ queryKey: ['keyword-bundles', clientId] })
    },
  })
}

export function useUpdateKeywordRule(clientId: string) {
  const qc = useQueryClient()

  return useMutation({
    mutationFn: async ({
      ruleId,
      payload,
    }: {
      ruleId: string | number
      payload: UpdateKeywordRulePayload
    }) => {
      if (payload.enabled === false) {
        await apiDelete(`/api/clients/${clientId}/keywords/${ruleId}`)
        return null
      }

      const current = await apiGet<BackendKeywordRule>(`/api/clients/${clientId}/keywords/${ruleId}`)
      const updated = await apiPut<BackendKeywordRule>(`/api/clients/${clientId}/keywords/${ruleId}`, {
        phrase: payload.keywords?.[0] ?? current.phrase,
        locale: payload.jurisdictions?.[0]?.toLowerCase() ?? current.locale,
        weight: payload.weight ?? current.weight,
        category: payload.topics?.[0] ?? current.category,
      })
      return mapKeywordRule(updated)
    },
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ['keyword-rules', clientId] })
      qc.invalidateQueries({ queryKey: ['keyword-bundles', clientId] })
    },
  })
}

export function useDeleteKeywordRule(clientId: string) {
  const qc = useQueryClient()

  return useMutation({
    mutationFn: (ruleId: string | number) => apiDelete(`/api/clients/${clientId}/keywords/${ruleId}`),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ['keyword-rules', clientId] })
      qc.invalidateQueries({ queryKey: ['keyword-bundles', clientId] })
    },
  })
}

export function useSourceProposals(clientId: string) {
  return useQuery<SourceProposal[]>({
    queryKey: ['source-proposals', clientId],
    queryFn: async () => {
      const proposals = await apiGet<BackendSourceProposal[]>(`/api/clients/${clientId}/source-proposals`)
      return proposals.map(mapSourceProposal)
    },
    enabled: !!clientId,
    retry: false,
  })
}

export function useSuggestSourceProposals(clientId: string) {
  const qc = useQueryClient()

  return useMutation({
    mutationFn: async () => {
      const proposals = await apiPost<BackendSourceProposal[]>(`/api/clients/${clientId}/source-proposals/suggest`)
      return proposals.map(mapSourceProposal)
    },
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ['source-proposals', clientId] })
    },
  })
}

export function useProposalImpact(clientId: string, proposalId: string | number) {
  return useQuery<ImpactPreview>({
    queryKey: ['proposal-impact', clientId, proposalId],
    queryFn: () => apiGet<ImpactPreview>(`/api/clients/${clientId}/source-proposals/${proposalId}/impact`),
    enabled: !!clientId && !!proposalId,
    retry: false,
  })
}

export function useActOnProposal(clientId: string) {
  const qc = useQueryClient()

  return useMutation({
    mutationFn: ({
      proposalId,
      action,
      note,
    }: {
      proposalId: string | number
      action: ProposalAction
      note?: string
    }) =>
      apiPost<BackendSourceProposal>(`/api/clients/${clientId}/source-proposals/${proposalId}/action`, {
        action,
        reviewer: 'web-reviewer',
        note,
      }),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ['source-proposals', clientId] })
      qc.invalidateQueries({ queryKey: ['sources', clientId] })
    },
  })
}
