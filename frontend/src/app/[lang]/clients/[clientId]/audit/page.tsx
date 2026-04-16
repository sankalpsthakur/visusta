'use client'

import { use, useState } from 'react'
import { motion, AnimatePresence } from 'framer-motion'
import { PageTransition } from '@/components/shared/page-transition'
import { Skeleton } from '@/components/ui/skeleton'
import { ErrorBoundary } from '@/components/shared/error-boundary'
import { EmptyState } from '@/components/shared/empty-state'
import { useAudit } from '@/lib/api/hooks'
import { AlertTriangle, CheckCircle, Circle, ShieldCheck } from 'lucide-react'

type GapStatus = 'compliant' | 'gap' | 'partial' | 'not_assessed'
type GapType = 'regulatory' | 'data_quality' | 'code_health'
type ActiveTab = 'regulatory' | 'code_health'

interface GapItem {
  topic: string
  area: string
  status: GapStatus
  finding?: string
  priority: 'critical' | 'high' | 'medium' | 'low'
  gap_type: GapType
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

  const allGaps: GapItem[] = auditData
    ? auditData.findings.map((f) => ({
        topic: f.category,
        area: f.location,
        // severity comes as uppercase from API; lowercase for comparison
        status: (f.severity.toLowerCase() === 'low' ? 'compliant' : 'gap') as GapStatus,
        finding: f.message,
        priority: f.severity.toLowerCase() as GapItem['priority'],
        gap_type: (f.gap_type ?? 'regulatory') as GapType,
      }))
    : []

  const regulatoryGaps = allGaps.filter((g) => g.gap_type !== 'code_health')
  const codeHealthGaps = allGaps.filter((g) => g.gap_type === 'code_health')
  const gaps = activeTab === 'code_health' ? codeHealthGaps : regulatoryGaps

  const criticalCount = regulatoryGaps.filter((g) => g.status === 'gap' && g.priority === 'critical').length
  const gapCount = regulatoryGaps.filter((g) => g.status === 'gap').length
  const compliantCount = regulatoryGaps.filter((g) => g.status === 'compliant').length

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
                  {tab === 'code_health' ? codeHealthGaps.length : regulatoryGaps.length}
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
              ) : gaps.length === 0 ? (
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
                  {gaps.map((gap, i) => (
                    <motion.div
                      key={`${gap.topic}-${gap.area}-${i}`}
                      variants={{ hidden: { opacity: 0, x: -8 }, show: { opacity: 1, x: 0, transition: { duration: 0.2 } } }}
                      className="grid grid-cols-[auto_1fr_auto_auto] gap-4 px-5 py-4 items-start"
                      style={{ borderTop: i > 0 ? '1px solid var(--border-color)' : undefined }}
                    >
                      <span className="w-24 text-xs tabular-nums flex-shrink-0 pt-0.5" style={{ color: 'var(--text-muted)', fontFamily: 'var(--font-mono)' }}>
                        {gap.topic.replace(/_/g, ' ')}
                      </span>
                      <div>
                        <div className="text-sm font-medium mb-0.5" style={{ color: 'var(--text-primary)' }}>{gap.area}</div>
                        {gap.finding && <div className="text-xs" style={{ color: 'var(--text-muted)' }}>{gap.finding}</div>}
                      </div>
                      <div className="w-24 flex justify-center pt-0.5">
                        <span
                          className="text-xs px-2 py-0.5 rounded"
                          style={{
                            background: 'var(--bg-elevated)',
                            color: gap.priority === 'critical' ? 'var(--severity-critical)' : gap.priority === 'high' ? 'var(--severity-high)' : gap.priority === 'medium' ? 'var(--severity-medium)' : 'var(--text-muted)',
                          }}
                        >
                          {gap.priority}
                        </span>
                      </div>
                      <div className="w-28 flex justify-center pt-0.5">
                        <StatusBadge status={gap.status} />
                      </div>
                    </motion.div>
                  ))}
                </motion.div>
              )}
            </AnimatePresence>
          </div>
        </ErrorBoundary>
      </div>
    </PageTransition>
  )
}
