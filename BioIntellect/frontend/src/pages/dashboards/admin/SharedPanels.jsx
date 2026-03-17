import styles from '../AdminOperationsDashboard.module.css'

const toneClassMap = {
  info: styles.toneInfo,
  success: styles.toneSuccess,
  warning: styles.toneWarning,
  critical: styles.toneCritical,
  healthy: styles.toneSuccess,
}

export const StatCard = ({ item }) => (
  <article className={`${styles.metricCard} ${item.available === false ? styles.metricCardMuted : ''}`}>
    <div className={styles.metricCardHeader}>
      <span className={styles.metricLabel}>{item.label}</span>
      <span className={`${styles.badge} ${toneClassMap[item.tone] || styles.toneInfo}`}>
        {item.available === false ? 'Unavailable' : 'Live'}
      </span>
    </div>
    <strong className={styles.metricValue}>
      {item.available === false ? 'Not configured' : item.value}
    </strong>
    <p className={styles.metricHelper}>{item.helper}</p>
  </article>
)

export const EmptyPanel = ({ title, message }) => (
  <div className={styles.emptyPanel}>
    <strong>{title}</strong>
    <p>{message}</p>
  </div>
)

export const ChartPanel = ({ title, chart }) => {
  if (!chart?.available || !chart?.data?.length) {
    return (
      <article className={styles.panel}>
        <div className={styles.panelHeading}>
          <div>
            <h3>{title}</h3>
            <p>{chart?.message}</p>
          </div>
        </div>
        <EmptyPanel
          title={chart?.available ? 'No chart data yet' : 'Capability disabled'}
          message={
            chart?.message ||
            (chart?.available
              ? 'The source is active, but no records are available yet.'
              : 'No trusted data source is available.')
          }
        />
      </article>
    )
  }

  const maxValue = Math.max(...chart.data.map((item) => item.value), 1)

  return (
    <article className={styles.panel}>
      <div className={styles.panelHeading}>
        <div>
          <h3>{title}</h3>
          <p>{chart.message}</p>
        </div>
      </div>

      <div className={styles.barList}>
        {chart.data.map((item) => (
          <div key={item.label} className={styles.barRow}>
            <div className={styles.barMeta}>
              <span>{item.label}</span>
              <strong>{item.value}</strong>
            </div>
            <div className={styles.barTrack}>
              <span
                className={styles.barFill}
                style={{ width: `${Math.max(16, (item.value / maxValue) * 100)}%` }}
              />
            </div>
          </div>
        ))}
      </div>
    </article>
  )
}

export const ActivityList = ({ title, items, emptyMessage }) => (
  <article className={styles.panel}>
    <div className={styles.panelHeading}>
      <div>
        <h3>{title}</h3>
        <p>Live operational events pulled from system telemetry.</p>
      </div>
    </div>

    {items?.length ? (
      <div className={styles.feedList}>
        {items.map((item) => (
          <div key={item.id} className={styles.feedItem}>
            <span className={`${styles.feedDot} ${toneClassMap[item.severity] || styles.toneInfo}`} />
            <div className={styles.feedBody}>
              <strong>{item.title}</strong>
              <p>{item.message}</p>
            </div>
            <span className={styles.feedTime}>{item.time_ago || item.timestamp}</span>
          </div>
        ))}
      </div>
    ) : (
      <EmptyPanel title="No recent activity" message={emptyMessage} />
    )}
  </article>
)

export const SectionLoading = () => (
  <div className={styles.loadingGrid} data-testid="section-loading">
    {Array.from({ length: 8 }).map((_, index) => (
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

export const formatCapabilityLabel = (value = '') =>
  value
    .replace(/_/g, ' ')
    .replace(/\b\w/g, (character) => character.toUpperCase())

export { toneClassMap }
