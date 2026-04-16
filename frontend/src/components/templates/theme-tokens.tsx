'use client'

import { useState, useEffect } from 'react'
import { motion } from 'framer-motion'
import { Palette, Save, RotateCcw } from 'lucide-react'

const DEFAULT_TOKENS: Record<string, string> = {
  '--brand-primary': '#1a1a2e',
  '--brand-accent': '#4f46e5',
  '--brand-accent-secondary': '#7c3aed',
  '--heading-font': 'Fraunces, serif',
  '--body-font': 'Inter, sans-serif',
  '--report-bg': '#ffffff',
  '--report-text': '#1a1a2e',
}

interface ThemeTokensProps {
  tokens: Record<string, string>
  onSave: (tokens: Record<string, string>) => void
  isSaving?: boolean
  readOnly?: boolean
}

function isColorToken(key: string): boolean {
  return key.includes('color') || key.includes('bg') || key.includes('accent') || key.includes('primary') || key.includes('text')
}

function isHexColor(value: string): boolean {
  return /^#[0-9a-fA-F]{3,8}$/.test(value)
}

export function ThemeTokens({ tokens: initialTokens, onSave, isSaving, readOnly }: ThemeTokensProps) {
  const [tokens, setTokens] = useState<Record<string, string>>({ ...DEFAULT_TOKENS, ...initialTokens })

  useEffect(() => {
    setTokens({ ...DEFAULT_TOKENS, ...initialTokens })
  }, [JSON.stringify(initialTokens)])

  function updateToken(key: string, value: string) {
    setTokens((prev) => ({ ...prev, [key]: value }))
  }

  function handleReset() {
    setTokens({ ...DEFAULT_TOKENS, ...initialTokens })
  }

  const isDirty = JSON.stringify(tokens) !== JSON.stringify({ ...DEFAULT_TOKENS, ...initialTokens })

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: 16 }}>
      <div style={{ display: 'flex', alignItems: 'center', gap: 8, marginBottom: 4 }}>
        <Palette size={16} color="var(--brand-accent)" />
        <span style={{ fontSize: 13, fontWeight: 500, color: 'var(--text-primary)' }}>Theme tokens</span>
        <span style={{ fontSize: 11, color: 'var(--text-muted)', marginLeft: 'auto' }}>
          CSS variables applied to generated PDFs
        </span>
      </div>

      <div style={{ display: 'flex', flexDirection: 'column', gap: 10 }}>
        {Object.entries(tokens).map(([key, value]) => (
          <motion.div
            key={key}
            layout
            style={{ display: 'flex', alignItems: 'center', gap: 10 }}
          >
            <code
              style={{
                fontSize: 11,
                color: 'var(--text-secondary)',
                background: 'var(--bg-surface-raised)',
                padding: '3px 8px',
                borderRadius: 4,
                minWidth: 220,
                flexShrink: 0,
              }}
            >
              {key}
            </code>

            <div style={{ display: 'flex', alignItems: 'center', gap: 8, flex: 1 }}>
              {isHexColor(value) && !readOnly && (
                <input
                  type="color"
                  value={value}
                  onChange={(e) => updateToken(key, e.target.value)}
                  style={{ width: 32, height: 32, borderRadius: 6, border: '1px solid var(--border-subtle)', padding: 2, cursor: 'pointer' }}
                />
              )}
              {isHexColor(value) && readOnly && (
                <div style={{ width: 20, height: 20, borderRadius: 4, background: value, border: '1px solid var(--border-subtle)' }} />
              )}
              <input
                value={value}
                onChange={(e) => updateToken(key, e.target.value)}
                disabled={readOnly}
                style={{
                  flex: 1,
                  padding: '6px 10px',
                  borderRadius: 6,
                  border: '1px solid var(--border-subtle)',
                  background: 'var(--bg-surface-raised)',
                  color: 'var(--text-primary)',
                  fontSize: 13,
                  fontFamily: 'monospace',
                }}
              />
            </div>
          </motion.div>
        ))}
      </div>

      {!readOnly && (
        <div style={{ display: 'flex', gap: 8, justifyContent: 'flex-end', paddingTop: 8, borderTop: '1px solid var(--border-subtle)' }}>
          <motion.button
            whileHover={{ scale: 1.02 }}
            whileTap={{ scale: 0.98 }}
            onClick={handleReset}
            disabled={!isDirty}
            style={{
              display: 'flex',
              alignItems: 'center',
              gap: 6,
              padding: '7px 14px',
              borderRadius: 8,
              border: '1px solid var(--border-subtle)',
              background: 'transparent',
              color: 'var(--text-secondary)',
              fontSize: 13,
              cursor: isDirty ? 'pointer' : 'not-allowed',
              opacity: isDirty ? 1 : 0.4,
            }}
          >
            <RotateCcw size={13} />
            Reset
          </motion.button>

          <motion.button
            whileHover={{ scale: 1.02 }}
            whileTap={{ scale: 0.98 }}
            onClick={() => onSave(tokens)}
            disabled={!isDirty || isSaving}
            style={{
              display: 'flex',
              alignItems: 'center',
              gap: 6,
              padding: '7px 16px',
              borderRadius: 8,
              border: 'none',
              background: isDirty && !isSaving ? 'var(--brand-accent)' : 'var(--bg-surface-raised)',
              color: isDirty && !isSaving ? '#fff' : 'var(--text-muted)',
              fontSize: 13,
              fontWeight: 500,
              cursor: !isDirty || isSaving ? 'not-allowed' : 'pointer',
              transition: 'background 0.15s, color 0.15s',
            }}
          >
            <Save size={13} />
            {isSaving ? 'Saving…' : 'Save theme'}
          </motion.button>
        </div>
      )}
    </div>
  )
}
