import styles from './MriPatientView.module.css'

const formatPercent = (value) =>
  typeof value === 'number' ? `${(value * 100).toFixed(1)}%` : 'N/A'

export const MriPatientView = ({ result }) => {
  if (!result) return null

  const confidence =
    typeof result.confidence === 'number'
      ? result.confidence
      : result.confidenceBreakdown?.overall

  return (
    <section className={styles.card}>
      <div className={styles.header}>
        <div>
          <h4 className={styles.title}>Patient Summary</h4>
          <p className={styles.description}>
            This view simplifies the AI output into the main points you should discuss with
            your clinician.
          </p>
        </div>
        <span className={styles.badge} style={{ background: result.severity?.color || 'var(--color-primary)' }}>
          {result.severity?.label || 'Analysis Complete'}
        </span>
      </div>

      <div className={styles.metricGrid}>
        <div className={styles.metricCard}>
          <div className={styles.metricLabel}>
            Confidence
          </div>
          <strong className={styles.metricValue}>{formatPercent(confidence)}</strong>
        </div>
        <div className={styles.metricCard}>
          <div className={styles.metricLabel}>
            Total Volume
          </div>
          <strong className={styles.metricValue}>
            {Number(result.totalVolume ?? 0).toFixed(2)} cm3
          </strong>
        </div>
      </div>

      <div className={styles.suggestionBox}>
        <strong className={styles.suggestionTitle}>What the AI suggests</strong>
        <p className={styles.suggestionText}>
          {result.severity?.description || 'Consult your clinician for interpretation.'}
        </p>
      </div>

      <p className={styles.disclaimer}>
        {result.disclaimer ||
          'This output is for clinical decision support and should not be treated as a final diagnosis.'}
      </p>
    </section>
  )
}
