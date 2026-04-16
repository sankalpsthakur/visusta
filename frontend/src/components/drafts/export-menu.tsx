'use client'

import { useState, useRef, useEffect } from 'react'
import { motion, AnimatePresence } from 'framer-motion'
import { FileText, FileJson, File, Download, Loader2, Lock } from 'lucide-react'
import type { DraftStatus } from '@/lib/api/draft-hooks'

type ExportFormat = 'pdf' | 'docx' | 'json'

interface ExportMenuProps {
  onExport: (format: ExportFormat) => Promise<void>
  isOpen: boolean
  onClose: () => void
  draftStatus: DraftStatus
}

const FORMAT_OPTIONS: { format: ExportFormat; label: string; description: string; icon: React.ReactNode }[] = [
  { format: 'pdf', label: 'PDF', description: 'Print-ready document', icon: <FileText size={15} /> },
  { format: 'docx', label: 'Word', description: 'Editable .docx file', icon: <File size={15} /> },
  { format: 'json', label: 'JSON', description: 'Structured data export', icon: <FileJson size={15} /> },
]

export function ExportMenu({ onExport, isOpen, onClose, draftStatus }: ExportMenuProps) {
  const [loadingFormat, setLoadingFormat] = useState<ExportFormat | null>(null)
  const ref = useRef<HTMLDivElement>(null)
  const pdfLocked = draftStatus !== 'approved' && draftStatus !== 'exported'

  useEffect(() => {
    function handleClickOutside(e: MouseEvent) {
      if (ref.current && !ref.current.contains(e.target as Node)) onClose()
    }
    if (isOpen) document.addEventListener('mousedown', handleClickOutside)
    return () => document.removeEventListener('mousedown', handleClickOutside)
  }, [isOpen, onClose])

  async function handleSelect(format: ExportFormat) {
    setLoadingFormat(format)
    try {
      await onExport(format)
    } finally {
      setLoadingFormat(null)
      onClose()
    }
  }

  return (
    <AnimatePresence>
      {isOpen && (
        <motion.div
          ref={ref}
          initial={{ opacity: 0, scale: 0.95, y: -4 }}
          animate={{ opacity: 1, scale: 1, y: 0 }}
          exit={{ opacity: 0, scale: 0.95, y: -4 }}
          style={{
            position: 'absolute',
            top: 44,
            right: 0,
            background: 'var(--bg-surface)',
            border: '1px solid var(--border-subtle)',
            borderRadius: 12,
            boxShadow: '0 12px 32px rgba(0,0,0,0.16)',
            zIndex: 200,
            minWidth: 220,
            overflow: 'hidden',
          }}
        >
          <div style={{ padding: '8px 0' }}>
            <div style={{ padding: '6px 14px 10px', fontSize: 11, fontWeight: 600, color: 'var(--text-muted)', textTransform: 'uppercase', letterSpacing: '0.06em' }}>
              Export as
            </div>
            {FORMAT_OPTIONS.map(({ format, label, description, icon }) => {
              const loading = loadingFormat === format
              const isLocked = format === 'pdf' && pdfLocked
              return (
                <motion.button
                  key={format}
                  whileHover={{ background: 'var(--bg-surface-raised)' }}
                  onClick={() => {
                    if (isLocked) return
                    void handleSelect(format)
                  }}
                  disabled={!!loadingFormat || isLocked}
                  style={{
                    display: 'flex',
                    alignItems: 'center',
                    gap: 12,
                    width: '100%',
                    padding: '10px 14px',
                    border: 'none',
                    background: 'transparent',
                    cursor: loadingFormat || isLocked ? 'not-allowed' : 'pointer',
                    textAlign: 'left',
                    opacity: (loadingFormat && !loading) || isLocked ? 0.4 : 1,
                  }}
                >
                  <div
                    style={{
                      width: 32,
                      height: 32,
                      borderRadius: 8,
                      background: 'var(--bg-surface-raised)',
                      border: '1px solid var(--border-subtle)',
                      display: 'flex',
                      alignItems: 'center',
                      justifyContent: 'center',
                      color: 'var(--text-secondary)',
                      flexShrink: 0,
                    }}
                  >
                    {loading ? <Loader2 size={14} style={{ animation: 'spin 1s linear infinite' }} /> : icon}
                  </div>
                  <div>
                    <div style={{ fontSize: 13, fontWeight: 500, color: 'var(--text-primary)' }}>{label}</div>
                    <div style={{ fontSize: 11, color: 'var(--text-muted)' }}>
                      {isLocked ? 'Requires approved status' : description}
                    </div>
                  </div>
                  {isLocked ? (
                    <Lock size={12} color="var(--text-muted)" style={{ marginLeft: 'auto' }} />
                  ) : (
                    !loading && <Download size={12} color="var(--text-muted)" style={{ marginLeft: 'auto' }} />
                  )}
                </motion.button>
              )
            })}
          </div>
        </motion.div>
      )}
    </AnimatePresence>
  )
}
