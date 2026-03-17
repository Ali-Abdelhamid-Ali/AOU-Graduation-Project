import { useEffect, useMemo, useState } from 'react'
import { useNavigate } from 'react-router-dom'

import { dashboardAPI } from '@/services/api'
import { getApiErrorMessage } from '@/utils/apiErrorUtils'
import { EmptyPanel, SectionLoading, ErrorBanner, HeroSection, toneClassMap } from './SharedPanels'
import styles from '../DoctorDashboard.module.css'

export const DoctorMessages = () => {
  const navigate = useNavigate()
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')
  const [notifications, setNotifications] = useState([])
  const [searchQuery, setSearchQuery] = useState('')

  useEffect(() => {
    let cancelled = false
    const load = async () => {
      setLoading(true); setError('')
      try {
        const response = await dashboardAPI.getDoctorOverview()
        if (!cancelled) { setNotifications(response.data?.notifications || []); setLoading(false) }
      } catch (err) {
        if (!cancelled) { setError(getApiErrorMessage(err, 'Failed to load messages.')); setLoading(false) }
      }
    }
    load()
    return () => { cancelled = true }
  }, [])

  const filtered = useMemo(() => {
    const q = searchQuery.trim().toLowerCase()
    if (!q) return notifications
    return notifications.filter((item) =>
      [item.title, item.message, item.priority]
        .filter(Boolean).some((v) => v.toLowerCase().includes(q))
    )
  }, [notifications, searchQuery])

  if (loading) return <SectionLoading />

  return (
    <>
      <ErrorBanner message={error} />
      <HeroSection
        kicker="Messages center"
        heading="See which alerts need a reply and which only need review"
        body="This center stays grounded in the real unread notification feed."
      />
      <article className={styles.panel}>
        <div className={styles.panelHeading}>
          <div><h3>Messages & Notifications</h3><p>Unread care-team alerts and operational notices.</p></div>
        </div>
        <div style={{ padding: '0 1.5rem 1rem' }}>
          <input
            type="search"
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            placeholder="Filter messages..."
            style={{ width: '100%', padding: '0.5rem 0.75rem', borderRadius: '6px', border: '1px solid var(--color-border, #333)', background: 'var(--color-surface, #1a1a2e)', color: 'inherit', fontSize: '0.875rem' }}
          />
        </div>
        {filtered.length ? (
          <div className={styles.notificationList}>
            {filtered.map((item) => (
              <div key={item.id} className={styles.notificationItem}>
                <div>
                  <strong>{item.title}</strong>
                  <p>{item.message}</p>
                </div>
                <div className={styles.queueMeta}>
                  <span className={`${styles.badge} ${toneClassMap[item.priority] || styles.toneInfo}`}>{item.priority}</span>
                  <span>{item.time_ago}</span>
                </div>
              </div>
            ))}
          </div>
        ) : (
          <EmptyPanel title="Notification center is quiet" message="No unread or matching notifications." />
        )}
      </article>
      <section className={styles.splitGrid}>
        <article className={styles.panel}>
          <div className={styles.panelHeading}><div><h3>Reply Paths</h3><p>Move from alerts into the right production route.</p></div></div>
          <div className={styles.actionGrid}>
            <button type="button" className={styles.actionCard} onClick={() => navigate('/doctor-dashboard/results')}>
              <strong>Open Results Inbox</strong><p>Useful when the message is driven by a new ECG or MRI upload.</p>
            </button>
            <button type="button" className={styles.actionCard} onClick={() => navigate('/medical-llm')}>
              <strong>Open Assistant</strong><p>Use the assistant for drafting communication text.</p>
            </button>
          </div>
        </article>
      </section>
    </>
  )
}

export default DoctorMessages
