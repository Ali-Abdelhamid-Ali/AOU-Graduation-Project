import { useEffect, useMemo, useState } from 'react'
import { useLocation, useNavigate } from 'react-router-dom'

import StaffDashboardShell from '@/components/layout/StaffDashboardShell'
import { brandingConfig } from '@/config/brandingConfig'
import { ROLES } from '@/config/roles'
import { dashboardAPI, patientsAPI, usersAPI } from '@/services/api'
import { useAuth } from '@/store/AuthContext'
import { getApiErrorMessage } from '@/utils/apiErrorUtils'
import styles from './AdminOperationsDashboard.module.css'

const adminViewConfig = {
  overview: {
    key: 'overview',
    title: 'Administrative Operations Dashboard',
    subtitle: `Production oversight for ${brandingConfig.hospitalName}`,
  },
  analytics: {
    key: 'analytics',
    title: 'Reports & Analytics',
    subtitle: 'Trend panels, telemetry, and chart-backed operational review.',
  },
  alerts: {
    key: 'alerts',
    title: 'Alerts & System Health',
    subtitle: 'Flagged audit signals, infrastructure health, and urgent notices.',
  },
  users: {
    key: 'users',
    title: 'User Management',
    subtitle: 'Doctors, staff, and patients under one operational table.',
  },
  patients: {
    key: 'patients',
    title: 'Patient Directory Snapshot',
    subtitle: 'Live patient registry view inside the admin workspace shell.',
  },
  provisioning: {
    key: 'provisioning',
    title: 'Provisioning Hub',
    subtitle: 'Role-aware quick actions for onboarding and operational handoff.',
  },
}

const getAdminView = (pathname = '') => {
  if (pathname.startsWith('/admin-dashboard/analytics')) return adminViewConfig.analytics
  if (pathname.startsWith('/admin-dashboard/alerts')) return adminViewConfig.alerts
  if (pathname.startsWith('/admin-dashboard/users')) return adminViewConfig.users
  if (pathname.startsWith('/admin-dashboard/patients')) return adminViewConfig.patients
  if (pathname.startsWith('/admin-dashboard/provisioning')) return adminViewConfig.provisioning
  return adminViewConfig.overview
}

const unwrapList = (response) => {
  if (Array.isArray(response)) return response
  if (Array.isArray(response?.data)) return response.data
  if (Array.isArray(response?.data?.data)) return response.data.data
  return []
}

const formatCapabilityLabel = (value = '') =>
  value
    .replace(/_/g, ' ')
    .replace(/\b\w/g, (character) => character.toUpperCase())

const normalizeUserRecord = (type, item = {}) => {
  const roleMap = {
    administrators: 'Administrator',
    doctors: 'Doctor',
    patients: 'Patient',
  }

  const name =
    item.full_name ||
    [item.first_name, item.last_name].filter(Boolean).join(' ') ||
    item.email ||
    'Unnamed user'

  const secondary =
    item.specialty ||
    item.department ||
    item.mrn ||
    item.medical_record_number ||
    item.license_number ||
    'Profile details unavailable'

  const contact = [item.email, item.phone].filter(Boolean).join(' | ') || 'No contact details'

  return {
    id: item.id || item.user_id || `${type}-${name}`,
    name,
    role: roleMap[type] || 'User',
    hospital: item.hospital_name || item.hospital_id || 'Unassigned facility',
    secondary,
    contact,
    isActive: item.is_active !== false,
  }
}

const normalizePatientRecord = (item = {}) => ({
  id: item.id || item.user_id || item.mrn || item.medical_record_number,
  name:
    item.full_name ||
    [item.first_name, item.last_name].filter(Boolean).join(' ') ||
    'Unnamed patient',
  mrn: item.mrn || item.medical_record_number || 'MRN unavailable',
  phone: item.phone || 'No phone on record',
  hospital: item.hospital_name || item.hospital_id || 'Unassigned facility',
  gender: item.gender || 'Unspecified',
  isActive: item.is_active !== false,
})

const toneClassMap = {
  info: styles.toneInfo,
  success: styles.toneSuccess,
  warning: styles.toneWarning,
  critical: styles.toneCritical,
  healthy: styles.toneSuccess,
}

