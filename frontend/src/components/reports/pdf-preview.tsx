'use client'

import { useState, useRef } from 'react'
import { Download, Maximize2, Minimize2, FileText } from 'lucide-react'

interface PdfPreviewProps {
  blobUrl: string | null
  filename: string
}

export function PdfPreview({ blobUrl, filename }: PdfPreviewProps) {
  const [fullscreen, setFullscreen] = useState(false)
  const downloadRef = useRef<HTMLAnchorElement>(null)

  const handleDownload = () => {
    if (!blobUrl) return
    const a = document.createElement('a')
    a.href = blobUrl
    a.download = filename
    a.click()
  }

  const containerStyle: React.CSSProperties = fullscreen
    ? {
        position: 'fixed',
        inset: 0,
        zIndex: 50,
        background: 'var(--bg-primary)',
        display: 'flex',
        flexDirection: 'column',
      }
    : {
        display: 'flex',
        flexDirection: 'column',
        border: '1px solid var(--border-color)',
        borderRadius: '0.5rem',
        overflow: 'hidden',
        height: '600px',
      }

  return (
    <div style={containerStyle}>
      {/* Toolbar */}
      <div
        className="flex items-center justify-between px-4 py-2 flex-shrink-0"
        style={{
          background: 'var(--bg-elevated)',
          borderBottom: '1px solid var(--border-color)',
        }}
      >
        <span
          className="text-xs truncate"
          style={{ color: 'var(--text-muted)', fontFamily: 'var(--font-mono)' }}
        >
          {filename}
        </span>
        <div className="flex items-center gap-2 ml-4">
          {blobUrl && (
            <>
              <a ref={downloadRef} style={{ display: 'none' }} />
              <button
                onClick={handleDownload}
                className="flex items-center gap-1.5 text-xs px-2.5 py-1 rounded transition-opacity hover:opacity-80"
                style={{
                  background: 'var(--brand)',
                  color: 'var(--brand-contrast)',
                }}
              >
                <Download className="w-3.5 h-3.5" />
                Download
              </button>
            </>
          )}
          <button
            onClick={() => setFullscreen((f) => !f)}
            className="p-1.5 rounded transition-opacity hover:opacity-80"
            style={{ color: 'var(--text-muted)' }}
            title={fullscreen ? 'Exit fullscreen' : 'Fullscreen'}
          >
            {fullscreen ? (
              <Minimize2 className="w-4 h-4" />
            ) : (
              <Maximize2 className="w-4 h-4" />
            )}
          </button>
        </div>
      </div>

      {/* Content */}
      <div className="flex-1 min-h-0">
        {blobUrl ? (
          <iframe
            src={blobUrl}
            className="w-full h-full"
            title={filename}
            style={{ border: 'none', display: 'block' }}
          />
        ) : (
          <div
            className="w-full h-full flex flex-col items-center justify-center gap-3"
            style={{ background: 'var(--bg-surface)' }}
          >
            <FileText
              className="w-10 h-10"
              style={{ color: 'var(--text-muted)', opacity: 0.4 }}
            />
            <span className="text-sm" style={{ color: 'var(--text-muted)' }}>
              No report generated yet
            </span>
          </div>
        )}
      </div>
    </div>
  )
}
