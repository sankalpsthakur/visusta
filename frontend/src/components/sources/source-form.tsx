'use client'

import { useState, useEffect } from 'react'
import { motion } from 'framer-motion'
import { Save, X } from 'lucide-react'
import type { SourceConfig } from '@/lib/api/hooks'

interface SourceFormProps {
  initial?: Partial<SourceConfig>
  onSave: (source: Omit<SourceConfig, 'id'> & { id?: string }) => void
  onCancel: () => void
  isSaving?: boolean
}

const SOURCE_TYPES = ['gazette', 'agency', 'ministry', 'registry', 'legislature']
const FREQUENCIES = ['daily', 'weekly', 'monthly']

export function SourceForm({ initial, onSave, onCancel, isSaving }: SourceFormProps) {
  const [form, setForm] = useState({
    id: initial?.id ?? '',
    display_name: initial?.display_name ?? '',
    url: initial?.url ?? '',
    frequency: initial?.frequency ?? 'weekly',
    source_type: initial?.source_type ?? 'gazette',
  })

  useEffect(() => {
    setForm({
      id: initial?.id ?? '',
      display_name: initial?.display_name ?? '',
      url: initial?.url ?? '',
      frequency: initial?.frequency ?? 'weekly',
      source_type: initial?.source_type ?? 'gazette',
    })
  }, [initial?.id])

  function update(key: keyof typeof form, value: string) {
    setForm((prev) => ({ ...prev, [key]: value }))
  }

  const isValid = form.display_name.trim() && (initial?.id || form.id.trim())

  return (
    <motion.div
      initial={{ opacity: 0, y: -4 }}
      animate={{ opacity: 1, y: 0 }}
      style={{
        padding: '20px 24px',
        borderRadius: 12,
        border: '1px solid var(--border-subtle)',
        background: 'var(--bg-surface)',
        display: 'flex',
        flexDirection: 'column',
        gap: 14,
      }}
    >
      <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
        <span style={{ fontSize: 14, fontWeight: 500, color: 'var(--text-primary)' }}>
          {initial?.id ? 'Edit source' : 'Add source'}
        </span>
        <button onClick={onCancel} style={{ background: 'none', border: 'none', cursor: 'pointer', color: 'var(--text-muted)' }}>
          <X size={16} />
        </button>
      </div>

      <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 12 }}>
        <div>
          <label style={{ fontSize: 11, fontWeight: 500, color: 'var(--text-muted)', display: 'block', marginBottom: 5 }}>
            Display name *
          </label>
          <input
            aria-label="Source display name"
            value={form.display_name}
            onChange={(e) => update('display_name', e.target.value)}
            placeholder="EUR-Lex"
            style={{ width: '100%', padding: '7px 10px', borderRadius: 7, border: '1px solid var(--border-subtle)', background: 'var(--bg-surface-raised)', color: 'var(--text-primary)', fontSize: 13, boxSizing: 'border-box' }}
          />
        </div>

        {!initial?.id && (
          <div>
            <label style={{ fontSize: 11, fontWeight: 500, color: 'var(--text-muted)', display: 'block', marginBottom: 5 }}>
              Source ID *
            </label>
            <input
              aria-label="Source ID"
              value={form.id}
              onChange={(e) => update('id', e.target.value.toLowerCase().replace(/\s+/g, '_'))}
              placeholder="eur_lex"
              style={{ width: '100%', padding: '7px 10px', borderRadius: 7, border: '1px solid var(--border-subtle)', background: 'var(--bg-surface-raised)', color: 'var(--text-primary)', fontSize: 13, fontFamily: 'monospace', boxSizing: 'border-box' }}
            />
          </div>
        )}

        <div>
          <label style={{ fontSize: 11, fontWeight: 500, color: 'var(--text-muted)', display: 'block', marginBottom: 5 }}>
            Type
          </label>
          <select
            aria-label="Source type"
            value={form.source_type}
            onChange={(e) => update('source_type', e.target.value)}
            style={{ width: '100%', padding: '7px 10px', borderRadius: 7, border: '1px solid var(--border-subtle)', background: 'var(--bg-surface-raised)', color: 'var(--text-primary)', fontSize: 13, boxSizing: 'border-box' }}
          >
            {SOURCE_TYPES.map((t) => <option key={t} value={t}>{t}</option>)}
          </select>
        </div>

        <div>
          <label style={{ fontSize: 11, fontWeight: 500, color: 'var(--text-muted)', display: 'block', marginBottom: 5 }}>
            Frequency
          </label>
          <select
            aria-label="Source frequency"
            value={form.frequency}
            onChange={(e) => update('frequency', e.target.value)}
            style={{ width: '100%', padding: '7px 10px', borderRadius: 7, border: '1px solid var(--border-subtle)', background: 'var(--bg-surface-raised)', color: 'var(--text-primary)', fontSize: 13, boxSizing: 'border-box' }}
          >
            {FREQUENCIES.map((f) => <option key={f} value={f}>{f}</option>)}
          </select>
        </div>
      </div>

      <div>
        <label style={{ fontSize: 11, fontWeight: 500, color: 'var(--text-muted)', display: 'block', marginBottom: 5 }}>
          URL (optional)
        </label>
        <input
          aria-label="Source URL"
          value={form.url}
          onChange={(e) => update('url', e.target.value)}
          placeholder="https://eur-lex.europa.eu"
          style={{ width: '100%', padding: '7px 10px', borderRadius: 7, border: '1px solid var(--border-subtle)', background: 'var(--bg-surface-raised)', color: 'var(--text-primary)', fontSize: 13, boxSizing: 'border-box' }}
        />
      </div>

      <div style={{ display: 'flex', gap: 8, justifyContent: 'flex-end' }}>
        <button
          onClick={onCancel}
          style={{ padding: '7px 14px', borderRadius: 8, border: '1px solid var(--border-subtle)', background: 'transparent', color: 'var(--text-secondary)', fontSize: 13, cursor: 'pointer' }}
        >
          Cancel
        </button>
        <motion.button
          whileHover={{ scale: 1.02 }}
          whileTap={{ scale: 0.98 }}
          onClick={() => onSave(form)}
          disabled={!isValid || isSaving}
          style={{
            display: 'flex',
            alignItems: 'center',
            gap: 6,
            padding: '7px 16px',
            borderRadius: 8,
            border: 'none',
            background: isValid && !isSaving ? 'var(--brand-accent)' : 'var(--bg-surface-raised)',
            color: isValid && !isSaving ? '#fff' : 'var(--text-muted)',
            fontSize: 13,
            fontWeight: 500,
            cursor: !isValid || isSaving ? 'not-allowed' : 'pointer',
            transition: 'background 0.15s, color 0.15s',
          }}
        >
          <Save size={13} />
          {isSaving ? 'Saving…' : 'Save source'}
        </motion.button>
      </div>
    </motion.div>
  )
}
