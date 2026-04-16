'use client'

import { useState } from 'react'
import { motion, AnimatePresence } from 'framer-motion'
import { NavItem } from './nav-item'
import { ClientSwitcher } from './client-switcher'
import { LocaleSwitcher } from './locale-switcher'
import { useHealth } from '@/lib/api/hooks'
import { useActiveClient } from '@/lib/clients/context'
import { useLocale } from '@/lib/i18n/dictionary-context'
import {
  LayoutDashboard,
  Home,
  FileText,
  ClipboardList,
  Settings,
  Database,
  Users,
  ChevronLeft,
  ChevronRight,
  LayoutTemplate,
  BookOpen,
  Radio,
} from 'lucide-react'

export function Sidebar() {
  const [collapsed, setCollapsed] = useState(false)
  const { data: health } = useHealth()
  const { activeClient } = useActiveClient()
  const locale = useLocale()
  const localePath = (path: string) => `/${locale}${path}`
  const clientBase = activeClient ? localePath(`/clients/${activeClient.id}`) : null

  const width = collapsed ? 64 : 280

  return (
    <motion.aside
      animate={{ width }}
      transition={{ type: 'spring', stiffness: 300, damping: 30 }}
      className="relative flex flex-col flex-shrink-0 h-screen overflow-hidden"
      style={{
        background: 'var(--bg-surface)',
        borderRight: '1px solid var(--border-color)',
      }}
    >
      {/* Toggle button */}
      <button
        onClick={() => setCollapsed((c) => !c)}
        aria-label={collapsed ? 'Expand sidebar' : 'Collapse sidebar'}
        className="absolute -right-3 top-8 z-10 w-6 h-6 rounded-full flex items-center justify-center transition-colors"
        style={{
          background: 'var(--bg-elevated)',
          border: '1px solid var(--border-color)',
          color: 'var(--text-muted)',
        }}
      >
        {collapsed ? (
          <ChevronRight className="w-3 h-3" />
        ) : (
          <ChevronLeft className="w-3 h-3" />
        )}
      </button>

      {/* Logo */}
      <div
        className="flex items-center px-4 h-14 flex-shrink-0"
        style={{ borderBottom: '1px solid var(--border-color)' }}
      >
        <div className="flex items-center gap-2">
          <span
            className="w-7 h-7 rounded flex items-center justify-center text-xs font-bold flex-shrink-0"
            style={{ background: 'var(--brand)', color: 'var(--brand-contrast)' }}
          >
            V
          </span>
          <AnimatePresence>
            {!collapsed && (
              <motion.span
                initial={{ opacity: 0, width: 0 }}
                animate={{ opacity: 1, width: 'auto' }}
                exit={{ opacity: 0, width: 0 }}
                transition={{ duration: 0.15 }}
                className="text-sm font-semibold tracking-wide overflow-hidden whitespace-nowrap"
                style={{ color: 'var(--text-primary)' }}
              >
                Visusta
              </motion.span>
            )}
          </AnimatePresence>
        </div>
      </div>

      {/* Client switcher */}
      <div className="px-3 py-3 flex-shrink-0" style={{ borderBottom: '1px solid var(--border-color)' }}>
        <ClientSwitcher collapsed={collapsed} />
      </div>

      {/* Navigation */}
      <nav className="flex-1 px-2 py-3 overflow-y-auto">
        <div className="space-y-0.5">
          <NavItem href={localePath('/')} label="Overview" icon={<Home className="w-4 h-4" />} collapsed={collapsed} />
          <NavItem href={localePath('/clients')} label="Clients" icon={<Users className="w-4 h-4" />} collapsed={collapsed} />
          <NavItem href={localePath('/templates')} label="Templates" icon={<LayoutTemplate className="w-4 h-4" />} collapsed={collapsed} />
        </div>
        {clientBase && (
          <>
            <div
              className="my-3 mx-2"
              style={{ borderTop: '1px solid var(--border-color)' }}
            />
            {!collapsed && (
              <div
                className="px-3 mb-1 text-xs font-semibold tracking-widest uppercase"
                style={{ color: 'var(--text-muted)', letterSpacing: '0.08em' }}
              >
                {activeClient?.name}
              </div>
            )}
            <div className="space-y-0.5">
              <NavItem href={clientBase} label="Dashboard" icon={<LayoutDashboard className="w-4 h-4" />} collapsed={collapsed} />
              <NavItem href={`${clientBase}/regulatory`} label="Regulatory" icon={<Database className="w-4 h-4" />} collapsed={collapsed} />
              <NavItem href={`${clientBase}/reports`} label="Reports" icon={<FileText className="w-4 h-4" />} collapsed={collapsed} />
              <NavItem href={`${clientBase}/audit`} label="Audit" icon={<ClipboardList className="w-4 h-4" />} collapsed={collapsed} />
              <NavItem href={`${clientBase}/settings`} label="Settings" icon={<Settings className="w-4 h-4" />} collapsed={collapsed} />
              <NavItem href={`${clientBase}/drafts`} label="Drafts" icon={<BookOpen className="w-4 h-4" />} collapsed={collapsed} />
              <NavItem href={`${clientBase}/sources`} label="Sources" icon={<Radio className="w-4 h-4" />} collapsed={collapsed} />
            </div>
          </>
        )}
      </nav>

      {/* System health */}
      <div
        className="flex items-center gap-2 px-4 py-3 flex-shrink-0"
        style={{ borderTop: '1px solid var(--border-color)' }}
      >
        <span
          className="w-2 h-2 rounded-full flex-shrink-0"
          style={{
            background: health?.status === 'ok' ? 'var(--severity-low)' : 'var(--severity-medium)',
            boxShadow: health?.status === 'ok'
              ? '0 0 6px var(--severity-low)'
              : '0 0 6px var(--severity-medium)',
          }}
        />
        <AnimatePresence>
          {!collapsed && (
            <motion.span
              initial={{ opacity: 0, width: 0 }}
              animate={{ opacity: 1, width: 'auto' }}
              exit={{ opacity: 0, width: 0 }}
              transition={{ duration: 0.15 }}
              className="text-xs overflow-hidden whitespace-nowrap"
              style={{ color: 'var(--text-muted)' }}
            >
              {health?.status === 'ok' ? 'System operational' : 'Backend offline'}
            </motion.span>
          )}
        </AnimatePresence>
      </div>

      {/* Locale switcher */}
      {!collapsed && (
        <div
          className="px-3 py-2 flex-shrink-0"
          style={{ borderTop: '1px solid var(--border-color)' }}
        >
          <LocaleSwitcher />
        </div>
      )}
    </motion.aside>
  )
}
