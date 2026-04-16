'use client'

import { use, useState } from 'react'
import { motion, AnimatePresence } from 'framer-motion'
import { PageTransition } from '@/components/shared/page-transition'
import { Skeleton } from '@/components/ui/skeleton'
import { ErrorBoundary } from '@/components/shared/error-boundary'
import { EmptyState } from '@/components/shared/empty-state'
import { useAudit } from '@/lib/api/hooks'
import { AlertTriangle, CheckCircle, ChevronDown, ChevronRight, Circle, ShieldCheck } from 'lucide-react'

type GapStatus = 'compliant' | 'gap' | 'partial' | 'not_assessed'
type GapType = 'regulatory' | 'data_quality' | 'code_health'
type GapPriority = 'critical' | 'high' | 'medium' | 'low'
type ActiveTab = 'regulatory' | 'code_health'

interface GapItem {
  topic: string
  area: string
  status: GapStatus
  finding?: string
  priority: GapPriority
  gap_type: GapType
}

// Displayed row in the audit table. `count > 1` means this is a collapsed group
// (data_quality findings sharing `(category, message)`). Single-finding rows carry
// `count === 1` and `locations` of length 1.
interface GapGroup {
  key: string
  topic: string
  finding?: string
  priority: GapPriority
  status: GapStatus
  gap_type: GapType
  count: number
  locations: string[]
}

const PRIORITY_ORDER: Record<GapPriority, number> = { critical: 0, high: 1, medium: 2, low: 3 }

function maxPriority(a: GapPriority, b: GapPriority): GapPriority {
  return PRIORITY_ORDER[a] <= PRIORITY_ORDER[b] ? a : b
}

function dedupeDataQuality(items: GapItem[]): GapGroup[] {
  const groups = new Map<string, GapGroup>()
  const order: string[] = []

  for (const item of items) {
    // Only data_quality items collapse; everything else stays one-per-finding.
    const groupKey =
      item.gap_type === 'data_quality'
        ? `dq::${item.topic}::${item.finding ?? ''}`
        : `one::${item.gap_type}::${item.topic}::${item.area}::${item.finding ?? ''}::${order.length}`

    const existing = groups.get(groupKey)
    if (existing) {
      existing.count += 1
      existing.locations.push(item.area)
      existing.priority = maxPriority(existing.priority, item.priority)
      if (existing.status !== 'gap' && item.status === 'gap') {
        existing.status = 'gap'
      }
      continue
    }

    groups.set(groupKey, {
      key: groupKey,
      topic: item.topic,
      finding: item.finding,
      priority: item.priority,
      status: item.status,
      gap_type: item.gap_type,
      count: 1,
      locations: [item.area],
    })
    order.push(groupKey)
  }

  return order.map((k) => groups.get(k)!)
}

const STATUS_CONFIG: Record<GapStatus, { label: string; color: string; icon: React.ReactNode }> = {
  compliant: { label: 'Compliant', color: 'var(--severity-low)', icon: <CheckCircle className="w-3.5 h-3.5" /> },
  gap: { label: 'Gap', color: 'var(--severity-critical)', icon: <AlertTriangle className="w-3.5 h-3.5" /> },
  partial: { label: 'Partial', color: 'var(--severity-medium)', icon: <Circle className="w-3.5 h-3.5" /> },
  not_assessed: { label: 'Not assessed', color: 'var(--text-muted)', icon: <Circle className="w-3.5 h-3.5" /> },
}

function StatusBadge({ status }: { status: GapStatus }) {
  const config = STATUS_CONFIG[status]
  return (
    <span
      className="inline-flex items-center gap-1 text-xs px-2 py-0.5 rounded"
      style={{
        color: config.color,
        background: `color-mix(in srgb, ${config.color} 12%, transparent)`,
        border: `1px solid color-mix(in srgb, ${config.color} 25%, transparent)`,
      }}
    >
      {config.icon}
      {config.label}
    </span>
  )
}

