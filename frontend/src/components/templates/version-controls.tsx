'use client'

import { motion } from 'framer-motion'
import { History, Clock, User, ChevronRight } from 'lucide-react'
import type { TemplateVersion } from '@/lib/api/template-hooks'

interface VersionControlsProps {
  versions: TemplateVersion[]
  currentVersionNumber: number
  onSelectVersion: (version: TemplateVersion) => void
}

function formatDate(ts: string): string {
  try {
    return new Date(ts).toLocaleDateString(undefined, { month: 'short', day: 'numeric', year: 'numeric', hour: '2-digit', minute: '2-digit' })
  } catch {
    return ts
  }
}

export function VersionControls({ versions, currentVersionNumber, onSelectVersion }: VersionControlsProps) {
  const sorted = [...versions].sort((a, b) => b.version_number - a.version_number)

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: 4 }}>
      <div style={{ display: 'flex', alignItems: 'center', gap: 6, marginBottom: 8 }}>
        <History size={14} color="var(--text-muted)" />
        <span style={{ fontSize: 12, fontWeight: 500, color: 'var(--text-secondary)' }}>
          Version history ({versions.length})
        </span>
      </div>

      {sorted.map((version) => {
        const isCurrent = version.version_number === currentVersionNumber
        return (
          <motion.div
            key={version.version_id}
            whileHover={{ x: 2 }}
            onClick={() => onSelectVersion(version)}
            style={{
              display: 'flex',
              alignItems: 'flex-start',
              gap: 10,
              padding: '10px 12px',
              borderRadius: 8,
              cursor: 'pointer',
              background: isCurrent ? 'rgba(var(--brand-accent-rgb),0.08)' : 'var(--bg-surface-raised)',
              border: isCurrent ? '1px solid rgba(var(--brand-accent-rgb),0.3)' : '1px solid var(--border-subtle)',
            }}
          >
            <div
              style={{
                width: 28,
                height: 28,
                borderRadius: 6,
                background: isCurrent ? 'rgba(var(--brand-accent-rgb),0.15)' : 'var(--bg-surface)',
                border: '1px solid var(--border-subtle)',
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center',
                flexShrink: 0,
                fontSize: 11,
                fontWeight: 600,
                color: isCurrent ? 'var(--brand-accent)' : 'var(--text-muted)',
              }}
            >
              v{version.version_number}
            </div>

            <div style={{ flex: 1, minWidth: 0 }}>
              <div style={{ display: 'flex', alignItems: 'center', gap: 6 }}>
                <span style={{ fontSize: 13, fontWeight: isCurrent ? 600 : 400, color: 'var(--text-primary)' }}>
                  Version {version.version_number}
                </span>
                {isCurrent && (
                  <span
                    style={{
                      fontSize: 10,
                      fontWeight: 500,
                      color: 'var(--brand-accent)',
                      background: 'rgba(var(--brand-accent-rgb),0.12)',
                      padding: '1px 6px',
                      borderRadius: 999,
                    }}
                  >
                    Current
                  </span>
                )}
              </div>

              {version.changelog && (
                <div style={{ fontSize: 12, color: 'var(--text-secondary)', marginTop: 2, overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>
                  {version.changelog}
                </div>
              )}

              <div style={{ display: 'flex', gap: 10, marginTop: 4 }}>
                <span style={{ fontSize: 11, color: 'var(--text-muted)', display: 'flex', alignItems: 'center', gap: 3 }}>
                  <Clock size={9} />
                  {formatDate(version.created_at)}
                </span>
                {version.created_by && (
                  <span style={{ fontSize: 11, color: 'var(--text-muted)', display: 'flex', alignItems: 'center', gap: 3 }}>
                    <User size={9} />
                    {version.created_by}
                  </span>
                )}
              </div>
            </div>

            <ChevronRight size={13} color="var(--text-muted)" style={{ flexShrink: 0, marginTop: 6 }} />
          </motion.div>
        )
      })}
    </div>
  )
}
