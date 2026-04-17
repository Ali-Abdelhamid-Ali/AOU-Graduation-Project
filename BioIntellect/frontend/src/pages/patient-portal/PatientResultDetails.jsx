import { useEffect, useState } from 'react'
import { motion, AnimatePresence } from 'framer-motion'
import { useNavigate, useParams } from 'react-router-dom'

import { medicalService } from '@/services/medical.service'
import { reportsAPI } from '@/services/api/endpoints'
import { Skeleton } from '@/components/ui/Skeleton'
import SkeletonText from '@/components/ui/SkeletonText'
import styles from './PatientResultDetails.module.css'

const formatDateTime = (value) => {
  if (!value) {
    return 'Not available'
  }

  const parsed = new Date(value)
  if (Number.isNaN(parsed.getTime())) {
    return value
  }

  return parsed.toLocaleString()
}

const formatPercent = (value) => {
  if (value === null || value === undefined || Number.isNaN(Number(value))) {
    return 'Not available'
  }

  const normalized = Number(value)
  return `${normalized <= 1 ? normalized * 100 : normalized}%`
}

const formatMetricValue = (value) => {
  if (value === null || value === undefined || value === '') {
    return 'Not available'
  }

  if (typeof value === 'boolean') {
    return value ? 'Yes' : 'No'
  }

  if (Array.isArray(value)) {
    return value.join(', ') || 'Not available'
  }

  if (typeof value === 'object') {
    return JSON.stringify(value)
  }

  return String(value)
}

const hasText = (value) => typeof value === 'string' && value.trim().length > 0

const summarizeObject = (item = {}) =>
  Object.entries(item)
    .filter(([, value]) => value !== null && value !== undefined && value !== '')
    .slice(0, 4)
    .map(([key, value]) => `${key.replace(/_/g, ' ')}: ${formatMetricValue(value)}`)
    .join(' | ')

const renderMetricValue = (item) => {
  if (item.variant === 'badge') {
    return (
      <span className={styles.unavailableBadge}>
        {item.value}
      </span>
    )
  }

  return formatMetricValue(item.value)
}

