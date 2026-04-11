'use client'

import { use } from 'react'
import Link from 'next/link'
import { PageTransition } from '@/components/shared/page-transition'
import { ErrorBoundary } from '@/components/shared/error-boundary'
import { EvidenceDetail } from '@/components/evidence/evidence-detail'
import { useEvidenceRecord } from '@/lib/api/hooks'
import { ArrowLeft } from 'lucide-react'

interface EvidenceDetailPageProps {
  params: Promise<{ clientId: string; evidenceId: string }>
}

export default function EvidenceDetailPage({ params }: EvidenceDetailPageProps) {
  const { clientId, evidenceId } = use(params)
  const { data: record, isLoading, error } = useEvidenceRecord(clientId, evidenceId)

  return (
    <PageTransition className="p-8">
      <div className="max-w-3xl">
        <Link
          href={`/clients/${clientId}/evidence`}
          className="inline-flex items-center gap-1.5 text-xs mb-6 transition-opacity hover:opacity-70"
          style={{ color: 'var(--text-muted)' }}
        >
          <ArrowLeft className="w-3.5 h-3.5" />
          Evidence
        </Link>

        <ErrorBoundary>
          <EvidenceDetail
            record={record}
            isLoading={isLoading}
            error={error instanceof Error ? error : error ? new Error(String(error)) : null}
          />
        </ErrorBoundary>
      </div>
    </PageTransition>
  )
}
