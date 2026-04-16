'use client'

import { use, useState } from 'react'
import { motion, AnimatePresence } from 'framer-motion'
import { PageTransition } from '@/components/shared/page-transition'
import { Skeleton } from '@/components/ui/skeleton'
import {
  useClient, useUpdateClient, FacilityConfig,
  useSources, useUpdateSources, SourceConfig,
  useThresholds, useUpdateThresholds, Thresholds,
  usePreferences, useUpdatePreferences, ReportPreferences,
  useLocales, useClientLocaleSettings, useUpdateClientLocaleSettings,
} from '@/lib/api/hooks'
import { Check, Plus, X, ChevronUp, ChevronDown } from 'lucide-react'

interface SettingsPageProps {
  params: Promise<{ clientId: string }>
}

const ALL_TOPICS = ['ghg', 'packaging', 'water', 'waste', 'social_human_rights']
const ALL_JURISDICTIONS = ['EU', 'DE', 'AT', 'CH', 'NO']
const FREQUENCIES = ['daily', 'weekly', 'monthly'] as const
const TONES = ['executive', 'technical', 'boardroom'] as const
const DEPTHS = ['brief', 'standard', 'deep'] as const
const CHART_OPTIONS = ['severity_heatmap', 'enforcement_timeline', 'topic_distribution', 'change_velocity', 'jurisdiction_map']

function SectionHeading({ children }: { children: React.ReactNode }) {
  return (
    <div
      className="text-xs font-semibold tracking-wide uppercase mb-3"
      style={{ color: 'var(--text-muted)' }}
    >
      {children}
    </div>
  )
}

function SavedBadge({ show }: { show: boolean }) {
  return (
    <AnimatePresence>
      {show && (
        <motion.span
          initial={{ opacity: 0, scale: 0.8 }}
          animate={{ opacity: 1, scale: 1 }}
          exit={{ opacity: 0 }}
          className="flex items-center gap-1.5 text-xs"
          style={{ color: 'var(--severity-low)' }}
        >
          <Check className="w-3.5 h-3.5" />
          Saved
        </motion.span>
      )}
    </AnimatePresence>
  )
}

function SaveButton({ onClick, isPending }: { onClick: () => void; isPending: boolean }) {
  return (
    <motion.button
      onClick={onClick}
      disabled={isPending}
      className="text-sm px-4 py-1.5 rounded font-medium transition-opacity"
      style={{
        background: 'var(--brand)',
        color: 'var(--brand-contrast)',
        opacity: isPending ? 0.6 : 1,
      }}
      whileHover={{ opacity: 0.85 }}
      whileTap={{ scale: 0.97 }}
    >
      {isPending ? 'Saving…' : 'Save'}
    </motion.button>
  )
}

function SettingRow({
  label,
  description,
  value,
}: {
  label: string
  description?: string
  value: React.ReactNode
}) {
  return (
    <div
      className="flex items-start justify-between py-4"
      style={{ borderBottom: '1px solid var(--border-color)' }}
    >
      <div className="flex-1 pr-8">
        <div className="text-sm font-medium" style={{ color: 'var(--text-primary)' }}>
          {label}
        </div>
        {description && (
          <div className="text-xs mt-0.5" style={{ color: 'var(--text-muted)' }}>
            {description}
          </div>
        )}
      </div>
      <div className="flex-shrink-0">{value}</div>
    </div>
  )
}

function SkeletonSettingRow() {
  return (
    <div
      className="flex items-start justify-between py-4"
      style={{ borderBottom: '1px solid var(--border-color)' }}
    >
      <div className="flex-1 pr-8">
        <Skeleton className="h-4 w-32 mb-1" style={{ background: 'var(--bg-elevated)' }} />
        <Skeleton className="h-3 w-48" style={{ background: 'var(--bg-elevated)' }} />
      </div>
      <Skeleton className="h-7 w-24" style={{ background: 'var(--bg-elevated)' }} />
    </div>
  )
}

// ── Report Language section ───────────────────────────────────────────────────

