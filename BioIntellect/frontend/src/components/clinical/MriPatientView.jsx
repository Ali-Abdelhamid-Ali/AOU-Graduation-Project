const cardStyle = {
  marginTop: '1rem',
  padding: '1rem',
  borderRadius: '0.75rem',
  border: '1px solid rgba(59, 130, 246, 0.25)',
  background: 'rgba(239, 246, 255, 0.55)',
  color: '#111827',
}

export const MriPatientView = ({ result }) => {
  if (!result) return null

  return (
    <div style={cardStyle}>
      <h4 style={{ marginTop: 0 }}>Patient Summary</h4>
      <p>
        <strong>Status:</strong> {result.severity?.label || 'Analysis Complete'}
      </p>
      <p>
        <strong>Total Volume:</strong> {result.totalVolume ?? 0} cm3
      </p>
      <p style={{ marginBottom: 0 }}>
        <strong>Recommendation:</strong> {result.severity?.description || 'Consult your clinician for interpretation.'}
      </p>
    </div>
  )
}
