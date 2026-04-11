'use client'

import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { useState } from 'react'
import { ActiveClientProvider } from '@/lib/clients/context'
import { TooltipProvider } from '@/components/ui/tooltip'

export function Providers({ children }: { children: React.ReactNode }) {
  const [queryClient] = useState(
    () =>
      new QueryClient({
        defaultOptions: {
          queries: {
            staleTime: 60 * 1000,
          },
        },
      })
  )

  return (
    <QueryClientProvider client={queryClient}>
      <ActiveClientProvider>
        <TooltipProvider>
          {children}
        </TooltipProvider>
      </ActiveClientProvider>
    </QueryClientProvider>
  )
}