function ReportLanguageSection({ clientId }: { clientId: string }) {
  const { data: locales } = useLocales()
  const { data: settings, isLoading } = useClientLocaleSettings(clientId)
  const updateSettings = useUpdateClientLocaleSettings(clientId)
  const [saved, setSaved] = useState(false)

  if (isLoading || !settings) {
    return (
      <div className="mb-8">
        <SectionHeading>Report Language</SectionHeading>
        <div className="rounded-lg overflow-hidden" style={{ background: 'var(--bg-surface)', border: '1px solid var(--border-color)' }}>
          <div className="px-5"><SkeletonSettingRow /></div>
        </div>
      </div>
    )
  }

  const handleChange = async (locale: string) => {
    await updateSettings.mutateAsync({ primary_locale: locale, enabled_locales: [locale, 'en'] })
    setSaved(true)
    setTimeout(() => setSaved(false), 2000)
  }

  return (
    <div className="mb-8">
      <div className="flex items-center justify-between mb-3">
        <SectionHeading>Report Language</SectionHeading>
        <SavedBadge show={saved} />
      </div>
      <div className="rounded-lg overflow-hidden" style={{ background: 'var(--bg-surface)', border: '1px solid var(--border-color)' }}>
        <div className="px-5">
          <SettingRow
            label="Primary language"
            description="Default language for new drafts. Compose and translate actions in the draft studio can override this per-draft."
            value={
              <select
                value={settings.primary_locale}
                onChange={(e) => handleChange(e.target.value)}
                className="text-sm rounded px-3 py-1.5"
                style={{ background: 'var(--bg-elevated)', color: 'var(--text-primary)', border: '1px solid var(--border-color)' }}
              >
                {(locales ?? []).map((l) => (
                  <option key={l.code} value={l.code}>
                    {l.name} ({l.native_name})
                  </option>
                ))}
                {!locales?.length && <option value={settings.primary_locale}>{settings.primary_locale}</option>}
              </select>
            }
          />
          <SettingRow
            label="Fallback language"
            description="Used when content is not available in the primary language."
            value={
              <span className="text-sm px-3 py-1.5 rounded" style={{ background: 'var(--bg-elevated)', color: 'var(--text-muted)' }}>
                {settings.fallback_locale.toUpperCase()}
              </span>
            }
          />
        </div>
      </div>
    </div>
  )
}

// ── Sources section ────────────────────────────────────────────────────────────

function SourcesSection({ clientId }: { clientId: string }) {
  const { data: remoteSources, isLoading } = useSources(clientId)

  if (isLoading || !remoteSources) {
    return (
      <div className="mb-8">
        <SectionHeading>Monitored Sources</SectionHeading>
        <div
          className="rounded-lg overflow-hidden"
          style={{ background: 'var(--bg-surface)', border: '1px solid var(--border-color)' }}
        >
          <div className="px-5">
            <SkeletonSettingRow />
            <SkeletonSettingRow />
          </div>
        </div>
      </div>
    )
  }

  return <SourcesSectionLoaded clientId={clientId} initialSources={remoteSources} />
}

