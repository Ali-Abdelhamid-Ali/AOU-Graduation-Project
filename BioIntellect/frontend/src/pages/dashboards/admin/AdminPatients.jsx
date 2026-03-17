import { useEffect, useMemo, useState } from 'react'
import { useNavigate } from 'react-router-dom'

import { patientsAPI } from '@/services/api'
import { getApiErrorMessage } from '@/utils/apiErrorUtils'
import { EmptyPanel, SectionLoading, ErrorBanner } from './SharedPanels'
import styles from '../AdminOperationsDashboard.module.css'

const unwrapList = (response) => {
  if (Array.isArray(response)) return response
  if (Array.isArray(response?.data)) return response.data
  if (Array.isArray(response?.data?.data)) return response.data.data
  return []
}

const normalizePatientRecord = (item = {}) => ({
  id: item.id || item.user_id || item.mrn || item.medical_record_number,
  name: item.full_name || [item.first_name, item.last_name].filter(Boolean).join(' ') || 'Unnamed patient',
  mrn: item.mrn || item.medical_record_number || 'MRN unavailable',
  phone: item.phone || 'No phone on record',
  hospital: item.hospital_name || item.hospital_id || 'Unassigned facility',
  gender: item.gender || 'Unspecified',
  isActive: item.is_active !== false,
})

export const AdminPatients = () => {
  const navigate = useNavigate()
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')
  const [patients, setPatients] = useState([])
  const [searchQuery, setSearchQuery] = useState('')
  const [statusFilter, setStatusFilter] = useState('all')
  const [page, setPage] = useState(1)

  useEffect(() => {
    let cancelled = false
    const activeParam = statusFilter === 'active' ? true : statusFilter === 'inactive' ? false : undefined

    const load = async () => {
      setLoading(true)
      setError('')
      try {
        const response = await patientsAPI.list({
          limit: 100,
          ...(activeParam !== undefined ? { is_active: activeParam } : {}),
        })
        if (!cancelled) {
          setPatients(unwrapList(response).map(normalizePatientRecord))
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
  }, [statusFilter])

  useEffect(() => {
    setPage(1)
  }, [searchQuery, statusFilter])

  const filteredPatients = useMemo(() => {
    const q = searchQuery.trim().toLowerCase()
    return patients.filter((p) => {
      if (!q) return true
      return [p.name, p.mrn, p.phone, p.hospital, p.gender]
        .filter(Boolean)
        .some((v) => v.toLowerCase().includes(q))
    })
  }, [patients, searchQuery])

  const pageSize = 10
  const totalPages = Math.max(1, Math.ceil(filteredPatients.length / pageSize))
  const paginatedPatients = useMemo(() => {
    const start = (page - 1) * pageSize
    return filteredPatients.slice(start, start + pageSize)
  }, [filteredPatients, page])

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
            <strong>{filteredPatients.length}</strong>
            <span>patients in scope</span>
          </div>
        </div>

        {paginatedPatients.length ? (
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
            <button type="button" className={styles.actionCard} onClick={() => navigate('/patient-directory')}>
              <strong>Open Full Directory</strong>
              <p>Launch the deeper patient management view for search and profile editing.</p>
            </button>
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
