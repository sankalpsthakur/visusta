'use client'

import { useState } from 'react'
import { motion, type Variants, type Transition } from 'framer-motion'
import Link from 'next/link'
import { useRouter } from 'next/navigation'
import { PageTransition } from '@/components/shared/page-transition'
import { useActiveClient } from '@/lib/clients/context'
import { useCreateClient } from '@/lib/api/hooks'
import { useLocale } from '@/lib/i18n/dictionary-context'
import { Plus, MapPin, X } from 'lucide-react'
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
} from '@/components/ui/dialog'
import type { FacilityConfig } from '@/lib/api/hooks'

const container = {
  hidden: { opacity: 0 },
  show: {
    opacity: 1,
    transition: { staggerChildren: 0.06 },
  },
}

const cardTransition: Transition = { duration: 0.25, ease: 'easeOut' }

const cardVariant: Variants = {
  hidden: { opacity: 0, y: 16 },
  show: { opacity: 1, y: 0, transition: cardTransition },
}

const formSectionVariant: Variants = {
  hidden: { opacity: 0, y: 12 },
  show: { opacity: 1, y: 0, transition: { duration: 0.2, ease: 'easeOut' } },
}

const formContainer: Variants = {
  hidden: {},
  show: { transition: { staggerChildren: 0.06, delayChildren: 0.05 } },
}

const ALL_JURISDICTIONS = ['EU', 'DE', 'AT', 'CH', 'NO']
const ALL_TOPICS = ['ghg', 'packaging', 'water', 'waste', 'social_human_rights']

function slugify(val: string) {
  return val
    .toLowerCase()
    .trim()
    .replace(/[^a-z0-9]+/g, '-')
    .replace(/^-+|-+$/g, '')
}