function SourcesSectionLoaded({ clientId, initialSources }: { clientId: string; initialSources: SourceConfig[] }) {
  const updateSources = useUpdateSources(clientId)
  const [sources, setSources] = useState<SourceConfig[]>(initialSources)
  const [saved, setSaved] = useState(false)

  const addSource = () => {
    setSources((prev) => [
      ...prev,
      { id: `src-${Date.now()}`, display_name: '', url: '', frequency: 'weekly', source_type: 'gazette' },
    ])
  }

  const removeSource = (idx: number) => setSources((prev) => prev.filter((_, i) => i !== idx))

  const updateField = (idx: number, field: keyof SourceConfig, val: string) => {
    setSources((prev) => prev.map((s, i) => i === idx ? { ...s, [field]: val } : s))
  }

  const handleSave = async () => {
    await updateSources.mutateAsync(sources)
    setSaved(true)
    setTimeout(() => setSaved(false), 2000)
  }

  return (
    <div className="mb-8">
      <div className="flex items-center justify-between mb-3">
        <SectionHeading>Monitored Sources</SectionHeading>
        <div className="flex items-center gap-3">
          <SavedBadge show={saved} />
          <SaveButton onClick={handleSave} isPending={updateSources.isPending} />
        </div>
      </div>
      <div
        className="rounded-lg overflow-hidden"
        style={{ background: 'var(--bg-surface)', border: '1px solid var(--border-color)' }}
      >
        {sources.length === 0 ? (
          <div className="px-5 py-6 text-sm text-center" style={{ color: 'var(--text-muted)' }}>
            No sources configured.
          </div>
        ) : (
          sources.map((src, idx) => (
            <div
              key={src.id}
              className="px-5 py-4"
              style={{ borderBottom: idx < sources.length - 1 ? '1px solid var(--border-color)' : undefined }}
            >
              <div className="grid grid-cols-[1fr_1fr_auto_auto] gap-3 items-center">
                <input
                  type="text"
                  value={src.display_name}
                  onChange={(e) => updateField(idx, 'display_name', e.target.value)}
                  placeholder="Source name"
                  className="text-sm px-2.5 py-1.5 rounded outline-none"
                  style={{
                    background: 'var(--bg-elevated)',
                    border: '1px solid var(--border-color)',
                    color: 'var(--text-primary)',
                  }}
                />
                <input
                  type="text"
                  value={src.url ?? ''}
                  onChange={(e) => updateField(idx, 'url', e.target.value)}
                  placeholder="https://…"
                  className="text-sm px-2.5 py-1.5 rounded outline-none"
                  style={{
                    background: 'var(--bg-elevated)',
                    border: '1px solid var(--border-color)',
                    color: 'var(--text-primary)',
                    fontFamily: 'var(--font-mono)',
                  }}
                />
                <select
                  value={src.frequency}
                  onChange={(e) => updateField(idx, 'frequency', e.target.value)}
                  className="text-xs px-2 py-1.5 rounded outline-none"
                  style={{
                    background: 'var(--bg-elevated)',
                    border: '1px solid var(--border-color)',
                    color: 'var(--text-muted)',
                  }}
                >
                  {FREQUENCIES.map((f) => (
                    <option key={f} value={f}>{f}</option>
                  ))}
                </select>
                <button
                  onClick={() => removeSource(idx)}
                  className="p-1.5 rounded"
                  style={{ background: 'var(--bg-elevated)', border: '1px solid var(--border-color)' }}
                >
                  <X className="w-3.5 h-3.5" style={{ color: 'var(--text-muted)' }} />
                </button>
              </div>
            </div>
          ))
        )}
        <div
          className="px-5 py-3"
          style={{ borderTop: sources.length > 0 ? '1px solid var(--border-color)' : undefined }}
        >
          <button
            onClick={addSource}
            className="flex items-center gap-1.5 text-xs"
            style={{ color: 'var(--text-muted)' }}
          >
            <Plus className="w-3.5 h-3.5" />
            Add source
          </button>
        </div>
      </div>
    </div>
  )
}

// ── Thresholds section ─────────────────────────────────────────────────────────

function ThresholdsSection({ clientId }: { clientId: string }) {
  const { data: remoteThresholds, isLoading } = useThresholds(clientId)

  if (isLoading || !remoteThresholds) {
    return (
      <div className="mb-8">
        <SectionHeading>Thresholds</SectionHeading>
        <div
          className="rounded-lg px-5"
          style={{ background: 'var(--bg-surface)', border: '1px solid var(--border-color)' }}
        >
          <SkeletonSettingRow />
          <SkeletonSettingRow />
          <SkeletonSettingRow />
        </div>
      </div>
    )
  }

  return <ThresholdsSectionLoaded clientId={clientId} initialThresholds={remoteThresholds} />
}

