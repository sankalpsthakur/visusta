'use client'

import { useState, useMemo, useCallback } from 'react'
import { motion } from 'framer-motion'
import { ChevronUp, ChevronDown, ChevronsUpDown } from 'lucide-react'
import {
  Table,
  TableHeader,
  TableBody,
  TableHead,
  TableRow,
  TableCell,
} from '@/components/ui/table'
import { SeverityBadge, Severity } from '@/components/shared/severity-badge'
import { Skeleton } from '@/components/ui/skeleton'
import { SearchBar } from './search-bar'
import { TopicFilter } from './topic-filter'

export interface ChangelogEntry {
  id: string
  date: string
  regulationId: string
  title: string
  topic: string
  changeType: string
  severity: Severity
  status?: string
  summary?: string
}

type SortKey = 'severity' | 'regulationId' | 'title' | 'topic' | 'changeType' | 'status'
type SortDir = 'asc' | 'desc'

const SEVERITY_ORDER: Record<Severity, number> = {
  critical: 4,
  high: 3,
  medium: 2,
  low: 1,
}

const CHANGE_TYPE_LABELS: Record<string, string> = {
  regulation_removed: 'removed',
  amendment: 'amended',
  new_regulation: 'new',
  status_change: 'status',
  content_update: 'updated',
  timeline_change: 'timeline',
}

interface SortHeaderProps {
  label: string
  sortKey: SortKey
  currentKey: SortKey
  dir: SortDir
  onSort: (key: SortKey) => void
}

function SortHeader({ label, sortKey, currentKey, dir, onSort }: SortHeaderProps) {
  const active = sortKey === currentKey
  return (
    <TableHead
      className="cursor-pointer select-none"
      onClick={() => onSort(sortKey)}
    >
      <div className="flex items-center gap-1">
        {label}
        {active ? (
          dir === 'asc' ? (
            <ChevronUp className="w-3 h-3" style={{ color: 'var(--brand-accent)' }} />
          ) : (
            <ChevronDown className="w-3 h-3" style={{ color: 'var(--brand-accent)' }} />
          )
        ) : (
          <ChevronsUpDown className="w-3 h-3" style={{ color: 'var(--border-color)' }} />
        )}
      </div>
    </TableHead>
  )
}

const rowVariants = {
  hidden: { opacity: 0, y: 6 },
  show: (i: number) => ({
    opacity: 1,
    y: 0,
    transition: { delay: i * 0.02, duration: 0.2 },
  }),
}

interface ChangelogTableProps {
  entries: ChangelogEntry[]
  isLoading?: boolean
}

