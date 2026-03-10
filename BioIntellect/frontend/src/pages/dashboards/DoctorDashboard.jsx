import { useEffect, useMemo, useState } from 'react'
import { useNavigate } from 'react-router-dom'

import StaffDashboardShell from '@/components/layout/StaffDashboardShell'
import { useAuth } from '@/store/AuthContext'
import { dashboardAPI } from '@/services/api'
import { brandingConfig } from '@/config/brandingConfig'
import styles from './DoctorDashboard.module.css'

const toneClassMap = {
  info: styles.toneInfo,
  success: styles.toneSuccess,
  warning: styles.toneWarning,
  critical: styles.toneCritical,
  normal: styles.toneInfo,
  high: styles.toneWarning,
  urgent: styles.toneCritical,
}

const MetricCard = ({ item }) => (
  <article className={styles.metricCard}>
    <span className={styles.metricLabel}>{item.label}</span>
    <strong className={styles.metricValue}>{item.value}</strong>
    <p className={styles.metricHelper}>{item.helper}</p>
  </article>
)

const EmptyPanel = ({ title, message }) => (
  <div className={styles.emptyPanel}>
    <strong>{title}</strong>
    <p>{message}</p>
  </div>
)

const LoadingDashboard = () => (
  <div className={styles.loadingGrid} data-testid="doctor-dashboard-loading">
    {Array.from({ length: 6 }).map((_, index) => (
      <div key={index} className={`skeleton ${styles.loadingCard}`} />
    ))}
  </div>
)