function ThresholdsSectionLoaded({ clientId, initialThresholds }: { clientId: string; initialThresholds: Thresholds }) {
  const updateThresholds = useUpdateThresholds(clientId)
  const [thresholds, setThresholds] = useState<Thresholds>(initialThresholds)
  const [saved, setSaved] = useState(false)

  const handleSave = async () => {
    await updateThresholds.mutateAsync(thresholds)
    setSaved(true)
    setTimeout(() => setSaved(false), 2000)
  }

  const sliders: Array<{
    key: keyof Thresholds
    label: string
    description: string
    min: number
    max: number
    step: number
    format: (v: number) => string
  }> = [
    {
      key: 'critical_enforcement_window_days',
      label: 'Critical enforcement window',
      description: 'Days before enforcement date a change is flagged critical',
      min: 30, max: 180, step: 10,
      format: (v) => `${v}d`,
    },
    {
      key: 'min_confidence',
      label: 'Minimum confidence',
      description: 'Minimum model confidence to include a regulatory change',
      min: 0, max: 1, step: 0.05,
      format: (v) => v.toFixed(2),
    },
    {
      key: 'min_sources_per_entry',
      label: 'Minimum sources per entry',
      description: 'Number of independent sources required to surface a change',
      min: 1, max: 5, step: 1,
      format: (v) => String(v),
    },
  ]

  return (
    <div className="mb-8">
      <div className="flex items-center justify-between mb-3">
        <SectionHeading>Thresholds</SectionHeading>
        <div className="flex items-center gap-3">
          <SavedBadge show={saved} />
          <SaveButton onClick={handleSave} isPending={updateThresholds.isPending} />
        </div>
      </div>
      <div
        className="rounded-lg px-5"
        style={{ background: 'var(--bg-surface)', border: '1px solid var(--border-color)' }}
      >
        {sliders.map((slider, idx) => (
          <div
            key={slider.key}
            className="flex items-start justify-between py-4"
            style={{ borderBottom: idx < sliders.length - 1 ? '1px solid var(--border-color)' : undefined }}
          >
            <div className="flex-1 pr-8">
              <div className="text-sm font-medium mb-0.5" style={{ color: 'var(--text-primary)' }}>
                {slider.label}
              </div>
              <div className="text-xs" style={{ color: 'var(--text-muted)' }}>
                {slider.description}
              </div>
            </div>
            <div className="flex items-center gap-3 flex-shrink-0">
              <span
                className="text-sm tabular-nums w-10 text-right"
                style={{ color: 'var(--brand-accent)', fontFamily: 'var(--font-mono)' }}
              >
                {slider.format(thresholds[slider.key] as number)}
              </span>
              <input
                type="range"
                min={slider.min}
                max={slider.max}
                step={slider.step}
                value={thresholds[slider.key] as number}
                onChange={(e) =>
                  setThresholds((prev) => ({
                    ...prev,
                    [slider.key]: parseFloat(e.target.value),
                  }))
                }
                className="w-32"
                style={{ accentColor: 'var(--brand-accent)' }}
              />
            </div>
          </div>
        ))}
      </div>
    </div>
  )
}

// ── Report preferences section ─────────────────────────────────────────────────

function PreferencesSection({ clientId }: { clientId: string }) {
  const { data: remotePrefs, isLoading } = usePreferences(clientId)

  if (isLoading || !remotePrefs) {
    return (
      <div className="mb-8">
        <SectionHeading>Report Preferences</SectionHeading>
        <div
          className="rounded-lg px-5"
          style={{ background: 'var(--bg-surface)', border: '1px solid var(--border-color)' }}
        >
          <SkeletonSettingRow />
          <SkeletonSettingRow />
          <SkeletonSettingRow />
          <SkeletonSettingRow />
        </div>
      </div>
    )
  }

  return <PreferencesSectionLoaded clientId={clientId} initialPrefs={remotePrefs} />
}

