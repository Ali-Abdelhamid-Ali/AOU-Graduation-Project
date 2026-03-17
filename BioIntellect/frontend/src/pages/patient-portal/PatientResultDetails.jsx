import { useEffect, useState } from 'react'
import { motion } from 'framer-motion'
import { useNavigate, useParams } from 'react-router-dom'

import { medicalService } from '@/services/medical.service'
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

export const PatientResultDetails = () => {
  const navigate = useNavigate()
  const { resultType, resultId } = useParams()
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')
  const [result, setResult] = useState(null)

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
