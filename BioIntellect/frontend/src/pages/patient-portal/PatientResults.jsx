import { useState, useEffect, useMemo } from 'react'
import { motion, AnimatePresence } from 'framer-motion'
import { useNavigate } from 'react-router-dom'

import { useAuth } from '@/store/AuthContext'
import { medicalService } from '@/services/medical.service'
import { reportsAPI } from '@/services/api/endpoints'
import { Skeleton } from '@/components/ui/Skeleton'
import SkeletonText from '@/components/ui/SkeletonText'
import styles from './PatientResults.module.css'

/* ── AI Report Modal ─────────────────────────────────────────────────── */
const AIReportModal = ({ result, onClose }) => {
  if (!result) return null

  const lines = result.summary
    ? result.summary.split(/\.\s+/).filter(Boolean)
    : ['No detailed report available for this analysis.']

  return (
    <AnimatePresence>
      <motion.div
        key="backdrop"
        initial={{ opacity: 0 }}
        animate={{ opacity: 1 }}
        exit={{ opacity: 0 }}
        onClick={onClose}
        style={{
          position: 'fixed', inset: 0,
          background: 'rgba(0,0,0,0.72)',
          backdropFilter: 'blur(6px)',
          zIndex: 1000,
          display: 'flex', alignItems: 'center', justifyContent: 'center',
          padding: '1rem',
        }}
      >
        <motion.div
          key="modal"
          initial={{ opacity: 0, scale: 0.88, y: 32 }}
          animate={{ opacity: 1, scale: 1, y: 0, transition: { type: 'spring', stiffness: 340, damping: 28 } }}
          exit={{ opacity: 0, scale: 0.92, y: 20 }}
          onClick={(e) => e.stopPropagation()}
          style={{
            background: 'var(--color-surface, #12121f)',
            border: '1px solid rgba(108,99,255,0.35)',
            borderRadius: '18px',
            padding: '2rem',
            maxWidth: '560px',
            width: '100%',
            boxShadow: '0 8px 48px rgba(108,99,255,0.22), 0 2px 12px rgba(0,0,0,0.5)',
            position: 'relative',
            overflow: 'hidden',
          }}
        >
          {/* Glow ring */}
          <div style={{
            position: 'absolute', insetBlockStart: '-60px', insetInlineStart: '50%',
            transform: 'translateX(-50%)',
            width: '240px', height: '240px',
            background: 'radial-gradient(circle, rgba(108,99,255,0.18) 0%, transparent 70%)',
            pointerEvents: 'none',
          }} />

          {/* Header */}
          <div style={{ display: 'flex', alignItems: 'center', gap: '0.75rem', marginBottom: '1.25rem' }}>
            <motion.div
              animate={{ rotate: [0, 8, -8, 0] }}
              transition={{ duration: 2.5, repeat: Infinity, ease: 'easeInOut' }}
              style={{ fontSize: '1.75rem', lineHeight: 1 }}
            >
              🧠
            </motion.div>
            <div>
              <p style={{ fontSize: '0.7rem', fontWeight: 700, letterSpacing: '0.12em', color: 'var(--color-primary, #6c63ff)', textTransform: 'uppercase', margin: 0 }}>
                AI-Generated Report
              </p>
              <h2 style={{ margin: 0, fontSize: '1.1rem', fontWeight: 700 }}>{result.name}</h2>
            </div>
            <button
              onClick={onClose}
              aria-label="Close report"
              style={{
                marginInlineStart: 'auto', background: 'none', border: 'none',
                color: 'var(--color-text-muted, #888)', fontSize: '1.25rem',
                cursor: 'pointer', lineHeight: 1, padding: '0.25rem',
              }}
            >✕</button>
          </div>

          {/* Meta row */}
          <div style={{
            display: 'flex', gap: '0.5rem', flexWrap: 'wrap',
            marginBottom: '1.25rem',
          }}>
            <span style={{ fontSize: '0.72rem', padding: '3px 10px', borderRadius: '999px', background: 'rgba(108,99,255,0.15)', color: 'var(--color-primary, #6c63ff)', border: '1px solid rgba(108,99,255,0.3)' }}>
              {result.type === 'ecg' ? '⚡ ECG Analysis' : '🧩 MRI Segmentation'}
            </span>
            <span style={{ fontSize: '0.72rem', padding: '3px 10px', borderRadius: '999px', background: 'rgba(255,255,255,0.06)', color: 'var(--color-text-muted, #888)', border: '1px solid rgba(255,255,255,0.1)' }}>
              {result.date}
            </span>
            <span style={{ fontSize: '0.72rem', padding: '3px 10px', borderRadius: '999px', background: 'rgba(255,255,255,0.06)', color: 'var(--color-text-muted, #888)', border: '1px solid rgba(255,255,255,0.1)' }}>
              {result.status}
            </span>
          </div>

          {/* Report body */}
          <div style={{
            background: 'rgba(255,255,255,0.04)',
            borderRadius: '10px',
            padding: '1rem 1.25rem',
            marginBottom: '1.25rem',
            borderInlineStart: '3px solid var(--color-primary, #6c63ff)',
          }}>
            {lines.map((line, i) => (
              <motion.p
                key={i}
                initial={{ opacity: 0, x: -10 }}
                animate={{ opacity: 1, x: 0 }}
                transition={{ delay: i * 0.07 }}
                style={{ margin: i === 0 ? 0 : '0.5rem 0 0', fontSize: '0.875rem', lineHeight: 1.65, color: 'var(--color-text, #e0e0e0)' }}
              >
                {line}{line.endsWith('.') ? '' : '.'}
              </motion.p>
            ))}
          </div>

          {/* Disclaimer */}
          <p style={{ fontSize: '0.7rem', color: 'var(--color-text-muted, #888)', margin: 0, lineHeight: 1.55 }}>
            ⚠️ This report is generated by an AI model and is intended for informational purposes only. It does not replace the advice of a qualified healthcare professional.
          </p>
        </motion.div>
      </motion.div>
    </AnimatePresence>
  )
}