function FindingRowSkeleton({ i }: { i: number }) {
  return (
    <div
      className="grid grid-cols-[auto_1fr_auto_auto] gap-4 px-5 py-4 items-start"
      style={{ borderTop: i > 0 ? '1px solid var(--border-color)' : undefined }}
    >
      <Skeleton className="w-24 h-3 mt-1" style={{ background: 'var(--bg-elevated)' }} />
      <div>
        <Skeleton className="h-4 w-2/3 mb-1.5" style={{ background: 'var(--bg-elevated)' }} />
        <Skeleton className="h-3 w-1/2" style={{ background: 'var(--bg-elevated)' }} />
      </div>
      <Skeleton className="w-16 h-5 rounded" style={{ background: 'var(--bg-elevated)' }} />
      <Skeleton className="w-20 h-5 rounded" style={{ background: 'var(--bg-elevated)' }} />
    </div>
  )
}

interface AuditPageProps {
  params: Promise<{ clientId: string }>
}

export default function AuditPage({ params }: AuditPageProps) {
  const { clientId } = use(params)
  const { data: auditData, isLoading, isError } = useAudit(clientId)
  const [activeTab, setActiveTab] = useState<ActiveTab>('regulatory')
  const [expandedGroups, setExpandedGroups] = useState<Record<string, boolean>>({})

  const allGaps: GapItem[] = auditData
    ? auditData.findings.map((f) => ({
        topic: f.category,
        area: f.location,
        // severity comes as uppercase from API; lowercase for comparison
        status: (f.severity.toLowerCase() === 'low' ? 'compliant' : 'gap') as GapStatus,
        finding: f.message,
        priority: f.severity.toLowerCase() as GapPriority,
        gap_type: (f.gap_type ?? 'regulatory') as GapType,
      }))
    : []

  const regulatoryGaps = allGaps.filter((g) => g.gap_type !== 'code_health')
  const codeHealthGaps = allGaps.filter((g) => g.gap_type === 'code_health')

  // Regulatory tab collapses data_quality duplicates; System Health keeps
  // every code_health row separate (one per .py file or per issue).
  const regulatoryGroups = dedupeDataQuality(regulatoryGaps)
  const codeHealthGroups: GapGroup[] = codeHealthGaps.map((g, i) => ({
    key: `ch-${i}`,
    topic: g.topic,
    finding: g.finding,
    priority: g.priority,
    status: g.status,
    gap_type: g.gap_type,
    count: 1,
    locations: [g.area],
  }))
  const groups = activeTab === 'code_health' ? codeHealthGroups : regulatoryGroups

  // Headline counts reflect deduped regulatory exposure: each collapsed
  // data_quality group counts once, not once per affected location.
  const criticalCount = regulatoryGroups.filter((g) => g.status === 'gap' && g.priority === 'critical').length
  const gapCount = regulatoryGroups.filter((g) => g.status === 'gap').length
  const compliantCount = regulatoryGroups.filter((g) => g.status === 'compliant').length

  const toggleGroup = (key: string) =>
    setExpandedGroups((prev) => ({ ...prev, [key]: !prev[key] }))

  return (
    <PageTransition className="p-8">
      <div className="max-w-4xl">
        <div className="mb-6">
          <h2 className="text-lg font-semibold mb-1" style={{ color: 'var(--text-primary)' }}>
            Gap Analysis
          </h2>
          <p className="text-sm" style={{ color: 'var(--text-muted)' }}>
            Compliance posture vs. regulatory requirements
          </p>
        </div>

        {/* Summary cards — always counts regulatory gaps only */}
        <ErrorBoundary>
          <div className="grid grid-cols-3 gap-4 mb-8">
            {isLoading
              ? [0, 1, 2].map((i) => (
                  <div key={i} className="rounded-lg p-5" style={{ background: 'var(--bg-surface)', border: '1px solid var(--border-color)' }}>
                    <Skeleton className="h-3 w-24 mb-3" style={{ background: 'var(--bg-elevated)' }} />
                    <Skeleton className="h-9 w-12" style={{ background: 'var(--bg-elevated)' }} />
                  </div>
                ))
              : [
                  { label: 'Critical gaps', value: criticalCount, color: 'var(--severity-critical)' },
                  { label: 'Total gaps', value: gapCount, color: 'var(--severity-high)' },
                  { label: 'Compliant', value: compliantCount, color: 'var(--severity-low)' },
                ].map((stat) => (
                  <div key={stat.label} className="rounded-lg p-5" style={{ background: 'var(--bg-surface)', border: '1px solid var(--border-color)' }}>
                    <div className="text-xs mb-2" style={{ color: 'var(--text-muted)' }}>{stat.label}</div>
                    <div className="text-3xl font-semibold tabular-nums" style={{ color: stat.color }}>{stat.value}</div>
                  </div>
                ))}
          </div>
        </ErrorBoundary>

        {/* Tab toggle */}
        <div className="flex gap-1 mb-4 p-1 rounded-lg w-fit" style={{ background: 'var(--bg-elevated)' }}>
          {([['regulatory', 'Regulatory Gaps'], ['code_health', 'System Health']] as [ActiveTab, string][]).map(([tab, label]) => (
            <button
              key={tab}
              onClick={() => setActiveTab(tab)}
              className="text-xs px-3 py-1.5 rounded-md transition-colors"
              style={{
                background: activeTab === tab ? 'var(--bg-surface)' : 'transparent',
                color: activeTab === tab ? 'var(--text-primary)' : 'var(--text-muted)',
                border: activeTab === tab ? '1px solid var(--border-color)' : '1px solid transparent',
                cursor: 'pointer',
              }}
            >
              {label}
              {!isLoading && (
                <span
                  className="ml-1.5 tabular-nums"
                  style={{ color: 'var(--text-muted)' }}
                >
                  {tab === 'code_health' ? codeHealthGroups.length : regulatoryGroups.length}
                </span>
              )}
            </button>
          ))}
        </div>

        {/* Gap table */}
        <ErrorBoundary>
          <div className="rounded-lg overflow-hidden" style={{ border: '1px solid var(--border-color)' }}>
            <div
              className="grid grid-cols-[auto_1fr_auto_auto] gap-4 px-5 py-3 text-xs font-medium"
              style={{ background: 'var(--bg-elevated)', color: 'var(--text-muted)', borderBottom: '1px solid var(--border-color)' }}
            >
              <span className="w-24">Topic</span>
              <span>Area / Finding</span>
              <span className="w-24 text-center">Priority</span>
              <span className="w-28 text-center">Status</span>
            </div>

            <AnimatePresence mode="wait">
              {isLoading ? (
                <motion.div key="finding-skeletons" initial={{ opacity: 0 }} animate={{ opacity: 1 }} exit={{ opacity: 0 }} style={{ background: 'var(--bg-surface)' }}>
                  {[0, 1, 2, 3, 4, 5].map((i) => <FindingRowSkeleton key={i} i={i} />)}
                </motion.div>
              ) : isError ? (
                <motion.div key="error" initial={{ opacity: 0 }} animate={{ opacity: 1 }} className="px-5 py-10" style={{ background: 'var(--bg-surface)' }}>
                  <EmptyState
                    icon={ShieldCheck}
                    title="Could not load audit data"
                    description="The backend is unavailable. Check your connection and try again."
                  />
                </motion.div>
              ) : groups.length === 0 ? (
                <motion.div key="empty" initial={{ opacity: 0 }} animate={{ opacity: 1 }} className="px-5 py-10" style={{ background: 'var(--bg-surface)' }}>
                  <EmptyState
                    icon={ShieldCheck}
                    title={activeTab === 'code_health' ? 'No system health issues' : 'No compliance gaps'}
                    description={activeTab === 'code_health' ? 'No code or build issues detected.' : 'This client has no compliance gaps on record.'}
                  />
                </motion.div>
              ) : (
                <motion.div
                  key={`findings-${activeTab}`}
                  initial="hidden"
                  animate="show"
                  variants={{ hidden: {}, show: { transition: { staggerChildren: 0.04 } } }}
                  style={{ background: 'var(--bg-surface)' }}
                >
                  {groups.map((group, i) => {
                    const isExpanded = !!expandedGroups[group.key]
                    const hasMany = group.count > 1
                    const primaryLocation = group.locations[0]
                    return (
                      <motion.div
                        key={group.key}
                        variants={{ hidden: { opacity: 0, x: -8 }, show: { opacity: 1, x: 0, transition: { duration: 0.2 } } }}
                        className="px-5 py-4"
                        style={{ borderTop: i > 0 ? '1px solid var(--border-color)' : undefined }}
                      >
                        <div className="grid grid-cols-[auto_1fr_auto_auto] gap-4 items-start">
                          <span className="w-24 text-xs tabular-nums flex-shrink-0 pt-0.5" style={{ color: 'var(--text-muted)', fontFamily: 'var(--font-mono)' }}>
                            {group.topic.replace(/_/g, ' ')}
                          </span>
                          <div>
                            {hasMany ? (
                              <div className="text-sm font-medium mb-0.5 flex items-center gap-2" style={{ color: 'var(--text-primary)' }}>
                                {group.finding ? (
                                  <span>{group.finding}</span>
                                ) : (
                                  <span>{group.topic}</span>
                                )}
                                <span
                                  className="text-xs px-1.5 py-0.5 rounded tabular-nums"
                                  style={{ background: 'var(--bg-elevated)', color: 'var(--text-muted)' }}
                                >
                                  &times; {group.count}
                                </span>
                              </div>
                            ) : (
                              <>
                                <div className="text-sm font-medium mb-0.5" style={{ color: 'var(--text-primary)' }}>{primaryLocation}</div>
                                {group.finding && <div className="text-xs" style={{ color: 'var(--text-muted)' }}>{group.finding}</div>}
                              </>
                            )}
                            {hasMany && (
                              <button
                                type="button"
                                onClick={() => toggleGroup(group.key)}
                                className="mt-2 inline-flex items-center gap-1 text-xs"
                                style={{ color: 'var(--text-muted)', cursor: 'pointer', background: 'transparent', border: 'none', padding: 0 }}
                              >
                                {isExpanded ? <ChevronDown className="w-3 h-3" /> : <ChevronRight className="w-3 h-3" />}
                                {isExpanded ? 'Hide' : 'Show'} affected locations ({group.count})
                              </button>
                            )}
                            {hasMany && isExpanded && (
                              <ul className="mt-2 space-y-0.5">
                                {group.locations.map((loc, li) => (
                                  <li
                                    key={`${group.key}-loc-${li}`}
                                    className="text-xs tabular-nums"
                                    style={{ color: 'var(--text-muted)', fontFamily: 'var(--font-mono)' }}
                                  >
                                    {loc}
                                  </li>
                                ))}
                              </ul>
                            )}
                          </div>
                          <div className="w-24 flex justify-center pt-0.5">
                            <span
                              className="text-xs px-2 py-0.5 rounded"
                              style={{
                                background: 'var(--bg-elevated)',
                                color: group.priority === 'critical' ? 'var(--severity-critical)' : group.priority === 'high' ? 'var(--severity-high)' : group.priority === 'medium' ? 'var(--severity-medium)' : 'var(--text-muted)',
                              }}
                            >
                              {group.priority}
                            </span>
                          </div>
                          <div className="w-28 flex justify-center pt-0.5">
                            <StatusBadge status={group.status} />
                          </div>
                        </div>
                      </motion.div>
                    )
                  })}
                </motion.div>
              )}
            </AnimatePresence>
          </div>
        </ErrorBoundary>
      </div>
    </PageTransition>
  )
}
