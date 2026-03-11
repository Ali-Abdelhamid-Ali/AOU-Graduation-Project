import { useEffect, useMemo, useState } from 'react'
import { motion } from 'framer-motion'
import { useNavigate } from 'react-router-dom'

import { useAuth } from '@/store/AuthContext'
import { analyticsAPI } from '@/services/api'
import { medicalService } from '@/services/medical.service'
import styles from './PatientDashboard.module.css'

const formatDateLabel = (value) => {
  if (!value) return 'Pending'
  const parsed = new Date(value)
  if (Number.isNaN(parsed.getTime())) return value
  return parsed.toLocaleDateString(undefined, { month: 'short', day: 'numeric' })
}

const formatDateTimeLabel = (date, time) => {
  if (!date) return 'Not scheduled'
  const dateLabel = formatDateLabel(date)
  return time ? `${dateLabel} at ${time}` : dateLabel
}

const normalizeStatus = (value) => {
  const text = String(value || 'Scheduled')
    .replace(/_/g, ' ')
    .trim()
  return text
    ? text.replace(/\w\S*/g, (part) => part[0].toUpperCase() + part.slice(1).toLowerCase())
    : 'Scheduled'
}

const normalizeAppointment = (appointment = {}) => ({
  id: appointment.id,
  doctor: appointment.doctors
    ? `Dr. ${appointment.doctors.first_name} ${appointment.doctors.last_name}`
    : 'Clinical Staff',
  specialty: appointment.doctors?.specialty || 'Medical Specialist',
  date: appointment.appointment_date,
  time: appointment.appointment_time,
  status: normalizeStatus(appointment.status),
  type: appointment.appointment_type || 'Follow-up',
})

const normalizeResult = (type, record = {}) => {
  const hasTumorFlag = record.tumor_detected === true || record.tumor_detected === 'true'

  return {
    id: `${type}-${record.id}`,
    type: type.toUpperCase(),
    date: record.analysis_completed_at || record.created_at,
    status:
      type === 'ecg'
        ? (record.confidence_score ?? 0) > 0.8
          ? 'Normal'
          : 'Needs review'
        : hasTumorFlag
          ? 'Attention'
          : 'Normal',
    summary:
      type === 'ecg'
        ? record.primary_diagnosis || 'Automated ECG interpretation completed.'
        : hasTumorFlag
          ? `Possible finding: ${record.tumor_type || 'Further clinical review needed'}`
          : 'No abnormal MRI growth pattern detected.',
  }
}

const statusClassMap = {
  Normal: styles.statusSuccess,
  Scheduled: styles.statusInfo,
  Completed: styles.statusSuccess,
  Cancelled: styles.statusDanger,
  Attention: styles.statusDanger,
  'Needs review': styles.statusWarning,
}

const LoadingDashboard = () => (
  <div className={styles.loadingGrid}>
    {Array.from({ length: 6 }).map((_, index) => (
      <div key={index} className={`skeleton ${styles.loadingCard}`} />
    ))}
  </div>
)

