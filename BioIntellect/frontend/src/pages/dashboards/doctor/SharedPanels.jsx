import styles from '../DoctorDashboard.module.css'

const toneClassMap = {
  info: styles.toneInfo,
  success: styles.toneSuccess,
  warning: styles.toneWarning,
  critical: styles.toneCritical,
  normal: styles.toneInfo,
  high: styles.toneWarning,
  urgent: styles.toneCritical,
}

export const MetricCard = ({ item }) => (
  <article className={styles.metricCard}>
    <span className={styles.metricLabel}>{item.label}</span>
    <strong className={styles.metricValue}>{item.value}</strong>
    <p className={styles.metricHelper}>{item.helper}</p>
  </article>
)

export const EmptyPanel = ({ title, message }) => (
  <div className={styles.emptyPanel}>
    <strong>{title}</strong>
    <p>{message}</p>
  </div>
)

export const SectionLoading = () => (
  <div className={styles.loadingGrid} data-testid="doctor-section-loading">
    {Array.from({ length: 6 }).map((_, index) => (
      <div key={index} className={`skeleton ${styles.loadingCard}`} />
    ))}
  </div>
)

export const ErrorBanner = ({ message }) =>
  message ? (
    <article className={styles.errorBanner}>
      <strong>Unable to load this section</strong>
      <p>{message}</p>
    </article>
  ) : null

export const HeroSection = ({ kicker, heading, body, capabilities }) => (
  <section className={styles.heroSection}>
    <div>
      <span className={styles.kicker}>{kicker}</span>
      <h2>{heading}</h2>
      <p>{body}</p>
    </div>
    {capabilities ? (
      <div className={styles.heroCapabilities}>
        {Object.entries(capabilities).map(([key, enabled]) => (
          <span
            key={key}
            className={`${styles.badge} ${enabled ? styles.toneSuccess : styles.toneWarning}`}
          >
            {key.replace(/_/g, ' ').replace(/\b\w/g, (c) => c.toUpperCase())}: {enabled ? 'available' : 'pending'}
          </span>
        ))}
      </div>
    ) : null}
  </section>
)

export { toneClassMap }
