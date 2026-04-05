import { useEffect, useState } from 'react'

import { ROLES } from '@/config/roles'
import { dashboardAPI } from '@/services/api'
import { useAuth } from '@/store/AuthContext'
import { getApiErrorMessage } from '@/utils/apiErrorUtils'
import {
  ActivityList,
  EmptyPanel,
  SectionLoading,
  ErrorBanner,
  toneClassMap,
} from './SharedPanels'
import styles from './AdminPanels.module.css'

export const AdminAlerts = () => {
  const { currentUser } = useAuth()
  const isSuperAdmin = currentUser?.user_role === ROLES.SUPER_ADMIN

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
          setError(getApiErrorMessage(err, 'Failed to load alerts.'))
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
          <span className={styles.kicker}>Alert management</span>
          <h2>Separate urgent signals from general admin browsing</h2>
          <p>
            The alerts page gives audit warnings and runtime health a dedicated surface, so
            operational users can triage incidents without scanning the full dashboard.
          </p>
        </div>
      </section>

      <section className={styles.splitGrid}>
        <article className={styles.panel}>
          <div className={styles.panelHeading}>
            <div>
              <h3>Alerts</h3>
              <p>Flagged audit signals, performance warnings, and urgent notifications.</p>
            </div>
          </div>
          {overview?.alerts?.length ? (
            <div className={styles.alertList}>
              {overview.alerts.map((alert) => (
                <div key={alert.id} className={styles.alertItem}>
                  <span className={`${styles.badge} ${toneClassMap[alert.severity] || styles.toneWarning}`}>
                    {alert.severity}
                  </span>
                  <div>
                    <strong>{alert.title}</strong>
                    <p>{alert.message}</p>
                  </div>
                  <span className={styles.feedTime}>
                    {alert.timestamp ? new Date(alert.timestamp).toLocaleString() : 'No timestamp'}
                  </span>
                </div>
              ))}
            </div>
          ) : (
            <EmptyPanel title="No active alerts" message="System thresholds are currently within healthy bounds." />
          )}
        </article>

        <article className={styles.panel}>
          <div className={styles.panelHeading}>
            <div>
              <h3>System Health</h3>
              <p>{overview?.system_health?.summary}</p>
            </div>
            <span className={`${styles.badge} ${toneClassMap[overview?.system_health?.status] || styles.toneInfo}`}>
              {overview?.system_health?.status || 'unknown'}
            </span>
          </div>
          <div className={styles.healthGrid}>
            {overview?.system_health?.metrics?.map((metric) => (
              <div key={metric.label} className={styles.healthMetric}>
                <span>{metric.label}</span>
                <strong>{metric.value}</strong>
                <span className={`${styles.badge} ${toneClassMap[metric.tone] || styles.toneInfo}`}>{metric.tone}</span>
              </div>
            ))}
          </div>
        </article>
      </section>

      <section className={styles.splitGrid}>
        <ActivityList
          title="Recent Activity"
          items={overview?.recent_activity}
          emptyMessage="No recent operational activity is available."
        />
        <article className={styles.panel}>
          <div className={styles.panelHeading}>
            <div>
              <h3>Role Coverage</h3>
              <p>This summary reflects what this signed-in role can responsibly act on.</p>
            </div>
          </div>
          <div className={styles.healthGrid}>
            <div className={styles.healthMetric}>
              <span>Access Scope</span>
              <strong>{isSuperAdmin ? 'System-wide governance' : 'Facility administration'}</strong>
              <span className={`${styles.badge} ${styles.toneInfo}`}>info</span>
            </div>
          </div>
        </article>
      </section>
    </>
  )
}

export default AdminAlerts

