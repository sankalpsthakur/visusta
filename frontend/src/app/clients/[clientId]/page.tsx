'use client'

import { use } from 'react'
import { motion, AnimatePresence } from 'framer-motion'
import Link from 'next/link'
import { PageTransition } from '@/components/shared/page-transition'
import { Skeleton } from '@/components/ui/skeleton'
import { ErrorBoundary } from '@/components/shared/error-boundary'
import { EmptyState } from '@/components/shared/empty-state'
import { useClient, useLatestChangelog, useSources, useEvidence, type ChangeEntry, type ChangelogResponse } from '@/lib/api/hooks'
import { MetricCard, metricGridVariants } from '@/components/dashboard/metric-card'
import { TopicStatusCard, topicGridVariants } from '@/components/dashboard/topic-status-card'
import { CriticalActionCard, criticalActionsVariants } from '@/components/dashboard/critical-action-card'
import { RegulatoryTimeline } from '@/components/timeline/regulatory-timeline'
import type { TimelineEntryData } from '@/components/timeline/timeline-entry'
import { FileText, AlertTriangle, TrendingUp, Layers, Activity, Radio, ArrowRight } from 'lucide-react'

function changeEntryToTimeline(entry: ChangeEntry, date: string, index: number): TimelineEntryData {
  return {
    id: `${entry.regulation_id}-${index}`,
    date,
    regulationId: entry.regulation_id,
    title: entry.title,
    changeType: entry.change_type,
    severity: entry.severity as TimelineEntryData['severity'],
    summary: entry.summary,
    topic: entry.topic,
    effectiveDate: entry.effective_date ?? undefined,
    enforcementDate: entry.enforcement_date ?? undefined,
  }
}

function deriveTimelineEntries(changelog: ChangelogResponse): TimelineEntryData[] {
  const date = changelog.generated_date ?? ''
  const allEntries: ChangeEntry[] = [
    ...(changelog.new_regulations ?? []),
    ...(changelog.status_changes ?? []),
    ...(changelog.content_updates ?? []),
    ...(changelog.timeline_changes ?? []),
    ...(changelog.ended_regulations ?? []),
  ]
  return allEntries.map((entry, i) => changeEntryToTimeline(entry, date, i))
}

interface ClientDashboardProps {
  params: Promise<{ clientId: string }>
}

function MetricCardSkeleton() {
  return (
    <div className="rounded-lg p-5" style={{ background: 'var(--bg-surface)', border: '1px solid var(--border-color)' }}>
      <Skeleton className="h-3 w-24 mb-3" style={{ background: 'var(--bg-elevated)' }} />
      <Skeleton className="h-8 w-16 mb-1" style={{ background: 'var(--bg-elevated)' }} />
    </div>
  )
}

function TopicCardSkeleton() {
  return (
    <div className="rounded-lg p-4" style={{ background: 'var(--bg-surface)', border: '1px solid var(--border-color)' }}>
      <Skeleton className="h-3 w-20 mb-2" style={{ background: 'var(--bg-elevated)' }} />
      <Skeleton className="h-4 w-16" style={{ background: 'var(--bg-elevated)' }} />
    </div>
  )
}

function TimelineEntrySkeleton() {
  return (
    <div className="flex gap-4 mb-4 ml-4">
      <div className="flex flex-col items-center">
        <Skeleton className="w-3 h-3 rounded-full mt-1" style={{ background: 'var(--bg-elevated)' }} />
      </div>
      <div className="flex-1 pb-4" style={{ borderBottom: '1px solid var(--border-color)' }}>
        <Skeleton className="h-3 w-20 mb-2" style={{ background: 'var(--bg-elevated)' }} />
        <Skeleton className="h-4 w-3/4 mb-1" style={{ background: 'var(--bg-elevated)' }} />
        <Skeleton className="h-3 w-1/2" style={{ background: 'var(--bg-elevated)' }} />
      </div>
    </div>
  )
}

