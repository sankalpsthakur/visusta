'use client'

import Link from 'next/link'
import { usePathname } from 'next/navigation'
import { use } from 'react'
import { useClient } from '@/lib/api/hooks'

const TABS = [
  { label: 'Dashboard', segment: '' },
  { label: 'Regulatory', segment: 'regulatory' },
  { label: 'Evidence', segment: 'evidence' },
  { label: 'Reports', segment: 'reports' },
  { label: 'Audit', segment: 'audit' },
  { label: 'Settings', segment: 'settings' },
]

interface ClientLayoutProps {
  children: React.ReactNode
  params: Promise<{ clientId: string }>
}

export default function ClientLayout({ children, params }: ClientLayoutProps) {
  const { clientId } = use(params)
  const pathname = usePathname()
  const { data: client } = useClient(clientId)

  const baseHref = `/clients/${clientId}`

  const isTabActive = (segment: string) => {
    if (segment === '') return pathname === baseHref
    return pathname.startsWith(`${baseHref}/${segment}`)
  }

  return (
    <div className="flex flex-col h-full">
      {/* Client header */}
      <div
        className="flex items-center justify-between px-8 h-14 flex-shrink-0"
        style={{
          borderBottom: '1px solid var(--border-color)',
          background: 'var(--bg-surface)',
        }}
      >
        <div className="flex items-center gap-3">
          <Link href="/clients" className="text-xs" style={{ color: 'var(--text-muted)' }}>
            Clients
          </Link>
          <span style={{ color: 'var(--border-color)' }}>/</span>
          <span className="text-sm font-medium" style={{ color: 'var(--text-primary)' }}>
            {client?.display_name ?? clientId}
          </span>
        </div>
        <div className="flex items-center gap-2">
          {client?.allowed_countries.map((j) => (
            <span
              key={j}
              className="text-xs px-2 py-0.5 rounded font-mono"
              style={{
                background: 'var(--bg-elevated)',
                color: 'var(--text-muted)',
                border: '1px solid var(--border-color)',
              }}
            >
              {j}
            </span>
          ))}
        </div>
      </div>

      {/* Tab navigation */}
      <div
        className="flex items-end gap-0 px-8 flex-shrink-0"
        style={{ borderBottom: '1px solid var(--border-color)' }}
      >
        {TABS.map((tab) => {
          const href = tab.segment ? `${baseHref}/${tab.segment}` : baseHref
          const active = isTabActive(tab.segment)
          return (
            <Link
              key={tab.segment}
              href={href}
              className="relative px-4 py-3 text-sm transition-colors"
              style={{
                color: active ? 'var(--text-primary)' : 'var(--text-muted)',
              }}
            >
              {tab.label}
              {active && (
                <span
                  className="absolute bottom-0 left-0 right-0 h-0.5 rounded-t-full"
                  style={{ background: 'var(--brand-accent)' }}
                />
              )}
            </Link>
          )
        })}
      </div>

      {/* Content */}
      <div className="flex-1 overflow-y-auto">
        {children}
      </div>
    </div>
  )
}
