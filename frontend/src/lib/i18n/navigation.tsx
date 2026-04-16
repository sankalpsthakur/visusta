'use client'

import Link from 'next/link'
import { useLocale } from './dictionary-context'
import type { ComponentProps } from 'react'

export function useLocalePath() {
  const locale = useLocale()
  return (path: string) => `/${locale}${path.startsWith('/') ? path : `/${path}`}`
}

type LocaleLinkProps = Omit<ComponentProps<typeof Link>, 'href'> & {
  href: string
}

export function LocaleLink({ href, ...props }: LocaleLinkProps) {
  const localePath = useLocalePath()
  return <Link href={localePath(href)} {...props} />
}
