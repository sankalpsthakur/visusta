'use client'

import { useState, useRef } from 'react'
import { useCreateEvidence, useUploadEvidence, useSources } from '@/lib/api/hooks'
import { Upload } from 'lucide-react'

const ESG_TOPICS = [
  { value: 'ghg', label: 'GHG Emissions' },
  { value: 'water', label: 'Water' },
  { value: 'waste', label: 'Waste' },
  { value: 'packaging', label: 'Packaging' },
  { value: 'social_human_rights', label: 'Social / Human Rights' },
]

interface EvidenceUploadProps {
  clientId: string
}

export function EvidenceUpload({ clientId }: EvidenceUploadProps) {
  const { data: sources } = useSources(clientId)
  const createEvidence = useCreateEvidence(clientId)
  const uploadEvidence = useUploadEvidence(clientId)

  const [url, setUrl] = useState('')
  const [sourceId, setSourceId] = useState('')
  const [documentTitle, setDocumentTitle] = useState('')
  const [topic, setTopic] = useState('')
  const [successMsg, setSuccessMsg] = useState('')
  const [isDragging, setIsDragging] = useState(false)
  const fileInputRef = useRef<HTMLInputElement>(null)

  const isPending = createEvidence.isPending || uploadEvidence.isPending
  const mutationError = createEvidence.error ?? uploadEvidence.error

  function showSuccess() {
    setSuccessMsg('Evidence ingested')
    setTimeout(() => setSuccessMsg(''), 3000)
  }

  function resetForm() {
    setUrl('')
    setSourceId('')
    setDocumentTitle('')
    setTopic('')
  }

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    if (!url) return

    await createEvidence.mutateAsync({
      url,
      source_id: sourceId || undefined,
      document_title: documentTitle || undefined,
      topic: topic || undefined,
    } as Parameters<typeof createEvidence.mutateAsync>[0])

    resetForm()
    showSuccess()
  }

  const handleFile = async (file: File) => {
    if (!file.type.includes('pdf') && !file.name.endsWith('.pdf')) return
    const fd = new FormData()
    fd.append('file', file)
    if (sourceId) fd.append('source_id', sourceId)
    if (documentTitle) fd.append('document_title', documentTitle)
    if (topic) fd.append('topic', topic)
    await uploadEvidence.mutateAsync(fd)
    resetForm()
    showSuccess()
  }

  const handleDrop = (e: React.DragEvent) => {
    e.preventDefault()
    setIsDragging(false)
    const file = e.dataTransfer.files[0]
    if (file) void handleFile(file)
  }

  return (
    <div
      className="rounded-lg p-5 mb-6"
      style={{ background: 'var(--bg-surface)', border: '1px solid var(--border-color)' }}
    >
      <div className="text-xs font-medium mb-3" style={{ color: 'var(--text-muted)' }}>
        Add Evidence Record
      </div>

      {/* PDF drop zone */}
      <div
        className="rounded-lg mb-3 flex flex-col items-center justify-center gap-1.5 cursor-pointer transition-colors"
        style={{
          border: `1.5px dashed ${isDragging ? 'var(--brand-accent)' : 'var(--border-color)'}`,
          background: isDragging
            ? 'color-mix(in srgb, var(--brand-accent) 6%, transparent)'
            : 'var(--bg-elevated)',
          padding: '20px',
        }}
        onDragOver={(e) => { e.preventDefault(); setIsDragging(true) }}
        onDragLeave={() => setIsDragging(false)}
        onDrop={handleDrop}
        onClick={() => fileInputRef.current?.click()}
      >
        <Upload className="w-4 h-4" style={{ color: 'var(--text-muted)' }} />
        <span className="text-xs" style={{ color: 'var(--text-muted)' }}>
          Drag a PDF or{' '}
          <span style={{ color: 'var(--brand-accent)' }}>browse</span>
        </span>
        <input
          ref={fileInputRef}
          type="file"
          accept=".pdf,application/pdf"
          className="hidden"
          onChange={(e) => { const f = e.target.files?.[0]; if (f) void handleFile(f) }}
        />
      </div>

      <form onSubmit={handleSubmit}>
        <div className="grid grid-cols-1 gap-3">
          <div className="flex gap-3">
            <input
              type="url"
              required
              placeholder="Paste a URL (required)"
              value={url}
              onChange={(e) => setUrl(e.target.value)}
              className="flex-1 text-sm px-3 py-2 rounded outline-none"
              style={{
                background: 'var(--bg-elevated)',
                border: '1px solid var(--border-color)',
                color: 'var(--text-primary)',
              }}
            />
            <input
              type="text"
              placeholder="Document title"
              value={documentTitle}
              onChange={(e) => setDocumentTitle(e.target.value)}
              className="flex-1 text-sm px-3 py-2 rounded outline-none"
              style={{
                background: 'var(--bg-elevated)',
                border: '1px solid var(--border-color)',
                color: 'var(--text-primary)',
              }}
            />
          </div>
          <div className="flex gap-3 items-center">
            <select
              value={sourceId}
              onChange={(e) => setSourceId(e.target.value)}
              className="flex-1 text-sm px-3 py-2 rounded outline-none"
              style={{
                background: 'var(--bg-elevated)',
                border: '1px solid var(--border-color)',
                color: sourceId ? 'var(--text-primary)' : 'var(--text-muted)',
              }}
            >
              <option value="">Source (optional)</option>
              {sources?.map((s) => (
                <option key={s.id} value={s.id}>{s.display_name}</option>
              ))}
            </select>
            <select
              value={topic}
              onChange={(e) => setTopic(e.target.value)}
              className="flex-1 text-sm px-3 py-2 rounded outline-none"
              style={{
                background: 'var(--bg-elevated)',
                border: '1px solid var(--border-color)',
                color: topic ? 'var(--text-primary)' : 'var(--text-muted)',
              }}
            >
              <option value="">Topic (optional)</option>
              {ESG_TOPICS.map((t) => (
                <option key={t.value} value={t.value}>{t.label}</option>
              ))}
            </select>
            <button
              type="submit"
              disabled={isPending || !url}
              className="px-4 py-2 text-sm rounded font-medium transition-opacity"
              style={{
                background: 'var(--brand-accent)',
                color: 'var(--brand-contrast)',
                opacity: isPending || !url ? 0.5 : 1,
                cursor: isPending || !url ? 'not-allowed' : 'pointer',
              }}
            >
              {isPending ? 'Ingesting…' : 'Ingest'}
            </button>
          </div>
        </div>
      </form>

      {successMsg && (
        <div className="mt-2 text-xs" style={{ color: 'var(--severity-low)' }}>
          {successMsg}
        </div>
      )}
      {mutationError && (
        <div className="mt-2 text-xs" style={{ color: 'var(--severity-critical)' }}>
          {(mutationError as Error).message}
        </div>
      )}
    </div>
  )
}
