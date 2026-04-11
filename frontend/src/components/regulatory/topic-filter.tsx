'use client'

const TOPICS = [
  { id: 'ghg', label: 'GHG' },
  { id: 'packaging', label: 'Packaging' },
  { id: 'water', label: 'Water' },
  { id: 'waste', label: 'Waste' },
  { id: 'social_human_rights', label: 'Social & HR' },
]

interface TopicFilterProps {
  selected: string[]
  onChange: (topics: string[]) => void
}

export function TopicFilter({ selected, onChange }: TopicFilterProps) {
  function toggle(id: string) {
    if (selected.includes(id)) {
      onChange(selected.filter((t) => t !== id))
    } else {
      onChange([...selected, id])
    }
  }

  return (
    <div className="flex items-center gap-2 flex-wrap">
      {TOPICS.map((topic) => {
        const active = selected.includes(topic.id)
        return (
          <button
            key={topic.id}
            onClick={() => toggle(topic.id)}
            className="text-xs px-2.5 py-1 rounded transition-colors"
            style={{
              background: active ? 'color-mix(in srgb, var(--brand-accent) 15%, transparent)' : 'var(--bg-elevated)',
              color: active ? 'var(--brand-accent)' : 'var(--text-muted)',
              border: active ? '1px solid color-mix(in srgb, var(--brand-accent) 40%, transparent)' : '1px solid var(--border-color)',
              fontFamily: 'var(--font-mono)',
            }}
          >
            {topic.label}
          </button>
        )
      })}
      {selected.length > 0 && (
        <button
          onClick={() => onChange([])}
          className="text-xs px-2 py-1 rounded"
          style={{ color: 'var(--text-muted)', border: '1px solid var(--border-color)' }}
        >
          clear
        </button>
      )}
    </div>
  )
}
