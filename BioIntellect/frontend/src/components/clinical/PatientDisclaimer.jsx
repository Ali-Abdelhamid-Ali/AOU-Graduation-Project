const baseStyle = {
  padding: '0.75rem 1rem',
  borderRadius: '0.75rem',
  border: '1px solid var(--color-warning)',
  background: 'var(--color-warning-bg)',
  color: 'var(--color-text)',
  fontSize: '0.875rem',
}

export const PatientDisclaimer = () => (
  <div style={baseStyle}>
    <strong>Medical notice:</strong> This tool supports education only and does not
    replace diagnosis by a licensed clinician.
  </div>
)
