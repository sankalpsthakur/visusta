import 'server-only'

import type { SupportedLocale } from '@/lib/i18n/locales'

const dictionaries: Record<SupportedLocale, () => Promise<Record<string, unknown>>> = {
  en: () => import('./dictionaries/en.json').then((m) => m.default),
  bg: () => import('./dictionaries/bg.json').then((m) => m.default),
  cs: () => import('./dictionaries/cs.json').then((m) => m.default),
  da: () => import('./dictionaries/da.json').then((m) => m.default),
  de: () => import('./dictionaries/de.json').then((m) => m.default),
  el: () => import('./dictionaries/el.json').then((m) => m.default),
  fr: () => import('./dictionaries/fr.json').then((m) => m.default),
  es: () => import('./dictionaries/es.json').then((m) => m.default),
  et: () => import('./dictionaries/et.json').then((m) => m.default),
  fi: () => import('./dictionaries/fi.json').then((m) => m.default),
  ga: () => import('./dictionaries/ga.json').then((m) => m.default),
  hr: () => import('./dictionaries/hr.json').then((m) => m.default),
  hu: () => import('./dictionaries/hu.json').then((m) => m.default),
  it: () => import('./dictionaries/it.json').then((m) => m.default),
  lt: () => import('./dictionaries/lt.json').then((m) => m.default),
  lv: () => import('./dictionaries/lv.json').then((m) => m.default),
  mt: () => import('./dictionaries/mt.json').then((m) => m.default),
  pt: () => import('./dictionaries/pt.json').then((m) => m.default),
  nl: () => import('./dictionaries/nl.json').then((m) => m.default),
  pl: () => import('./dictionaries/pl.json').then((m) => m.default),
  ro: () => import('./dictionaries/ro.json').then((m) => m.default),
  sk: () => import('./dictionaries/sk.json').then((m) => m.default),
  sl: () => import('./dictionaries/sl.json').then((m) => m.default),
  sv: () => import('./dictionaries/sv.json').then((m) => m.default),
}

export type Locale = SupportedLocale

export const hasLocale = (locale: string): locale is Locale => locale in dictionaries

export const getDictionary = async (locale: Locale) => dictionaries[locale]()