function PreferencesSectionLoaded({ clientId, initialPrefs }: { clientId: string; initialPrefs: ReportPreferences }) {
  const updatePreferences = useUpdatePreferences(clientId)
  const [prefs, setPrefs] = useState<ReportPreferences>(initialPrefs)
  const [saved, setSaved] = useState(false)

  const handleSave = async () => {
    await updatePreferences.mutateAsync(prefs)
    setSaved(true)
    setTimeout(() => setSaved(false), 2000)
  }

  const toggleChart = (chart: string) => {
    setPrefs((prev) => ({
      ...prev,
      chart_mix: prev.chart_mix.includes(chart)
        ? prev.chart_mix.filter((c) => c !== chart)
        : [...prev.chart_mix, chart],
    }))
  }

  const moveSection = (idx: number, dir: -1 | 1) => {
    const next = idx + dir
    if (next < 0 || next >= prefs.section_order.length) return
    setPrefs((prev) => {
      const order = [...prev.section_order]
      ;[order[idx], order[next]] = [order[next], order[idx]]
      return { ...prev, section_order: order }
    })
  }

  const selectStyle = {
    background: 'var(--bg-elevated)',
    border: '1px solid var(--border-color)',
    color: 'var(--text-primary)',
  }

  return (
    <div className="mb-8">
      <div className="flex items-center justify-between mb-3">
        <SectionHeading>Report Preferences</SectionHeading>
        <div className="flex items-center gap-3">
          <SavedBadge show={saved} />
          <SaveButton onClick={handleSave} isPending={updatePreferences.isPending} />
        </div>
      </div>
      <div
        className="rounded-lg px-5"
        style={{ background: 'var(--bg-surface)', border: '1px solid var(--border-color)' }}
      >
        <SettingRow
          label="Tone"
          description="Writing style for generated reports"
          value={
            <select
              value={prefs.tone}
              onChange={(e) => setPrefs((p) => ({ ...p, tone: e.target.value }))}
              className="text-sm px-2.5 py-1 rounded outline-none"
              style={selectStyle}
            >
              {TONES.map((t) => <option key={t} value={t}>{t}</option>)}
            </select>
          }
        />
        <SettingRow
          label="Depth"
          description="Level of detail in report sections"
          value={
            <select
              value={prefs.depth}
              onChange={(e) => setPrefs((p) => ({ ...p, depth: e.target.value }))}
              className="text-sm px-2.5 py-1 rounded outline-none"
              style={selectStyle}
            >
              {DEPTHS.map((d) => <option key={d} value={d}>{d}</option>)}
            </select>
          }
        />
        <div className="py-4" style={{ borderBottom: '1px solid var(--border-color)' }}>
          <div className="text-sm font-medium mb-3" style={{ color: 'var(--text-primary)' }}>
            Chart mix
          </div>
          <div className="flex flex-col gap-2">
            {CHART_OPTIONS.map((chart) => (
              <label key={chart} className="flex items-center gap-2 cursor-pointer">
                <input
                  type="checkbox"
                  checked={prefs.chart_mix.includes(chart)}
                  onChange={() => toggleChart(chart)}
                  style={{ accentColor: 'var(--brand-accent)' }}
                />
                <span
                  className="text-xs"
                  style={{
                    color: prefs.chart_mix.includes(chart) ? 'var(--text-primary)' : 'var(--text-muted)',
                    fontFamily: 'var(--font-mono)',
                  }}
                >
                  {chart}
                </span>
              </label>
            ))}
          </div>
        </div>
        <div className="py-4">
          <div className="flex items-baseline gap-2 mb-3">
            <div className="text-sm font-medium" style={{ color: 'var(--text-primary)' }}>
              Section order
            </div>
            <div className="text-xs" style={{ color: 'var(--text-muted)' }}>
              Controls the section order in both monthly and quarterly reports.
            </div>
          </div>
          <div className="flex flex-col gap-1.5">
            {prefs.section_order.map((section, idx) => (
              <div
                key={section}
                className="flex items-center justify-between px-3 py-2 rounded"
                style={{
                  background: 'var(--bg-elevated)',
                  border: '1px solid var(--border-color)',
                }}
              >
                <span
                  className="text-xs"
                  style={{ color: 'var(--text-primary)', fontFamily: 'var(--font-mono)' }}
                >
                  {section}
                </span>
                <div className="flex gap-1">
                  <button
                    onClick={() => moveSection(idx, -1)}
                    disabled={idx === 0}
                    className="p-0.5 rounded"
                    style={{ opacity: idx === 0 ? 0.3 : 1 }}
                  >
                    <ChevronUp className="w-3.5 h-3.5" style={{ color: 'var(--text-muted)' }} />
                  </button>
                  <button
                    onClick={() => moveSection(idx, 1)}
                    disabled={idx === prefs.section_order.length - 1}
                    className="p-0.5 rounded"
                    style={{ opacity: idx === prefs.section_order.length - 1 ? 0.3 : 1 }}
                  >
                    <ChevronDown className="w-3.5 h-3.5" style={{ color: 'var(--text-muted)' }} />
                  </button>
                </div>
              </div>
            ))}
          </div>
        </div>
      </div>
    </div>
  )
}