/* ── Doctor Report Popup ─────────────────────────────────────────────── */
const DoctorReportModal = ({ resultType, resultId, onClose }) => {
  const [report, setReport] = useState(null)
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    let cancelled = false
    reportsAPI.getByResult(resultType, resultId)
      .then((res) => { if (!cancelled) setReport(res.data || null) })
      .catch(() => {})
      .finally(() => { if (!cancelled) setLoading(false) })
    return () => { cancelled = true }
  }, [resultType, resultId])

  const typeTone = resultType === 'ecg'
    ? { color: '#63b3ed', bg: 'rgba(99,179,237,0.12)', label: 'ECG' }
    : { color: '#9a75ea', bg: 'rgba(154,117,234,0.12)', label: 'MRI' }

  const date = report?.approved_at || report?.created_at
  const dateLabel = date
    ? new Date(date).toLocaleDateString(undefined, { year: 'numeric', month: 'long', day: 'numeric' })
    : ''

  return (
    <AnimatePresence>
      <motion.div
        key="backdrop"
        initial={{ opacity: 0 }}
        animate={{ opacity: 1 }}
        exit={{ opacity: 0 }}
        onClick={onClose}
        style={{
          position: 'fixed', inset: 0, zIndex: 9000,
          background: 'rgba(0,0,0,0.72)', backdropFilter: 'blur(6px)',
          display: 'flex', alignItems: 'center', justifyContent: 'center', padding: '1rem',
        }}
      >
        <motion.div
          key="modal"
          initial={{ opacity: 0, y: 32, scale: 0.97 }}
          animate={{ opacity: 1, y: 0, scale: 1, transition: { type: 'spring', stiffness: 320, damping: 28 } }}
          exit={{ opacity: 0, y: 20, scale: 0.97 }}
          onClick={(e) => e.stopPropagation()}
          style={{
            background: 'var(--color-surface, #12121e)',
            border: '1px solid var(--color-border, #2a2a40)',
            borderRadius: '16px', width: '100%', maxWidth: '680px',
            maxHeight: '88vh', display: 'flex', flexDirection: 'column',
            overflow: 'hidden', boxShadow: '0 24px 64px rgba(0,0,0,0.6)',
          }}
        >
          {/* Header */}
          <div style={{ padding: '1.5rem 2rem 1rem', borderBottom: '1px solid var(--color-border, #2a2a40)', position: 'relative' }}>
            <div style={{ display: 'flex', gap: '0.5rem', marginBottom: '0.5rem' }}>
              <span style={{ padding: '0.2rem 0.65rem', borderRadius: '999px', fontSize: '0.7rem', fontWeight: 700, letterSpacing: '0.06em', textTransform: 'uppercase', background: typeTone.bg, color: typeTone.color }}>
                {typeTone.label}
              </span>
              {report?.is_final && (
                <span style={{ padding: '0.2rem 0.65rem', borderRadius: '999px', fontSize: '0.7rem', fontWeight: 700, background: 'rgba(72,199,142,0.15)', color: '#48c78e' }}>
                  Finalized
                </span>
              )}
            </div>
            <h2 style={{ margin: '0 0 0.2rem', fontSize: '1.2rem', fontWeight: 700, color: 'var(--color-text-primary, #e8e8f0)' }}>
              {report?.title || 'Clinical Report'}
            </h2>
            <p style={{ margin: 0, fontSize: '0.8rem', color: 'var(--color-text-muted, #888)' }}>
              {dateLabel || 'Written by your treating physician'}
            </p>
            <button
              onClick={onClose}
              style={{ position: 'absolute', top: '1.25rem', right: '1.25rem', background: 'none', border: 'none', color: 'var(--color-text-muted, #888)', fontSize: '1.1rem', cursor: 'pointer', padding: '0.25rem 0.5rem', borderRadius: '6px' }}
            >✕</button>
          </div>

          {/* Body */}
          <div style={{ flex: 1, overflowY: 'auto', padding: '1.5rem 2rem', display: 'flex', flexDirection: 'column', gap: '1.25rem' }}>
            {loading ? (
              <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'center', gap: '1rem', padding: '3rem', color: 'var(--color-text-muted, #888)' }}>
                <div style={{ width: 28, height: 28, border: '3px solid rgba(99,179,237,0.2)', borderTopColor: '#63b3ed', borderRadius: '50%', animation: 'spin 0.7s linear infinite' }} />
                <p style={{ margin: 0, fontSize: '0.9rem' }}>Loading report…</p>
              </div>
            ) : !report ? (
              <div style={{ textAlign: 'center', padding: '3rem 1rem', color: 'var(--color-text-muted, #888)' }}>
                <p style={{ fontSize: '1.1rem', fontWeight: 600, marginBottom: '0.5rem' }}>No report yet</p>
                <p style={{ fontSize: '0.875rem', margin: 0 }}>
                  Your doctor has not published a clinical report for this result yet. Check back after your consultation.
                </p>
              </div>
            ) : (
              <>
                {report.summary && (
                  <div style={{ background: 'rgba(99,179,237,0.06)', border: '1px solid rgba(99,179,237,0.18)', borderRadius: '10px', padding: '0.9rem 1.1rem' }}>
                    <p style={{ margin: '0 0 0.35rem', fontSize: '0.7rem', fontWeight: 700, letterSpacing: '0.08em', textTransform: 'uppercase', color: '#63b3ed' }}>Clinical Impression</p>
                    <p style={{ margin: 0, fontSize: '0.875rem', color: 'var(--color-text-secondary, #b0b0c8)', lineHeight: 1.65 }}>{report.summary}</p>
                  </div>
                )}
                <div>
                  <p style={{ margin: '0 0 0.5rem', fontSize: '0.75rem', fontWeight: 700, letterSpacing: '0.06em', textTransform: 'uppercase', color: 'var(--color-text-muted, #888)' }}>Full Report</p>
                  <p style={{ margin: 0, fontSize: '0.875rem', color: 'var(--color-text-secondary, #b0b0c8)', lineHeight: 1.75, whiteSpace: 'pre-wrap' }}>
                    {report.content?.body || 'No detailed report content was added.'}
                  </p>
                </div>
                <p style={{ margin: 0, fontSize: '0.7rem', color: 'var(--color-text-muted, #888)', lineHeight: 1.55 }}>
                  ⚠️ This report was prepared by your treating physician and forms part of your official medical record. It is provided for your information and does not replace clinical consultation.
                </p>
              </>
            )}
          </div>

          {/* Footer */}
          <div style={{ padding: '1rem 2rem', borderTop: '1px solid var(--color-border, #2a2a40)', display: 'flex', justifyContent: 'flex-end' }}>
            <button
              onClick={onClose}
              style={{ padding: '0.55rem 1.4rem', borderRadius: '8px', border: 'none', background: 'var(--color-border, #2a2a40)', color: 'var(--color-text-primary, #e8e8f0)', fontWeight: 600, fontSize: '0.85rem', cursor: 'pointer' }}
            >
              Close
            </button>
          </div>
        </motion.div>
      </motion.div>
    </AnimatePresence>
  )
}

