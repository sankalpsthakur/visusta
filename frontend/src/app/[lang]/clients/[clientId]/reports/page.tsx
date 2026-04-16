'use client'

import { use, useState } from 'react'
import { motion, AnimatePresence } from 'framer-motion'
import { PageTransition } from '@/components/shared/page-transition'
import { Skeleton } from '@/components/ui/skeleton'
import { ErrorBoundary } from '@/components/shared/error-boundary'
import { FileText, Download, Play, Clock } from 'lucide-react'
import {
  useGenerateMonthlyReport,
  useGenerateQuarterlyReport,
  useChangelogs,
  usePreferences,
} from '@/lib/api/hooks'

const REPORT_TYPE_META = [
  {
    id: 'monthly',
    label: 'Monthly Impact Report',
    description: 'Regulatory changes, screening results, and compliance status for the period.',
  },
  {
    id: 'quarterly',
    label: 'Quarterly Strategic Brief',
    description: 'Executive summary with trend analysis, risk prioritization, and forward planning.',
  },
]

function deriveQuarterlyPeriods(monthlyPeriods: string[]): string[] {
  const seen = new Set<string>()
  const quarters: string[] = []
  for (const p of [...monthlyPeriods].reverse()) {
    const [year, month] = p.split('-')
    const q = Math.ceil(parseInt(month) / 3)
    const label = `Q${q} ${year}`
    if (!seen.has(label)) {
      seen.add(label)
      quarters.push(label)
    }
  }
  return quarters
}

interface ReportsPageProps {
  params: Promise<{ clientId: string }>
}

function PeriodSkeleton() {
  return (
    <div className="flex flex-wrap gap-1.5">
      {[0, 1, 2].map((i) => (
        <Skeleton key={i} className="h-6 w-16 rounded" style={{ background: 'var(--bg-elevated)' }} />
      ))}
    </div>
  )
}