export const PatientDashboard = () => {
  const { currentUser } = useAuth()
  const navigate = useNavigate()
  const [state, setState] = useState({
    loading: true,
    error: '',
    data: {
      stats: null,
      appointments: [],
      results: [],
    },
  })

  useEffect(() => {
    const fetchDashboardData = async () => {
      if (!currentUser?.id) {
        setState((previous) => ({ ...previous, loading: false }))
        return
      }

      setState({
        loading: true,
        error: '',
        data: {
          stats: null,
          appointments: [],
          results: [],
        },
      })

      const [statsResult, appointmentsResult, ecgResult, mriResult] = await Promise.allSettled([
        analyticsAPI.getDashboardStats(),
        analyticsAPI.getAppointments(),
        medicalService.getEcgResults(currentUser.id),
        medicalService.getMriResults(currentUser.id),
      ])

      const failures = []

      const stats =
        statsResult.status === 'fulfilled' && statsResult.value?.success
          ? statsResult.value.data
          : (failures.push('stats'), null)

      const appointments =
        appointmentsResult.status === 'fulfilled' && appointmentsResult.value?.success
          ? (appointmentsResult.value.data || [])
              .map(normalizeAppointment)
              .sort((left, right) => new Date(left.date).getTime() - new Date(right.date).getTime())
          : (failures.push('appointments'), [])

      const ecgResults =
        ecgResult.status === 'fulfilled'
          ? ecgResult.value.map((item) => normalizeResult('ecg', item))
          : (failures.push('ecg'), [])

      const mriResults =
        mriResult.status === 'fulfilled'
          ? mriResult.value.map((item) => normalizeResult('mri', item))
          : (failures.push('mri'), [])

      const results = [...ecgResults, ...mriResults].sort(
        (left, right) => new Date(right.date).getTime() - new Date(left.date).getTime()
      )

      setState({
        loading: false,
        error:
          failures.length === 4
            ? 'Unable to load your dashboard right now.'
            : failures.length
              ? 'Some dashboard panels are temporarily unavailable.'
              : '',
        data: {
          stats,
          appointments,
          results,
        },
      })
    }

    fetchDashboardData()
  }, [currentUser?.id])

  const dashboardStats = state.data.stats || {}
  const appointments = state.data.appointments
  const results = state.data.results

  const nextAppointment = useMemo(
    () => appointments.find((item) => item.status !== 'Cancelled') || null,
    [appointments]
  )

  const recentAppointments = useMemo(() => appointments.slice(0, 3), [appointments])
  const recentResults = useMemo(() => results.slice(0, 4), [results])

  const statCards = [
    {
      label: 'Health Score',
      value: dashboardStats.health_score ?? 100,
      helper: 'Latest consolidated wellness score from your dashboard feed.',
    },
    {
      label: 'Total Reports',
      value: dashboardStats.total_reports ?? results.length,
      helper: 'ECG and MRI reports currently available to you.',
    },
    {
      label: 'Next Appointment',
      value: nextAppointment ? formatDateTimeLabel(nextAppointment.date, nextAppointment.time) : dashboardStats.next_appointment || 'Not scheduled',
      helper: nextAppointment?.type || 'Book when your care team opens scheduling.',
    },
    {
      label: 'Last Analysis',
      value: dashboardStats.last_analysis || recentResults[0]?.status || 'No recent analysis',
      helper: recentResults[0]?.summary || 'Your latest clinical interpretation will appear here.',
    },
  ]

  const quickActions = [
    {
      glyph: 'EC',
      title: 'Upload ECG Study',
      description: 'You can upload ECG signals directly and review the resulting interpretation.',
      path: '/ecg-analysis',
    },
    {
      glyph: 'MR',
      title: 'Upload MRI Study',
      description: 'You can upload MRI scans directly for segmentation and follow-up review.',
      path: '/mri-analysis',
    },
    {
      glyph: 'RS',
      title: 'Results Center',
      description: 'Open your combined ECG and MRI results history.',
      path: '/patient-results',
    },
    {
      glyph: 'AP',
      title: 'Appointments',
      description: 'Review upcoming consultations and recent visits.',
      path: '/patient-appointments',
    },
    {
      glyph: 'PR',
      title: 'Profile Settings',
      description: 'Update demographics, history, and contact information.',
      path: '/patient-profile',
    },
    {
      glyph: 'SC',
      title: 'Security Center',
      description: 'Manage password strength and active sessions.',
      path: '/patient-security',
    },
  ]

  const trendBars = dashboardStats.trends || []

  if (state.loading) {
    return <LoadingDashboard />
  }

  return (
    <motion.div
      className={styles.container}
      initial={{ opacity: 0, y: 16 }}
      animate={{ opacity: 1, y: 0 }}
    >
      {state.error ? (
        <article className={styles.errorBanner}>
          <strong>Dashboard data is partially unavailable</strong>
          <p>{state.error}</p>
        </article>
      ) : null}

      <section className={styles.hero}>
        <div className={styles.heroContent}>
          <span className={styles.heroKicker}>Patient overview</span>
          <h1 className={styles.heroTitle}>
            Welcome back, <span className={styles.highlight}>{currentUser?.first_name || 'Patient'}</span>
          </h1>
          <p className={styles.heroSubtitle}>
            Track your results, prepare for appointments, and upload ECG or MRI studies directly from your own portal.
          </p>

          <div className={styles.heroActions}>
            <button type="button" className={styles.primaryAction} onClick={() => navigate('/ecg-analysis')}>
              Upload ECG
            </button>
            <button type="button" className={styles.primaryAction} onClick={() => navigate('/mri-analysis')}>
              Upload MRI
            </button>
            <button type="button" className={styles.secondaryAction} onClick={() => navigate('/patient-results')}>
              View Results
            </button>
          </div>
        </div>

        <div className={styles.heroMeta}>
          <div className={styles.heroMetaCard}>
            <span>MRN</span>
            <strong>{currentUser?.mrn || 'Pending assignment'}</strong>
          </div>
          <div className={styles.heroMetaCard}>
            <span>Hospital</span>
            <strong>{currentUser?.hospital_name || 'BioIntellect Medical Center'}</strong>
          </div>
          <div className={styles.heroMetaCard}>
            <span>Latest result</span>
            <strong>{recentResults[0]?.type || 'No recent result'}</strong>
          </div>
        </div>
      </section>

      <section className={styles.statsGrid}>
        {statCards.map((item) => (
          <article key={item.label} className={styles.statCard}>
            <span className={styles.statLabel}>{item.label}</span>
            <strong className={styles.statValue}>{item.value}</strong>
            <p className={styles.statHelper}>{item.helper}</p>
          </article>
        ))}
      </section>

      <section className={styles.section}>
        <div className={styles.sectionHeading}>
          <div>
            <h2 className={styles.sectionTitle}>Quick Access</h2>
            <p className={styles.sectionSubtitle}>
              Only routes that already exist in your real patient portal are exposed here.
            </p>
          </div>
        </div>

        <div className={styles.actionGrid}>
          {quickActions.map((item) => (
            <button
              key={item.title}
              type="button"
              className={styles.actionCard}
              onClick={() => navigate(item.path)}
            >
              <span className={styles.actionGlyph}>{item.glyph}</span>
              <div className={styles.actionInfo}>
                <strong>{item.title}</strong>
                <p>{item.description}</p>
              </div>
            </button>
          ))}
        </div>
      </section>

      <section className={styles.splitGrid}>
        <article className={styles.listCard}>
          <div className={styles.sectionHeading}>
            <div>
              <h2 className={styles.sectionTitle}>Upcoming Appointments</h2>
              <p className={styles.sectionSubtitle}>Your nearest consultations and visit context.</p>
            </div>
          </div>

          {recentAppointments.length ? (
            <div className={styles.list}>
              {recentAppointments.map((item) => (
                <div key={item.id} className={styles.listItem}>
                  <div>
                    <strong>{item.doctor}</strong>
                    <p>{item.specialty}</p>
                  </div>
                  <div className={styles.listMeta}>
                    <span>{formatDateTimeLabel(item.date, item.time)}</span>
                    <span className={`${styles.statusBadge} ${statusClassMap[item.status] || styles.statusInfo}`}>
                      {item.status}
                    </span>
                  </div>
                </div>
              ))}
            </div>
          ) : (
            <div className={styles.emptyState}>
              <strong>No appointments yet</strong>
              <p>Your booked consultations will appear here once scheduling data is available.</p>
            </div>
          )}
        </article>

        <article className={styles.listCard}>
          <div className={styles.sectionHeading}>
            <div>
              <h2 className={styles.sectionTitle}>Recent Results</h2>
              <p className={styles.sectionSubtitle}>Combined ECG and MRI outcomes from your account.</p>
            </div>
          </div>

          {recentResults.length ? (
            <div className={styles.list}>
              {recentResults.map((item) => (
                <div key={item.id} className={styles.listItem}>
                  <div>
                    <strong>{item.type} Study</strong>
                    <p>{item.summary}</p>
                  </div>
                  <div className={styles.listMeta}>
                    <span>{formatDateLabel(item.date)}</span>
                    <span className={`${styles.statusBadge} ${statusClassMap[item.status] || styles.statusInfo}`}>
                      {item.status}
                    </span>
                  </div>
                </div>
              ))}
            </div>
          ) : (
            <div className={styles.emptyState}>
              <strong>No results yet</strong>
              <p>Your uploaded studies and processed reports will show up here.</p>
            </div>
          )}
        </article>
      </section>

      <section className={styles.splitGrid}>
        <article className={styles.listCard}>
          <div className={styles.sectionHeading}>
            <div>
              <h2 className={styles.sectionTitle}>Portal Readiness</h2>
              <p className={styles.sectionSubtitle}>Keep the essentials complete so care teams can act faster.</p>
            </div>
          </div>

          <div className={styles.readinessGrid}>
            <div className={styles.readinessCard}>
              <span>Profile data</span>
              <strong>{currentUser?.phone && currentUser?.address ? 'Complete' : 'Needs review'}</strong>
              <p>Contact details and address help with secure communication and follow-up.</p>
            </div>
            <div className={styles.readinessCard}>
              <span>Security posture</span>
              <strong>Managed in portal</strong>
              <p>Password and session controls are available in your security settings page.</p>
            </div>
            <div className={styles.readinessCard}>
              <span>Diagnostic access</span>
              <strong>ECG and MRI enabled</strong>
              <p>You can upload both study types yourself without waiting for a doctor-only entry point.</p>
            </div>
          </div>
        </article>

        <article className={styles.listCard}>
          <div className={styles.sectionHeading}>
            <div>
              <h2 className={styles.sectionTitle}>Health Trend Snapshot</h2>
              <p className={styles.sectionSubtitle}>Recent scoring pattern from your analytics feed.</p>
            </div>
          </div>

          {trendBars.length ? (
            <div className={styles.trendChart}>
              {trendBars.map((item, index) => (
                <div key={`${item.date || 'trend'}-${index}`} className={styles.trendColumn}>
                  <span className={styles.trendValue}>{item.score}%</span>
                  <div className={styles.trendTrack}>
                    <span className={styles.trendBar} style={{ height: `${Math.max(item.score, 12)}%` }} />
                  </div>
                  <span className={styles.trendLabel}>{formatDateLabel(item.date)}</span>
                </div>
              ))}
            </div>
          ) : (
            <div className={styles.emptyState}>
              <strong>No trend data yet</strong>
              <p>Trend bars will appear when analytics snapshots become available for your account.</p>
            </div>
          )}
        </article>
      </section>
    </motion.div>
  )
}
