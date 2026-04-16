'use client'

import { createContext, useContext } from 'react'
import type { getDictionary, Locale } from '@/app/[lang]/dictionaries'

type Dictionary = Awaited<ReturnType<typeof getDictionary>>

interface DictionaryContextValue {
  dictionary: Dictionary
  locale: Locale
}

const DictionaryContext = createContext<DictionaryContextValue | null>(null)

export function DictionaryProvider({
  children,
  dictionary,
  locale,
}: {
  children: React.ReactNode
  dictionary: Dictionary
  locale: Locale
}) {
  return (
    <DictionaryContext.Provider value={{ dictionary, locale }}>
      {children}
    </DictionaryContext.Provider>
  )
}

export function useDictionary(): Dictionary {
  const ctx = useContext(DictionaryContext)
  if (!ctx) throw new Error('useDictionary must be used within DictionaryProvider')
  return ctx.dictionary
}

export function useLocale(): Locale {
  const ctx = useContext(DictionaryContext)
  if (!ctx) throw new Error('useLocale must be used within DictionaryProvider')
  return ctx.locale
}
