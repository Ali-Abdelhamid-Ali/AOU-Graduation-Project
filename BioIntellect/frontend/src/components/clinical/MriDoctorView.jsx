const cardStyle = {
  marginTop: '1rem',
  padding: '1rem',
  borderRadius: '0.75rem',
  border: '1px solid rgba(16, 185, 129, 0.25)',
  background: 'rgba(236, 253, 245, 0.6)',
  color: '#111827',
}

const listStyle = {
  margin: '0.5rem 0 0',
  paddingLeft: '1.25rem',
}

export const MriDoctorView = ({ result }) => {
  if (!result) return null

  const regions = Array.isArray(result.regions) ? result.regions : []

  return (
    <div style={cardStyle}>
      <h4 style={{ marginTop: 0 }}>Physician Summary</h4>
      <p>
        <strong>Severity:</strong> {result.severity?.label || 'N/A'}
      </p>
      <p>
        <strong>Confidence:</strong> {typeof result.confidence === 'number' ? `${(result.confidence * 100).toFixed(1)}%` : 'N/A'}
      </p>
      <p>
        <strong>Total Tumor Volume:</strong> {result.totalVolume ?? 0} cm3
      </p>
      {regions.length > 0 && (
        <>
          <strong>Segmented Regions</strong>
          <ul style={listStyle}>
            {regions.map((region, idx) => (
              <li key={`${region.class_id ?? idx}-${idx}`}>
                {region.class_name || `Class ${region.class_id}`}: {region.volume_cm3 ?? 0} cm3
              </li>
            ))}
          </ul>
        </>
      )}
    </div>
  )
}