export const DoctorDashboard = ({ onLogout }) => {
  const navigate = useNavigate()
  const { currentUser } = useAuth()

  const [searchQuery, setSearchQuery] = useState('')
  const [state, setState] = useState({
    loading: true,
    error: '',
    data: null,
  })

  useEffect(() => {
    const loadOverview = async () => {
      setState({ loading: true, error: '', data: null })
      try {
        const response = await dashboardAPI.getDoctorOverview()
        setState({ loading: false, error: '', data: response.data })
      } catch (error) {
        setState({
          loading: false,
          error: error?.detail || error?.message || 'Failed to load doctor overview.',
          data: null,
        })
      }
    }

    loadOverview()
  }, [])

  const overview = state.data
  const normalizedQuery = searchQuery.trim().toLowerCase()

  const filteredQueue = useMemo(() => {
    const items = overview?.patient_queue || []
    if (!normalizedQuery) return items
    return items.filter((item) =>
      [item.patient_name, item.case_number, item.mrn, item.status]
        .filter(Boolean)
        .some((value) => value.toLowerCase().includes(normalizedQuery))
    )
  }, [normalizedQuery, overview?.patient_queue])

  const filteredPatients = useMemo(() => {
    const items = overview?.recent_patients || []
    if (!normalizedQuery) return items
    return items.filter((item) =>
      [item.name, item.mrn]
        .filter(Boolean)
        .some((value) => value.toLowerCase().includes(normalizedQuery))
    )
  }, [normalizedQuery, overview?.recent_patients])

  const filteredResults = useMemo(() => {
    const items = overview?.pending_results || []
    if (!normalizedQuery) return items
    return items.filter((item) =>
      [item.patient_name, item.case_number, item.summary, item.type]
        .filter(Boolean)
        .some((value) => value.toLowerCase().includes(normalizedQuery))
    )
  }, [normalizedQuery, overview?.pending_results])

  const filteredNotifications = useMemo(() => {
    const items = overview?.notifications || []
    if (!normalizedQuery) return items
    return items.filter((item) =>
      [item.title, item.message, item.priority]
        .filter(Boolean)
        .some((value) => value.toLowerCase().includes(normalizedQuery))
    )
  }, [normalizedQuery, overview?.notifications])

  const navSections = useMemo(
    () => [
      {
        title: 'Clinical workflow',
        items: [
          { key: 'overview', label: 'Dashboard', description: 'Today and pending work', glyph: 'D', anchorId: 'doctor-overview' },
          { key: 'patients', label: 'My Patients', description: 'Open patient directory', glyph: 'P', route: '/patient-directory' },
          { key: 'schedule', label: 'Schedule', description: 'Scheduling module pending', glyph: 'S', available: false },
          { key: 'results', label: 'Lab Results', description: 'Review ECG workspace', glyph: 'L', route: '/ecg-analysis' },
        ],
      },
      {
        title: 'Practice tools',
        items: [
          { key: 'messages', label: 'Messages', description: 'Clinical drafting assistant', glyph: 'M', route: '/medical-llm' },
          { key: 'availability', label: 'Availability', description: 'Module pending', glyph: 'A', available: false },
          { key: 'prescriptions', label: 'Prescriptions', description: 'Module pending', glyph: 'Rx', available: false },
        ],
      },
    ],
    []
  )

  const handleNav = (item) => {
    if (item.route) {
      navigate(item.route)
      return
    }
    if (item.anchorId) {
      document.getElementById(item.anchorId)?.scrollIntoView({ behavior: 'smooth', block: 'start' })
    }
  }

  const quickActions = [
    {
      title: 'New Prescription',
      description: 'Prescription workspace is still missing in the production stack.',
      action: null,
    },
    {
      title: 'Write Report',
      description: 'Open the clinical drafting assistant for narrative reporting.',
      action: () => navigate('/medical-llm'),
    },
    {
      title: 'View ECG Results',
      description: 'Jump directly to the ECG analysis and review workspace.',
      action: () => navigate('/ecg-analysis'),
    },
  ]

  const notificationCount = overview?.quick_stats?.unread_messages?.value || 0

  if (state.loading) {
    return (
      <StaffDashboardShell
        currentUser={currentUser}
        roleLabel="Doctor Workspace"
        navSections={navSections}
        activeKey="overview"
        onNavigate={handleNav}
        searchValue={searchQuery}
        onSearchChange={setSearchQuery}
        notificationCount={0}
        onLogout={onLogout}
        headerTitle="Doctor Dashboard"
        headerSubtitle={`Clinical focus board for ${brandingConfig.hospitalName}`}
      >
        <LoadingDashboard />
      </StaffDashboardShell>
    )
  }

  return (
    <StaffDashboardShell
      currentUser={currentUser}
      roleLabel="Doctor Workspace"
      navSections={navSections}
      activeKey="overview"
      onNavigate={handleNav}
      searchValue={searchQuery}
      onSearchChange={setSearchQuery}
      notificationCount={notificationCount}
      onLogout={onLogout}
      headerTitle="Doctor Dashboard"
      headerSubtitle={`Clinical focus board for ${brandingConfig.hospitalName}`}
    >
      {state.error ? (
        <article className={styles.errorBanner}>
          <strong>Unable to load dashboard</strong>
          <p>{state.error}</p>
        </article>
      ) : null}

      <section id="doctor-overview" className={styles.heroSection}>
        <div>
          <span className={styles.kicker}>Care delivery status</span>
          <h2>Prioritize patient flow, unread alerts, and unreviewed results</h2>
          <p>
            This doctor workspace is built from assigned cases, unread notifications, and pending ECG/MRI reviews.
            Appointment scheduling remains disabled until a trusted appointments domain exists.
          </p>
        </div>

        <div className={styles.heroCapabilities}>
          {Object.entries(overview?.capabilities || {}).map(([key, enabled]) => (
            <span
              key={key}
              className={`${styles.badge} ${enabled ? styles.toneSuccess : styles.toneWarning}`}
            >
              {key.replace(/_/g, ' ')}: {enabled ? 'available' : 'pending'}
            </span>
          ))}
        </div>
      </section>

      <section className={styles.metricGrid}>
        {overview?.quick_stats ? Object.values(overview.quick_stats).map((item) => (
          <MetricCard key={item.label} item={item} />
        )) : null}
      </section>

      <section className={styles.splitGrid}>
        <article className={styles.panel}>
          <div className={styles.panelHeading}>
            <div>
              <h3>Today's Schedule</h3>
              <p>Timeline fed only from real appointment data sources.</p>
            </div>
            <span className={`${styles.badge} ${overview?.today_schedule?.available ? styles.toneSuccess : styles.toneWarning}`}>
              {overview?.today_schedule?.available ? 'configured' : 'not configured'}
            </span>
          </div>

          {overview?.today_schedule?.available ? (
            <div className={styles.timelineList}>
              {overview.today_schedule.data.map((item, index) => (
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
              title="Scheduling module not configured"
              message={overview?.today_schedule?.message || 'No trusted appointments source is available.'}
            />
          )}
        </article>

        <article className={styles.panel}>
          <div className={styles.panelHeading}>
            <div>
              <h3>Quick Access</h3>
              <p>Jump into the highest-frequency clinical tasks.</p>
            </div>
          </div>

          <div className={styles.actionGrid}>
            {quickActions.map((item) => (
              <button
                key={item.title}
                type="button"
                className={`${styles.actionCard} ${!item.action ? styles.actionCardDisabled : ''}`}
                onClick={item.action || undefined}
                disabled={!item.action}
              >
                <strong>{item.title}</strong>
                <p>{item.description}</p>
              </button>
            ))}
          </div>
        </article>
      </section>

      <section className={styles.splitGrid}>
        <article className={styles.panel}>
          <div className={styles.panelHeading}>
            <div>
              <h3>Patient Queue</h3>
              <p>Cases in open, in-progress, or pending-review states.</p>
            </div>
          </div>

          {filteredQueue.length ? (
            <div className={styles.queueList}>
              {filteredQueue.map((item) => (
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

        <article className={styles.panel}>
          <div className={styles.panelHeading}>
            <div>
              <h3>Recent Patients</h3>
              <p>Most recent unique patients associated with your current cases.</p>
            </div>
          </div>

          {filteredPatients.length ? (
            <div className={styles.patientList}>
              {filteredPatients.map((item) => (
                <div key={item.id} className={styles.patientCard}>
                  <strong>{item.name}</strong>
                  <span>{item.mrn || 'MRN unavailable'}</span>
                  <p>Last touchpoint: {item.last_visit_label}</p>
                </div>
              ))}
            </div>
          ) : (
            <EmptyPanel title="No patient matches your search" message="Try a different name, MRN, or clear the search field." />
          )}
        </article>
      </section>

      <section className={styles.splitGrid}>
        <article className={styles.panel}>
          <div className={styles.panelHeading}>
            <div>
              <h3>Pending Lab Results</h3>
              <p>Unread ECG and MRI analyses linked to your assigned cases.</p>
            </div>
          </div>

          {filteredResults.length ? (
            <div className={styles.resultList}>
              {filteredResults.map((item) => (
                <div key={item.id} className={styles.resultItem}>
                  <div>
                    <div className={styles.resultHeading}>
                      <strong>{item.patient_name}</strong>
                      <span className={`${styles.badge} ${styles.toneInfo}`}>{item.type}</span>
                    </div>
                    <p>{item.summary}</p>
                  </div>
                  <div className={styles.resultMeta}>
                    <span>{item.case_number || 'No case number'}</span>
                    <span>{item.time_ago}</span>
                  </div>
                </div>
              ))}
            </div>
          ) : (
            <EmptyPanel title="No pending results" message="All linked ECG and MRI results appear to be reviewed." />
          )}
        </article>

        <article className={styles.panel}>
          <div className={styles.panelHeading}>
            <div>
              <h3>Messages & Notifications</h3>
              <p>Unread care-team alerts and operational notices for this doctor account.</p>
            </div>
          </div>

          {filteredNotifications.length ? (
            <div className={styles.notificationList}>
              {filteredNotifications.map((item) => (
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
            <EmptyPanel title="Notification center is quiet" message="No unread or matching notifications were returned." />
          )}
        </article>
      </section>
    </StaffDashboardShell>
  )
}

export default DoctorDashboard
