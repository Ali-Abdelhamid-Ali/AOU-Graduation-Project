const baseStyle = {
  padding: '0.75rem 1rem',
  borderRadius: '0.75rem',
  border: '1px solid rgba(59, 130, 246, 0.35)',
  background: 'rgba(219, 234, 254, 0.35)',
  color: '#1f2937',
  fontSize: '0.875rem',
  lineHeight: 1.5,
}

export const EcgDisclaimer = () => (
  <div style={baseStyle}>
    <strong>Clinical workflow:</strong> AI findings are decision support only; confirm
    ECG interpretation with standard clinical review.
  </div>
)
