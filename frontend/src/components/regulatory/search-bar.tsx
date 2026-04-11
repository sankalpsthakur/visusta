'use client'

import { useState, useEffect } from 'react'
import { Search } from 'lucide-react'
import { Input } from '@/components/ui/input'

interface SearchBarProps {
  value: string
  onChange: (value: string) => void
}

export function SearchBar({ value, onChange }: SearchBarProps) {
  const [localValue, setLocalValue] = useState(value)

  useEffect(() => {
    const timer = setTimeout(() => {
      onChange(localValue)
    }, 300)
    return () => clearTimeout(timer)
  }, [localValue, onChange])

  return (
    <div className="relative flex-1 min-w-0">
      <Search
        className="absolute left-2.5 top-1/2 -translate-y-1/2 w-3.5 h-3.5 pointer-events-none"
        style={{ color: 'var(--text-muted)' }}
      />
      <Input
        type="text"
        placeholder="Search regulations..."
        value={localValue}
        onChange={(e) => setLocalValue(e.target.value)}
        className="pl-8 text-sm"
      />
    </div>
  )
}
