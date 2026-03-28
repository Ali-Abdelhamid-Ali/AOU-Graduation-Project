import { useState, useEffect } from 'react'
import { motion } from 'framer-motion'
import { useNavigate } from 'react-router-dom'

import { useAuth } from '@/store/AuthContext'
import { medicalService } from '@/services/medical.service'
import { Skeleton } from '@/components/ui/Skeleton'
import SkeletonText from '@/components/ui/SkeletonText'
import styles from './PatientResults.module.css'

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
      <div className={styles.header}>
        <h1 className={styles.title}>Medical Analysis Results</h1>
        <p className={styles.subtitle}>
          Review your clinical reports and AI-assisted findings in one place.
        </p>
        {error ? <p className={styles.subtitle}>{error}</p> : null}
      </div>

      <div className={styles.resultsGrid}>
        {results.map((result) => {
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
              <button
                className={styles.viewDetails}
                onClick={() =>
                  navigate(`/patient-results/${result.type}/${result.resultId}`)
                }
              >
                Open result details {'->'}
              </button>
            </motion.div>
          )
        })}
      </div>

      {results.length === 0 && (
        <div className={styles.emptyState}>
          <span className={styles.emptyIcon}>No data</span>
          <h3>No Results Found</h3>
          <p>When your medical tests are processed, they will appear here.</p>
        </div>
      )}
    </motion.div>
  )
}
