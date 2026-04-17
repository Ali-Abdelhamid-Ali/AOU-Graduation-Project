import { useEffect, useMemo, useState } from 'react'
import { useNavigate } from 'react-router-dom'

import { dashboardAPI } from '@/services/api'
import { getApiErrorMessage } from '@/utils/apiErrorUtils'
import { EmptyPanel, SectionLoading, ErrorBanner, HeroSection } from './SharedPanels'
import { ReportModal } from '@/components/clinical/ReportModal'
import { useAuth } from '@/store/AuthContext'
import styles from './DoctorPanels.module.css'

const renderSummaryText = (value) => {
  if (typeof value === 'string') {
    const cleaned = value.trim()
    return cleaned || 'Awaiting radiology review'
  }

  if (value && typeof value === 'object') {
    const name = value.name || value.class_name || 'MRI finding'
    const severity = value.severity ? `severity ${value.severity}` : null
    const percentage = value.percentage != null ? `${Number(value.percentage).toFixed(1)}% of study` : null
    const volume = value.volume_cm3 != null ? `${Number(value.volume_cm3).toFixed(2)} cm3` : null

    return [name, severity, percentage, volume].filter(Boolean).join(' • ')
  }

  return 'Awaiting radiology review'
}

export const DoctorResults = () => {
  const navigate = useNavigate()
  const { user } = useAuth()
  const [loading, setLoading]           = useState(true)
  const [error, setError]               = useState('')
  const [results, setResults]           = useState([])
  const [searchQuery, setSearchQuery]   = useState('')
  const [reportTarget, setReportTarget] = useState(null) // { result, resultType, patientId }

  useEffect(() => {
    let cancelled = false
    const load = async () => {
      setLoading(true); setError('')
      try {
        const response = await dashboardAPI.getDoctorOverview()
        if (!cancelled) { setResults(response.data?.pending_results || []); setLoading(false) }
      } catch (err) {
        if (!cancelled) { setError(getApiErrorMessage(err, 'Failed to load results.')); setLoading(false) }
      }
    }
    load()
    return () => { cancelled = true }
  }, [])

  const filtered = useMemo(() => {
    const q = searchQuery.trim().toLowerCase()
    if (!q) return results
    return results.filter((item) =>
      [item.patient_name, item.case_number, renderSummaryText(item.summary), item.type]
        .filter(Boolean).some((v) => v.toLowerCase().includes(q))
    )
  }, [results, searchQuery])

  const openReport = (item) => {
    const resultType = (item.type || '').toLowerCase().includes('mri') ? 'mri' : 'ecg'
    setReportTarget({ result: item, resultType, patientId: item.patient_id })
  }

  if (loading) return <SectionLoading />

  return (
    <>
      <ErrorBanner message={error} />
      <HeroSection
        kicker="Results inbox"
        heading="Review pending ECG and MRI studies from one honest queue"
        body="Both patient-initiated uploads and doctor-initiated uploads land here through the same diagnostic pathways."
      />
      <article className={styles.panel}>
        <div className={styles.panelHeading}>
          <div><h3>Pending Diagnostic Results</h3><p>Unread ECG and MRI analyses linked to your assigned cases.</p></div>
        </div>
        <div style={{ padding: '0 1.5rem 1rem' }}>
          <input
            type="search"
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            placeholder="Filter by patient, type, or case..."
            style={{ inlineSize: '100%', padding: '0.5rem 0.75rem', borderRadius: '6px', border: '1px solid var(--color-border, #333)', background: 'var(--color-surface, #1a1a2e)', color: 'inherit', fontSize: '0.875rem' }}
          />
        </div>
        {filtered.length ? (
          <div className={styles.resultList}>
            {filtered.map((item) => (
              <div key={item.id} className={styles.resultItem}>
                <div style={{ flex: 1 }}>
                  <div className={styles.resultHeading}>
                    <strong>{item.patient_name}</strong>
                    <span className={`${styles.badge} ${styles.toneInfo}`}>{item.type}</span>
                  </div>
                  <p>{renderSummaryText(item.summary)}</p>
                </div>
                <div className={styles.resultMeta}>
                  <span>{item.case_number || 'No case number'}</span>
                  <span>{item.time_ago}</span>
                </div>
                <button
                  className={styles.reportBtn}
                  onClick={() => openReport(item)}
                  title="Write / view clinical report"
                >
                  Write Report
                </button>
              </div>
            ))}
          </div>
        ) : (
          <EmptyPanel title="No pending results" message="All linked ECG and MRI results appear to be reviewed." />
        )}
      </article>
      <section className={styles.splitGrid}>
        <article className={styles.panel}>
          <div className={styles.panelHeading}><div><h3>Result Actions</h3><p>Continue into the right module based on the modality.</p></div></div>
          <div className={styles.actionGrid}>
            <button type="button" className={styles.actionCard} onClick={() => navigate('/ecg-analysis')}>
              <strong>Open ECG Review</strong><p>Upload, analyze, and review waveform results.</p>
            </button>
            <button type="button" className={styles.actionCard} onClick={() => navigate('/mri-analysis')}>
              <strong>Open MRI Review</strong><p>Run segmentation and inspect imaging artifacts.</p>
            </button>
          </div>
        </article>
      </section>

      {/* ── Report Modal ── */}
      {reportTarget && (
        <ReportModal
          result={reportTarget.result}
          resultType={reportTarget.resultType}
          patientId={reportTarget.patientId}
          doctorId={user?.profile?.id}
          onClose={() => setReportTarget(null)}
          onSaved={() => setReportTarget(null)}
        />
      )}
    </>
  )
}

export default DoctorResults
