import { useEffect, useMemo, useState } from 'react'
import { useNavigate } from 'react-router-dom'

import { brandingConfig } from '@/config/brandingConfig'
import { ROLES } from '@/config/roles'
import { dashboardAPI, usersAPI, patientsAPI } from '@/services/api'
import { useAuth } from '@/store/AuthContext'
import { getApiErrorMessage } from '@/utils/apiErrorUtils'
import {
  StatCard,
  ChartPanel,
  ActivityList,
  EmptyPanel,
  SectionLoading,
  ErrorBanner,
  formatCapabilityLabel,
  toneClassMap,
} from './SharedPanels'
import styles from '../AdminOperationsDashboard.module.css'

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
    item.specialty || item.department || item.mrn || item.medical_record_number || item.license_number || 'Profile details unavailable'
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

export const AdminOverview = () => {
  const navigate = useNavigate()
  const { currentUser } = useAuth()

  const normalizedRole = currentUser?.user_role
  const isSuperAdmin = normalizedRole === ROLES.SUPER_ADMIN
  const isNurse = normalizedRole === ROLES.NURSE

  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')
  const [overview, setOverview] = useState(null)
  const [usersData, setUsersData] = useState({ loading: true, error: '', data: [] })

  // Fetch overview data
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
          setError(getApiErrorMessage(err, 'Failed to load admin overview.'))
          setLoading(false)
        }
      }
    }
    load()
    return () => { cancelled = true }
  }, [])

  // Fetch user summary for the table on overview
  useEffect(() => {
    let cancelled = false
    const load = async () => {
      setUsersData(prev => ({ ...prev, loading: true, error: '' }))
      try {
        const [patients, doctors, administrators, nurses] = await Promise.all([
          usersAPI.list('patients', { limit: 10 }),
          usersAPI.list('doctors', { limit: 10 }),
          usersAPI.list('administrators', { limit: 10 }),
          usersAPI.list('nurses', { limit: 10 }),
        ])
        if (!cancelled) {
          const rows = [
            ...unwrapList(administrators).map((i) => normalizeUserRecord('administrators', i)),
            ...unwrapList(doctors).map((i) => normalizeUserRecord('doctors', i)),
            ...unwrapList(nurses).map((i) => normalizeUserRecord('nurses', i)),
            ...unwrapList(patients).map((i) => normalizeUserRecord('patients', i)),
          ]
          setUsersData({ loading: false, error: '', data: rows })
        }
      } catch (err) {
        if (!cancelled) {
          setUsersData({ loading: false, error: getApiErrorMessage(err, 'Failed to load users.'), data: [] })
        }
      }
    }
    load()
    return () => { cancelled = true }
  }, [])

  const quickActions = useMemo(() => {
    if (isSuperAdmin) {
      return [
        { title: 'Add Administrator', description: 'Provision another administrative operator with scoped access.', action: () => navigate('/create-admin') },
        { title: 'Add Doctor', description: 'Create a clinician profile and assign medical metadata.', action: () => navigate('/create-doctor') },
        { title: 'Add Patient', description: 'Register a patient identity and baseline demographics.', action: () => navigate('/create-patient') },
        { title: 'Open Registry', description: 'Move into the patient registry page inside the admin workspace tree.', action: () => navigate('/admin-dashboard/patients') },
      ]
    }
    if (isNurse) {
      return [
        { title: 'Add Patient', description: 'Register a patient record that requires immediate intake.', action: () => navigate('/create-patient') },
        { title: 'Open Registry', description: 'Review the patient registry snapshot and then open the live directory.', action: () => navigate('/admin-dashboard/patients') },
        { title: 'Open Analytics', description: 'Review appointment load and trend panels for the current operational scope.', action: () => navigate('/admin-dashboard/analytics') },
      ]
    }
    return [
      { title: 'Add Doctor', description: 'Create a new clinician profile and assign role metadata.', action: () => navigate('/create-doctor') },
      { title: 'Add Patient', description: 'Register a new patient identity and baseline demographics.', action: () => navigate('/create-patient') },
      { title: 'Open Registry', description: 'Review the patient registry snapshot and then move into the full live directory.', action: () => navigate('/admin-dashboard/patients') },
      { title: 'Open Analytics', description: 'Inspect appointment load, trend panels, and operational charts.', action: () => navigate('/admin-dashboard/analytics') },
    ]
  }, [isNurse, isSuperAdmin, navigate])

  const scopeCards = [
    {
      label: 'Access Scope',
      value: isSuperAdmin ? 'System-wide governance' : isNurse ? 'Clinical operations coordination' : 'Facility administration',
      tone: 'info',
    },
    {
      label: 'Provisioning',
      value: isSuperAdmin ? 'Admins, doctors, patients' : isNurse ? 'Patients and directory only' : 'Doctors and patients',
      tone: 'success',
    },
    {
      label: 'Facility',
      value: currentUser?.hospital_name || brandingConfig.hospitalName,
      tone: 'info',
    },
  ]

  const statEntries = overview?.stats ? Object.values(overview.stats) : []

  if (loading) return <SectionLoading />

  return (
    <>
      <ErrorBanner message={error} />

      <section className={styles.heroSection}>
        <div>
          <span className={styles.kicker}>
            {isSuperAdmin ? 'Enterprise control layer' : isNurse ? 'Shift operations layer' : 'Production command center'}
          </span>
          <h2>
            {isSuperAdmin
              ? 'Govern live users, alerts, and platform readiness without fabricated metrics'
              : isNurse
                ? 'Coordinate patient flow, live telemetry, and open issues from one calm operational view'
                : 'Operational visibility without fabricated data'}
          </h2>
          <p>
            {isSuperAdmin
              ? 'This command center keeps governance, user operations, and system health in one place. Any module without a trusted backend source stays visible as a pending capability, not fake data.'
              : isNurse
                ? 'This workspace keeps the floor team aligned around users, directory access, alerts, and health telemetry. Unsupported modules remain visible as controlled gaps.'
                : 'This dashboard surfaces live user, clinical, audit, and infrastructure signals. Modules without a trusted backend source remain visible as disabled production gaps.'}
          </p>
        </div>
        <div className={styles.heroCapabilities}>
          {Object.entries(overview?.capabilities || {}).map(([key, enabled]) => (
            <span key={key} className={`${styles.badge} ${enabled ? styles.toneSuccess : styles.toneWarning}`}>
              {formatCapabilityLabel(key)}: {enabled ? 'available' : 'pending'}
            </span>
          ))}
        </div>
      </section>

      <section className={styles.metricGrid}>
        {statEntries.map((item) => (
          <StatCard key={item.label} item={item} />
        ))}
      </section>

      <section className={styles.chartGrid}>
        <ChartPanel title="Daily Appointments Trend" chart={overview?.charts?.daily_appointments_trend} />
        <ChartPanel title="Revenue by Month" chart={overview?.charts?.revenue_by_month} />
        <ChartPanel title="Disease Distribution" chart={overview?.charts?.disease_distribution} />
      </section>

      <section className={styles.splitGrid}>
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
                <span className={`${styles.badge} ${toneClassMap[item.tone] || styles.toneInfo}`}>{item.tone}</span>
              </div>
            ))}
          </div>
        </article>
      </section>

      <section className={styles.splitGrid}>
        <ActivityList title="Recent Activity" items={overview?.recent_activity} emptyMessage="No audit activity has been captured yet." />

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
                  <span className={`${styles.badge} ${toneClassMap[alert.severity] || styles.toneWarning}`}>{alert.severity}</span>
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
      </section>

      <section className={styles.splitGrid}>
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

        <article className={styles.panel}>
          <div className={styles.panelHeading}>
            <div>
              <h3>Users Summary</h3>
              <p>Quick counts across all user types.</p>
            </div>
          </div>
          <div className={styles.healthGrid}>
            <div className={styles.healthMetric}>
              <span>Total Users</span>
              <strong>{usersData.loading ? '...' : usersData.data.length}</strong>
              <span className={`${styles.badge} ${styles.toneSuccess}`}>live</span>
            </div>
          </div>
        </article>
      </section>
    </>
  )
}

export default AdminOverview
