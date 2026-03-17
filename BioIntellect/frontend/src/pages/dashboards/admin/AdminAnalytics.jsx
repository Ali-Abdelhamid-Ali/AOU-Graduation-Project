import { useEffect, useState } from 'react'
import { useNavigate } from 'react-router-dom'

import { dashboardAPI } from '@/services/api'
import { getApiErrorMessage } from '@/utils/apiErrorUtils'
import {
  ChartPanel,
  ActivityList,
  SectionLoading,
  ErrorBanner,
  formatCapabilityLabel,
} from './SharedPanels'
import styles from '../AdminOperationsDashboard.module.css'

export const AdminAnalytics = () => {
  const navigate = useNavigate()
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')
  const [overview, setOverview] = useState(null)

  useEffect(() => {
    let cancelled = false
    const load = async () => {
      setLoading(true)
      setError('')
      try {
        const response = await dashboardAPI.getAdminOverview()
        if (!cancelled) {
          setOverview(response.data)
          setLoading(false)
        }
      } catch (err) {
        if (!cancelled) {
          setError(getApiErrorMessage(err, 'Failed to load analytics.'))
          setLoading(false)
        }
      }
    }
    load()
    return () => { cancelled = true }
  }, [])

  if (loading) return <SectionLoading />

  return (
    <>
      <ErrorBanner message={error} />

      <section className={styles.heroSection}>
        <div>
          <span className={styles.kicker}>Analytics review</span>
          <h2>Inspect trends without pretending unsupported modules are complete</h2>
          <p>
            This analytics page isolates the chart-backed operational view. When a capability is not
            configured, it remains explicit here instead of being hidden behind decorative visuals.
          </p>
        </div>
        <div className={styles.heroCapabilities}>
          {Object.entries(overview?.capabilities || {}).map(([key, enabled]) => (
            <span
              key={key}
              className={`${styles.badge} ${enabled ? styles.toneSuccess : styles.toneWarning}`}
            >
              {formatCapabilityLabel(key)}: {enabled ? 'available' : 'pending'}
            </span>
          ))}
        </div>
      </section>

      <section className={styles.chartGrid}>
        <ChartPanel title="Daily Appointments Trend" chart={overview?.charts?.daily_appointments_trend} />
        <ChartPanel title="Revenue by Month" chart={overview?.charts?.revenue_by_month} />
        <ChartPanel title="Disease Distribution" chart={overview?.charts?.disease_distribution} />
      </section>

      <section className={styles.splitGrid}>
        <ActivityList
          title="Recent Activity"
          items={overview?.recent_activity}
          emptyMessage="No audit activity has been captured yet."
        />
        <article className={styles.panel}>
          <div className={styles.panelHeading}>
            <div>
              <h3>Quick Actions</h3>
              <p>Navigate to operational areas.</p>
            </div>
          </div>
          <div className={styles.actionGrid}>
            <button type="button" className={styles.actionCard} onClick={() => navigate('/admin-dashboard/users')}>
              <strong>User Management</strong>
              <p>Review and manage all system users.</p>
            </button>
            <button type="button" className={styles.actionCard} onClick={() => navigate('/admin-dashboard/alerts')}>
              <strong>Alerts & Health</strong>
              <p>Check system health and audit warnings.</p>
            </button>
          </div>
        </article>
      </section>
    </>
  )
}

export default AdminAnalytics
