import { useEffect, useState } from 'react'
import { useNavigate } from 'react-router-dom'

import { dashboardAPI } from '@/services/api'
import { getApiErrorMessage } from '@/utils/apiErrorUtils'
import { EmptyPanel, SectionLoading, ErrorBanner, HeroSection } from './SharedPanels'
import styles from '../DoctorDashboard.module.css'

export const DoctorSchedule = () => {
  const navigate = useNavigate()
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')
  const [data, setData] = useState(null)

  useEffect(() => {
    let cancelled = false
    const load = async () => {
      setLoading(true); setError('')
      try {
        const response = await dashboardAPI.getDoctorOverview()
        if (!cancelled) { setData(response.data); setLoading(false) }
      } catch (err) {
        if (!cancelled) { setError(getApiErrorMessage(err, 'Failed to load schedule.')); setLoading(false) }
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
        kicker="Schedule board"
        heading="See clinic rhythm without mixing in fake appointments"
        body="This page isolates the real appointment timeline. If the scheduling source is not configured, the page stays explicit about that gap."
      />
      <article className={styles.panel}>
        <div className={styles.panelHeading}>
          <div><h3>Today's Schedule</h3><p>Timeline fed only from real appointment data sources.</p></div>
          <span className={`${styles.badge} ${data?.today_schedule?.available ? styles.toneSuccess : styles.toneWarning}`}>
            {data?.today_schedule?.available ? 'configured' : 'not configured'}
          </span>
        </div>
        {data?.today_schedule?.available && data?.today_schedule?.data?.length ? (
          <div className={styles.timelineList}>
            {data.today_schedule.data.map((item, index) => (
              <div key={item.id || index} className={styles.timelineItem}>
                <span className={styles.timelineTime}>{item.time || item.start_time || 'Scheduled'}</span>
                <div>
                  <strong>{item.patient_name || item.title || 'Appointment'}</strong>
                  <p>{item.reason || item.status || 'Clinical appointment'}</p>
                </div>
              </div>
            ))}
          </div>
        ) : (
          <EmptyPanel
            title={data?.today_schedule?.available ? 'No appointments scheduled' : 'Scheduling module not configured'}
            message={data?.today_schedule?.message || 'No trusted appointments source is available.'}
          />
        )}
      </article>
      <section className={styles.splitGrid}>
        <article className={styles.panel}>
          <div className={styles.panelHeading}><div><h3>Schedule Actions</h3><p>Navigate from schedule into other workflows.</p></div></div>
          <div className={styles.actionGrid}>
            <button type="button" className={styles.actionCard} onClick={() => navigate('/doctor-dashboard/queue')}>
              <strong>Open Queue</strong><p>Review waiting patients.</p>
            </button>
            <button type="button" className={styles.actionCard} onClick={() => navigate('/doctor-dashboard/results')}>
              <strong>Results Inbox</strong><p>Review pending ECG/MRI results.</p>
            </button>
          </div>
        </article>
      </section>
    </>
  )
}

export default DoctorSchedule
