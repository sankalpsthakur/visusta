'use client'

import { motion, type Variants } from 'framer-motion'
import Link from 'next/link'
import { PageTransition } from '@/components/shared/page-transition'
import { AnimatedNumber } from '@/components/shared/animated-number'
import { useActiveClient } from '@/lib/clients/context'
import { useLocale } from '@/lib/i18n/dictionary-context'
import { MapPin, AlertTriangle, Calendar, ArrowRight } from 'lucide-react'
import { Skeleton } from '@/components/ui/skeleton'

const container: Variants = {
  hidden: { opacity: 0 },
  show: {
    opacity: 1,
    transition: {
      staggerChildren: 0.06,
    },
  },
}

const cardVariant: Variants = {
  hidden: { opacity: 0, y: 16 },
  show: { opacity: 1, y: 0, transition: { duration: 0.3, ease: 'easeOut' as const } },
}

function ClientCardSkeleton() {
  return (
    <div
      className="rounded-lg p-5"
      style={{ background: 'var(--bg-surface)', border: '1px solid var(--border-color)' }}
    >
      <Skeleton className="h-4 w-32 mb-2" style={{ background: 'var(--bg-elevated)' }} />
      <Skeleton className="h-3 w-20 mb-4" style={{ background: 'var(--bg-elevated)' }} />
      <div className="grid grid-cols-2 gap-3 mb-4">
        <Skeleton className="h-8 w-16" style={{ background: 'var(--bg-elevated)' }} />
        <Skeleton className="h-8 w-16" style={{ background: 'var(--bg-elevated)' }} />
      </div>
      <Skeleton className="h-3 w-full mb-3" style={{ background: 'var(--bg-elevated)' }} />
      <Skeleton className="h-3 w-24" style={{ background: 'var(--bg-elevated)' }} />
    </div>
  )
}

export default function HomePage() {
  const { clients, isLoading } = useActiveClient()
  const locale = useLocale()

  return (
    <PageTransition className="p-8">
      <div className="max-w-5xl">
        {/* Header */}
        <div className="mb-10">
          <h1
            className="text-3xl font-semibold tracking-tight mb-1"
            style={{ color: 'var(--text-primary)' }}
          >
            Visusta
          </h1>
          <p className="text-sm" style={{ color: 'var(--text-muted)' }}>
            ESG Regulatory Intelligence — {isLoading ? '…' : clients.length} active clients
          </p>
        </div>

        {/* Client overview cards */}
        {isLoading ? (
          <div className="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-3 gap-4">
            {[0, 1, 2].map((i) => (
              <ClientCardSkeleton key={i} />
            ))}
          </div>
        ) : (
          <motion.div
            variants={container}
            initial="hidden"
            animate="show"
            className="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-3 gap-4"
          >
            {clients.map((client) => (
              <motion.div key={client.id} variants={cardVariant}>
                <Link href={`/${locale}/clients/${client.id}`} className="block">
                  <motion.div
                    className="rounded-lg p-5 cursor-pointer"
                    style={{
                      background: 'var(--bg-surface)',
                      border: '1px solid var(--border-color)',
                    }}
                    whileHover={{ y: -2, borderColor: 'var(--brand)' }}
                    transition={{ duration: 0.15 }}
                  >
                    {/* Client name + jurisdiction */}
                    <div className="flex items-start justify-between mb-4">
                      <div>
                        <div
                          className="font-semibold text-sm mb-0.5"
                          style={{ color: 'var(--text-primary)' }}
                        >
                          {client.name}
                        </div>
                        <div
                          className="text-xs font-mono"
                          style={{ color: 'var(--text-muted)' }}
                        >
                          {client.allowed_countries.join(' / ')}
                        </div>
                      </div>
                    </div>

                    {/* Metrics row */}
                    <div className="grid grid-cols-2 gap-3 mb-4">
                      <div>
                        <div
                          className="text-xs mb-1"
                          style={{ color: 'var(--text-muted)' }}
                        >
                          Facilities
                        </div>
                        <div
                          className="text-xl font-semibold tabular-nums"
                          style={{ color: 'var(--text-primary)' }}
                        >
                          <AnimatedNumber value={client.facilities.length} />
                        </div>
                      </div>
                      <div>
                        <div
                          className="text-xs mb-1"
                          style={{ color: 'var(--text-muted)' }}
                        >
                          Topics
                        </div>
                        <div
                          className="text-xl font-semibold tabular-nums"
                          style={{ color: 'var(--text-primary)' }}
                        >
                          <AnimatedNumber value={client.required_topics.length} />
                        </div>
                      </div>
                    </div>

                    {/* Facilities list */}
                    <div
                      className="flex items-center gap-1 text-xs mb-3"
                      style={{ color: 'var(--text-muted)' }}
                    >
                      <MapPin className="w-3 h-3 flex-shrink-0" />
                      {client.facilities.map((f) => f.name).join(', ') || 'No facilities'}
                    </div>

                    {/* Footer */}
                    <div
                      className="flex items-center justify-between pt-3"
                      style={{ borderTop: '1px solid var(--border-color)' }}
                    >
                      <div
                        className="flex items-center gap-1 text-xs"
                        style={{ color: 'var(--text-muted)' }}
                      >
                        <Calendar className="w-3 h-3" />
                        {client.id}
                      </div>
                      <ArrowRight
                        className="w-3.5 h-3.5"
                        style={{ color: 'var(--brand-accent)' }}
                      />
                    </div>
                  </motion.div>
                </Link>
              </motion.div>
            ))}
          </motion.div>
        )}
      </div>
    </PageTransition>
  )
}
