import type { ReactNode } from 'react'

interface DraftLayoutProps {
  children: ReactNode
}

export default function DraftLayout({ children }: DraftLayoutProps) {
  return (
    <div style={{ height: '100vh', display: 'flex', flexDirection: 'column', overflow: 'hidden' }}>
      {children}
    </div>
  )
}
