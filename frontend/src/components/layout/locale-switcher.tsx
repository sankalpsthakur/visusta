'use client'

import { usePathname, useRouter } from 'next/navigation'
import { useLocale } from '@/lib/i18n/dictionary-context'
import type { Locale } from '@/app/[lang]/dictionaries'
import { LOCALE_LABELS, SUPPORTED_LOCALES } from '@/lib/i18n/locales'
import { Globe } from 'lucide-react'

export function LocaleSwitcher() {
  const locale = useLocale()
  const pathname = usePathname()
  const router = useRouter()

  const handleChange = (e: React.ChangeEvent<HTMLSelectElement>) => {
    const newLocale = e.target.value as Locale
    // Replace locale segment: /en/clients/... -> /de/clients/...
    const segments = pathname.split('/')
    segments[1] = newLocale
    router.push(segments.join('/') || '/')
  }

  return (
    <div className="flex items-center gap-2">
      <Globe className="w-3.5 h-3.5 flex-shrink-0" style={{ color: 'var(--text-muted)' }} />
      <select
        aria-label="Select language"
        value={locale}
        onChange={handleChange}
        className="flex-1 text-xs py-1 px-1.5 rounded outline-none cursor-pointer"
        style={{
          background: 'var(--bg-elevated)',
          border: '1px solid var(--border-color)',
          color: 'var(--text-muted)',
        }}
      >
        {SUPPORTED_LOCALES.map((code) => (
          <option key={code} value={code}>
            {LOCALE_LABELS[code]}
          </option>
        ))}
      </select>
    </div>
  )
}
