'use client'

import { useState } from 'react'
import { motion, AnimatePresence } from 'framer-motion'
import { Plus, X, Save, Hash } from 'lucide-react'
import type { KeywordRule, KeywordMatchMode, CreateKeywordRulePayload } from '@/lib/api/source-hooks'

interface KeywordEditorProps {
  bundleName: string
  rules: KeywordRule[]
  onCreateRule: (payload: CreateKeywordRulePayload) => void
  onToggleRule: (ruleId: string | number, enabled: boolean) => void
  onDeleteRule: (ruleId: string | number) => void
  isSaving?: boolean
}

const MATCH_MODES: KeywordMatchMode[] = ['exact', 'fuzzy', 'regex']

export function KeywordEditor({ bundleName, rules, onCreateRule, onToggleRule, onDeleteRule, isSaving }: KeywordEditorProps) {
  const [showForm, setShowForm] = useState(false)
  const [newKeywords, setNewKeywords] = useState('')
  const [matchMode, setMatchMode] = useState<KeywordMatchMode>('fuzzy')
  const [topics, setTopics] = useState('')
  const [jurisdictions, setJurisdictions] = useState('')

  function handleAdd() {
    const keywords = newKeywords.split(',').map((k) => k.trim()).filter(Boolean)
    if (!keywords.length) return

    onCreateRule({
      bundle_name: bundleName,
      keywords,
      match_mode: matchMode,
      topics: topics.split(',').map((t) => t.trim()).filter(Boolean),
      jurisdictions: jurisdictions.split(',').map((j) => j.trim()).filter(Boolean),
    })
    setNewKeywords('')
    setTopics('')
    setJurisdictions('')
    setShowForm(false)
  }

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: 12 }}>
      {/* Header */}
      <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
          <Hash size={14} color="var(--brand-accent)" />
          <span style={{ fontSize: 14, fontWeight: 500, color: 'var(--text-primary)' }}>
            {bundleName.replace(/_/g, ' ')}
          </span>
          <span style={{ fontSize: 11, color: 'var(--text-muted)', background: 'var(--bg-surface-raised)', padding: '2px 8px', borderRadius: 999 }}>
            {rules.length} rules
          </span>
        </div>
        <motion.button
          whileHover={{ scale: 1.02 }}
          whileTap={{ scale: 0.98 }}
          onClick={() => setShowForm(!showForm)}
          style={{
            display: 'flex',
            alignItems: 'center',
            gap: 5,
            padding: '6px 12px',
            borderRadius: 8,
            border: 'none',
            background: 'var(--brand-accent)',
            color: '#fff',
            fontSize: 12,
            cursor: 'pointer',
          }}
        >
          <Plus size={12} />
          Add rule
        </motion.button>
      </div>

      {/* Add form */}
      <AnimatePresence>
        {showForm && (
          <motion.div
            initial={{ opacity: 0, height: 0 }}
            animate={{ opacity: 1, height: 'auto' }}
            exit={{ opacity: 0, height: 0 }}
            style={{ overflow: 'hidden' }}
          >
            <div style={{ padding: '14px 16px', borderRadius: 10, border: '1px solid var(--border-subtle)', background: 'var(--bg-surface-raised)', display: 'flex', flexDirection: 'column', gap: 10 }}>
              <div>
                <label style={{ fontSize: 11, fontWeight: 500, color: 'var(--text-muted)', display: 'block', marginBottom: 5 }}>
                  Keywords (comma-separated)
                </label>
                <textarea
                  aria-label="Keywords"
                  value={newKeywords}
                  onChange={(e) => setNewKeywords(e.target.value)}
                  placeholder="packaging regulation, single-use plastics, EPR"
                  rows={2}
                  style={{ width: '100%', padding: '7px 10px', borderRadius: 7, border: '1px solid var(--border-subtle)', background: 'var(--bg-surface)', color: 'var(--text-primary)', fontSize: 13, resize: 'vertical', fontFamily: 'inherit', boxSizing: 'border-box' }}
                />
              </div>

              <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr 1fr', gap: 10 }}>
                <div>
                  <label style={{ fontSize: 11, fontWeight: 500, color: 'var(--text-muted)', display: 'block', marginBottom: 5 }}>Match mode</label>
                  <select
                    aria-label="Keyword match mode"
                    value={matchMode}
                    onChange={(e) => setMatchMode(e.target.value as KeywordMatchMode)}
                    style={{ width: '100%', padding: '6px 10px', borderRadius: 7, border: '1px solid var(--border-subtle)', background: 'var(--bg-surface)', color: 'var(--text-primary)', fontSize: 12, boxSizing: 'border-box' }}
                  >
                    {MATCH_MODES.map((m) => <option key={m} value={m}>{m}</option>)}
                  </select>
                </div>
                <div>
                  <label style={{ fontSize: 11, fontWeight: 500, color: 'var(--text-muted)', display: 'block', marginBottom: 5 }}>Topics</label>
                  <input
                    aria-label="Keyword topics"
                    value={topics}
                    onChange={(e) => setTopics(e.target.value)}
                    placeholder="packaging, waste"
                    style={{ width: '100%', padding: '6px 10px', borderRadius: 7, border: '1px solid var(--border-subtle)', background: 'var(--bg-surface)', color: 'var(--text-primary)', fontSize: 12, boxSizing: 'border-box' }}
                  />
                </div>
                <div>
                  <label style={{ fontSize: 11, fontWeight: 500, color: 'var(--text-muted)', display: 'block', marginBottom: 5 }}>Jurisdictions</label>
                  <input
                    aria-label="Keyword jurisdictions"
                    value={jurisdictions}
                    onChange={(e) => setJurisdictions(e.target.value)}
                    placeholder="EU, DE"
                    style={{ width: '100%', padding: '6px 10px', borderRadius: 7, border: '1px solid var(--border-subtle)', background: 'var(--bg-surface)', color: 'var(--text-primary)', fontSize: 12, boxSizing: 'border-box' }}
                  />
                </div>
              </div>

              <div style={{ display: 'flex', gap: 8, justifyContent: 'flex-end' }}>
                <button onClick={() => setShowForm(false)} style={{ padding: '6px 12px', borderRadius: 7, border: '1px solid var(--border-subtle)', background: 'transparent', color: 'var(--text-secondary)', fontSize: 12, cursor: 'pointer' }}>
                  Cancel
                </button>
                <motion.button
                  whileHover={{ scale: 1.02 }}
                  whileTap={{ scale: 0.98 }}
                  onClick={handleAdd}
                  disabled={!newKeywords.trim() || isSaving}
                  style={{
                    display: 'flex',
                    alignItems: 'center',
                    gap: 5,
                    padding: '6px 14px',
                    borderRadius: 7,
                    border: 'none',
                    background: newKeywords.trim() && !isSaving ? 'var(--brand-accent)' : 'var(--bg-surface)',
                    color: newKeywords.trim() && !isSaving ? '#fff' : 'var(--text-muted)',
                    fontSize: 12,
                    fontWeight: 500,
                    cursor: !newKeywords.trim() || isSaving ? 'not-allowed' : 'pointer',
                  }}
                >
                  <Save size={12} />
                  {isSaving ? 'Adding…' : 'Add rule'}
                </motion.button>
              </div>
            </div>
          </motion.div>
        )}
      </AnimatePresence>

      {/* Rules list */}
      {rules.length === 0 ? (
        <div style={{ textAlign: 'center', padding: '24px 0', color: 'var(--text-muted)', fontSize: 12 }}>
          No rules in this bundle
        </div>
      ) : (
        <div style={{ display: 'flex', flexDirection: 'column', gap: 6 }}>
          {rules.map((rule) => (
            <motion.div
              key={rule.rule_id}
              layout
              style={{
                padding: '10px 12px',
                borderRadius: 8,
                border: '1px solid var(--border-subtle)',
                background: rule.enabled ? 'var(--bg-surface)' : 'var(--bg-surface-raised)',
                opacity: rule.enabled ? 1 : 0.6,
                display: 'flex',
                alignItems: 'flex-start',
                gap: 10,
              }}
            >
              <div style={{ flex: 1 }}>
                <div style={{ display: 'flex', flexWrap: 'wrap', gap: 4, marginBottom: 4 }}>
                  {rule.keywords.map((kw) => (
                    <span
                      key={kw}
                      style={{
                        fontSize: 11,
                        background: 'var(--bg-surface-raised)',
                        border: '1px solid var(--border-subtle)',
                        padding: '1px 8px',
                        borderRadius: 999,
                        color: 'var(--text-primary)',
                      }}
                    >
                      {kw}
                    </span>
                  ))}
                </div>
                <div style={{ fontSize: 10, color: 'var(--text-muted)' }}>
                  {rule.match_mode}
                  {rule.topics.length > 0 && ` · ${rule.topics.join(', ')}`}
                  {rule.jurisdictions.length > 0 && ` · ${rule.jurisdictions.join(', ')}`}
                </div>
              </div>

              <div style={{ display: 'flex', gap: 6, alignItems: 'center', flexShrink: 0 }}>
                <motion.button
                  whileHover={{ scale: 1.05 }}
                  whileTap={{ scale: 0.95 }}
                  onClick={() => onToggleRule(rule.rule_id, !rule.enabled)}
                  title={rule.enabled ? 'Disable' : 'Enable'}
                  style={{
                    width: 32,
                    height: 18,
                    borderRadius: 999,
                    border: 'none',
                    background: rule.enabled ? '#22c55e' : 'var(--bg-surface-raised)',
                    cursor: 'pointer',
                    position: 'relative',
                    transition: 'background 0.2s',
                    flexShrink: 0,
                  }}
                >
                  <div style={{ position: 'absolute', top: 2, left: rule.enabled ? 16 : 2, width: 14, height: 14, borderRadius: '50%', background: '#fff', transition: 'left 0.2s' }} />
                </motion.button>
                <motion.button
                  whileHover={{ scale: 1.08 }}
                  whileTap={{ scale: 0.92 }}
                  onClick={() => onDeleteRule(rule.rule_id)}
                  style={{ background: 'none', border: 'none', cursor: 'pointer', color: 'var(--text-muted)', padding: 2 }}
                >
                  <X size={13} />
                </motion.button>
              </div>
            </motion.div>
          ))}
        </div>
      )}
    </div>
  )
}