/* ── Animated AI Report Button ───────────────────────────────────────── */
const AIReportButton = ({ onClick }) => (
  <motion.button
    onClick={onClick}
    whileHover={{ scale: 1.04 }}
    whileTap={{ scale: 0.97 }}
    style={{
      position: 'relative',
      display: 'inline-flex',
      alignItems: 'center',
      gap: '0.45rem',
      padding: '0.5rem 1rem',
      borderRadius: '10px',
      border: 'none',
      background: 'linear-gradient(135deg, #6c63ff 0%, #a78bfa 100%)',
      color: '#fff',
      fontSize: '0.78rem',
      fontWeight: 700,
      letterSpacing: '0.03em',
      cursor: 'pointer',
      overflow: 'hidden',
      boxShadow: '0 2px 14px rgba(108,99,255,0.35)',
    }}
  >
    {/* Shimmer sweep */}
    <motion.span
      animate={{ x: ['-100%', '200%'] }}
      transition={{ duration: 2.2, repeat: Infinity, ease: 'easeInOut', repeatDelay: 1.5 }}
      style={{
        position: 'absolute', inset: 0,
        background: 'linear-gradient(90deg, transparent 0%, rgba(255,255,255,0.22) 50%, transparent 100%)',
        pointerEvents: 'none',
      }}
    />
    <motion.span
      animate={{ rotate: [0, 15, -15, 0] }}
      transition={{ duration: 3, repeat: Infinity, ease: 'easeInOut' }}
      style={{ fontSize: '0.9rem', lineHeight: 1 }}
    >
      🧠
    </motion.span>
    View AI Report
  </motion.button>
)

/* ── Clinical Reports Panel ──────────────────────────────────────────── */
const REPORT_TYPE_COLORS = {
  ecg_analysis:  { text: '#63b3ed', bg: 'rgba(99,179,237,0.12)', label: 'ECG' },
  mri_analysis:  { text: '#9a75ea', bg: 'rgba(154,117,234,0.12)', label: 'MRI' },
}

