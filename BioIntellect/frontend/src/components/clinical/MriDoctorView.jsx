const cardBase = {
  marginTop: '1rem',
  padding: '1.2rem',
  borderRadius: '1rem',
  border: '1px solid rgba(16, 185, 129, 0.22)',
  background:
    'linear-gradient(180deg, rgba(236, 253, 245, 0.98) 0%, rgba(255, 255, 255, 0.98) 100%)',
  color: '#111827',
  boxShadow: '0 16px 30px rgba(15, 23, 42, 0.06)',
}

const metricGrid = {
  display: 'grid',
  gridTemplateColumns: 'repeat(3, minmax(0, 1fr))',
  gap: '0.75rem',
  marginTop: '1rem',
}

const metricCard = {
  padding: '0.85rem',
  borderRadius: '0.9rem',
  background: 'rgba(220, 252, 231, 0.58)',
  border: '1px solid rgba(16, 185, 129, 0.12)',
}

const regionList = {
  margin: '0.9rem 0 0',
  paddingLeft: '1.1rem',
  color: '#334155',
  lineHeight: 1.6,
}

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
    <section style={cardBase}>
      <div style={{ display: 'flex', justifyContent: 'space-between', gap: '1rem' }}>
        <div>
          <h4 style={{ margin: 0, fontSize: '1rem' }}>Clinician Summary</h4>
          <p style={{ margin: '0.35rem 0 0', color: '#475569', lineHeight: 1.6 }}>
            Structured overview of the segmentation output before you review or sign it off.
          </p>
        </div>
        <span
          style={{
            alignSelf: 'flex-start',
            padding: '0.4rem 0.8rem',
            borderRadius: '999px',
            background: result.severity?.color || '#059669',
            color: '#fff',
            fontSize: '0.78rem',
            fontWeight: 700,
          }}
        >
          {result.severity?.label || 'Analysis Complete'}
        </span>
      </div>

      <div style={metricGrid}>
        <div style={metricCard}>
          <div style={{ fontSize: '0.74rem', color: '#64748b', textTransform: 'uppercase' }}>
            Confidence
          </div>
          <strong style={{ fontSize: '1.05rem' }}>{formatPercent(confidence)}</strong>
        </div>
        <div style={metricCard}>
          <div style={{ fontSize: '0.74rem', color: '#64748b', textTransform: 'uppercase' }}>
            Total Volume
          </div>
          <strong style={{ fontSize: '1.05rem' }}>
            {Number(result.totalVolume ?? 0).toFixed(2)} cm3
          </strong>
        </div>
        <div style={metricCard}>
          <div style={{ fontSize: '0.74rem', color: '#64748b', textTransform: 'uppercase' }}>
            Review Required
          </div>
          <strong style={{ fontSize: '1.05rem' }}>
            {result.requiresReview ? 'Yes' : 'No'}
          </strong>
        </div>
      </div>

      {highlightedRegions.length > 0 && (
        <>
          <strong style={{ display: 'block', marginTop: '1rem' }}>Detected Regions</strong>
          <ul style={regionList}>
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
        style={{
          marginTop: '1rem',
          padding: '0.95rem',
          borderRadius: '0.9rem',
          background: 'rgba(5, 150, 105, 0.07)',
          border: '1px solid rgba(5, 150, 105, 0.12)',
        }}
      >
        <strong style={{ display: 'block', marginBottom: '0.35rem' }}>Clinical interpretation</strong>
        <p style={{ margin: 0, color: '#334155', lineHeight: 1.65 }}>
          {result.aiInterpretation || result.severity?.description}
        </p>
      </div>
    </section>
  )
}
