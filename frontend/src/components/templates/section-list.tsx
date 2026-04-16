'use client'

import { motion, AnimatePresence, Reorder } from 'framer-motion'
import { GripVertical, ChevronDown, ChevronRight, AlertCircle, Plus, Trash2 } from 'lucide-react'
import type { TemplateSection } from '@/lib/api/template-hooks'

interface SectionListProps {
  sections: TemplateSection[]
  selectedSectionId: string | null
  onSelect: (section: TemplateSection) => void
  onReorder: (sections: TemplateSection[]) => void
  onDelete: (sectionId: string) => void
  onAdd: () => void
  readOnly?: boolean
}

interface SectionRowProps {
  section: TemplateSection
  isSelected: boolean
  onSelect: () => void
  onDelete: () => void
  readOnly?: boolean
}

function SectionRow({ section, isSelected, onSelect, onDelete, readOnly }: SectionRowProps) {
  return (
    <Reorder.Item
      value={section}
      id={section.section_id}
      style={{ listStyle: 'none' }}
    >
      <motion.div
        layout
        onClick={onSelect}
        style={{
          display: 'flex',
          alignItems: 'center',
          gap: 8,
          padding: '8px 10px',
          borderRadius: 8,
          cursor: 'pointer',
          background: isSelected ? 'rgba(var(--brand-accent-rgb),0.1)' : 'transparent',
          border: isSelected ? '1px solid rgba(var(--brand-accent-rgb),0.3)' : '1px solid transparent',
          userSelect: 'none',
        }}
      >
        {!readOnly && (
          <GripVertical size={14} color="var(--text-muted)" style={{ cursor: 'grab', flexShrink: 0 }} />
        )}

        {isSelected ? (
          <ChevronDown size={14} color="var(--brand-accent)" style={{ flexShrink: 0 }} />
        ) : (
          <ChevronRight size={14} color="var(--text-muted)" style={{ flexShrink: 0 }} />
        )}

        <span
          style={{
            fontSize: 13,
            fontWeight: isSelected ? 500 : 400,
            color: isSelected ? 'var(--brand-accent)' : 'var(--text-primary)',
            flex: 1,
            overflow: 'hidden',
            textOverflow: 'ellipsis',
            whiteSpace: 'nowrap',
          }}
        >
          {section.heading}
        </span>

        {section.required && (
          <AlertCircle size={12} color="var(--text-muted)" aria-label="Required section" />
        )}

        {!readOnly && !section.required && (
          <motion.button
            whileHover={{ scale: 1.1 }}
            whileTap={{ scale: 0.9 }}
            onClick={(e) => { e.stopPropagation(); onDelete() }}
            style={{
              width: 22,
              height: 22,
              borderRadius: 6,
              border: 'none',
              background: 'transparent',
              color: 'var(--text-muted)',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              cursor: 'pointer',
              flexShrink: 0,
            }}
          >
            <Trash2 size={12} />
          </motion.button>
        )}
      </motion.div>
    </Reorder.Item>
  )
}

export function SectionList({
  sections,
  selectedSectionId,
  onSelect,
  onReorder,
  onDelete,
  onAdd,
  readOnly,
}: SectionListProps) {
  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: 4 }}>
      <Reorder.Group
        axis="y"
        values={sections}
        onReorder={onReorder}
        style={{ margin: 0, padding: 0, display: 'flex', flexDirection: 'column', gap: 2 }}
      >
        <AnimatePresence>
          {sections.map((section) => (
            <SectionRow
              key={section.section_id}
              section={section}
              isSelected={selectedSectionId === section.section_id}
              onSelect={() => onSelect(section)}
              onDelete={() => onDelete(section.section_id)}
              readOnly={readOnly}
            />
          ))}
        </AnimatePresence>
      </Reorder.Group>

      {!readOnly && (
        <motion.button
          whileHover={{ scale: 1.01 }}
          whileTap={{ scale: 0.99 }}
          onClick={onAdd}
          style={{
            display: 'flex',
            alignItems: 'center',
            gap: 6,
            padding: '8px 10px',
            borderRadius: 8,
            border: '1px dashed var(--border-subtle)',
            background: 'transparent',
            color: 'var(--text-muted)',
            fontSize: 13,
            cursor: 'pointer',
            marginTop: 4,
          }}
        >
          <Plus size={13} />
          Add section
        </motion.button>
      )}
    </div>
  )
}
