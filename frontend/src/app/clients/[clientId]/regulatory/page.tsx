'use client'

import { use, useState } from 'react'
import { motion, AnimatePresence } from 'framer-motion'
import { PageTransition } from '@/components/shared/page-transition'
import { Skeleton } from '@/components/ui/skeleton'
import { ErrorBoundary } from '@/components/shared/error-boundary'
import { EmptyState } from '@/components/shared/empty-state'
import { useChangelogs, useChangelog, type ChangeEntry } from '@/lib/api/hooks'
import { ChangelogTable, type ChangelogEntry } from '@/components/regulatory/changelog-table'
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select'
import type { Severity } from '@/components/shared/severity-badge'
import { FileSearch } from 'lucide-react'

function changeEntryToRow(entry: ChangeEntry, index: number): ChangelogEntry {
  return {
    id: String(index),
    date: entry.effective_date ?? '',
    regulationId: entry.regulation_id,
    title: entry.title,
    topic: entry.topic,
    changeType: entry.change_type,
    severity: entry.severity as Severity,
    status: entry.current_status,
    summary: entry.summary,
  }
}

function TableRowSkeleton({ i }: { i: number }) {
  return (
    <div
      className="grid grid-cols-6 gap-3 px-4 py-3 items-center"
      style={{ borderBottom: i < 5 ? '1px solid var(--border-color)' : undefined }}
    >
      <Skeleton className="h-3 w-16" style={{ background: 'var(--bg-elevated)' }} />
      <Skeleton className="h-3 w-20" style={{ background: 'var(--bg-elevated)' }} />
      <Skeleton className="h-3 w-full" style={{ background: 'var(--bg-elevated)' }} />
      <Skeleton className="h-3 w-12" style={{ background: 'var(--bg-elevated)' }} />
      <Skeleton className="h-5 w-14 rounded" style={{ background: 'var(--bg-elevated)' }} />
      <Skeleton className="h-5 w-16 rounded" style={{ background: 'var(--bg-elevated)' }} />
    </div>
  )
}

interface RegulatoryPageProps {
  params: Promise<{ clientId: string }>
}

export default function RegulatoryPage({ params }: RegulatoryPageProps) {
  const { clientId } = use(params)
  const { data: periodsData, isLoading: periodsLoading, isError: periodsError } = useChangelogs(clientId)
  const periods = periodsData?.periods ?? []
  const [selectedPeriod, setSelectedPeriod] = useState<string>('')

  const activePeriod = selectedPeriod || periods[periods.length - 1] || ''
  const { data: changelogData, isLoading: changelogLoading, isError: changelogError } = useChangelog(clientId, activePeriod)

  const isLoading = periodsLoading || changelogLoading
  const isError = periodsError || changelogError
  const isEmpty = !isLoading && !isError && periodsData && periods.length === 0

  const entries: ChangelogEntry[] = changelogData
    ? [
        ...changelogData.new_regulations,
        ...changelogData.status_changes,
        ...changelogData.content_updates,
        ...changelogData.timeline_changes,
        ...changelogData.ended_regulations,
      ].map((e, i) => changeEntryToRow(e, i))
    : []

  return (
    <PageTransition className="p-8">
      <div className="max-w-4xl">
        <div className="flex items-start justify-between mb-6 gap-4 flex-wrap">
          <div>
            <h2 className="text-lg font-semibold mb-1" style={{ color: 'var(--text-primary)' }}>
              Regulatory Data
            </h2>
            <p className="text-sm" style={{ color: 'var(--text-muted)' }}>
              Recent regulatory changes affecting this client
            </p>
          </div>

          {periods.length > 0 && (
            <Select value={activePeriod} onValueChange={(v) => setSelectedPeriod(v as string)}>
              <SelectTrigger className="w-36">
                <SelectValue placeholder="Period" />
              </SelectTrigger>
              <SelectContent>
                {periods.map((p) => (
                  <SelectItem key={p} value={p}>{p}</SelectItem>
                ))}
              </SelectContent>
            </Select>
          )}
        </div>

        <AnimatePresence>
          {changelogData && !isLoading && (
            <motion.div
              initial={{ opacity: 0, y: -4 }}
              animate={{ opacity: 1, y: 0 }}
              exit={{ opacity: 0 }}
              className="rounded-lg px-4 py-2.5 mb-4 text-xs"
              style={{
                background: 'color-mix(in srgb, var(--severity-low) 10%, transparent)',
                border: '1px solid color-mix(in srgb, var(--severity-low) 25%, transparent)',
                color: 'var(--severity-low)',
              }}
            >
              Live data — {activePeriod} ({entries.length} entries)
            </motion.div>
          )}
        </AnimatePresence>

        <ErrorBoundary>
          <AnimatePresence mode="wait">
            {isLoading ? (
              <motion.div
                key="table-skeleton"
                initial={{ opacity: 0 }}
                animate={{ opacity: 1 }}
                exit={{ opacity: 0 }}
                className="rounded-lg overflow-hidden"
                style={{ border: '1px solid var(--border-color)' }}
              >
                <div
                  className="grid grid-cols-6 gap-3 px-4 py-3 text-xs font-medium"
                  style={{ background: 'var(--bg-elevated)', color: 'var(--text-muted)', borderBottom: '1px solid var(--border-color)' }}
                >
                  {['Date', 'Regulation', 'Title', 'Topic', 'Severity', 'Status'].map((h) => (
                    <span key={h}>{h}</span>
                  ))}
                </div>
                <div style={{ background: 'var(--bg-surface)' }}>
                  {[0, 1, 2, 3, 4, 5].map((i) => <TableRowSkeleton key={i} i={i} />)}
                </div>
              </motion.div>
            ) : isError ? (
              <motion.div key="error" initial={{ opacity: 0 }} animate={{ opacity: 1 }}>
                <EmptyState
                  icon={FileSearch}
                  title="Could not load regulatory data"
                  description="The backend is unavailable. Check your connection and try again."
                />
              </motion.div>
            ) : isEmpty ? (
              <motion.div key="empty" initial={{ opacity: 0 }} animate={{ opacity: 1 }}>
                <EmptyState
                  icon={FileSearch}
                  title="No regulatory data yet"
                  description="Run the first screening to populate the changelog for this client."
                />
              </motion.div>
            ) : (
              <motion.div key="table" initial={{ opacity: 0 }} animate={{ opacity: 1 }}>
                <ChangelogTable entries={entries} isLoading={false} />
              </motion.div>
            )}
          </AnimatePresence>
        </ErrorBoundary>
      </div>
    </PageTransition>
  )
}