export const PatientResultDetails = () => {
  const navigate = useNavigate()
  const { resultType, resultId } = useParams()
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')
  const [result, setResult] = useState(null)
  const [showReport, setShowReport] = useState(false)

  useEffect(() => {
    const fetchResult = async () => {
      if (!resultId || !['ecg', 'mri'].includes(resultType)) {
        setError('Invalid result reference.')
        setLoading(false)
        return
      }

      setLoading(true)
      setError('')

      try {
        const data =
          resultType === 'ecg'
            ? await medicalService.getEcgResultById(resultId)
            : await medicalService.getMriResultById(resultId)

        setResult(data)
      } catch (err) {
        setError(err.message || 'Failed to load result details.')
      } finally {
        setLoading(false)
      }
    }

    fetchResult()
  }, [resultId, resultType])

  if (loading) {
    return (
      <div className={styles.container}>
        <div className={styles.header}>
          <SkeletonText lines={1} width="240px" />
          <SkeletonText lines={1} width="420px" />
        </div>
        <div className={styles.grid}>
          {[1, 2, 3].map((item) => (
            <div key={item} className={styles.card}>
              <SkeletonText lines={1} width="180px" />
              <SkeletonText lines={4} width="100%" />
              <Skeleton height="140px" borderRadius="20px" />
            </div>
          ))}
        </div>
      </div>
    )
  }

  if (error || !result) {
    return (
      <div className={styles.container}>
        <div className={styles.errorState}>
          <h1>Result Unavailable</h1>
          <p>{error || 'The requested result could not be found.'}</p>
          <button type="button" className={styles.secondaryButton} onClick={() => navigate('/patient-results')}>
            {'<-'} Back to results
          </button>
        </div>
      </div>
    )
  }

  const isEcg = resultType === 'ecg'
  const title = isEcg ? 'ECG Result Details' : 'MRI Result Details'
  const analysisCompleted = Boolean(result.analysis_completed_at)
  const headline = isEcg
    ? result.primary_diagnosis ||
      result.rhythm_classification ||
      (hasText(result.ai_interpretation) ? result.ai_interpretation.trim() : null) ||
      'ECG analysis details unavailable'
    : hasText(result.tumor_type)
      ? result.tumor_type.trim()
      : result.tumor_detected === true
        ? 'Finding reported'
        : result.tumor_detected === false
          ? 'No abnormality flagged'
          : 'MRI analysis details unavailable'

  const statusLabel = result.is_reviewed
    ? 'Reviewed'
    : analysisCompleted
      ? 'Awaiting Review'
      : 'Analysis Pending'

  const heroText = hasText(result.ai_interpretation)
    ? result.ai_interpretation.trim()
    : analysisCompleted
      ? 'The analysis record is available, but no narrative interpretation was attached.'
      : 'Analysis pending or incomplete. A narrative interpretation is not available yet.'

  const metricItems = isEcg
    ? [
        { label: 'Heart rate', value: result.heart_rate ? `${result.heart_rate} bpm` : null },
        { label: 'HRV', value: result.heart_rate_variability },
        { label: 'Rhythm confidence', value: formatPercent(result.rhythm_confidence) },
        { label: 'Risk score', value: formatPercent(result.risk_score) },
        { label: 'PR interval', value: result.pr_interval ? `${result.pr_interval} ms` : null },
        { label: 'QRS duration', value: result.qrs_duration ? `${result.qrs_duration} ms` : null },
        { label: 'QT interval', value: result.qt_interval ? `${result.qt_interval} ms` : null },
        { label: 'QTc interval', value: result.qtc_interval ? `${result.qtc_interval} ms` : null },
      ]
    : [
        { label: 'Tumor detected', value: result.tumor_detected },
        { label: 'Confidence score', value: formatPercent(result.confidence_score) },
        { label: 'Severity score', value: result.severity_score },
        result.segmentation_mask_path
          ? { label: 'Segmentation mask', value: result.segmentation_mask_path }
          : {
              label: 'Segmentation mask',
              value: 'Mask not available',
              variant: 'badge',
            },
        {
          label: 'Abnormalities',
          value: Array.isArray(result.detected_abnormalities)
            ? result.detected_abnormalities.length
            : 0,
        },
        {
          label: 'Segmented regions',
          value: Array.isArray(result.segmented_regions)
            ? result.segmented_regions.length
            : 0,
        },
      ]

  const recommendationItems = Array.isArray(result.ai_recommendations)
    ? result.ai_recommendations
    : []

  const findingItems = isEcg
    ? Array.isArray(result.detected_conditions)
      ? result.detected_conditions
      : []
    : Array.isArray(result.detected_abnormalities)
      ? result.detected_abnormalities
      : []

  return (
    <motion.div
      className={styles.container}
      initial={{ opacity: 0, y: 16 }}
      animate={{ opacity: 1, y: 0 }}
    >
      {showReport && (
        <DoctorReportModal
          resultType={resultType}
          resultId={resultId}
          onClose={() => setShowReport(false)}
        />
      )}

      <div className={styles.header}>
        <div>
          <button
            type="button"
            className={styles.backLink}
            onClick={() => navigate('/patient-results')}
          >
            {'<-'} Back to results
          </button>
          <h1 className={styles.title}>{title}</h1>
          <p className={styles.subtitle}>
            Review the AI summary, clinical review status, and supporting metrics.
          </p>
        </div>
        <div className={styles.statusBlock}>
          <span className={styles.statusLabel}>{statusLabel}</span>
          <span className={styles.timestamp}>
            Updated {formatDateTime(result.updated_at || result.analysis_completed_at)}
          </span>
          <button
            type="button"
            onClick={() => setShowReport(true)}
            style={{
              marginTop: '0.75rem',
              padding: '0.5rem 1.1rem',
              borderRadius: '8px',
              border: '1px solid rgba(99,179,237,0.35)',
              background: 'rgba(99,179,237,0.08)',
              color: '#63b3ed',
              fontSize: '0.82rem',
              fontWeight: 600,
              cursor: 'pointer',
              transition: 'background 0.15s',
            }}
          >
            View Doctor Report
          </button>
        </div>
      </div>

      <section className={styles.heroCard}>
        <div>
          <span className={styles.heroEyebrow}>
            {isEcg ? 'Electrocardiogram analysis' : 'MRI segmentation analysis'}
          </span>
          <h2 className={styles.heroTitle}>{headline}</h2>
          <p className={styles.heroText}>{heroText}</p>
        </div>
      </section>

      <div className={styles.grid}>
        <section className={styles.card}>
          <h3 className={styles.cardTitle}>Key Metrics</h3>
          <div className={styles.metricGrid}>
            {metricItems.map((item) => (
              <div key={item.label} className={styles.metricItem}>
                <span className={styles.metricLabel}>{item.label}</span>
                <strong className={styles.metricValue}>{renderMetricValue(item)}</strong>
              </div>
            ))}
          </div>
        </section>

        <section className={styles.card}>
          <h3 className={styles.cardTitle}>Clinical Review</h3>
          <div className={styles.reviewList}>
            <div className={styles.reviewRow}>
              <span>Reviewed by clinician</span>
              <strong>{result.is_reviewed ? 'Yes' : 'No'}</strong>
            </div>
            <div className={styles.reviewRow}>
              <span>Doctor agreement with AI</span>
              <strong>{formatMetricValue(result.doctor_agrees_with_ai)}</strong>
            </div>
            <div className={styles.reviewRow}>
              <span>Reviewed at</span>
              <strong>{formatDateTime(result.reviewed_at)}</strong>
            </div>
            <div className={styles.reviewNotes}>
              <span>Doctor notes</span>
              <p>{result.doctor_notes || 'No clinician notes were added yet.'}</p>
            </div>
          </div>
        </section>

        <section className={styles.card}>
          <h3 className={styles.cardTitle}>AI Recommendations</h3>
          {recommendationItems.length > 0 ? (
            <div className={styles.list}>
              {recommendationItems.map((item, index) => (
                <div key={`${item}-${index}`} className={styles.listItem}>
                  {item}
                </div>
              ))}
            </div>
          ) : (
            <p className={styles.emptyCopy}>No AI recommendations were attached.</p>
          )}
        </section>

        <section className={styles.card}>
          <h3 className={styles.cardTitle}>
            {isEcg ? 'Detected Conditions' : 'Detected Findings'}
          </h3>
          {findingItems.length > 0 ? (
            <div className={styles.list}>
              {findingItems.map((item, index) => (
                <div key={index} className={styles.listItem}>
                  {summarizeObject(item)}
                </div>
              ))}
            </div>
          ) : (
            <p className={styles.emptyCopy}>No structured findings were attached.</p>
          )}
        </section>

        {!isEcg && (
          <section className={styles.card}>
            <h3 className={styles.cardTitle}>Segmentation Measurements</h3>
            {result.measurements && Object.keys(result.measurements).length > 0 ? (
              <div className={styles.metricGrid}>
                {Object.entries(result.measurements).map(([key, value]) => (
                  <div key={key} className={styles.metricItem}>
                    <span className={styles.metricLabel}>{key.replace(/_/g, ' ')}</span>
                    <strong className={styles.metricValue}>
                      {formatMetricValue(value)}
                    </strong>
                  </div>
                ))}
              </div>
            ) : (
              <p className={styles.emptyCopy}>No MRI measurements were returned.</p>
            )}
          </section>
        )}

        <section className={styles.card}>
          <h3 className={styles.cardTitle}>Technical Trace</h3>
          <div className={styles.reviewList}>
            <div className={styles.reviewRow}>
              <span>Model</span>
              <strong>{result.analyzed_by_model || 'Not available'}</strong>
            </div>
            <div className={styles.reviewRow}>
              <span>Model version</span>
              <strong>{result.model_version || 'Not available'}</strong>
            </div>
            <div className={styles.reviewRow}>
              <span>Processing time</span>
              <strong>
                {result.processing_time_ms
                  ? `${result.processing_time_ms} ms`
                  : 'Not available'}
              </strong>
            </div>
            <div className={styles.reviewRow}>
              <span>Created at</span>
              <strong>{formatDateTime(result.created_at)}</strong>
            </div>
          </div>
        </section>
      </div>
    </motion.div>
  )
}
