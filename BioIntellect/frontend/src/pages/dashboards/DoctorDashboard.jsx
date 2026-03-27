import { useEffect, useMemo, useState } from 'react'
import { useLocation, useNavigate } from 'react-router-dom'

import StaffDashboardShell from '@/components/layout/StaffDashboardShell'
import { brandingConfig } from '@/config/brandingConfig'
import { dashboardAPI } from '@/services/api'
import { useAuth } from '@/store/AuthContext'
import { getApiErrorMessage } from '@/utils/apiErrorUtils'
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

const doctorViewConfig = {
  overview: {
    key: 'overview',
    title: 'Doctor Dashboard',
    subtitle: `Clinical focus board for ${brandingConfig.hospitalName}`,
  },
  patients: {
    key: 'patients',
    title: 'My Patients',
    subtitle: 'Assigned patients, recent touchpoints, and directory access.',
  },
  results: {
    key: 'results',
    title: 'Results Inbox',
    subtitle: 'Unread ECG and MRI analyses linked to your current cases.',
  },
  messages: {
    key: 'messages',
    title: 'Messages Center',
    subtitle: 'Unread care-team alerts, patient updates, and workflow notices.',
  },
}

const getDoctorView = (pathname = '') => {
  if (pathname.startsWith('/doctor-dashboard/patients')) return doctorViewConfig.patients
  if (pathname.startsWith('/doctor-dashboard/results')) return doctorViewConfig.results
  if (pathname.startsWith('/doctor-dashboard/messages')) return doctorViewConfig.messages
  return doctorViewConfig.overview
}

