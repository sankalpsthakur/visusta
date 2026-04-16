'use client'

import { useState } from 'react'
import { motion } from 'framer-motion'
import { Save, BarChart2, X } from 'lucide-react'
import type { TemplateSection } from '@/lib/api/template-hooks'

const CHART_OPTIONS = [
  'severity_heatmap',
  'enforcement_timeline',
  'topic_distribution',
  'regulation_count',
  'change_velocity',
  'jurisdiction_map',
]

interface SectionEditorProps {
  section: TemplateSection
  onSave: (updated: TemplateSection) => void
  isSaving?: boolean
  readOnly?: boolean
}

export function SectionEditor({ section, onSave, isSaving, readOnly }: SectionEditorProps) {
  const [heading, setHeading] = useState(section.heading)
  const [promptTemplate, setPromptTemplate] = useState(section.prompt_template)
  const [chartTypes, setChartTypes] = useState<string[]>(section.chart_types)
  const [maxTokens, setMaxTokens] = useState(section.max_tokens)

  const isDirty =
    heading !== section.heading ||
    promptTemplate !== section.prompt_template ||
    JSON.stringify(chartTypes) !== JSON.stringify(section.chart_types) ||
    maxTokens !== section.max_tokens

  function toggleChart(chart: string) {
    setChartTypes((prev) =>
      prev.includes(chart) ? prev.filter((c) => c !== chart) : [...prev, chart]
    )
  }

  function handleSave() {
    onSave({ ...section, heading, prompt_template: promptTemplate, chart_types: chartTypes, max_tokens: maxTokens })
  }

  return (
    <motion.div
      key={section.section_id}
      initial={{ opacity: 0, x: 8 }}
      animate={{ opacity: 1, x: 0 }}
      style={{ display: 'flex', flexDirection: 'column', gap: 16 }}
    >
      {/* Heading */}
      <div>
        <label style={{ fontSize: 11, fontWeight: 500, color: 'var(--text-muted)', textTransform: 'uppercase', letterSpacing: '0.05em', display: 'block', marginBottom: 6 }}>
          Section heading
        </label>
        <input
          aria-label="Section heading"
          value={heading}
          onChange={(e) => setHeading(e.target.value)}
          disabled={readOnly}
          style={{
            width: '100%',
            padding: '8px 12px',
            borderRadius: 8,
            border: '1px solid var(--border-subtle)',
            background: 'var(--bg-surface-raised)',
            color: 'var(--text-primary)',
            fontSize: 14,
            fontWeight: 500,
            boxSizing: 'border-box',
          }}
        />
      </div>

      {/* Prompt template */}
      <div>
        <label style={{ fontSize: 11, fontWeight: 500, color: 'var(--text-muted)', textTransform: 'uppercase', letterSpacing: '0.05em', display: 'block', marginBottom: 6 }}>
          Prompt template
        </label>
        <textarea
          aria-label="Section prompt template"
          value={promptTemplate}
          onChange={(e) => setPromptTemplate(e.target.value)}
          disabled={readOnly}
          rows={8}
          placeholder="Write the generation prompt for this section. Use {{variables}} for dynamic content."
          style={{
            width: '100%',
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
      </div>

      {/* Chart types */}
      <div>
        <label style={{ fontSize: 11, fontWeight: 500, color: 'var(--text-muted)', textTransform: 'uppercase', letterSpacing: '0.05em', display: 'block', marginBottom: 8 }}>
          Allowed chart types
        </label>
        <div style={{ display: 'flex', flexWrap: 'wrap', gap: 6 }}>
          {CHART_OPTIONS.map((chart) => {
            const active = chartTypes.includes(chart)
            return (
              <motion.button
                key={chart}
                whileHover={{ scale: 1.02 }}
                whileTap={{ scale: 0.98 }}
                disabled={readOnly}
                onClick={() => toggleChart(chart)}
                style={{
                  display: 'flex',
                  alignItems: 'center',
                  gap: 5,
                  padding: '4px 10px',
                  borderRadius: 999,
                  border: active ? '1px solid rgba(var(--brand-accent-rgb),0.5)' : '1px solid var(--border-subtle)',
                  background: active ? 'rgba(var(--brand-accent-rgb),0.1)' : 'var(--bg-surface-raised)',
                  color: active ? 'var(--brand-accent)' : 'var(--text-secondary)',
                  fontSize: 12,
                  cursor: readOnly ? 'default' : 'pointer',
                }}
              >
                <BarChart2 size={10} />
                {chart.replace(/_/g, ' ')}
                {active && <X size={9} />}
              </motion.button>
            )
          })}
        </div>
      </div>

      {/* Max tokens */}
      <div>
        <label style={{ fontSize: 11, fontWeight: 500, color: 'var(--text-muted)', textTransform: 'uppercase', letterSpacing: '0.05em', display: 'block', marginBottom: 6 }}>
          Max tokens
        </label>
        <input
          aria-label="Section max tokens"
          type="number"
          value={maxTokens}
          onChange={(e) => setMaxTokens(Number(e.target.value))}
          disabled={readOnly}
          min={100}
          max={8000}
          step={100}
          style={{
            width: 140,
            padding: '8px 12px',
            borderRadius: 8,
            border: '1px solid var(--border-subtle)',
            background: 'var(--bg-surface-raised)',
            color: 'var(--text-primary)',
            fontSize: 13,
          }}
        />
      </div>

      {/* Save button */}
      {!readOnly && (
        <div style={{ display: 'flex', justifyContent: 'flex-end' }}>
          <motion.button
            whileHover={{ scale: 1.02 }}
            whileTap={{ scale: 0.98 }}
            onClick={handleSave}
            disabled={!isDirty || isSaving}
            style={{
              display: 'flex',
              alignItems: 'center',
              gap: 6,
              padding: '8px 18px',
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
            <Save size={14} />
            {isSaving ? 'Saving…' : 'Save section'}
          </motion.button>
        </div>
      )}
    </motion.div>
  )
}