export function ChangelogTable({ entries, isLoading = false }: ChangelogTableProps) {
  const [sortKey, setSortKey] = useState<SortKey>('severity')
  const [sortDir, setSortDir] = useState<SortDir>('desc')
  const [search, setSearch] = useState('')
  const [selectedTopics, setSelectedTopics] = useState<string[]>([])

  const handleSort = useCallback((key: SortKey) => {
    if (key === sortKey) {
      setSortDir((d) => (d === 'asc' ? 'desc' : 'asc'))
    } else {
      setSortKey(key)
      setSortDir('desc')
    }
  }, [sortKey])

  const filtered = useMemo(() => {
    let rows = entries

    if (selectedTopics.length > 0) {
      rows = rows.filter((e) => selectedTopics.includes(e.topic))
    }

    if (search.trim()) {
      const q = search.toLowerCase()
      rows = rows.filter(
        (e) =>
          e.title.toLowerCase().includes(q) ||
          e.regulationId.toLowerCase().includes(q) ||
          (e.summary ?? '').toLowerCase().includes(q)
      )
    }

    return [...rows].sort((a, b) => {
      let cmp = 0
      if (sortKey === 'severity') {
        cmp = SEVERITY_ORDER[a.severity] - SEVERITY_ORDER[b.severity]
      } else {
        const aVal = (a[sortKey as keyof ChangelogEntry] ?? '') as string
        const bVal = (b[sortKey as keyof ChangelogEntry] ?? '') as string
        cmp = aVal.localeCompare(bVal)
      }
      return sortDir === 'asc' ? cmp : -cmp
    })
  }, [entries, search, selectedTopics, sortKey, sortDir])

  if (isLoading) {
    return (
      <div className="space-y-2">
        {[...Array(5)].map((_, i) => (
          <Skeleton key={i} className="h-12 w-full" style={{ background: 'var(--bg-elevated)' }} />
        ))}
      </div>
    )
  }

  return (
    <div className="space-y-3">
      {/* Filters */}
      <div className="flex items-center gap-3 flex-wrap">
        <SearchBar value={search} onChange={setSearch} />
      </div>
      <TopicFilter selected={selectedTopics} onChange={setSelectedTopics} />

      {/* Table */}
      <div
        className="rounded-lg overflow-hidden"
        style={{ border: '1px solid var(--border-color)' }}
      >
        <Table>
          <TableHeader>
            <TableRow style={{ background: 'var(--bg-elevated)', borderColor: 'var(--border-color)' }}>
              <SortHeader label="Severity" sortKey="severity" currentKey={sortKey} dir={sortDir} onSort={handleSort} />
              <SortHeader label="ID" sortKey="regulationId" currentKey={sortKey} dir={sortDir} onSort={handleSort} />
              <SortHeader label="Title" sortKey="title" currentKey={sortKey} dir={sortDir} onSort={handleSort} />
              <SortHeader label="Topic" sortKey="topic" currentKey={sortKey} dir={sortDir} onSort={handleSort} />
              <SortHeader label="Change" sortKey="changeType" currentKey={sortKey} dir={sortDir} onSort={handleSort} />
              <SortHeader label="Status" sortKey="status" currentKey={sortKey} dir={sortDir} onSort={handleSort} />
            </TableRow>
          </TableHeader>
          <TableBody>
            {filtered.length === 0 ? (
              <TableRow>
                <td colSpan={6} className="py-10 text-center text-sm" style={{ color: 'var(--text-muted)' }}>
                  No matching regulations
                </td>
              </TableRow>
            ) : (
              filtered.map((entry, i) => (
                <motion.tr
                  key={entry.id}
                  custom={i}
                  variants={rowVariants}
                  initial="hidden"
                  animate="show"
                  className="border-b transition-colors hover:bg-muted/50"
                  style={{
                    borderColor: 'var(--border-color)',
                    background: 'var(--bg-surface)',
                  }}
                >
                  <TableCell>
                    <SeverityBadge severity={entry.severity} />
                  </TableCell>
                  <TableCell>
                    <span
                      className="text-xs tabular-nums"
                      style={{ fontFamily: 'var(--font-mono)', color: 'var(--text-muted)' }}
                    >
                      {entry.regulationId}
                    </span>
                  </TableCell>
                  <TableCell>
                    <div>
                      <div className="text-sm" style={{ color: 'var(--text-primary)' }}>
                        {entry.title}
                      </div>
                      {entry.summary && (
                        <div className="text-xs mt-0.5" style={{ color: 'var(--text-muted)' }}>
                          {entry.summary}
                        </div>
                      )}
                    </div>
                  </TableCell>
                  <TableCell>
                    <span
                      className="text-xs px-1.5 py-0.5 rounded"
                      style={{
                        background: 'var(--bg-elevated)',
                        color: 'var(--text-muted)',
                        border: '1px solid var(--border-color)',
                        fontFamily: 'var(--font-mono)',
                      }}
                    >
                      {entry.topic.replace(/_/g, ' ')}
                    </span>
                  </TableCell>
                  <TableCell>
                    <span
                      className="text-xs"
                      style={{ color: 'var(--text-muted)', fontFamily: 'var(--font-mono)' }}
                    >
                      {CHANGE_TYPE_LABELS[entry.changeType] ?? entry.changeType.replace(/_/g, ' ')}
                    </span>
                  </TableCell>
                  <TableCell>
                    <span className="text-xs" style={{ color: 'var(--text-muted)' }}>
                      {entry.status ?? '—'}
                    </span>
                  </TableCell>
                </motion.tr>
              ))
            )}
          </TableBody>
        </Table>
      </div>
    </div>
  )
}
