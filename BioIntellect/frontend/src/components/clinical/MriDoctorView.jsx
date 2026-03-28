import styles from './MriDoctorView.module.css'

const formatPercent = (value) =>
  typeof value === 'number' ? `${(value * 100).toFixed(1)}%` : 'N/A'

export const MriDoctorView = ({ result }) => {
  if (!result) return null

  const regions = Array.isArray(result.regions) ? result.regions : []
  const confidence =
    typeof result.confidence === 'number'
      ? result.confidence
      : result.confidenceBreakdown?.overall
  const highlightedRegions = regions.filter(
    (region) => region.present && Number(region.volume_cm3 || 0) > 0
  )

  return (
    <section className={styles.card}>
      <div className={styles.header}>
        <div>
          <h4 className={styles.title}>Clinician Summary</h4>
          <p className={styles.description}>
            Structured overview of the segmentation output before you review or sign it off.
          </p>
        </div>
        <span className={styles.badge} style={{ background: result.severity?.color || 'var(--color-secondary)' }}>
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
        <div className={styles.metricCard}>
          <div className={styles.metricLabel}>
            Review Required
          </div>
          <strong className={styles.metricValue}>
            {result.requiresReview ? 'Yes' : 'No'}
          </strong>
        </div>
      </div>

      {highlightedRegions.length > 0 && (
        <>
          <strong className={styles.regionTitle}>Detected Regions</strong>
          <ul className={styles.regionList}>
            {highlightedRegions.map((region, idx) => (
              <li key={`${region.class_id ?? idx}-${idx}`}>
                {region.class_name || `Class ${region.class_id}`}:&nbsp;
                {Number(region.volume_cm3 ?? 0).toFixed(2)} cm3
                {typeof region.percentage === 'number'
                  ? ` (${region.percentage.toFixed(1)}% of segmented volume)`
                  : ''}
              </li>
            ))}
          </ul>
        </>
      )}

      <div
        className={styles.interpretationBox}
      >
        <strong className={styles.interpretationTitle}>Clinical interpretation</strong>
        <p className={styles.interpretationText}>
          {result.aiInterpretation || result.severity?.description}
        </p>
      </div>
    </section>
  )
}