export default function ClientsPage() {
  const router = useRouter()
  const { clients, isLoading } = useActiveClient()
  const createClient = useCreateClient()
  const locale = useLocale()
  const [dialogOpen, setDialogOpen] = useState(false)

  // Form state
  const [displayName, setDisplayName] = useState('')
  const [clientId, setClientId] = useState('')
  const [idManuallyEdited, setIdManuallyEdited] = useState(false)
  const [facilities, setFacilities] = useState<string[]>([])
  const [newFacility, setNewFacility] = useState('')
  const [jurisdictions, setJurisdictions] = useState<string[]>(['EU'])
  const [topics, setTopics] = useState<string[]>([...ALL_TOPICS])
  const [error, setError] = useState<string | null>(null)

  const resetForm = () => {
    setDisplayName('')
    setClientId('')
    setIdManuallyEdited(false)
    setFacilities([])
    setNewFacility('')
    setJurisdictions(['EU'])
    setTopics([...ALL_TOPICS])
    setError(null)
  }

  const handleNameChange = (val: string) => {
    setDisplayName(val)
    if (!idManuallyEdited) {
      setClientId(slugify(val))
    }
  }

  const addFacility = () => {
    const val = newFacility.trim()
    if (val && !facilities.includes(val)) setFacilities((p) => [...p, val])
    setNewFacility('')
  }

  const toggleJurisdiction = (j: string) =>
    setJurisdictions((p) => (p.includes(j) ? p.filter((x) => x !== j) : [...p, j]))

  const toggleTopic = (t: string) =>
    setTopics((p) => (p.includes(t) ? p.filter((x) => x !== t) : [...p, t]))

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    setError(null)
    if (!displayName.trim()) { setError('Display name is required'); return }
    if (!clientId.trim()) { setError('Client ID is required'); return }
    try {
      const facilityConfigs: FacilityConfig[] = facilities.map((name) => ({
        name,
        jurisdiction: jurisdictions[0] ?? 'EU',
      }))
      const result = await createClient.mutateAsync({
        client_id: clientId,
        display_name: displayName,
        facilities: facilityConfigs,
        allowed_countries: jurisdictions,
        required_topics: topics,
      })
      setDialogOpen(false)
      resetForm()
      router.push(`/${locale}/clients/${result.client_id}`)
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to create client')
    }
  }

  return (
    <PageTransition className="p-8">
      <div className="max-w-5xl">
        <div className="mb-8">
          <h1
            className="text-2xl font-semibold tracking-tight mb-1"
            style={{ color: 'var(--text-primary)' }}
          >
            Clients
          </h1>
          <p className="text-sm" style={{ color: 'var(--text-muted)' }}>
            {isLoading ? '…' : clients.length} active workspaces
          </p>
        </div>

        <motion.div
          variants={container}
          initial="hidden"
          animate="show"
          className="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-3 gap-4"
        >
          {clients.map((client) => (
            <motion.div key={client.id} variants={cardVariant}>
              <Link href={`/${locale}/clients/${client.id}`} className="block">
                <motion.div
                  className="rounded-lg p-5"
                  style={{
                    background: 'var(--bg-surface)',
                    border: '1px solid var(--border-color)',
                  }}
                  whileHover={{ y: -2, borderColor: 'var(--brand)' }}
                  transition={{ duration: 0.15 }}
                >
                  <div className="flex items-center gap-3 mb-3">
                    <span
                      className="w-8 h-8 rounded flex items-center justify-center text-sm font-bold flex-shrink-0"
                      style={{ background: 'var(--brand-dark)', color: 'var(--brand-contrast)' }}
                    >
                      {client.name.charAt(0)}
                    </span>
                    <div>
                      <div className="font-semibold text-sm" style={{ color: 'var(--text-primary)' }}>
                        {client.name}
                      </div>
                      <div className="text-xs" style={{ color: 'var(--text-muted)' }}>
                        {client.allowed_countries.join(' / ')}
                      </div>
                    </div>
                  </div>
                  <div className="flex items-center gap-1 text-xs" style={{ color: 'var(--text-muted)' }}>
                    <MapPin className="w-3 h-3" />
                    {client.facilities.map((f) => f.name).join(', ') || 'No facilities'}
                  </div>
                  <div className="mt-3 flex flex-wrap gap-1">
                    {client.required_topics.slice(0, 3).map((t) => (
                      <span
                        key={t}
                        className="text-xs px-1.5 py-0.5 rounded"
                        style={{
                          background: 'var(--bg-elevated)',
                          color: 'var(--text-muted)',
                          border: '1px solid var(--border-color)',
                        }}
                      >
                        {t}
                      </span>
                    ))}
                    {client.required_topics.length > 3 && (
                      <span
                        className="text-xs px-1.5 py-0.5 rounded"
                        style={{
                          background: 'var(--bg-elevated)',
                          color: 'var(--text-muted)',
                          border: '1px solid var(--border-color)',
                        }}
                      >
                        +{client.required_topics.length - 3}
                      </span>
                    )}
                  </div>
                </motion.div>
              </Link>
            </motion.div>
          ))}

          {/* Add client card */}
          <motion.div variants={cardVariant}>
            <motion.div
              onClick={() => { resetForm(); setDialogOpen(true) }}
              className="rounded-lg p-5 flex flex-col items-center justify-center gap-2 cursor-pointer min-h-[140px]"
              style={{
                background: 'transparent',
                border: '1px dashed var(--border-color)',
              }}
              whileHover={{ borderColor: 'var(--brand)', y: -2 }}
              transition={{ duration: 0.15 }}
            >
              <div
                className="w-8 h-8 rounded-full flex items-center justify-center"
                style={{ background: 'var(--bg-elevated)' }}
              >
                <Plus className="w-4 h-4" style={{ color: 'var(--text-muted)' }} />
              </div>
              <span className="text-sm" style={{ color: 'var(--text-muted)' }}>
                Add Client
              </span>
            </motion.div>
          </motion.div>
        </motion.div>
      </div>

      {/* New client dialog */}
      <Dialog open={dialogOpen} onOpenChange={(open) => { setDialogOpen(open); if (!open) resetForm() }}>
        <DialogContent
          className="sm:max-w-lg"
          style={{
            background: 'var(--bg-surface)',
            border: '1px solid var(--border-color)',
            color: 'var(--text-primary)',
          }}
        >
          <DialogHeader>
            <DialogTitle style={{ color: 'var(--text-primary)' }}>New Client</DialogTitle>
          </DialogHeader>

          <form onSubmit={handleSubmit}>
            <motion.div
              variants={formContainer}
              initial="hidden"
              animate="show"
              className="flex flex-col gap-5 mt-2"
            >
              {/* Display name */}
              <motion.div variants={formSectionVariant}>
                <label className="text-xs font-medium mb-1.5 block" style={{ color: 'var(--text-muted)' }}>
                  Display name *
                </label>
                <input
                  type="text"
                  value={displayName}
                  onChange={(e) => handleNameChange(e.target.value)}
                  placeholder="Acme GmbH"
                  className="w-full text-sm px-3 py-2 rounded outline-none"
                  style={{
                    background: 'var(--bg-elevated)',
                    border: '1px solid var(--border-color)',
                    color: 'var(--text-primary)',
                  }}
                />
              </motion.div>

              {/* Client ID */}
              <motion.div variants={formSectionVariant}>
                <label className="text-xs font-medium mb-1.5 block" style={{ color: 'var(--text-muted)' }}>
                  Client ID *
                </label>
                <input
                  type="text"
                  value={clientId}
                  onChange={(e) => { setClientId(slugify(e.target.value)); setIdManuallyEdited(true) }}
                  placeholder="acme-gmbh"
                  className="w-full text-sm px-3 py-2 rounded outline-none"
                  style={{
                    background: 'var(--bg-elevated)',
                    border: '1px solid var(--border-color)',
                    color: 'var(--text-primary)',
                    fontFamily: 'var(--font-mono)',
                  }}
                />
              </motion.div>

              {/* Facilities */}
              <motion.div variants={formSectionVariant}>
                <label className="text-xs font-medium mb-1.5 block" style={{ color: 'var(--text-muted)' }}>
                  Facilities
                </label>
                <div className="flex gap-1.5 flex-wrap mb-2">
                  {facilities.map((f) => (
                    <span
                      key={f}
                      className="flex items-center gap-1 text-xs px-2 py-0.5 rounded"
                      style={{
                        background: 'var(--bg-elevated)',
                        color: 'var(--text-muted)',
                        border: '1px solid var(--border-color)',
                      }}
                    >
                      {f}
                      <button type="button" onClick={() => setFacilities((p) => p.filter((x) => x !== f))}>
                        <X className="w-3 h-3" />
                      </button>
                    </span>
                  ))}
                </div>
                <div className="flex gap-2">
                  <input
                    type="text"
                    value={newFacility}
                    onChange={(e) => setNewFacility(e.target.value)}
                    onKeyDown={(e) => { if (e.key === 'Enter') { e.preventDefault(); addFacility() } }}
                    placeholder="Hamburg"
                    className="flex-1 text-sm px-3 py-1.5 rounded outline-none"
                    style={{
                      background: 'var(--bg-elevated)',
                      border: '1px solid var(--border-color)',
                      color: 'var(--text-primary)',
                    }}
                  />
                  <button
                    type="button"
                    onClick={addFacility}
                    className="text-xs px-3 py-1.5 rounded"
                    style={{ background: 'var(--bg-elevated)', border: '1px solid var(--border-color)', color: 'var(--text-muted)' }}
                  >
                    Add
                  </button>
                </div>
              </motion.div>

              {/* Jurisdictions */}
              <motion.div variants={formSectionVariant}>
                <label className="text-xs font-medium mb-1.5 block" style={{ color: 'var(--text-muted)' }}>
                  Jurisdictions
                </label>
                <div className="flex gap-1.5 flex-wrap">
                  {ALL_JURISDICTIONS.map((j) => (
                    <button
                      type="button"
                      key={j}
                      onClick={() => toggleJurisdiction(j)}
                      className="text-xs px-2.5 py-1 rounded transition-all"
                      style={{
                        background: jurisdictions.includes(j) ? 'var(--brand)' : 'var(--bg-elevated)',
                        color: jurisdictions.includes(j) ? 'var(--brand-contrast)' : 'var(--text-muted)',
                        border: '1px solid var(--border-color)',
                        fontFamily: 'var(--font-mono)',
                      }}
                    >
                      {j}
                    </button>
                  ))}
                </div>
              </motion.div>

              {/* Topics */}
              <motion.div variants={formSectionVariant}>
                <label className="text-xs font-medium mb-1.5 block" style={{ color: 'var(--text-muted)' }}>
                  Topics
                </label>
                <div className="flex gap-1.5 flex-wrap">
                  {ALL_TOPICS.map((t) => (
                    <button
                      type="button"
                      key={t}
                      onClick={() => toggleTopic(t)}
                      className="text-xs px-2.5 py-1 rounded transition-all"
                      style={{
                        background: topics.includes(t)
                          ? 'color-mix(in srgb, var(--brand-accent) 15%, var(--bg-elevated))'
                          : 'var(--bg-elevated)',
                        color: topics.includes(t) ? 'var(--brand-accent)' : 'var(--text-muted)',
                        border: `1px solid ${topics.includes(t) ? 'var(--brand)' : 'var(--border-color)'}`,
                        fontFamily: 'var(--font-mono)',
                      }}
                    >
                      {t}
                    </button>
                  ))}
                </div>
              </motion.div>

              {/* Error */}
              {error && (
                <motion.div
                  initial={{ opacity: 0 }}
                  animate={{ opacity: 1 }}
                  className="text-xs px-3 py-2 rounded"
                  style={{
                    background: 'color-mix(in srgb, var(--severity-critical) 10%, transparent)',
                    color: 'var(--severity-critical)',
                    border: '1px solid color-mix(in srgb, var(--severity-critical) 25%, transparent)',
                  }}
                >
                  {error}
                </motion.div>
              )}

              {/* Actions */}
              <motion.div variants={formSectionVariant} className="flex justify-end gap-2 pt-1">
                <button
                  type="button"
                  onClick={() => { setDialogOpen(false); resetForm() }}
                  className="text-sm px-4 py-1.5 rounded"
                  style={{
                    background: 'var(--bg-elevated)',
                    border: '1px solid var(--border-color)',
                    color: 'var(--text-muted)',
                  }}
                >
                  Cancel
                </button>
                <motion.button
                  type="submit"
                  disabled={createClient.isPending}
                  className="text-sm px-4 py-1.5 rounded font-medium"
                  style={{
                    background: 'var(--brand)',
                    color: 'var(--brand-contrast)',
                    opacity: createClient.isPending ? 0.6 : 1,
                  }}
                  whileHover={{ opacity: 0.85 }}
                  whileTap={{ scale: 0.97 }}
                >
                  {createClient.isPending ? 'Creating…' : 'Create client'}
                </motion.button>
              </motion.div>
            </motion.div>
          </form>
        </DialogContent>
      </Dialog>
    </PageTransition>
  )
}
