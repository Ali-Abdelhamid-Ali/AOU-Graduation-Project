import { useEffect, useMemo, useState } from 'react'
import { motion } from 'framer-motion'
import { useNavigate } from 'react-router-dom'

import { useAuth } from '@/store/AuthContext'
import { analyticsAPI } from '@/services/api'
import { medicalService } from '@/services/medical.service'
import styles from './PatientDashboard.module.css'

const UNAVAILABLE_VALUE = 'Unavailable'

const formatDateLabel = (value) => {
  if (!value) return UNAVAILABLE_VALUE
  const parsed = new Date(value)
  if (Number.isNaN(parsed.getTime())) return value
  return parsed.toLocaleDateString(undefined, { month: 'short', day: 'numeric' })
}

const formatDateTimeLabel = (date, time) => {
  if (!date) return UNAVAILABLE_VALUE
  const dateLabel = formatDateLabel(date)
  return time ? `${dateLabel} at ${time}` : dateLabel
}

const hasText = (value) => typeof value === 'string' && value.trim().length > 0

const pickFirstText = (...values) =>
  values.find((value) => hasText(value))?.trim() ?? null

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
  const analysisCompleted = Boolean(record.analysis_completed_at)
  const summary =
    type === 'ecg'
      ? pickFirstText(
          record.primary_diagnosis,
          record.rhythm_classification,
          record.ai_interpretation
        ) ||
        (analysisCompleted
          ? 'Analysis completed. A clinical summary is not available yet.'
          : 'Analysis details are not available yet.')
      : pickFirstText(record.ai_interpretation, record.tumor_type) ||
        (analysisCompleted
          ? 'Analysis completed. Detailed findings are not attached yet.'
          : 'Analysis details are not available yet.')

  return {
    id: `${type}-${record.id}`,
    type: type.toUpperCase(),
    date: record.analysis_completed_at || record.created_at,
    status:
      record.is_reviewed
        ? 'Reviewed'
        : analysisCompleted
          ? 'Awaiting review'
          : 'Awaiting analysis',
    summary,
  }
}

const statusClassMap = {
  Reviewed: styles.statusSuccess,
  Scheduled: styles.statusInfo,
  Completed: styles.statusSuccess,
  Cancelled: styles.statusDanger,
  'Needs review': styles.statusWarning,
  'Awaiting review': styles.statusInfo,
  'Awaiting analysis': styles.statusWarning,
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
      availability: {
        stats: false,
        appointments: false,
        results: false,
      },
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
          availability: {
            stats: false,
            appointments: false,
            results: false,
          },
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
          availability: {
            stats:
              statsResult.status === 'fulfilled' && statsResult.value?.success === true,
            appointments:
              appointmentsResult.status === 'fulfilled' &&
              appointmentsResult.value?.success === true,
            results:
              ecgResult.status === 'fulfilled' || mriResult.status === 'fulfilled',
          },
        },
      })
    }

    fetchDashboardData()
  }, [currentUser?.id])

  const dashboardStats = state.data.stats
  const appointments = state.data.appointments
  const results = state.data.results
  const availability = state.data.availability

  const nextAppointment = useMemo(
    () => appointments.find((item) => item.status !== 'Cancelled') || null,
    [appointments]
  )

  const recentAppointments = useMemo(() => appointments.slice(0, 3), [appointments])
  const recentResults = useMemo(() => results.slice(0, 4), [results])

  const statCards = [
    {
      label: 'Health Score',
      value:
        availability.stats && dashboardStats?.health_score !== null && dashboardStats?.health_score !== undefined
          ? dashboardStats.health_score
          : UNAVAILABLE_VALUE,
      helper:
        availability.stats && dashboardStats?.health_score !== null && dashboardStats?.health_score !== undefined
          ? 'Latest consolidated wellness score from your dashboard feed.'
          : 'Health score is unavailable until the analytics feed returns a value.',
    },
    {
      label: 'Total Reports',
      value:
        availability.stats && dashboardStats?.total_reports !== null && dashboardStats?.total_reports !== undefined
          ? dashboardStats.total_reports
          : availability.results
            ? results.length
            : UNAVAILABLE_VALUE,
      helper:
        availability.stats && dashboardStats?.total_reports !== null && dashboardStats?.total_reports !== undefined
          ? 'ECG and MRI reports currently available to you.'
          : availability.results
            ? 'Counted from the result records currently available to your portal.'
            : 'Result totals are temporarily unavailable.',
    },
    {
      label: 'Next Appointment',
      value: nextAppointment
        ? formatDateTimeLabel(nextAppointment.date, nextAppointment.time)
        : availability.appointments
          ? 'No appointment scheduled'
          : UNAVAILABLE_VALUE,
      helper: nextAppointment?.type || 'Appointment timing will appear here when your care team schedules a visit.',
    },
    {
      label: 'Last Analysis',
      value:
        dashboardStats?.last_analysis ||
        recentResults[0]?.status ||
        (availability.results ? 'No results available yet' : UNAVAILABLE_VALUE),
      helper:
        recentResults[0]?.summary ||
        'Your latest clinical interpretation will appear here when it is available.',
    },
  ]

  const quickActions = [
    {
      glyph: 'RS',
      title: 'View My Results',
      description: 'Open your doctor-uploaded ECG and MRI results in a read-only view.',
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

  const trendBars = Array.isArray(dashboardStats?.trends) ? dashboardStats.trends : []

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
            Track your results and appointments from your patient portal. Your care team will upload study outputs and finalized reports here.
          </p>

          <div className={styles.heroActions}>
            <button type="button" className={styles.primaryAction} onClick={() => navigate('/patient-results')}>
              View My Results
            </button>
            <button type="button" className={styles.secondaryAction} onClick={() => navigate('/patient-appointments')}>
              Appointments
            </button>
          </div>
        </div>

        <div className={styles.heroMeta}>
          <div className={styles.heroMetaCard}>
            <span>MRN</span>
            <strong>{currentUser?.mrn || 'MRN not assigned yet'}</strong>
          </div>
          <div className={styles.heroMetaCard}>
            <span>Hospital</span>
            <strong>{currentUser?.hospital_name || 'Hospital unavailable'}</strong>
          </div>
          <div className={styles.heroMetaCard}>
            <span>Latest result</span>
            <strong>
              {recentResults[0]?.type || (availability.results ? 'No results yet' : UNAVAILABLE_VALUE)}
            </strong>
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
              Only live patient routes are exposed here. Staff analysis workspaces are not available in the patient portal.
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
              <p>Your doctor will upload your study results here once they are finalized.</p>
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
              <span>Result delivery</span>
              <strong>Doctor-managed</strong>
              <p>Your doctor will upload your study results here. You can review them in the Results Center once they are ready.</p>
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
