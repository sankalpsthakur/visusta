'use client'

import Link from 'next/link'
import { usePathname } from 'next/navigation'
import { motion } from 'framer-motion'
import { useLocale } from '@/lib/i18n/dictionary-context'

interface NavItemProps {
  href: string
  label: string
  icon: React.ReactNode
  collapsed?: boolean
}

export function NavItem({ href, label, icon, collapsed = false }: NavItemProps) {
  const pathname = usePathname()
  const locale = useLocale()
  const localePrefix = `/${locale}`
  const strip = (p: string) => p.startsWith(localePrefix) ? (p.slice(localePrefix.length) || '/') : p
  const strippedPathname = strip(pathname)
  const strippedHref = strip(href)
  const isActive = strippedPathname === strippedHref || (strippedHref !== '/' && strippedPathname.startsWith(strippedHref))

  return (
    <Link href={href} className="relative block">
      <div
        className={`
          relative flex items-center gap-3 px-3 py-2 rounded-md text-sm transition-colors
          ${isActive
            ? 'text-[var(--brand-accent)]'
            : 'text-[var(--text-muted)] hover:text-[var(--text-primary)] hover:bg-[var(--bg-elevated)]'
          }
        `}
      >
        {isActive && (
          <motion.div
            layoutId="nav-active-indicator"
            className="absolute left-0 top-1/2 -translate-y-1/2 w-0.5 h-5 bg-[var(--brand-accent)] rounded-full"
            transition={{ type: 'spring', stiffness: 400, damping: 30 }}
          />
        )}
        <span className="flex-shrink-0 w-4 h-4 flex items-center justify-center ml-1">
          {icon}
        </span>
        {!collapsed && (
          <span className="truncate">{label}</span>
        )}
      </div>
    </Link>
  )
}