function MonitoredSourcesCard({ clientId }: { clientId: string }) {
  const { data: sources, isLoading } = useSources(clientId)

  const daily = sources?.filter((s) => s.frequency === 'daily').length ?? 0
  const weekly = sources?.filter((s) => s.frequency === 'weekly').length ?? 0
  const monthly = sources?.filter((s) => s.frequency === 'monthly').length ?? 0
  const total = sources?.length ?? 0
  const preview = sources?.slice(0, 4) ?? []

  return (
    <div
      className="rounded-lg p-5 mb-4"
      style={{ background: 'var(--bg-surface)', border: '1px solid var(--border-color)' }}
    >
      <div className="flex items-start justify-between mb-3">
        <div className="flex items-center gap-2">
          <Radio className="w-3.5 h-3.5" style={{ color: 'var(--text-muted)' }} />
          <span className="text-xs" style={{ color: 'var(--text-muted)' }}>Monitored Sources</span>
        </div>
        <Link
          href={`/clients/${clientId}/settings`}
          className="flex items-center gap-1 text-xs transition-opacity hover:opacity-70"
          style={{ color: 'var(--brand-accent)' }}
        >
          Configure
          <ArrowRight className="w-3 h-3" />
        </Link>
      </div>

      {isLoading ? (
        <div>
          <Skeleton className="h-8 w-12 mb-2" style={{ background: 'var(--bg-elevated)' }} />
          <Skeleton className="h-3 w-40 mb-3" style={{ background: 'var(--bg-elevated)' }} />
          <Skeleton className="h-3 w-full mb-1" style={{ background: 'var(--bg-elevated)' }} />
          <Skeleton className="h-3 w-3/4" style={{ background: 'var(--bg-elevated)' }} />
        </div>
      ) : total === 0 ? (
        <div className="text-xs" style={{ color: 'var(--text-muted)' }}>
          No sources configured.
        </div>
      ) : (
        <>
          <div
            className="text-3xl font-semibold tabular-nums mb-1"
            style={{ color: 'var(--brand-accent)' }}
          >
            {total}
          </div>
          <div className="text-xs mb-3" style={{ color: 'var(--text-muted)' }}>
            {[
              daily > 0 && `${daily} daily`,
              weekly > 0 && `${weekly} weekly`,
              monthly > 0 && `${monthly} monthly`,
            ]
              .filter(Boolean)
              .join(' · ')}
          </div>
          <div className="flex flex-col gap-1">
            {preview.map((src) => (
              <div
                key={src.id}
                className="flex items-center gap-1.5 text-xs"
                style={{ color: 'var(--text-muted)' }}
              >
                <span
                  className="w-1.5 h-1.5 rounded-full flex-shrink-0"
                  style={{ background: 'var(--brand-accent)' }}
                />
                {src.display_name}
              </div>
            ))}
            {total > 4 && (
              <div className="text-xs" style={{ color: 'var(--text-muted)' }}>
                +{total - 4} more
              </div>
            )}
          </div>
        </>
      )}
    </div>
  )
}