export default function ReportsPage({ params }: ReportsPageProps) {
  const { clientId } = use(params)
  const monthlyMutation = useGenerateMonthlyReport(clientId)
  const quarterlyMutation = useGenerateQuarterlyReport(clientId)
  const { data: changelogsData, isLoading: changelogsLoading } = useChangelogs(clientId)
  const { data: prefs } = usePreferences(clientId)

  const monthlyPeriods = changelogsData?.periods ?? []
  const quarterlyPeriods = deriveQuarterlyPeriods(monthlyPeriods)
  const isNewClient = !changelogsLoading && monthlyPeriods.length === 0

  const [selectedPeriods, setSelectedPeriods] = useState<Record<string, string>>({
    monthly: '',
    quarterly: '',
  })
  const [pdfUrl, setPdfUrl] = useState<string | null>(null)
  const [pdfFilename, setPdfFilename] = useState<string>('')

  const getSelectedPeriod = (id: string) => {
    if (id === 'monthly') return selectedPeriods.monthly || monthlyPeriods[monthlyPeriods.length - 1] || ''
    return selectedPeriods.quarterly || quarterlyPeriods[0] || ''
  }

  const getPeriods = (id: string) => id === 'monthly' ? monthlyPeriods : quarterlyPeriods

  const isGenerating = (id: string) =>
    id === 'monthly' ? monthlyMutation.isPending : quarterlyMutation.isPending

  const handleGenerate = async (reportId: string) => {
    const period = getSelectedPeriod(reportId)
    if (!period) return
    try {
      if (reportId === 'monthly') {
        const result = await monthlyMutation.mutateAsync({ period, preferences: prefs })
        setPdfUrl(result.blobUrl)
        setPdfFilename(result.filename)
      } else {
        const [q, y] = period.replace('Q', '').split(' ')
        const result = await quarterlyMutation.mutateAsync({ quarter: parseInt(q), year: parseInt(y), preferences: prefs })
        setPdfUrl(result.blobUrl)
        setPdfFilename(result.filename)
      }
    } catch {
      // mutation.isError handles display
    }
  }

  return (
    <PageTransition className="p-8">
      <div className="max-w-4xl">
        <div className="mb-6">
          <h2 className="text-lg font-semibold mb-1" style={{ color: 'var(--text-primary)' }}>
            Report Studio
          </h2>
          <p className="text-sm" style={{ color: 'var(--text-muted)' }}>
            Generate and download compliance reports
          </p>
        </div>

        {/* Report builders */}
        <ErrorBoundary>
          <motion.div
            initial="hidden"
            animate="show"
            variants={{ hidden: {}, show: { transition: { staggerChildren: 0.06 } } }}
            className="grid grid-cols-2 gap-4 mb-8"
          >
            {REPORT_TYPE_META.map((report) => {
              const periods = getPeriods(report.id)
              const selected = getSelectedPeriod(report.id)
              return (
                <motion.div
                  key={report.id}
                  variants={{ hidden: { opacity: 0, y: 12 }, show: { opacity: 1, y: 0, transition: { duration: 0.2, ease: 'easeOut' } } }}
                  className="rounded-lg p-5"
                  style={{ background: 'var(--bg-surface)', border: '1px solid var(--border-color)' }}
                >
                  <div className="flex items-center gap-2 mb-2">
                    <FileText className="w-4 h-4 flex-shrink-0" style={{ color: 'var(--brand)' }} />
                    <span className="text-sm font-semibold" style={{ color: 'var(--text-primary)' }}>
                      {report.label}
                    </span>
                  </div>
                  <p className="text-xs mb-4 leading-relaxed" style={{ color: 'var(--text-muted)' }}>
                    {report.description}
                  </p>

                  <div className="mb-4">
                    <div className="text-xs mb-2" style={{ color: 'var(--text-muted)' }}>Period</div>
                    <div className="flex flex-wrap gap-1.5 items-center">
                      {changelogsLoading ? (
                        <PeriodSkeleton />
                      ) : (
                        <>
                          {periods.map((period) => (
                            <button
                              key={period}
                              onClick={() =>
                                setSelectedPeriods((prev) => ({ ...prev, [report.id]: period }))
                              }
                              className="text-xs px-2.5 py-1 rounded transition-all"
                              style={{
                                background: selected === period ? 'var(--brand)' : 'var(--bg-elevated)',
                                color: selected === period ? 'var(--brand-contrast)' : 'var(--text-muted)',
                                border: '1px solid var(--border-color)',
                                fontFamily: 'var(--font-mono)',
                              }}
                            >
                              {period}
                            </button>
                          ))}
                          <input
                            type="text"
                            placeholder={report.id === 'monthly' ? '2026-04' : 'Q2 2026'}
                            value={!periods.includes(selected) ? selected : ''}
                            onChange={(e) =>
                              setSelectedPeriods((prev) => ({ ...prev, [report.id]: e.target.value }))
                            }
                            className="text-xs px-2.5 py-1 rounded"
                            style={{
                              width: 80,
                              background: 'var(--bg-elevated)',
                              color: 'var(--text-primary)',
                              border: '1px solid var(--border-color)',
                              fontFamily: 'var(--font-mono)',
                            }}
                          />
                        </>
                      )}
                    </div>
                  </div>

                  <motion.button
                    onClick={() => handleGenerate(report.id)}
                    disabled={isGenerating(report.id) || !selected}
                    className="w-full flex items-center justify-center gap-2 py-2 rounded text-sm font-medium"
                    style={{
                      background: isGenerating(report.id) ? 'var(--bg-elevated)' : 'var(--brand)',
                      color: 'var(--brand-contrast)',
                      opacity: (isGenerating(report.id) || !selected) ? 0.7 : 1,
                    }}
                    whileHover={{ opacity: 0.9 }}
                    whileTap={{ scale: 0.98 }}
                  >
                    {isGenerating(report.id) ? (
                      <><Clock className="w-3.5 h-3.5 animate-spin" />Generating...</>
                    ) : (
                      <><Play className="w-3.5 h-3.5" />Generate</>
                    )}
                  </motion.button>

                  {((report.id === 'monthly' && monthlyMutation.isError) ||
                    (report.id === 'quarterly' && quarterlyMutation.isError)) && (
                    <div
                      className="mt-2 text-xs px-2 py-1.5 rounded"
                      style={{
                        background: 'color-mix(in srgb, var(--severity-critical) 10%, transparent)',
                        color: 'var(--severity-critical)',
                      }}
                    >
                      {(report.id === 'monthly' ? monthlyMutation.error : quarterlyMutation.error)?.message ?? 'Generation failed'}
                    </div>
                  )}
                </motion.div>
              )
            })}
          </motion.div>
        </ErrorBoundary>

        {/* PDF preview */}
        <AnimatePresence>
          {pdfUrl && (
            <motion.div
              initial={{ opacity: 0, y: 8 }}
              animate={{ opacity: 1, y: 0 }}
              exit={{ opacity: 0 }}
              className="rounded-lg overflow-hidden mb-8"
              style={{ border: '1px solid var(--border-color)' }}
            >
              <div
                className="flex items-center justify-between px-4 py-3"
                style={{ background: 'var(--bg-elevated)', borderBottom: '1px solid var(--border-color)' }}
              >
                <span className="text-xs" style={{ color: 'var(--text-muted)', fontFamily: 'var(--font-mono)' }}>
                  {pdfFilename}
                </span>
                <button
                  onClick={() => {
                    const link = document.createElement('a')
                    link.href = pdfUrl
                    link.download = pdfFilename
                    link.click()
                  }}
                  className="flex items-center gap-1.5 text-xs px-3 py-1 rounded"
                  style={{ background: 'var(--brand)', color: 'var(--brand-contrast)' }}
                >
                  <Download className="w-3 h-3" />
                  Download
                </button>
              </div>
              <iframe
                src={pdfUrl}
                title="Report preview"
                className="w-full"
                style={{ height: 480, background: 'var(--bg-surface)' }}
              />
            </motion.div>
          )}
        </AnimatePresence>

        {/* Recent reports */}
        <ErrorBoundary>
          <div>
            <div className="text-xs font-medium mb-3" style={{ color: 'var(--text-muted)' }}>
              Recent Reports
            </div>
            <div className="rounded-lg overflow-hidden" style={{ border: '1px solid var(--border-color)' }}>
              <div className="px-5 py-8 text-center" style={{ background: 'var(--bg-surface)' }}>
                <p className="text-xs" style={{ color: 'var(--text-muted)' }}>
                  No reports generated yet. Use the builders above.
                </p>
              </div>
            </div>
          </div>
        </ErrorBoundary>
      </div>
    </PageTransition>
  )
}