const ClinicalReports = ({ patientId }) => {
  const [reports, setReports]       = useState([])
  const [loading, setLoading]       = useState(true)
  const [expanded, setExpanded]     = useState(null)

  useEffect(() => {
    if (!patientId) { setLoading(false); return }
    let cancelled = false
    reportsAPI.listForPatient(patientId)
      .then((res) => { if (!cancelled) setReports(res.data || []) })
      .catch(() => {})
      .finally(() => { if (!cancelled) setLoading(false) })
    return () => { cancelled = true }
  }, [patientId])

  if (loading) return (
    <div style={{ marginTop: '3rem' }}>
      <Skeleton width="220px" height="24px" borderRadius="8px" style={{ marginBottom: '1rem' }} />
      <div style={{ display: 'grid', gap: '1rem' }}>
        {[1, 2].map((k) => <Skeleton key={k} width="100%" height="76px" borderRadius="14px" />)}
      </div>
    </div>
  )

  if (!reports.length) return (
    <div style={{ marginTop: '3rem' }}>
      <h2 style={{ fontSize: '1.3rem', fontWeight: 700, marginBottom: '0.5rem' }}>Clinical Reports</h2>
      <div style={{
        background: 'rgba(255,255,255,0.03)', border: '1px dashed var(--color-border-strong)',
        borderRadius: '14px', padding: '2rem', textAlign: 'center',
        color: 'var(--color-text-muted)', fontSize: '0.9rem',
      }}>
        No finalized clinical reports yet. Your doctor will publish them here once complete.
      </div>
    </div>
  )

  return (
    <div style={{ marginTop: '3rem' }}>
      <h2 style={{ fontSize: '1.3rem', fontWeight: 700, marginBottom: '1rem' }}>Clinical Reports</h2>
      <div style={{ display: 'flex', flexDirection: 'column', gap: '0.75rem' }}>
        {reports.map((r) => {
          const tone = REPORT_TYPE_COLORS[r.report_type] || { text: '#888', bg: 'rgba(255,255,255,0.06)', label: r.report_type || 'Report' }
          const isOpen = expanded === r.id
          const date = r.approved_at || r.created_at
          const dateLabel = date ? new Date(date).toLocaleDateString(undefined, { year: 'numeric', month: 'short', day: 'numeric' }) : ''
          return (
            <motion.div
              key={r.id}
              layout
              style={{
                background: 'var(--color-surface-elevated)',
                border: `1px solid ${isOpen ? tone.text + '55' : 'var(--color-border)'}`,
                borderRadius: '14px',
                overflow: 'hidden',
                transition: 'border-color 0.2s',
              }}
            >
              {/* Header row */}
              <button
                onClick={() => setExpanded(isOpen ? null : r.id)}
                style={{
                  width: '100%', display: 'flex', alignItems: 'center', gap: '0.75rem',
                  padding: '1rem 1.25rem', background: 'none', border: 'none', cursor: 'pointer',
                  color: 'inherit', textAlign: 'start',
                }}
              >
                <span style={{
                  padding: '0.2rem 0.65rem', borderRadius: '999px', fontSize: '0.68rem',
                  fontWeight: 700, letterSpacing: '0.06em', textTransform: 'uppercase',
                  background: tone.bg, color: tone.text, flexShrink: 0,
                }}>
                  {tone.label}
                </span>
                <div style={{ flex: 1, minWidth: 0 }}>
                  <strong style={{ fontSize: '0.9rem', display: 'block', overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>
                    {r.title || 'Clinical Report'}
                  </strong>
                  {r.summary && <p style={{ margin: 0, fontSize: '0.78rem', color: 'var(--color-text-muted)', overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>{r.summary}</p>}
                </div>
                <span style={{ fontSize: '0.72rem', color: 'var(--color-text-muted)', flexShrink: 0 }}>{dateLabel}</span>
                <span style={{ fontSize: '0.85rem', color: 'var(--color-text-muted)', marginLeft: '0.25rem', transition: 'transform 0.2s', transform: isOpen ? 'rotate(180deg)' : 'none' }}>▾</span>
              </button>

              {/* Expanded body */}
              <AnimatePresence initial={false}>
                {isOpen && (
                  <motion.div
                    key="body"
                    initial={{ height: 0, opacity: 0 }}
                    animate={{ height: 'auto', opacity: 1 }}
                    exit={{ height: 0, opacity: 0 }}
                    transition={{ duration: 0.22 }}
                    style={{ overflow: 'hidden' }}
                  >
                    <div style={{ padding: '0 1.25rem 1.25rem', borderTop: '1px solid var(--color-border-subtle)' }}>
                      <p style={{
                        marginTop: '1rem', fontSize: '0.875rem', lineHeight: 1.7,
                        color: 'var(--color-text-secondary, #b0b0c8)',
                        whiteSpace: 'pre-wrap',
                      }}>
                        {r.content?.body || r.summary || 'No detailed content available.'}
                      </p>
                      <p style={{ margin: '0.75rem 0 0', fontSize: '0.7rem', color: 'var(--color-text-muted)' }}>
                        ⚠️ This report was written by your treating physician. It is part of your official medical record.
                      </p>
                    </div>
                  </motion.div>
                )}
              </AnimatePresence>
            </motion.div>
          )
        })}
      </div>
    </div>
  )
}

const hasText = (value) => typeof value === 'string' && value.trim().length > 0

const formatResultDate = (value) => {
  if (!value) {
    return 'Pending'
  }

  return value.split('T')[0]
}

const getResultStatus = (result) => {
  if (result.is_reviewed) {
    return 'Reviewed'
  }

  if (result.analysis_completed_at) {
    return 'Awaiting Review'
  }

  return 'Awaiting Analysis'
}

const getEcgSummary = (result) => {
  if (hasText(result.primary_diagnosis)) {
    return result.primary_diagnosis.trim()
  }

  if (hasText(result.rhythm_classification)) {
    return result.rhythm_classification.trim()
  }

  if (hasText(result.ai_interpretation)) {
    return result.ai_interpretation.trim()
  }

  return result.analysis_completed_at
    ? 'Analysis completed. A clinical summary is not available yet.'
    : 'Analysis pending or incomplete.'
}

const getMriSummary = (result) => {
  if (hasText(result.ai_interpretation)) {
    return result.ai_interpretation.trim()
  }

  if (hasText(result.tumor_type)) {
    return result.tumor_type.trim()
  }

  return result.analysis_completed_at
    ? 'Analysis completed. Detailed findings are not attached yet.'
    : 'Analysis pending or incomplete.'
}

export const PatientResults = () => {
  const { currentUser } = useAuth()
  const navigate = useNavigate()
  const [loading, setLoading] = useState(true)
  const [results, setResults] = useState([])
  const [error, setError] = useState('')
  const [page, setPage] = useState(1)
  const [reportResult, setReportResult] = useState(null)
  const pageSize = 12

  useEffect(() => {
    const fetchRealResults = async () => {
      if (!currentUser?.id) {
        setLoading(false)
        return
      }

      setLoading(true)
      setError('')
      try {
        const [ecgResults, mriResults] = await Promise.all([
          medicalService.getEcgResults(currentUser.id),
          medicalService.getMriResults(currentUser.id),
        ])

        const ecgMapped = (ecgResults || []).map((result) => ({
          id: `ecg-${result.id}`,
          resultId: result.id,
          name: 'ECG Arrhythmia Scan',
          date: formatResultDate(result.analysis_completed_at),
          sortDate: result.analysis_completed_at || result.created_at || null,
          status: getResultStatus(result),
          summary: getEcgSummary(result),
          type: 'ecg',
        }))

        const mriMapped = (mriResults || []).map((result) => ({
          id: `mri-${result.id}`,
          resultId: result.id,
          name: 'Brain MRI Segmentation',
          date: formatResultDate(result.analysis_completed_at),
          sortDate: result.analysis_completed_at || result.created_at || null,
          status: getResultStatus(result),
          summary: getMriSummary(result),
          type: 'mri',
        }))

        const combined = [...ecgMapped, ...mriMapped].sort((a, b) => {
          const dateA = new Date(a.sortDate).getTime() || 0
          const dateB = new Date(b.sortDate).getTime() || 0
          return dateB - dateA
        })

        setResults(combined)
      } catch (error) {
        console.error('Error fetching clinical results:', error)
        setError(error.message || 'Unable to load your clinical results right now.')
      } finally {
        setLoading(false)
      }
    }

    fetchRealResults()
  }, [currentUser])

  useEffect(() => {
    setPage(1)
  }, [results.length])

  const totalPages = Math.max(1, Math.ceil(results.length / pageSize))
  const paginatedResults = useMemo(() => {
    const start = (page - 1) * pageSize
    return results.slice(start, start + pageSize)
  }, [page, results])

  const getStatusColor = (status) => {
    switch (status) {
      case 'Reviewed':
        return { text: 'var(--color-success-dark)', bg: 'var(--color-success-bg)' }
      case 'Awaiting Review':
        return { text: 'var(--color-primary)', bg: 'var(--color-primary-bg)' }
      case 'Awaiting Analysis':
        return { text: 'var(--color-warning-dark)', bg: 'var(--color-warning-bg)' }
      default:
        return { text: 'var(--color-text-muted)', bg: 'var(--color-surface-soft)' }
    }
  }

  if (loading) {
    return (
      <div className={styles.container}>
        <div className={styles.header}>
          <SkeletonText lines={1} width="300px" />
          <SkeletonText lines={1} width="500px" />
        </div>
        <div className={styles.resultsGrid}>
          {[1, 2, 3, 4].map((item) => (
            <div key={item} className={styles.resultCardSkeleton}>
              <div className={styles.cardHeader}>
                <Skeleton width="80px" height="20px" borderRadius="10px" />
                <Skeleton width="60px" height="24px" borderRadius="20px" />
              </div>
              <SkeletonText lines={1} width="100%" />
              <SkeletonText lines={2} width="100%" />
              <Skeleton width="120px" height="36px" borderRadius="12px" />
            </div>
          ))}
        </div>
      </div>
    )
  }

  return (
    <motion.div
      className={styles.container}
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
    >
      <AIReportModal result={reportResult} onClose={() => setReportResult(null)} />
      <div className={styles.header}>
        <h1 className={styles.title}>Medical Analysis Results</h1>
        <p className={styles.subtitle}>
          Review your clinical reports and AI-assisted findings in one place.
        </p>
        {error ? <p className={styles.subtitle}>{error}</p> : null}
      </div>

      <div className={styles.resultsGrid}>
        {paginatedResults.map((result) => {
          const statusColor = getStatusColor(result.status)

          return (
            <motion.div
              key={result.id}
              className={styles.resultCard}
              whileHover={{ y: -5, boxShadow: 'var(--shadow-lg)' }}
            >
              <div className={styles.cardHeader}>
                <span className={styles.date}>{result.date}</span>
                <span
                  className={styles.statusBadge}
                  style={{
                    backgroundColor: statusColor.bg,
                    color: statusColor.text,
                  }}
                >
                  {result.status}
                </span>
              </div>
              <h3 className={styles.resultName}>{result.name}</h3>
              <p className={styles.summary}>{result.summary}</p>
              <div style={{ display: 'flex', gap: '0.6rem', flexWrap: 'wrap', alignItems: 'center', marginTop: '0.5rem' }}>
                <AIReportButton onClick={() => setReportResult(result)} />
                <button
                  className={styles.viewDetails}
                  onClick={() =>
                    navigate(`/patient-results/${result.type}/${result.resultId}`)
                  }
                >
                  Open result details {'->'}
                </button>
              </div>
            </motion.div>
          )
        })}
      </div>

      {results.length > pageSize && (
        <div className={styles.paginationRow}>
          <button
            type="button"
            className={styles.viewDetails}
            onClick={() => setPage((current) => Math.max(1, current - 1))}
            disabled={page === 1}
          >
            Previous
          </button>
          <span>
            Page {page} of {totalPages}
          </span>
          <button
            type="button"
            className={styles.viewDetails}
            onClick={() => setPage((current) => Math.min(totalPages, current + 1))}
            disabled={page === totalPages}
          >
            Next
          </button>
        </div>
      )}

      {results.length === 0 && (
        <div className={styles.emptyState}>
          <span className={styles.emptyIcon}>No data</span>
          <h3>No Results Found</h3>
          <p>When your medical tests are processed, they will appear here.</p>
        </div>
      )}

      <ClinicalReports patientId={currentUser?.id} />
    </motion.div>
  )
}
