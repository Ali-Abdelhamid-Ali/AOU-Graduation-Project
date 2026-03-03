const baseStyle = {
  padding: '0.75rem 1rem',
  borderRadius: '0.75rem',
  border: '1px solid rgba(245, 158, 11, 0.35)',
  background: 'rgba(254, 243, 199, 0.25)',
  color: '#1f2937',
  fontSize: '0.875rem',
  lineHeight: 1.5,
}

export const PatientDisclaimer = () => (
  <div style={baseStyle}>
    <strong>Medical notice:</strong> This tool supports education only and does not
    replace diagnosis by a licensed clinician.
  </div>
)
