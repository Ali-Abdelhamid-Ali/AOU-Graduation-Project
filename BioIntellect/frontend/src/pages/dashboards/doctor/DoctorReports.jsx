import { useEffect, useState } from 'react'
import { useNavigate } from 'react-router-dom'

import { dashboardAPI } from '@/services/api'
import { getApiErrorMessage } from '@/utils/apiErrorUtils'
import { MetricCard, SectionLoading, ErrorBanner, HeroSection } from './SharedPanels'
import styles from '../DoctorDashboard.module.css'

export const DoctorReports = () => {
  const navigate = useNavigate()
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')
  const [quickStats, setQuickStats] = useState(null)

  useEffect(() => {
    let cancelled = false
    const load = async () => {
      setLoading(true); setError('')
      try {
        const response = await dashboardAPI.getDoctorOverview()
        if (!cancelled) { setQuickStats(response.data?.quick_stats || null); setLoading(false) }
      } catch (err) {
        if (!cancelled) { setError(getApiErrorMessage(err, 'Failed to load reports data.')); setLoading(false) }
      }
    }
    load()
    return () => { cancelled = true }
  }, [])

  if (loading) return <SectionLoading />

  return (
    <>
      <ErrorBanner message={error} />
      <HeroSection
        kicker="Report composer"
        heading="Draft narrative outputs only after reviewing the source result"
        body="This page keeps report drafting grounded in the live pending-results list."
      />
      <section className={styles.metricGrid}>
        {quickStats?.pending_reports ? <MetricCard item={quickStats.pending_reports} /> : null}
        {quickStats?.unread_messages ? <MetricCard item={quickStats.unread_messages} /> : null}
        {quickStats?.total_patients ? <MetricCard item={quickStats.total_patients} /> : null}
      </section>
      <section className={styles.splitGrid}>
        <article className={styles.panel}>
          <div className={styles.panelHeading}><div><h3>Drafting Actions</h3><p>Open the clinical assistant from a dedicated report-focused page.</p></div></div>
          <div className={styles.actionGrid}>
            <button type="button" className={styles.actionCard} onClick={() => navigate('/medical-llm')}>
              <strong>Launch Clinical Assistant</strong><p>Open the narrative drafting assistant.</p>
            </button>
            <button type="button" className={styles.actionCard} onClick={() => navigate('/doctor-dashboard/results')}>
              <strong>Review Source Results</strong><p>Go back to structured ECG and MRI outputs.</p>
            </button>
            <button type="button" className={styles.actionCard} onClick={() => navigate('/patient-directory')}>
              <strong>Open Patient Registry</strong><p>Cross-check patient details.</p>
            </button>
          </div>
        </article>
      </section>
    </>
  )
}

export default DoctorReports
