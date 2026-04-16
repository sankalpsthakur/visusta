import type { Metadata } from 'next'
import { Fraunces, Inter_Tight, JetBrains_Mono } from 'next/font/google'
import '../globals.css'
import { Providers } from '@/components/layout/providers'
import { Sidebar } from '@/components/layout/sidebar'
import { DictionaryProvider } from '@/lib/i18n/dictionary-context'
import { SUPPORTED_LOCALES } from '@/lib/i18n/locales'
import { getDictionary, hasLocale } from './dictionaries'
import type { Locale } from './dictionaries'
import { notFound } from 'next/navigation'

const fraunces = Fraunces({
  variable: '--font-display',
  subsets: ['latin'],
  axes: ['opsz', 'SOFT', 'WONK'],
  weight: 'variable',
  style: ['normal', 'italic'],
})

const interTight = Inter_Tight({
  variable: '--font-body',
  subsets: ['latin'],
  weight: ['400', '500', '600', '700'],
})

const jetbrainsMono = JetBrains_Mono({
  variable: '--font-mono',
  subsets: ['latin'],
  weight: ['400', '500'],
})

export const metadata: Metadata = {
  title: 'Visusta — ESG Regulatory Intelligence',
  description: 'Consultant operations console for ESG compliance management',
}

export async function generateStaticParams() {
  return SUPPORTED_LOCALES.map((lang) => ({ lang }))
}

interface RootLayoutProps {
  children: React.ReactNode
  params: Promise<{ lang: string }>
}

export default async function RootLayout({ children, params }: RootLayoutProps) {
  const { lang } = await params

  if (!hasLocale(lang)) notFound()

  const dictionary = await getDictionary(lang as Locale)

  return (
    <html
      lang={lang}
      className={`${fraunces.variable} ${interTight.variable} ${jetbrainsMono.variable} h-full antialiased`}
    >
      <body className="h-full flex" style={{ background: 'var(--bg-primary)' }}>
        <DictionaryProvider dictionary={dictionary} locale={lang as Locale}>
          <Providers>
            <Sidebar />
            <main className="flex-1 overflow-y-auto">
              {children}
            </main>
          </Providers>
        </DictionaryProvider>
      </body>
    </html>
  )
}