function EvidenceCard({ clientId }: { clientId: string }) {
  const { data, isLoading } = useEvidence(clientId)
  const records = data?.evidence ?? []
  const total = data?.total ?? records.length

  const oneWeekAgo = new Date(Date.now() - 7 * 24 * 60 * 60 * 1000).toISOString().slice(0, 10)
  const recentCount = records.filter((r) => r.access_date && r.access_date.slice(0, 10) >= oneWeekAgo).length
  const recent3 = records.slice(0, 3)

  return (
    <div
      className="rounded-lg p-5 mb-4"
      style={{ background: 'var(--bg-surface)', border: '1px solid var(--border-color)' }}
    >
      <div className="flex items-start justify-between mb-3">
        <div className="flex items-center gap-2">
          <FileText className="w-3.5 h-3.5" style={{ color: 'var(--text-muted)' }} />
          <span className="text-xs" style={{ color: 'var(--text-muted)' }}>Evidence</span>
        </div>
        <Link
          href={`/clients/${clientId}/evidence`}
          className="flex items-center gap-1 text-xs transition-opacity hover:opacity-70"
          style={{ color: 'var(--brand-accent)' }}
        >
          View all
          <ArrowRight className="w-3 h-3" />
        </Link>
      </div>

      {isLoading ? (
        <div>
          <Skeleton className="h-8 w-12 mb-2" style={{ background: 'var(--bg-elevated)' }} />
          <Skeleton className="h-3 w-32 mb-3" style={{ background: 'var(--bg-elevated)' }} />
          <Skeleton className="h-3 w-full mb-1" style={{ background: 'var(--bg-elevated)' }} />
          <Skeleton className="h-3 w-3/4" style={{ background: 'var(--bg-elevated)' }} />
        </div>
      ) : total === 0 ? (
        <div className="text-xs" style={{ color: 'var(--text-muted)' }}>
          No evidence records yet.
        </div>
      ) : (
        <>
          <div
            className="text-3xl font-semibold tabular-nums mb-1"
            style={{ color: 'var(--brand-accent)' }}
          >
            {total}
          </div>
          <div className="text-xs mb-3" style={{ color: 'var(--text-muted)' }}>
            {recentCount > 0 ? `${recentCount} new this week` : 'No new records this week'}
          </div>
          <div className="flex flex-col gap-1">
            {recent3.map((r) => (
              <div
                key={r.evidence_id}
                className="flex items-center gap-1.5 text-xs"
                style={{ color: 'var(--text-muted)' }}
              >
                <span
                  className="w-1.5 h-1.5 rounded-full flex-shrink-0"
                  style={{ background: 'var(--brand-accent)' }}
                />
                <span className="line-clamp-1">{r.document_title || r.url}</span>
              </div>
            ))}
          </div>
        </>
      )}
    </div>
  )
}

