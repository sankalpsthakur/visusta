'use client'

import { useState, useEffect } from 'react'
import {
  Command,
  CommandEmpty,
  CommandGroup,
  CommandInput,
  CommandItem,
  CommandList,
  CommandSeparator,
} from '@/components/ui/command'
import {
  Dialog,
  DialogContent,
} from '@/components/ui/dialog'
import { useActiveClient } from '@/lib/clients/context'
import { Plus, ChevronRight } from 'lucide-react'

interface ClientSwitcherProps {
  collapsed?: boolean
}

export function ClientSwitcher({ collapsed = false }: ClientSwitcherProps) {
  const { activeClient, clients, switchClient } = useActiveClient()
  const [open, setOpen] = useState(false)

  useEffect(() => {
    const down = (e: KeyboardEvent) => {
      if (e.key === 'k' && (e.metaKey || e.ctrlKey)) {
        e.preventDefault()
        setOpen((o) => !o)
      }
    }
    document.addEventListener('keydown', down)
    return () => document.removeEventListener('keydown', down)
  }, [])

  return (
    <>
      <button
        onClick={() => setOpen(true)}
        className={`
          w-full flex items-center gap-2 px-3 py-2 rounded-md text-sm
          bg-[var(--bg-elevated)] border border-[var(--border-color)]
          text-[var(--text-primary)] hover:border-[var(--brand)]
          transition-colors text-left
          ${collapsed ? 'justify-center px-2' : ''}
        `}
        title={collapsed ? activeClient?.name ?? 'Switch client' : undefined}
      >
        <span className="flex-shrink-0 w-5 h-5 rounded bg-[var(--brand-dark)] flex items-center justify-center text-[var(--brand-contrast)] text-xs font-bold">
          {(activeClient?.name ?? 'V').charAt(0)}
        </span>
        {!collapsed && (
          <>
            <span className="flex-1 truncate">{activeClient?.name ?? 'Select client'}</span>
            <ChevronRight className="w-3 h-3 text-[var(--text-muted)] flex-shrink-0" />
          </>
        )}
      </button>

      <Dialog open={open} onOpenChange={setOpen}>
        <DialogContent
          className="p-0 overflow-hidden max-w-md"
          style={{ background: 'var(--bg-elevated)', border: '1px solid var(--border-color)' }}
        >
          <Command
            style={{ background: 'transparent' }}
          >
            <CommandInput
              placeholder="Search clients..."
              className="border-b border-[var(--border-color)]"
              style={{ color: 'var(--text-primary)' }}
            />
            <CommandList>
              <CommandEmpty className="py-4 text-center text-sm" style={{ color: 'var(--text-muted)' }}>
                No clients found.
              </CommandEmpty>
              <CommandGroup heading="Clients">
                {clients.map((client) => (
                  <CommandItem
                    key={client.id}
                    value={client.name}
                    onSelect={() => {
                      switchClient(client.id)
                      setOpen(false)
                    }}
                    className="cursor-pointer"
                  >
                    <span className="w-6 h-6 rounded bg-[var(--brand-dark)] flex items-center justify-center text-[var(--brand-contrast)] text-xs font-bold mr-2 flex-shrink-0">
                      {client.name.charAt(0)}
                    </span>
                    <div className="flex-1 min-w-0">
                      <div className="font-medium" style={{ color: 'var(--text-primary)' }}>
                        {client.name}
                      </div>
                      <div className="text-xs" style={{ color: 'var(--text-muted)' }}>
                        {client.facilities.map((f) => f.name).join(', ')} · {client.allowed_countries.join('/')}
                      </div>
                    </div>
                    {activeClient?.id === client.id && (
                      <span className="ml-2 text-xs font-medium" style={{ color: 'var(--brand-accent)' }}>
                        active
                      </span>
                    )}
                  </CommandItem>
                ))}
              </CommandGroup>
              <CommandSeparator />
              <CommandGroup>
                <CommandItem
                  onSelect={() => setOpen(false)}
                  className="cursor-pointer"
                >
                  <Plus className="w-4 h-4 mr-2" style={{ color: 'var(--text-muted)' }} />
                  <span style={{ color: 'var(--text-muted)' }}>Add new client</span>
                </CommandItem>
              </CommandGroup>
            </CommandList>
          </Command>
        </DialogContent>
      </Dialog>
    </>
  )
}
