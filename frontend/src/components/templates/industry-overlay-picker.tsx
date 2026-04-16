'use client'

import { motion } from 'framer-motion'
import { Tag, X, Plus } from 'lucide-react'
import { useState } from 'react'

const INDUSTRY_OPTIONS = [
  'food_beverage',
  'retail',
  'manufacturing',
  'logistics',
  'financial_services',
  'healthcare',
  'energy',
  'agriculture',
  'chemicals',
  'textiles',
  'construction',
  'technology',
]

interface IndustryOverlayPickerProps {
  selected: string[]
  onChange: (tags: string[]) => void
  readOnly?: boolean
}

export function IndustryOverlayPicker({ selected, onChange, readOnly }: IndustryOverlayPickerProps) {
  const [customInput, setCustomInput] = useState('')
  const [showCustom, setShowCustom] = useState(false)

  function toggle(tag: string) {
    if (readOnly) return
    onChange(selected.includes(tag) ? selected.filter((t) => t !== tag) : [...selected, tag])
  }

  function addCustom() {
    const tag = customInput.trim().toLowerCase().replace(/\s+/g, '_')
    if (!tag || selected.includes(tag)) return
    onChange([...selected, tag])
    setCustomInput('')
    setShowCustom(false)
  }

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: 10 }}>
      <div style={{ display: 'flex', flexWrap: 'wrap', gap: 6 }}>
        {INDUSTRY_OPTIONS.map((tag) => {
          const active = selected.includes(tag)
          return (
            <motion.button
              key={tag}
              whileHover={{ scale: readOnly ? 1 : 1.03 }}
              whileTap={{ scale: readOnly ? 1 : 0.97 }}
              onClick={() => toggle(tag)}
              disabled={readOnly}
              style={{
                display: 'inline-flex',
                alignItems: 'center',
                gap: 5,
                padding: '4px 12px',
                borderRadius: 999,
                border: active ? '1px solid rgba(var(--brand-accent-rgb),0.5)' : '1px solid var(--border-subtle)',
                background: active ? 'rgba(var(--brand-accent-rgb),0.1)' : 'var(--bg-surface-raised)',
                color: active ? 'var(--brand-accent)' : 'var(--text-secondary)',
                fontSize: 12,
                cursor: readOnly ? 'default' : 'pointer',
                transition: 'background 0.12s, color 0.12s, border-color 0.12s',
              }}
            >
              <Tag size={10} />
              {tag.replace(/_/g, ' ')}
              {active && <X size={9} />}
            </motion.button>
          )
        })}

        {/* Custom tags */}
        {selected.filter((t) => !INDUSTRY_OPTIONS.includes(t)).map((tag) => (
          <motion.button
            key={tag}
            whileHover={{ scale: 1.03 }}
            whileTap={{ scale: 0.97 }}
            onClick={() => toggle(tag)}
            disabled={readOnly}
            style={{
              display: 'inline-flex',
              alignItems: 'center',
              gap: 5,
              padding: '4px 12px',
              borderRadius: 999,
              border: '1px solid rgba(var(--brand-accent-rgb),0.5)',
              background: 'rgba(var(--brand-accent-rgb),0.1)',
              color: 'var(--brand-accent)',
              fontSize: 12,
              cursor: readOnly ? 'default' : 'pointer',
            }}
          >
            <Tag size={10} />
            {tag.replace(/_/g, ' ')}
            {!readOnly && <X size={9} />}
          </motion.button>
        ))}
      </div>

      {!readOnly && (
        <div style={{ display: 'flex', gap: 6, alignItems: 'center' }}>
          {showCustom ? (
            <>
              <input
                value={customInput}
                onChange={(e) => setCustomInput(e.target.value)}
                onKeyDown={(e) => e.key === 'Enter' && addCustom()}
                placeholder="Custom tag (e.g. pharma)"
                autoFocus
                style={{
                  padding: '5px 10px',
                  borderRadius: 8,
                  border: '1px solid var(--border-subtle)',
                  background: 'var(--bg-surface-raised)',
                  color: 'var(--text-primary)',
                  fontSize: 12,
                  width: 180,
                }}
              />
              <button
                onClick={addCustom}
                style={{
                  padding: '5px 10px',
                  borderRadius: 8,
                  border: 'none',
                  background: 'var(--brand-accent)',
                  color: '#fff',
                  fontSize: 12,
                  cursor: 'pointer',
                }}
              >
                Add
              </button>
              <button
                onClick={() => { setShowCustom(false); setCustomInput('') }}
                style={{
                  padding: '5px 10px',
                  borderRadius: 8,
                  border: '1px solid var(--border-subtle)',
                  background: 'transparent',
                  color: 'var(--text-secondary)',
                  fontSize: 12,
                  cursor: 'pointer',
                }}
              >
                Cancel
              </button>
            </>
          ) : (
            <motion.button
              whileHover={{ scale: 1.02 }}
              whileTap={{ scale: 0.98 }}
              onClick={() => setShowCustom(true)}
              style={{
                display: 'inline-flex',
                alignItems: 'center',
                gap: 5,
                padding: '4px 12px',
                borderRadius: 999,
                border: '1px dashed var(--border-subtle)',
                background: 'transparent',
                color: 'var(--text-muted)',
                fontSize: 12,
                cursor: 'pointer',
              }}
            >
              <Plus size={10} />
              Custom tag
            </motion.button>
          )}
        </div>
      )}
    </div>
  )
}