const StatCard = ({ item }) => (
  <article className={`${styles.metricCard} ${item.available === false ? styles.metricCardMuted : ''}`}>
    <div className={styles.metricCardHeader}>
      <span className={styles.metricLabel}>{item.label}</span>
      <span className={`${styles.badge} ${toneClassMap[item.tone] || styles.toneInfo}`}>
        {item.available === false ? 'Unavailable' : 'Live'}
      </span>
    </div>
    <strong className={styles.metricValue}>
      {item.available === false ? 'Not configured' : item.value}
    </strong>
    <p className={styles.metricHelper}>{item.helper}</p>
  </article>
)

const EmptyPanel = ({ title, message }) => (
  <div className={styles.emptyPanel}>
    <strong>{title}</strong>
    <p>{message}</p>
  </div>
)

const ChartPanel = ({ title, chart }) => {
  if (!chart?.available || !chart?.data?.length) {
    return (
      <article className={styles.panel}>
        <div className={styles.panelHeading}>
          <div>
            <h3>{title}</h3>
            <p>{chart?.message}</p>
          </div>
        </div>
        <EmptyPanel
          title={chart?.available ? 'No chart data yet' : 'Capability disabled'}
          message={
            chart?.message ||
            (chart?.available
              ? 'The source is active, but no records are available yet.'
              : 'No trusted data source is available.')
          }
        />
      </article>
    )
  }

  const maxValue = Math.max(...chart.data.map((item) => item.value), 1)

  return (
    <article className={styles.panel}>
      <div className={styles.panelHeading}>
        <div>
          <h3>{title}</h3>
          <p>{chart.message}</p>
        </div>
      </div>

      <div className={styles.barList}>
        {chart.data.map((item) => (
          <div key={item.label} className={styles.barRow}>
            <div className={styles.barMeta}>
              <span>{item.label}</span>
              <strong>{item.value}</strong>
            </div>
            <div className={styles.barTrack}>
              <span
                className={styles.barFill}
                style={{ width: `${Math.max(16, (item.value / maxValue) * 100)}%` }}
              />
            </div>
          </div>
        ))}
      </div>
    </article>
  )
}

const ActivityList = ({ title, items, emptyMessage }) => (
  <article className={styles.panel}>
    <div className={styles.panelHeading}>
      <div>
        <h3>{title}</h3>
        <p>Live operational events pulled from system telemetry.</p>
      </div>
    </div>

    {items?.length ? (
      <div className={styles.feedList}>
        {items.map((item) => (
          <div key={item.id} className={styles.feedItem}>
            <span className={`${styles.feedDot} ${toneClassMap[item.severity] || styles.toneInfo}`} />
            <div className={styles.feedBody}>
              <strong>{item.title}</strong>
              <p>{item.message}</p>
            </div>
            <span className={styles.feedTime}>{item.time_ago || item.timestamp}</span>
          </div>
        ))}
      </div>
    ) : (
      <EmptyPanel title="No recent activity" message={emptyMessage} />
    )}
  </article>
)

const LoadingDashboard = () => (
  <div className={styles.loadingGrid} data-testid="admin-dashboard-loading">
    {Array.from({ length: 8 }).map((_, index) => (
      <div key={index} className={`skeleton ${styles.loadingCard}`} />
    ))}
  </div>
)