const formatCapabilityLabel = (value = '') =>
  value
    .replace(/_/g, ' ')
    .replace(/\b\w/g, (character) => character.toUpperCase())

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
  const location = useLocation()
  const { currentUser } = useAuth()

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
          error: getApiErrorMessage(error, 'Failed to load doctor overview.'),
          data: null,
        })
      }
    }

    loadOverview()
  }, [])

  const currentView = useMemo(() => getDoctorView(location.pathname), [location.pathname])
  const overview = state.data

  const filteredQueue = useMemo(() => {
    const items = overview?.patient_queue || []
    return items
  }, [overview?.patient_queue])

  const filteredPatients = useMemo(() => {
    const items = overview?.recent_patients || []
    return items
  }, [overview?.recent_patients])

  const filteredResults = useMemo(() => {
    const items = overview?.pending_results || []
    return items
  }, [overview?.pending_results])

  const filteredNotifications = useMemo(() => {
    const items = overview?.notifications || []
    return items
  }, [overview?.notifications])

  const navSections = useMemo(
    () => [
      {
        title: 'Clinical workflow',
        items: [
          {
            key: 'overview',
            label: 'Dashboard',
            description: 'Today, queue, and results',
            glyph: 'DB',
            route: '/doctor-dashboard',
          },
          {
            key: 'patients',
            label: 'My Patients',
            description: 'Assigned patients and directory access',
            glyph: 'PT',
            route: '/doctor-dashboard/patients',
          },
        ],
      },
      {
        title: 'Clinical tools',
        items: [
          {
            key: 'results',
            label: 'Results Inbox',
            description: 'Pending ECG and MRI reviews',
            glyph: 'RS',
            route: '/doctor-dashboard/results',
          },
          {
            key: 'messages',
            label: 'Messages',
            description: 'Patient and care-team notifications',
            glyph: 'MS',
            route: '/doctor-dashboard/messages',
          },
          {
            key: 'ecg',
            label: 'ECG Workspace',
            description: 'Doctor-only intake for ECG uploads and clinical review',
            glyph: 'EC',
            route: '/ecg-analysis',
          },
          {
            key: 'mri',
            label: 'MRI Workspace',
            description: 'Doctor-only intake for MRI uploads and segmentation review',
            glyph: 'MR',
            route: '/mri-analysis',
          },
        ],
      },
    ],
    []
  )

  const notificationCount = overview?.quick_stats?.unread_messages?.value || 0
  const notificationItems = useMemo(
    () =>
      (overview?.notifications || []).slice(0, 6).map((item, index) => ({
        id: item.id || `notification-${index}`,
        title: item.title,
        message: item.message,
        time: item.time_ago || item.timestamp || 'Recent',
      })),
    [overview?.notifications]
  )

  const quickActions = [
    {
      title: 'Open ECG Workspace',
      description: 'Shared intake for doctor-initiated and patient-uploaded ECG studies.',
      action: () => navigate('/ecg-analysis'),
    },
    {
      title: 'Open MRI Workspace',
      description: 'Shared intake for doctor-initiated and patient-uploaded MRI studies.',
      action: () => navigate('/mri-analysis'),
    },
    {
      title: 'Messages Center',
      description: 'Review unread notifications and patient-side workflow updates.',
      action: () => navigate('/doctor-dashboard/messages'),
    },
  ]

  const sharedToolSummary = [
    {
      title: 'ECG intake path',
      helper: 'Clinicians can upload new ECG studies or review assigned ECG cases from the same workspace.',
    },
    {
      title: 'MRI intake path',
      helper: 'Clinicians can upload MRI sequences or review existing imaging cases in one trusted workflow.',
    },
    {
      title: 'Scheduling posture',
      helper: overview?.today_schedule?.available
        ? overview?.today_schedule?.message || 'Appointments are currently flowing from a real scheduling source.'
        : overview?.today_schedule?.message || 'Scheduling remains intentionally disabled until the backend source is trusted.',
    },
  ]

  const handleNav = (item) => {
    if (item.anchorId) {
      document.getElementById(item.anchorId)?.scrollIntoView({ behavior: 'smooth', block: 'start' })
    }
  }

  const renderSchedulePanel = () => (
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

      {overview?.today_schedule?.available && overview?.today_schedule?.data?.length ? (
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
          title={overview?.today_schedule?.available ? 'No appointments scheduled' : 'Scheduling module not configured'}
          message={overview?.today_schedule?.message || 'No trusted appointments source is available.'}
        />
      )}
    </article>
  )

  const renderQueuePanel = () => (
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
        <EmptyPanel
          title="Queue is clear"
          message="No cases currently match the active queue statuses."
        />
      )}
    </article>
  )

  const renderPatientsPanel = () => (
    <article className={styles.panel}>
      <div className={styles.panelHeading}>
        <div>
          <h3>Recent Patients</h3>
          <p>Most recent unique patients associated with your active cases.</p>
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
        <EmptyPanel
          title="No patient matches your search"
          message="Try a different name, MRN, or clear the search field."
        />
      )}
    </article>
  )

  const renderResultsPanel = () => (
    <article className={styles.panel}>
      <div className={styles.panelHeading}>
        <div>
          <h3>Pending Diagnostic Results</h3>
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
        <EmptyPanel
          title="No pending results"
          message="All linked ECG and MRI results appear to be reviewed."
        />
      )}
    </article>
  )

  const renderNotificationsPanel = () => (
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
        <EmptyPanel
          title="Notification center is quiet"
          message="No unread or matching notifications were returned."
        />
      )}
    </article>
  )

  const renderSharedToolsPanel = () => (
    <article className={styles.panel}>
      <div className={styles.panelHeading}>
        <div>
          <h3>Shared Diagnostic Intake</h3>
          <p>Doctor and patient MRI or ECG uploads converge into the same trusted review path.</p>
        </div>
      </div>

      <div className={styles.patientList}>
        {sharedToolSummary.map((item) => (
          <div key={item.title} className={styles.patientCard}>
            <strong>{item.title}</strong>
            <span>Production policy</span>
            <p>{item.helper}</p>
          </div>
        ))}
      </div>
    </article>
  )

  const renderQuickAccessPanel = (title = 'Quick Access', description = 'Jump into the highest-frequency clinical tasks without leaving the current workflow.') => (
    <article className={styles.panel}>
      <div className={styles.panelHeading}>
        <div>
          <h3>{title}</h3>
          <p>{description}</p>
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
  )

  const renderWorkspaceHero = (kicker, heading, body) => (
    <section className={styles.heroSection}>
      <div>
        <span className={styles.kicker}>{kicker}</span>
        <h2>{heading}</h2>
        <p>{body}</p>
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
  )

  const renderOverview = () => (
    <>
      {renderWorkspaceHero(
        'Care delivery status',
        'Prioritize queue pressure, unread alerts, and shared diagnostic intake',
        'This workspace is built from assigned cases, unread notifications, and pending ECG or MRI results. Both doctor and patient uploads flow into the same clinical workspaces, so review never depends on who initiated the study.'
      )}

      <section className={styles.metricGrid}>
        {overview?.quick_stats ? Object.values(overview.quick_stats).map((item) => (
          <MetricCard key={item.label} item={item} />
        )) : null}
      </section>

      <section className={styles.splitGrid}>
        {renderSchedulePanel()}
        {renderQuickAccessPanel()}
      </section>

      <section className={styles.splitGrid}>
        {renderSharedToolsPanel()}
        {renderQueuePanel()}
      </section>

      <section className={styles.splitGrid}>
        {renderPatientsPanel()}
        {renderResultsPanel()}
      </section>

      <section className={styles.splitGrid}>
        {renderNotificationsPanel()}
        <article className={styles.panel}>
          <div className={styles.panelHeading}>
            <div>
              <h3>Clinical Shortcuts</h3>
              <p>Use these routes when you need to move out of the dashboard into a working module.</p>
            </div>
          </div>

          <div className={styles.actionGrid}>
            <button type="button" className={styles.actionCard} onClick={() => navigate('/doctor-dashboard/patients')}>
              <strong>Open Patients Page</strong>
              <p>Review assigned patients first, then jump to the full live directory only if needed.</p>
            </button>
            <button type="button" className={styles.actionCard} onClick={() => navigate('/doctor-dashboard/results')}>
              <strong>Review Pending Results</strong>
              <p>Jump directly to the results inbox for shared ECG and MRI follow-up.</p>
            </button>
          </div>
        </article>
      </section>
    </>
  )

  const renderPatientsView = () => (
    <>
      {renderWorkspaceHero(
        'Patient roster',
        'Stay inside the assigned cohort before jumping to the global directory',
        'This page keeps the most recent patient touchpoints in front of the doctor. Use the live registry only when you need broader search coverage or profile edits.'
      )}
      {renderPatientsPanel()}
      <section className={styles.splitGrid}>
        <article className={styles.panel}>
          <div className={styles.panelHeading}>
            <div>
              <h3>Patient Actions</h3>
              <p>Open related pages without losing the current doctor workflow.</p>
            </div>
          </div>
          <div className={styles.actionGrid}>
            <button type="button" className={styles.actionCard} onClick={() => navigate('/doctor-dashboard/results')}>
              <strong>Open Results Inbox</strong>
              <p>Review unread ECG and MRI outputs related to your active patients.</p>
            </button>
            <button type="button" className={styles.actionCard} onClick={() => navigate('/mri-analysis')}>
              <strong>Open MRI Workspace</strong>
              <p>Shared doctor and patient MRI upload and review path.</p>
            </button>
          </div>
        </article>
        {renderQueuePanel()}
      </section>
    </>
  )

  const renderResultsView = () => (
    <>
      {renderWorkspaceHero(
        'Results inbox',
        'Review pending ECG and MRI studies from one honest queue',
        'Both patient-initiated uploads and doctor-initiated uploads land here through the same diagnostic pathways, so no result gets hidden behind role-specific intake rules.'
      )}
      <section className={styles.splitGrid}>
        {renderResultsPanel()}
        {renderSharedToolsPanel()}
      </section>
      <section className={styles.splitGrid}>
        <article className={styles.panel}>
          <div className={styles.panelHeading}>
            <div>
              <h3>Result Actions</h3>
              <p>Continue into the right module based on the modality and review need.</p>
            </div>
          </div>
          <div className={styles.actionGrid}>
            <button type="button" className={styles.actionCard} onClick={() => navigate('/ecg-analysis')}>
              <strong>Open ECG Review</strong>
              <p>Upload, analyze, and review waveform results from the shared ECG workspace.</p>
            </button>
            <button type="button" className={styles.actionCard} onClick={() => navigate('/mri-analysis')}>
              <strong>Open MRI Review</strong>
              <p>Run segmentation and inspect imaging artifacts from the shared MRI workspace.</p>
            </button>
          </div>
        </article>
        {renderNotificationsPanel()}
      </section>
    </>
  )

  const renderMessagesView = () => (
    <>
      {renderWorkspaceHero(
        'Messages center',
        'See which alerts need a reply and which only need review',
        'This center stays grounded in the real unread notification feed. MRI and ECG uploads from patients show up through the same shared workflow, then surface here as follow-up notices.'
      )}
      {renderNotificationsPanel()}
      <section className={styles.splitGrid}>
        {renderQueuePanel()}
        <article className={styles.panel}>
          <div className={styles.panelHeading}>
            <div>
              <h3>Reply Paths</h3>
              <p>Move from alerts into the right production route instead of dead-end buttons.</p>
            </div>
          </div>
          <div className={styles.actionGrid}>
            <button type="button" className={styles.actionCard} onClick={() => navigate('/doctor-dashboard/results')}>
              <strong>Open Results Inbox</strong>
              <p>Useful when the message is driven by a new ECG or MRI upload.</p>
            </button>
            <button type="button" className={styles.actionCard} onClick={() => navigate('/medical-llm')}>
              <strong>Open Assistant</strong>
              <p>Use the assistant route for drafting communication or structured explanation text.</p>
            </button>
          </div>
        </article>
      </section>
    </>
  )

  const renderCurrentView = () => {
    switch (currentView.key) {
      case 'patients':
        return renderPatientsView()
      case 'results':
        return renderResultsView()
      case 'messages':
        return renderMessagesView()
      default:
        return renderOverview()
    }
  }

  if (state.loading) {
    return (
      <StaffDashboardShell
        currentUser={currentUser}
        roleLabel="Doctor Workspace"
        navSections={navSections}
        activeKey={currentView.key}
        onNavigate={handleNav}
        notificationCount={0}
        notificationItems={[]}
        notificationActionLabel="Open messages center"
        onNotificationAction={() => navigate('/doctor-dashboard/messages')}
        onLogout={onLogout}
        headerTitle={currentView.title}
        headerSubtitle={currentView.subtitle}
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
      activeKey={currentView.key}
      onNavigate={handleNav}
      notificationCount={notificationCount}
      notificationItems={notificationItems}
      notificationActionLabel="Open messages center"
      onNotificationAction={() => navigate('/doctor-dashboard/messages')}
      onLogout={onLogout}
      headerTitle={currentView.title}
      headerSubtitle={currentView.subtitle}
    >
      {state.error ? (
        <article className={styles.errorBanner}>
          <strong>Unable to load dashboard</strong>
          <p>{state.error}</p>
        </article>
      ) : null}

      {renderCurrentView()}
    </StaffDashboardShell>
  )
}

export default DoctorDashboard
