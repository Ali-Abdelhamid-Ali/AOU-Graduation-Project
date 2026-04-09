import { useEffect, useMemo, useState } from 'react'
import { useNavigate } from 'react-router-dom'

import { dashboardAPI } from '@/services/api'
import { getApiErrorMessage } from '@/utils/apiErrorUtils'
import { EmptyPanel, SectionLoading, ErrorBanner, HeroSection } from './SharedPanels'
import styles from './DoctorPanels.module.css'

export const DoctorPatients = () => {
  const navigate = useNavigate()
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')
  const [patients, setPatients] = useState([])
  const [searchQuery, setSearchQuery] = useState('')

  useEffect(() => {
    let cancelled = false
    const load = async () => {
      setLoading(true); setError('')
      try {
        const response = await dashboardAPI.getDoctorOverview()
        if (!cancelled) { setPatients(response.data?.recent_patients || []); setLoading(false) }
      } catch (err) {
        if (!cancelled) { setError(getApiErrorMessage(err, 'Failed to load patients.')); setLoading(false) }
      }
    }
    load()
    return () => { cancelled = true }
  }, [])

  const filtered = useMemo(() => {
    const q = searchQuery.trim().toLowerCase()
    if (!q) return patients
    return patients.filter((item) =>
      [item.name, item.mrn].filter(Boolean).some((v) => v.toLowerCase().includes(q))
    )
  }, [patients, searchQuery])

  if (loading) return <SectionLoading />

  return (
    <>
      <ErrorBanner message={error} />
      <HeroSection
        kicker="Patient roster"
        heading="Stay inside the assigned cohort before jumping to the global directory"
        body="This page keeps the most recent patient touchpoints in front of the doctor."
      />
      <article className={styles.panel}>
        <div className={styles.panelHeading}>
          <div><h3>My Patients</h3><p>Most recent unique patients associated with your active cases.</p></div>
        </div>
        <div style={{ padding: '0 1.5rem 1rem' }}>
          <input
            type="search"
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            placeholder="Search by name or MRN..."
            style={{ width: '100%', padding: '0.5rem 0.75rem', borderRadius: '6px', border: '1px solid var(--color-border, #333)', background: 'var(--color-surface, #1a1a2e)', color: 'inherit', fontSize: '0.875rem' }}
          />
        </div>
        {filtered.length ? (
          <div className={styles.patientList}>
            {filtered.map((item) => (
              <div key={item.id} className={styles.patientCard}>
                <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', flexWrap: 'wrap' }}>
                  <strong>{item.name}</strong>
                  {item.has_disability && (
                    <span
                      title={item.disability_notes || 'Disability / special accessibility needs'}
                      style={{
                        display: 'inline-flex',
                        alignItems: 'center',
                        gap: '0.25rem',
                        fontSize: '0.7rem',
                        fontWeight: 600,
                        padding: '2px 8px',
                        borderRadius: '999px',
                        background: 'rgba(251,191,36,0.15)',
                        color: '#f59e0b',
                        border: '1px solid rgba(251,191,36,0.35)',
                        letterSpacing: '0.02em',
                        whiteSpace: 'nowrap',
                        cursor: item.disability_notes ? 'help' : 'default',
                      }}
                    >
                      ♿ Accessibility
                    </span>
                  )}
                </div>
                <span>{item.mrn || 'MRN unavailable'}</span>
                <p>Last touchpoint: {item.last_visit_label}</p>
              </div>
            ))}
          </div>
        ) : (
          <EmptyPanel title="No patient matches your search" message="Try a different name, MRN, or clear the search field." />
        )}
      </article>
      <section className={styles.splitGrid}>
        <article className={styles.panel}>
          <div className={styles.panelHeading}><div><h3>Patient Actions</h3><p>Open related pages without losing the current workflow.</p></div></div>
          <div className={styles.actionGrid}>
            <button type="button" className={styles.actionCard} onClick={() => navigate('/doctor-dashboard/results')}>
              <strong>Open Results Inbox</strong>
              <p>Review unread ECG and MRI outputs related to your active patients.</p>
            </button>
          </div>
        </article>
      </section>
    </>
  )
}

export default DoctorPatients