export default function ClientDashboardPage({ params }: ClientDashboardProps) {
  const { clientId } = use(params)
  const { data: client } = useClient(clientId)
  const { data: changelog, isLoading, error } = useLatestChangelog(clientId)

  const timelineEntries = changelog ? deriveTimelineEntries(changelog) : []
  const isNewClient = !isLoading && !changelog && !error

  const topicCount = changelog
    ? Object.keys(changelog.topic_change_statuses).length
    : (client?.required_topics.length ?? 0)

  const metrics = [
    { label: 'Regulations Tracked', value: changelog?.total_regulations_tracked ?? 0, icon: FileText, valueColor: 'var(--brand-accent)' },
    { label: 'Changes Detected', value: changelog?.total_changes_detected ?? 0, icon: TrendingUp },
    { label: 'Critical Actions', value: changelog?.critical_actions?.length ?? 0, icon: AlertTriangle, valueColor: (changelog?.critical_actions?.length ?? 0) > 0 ? 'var(--severity-critical)' : undefined },
    { label: 'Topics Covered', value: topicCount, icon: Layers },
  ]

  return (
    <PageTransition className="p-8">
      <div className="max-w-4xl">
        <ErrorBoundary>
          {/* Metric cards */}
          <AnimatePresence mode="wait">
            {isLoading ? (
              <motion.div key="metric-skeletons" className="grid grid-cols-2 xl:grid-cols-4 gap-4 mb-8" initial={{ opacity: 0 }} animate={{ opacity: 1 }} exit={{ opacity: 0 }}>
                {[0, 1, 2, 3].map((i) => <MetricCardSkeleton key={i} />)}
              </motion.div>
            ) : (
              <motion.div key="metric-cards" className="grid grid-cols-2 xl:grid-cols-4 gap-4 mb-8" variants={metricGridVariants} initial="hidden" animate="show">
                {metrics.map((m) => (
                  <MetricCard key={m.label} label={m.label} value={m.value} icon={m.icon} valueColor={m.valueColor} />
                ))}
              </motion.div>
            )}
          </AnimatePresence>
        </ErrorBoundary>

        {/* Two-column row: topics + monitored sources */}
        <div className="grid grid-cols-1 xl:grid-cols-2 gap-4 mb-4">
          {/* Topics */}
          {client && (
            <div
              className="rounded-lg p-5"
              style={{ background: 'var(--bg-surface)', border: '1px solid var(--border-color)' }}
            >
              <div className="text-xs mb-3" style={{ color: 'var(--text-muted)' }}>Monitored Topics</div>
              <div className="flex flex-wrap gap-2">
                {client.required_topics.map((t) => (
                  <span
                    key={t}
                    className="text-xs px-2.5 py-1 rounded"
                    style={{ background: 'var(--bg-elevated)', color: 'var(--brand-accent)', border: '1px solid var(--border-color)', fontFamily: 'var(--font-mono)' }}
                  >
                    {t}
                  </span>
                ))}
              </div>
            </div>
          )}

          {/* Monitored Sources card */}
          <ErrorBoundary>
            <MonitoredSourcesCard clientId={clientId} />
          </ErrorBoundary>

          {/* Evidence card */}
          <ErrorBoundary>
            <EvidenceCard clientId={clientId} />
          </ErrorBoundary>
        </div>

        {/* Regulatory Timeline */}
        <ErrorBoundary>
          <div className="mb-4">
            <div className="text-xs mb-3" style={{ color: 'var(--text-muted)' }}>Regulatory Timeline</div>
            <AnimatePresence mode="wait">
              {isLoading ? (
                <motion.div key="timeline-skeleton" initial={{ opacity: 0 }} animate={{ opacity: 1 }} exit={{ opacity: 0 }} className="rounded-lg p-5" style={{ background: 'var(--bg-surface)', border: '1px solid var(--border-color)' }}>
                  {[0, 1, 2, 3].map((i) => <TimelineEntrySkeleton key={i} />)}
                </motion.div>
              ) : error ? (
                <motion.div key="timeline-error" initial={{ opacity: 0 }} animate={{ opacity: 1 }}>
                  <EmptyState
                    icon={Activity}
                    title="Could not load timeline"
                    description="Failed to fetch regulatory data. Please try refreshing the page."
                  />
                </motion.div>
              ) : timelineEntries.length === 0 ? (
                <motion.div key="timeline-empty" initial={{ opacity: 0 }} animate={{ opacity: 1 }}>
                  <EmptyState
                    icon={Activity}
                    title="No regulatory activity this period"
                    description="Regulatory changes will appear here after the first screening run."
                  />
                </motion.div>
              ) : (
                <motion.div key="timeline" initial={{ opacity: 0 }} animate={{ opacity: 1 }}>
                  <RegulatoryTimeline entries={timelineEntries} clientId={clientId} />
                </motion.div>
              )}
            </AnimatePresence>
          </div>
        </ErrorBoundary>

        {/* Topic status cards */}
        <ErrorBoundary>
          <AnimatePresence mode="wait">
            {isLoading ? (
              <motion.div key="topic-skeletons" className="grid grid-cols-2 xl:grid-cols-3 gap-3 mb-4" initial={{ opacity: 0 }} animate={{ opacity: 1 }} exit={{ opacity: 0 }}>
                {[0, 1, 2, 3, 4].map((i) => <TopicCardSkeleton key={i} />)}
              </motion.div>
            ) : changelog?.topic_change_statuses ? (
              <motion.div key="topic-cards" initial={{ opacity: 0 }} animate={{ opacity: 1 }} className="mb-4">
                <div className="text-xs mb-3" style={{ color: 'var(--text-muted)' }}>Topic Status</div>
                <motion.div className="grid grid-cols-2 xl:grid-cols-3 gap-3" variants={topicGridVariants} initial="hidden" animate="show">
                  {Object.entries(changelog.topic_change_statuses).map(([topic, status]) => (
                    <TopicStatusCard key={topic} topic={topic} status={status} />
                  ))}
                </motion.div>
              </motion.div>
            ) : null}
          </AnimatePresence>
        </ErrorBoundary>

        {/* Critical action cards */}
        {changelog?.critical_actions && changelog.critical_actions.length > 0 && (
          <ErrorBoundary>
            <div>
              <div className="text-xs mb-3" style={{ color: 'var(--text-muted)' }}>Critical Actions</div>
              <motion.div className="flex flex-col gap-3" variants={criticalActionsVariants} initial="hidden" animate="show">
                {changelog.critical_actions.map((action) => (
                  <CriticalActionCard key={action.regulation_id} entry={action} />
                ))}
              </motion.div>
            </div>
          </ErrorBoundary>
        )}
      </div>
    </PageTransition>
  )
}
