const baseStyle = {
  padding: '0.75rem 1rem',
  borderRadius: '0.75rem',
  border: '1px solid rgba(16, 185, 129, 0.35)',
  background: 'rgba(209, 250, 229, 0.35)',
  color: '#1f2937',
  fontSize: '0.875rem',
  lineHeight: 1.5,
}

export const LlmDisclaimer = () => (
  <div style={baseStyle}>
    <strong>Safety notice:</strong> Model output may contain mistakes and must be
    validated against patient records and clinical guidelines.
  </div>
)