// ── Page ───────────────────────────────────────────────────────────────────────

export default function SettingsPage({ params }: SettingsPageProps) {
  const { clientId } = use(params)
  const { data: remoteClient, isLoading } = useClient(clientId)

  if (!isLoading && !remoteClient) {
    return (
      <PageTransition className="p-8">
        <div style={{ color: 'var(--text-muted)' }}>Client not found.</div>
      </PageTransition>
    )
  }

  return (
    <PageTransition className="p-8">
      <div className="max-w-2xl">
        <div className="mb-8">
          <h2 className="text-lg font-semibold mb-1" style={{ color: 'var(--text-primary)' }}>
            Settings
          </h2>
          <p className="text-sm" style={{ color: 'var(--text-muted)' }}>
            Configuration for {remoteClient?.display_name ?? clientId}
          </p>
        </div>

        {isLoading || !remoteClient ? (
          <>
            {/* Identity skeleton */}
            <div className="mb-8">
              <SectionHeading>Identity</SectionHeading>
              <div
                className="rounded-lg px-5"
                style={{ background: 'var(--bg-surface)', border: '1px solid var(--border-color)' }}
              >
                <SkeletonSettingRow />
                <SkeletonSettingRow />
                <SkeletonSettingRow />
              </div>
            </div>
            {/* Topics skeleton */}
            <div className="mb-8">
              <SectionHeading>Monitored Topics</SectionHeading>
              <div
                className="rounded-lg px-5 py-4"
                style={{ background: 'var(--bg-surface)', border: '1px solid var(--border-color)' }}
              >
                <div className="flex flex-wrap gap-2">
                  {[80, 64, 72, 56, 96].map((w) => (
                    <Skeleton key={w} className="h-7 rounded" style={{ width: w, background: 'var(--bg-elevated)' }} />
                  ))}
                </div>
              </div>
            </div>
          </>
        ) : (
          <SettingsPageLoaded clientId={clientId} remoteClient={remoteClient} />
        )}

        {/* Report Language section */}
        <ReportLanguageSection clientId={clientId} />

        {/* Sources section */}
        <SourcesSection clientId={clientId} />

        {/* Thresholds section */}
        <ThresholdsSection clientId={clientId} />

        {/* Report Preferences section */}
        <PreferencesSection clientId={clientId} />
      </div>
    </PageTransition>
  )
}

