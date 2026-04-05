import { useEffect, useMemo, useState } from 'react'
import { useNavigate } from 'react-router-dom'

import { patientsAPI } from '@/services/api'
import { getApiErrorMessage } from '@/utils/apiErrorUtils'
import { EmptyPanel, SectionLoading, ErrorBanner } from './SharedPanels'
import styles from './AdminPanels.module.css'

const unwrapList = (response) => {
  if (Array.isArray(response)) return response
  if (Array.isArray(response?.data)) return response.data
  if (Array.isArray(response?.data?.data)) return response.data.data
  return []
}

const normalizePatientRecord = (item = {}) => ({
  id: item.id || item.user_id || item.mrn,
  name: item.full_name || [item.first_name, item.last_name].filter(Boolean).join(' ') || 'Unnamed patient',
  mrn: item.mrn || 'MRN unavailable',
  phone: item.phone || 'No phone on record',
  hospital: item.hospital_name || item.hospital_id || 'Unassigned facility',
  gender: item.gender || 'Unspecified',
  isActive: item.is_active !== false,
})

export const AdminPatients = () => {
  const navigate = useNavigate()
  const pageSize = 10
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')
  const [patients, setPatients] = useState([])
  const [searchQuery, setSearchQuery] = useState('')
  const [statusFilter, setStatusFilter] = useState('all')
  const [page, setPage] = useState(1)
  const [total, setTotal] = useState(0)

  useEffect(() => {
    let cancelled = false
    const activeParam = statusFilter === 'active' ? true : statusFilter === 'inactive' ? false : undefined
    const offset = (page - 1) * pageSize

    const load = async () => {
      setLoading(true)
      setError('')
      try {
        const response = await patientsAPI.listPaged({
          limit: pageSize,
          offset,
          ...(searchQuery.trim() ? { search: searchQuery.trim() } : {}),
          ...(activeParam !== undefined ? { is_active: activeParam } : {}),
        })
        if (!cancelled) {
          setPatients(unwrapList(response).map(normalizePatientRecord))
          setTotal(Number(response?.pagination?.total || 0))
          setLoading(false)
        }
      } catch (err) {
        if (!cancelled) {
          setError(getApiErrorMessage(err, 'Failed to load patient registry.'))
          setLoading(false)
        }
      }
    }
    load()
    return () => { cancelled = true }
  }, [statusFilter, page, searchQuery])

  useEffect(() => {
    setPage(1)
  }, [searchQuery, statusFilter])

  const totalPages = Math.max(1, Math.ceil(total / pageSize))
  const paginatedPatients = useMemo(() => patients, [patients])

  if (loading) return <SectionLoading />

  return (
    <>
      <ErrorBanner message={error} />

      <section className={styles.heroSection}>
        <div>
          <span className={styles.kicker}>Patient registry</span>
          <h2>Review the live patient snapshot before moving into detailed editing</h2>
          <p>
            This page gives administration a route-backed patient registry view inside the same
            workspace shell. When deeper editing is needed, the full legacy directory remains available.
          </p>
        </div>
      </section>

      <section className={styles.panel}>
        <div className={styles.panelHeading}>
          <div>
            <h3>Patient Directory Snapshot</h3>
            <p>Live patient registry view scoped to the signed-in operational role.</p>
          </div>
        </div>

        <div className={styles.filtersRow}>
          <label>
            <span>Search</span>
            <input
              type="search"
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              placeholder="Search by name, MRN, or phone..."
            />
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
            <strong>{total}</strong>
            <span>patients in scope</span>
          </div>
        </div>

        {paginatedPatients.length ? (
          <>
            <div className={styles.tableWrap}>
              <table className={styles.table} role="table" aria-label="Admin patients table">
                <thead>
                  <tr>
                    <th scope="col">Patient</th>
                    <th scope="col">MRN</th>
                    <th scope="col">Contact</th>
                    <th scope="col">Facility</th>
                    <th scope="col">Status</th>
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
              <button type="button" onClick={() => setPage((c) => Math.max(1, c - 1))} disabled={page === 1}>Previous</button>
              <span>Page {page} of {totalPages}</span>
              <button type="button" onClick={() => setPage((c) => Math.min(totalPages, c + 1))} disabled={page === totalPages}>Next</button>
            </div>
          </>
        ) : (
          <EmptyPanel title="No patients match the active filters" message="Try clearing the search box or broadening the status scope." />
        )}
      </section>

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
      </section>
    </>
  )
}

export default AdminPatients

