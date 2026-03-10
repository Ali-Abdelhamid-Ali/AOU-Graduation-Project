import { useEffect, useMemo, useState } from 'react'
import { useNavigate } from 'react-router-dom'

import StaffDashboardShell from '@/components/layout/StaffDashboardShell'
import { useAuth } from '@/store/AuthContext'
import { dashboardAPI, usersAPI } from '@/services/api'
import { brandingConfig } from '@/config/brandingConfig'
import styles from './AdminOperationsDashboard.module.css'

const unwrapList = (response) => {
  if (Array.isArray(response)) return response
  if (Array.isArray(response?.data)) return response.data
  if (Array.isArray(response?.data?.data)) return response.data.data
  return []
}

const normalizeUserRecord = (type, item = {}) => {
  const roleMap = {
    administrators: 'Administrator',
    doctors: 'Doctor',
    nurses: 'Nurse',
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

  const contact = [item.email, item.phone].filter(Boolean).join(' • ') || 'No contact details'

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
        <EmptyPanel title="Capability disabled" message={chart?.message || 'No data source available.'} />
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
  const { currentUser } = useAuth()

  const [searchQuery, setSearchQuery] = useState('')
  const [roleFilter, setRoleFilter] = useState('all')
  const [statusFilter, setStatusFilter] = useState('all')
  const [page, setPage] = useState(1)
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

  useEffect(() => {
    const loadOverview = async () => {
      setOverviewState({ loading: true, error: '', data: null })
      try {
        const response = await dashboardAPI.getAdminOverview()
        setOverviewState({ loading: false, error: '', data: response.data })
      } catch (error) {
        setOverviewState({
          loading: false,
          error: error?.detail || error?.message || 'Failed to load admin overview.',
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
        const [patients, doctors, administrators, nurses] = await Promise.all([
          usersAPI.list('patients', { limit: 25, ...(activeParam !== undefined ? { is_active: activeParam } : {}) }),
          usersAPI.list('doctors', { limit: 25, ...(activeParam !== undefined ? { is_active: activeParam } : {}) }),
          usersAPI.list('administrators', { limit: 25, ...(activeParam !== undefined ? { is_active: activeParam } : {}) }),
          usersAPI.list('nurses', { limit: 25, ...(activeParam !== undefined ? { is_active: activeParam } : {}) }),
        ])

        const rows = [
          ...unwrapList(administrators).map((item) => normalizeUserRecord('administrators', item)),
          ...unwrapList(doctors).map((item) => normalizeUserRecord('doctors', item)),
          ...unwrapList(nurses).map((item) => normalizeUserRecord('nurses', item)),
          ...unwrapList(patients).map((item) => normalizeUserRecord('patients', item)),
        ]

        setUsersState({ loading: false, error: '', data: rows })
      } catch (error) {
        setUsersState({
          loading: false,
          error: error?.detail || error?.message || 'Failed to load user table.',
          data: [],
        })
      }
    }

    loadUsers()
  }, [statusFilter])

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

  useEffect(() => {
    setPage(1)
  }, [searchQuery, roleFilter, statusFilter])

  const paginatedUsers = useMemo(() => {
    const start = (page - 1) * 8
    return filteredUsers.slice(start, start + 8)
  }, [filteredUsers, page])

  const totalPages = Math.max(1, Math.ceil(filteredUsers.length / 8))

  const navSections = useMemo(
    () => [
      {
        title: 'Operations',
        items: [
          { key: 'overview', label: 'Overview', description: 'Live command center', glyph: 'O', anchorId: 'overview' },
          { key: 'users', label: 'Users', description: 'Doctors, staff, patients', glyph: 'U', anchorId: 'user-management' },
          { key: 'departments', label: 'Departments', description: 'Module pending', glyph: 'D', available: false },
          { key: 'appointments', label: 'Appointments', description: 'Module pending', glyph: 'A', available: false },
        ],
      },
      {
        title: 'Governance',
        items: [
          { key: 'analytics', label: 'Reports', description: 'Printable snapshot', glyph: 'R', anchorId: 'analytics' },
          { key: 'billing', label: 'Billing', description: 'Module pending', glyph: 'B', available: false },
          { key: 'alerts', label: 'Alerts', description: 'Audit and system health', glyph: '!', anchorId: 'system-alerts' },
          { key: 'settings', label: 'Settings', description: 'Module pending', glyph: 'S', available: false },
        ],
      },
    ],
    []
  )

  const handleNav = (item) => {
    if (item.anchorId) {
      document.getElementById(item.anchorId)?.scrollIntoView({ behavior: 'smooth', block: 'start' })
    }
  }

  const quickActions = [
    {
      title: 'Add Doctor',
      description: 'Create a new clinician profile and assign role metadata.',
      action: () => navigate('/create-doctor'),
    },
    {
      title: 'Add Patient',
      description: 'Register a new patient identity and baseline demographics.',
      action: () => navigate('/create-patient'),
    },
    {
      title: 'Generate Report',
      description: 'Open browser print mode for a clean operational snapshot.',
      action: () => window.print(),
    },
  ]

  const overview = overviewState.data
  const statEntries = overview?.stats ? Object.values(overview.stats) : []

  if (overviewState.loading) {
    return (
      <StaffDashboardShell
        currentUser={currentUser}
        roleLabel="Admin Workspace"
        navSections={navSections}
        activeKey="overview"
        onNavigate={handleNav}
        searchValue={searchQuery}
        onSearchChange={setSearchQuery}
        notificationCount={0}
        onLogout={onLogout}
        headerTitle="Administrative Operations Dashboard"
        headerSubtitle={`Production oversight for ${brandingConfig.hospitalName}`}
      >
        <LoadingDashboard />
      </StaffDashboardShell>
    )
  }

  return (
    <StaffDashboardShell
      currentUser={currentUser}
      roleLabel="Admin Workspace"
      navSections={navSections}
      activeKey="overview"
      onNavigate={handleNav}
      searchValue={searchQuery}
      onSearchChange={setSearchQuery}
      notificationCount={overview?.alerts?.length || 0}
      onLogout={onLogout}
      headerTitle="Administrative Operations Dashboard"
      headerSubtitle={`Production oversight for ${brandingConfig.hospitalName}`}
    >
      {overviewState.error ? (
        <article className={styles.errorBanner}>
          <strong>Unable to load overview</strong>
          <p>{overviewState.error}</p>
        </article>
      ) : null}

      <section id="overview" className={styles.heroSection}>
        <div>
          <span className={styles.kicker}>Production command center</span>
          <h2>Operational visibility without fabricated data</h2>
          <p>
            This dashboard surfaces live user, clinical, audit, and infrastructure signals.
            Modules without a trusted backend source remain visible as disabled production gaps.
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
        {statEntries.map((item) => (
          <StatCard key={item.label} item={item} />
        ))}
      </section>

      <section id="analytics" className={styles.chartGrid}>
        <ChartPanel title="Daily Appointments Trend" chart={overview?.charts?.daily_appointments_trend} />
        <ChartPanel title="Revenue by Month" chart={overview?.charts?.revenue_by_month} />
        <ChartPanel title="Disease Distribution" chart={overview?.charts?.disease_distribution} />
      </section>

      <section className={styles.splitGrid}>
        <article className={styles.panel}>
          <div className={styles.panelHeading}>
            <div>
              <h3>Quick Actions</h3>
              <p>High-frequency administrative tasks for production operations.</p>
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

        <ActivityList
          title="Recent Activity"
          items={overview?.recent_activity}
          emptyMessage="No audit activity has been captured yet."
        />
      </section>

      <section id="system-alerts" className={styles.splitGrid}>
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
                  <span className={styles.feedTime}>{alert.timestamp ? new Date(alert.timestamp).toLocaleString() : 'No timestamp'}</span>
                </div>
              ))}
            </div>
          ) : (
            <EmptyPanel title="No active alerts" message="System thresholds are currently within healthy bounds." />
          )}
        </article>
      </section>

      <section id="user-management" className={styles.panel}>
        <div className={styles.panelHeading}>
          <div>
            <h3>User Management</h3>
            <p>Unified view across administrators, doctors, nurses, and patients.</p>
          </div>
        </div>

        <div className={styles.filtersRow}>
          <label>
            <span>Role</span>
            <select value={roleFilter} onChange={(event) => setRoleFilter(event.target.value)}>
              <option value="all">All roles</option>
              <option value="administrator">Administrators</option>
              <option value="doctor">Doctors</option>
              <option value="nurse">Nurses</option>
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
              <button type="button" onClick={() => setPage((current) => Math.max(1, current - 1))} disabled={page === 1}>
                Previous
              </button>
              <span>
                Page {page} of {totalPages}
              </span>
              <button type="button" onClick={() => setPage((current) => Math.min(totalPages, current + 1))} disabled={page === totalPages}>
                Next
              </button>
            </div>
          </>
        ) : (
          <EmptyPanel title="No users match these filters" message="Try adjusting the global search or status filters." />
        )}
      </section>
    </StaffDashboardShell>
  )
}

export default AdminOperationsDashboard
