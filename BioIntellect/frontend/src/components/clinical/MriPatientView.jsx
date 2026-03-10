const cardBase = {
  marginTop: '1rem',
  padding: '1.2rem',
  borderRadius: '1rem',
  border: '1px solid rgba(59, 130, 246, 0.2)',
  background:
    'linear-gradient(180deg, rgba(239, 246, 255, 0.96) 0%, rgba(255, 255, 255, 0.98) 100%)',
  color: '#111827',
  boxShadow: '0 16px 30px rgba(15, 23, 42, 0.06)',
}

const statGrid = {
  display: 'grid',
  gridTemplateColumns: 'repeat(2, minmax(0, 1fr))',
  gap: '0.75rem',
  marginTop: '1rem',
}

const statCard = {
  padding: '0.85rem',
  borderRadius: '0.9rem',
  background: 'rgba(219, 234, 254, 0.45)',
  border: '1px solid rgba(96, 165, 250, 0.18)',
}

const formatPercent = (value) =>
  typeof value === 'number' ? `${(value * 100).toFixed(1)}%` : 'N/A'

export const MriPatientView = ({ result }) => {
  if (!result) return null

  const confidence =
    typeof result.confidence === 'number'
      ? result.confidence
      : result.confidenceBreakdown?.overall

  return (
    <section style={cardBase}>
      <div style={{ display: 'flex', justifyContent: 'space-between', gap: '1rem' }}>
        <div>
          <h4 style={{ margin: 0, fontSize: '1rem' }}>Patient Summary</h4>
          <p style={{ margin: '0.35rem 0 0', color: '#475569', lineHeight: 1.6 }}>
            This view simplifies the AI output into the main points you should discuss with
            your clinician.
          </p>
        </div>
        <span
          style={{
            alignSelf: 'flex-start',
            padding: '0.4rem 0.8rem',
            borderRadius: '999px',
            background: result.severity?.color || '#2563eb',
            color: '#fff',
            fontSize: '0.78rem',
            fontWeight: 700,
          }}
        >
          {result.severity?.label || 'Analysis Complete'}
        </span>
      </div>

      <div style={statGrid}>
        <div style={statCard}>
          <div style={{ fontSize: '0.74rem', color: '#64748b', textTransform: 'uppercase' }}>
            Confidence
          </div>
          <strong style={{ fontSize: '1.05rem' }}>{formatPercent(confidence)}</strong>
        </div>
        <div style={statCard}>
          <div style={{ fontSize: '0.74rem', color: '#64748b', textTransform: 'uppercase' }}>
            Total Volume
          </div>
          <strong style={{ fontSize: '1.05rem' }}>
            {Number(result.totalVolume ?? 0).toFixed(2)} cm3
          </strong>
        </div>
      </div>

      <div
        style={{
          marginTop: '1rem',
          padding: '0.95rem',
          borderRadius: '0.9rem',
          background: 'rgba(37, 99, 235, 0.06)',
          border: '1px solid rgba(37, 99, 235, 0.12)',
        }}
      >
        <strong style={{ display: 'block', marginBottom: '0.35rem' }}>What the AI suggests</strong>
        <p style={{ margin: 0, color: '#334155', lineHeight: 1.65 }}>
          {result.severity?.description || 'Consult your clinician for interpretation.'}
        </p>
      </div>

      <p style={{ margin: '1rem 0 0', color: '#64748b', fontSize: '0.83rem', lineHeight: 1.6 }}>
        {result.disclaimer ||
          'This output is for clinical decision support and should not be treated as a final diagnosis.'}
      </p>
    </section>
  )
}
