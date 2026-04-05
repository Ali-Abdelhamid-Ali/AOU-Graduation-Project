import { useEffect, useMemo, useState } from 'react'
import { useNavigate } from 'react-router-dom'

import { dashboardAPI } from '@/services/api'
import { getApiErrorMessage } from '@/utils/apiErrorUtils'
import { MetricCard, EmptyPanel, SectionLoading, ErrorBanner, HeroSection, toneClassMap } from './SharedPanels'
import styles from './DoctorPanels.module.css'

const renderSummaryText = (value) => {
  if (typeof value === 'string') {
    const cleaned = value.trim()
    return cleaned || 'Awaiting radiology review'
  }

  if (value && typeof value === 'object') {
    const name = value.name || value.class_name || 'MRI finding'
    const severity = value.severity ? `severity ${value.severity}` : null
    const percentage = value.percentage != null ? `${Number(value.percentage).toFixed(1)}% of study` : null
    const volume = value.volume_cm3 != null ? `${Number(value.volume_cm3).toFixed(2)} cm3` : null

    return [name, severity, percentage, volume].filter(Boolean).join(' • ')
  }

  return 'Awaiting radiology review'
}

export const DoctorOverview = () => {
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
        const response = await dashboardAPI.getDoctorOverview()
        if (!cancelled) { setOverview(response.data); setLoading(false) }
      } catch (err) {
        if (!cancelled) { setError(getApiErrorMessage(err, 'Failed to load doctor overview.')); setLoading(false) }
      }
    }
    load()
    return () => { cancelled = true }
  }, [])

  const quickActions = useMemo(
    () => [
      { title: 'Open ECG Workspace', description: 'Shared intake for ECG studies.', action: () => navigate('/ecg-analysis') },
      { title: 'Open MRI Workspace', description: 'Shared intake for MRI studies.', action: () => navigate('/mri-analysis') },
    ],
    [navigate]
  )

  const recentPatientsPreview = useMemo(
    () => (overview?.recent_patients || []).slice(0, 5),
    [overview?.recent_patients]
  )

  if (loading) return <SectionLoading />

  return (
    <>
      <ErrorBanner message={error} />

      <HeroSection
        kicker="Care delivery status"
        heading="Prioritize queue pressure, unread alerts, and shared diagnostic intake"
        body="This workspace is built from assigned cases, unread notifications, and pending ECG or MRI results."
        capabilities={overview?.capabilities}
      />

      <section className={styles.metricGrid}>
        {overview?.quick_stats ? Object.values(overview.quick_stats).map((item) => (
          <MetricCard key={item.label} item={item} />
        )) : null}
      </section>

      <section className={styles.splitGrid}>
        {/* Quick Access */}
        <article className={styles.panel}>
          <div className={styles.panelHeading}>
            <div><h3>Quick Access</h3><p>Jump into the highest-frequency clinical tasks.</p></div>
          </div>
          <div className={styles.actionGrid}>
            {quickActions.map((item) => (
              <button key={item.title} type="button" className={styles.actionCard} onClick={item.action}>
                <strong>{item.title}</strong>
                <p>{item.description}</p>
              </button>
            ))}
          </div>
        </article>
      </section>

      <section className={styles.splitGrid}>
        {/* Recent Patients Preview */}
        <article className={styles.panel}>
          <div className={styles.panelHeading}>
            <div><h3>Recent Patients</h3><p>Most recent patients associated with your active cases.</p></div>
          </div>
          {recentPatientsPreview.length ? (
            <div className={styles.patientList}>
              {recentPatientsPreview.map((item) => (
                <div key={item.id} className={styles.patientCard}>
                  <strong>{item.name}</strong>
                  <span>{item.mrn || 'MRN unavailable'}</span>
                  <p>Last touchpoint: {item.last_visit_label}</p>
                </div>
              ))}
            </div>
          ) : (
            <EmptyPanel title="No recent patients" message="Patient data will appear when cases are assigned." />
          )}
        </article>
      </section>

      <section className={styles.splitGrid}>
        {/* Pending Results Preview */}
        <article className={styles.panel}>
          <div className={styles.panelHeading}>
            <div><h3>Pending Results</h3><p>Unread ECG and MRI analyses linked to your cases.</p></div>
          </div>
          {overview?.pending_results?.length ? (
            <div className={styles.resultList}>
              {overview.pending_results.slice(0, 5).map((item) => (
                <div key={item.id} className={styles.resultItem}>
                  <div>
                    <div className={styles.resultHeading}>
                      <strong>{item.patient_name}</strong>
                      <span className={`${styles.badge} ${styles.toneInfo}`}>{item.type}</span>
                    </div>
                    <p>{renderSummaryText(item.summary)}</p>
                  </div>
                  <div className={styles.resultMeta}>
                    <span>{item.case_number || 'No case number'}</span>
                    <span>{item.time_ago}</span>
                  </div>
                </div>
              ))}
            </div>
          ) : (
            <EmptyPanel title="No pending results" message="All linked results appear to be reviewed." />
          )}
        </article>

        {/* Notifications Preview */}
        <article className={styles.panel}>
          <div className={styles.panelHeading}>
            <div><h3>Workflow Alerts</h3><p>Unread operational alerts and case notices.</p></div>
          </div>
          {overview?.notifications?.length ? (
            <div className={styles.notificationList}>
              {overview.notifications.slice(0, 5).map((item) => (
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
            <EmptyPanel title="Alert center is quiet" message="No unread alerts." />
          )}
        </article>
      </section>
    </>
  )
}

export default DoctorOverview