export const AdminOperationsDashboard = ({ onLogout }) => {
  const navigate = useNavigate()
  const location = useLocation()
  const { currentUser } = useAuth()

  const [searchQuery, setSearchQuery] = useState('')
  const [roleFilter, setRoleFilter] = useState('all')
  const [statusFilter, setStatusFilter] = useState('all')
  const [userPage, setUserPage] = useState(1)
  const [patientPage, setPatientPage] = useState(1)
  const [overviewState, setOverviewState] = useState({
    loading: true,
    error: '',
    data: null,
  })
  const [usersState, setUsersState] = useState({
    loading: true,
    error: '',
    data: [],
  })
  const [patientsState, setPatientsState] = useState({
    loading: true,
    error: '',
    data: [],
  })

  const normalizedRole = currentUser?.user_role
  const isSuperAdmin = normalizedRole === ROLES.SUPER_ADMIN
  const currentView = useMemo(() => getAdminView(location.pathname), [location.pathname])

  const roleLabel = isSuperAdmin
    ? 'Super Admin Console'
    : 'Admin Workspace'

  useEffect(() => {
    const loadOverview = async () => {
      setOverviewState({ loading: true, error: '', data: null })
      try {
        const response = await dashboardAPI.getAdminOverview()
        setOverviewState({ loading: false, error: '', data: response.data })
      } catch (error) {
        setOverviewState({
          loading: false,
          error: getApiErrorMessage(error, 'Failed to load admin overview.'),
          data: null,
        })
      }
    }

    loadOverview()
  }, [])

  useEffect(() => {
    const activeParam =
      statusFilter === 'active' ? true : statusFilter === 'inactive' ? false : undefined

    const loadUsers = async () => {
      setUsersState((previous) => ({ ...previous, loading: true, error: '' }))
      try {
        const [patients, doctors, administrators] = await Promise.all([
          usersAPI.list('patients', { limit: 25, ...(activeParam !== undefined ? { is_active: activeParam } : {}) }),
          usersAPI.list('doctors', { limit: 25, ...(activeParam !== undefined ? { is_active: activeParam } : {}) }),
          usersAPI.list('administrators', { limit: 25, ...(activeParam !== undefined ? { is_active: activeParam } : {}) }),
        ])

        const rows = [
          ...unwrapList(administrators).map((item) => normalizeUserRecord('administrators', item)),
          ...unwrapList(doctors).map((item) => normalizeUserRecord('doctors', item)),
          ...unwrapList(patients).map((item) => normalizeUserRecord('patients', item)),
        ]

        setUsersState({ loading: false, error: '', data: rows })
      } catch (error) {
        setUsersState({
          loading: false,
          error: getApiErrorMessage(error, 'Failed to load user table.'),
          data: [],
        })
      }
    }

    const loadPatients = async () => {
      setPatientsState((previous) => ({ ...previous, loading: true, error: '' }))
      try {
        const response = await patientsAPI.list({
          limit: 50,
          ...(activeParam !== undefined ? { is_active: activeParam } : {}),
        })

        setPatientsState({
          loading: false,
          error: '',
          data: unwrapList(response).map(normalizePatientRecord),
        })
      } catch (error) {
        setPatientsState({
          loading: false,
          error: getApiErrorMessage(
            error,
            'Failed to load patient registry snapshot.'
          ),
          data: [],
        })
      }
    }

    loadUsers()
    loadPatients()
  }, [statusFilter])

  useEffect(() => {
    setUserPage(1)
    setPatientPage(1)
  }, [searchQuery, roleFilter, statusFilter])

  const filteredUsers = useMemo(() => {
    const normalizedQuery = searchQuery.trim().toLowerCase()

    return usersState.data.filter((user) => {
      const matchesRole = roleFilter === 'all' || user.role.toLowerCase() === roleFilter
      const matchesQuery =
        !normalizedQuery ||
        [user.name, user.role, user.secondary, user.hospital, user.contact]
          .filter(Boolean)
          .some((value) => value.toLowerCase().includes(normalizedQuery))

      return matchesRole && matchesQuery
    })
  }, [roleFilter, searchQuery, usersState.data])

  const filteredPatients = useMemo(() => {
    const normalizedQuery = searchQuery.trim().toLowerCase()

    return patientsState.data.filter((patient) => {
      const matchesQuery =
        !normalizedQuery ||
        [patient.name, patient.mrn, patient.phone, patient.hospital, patient.gender]
          .filter(Boolean)
          .some((value) => value.toLowerCase().includes(normalizedQuery))

      return matchesQuery
    })
  }, [patientsState.data, searchQuery])

  const paginatedUsers = useMemo(() => {
    const start = (userPage - 1) * 8
    return filteredUsers.slice(start, start + 8)
  }, [filteredUsers, userPage])

  const paginatedPatients = useMemo(() => {
    const start = (patientPage - 1) * 8
    return filteredPatients.slice(start, start + 8)
  }, [filteredPatients, patientPage])

  const userTotalPages = Math.max(1, Math.ceil(filteredUsers.length / 8))
  const patientTotalPages = Math.max(1, Math.ceil(filteredPatients.length / 8))
  const overview = overviewState.data
  const statEntries = overview?.stats ? Object.values(overview.stats) : []
  const notificationItems = useMemo(() => {
    const alerts = (overview?.alerts || []).map((item) => ({
      id: `alert-${item.id}`,
      title: item.title,
      message: item.message,
      time: item.timestamp ? new Date(item.timestamp).toLocaleString() : item.time_ago || 'Recent',
    }))
    const activity = (overview?.recent_activity || []).map((item) => ({
      id: `activity-${item.id}`,
      title: item.title,
      message: item.message,
      time: item.time_ago || item.timestamp || 'Recent',
    }))

    return [...alerts, ...activity].slice(0, 6)
  }, [overview?.alerts, overview?.recent_activity])

  const navSections = useMemo(
    () => [
      {
        title: 'Operations',
        items: [
          { key: 'overview', label: 'Overview', description: 'Live command center', glyph: 'OV', route: '/admin-dashboard' },
          { key: 'analytics', label: 'Reports', description: 'Trend panels and chart review', glyph: 'RP', route: '/admin-dashboard/analytics' },
          { key: 'alerts', label: 'Alerts', description: 'System health and audit warnings', glyph: 'AL', route: '/admin-dashboard/alerts' },
          { key: 'users', label: 'Users', description: 'Doctors, staff, and patients', glyph: 'US', route: '/admin-dashboard/users' },
        ],
      },
      {
        title: isSuperAdmin ? 'Governance' : 'Modules',
        items: [
          { key: 'patients', label: 'Patient Directory', description: 'Live registry snapshot inside the shell', glyph: 'PD', route: '/admin-dashboard/patients' },
          {
            key: 'provisioning',
            label: isSuperAdmin ? 'Admin Provisioning' : 'Staff Provisioning',
            description: isSuperAdmin ? 'Administrator creation available' : 'Role creation follows your permissions',
            glyph: 'PR',
            route: '/admin-dashboard/provisioning',
          },
          {
            key: 'appointments',
            label: 'Appointments',
            description: 'Follow-up workload and trend view',
            glyph: 'AP',
            route: '/admin-dashboard/analytics',
            available: overview?.capabilities?.appointments !== false,
          },
        ],
      },
    ],
    [isSuperAdmin, overview?.capabilities?.appointments]
  )

  const quickActions = useMemo(() => {
    if (isSuperAdmin) {
      return [
        { title: 'Add Administrator', description: 'Provision another administrative operator with scoped access.', action: () => navigate('/create-admin') },
        { title: 'Add Doctor', description: 'Create a clinician profile and assign medical metadata.', action: () => navigate('/create-doctor') },
        { title: 'Add Patient', description: 'Register a patient identity and baseline demographics.', action: () => navigate('/create-patient') },
        { title: 'Open Registry', description: 'Move into the patient registry page inside the admin workspace tree.', action: () => navigate('/admin-dashboard/patients') },
      ]
    }

    return [
      { title: 'Add Doctor', description: 'Create a new clinician profile and assign role metadata.', action: () => navigate('/create-doctor') },
      { title: 'Add Patient', description: 'Register a new patient identity and baseline demographics.', action: () => navigate('/create-patient') },
      { title: 'Open Registry', description: 'Review the patient registry snapshot and then move into the full live directory.', action: () => navigate('/admin-dashboard/patients') },
      { title: 'Open Analytics', description: 'Inspect appointment load, trend panels, and operational charts.', action: () => navigate('/admin-dashboard/analytics') },
    ]
  }, [isSuperAdmin, navigate])

  const scopeCards = [
    {
      label: 'Access Scope',
      value: isSuperAdmin
        ? 'System-wide governance'
        : 'Facility administration',
      tone: 'info',
    },
    {
      label: 'Provisioning',
      value: isSuperAdmin
        ? 'Admins, doctors, patients'
        : 'Doctors and patients',
      tone: 'success',
    },
    {
      label: 'Facility',
      value: currentUser?.hospital_name || brandingConfig.hospitalName,
      tone: 'info',
    },
    {
      label: 'Search Context',
      value: searchQuery.trim() ? 'Filtered across live records' : 'Global search idle',
      tone: searchQuery.trim() ? 'warning' : 'healthy',
    },
  ]

  const handleNav = (item) => {
    if (item.anchorId) {
      document.getElementById(item.anchorId)?.scrollIntoView({ behavior: 'smooth', block: 'start' })
    }
  }

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

  const renderQuickActionsPanel = () => (
    <article className={styles.panel}>
      <div className={styles.panelHeading}>
        <div>
          <h3>Quick Actions</h3>
          <p>Only actions backed by the current production permissions are exposed here.</p>
        </div>
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
  )

  const renderRoleCoveragePanel = () => (
    <article className={styles.panel}>
      <div className={styles.panelHeading}>
        <div>
          <h3>Role Coverage</h3>
          <p>This summary reflects what this signed-in role can responsibly act on.</p>
        </div>
      </div>

      <div className={styles.healthGrid}>
        {scopeCards.map((item) => (
          <div key={item.label} className={styles.healthMetric}>
            <span>{item.label}</span>
            <strong>{item.value}</strong>
            <span className={`${styles.badge} ${toneClassMap[item.tone] || styles.toneInfo}`}>
              {item.tone}
            </span>
          </div>
        ))}
      </div>
    </article>
  )

  const renderAlertsPanel = () => (
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
        <EmptyPanel
          title="No active alerts"
          message="System thresholds are currently within healthy bounds."
        />
      )}
    </article>
  )

  const renderSystemHealthPanel = () => (
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
            <span className={`${styles.badge} ${toneClassMap[metric.tone] || styles.toneInfo}`}>
              {metric.tone}
            </span>
          </div>
        ))}
      </div>
    </article>
  )

  const renderSearchCoveragePanel = () => (
    <article className={styles.panel}>
      <div className={styles.panelHeading}>
        <div>
          <h3>Search Coverage</h3>
          <p>Filters below combine the global search box with role and status scopes.</p>
        </div>
      </div>

      <div className={styles.healthGrid}>
        <div className={styles.healthMetric}>
          <span>Global Search</span>
          <strong>{searchQuery.trim() ? 'Active' : 'Idle'}</strong>
          <span className={`${styles.badge} ${searchQuery.trim() ? styles.toneInfo : styles.toneSuccess}`}>
            {searchQuery.trim() ? 'filtered' : 'clear'}
          </span>
        </div>
        <div className={styles.healthMetric}>
          <span>Role Filter</span>
          <strong>{roleFilter === 'all' ? 'All roles' : roleFilter}</strong>
          <span className={`${styles.badge} ${styles.toneInfo}`}>scope</span>
        </div>
        <div className={styles.healthMetric}>
          <span>Status Filter</span>
          <strong>{statusFilter === 'all' ? 'All statuses' : statusFilter}</strong>
          <span className={`${styles.badge} ${styles.toneInfo}`}>scope</span>
        </div>
        <div className={styles.healthMetric}>
          <span>Matched Users</span>
          <strong>{filteredUsers.length}</strong>
          <span className={`${styles.badge} ${styles.toneSuccess}`}>live</span>
        </div>
      </div>
    </article>
  )

  const renderUserTable = () => (
    <section className={styles.panel}>
      <div className={styles.panelHeading}>
        <div>
          <h3>User Management</h3>
            <p>Unified view across administrators, doctors, and patients.</p>
        </div>
      </div>

      <div className={styles.filtersRow}>
        <label>
          <span>Role</span>
          <select value={roleFilter} onChange={(event) => setRoleFilter(event.target.value)}>
            <option value="all">All roles</option>
            <option value="administrator">Administrators</option>
            <option value="doctor">Doctors</option>
            <option value="patient">Patients</option>
          </select>
        </label>

        <label>
          <span>Status</span>
          <select value={statusFilter} onChange={(event) => setStatusFilter(event.target.value)}>
            <option value="all">All statuses</option>
            <option value="active">Active only</option>
            <option value="inactive">Inactive only</option>
          </select>
        </label>

        <div className={styles.tableSummary}>
          <strong>{filteredUsers.length}</strong>
          <span>matching records</span>
        </div>
      </div>

      {usersState.loading ? (
        <div className={styles.tableLoading}>
          {Array.from({ length: 6 }).map((_, index) => (
            <div key={index} className={`skeleton ${styles.tableSkeleton}`} />
          ))}
        </div>
      ) : usersState.error ? (
        <EmptyPanel title="User table unavailable" message={usersState.error} />
      ) : paginatedUsers.length ? (
        <>
          <div className={styles.tableWrap}>
            <table className={styles.table}>
              <thead>
                <tr>
                  <th>User</th>
                  <th>Role</th>
                  <th>Context</th>
                  <th>Contact</th>
                  <th>Status</th>
                </tr>
              </thead>
              <tbody>
                {paginatedUsers.map((user) => (
                  <tr key={user.id}>
                    <td>
                      <strong>{user.name}</strong>
                      <span>{user.hospital}</span>
                    </td>
                    <td>{user.role}</td>
                    <td>{user.secondary}</td>
                    <td>{user.contact}</td>
                    <td>
                      <span className={`${styles.badge} ${user.isActive ? styles.toneSuccess : styles.toneWarning}`}>
                        {user.isActive ? 'Active' : 'Inactive'}
                      </span>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>

          <div className={styles.paginationRow}>
            <button
              type="button"
              onClick={() => setUserPage((current) => Math.max(1, current - 1))}
              disabled={userPage === 1}
            >
              Previous
            </button>
            <span>
              Page {userPage} of {userTotalPages}
            </span>
            <button
              type="button"
              onClick={() => setUserPage((current) => Math.min(userTotalPages, current + 1))}
              disabled={userPage === userTotalPages}
            >
              Next
            </button>
          </div>
        </>
      ) : (
        <EmptyPanel
          title="No users match these filters"
          message="Try adjusting the global search or status filters."
        />
      )}
    </section>
  )

  const renderPatientTable = () => (
    <section className={styles.panel}>
      <div className={styles.panelHeading}>
        <div>
          <h3>Patient Directory Snapshot</h3>
          <p>Live patient registry view scoped to the signed-in operational role.</p>
        </div>
      </div>

      <div className={styles.filtersRow}>
        <label>
          <span>Status</span>
          <select value={statusFilter} onChange={(event) => setStatusFilter(event.target.value)}>
            <option value="all">All statuses</option>
            <option value="active">Active only</option>
            <option value="inactive">Inactive only</option>
          </select>
        </label>

        <div className={styles.tableSummary}>
          <strong>{filteredPatients.length}</strong>
          <span>patients in scope</span>
        </div>
      </div>

      {patientsState.loading ? (
        <div className={styles.tableLoading}>
          {Array.from({ length: 6 }).map((_, index) => (
            <div key={index} className={`skeleton ${styles.tableSkeleton}`} />
          ))}
        </div>
      ) : patientsState.error ? (
        <EmptyPanel title="Patient registry unavailable" message={patientsState.error} />
      ) : paginatedPatients.length ? (
        <>
          <div className={styles.tableWrap}>
            <table className={styles.table}>
              <thead>
                <tr>
                  <th>Patient</th>
                  <th>MRN</th>
                  <th>Contact</th>
                  <th>Facility</th>
                  <th>Status</th>
                </tr>
              </thead>
              <tbody>
                {paginatedPatients.map((patient) => (
                  <tr key={patient.id}>
                    <td>
                      <strong>{patient.name}</strong>
                      <span>{patient.gender}</span>
                    </td>
                    <td>{patient.mrn}</td>
                    <td>{patient.phone}</td>
                    <td>{patient.hospital}</td>
                    <td>
                      <span className={`${styles.badge} ${patient.isActive ? styles.toneSuccess : styles.toneWarning}`}>
                        {patient.isActive ? 'Active' : 'Inactive'}
                      </span>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>

          <div className={styles.paginationRow}>
            <button
              type="button"
              onClick={() => setPatientPage((current) => Math.max(1, current - 1))}
              disabled={patientPage === 1}
            >
              Previous
            </button>
            <span>
              Page {patientPage} of {patientTotalPages}
            </span>
            <button
              type="button"
              onClick={() => setPatientPage((current) => Math.min(patientTotalPages, current + 1))}
              disabled={patientPage === patientTotalPages}
            >
              Next
            </button>
          </div>
        </>
      ) : (
        <EmptyPanel
          title="No patients match the active filters"
          message="Try clearing the search box or broadening the active status scope."
        />
      )}
    </section>
  )

  const renderOverview = () => (
    <>
      {renderWorkspaceHero(
        isSuperAdmin ? 'Enterprise control layer' : isNurse ? 'Shift operations layer' : 'Production command center',
        isSuperAdmin
          ? 'Govern live users, alerts, and platform readiness without fabricated metrics'
          : isNurse
            ? 'Coordinate patient flow, live telemetry, and open issues from one calm operational view'
            : 'Operational visibility without fabricated data',
        isSuperAdmin
          ? 'This command center keeps governance, user operations, and system health in one place. Any module without a trusted backend source stays visible as a pending capability, not fake data.'
          : isNurse
            ? 'This workspace keeps the floor team aligned around users, directory access, alerts, and health telemetry. Unsupported modules remain visible as controlled gaps.'
            : 'This dashboard surfaces live user, clinical, audit, and infrastructure signals. Modules without a trusted backend source remain visible as disabled production gaps.'
      )}

      <section className={styles.metricGrid}>
        {statEntries.map((item) => (
          <StatCard key={item.label} item={item} />
        ))}
      </section>

      <section className={styles.chartGrid}>
        <ChartPanel
          title="Daily Appointments Trend"
          chart={overview?.charts?.daily_appointments_trend}
        />
        <ChartPanel title="Revenue by Month" chart={overview?.charts?.revenue_by_month} />
        <ChartPanel
          title="Disease Distribution"
          chart={overview?.charts?.disease_distribution}
        />
      </section>

      <section className={styles.splitGrid}>
        {renderQuickActionsPanel()}
        {renderRoleCoveragePanel()}
      </section>

      <section className={styles.splitGrid}>
        <ActivityList
          title="Recent Activity"
          items={overview?.recent_activity}
          emptyMessage="No audit activity has been captured yet."
        />
        {renderAlertsPanel()}
      </section>

      <section className={styles.splitGrid}>
        {renderSystemHealthPanel()}
        {renderSearchCoveragePanel()}
      </section>

      {renderUserTable()}
    </>
  )

  const renderAnalyticsView = () => (
    <>
      {renderWorkspaceHero(
        'Analytics review',
        'Inspect trends without pretending unsupported modules are complete',
        'This analytics page isolates the chart-backed operational view. When a capability is not configured, it remains explicit here instead of being hidden behind decorative visuals.'
      )}
      <section className={styles.chartGrid}>
        <ChartPanel
          title="Daily Appointments Trend"
          chart={overview?.charts?.daily_appointments_trend}
        />
        <ChartPanel title="Revenue by Month" chart={overview?.charts?.revenue_by_month} />
        <ChartPanel
          title="Disease Distribution"
          chart={overview?.charts?.disease_distribution}
        />
      </section>
      <section className={styles.splitGrid}>
        <ActivityList
          title="Recent Activity"
          items={overview?.recent_activity}
          emptyMessage="No audit activity has been captured yet."
        />
        {renderQuickActionsPanel()}
      </section>
    </>
  )

  const renderAlertsView = () => (
    <>
      {renderWorkspaceHero(
        'Alert management',
        'Separate urgent signals from general admin browsing',
        'The alerts page gives audit warnings and runtime health a dedicated surface, so operational users can triage incidents without scanning the full dashboard.'
      )}
      <section className={styles.splitGrid}>
        {renderAlertsPanel()}
        {renderSystemHealthPanel()}
      </section>
      <section className={styles.splitGrid}>
        <ActivityList
          title="Recent Activity"
          items={overview?.recent_activity}
          emptyMessage="No recent operational activity is available."
        />
        {renderRoleCoveragePanel()}
      </section>
    </>
  )

  const renderUsersView = () => (
    <>
      {renderWorkspaceHero(
        'User operations',
        'Search and filter people records from one route-backed page',
        'This page keeps user management as a real destination in the admin workspace, not just a scrolled section hidden inside the overview.'
      )}
      <section className={styles.splitGrid}>
        {renderSearchCoveragePanel()}
        {renderRoleCoveragePanel()}
      </section>
      {renderUserTable()}
    </>
  )

  const renderPatientsView = () => (
    <>
      {renderWorkspaceHero(
        'Patient registry',
        'Review the live patient snapshot before moving into detailed editing',
        'This page gives administration a route-backed patient registry view inside the same workspace shell. When deeper editing is needed, the full legacy directory remains available as a next step.'
      )}
      {renderPatientTable()}
      <section className={styles.splitGrid}>
        <article className={styles.panel}>
          <div className={styles.panelHeading}>
            <div>
              <h3>Patient Actions</h3>
              <p>Use route-based actions instead of dead-end dashboard buttons.</p>
            </div>
          </div>
          <div className={styles.actionGrid}>
            <button type="button" className={styles.actionCard} onClick={() => navigate('/create-patient')}>
              <strong>Add Patient</strong>
              <p>Open the existing patient enrollment flow from within the admin workflow tree.</p>
            </button>
          </div>
        </article>
        {renderQuickActionsPanel()}
      </section>
    </>
  )

  const renderProvisioningView = () => (
    <>
      {renderWorkspaceHero(
        'Provisioning hub',
        'Onboard the right role without leaving the admin workspace tree',
        'This page turns the old quick-action block into a real route. Each button here opens an actual form or operational destination, not a decorative placeholder.'
      )}
      <section className={styles.splitGrid}>
        {renderQuickActionsPanel()}
        {renderRoleCoveragePanel()}
      </section>
      <section className={styles.splitGrid}>
        {renderPatientTable()}
        <article className={styles.panel}>
          <div className={styles.panelHeading}>
            <div>
              <h3>Provisioning Guidance</h3>
              <p>Keep this flow honest to the permissions and modules that exist today.</p>
            </div>
          </div>
          <div className={styles.healthGrid}>
            <div className={styles.healthMetric}>
              <span>Administrator Creation</span>
              <strong>{isSuperAdmin ? 'Enabled' : 'Restricted'}</strong>
              <span className={`${styles.badge} ${isSuperAdmin ? styles.toneSuccess : styles.toneWarning}`}>
                {isSuperAdmin ? 'allowed' : 'guarded'}
              </span>
            </div>
            <div className={styles.healthMetric}>
              <span>Doctor Creation</span>
              <strong>{isNurse ? 'Restricted' : 'Enabled'}</strong>
              <span className={`${styles.badge} ${isNurse ? styles.toneWarning : styles.toneSuccess}`}>
                {isNurse ? 'guarded' : 'allowed'}
              </span>
            </div>
            <div className={styles.healthMetric}>
              <span>Patient Intake</span>
              <strong>Enabled</strong>
              <span className={`${styles.badge} ${styles.toneSuccess}`}>allowed</span>
            </div>
          </div>
        </article>
      </section>
    </>
  )

  const renderCurrentView = () => {
    switch (currentView.key) {
      case 'analytics':
        return renderAnalyticsView()
      case 'alerts':
        return renderAlertsView()
      case 'users':
        return renderUsersView()
      case 'patients':
        return renderPatientsView()
      case 'provisioning':
        return renderProvisioningView()
      default:
        return renderOverview()
    }
  }

  if (overviewState.loading) {
    return (
      <StaffDashboardShell
        currentUser={currentUser}
        roleLabel={roleLabel}
        navSections={navSections}
        activeKey={currentView.key}
        onNavigate={handleNav}
        searchValue={searchQuery}
        onSearchChange={setSearchQuery}
        searchPlaceholder="Search users, patients, departments, or records"
        notificationCount={0}
        notificationItems={[]}
        notificationActionLabel="Open alerts page"
        onNotificationAction={() => navigate('/admin-dashboard/alerts')}
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
      roleLabel={roleLabel}
      navSections={navSections}
      activeKey={currentView.key}
      onNavigate={handleNav}
      searchValue={searchQuery}
      onSearchChange={setSearchQuery}
      searchPlaceholder="Search users, patients, departments, or records"
      notificationCount={overview?.alerts?.length || 0}
      notificationItems={notificationItems}
      notificationActionLabel="Open alerts page"
      onNotificationAction={() => navigate('/admin-dashboard/alerts')}
      onLogout={onLogout}
      headerTitle={currentView.title}
      headerSubtitle={currentView.subtitle}
    >
      {overviewState.error ? (
        <article className={styles.errorBanner}>
          <strong>Unable to load overview</strong>
          <p>{overviewState.error}</p>
        </article>
      ) : null}

      {renderCurrentView()}
    </StaffDashboardShell>
  )
}

export default AdminOperationsDashboard
