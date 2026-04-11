'use client'

import React, { createContext, useContext, useState } from 'react'
import { useClients } from '@/lib/api/hooks'

export interface ClientWorkspace {
  id: string
  name: string
  facilities: { name: string; jurisdiction: string }[]
  allowed_countries: string[]
  required_topics: string[]
}

interface ClientContextType {
  activeClient: ClientWorkspace | null
  clients: ClientWorkspace[]
  switchClient: (id: string) => void
  isLoading: boolean
}

const ClientContext = createContext<ClientContextType>({
  activeClient: null,
  clients: [],
  switchClient: () => {},
  isLoading: false,
})

function toWorkspace(raw: Record<string, unknown>): ClientWorkspace {
  return {
    id: raw.client_id as string,
    name: raw.display_name as string,
    facilities: (raw.facilities as { name: string; jurisdiction: string }[]) ?? [],
    allowed_countries: (raw.allowed_countries as string[]) ?? [],
    required_topics: (raw.required_topics as string[]) ?? [],
  }
}

export function ActiveClientProvider({ children }: { children: React.ReactNode }) {
  const { data, isLoading } = useClients()
  const [activeId, setActiveId] = useState<string | null>(null)

  const rawClients = Array.isArray(data) ? data : []
  const clients: ClientWorkspace[] = rawClients.map((c) =>
    toWorkspace(c as Record<string, unknown>)
  )

  const activeClient =
    clients.find((c) => c.id === activeId) ?? clients[0] ?? null

  return (
    <ClientContext.Provider
      value={{ activeClient, clients, switchClient: setActiveId, isLoading }}
    >
      {children}
    </ClientContext.Provider>
  )
}

export function useActiveClient() {
  return useContext(ClientContext)
}
