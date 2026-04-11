'use client'

import { Tooltip, TooltipContent, TooltipProvider, TooltipTrigger } from '@/components/ui/tooltip'

interface MilestoneMarkerProps {
  date: string
  type: 'effective' | 'enforcement'
}

export function MilestoneMarker({ date, type }: MilestoneMarkerProps) {
  const color = type === 'effective' ? 'var(--brand-accent)' : 'var(--severity-high)'
  const label = type === 'effective' ? 'Effective date' : 'Enforcement date'

  return (
    <TooltipProvider>
      <Tooltip>
        <TooltipTrigger aria-label={`${label}: ${date}`}>
          <div
            className="w-3 h-3 flex-shrink-0 cursor-default"
            style={{
              background: color,
              clipPath: 'polygon(50% 0%, 100% 50%, 50% 100%, 0% 50%)',
            }}
          />
        </TooltipTrigger>
        <TooltipContent side="right">
          <span className="font-medium">{label}:</span> {date}
        </TooltipContent>
      </Tooltip>
    </TooltipProvider>
  )
}