function SettingsPageLoaded({
  clientId,
  remoteClient,
}: {
  clientId: string
  remoteClient: NonNullable<ReturnType<typeof useClient>['data']>
}) {
  const updateClient = useUpdateClient(clientId)

  const [displayName, setDisplayName] = useState(remoteClient.display_name ?? '')
  const [facilities, setFacilities] = useState<FacilityConfig[]>(remoteClient.facilities ?? [])
  const [jurisdictions, setJurisdictions] = useState<string[]>(remoteClient.allowed_countries ?? [])
  const [topics, setTopics] = useState<string[]>(remoteClient.required_topics ?? [])
  const [newFacility, setNewFacility] = useState('')
  const [newTopic, setNewTopic] = useState('')
  const [saved, setSaved] = useState(false)
  const [screeningEnabled, setScreeningEnabled] = useState(true)
  const [alertsEnabled, setAlertsEnabled] = useState(true)

  const handleSave = async () => {
    await updateClient.mutateAsync({
      display_name: displayName,
      facilities,
      allowed_countries: jurisdictions,
      required_topics: topics,
    })
    setSaved(true)
    setTimeout(() => setSaved(false), 2000)
  }

  const addFacility = () => {
    const val = newFacility.trim()
    if (val && !facilities.some((f) => f.name === val)) {
      setFacilities((prev) => [...prev, { name: val, jurisdiction: '' }])
    }
    setNewFacility('')
  }

  const removeFacility = (name: string) => setFacilities((prev) => prev.filter((f) => f.name !== name))

  const toggleJurisdiction = (j: string) => {
    setJurisdictions((prev) =>
      prev.includes(j) ? prev.filter((x) => x !== j) : [...prev, j]
    )
  }

  const toggleTopic = (t: string) => {
    setTopics((prev) =>
      prev.includes(t) ? prev.filter((x) => x !== t) : [...prev, t]
    )
  }

  return (
    <>
      {/* Identity section */}
      <div className="mb-8">
        <div className="flex items-center justify-between mb-3">
          <SectionHeading>Identity</SectionHeading>
          <div className="flex items-center gap-3">
            <SavedBadge show={saved} />
            <SaveButton onClick={handleSave} isPending={updateClient.isPending} />
          </div>
        </div>
        <div
          className="rounded-lg px-5"
          style={{ background: 'var(--bg-surface)', border: '1px solid var(--border-color)' }}
        >
          <SettingRow
            label="Client ID"
            value={
              <span
                className="text-xs px-2 py-1 rounded"
                style={{
                  fontFamily: 'var(--font-mono)',
                  background: 'var(--bg-elevated)',
                  color: 'var(--text-muted)',
                }}
              >
                {clientId}
              </span>
            }
          />
          <SettingRow
            label="Display name"
            value={
              <input
                type="text"
                value={displayName}
                onChange={(e) => setDisplayName(e.target.value)}
                className="text-sm px-2.5 py-1 rounded outline-none w-48"
                style={{
                  background: 'var(--bg-elevated)',
                  border: '1px solid var(--border-color)',
                  color: 'var(--text-primary)',
                }}
              />
            }
          />
          <SettingRow
            label="Jurisdictions"
            value={
              <div className="flex gap-1.5 flex-wrap justify-end">
                {ALL_JURISDICTIONS.map((j) => (
                  <button
                    key={j}
                    onClick={() => toggleJurisdiction(j)}
                    className="text-xs px-2 py-0.5 rounded transition-all"
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
            }
          />
          <div className="flex items-start justify-between py-4">
            <div className="text-sm font-medium" style={{ color: 'var(--text-primary)' }}>
              Facilities
            </div>
            <div className="flex flex-col items-end gap-2">
              <div className="flex flex-wrap gap-1.5 justify-end">
                {facilities.map((f) => (
                  <span
                    key={f.name}
                    className="flex items-center gap-1 text-xs px-2 py-0.5 rounded"
                    style={{
                      background: 'var(--bg-elevated)',
                      color: 'var(--text-muted)',
                      border: '1px solid var(--border-color)',
                    }}
                  >
                    {f.name}
                    <button onClick={() => removeFacility(f.name)}>
                      <X className="w-3 h-3" style={{ color: 'var(--text-muted)' }} />
                    </button>
                  </span>
                ))}
              </div>
              <div className="flex gap-1">
                <input
                  type="text"
                  value={newFacility}
                  onChange={(e) => setNewFacility(e.target.value)}
                  onKeyDown={(e) => e.key === 'Enter' && addFacility()}
                  placeholder="Add facility…"
                  className="text-xs px-2 py-1 rounded outline-none w-32"
                  style={{
                    background: 'var(--bg-elevated)',
                    border: '1px solid var(--border-color)',
                    color: 'var(--text-primary)',
                  }}
                />
                <button
                  onClick={addFacility}
                  className="p-1 rounded"
                  style={{ background: 'var(--bg-elevated)', border: '1px solid var(--border-color)' }}
                >
                  <Plus className="w-3.5 h-3.5" style={{ color: 'var(--text-muted)' }} />
                </button>
              </div>
            </div>
          </div>
        </div>
      </div>

      {/* Topics section */}
      <div className="mb-8">
        <SectionHeading>Monitored Topics</SectionHeading>
        <div
          className="rounded-lg px-5 py-4"
          style={{ background: 'var(--bg-surface)', border: '1px solid var(--border-color)' }}
        >
          <div className="flex flex-wrap gap-2">
            {Array.from(new Set([...ALL_TOPICS, ...topics])).map((t) => (
              <button
                key={t}
                onClick={() => toggleTopic(t)}
                className="text-xs px-2.5 py-1 rounded transition-all flex items-center gap-1"
                style={{
                  background: topics.includes(t) ? 'color-mix(in srgb, var(--brand-accent) 15%, var(--bg-elevated))' : 'var(--bg-elevated)',
                  color: topics.includes(t) ? 'var(--brand-accent)' : 'var(--text-muted)',
                  border: `1px solid ${topics.includes(t) ? 'var(--brand)' : 'var(--border-color)'}`,
                  fontFamily: 'var(--font-mono)',
                }}
              >
                {t}
                {topics.includes(t) && !ALL_TOPICS.includes(t) && (
                  <X size={10} />
                )}
              </button>
            ))}
          </div>
          <div className="flex items-center gap-2 mt-3">
            <input
              value={newTopic}
              onChange={(e) => setNewTopic(e.target.value)}
              onKeyDown={(e) => {
                if (e.key === 'Enter') {
                  const val = newTopic.trim().toLowerCase().replace(/\s+/g, '_')
                  if (val && !topics.includes(val)) {
                    setTopics((prev) => [...prev, val])
                  }
                  setNewTopic('')
                }
              }}
              placeholder="Add topic…"
              className="text-xs px-2.5 py-1 rounded flex-1"
              style={{
                background: 'var(--bg-elevated)',
                border: '1px solid var(--border-color)',
                color: 'var(--text-primary)',
                fontFamily: 'var(--font-mono)',
                maxWidth: 180,
              }}
            />
            <button
              onClick={() => {
                const val = newTopic.trim().toLowerCase().replace(/\s+/g, '_')
                if (val && !topics.includes(val)) {
                  setTopics((prev) => [...prev, val])
                }
                setNewTopic('')
              }}
              className="p-1 rounded"
              style={{ background: 'var(--bg-elevated)', border: '1px solid var(--border-color)', color: 'var(--text-muted)' }}
            >
              <Plus size={14} />
            </button>
          </div>
        </div>
      </div>

      {/* Automation section */}
      <div>
        <SectionHeading>Automation</SectionHeading>
        <div
          className="rounded-lg px-5"
          style={{ background: 'var(--bg-surface)', border: '1px solid var(--border-color)' }}
        >
          <SettingRow
            label="Regulatory screening"
            description="Automatically screen for new regulations each month"
            value={
              <button
                onClick={() => setScreeningEnabled((v) => !v)}
                className="relative w-10 h-5 rounded-full transition-colors"
                style={{
                  background: screeningEnabled ? 'var(--brand)' : 'var(--bg-elevated)',
                  border: '1px solid var(--border-color)',
                }}
              >
                <span
                  className="absolute top-0.5 w-4 h-4 rounded-full transition-all"
                  style={{
                    background: screeningEnabled ? 'var(--brand-contrast)' : 'var(--text-muted)',
                    left: screeningEnabled ? '1.25rem' : '0.125rem',
                  }}
                />
              </button>
            }
          />
          <SettingRow
            label="Change alerts"
            description="Notify when critical regulatory changes are detected"
            value={
              <button
                onClick={() => setAlertsEnabled((v) => !v)}
                className="relative w-10 h-5 rounded-full transition-colors"
                style={{
                  background: alertsEnabled ? 'var(--brand)' : 'var(--bg-elevated)',
                  border: '1px solid var(--border-color)',
                }}
              >
                <span
                  className="absolute top-0.5 w-4 h-4 rounded-full transition-all"
                  style={{
                    background: alertsEnabled ? 'var(--brand-contrast)' : 'var(--text-muted)',
                    left: alertsEnabled ? '1.25rem' : '0.125rem',
                  }}
                />
              </button>
            }
          />
        </div>
      </div>
    </>
  )
}
