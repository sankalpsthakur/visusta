'use client'

import { useState, useEffect } from 'react'
import { motion } from 'framer-motion'
import { Save, Plus, Trash2, Link2 } from 'lucide-react'
import type { DraftSection, DraftBlock, SectionEditPayload } from '@/lib/api/draft-hooks'

interface SectionEditorProps {
  section: DraftSection
  onSave: (sectionId: string, payload: SectionEditPayload) => void
  isSaving?: boolean
}

export function SectionEditor({ section, onSave, isSaving }: SectionEditorProps) {
  const [blocks, setBlocks] = useState<DraftBlock[]>(section.blocks)
  const [citations, setCitations] = useState<string[]>(section.citations)
  const [revisionNote, setRevisionNote] = useState('')

  useEffect(() => {
    setBlocks(section.blocks)
    setCitations(section.citations)
    setRevisionNote('')
  }, [section.section_id])

  function updateBlock(index: number, content: string) {
    setBlocks((prev) => prev.map((b, i) => (i === index ? { ...b, content } : b)))
  }

  function addBlock() {
    setBlocks((prev) => [...prev, { type: 'paragraph', content: '' }])
  }

  function removeBlock(index: number) {
    setBlocks((prev) => prev.filter((_, i) => i !== index))
  }

  function addCitation() {
    setCitations((prev) => [...prev, ''])
  }

  function updateCitation(index: number, value: string) {
    setCitations((prev) => prev.map((c, i) => (i === index ? value : c)))
  }

  function removeCitation(index: number) {
    setCitations((prev) => prev.filter((_, i) => i !== index))
  }

  function handleSave() {
    onSave(section.section_id, {
      blocks,
      citations: citations.filter(Boolean),
      revision_note: revisionNote.trim() || undefined,
    })
  }

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: 18 }}>
      {/* Heading */}
      <div
        style={{
          fontSize: 16,
          fontWeight: 600,
          color: 'var(--text-primary)',
          paddingBottom: 10,
          borderBottom: '1px solid var(--border-subtle)',
        }}
      >
        {section.heading}
      </div>

      {/* Content blocks */}
      <div>
        <label style={{ fontSize: 11, fontWeight: 500, color: 'var(--text-muted)', textTransform: 'uppercase', letterSpacing: '0.05em', display: 'block', marginBottom: 8 }}>
          Content
        </label>
        <div style={{ display: 'flex', flexDirection: 'column', gap: 8 }}>
          {blocks.map((block, i) => (
            <div key={i} style={{ display: 'flex', gap: 8 }}>
              <textarea
                value={block.content}
                onChange={(e) => updateBlock(i, e.target.value)}
                rows={4}
                style={{
                  flex: 1,
                  padding: '10px 12px',
                  borderRadius: 8,
                  border: '1px solid var(--border-subtle)',
                  background: 'var(--bg-surface-raised)',
                  color: 'var(--text-primary)',
                  fontSize: 13,
                  lineHeight: 1.6,
                  resize: 'vertical',
                  fontFamily: 'inherit',
                  boxSizing: 'border-box',
                }}
              />
              <motion.button
                whileHover={{ scale: 1.05 }}
                whileTap={{ scale: 0.95 }}
                onClick={() => removeBlock(i)}
                style={{
                  width: 32,
                  height: 32,
                  borderRadius: 8,
                  border: '1px solid var(--border-subtle)',
                  background: 'transparent',
                  color: 'var(--text-muted)',
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'center',
                  cursor: 'pointer',
                  flexShrink: 0,
                  alignSelf: 'flex-start',
                  marginTop: 4,
                }}
              >
                <Trash2 size={12} />
              </motion.button>
            </div>
          ))}

          <motion.button
            whileHover={{ scale: 1.01 }}
            onClick={addBlock}
            style={{
              display: 'flex',
              alignItems: 'center',
              gap: 6,
              padding: '8px 12px',
              borderRadius: 8,
              border: '1px dashed var(--border-subtle)',
              background: 'transparent',
              color: 'var(--text-muted)',
              fontSize: 12,
              cursor: 'pointer',
            }}
          >
            <Plus size={12} />
            Add paragraph
          </motion.button>
        </div>
      </div>

      {/* Citations */}
      <div>
        <label style={{ fontSize: 11, fontWeight: 500, color: 'var(--text-muted)', textTransform: 'uppercase', letterSpacing: '0.05em', display: 'block', marginBottom: 8 }}>
          Citations
        </label>
        <div style={{ display: 'flex', flexDirection: 'column', gap: 6 }}>
          {citations.map((citation, i) => (
            <div key={i} style={{ display: 'flex', gap: 8, alignItems: 'center' }}>
              <Link2 size={12} color="var(--text-muted)" style={{ flexShrink: 0 }} />
              <input
                value={citation}
                onChange={(e) => updateCitation(i, e.target.value)}
                placeholder="Regulation ID or URL"
                style={{
                  flex: 1,
                  padding: '6px 10px',
                  borderRadius: 7,
                  border: '1px solid var(--border-subtle)',
                  background: 'var(--bg-surface-raised)',
                  color: 'var(--text-primary)',
                  fontSize: 12,
                  fontFamily: 'monospace',
                }}
              />
              <button
                onClick={() => removeCitation(i)}
                style={{ background: 'none', border: 'none', cursor: 'pointer', color: 'var(--text-muted)', padding: 0 }}
              >
                <Trash2 size={12} />
              </button>
            </div>
          ))}
          <button
            onClick={addCitation}
            style={{
              display: 'flex',
              alignItems: 'center',
              gap: 6,
              background: 'none',
              border: 'none',
              color: 'var(--text-muted)',
              fontSize: 12,
              cursor: 'pointer',
              padding: '4px 0',
            }}
          >
            <Plus size={11} />
            Add citation
          </button>
        </div>
      </div>

      {/* Revision note */}
      <div>
        <label style={{ fontSize: 11, fontWeight: 500, color: 'var(--text-muted)', textTransform: 'uppercase', letterSpacing: '0.05em', display: 'block', marginBottom: 6 }}>
          Revision note (optional)
        </label>
        <input
          value={revisionNote}
          onChange={(e) => setRevisionNote(e.target.value)}
          placeholder="Brief description of changes…"
          style={{
            width: '100%',
            padding: '7px 10px',
            borderRadius: 7,
            border: '1px solid var(--border-subtle)',
            background: 'var(--bg-surface-raised)',
            color: 'var(--text-primary)',
            fontSize: 12,
            boxSizing: 'border-box',
          }}
        />
      </div>

      {/* Save */}
      <div style={{ display: 'flex', justifyContent: 'flex-end' }}>
        <motion.button
          whileHover={{ scale: 1.02 }}
          whileTap={{ scale: 0.98 }}
          onClick={handleSave}
          disabled={isSaving}
          style={{
            display: 'flex',
            alignItems: 'center',
            gap: 6,
            padding: '8px 18px',
            borderRadius: 8,
            border: 'none',
            background: isSaving ? 'var(--bg-surface-raised)' : 'var(--brand-accent)',
            color: isSaving ? 'var(--text-muted)' : '#fff',
            fontSize: 13,
            fontWeight: 500,
            cursor: isSaving ? 'not-allowed' : 'pointer',
            transition: 'background 0.15s, color 0.15s',
          }}
        >
          <Save size={13} />
          {isSaving ? 'Saving…' : 'Save section'}
        </motion.button>
      </div>
    </div>
  )
}
