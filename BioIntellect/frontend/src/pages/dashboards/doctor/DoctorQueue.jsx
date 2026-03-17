import { useEffect, useMemo, useState } from 'react'

import { dashboardAPI } from '@/services/api'
import { getApiErrorMessage } from '@/utils/apiErrorUtils'
import { EmptyPanel, SectionLoading, ErrorBanner, HeroSection, toneClassMap } from './SharedPanels'
import styles from '../DoctorDashboard.module.css'

export const DoctorQueue = () => {
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')
  const [queue, setQueue] = useState([])
  const [searchQuery, setSearchQuery] = useState('')

  useEffect(() => {
    let cancelled = false
    const load = async () => {
      setLoading(true); setError('')
      try {
        const response = await dashboardAPI.getDoctorOverview()
        if (!cancelled) { setQueue(response.data?.patient_queue || []); setLoading(false) }
      } catch (err) {
        if (!cancelled) { setError(getApiErrorMessage(err, 'Failed to load queue.')); setLoading(false) }
      }
    }
    load()
    return () => { cancelled = true }
  }, [])

  const filtered = useMemo(() => {
    const q = searchQuery.trim().toLowerCase()
    if (!q) return queue
    return queue.filter((item) =>
      [item.patient_name, item.case_number, item.mrn, item.status]
        .filter(Boolean).some((v) => v.toLowerCase().includes(q))
    )
  }, [queue, searchQuery])

  if (loading) return <SectionLoading />

  return (
    <>
      <ErrorBanner message={error} />
      <HeroSection
        kicker="Queue pressure"
        heading="Sort urgent cases, open reviews, and waiting patients faster"
        body="The queue page gives the waiting list its own surface."
      />
      <article className={styles.panel}>
        <div className={styles.panelHeading}>
          <div><h3>Patient Queue</h3><p>Cases in open, in-progress, or pending-review states.</p></div>
        </div>
        <div style={{ padding: '0 1.5rem 1rem' }}>
          <input
            type="search"
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            placeholder="Filter queue by patient name, case number..."
            style={{ width: '100%', padding: '0.5rem 0.75rem', borderRadius: '6px', border: '1px solid var(--color-border, #333)', background: 'var(--color-surface, #1a1a2e)', color: 'inherit', fontSize: '0.875rem' }}
          />
        </div>
        {filtered.length ? (
          <div className={styles.queueList}>
            {filtered.map((item) => (
              <div key={item.id} className={styles.queueItem}>
                <div>
                  <strong>{item.patient_name}</strong>
                  <p>{item.case_number || 'Case number unavailable'}</p>
                </div>
                <div className={styles.queueMeta}>
                  <span className={`${styles.badge} ${toneClassMap[item.priority] || styles.toneInfo}`}>{item.priority}</span>
                  <span>{item.wait_time_label}</span>
                </div>
              </div>
            ))}
          </div>
        ) : (
          <EmptyPanel title="Queue is clear" message="No cases currently match the active queue statuses." />
        )}
      </article>
    </>
  )
}

export default DoctorQueue
