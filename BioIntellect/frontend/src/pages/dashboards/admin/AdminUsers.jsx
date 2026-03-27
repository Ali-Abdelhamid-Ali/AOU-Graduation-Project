import { useEffect, useMemo, useState } from 'react'

import { usersAPI } from '@/services/api'
import { getApiErrorMessage } from '@/utils/apiErrorUtils'
import { EmptyPanel, SectionLoading, ErrorBanner } from './SharedPanels'
import styles from '../AdminOperationsDashboard.module.css'

const unwrapList = (response) => {
  if (Array.isArray(response)) return response
  if (Array.isArray(response?.data)) return response.data
  if (Array.isArray(response?.data?.data)) return response.data.data
  return []
}

const normalizeUserRecord = (type, item = {}) => {
  const roleMap = { administrators: 'Administrator', doctors: 'Doctor', patients: 'Patient' }
  const name = item.full_name || [item.first_name, item.last_name].filter(Boolean).join(' ') || item.email || 'Unnamed user'
  const secondary = item.specialty || item.department || item.mrn || item.medical_record_number || item.license_number || 'Profile details unavailable'
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

export const AdminUsers = () => {
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')
  const [users, setUsers] = useState([])
  const [searchQuery, setSearchQuery] = useState('')
  const [roleFilter, setRoleFilter] = useState('all')
  const [statusFilter, setStatusFilter] = useState('all')
  const [page, setPage] = useState(1)

  useEffect(() => {
    let cancelled = false
    const activeParam = statusFilter === 'active' ? true : statusFilter === 'inactive' ? false : undefined
    const params = { limit: 50, ...(activeParam !== undefined ? { is_active: activeParam } : {}) }

    const listByType = async (type) => {
      try {
        const response = await usersAPI.list(type, params)
        return { type, data: unwrapList(response), error: '' }
      } catch (err) {
        return { type, data: [], error: getApiErrorMessage(err, `Failed to load ${type}.`) }
      }
    }

    const load = async () => {
      setLoading(true)
      setError('')
      const [patients, doctors, administrators] = await Promise.all([
        listByType('patients'),
        listByType('doctors'),
        listByType('administrators'),
      ])

      if (!cancelled) {
        const rows = [
          ...administrators.data.map((i) => normalizeUserRecord('administrators', i)),
          ...doctors.data.map((i) => normalizeUserRecord('doctors', i)),
          ...patients.data.map((i) => normalizeUserRecord('patients', i)),
        ]

        const errors = [patients.error, doctors.error, administrators.error].filter(Boolean)
        setUsers(rows)
        setError(rows.length ? '' : errors[0] || 'Failed to load user table.')
        setLoading(false)
      }
    }
    load()
    return () => { cancelled = true }
  }, [statusFilter])

  useEffect(() => {
    setPage(1)
  }, [searchQuery, roleFilter, statusFilter])

  const filteredUsers = useMemo(() => {
    const q = searchQuery.trim().toLowerCase()
    return users.filter((user) => {
      const matchesRole = roleFilter === 'all' || user.role.toLowerCase() === roleFilter
      const matchesQuery = !q || [user.name, user.role, user.secondary, user.hospital, user.contact]
        .filter(Boolean)
        .some((v) => v.toLowerCase().includes(q))
      return matchesRole && matchesQuery
    })
  }, [roleFilter, searchQuery, users])

  const pageSize = 10
  const totalPages = Math.max(1, Math.ceil(filteredUsers.length / pageSize))
  const paginatedUsers = useMemo(() => {
    const start = (page - 1) * pageSize
    return filteredUsers.slice(start, start + pageSize)
  }, [filteredUsers, page])

  if (loading) return <SectionLoading />

  return (
    <>
      <ErrorBanner message={error} />

      <section className={styles.heroSection}>
        <div>
          <span className={styles.kicker}>User operations</span>
          <h2>Search and filter people records from one route-backed page</h2>
          <p>
            This page keeps user management as a real destination in the admin workspace, not just a
            scrolled section hidden inside the overview.
          </p>
        </div>
      </section>

      <section className={styles.panel}>
        <div className={styles.panelHeading}>
          <div>
            <h3>User Management</h3>
            <p>Unified view across administrators, doctors, and patients.</p>
          </div>
        </div>

        <div className={styles.filtersRow}>
          <label>
            <span>Search</span>
            <input
              type="search"
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              placeholder="Search by name, role, or contact..."
            />
          </label>
          <label>
            <span>Role</span>
            <select value={roleFilter} onChange={(e) => setRoleFilter(e.target.value)}>
              <option value="all">All roles</option>
              <option value="administrator">Administrators</option>
              <option value="doctor">Doctors</option>
              <option value="patient">Patients</option>
            </select>
          </label>
          <label>
            <span>Status</span>
            <select value={statusFilter} onChange={(e) => setStatusFilter(e.target.value)}>
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

        {paginatedUsers.length ? (
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
              <button type="button" onClick={() => setPage((c) => Math.max(1, c - 1))} disabled={page === 1}>Previous</button>
              <span>Page {page} of {totalPages}</span>
              <button type="button" onClick={() => setPage((c) => Math.min(totalPages, c + 1))} disabled={page === totalPages}>Next</button>
            </div>
          </>
        ) : (
          <EmptyPanel title="No users match these filters" message="Try adjusting the search or status filters." />
        )}
      </section>
    </>
  )
}

export default AdminUsers
