import { useState } from 'react'
import styles from './InputField.module.css'

/**
 * InputField Component
 * 
 * Reusable form input with validation styling
 * Features:
 * - Support for different input types
 * - Label and placeholder
 * - Error state with message
 * - Success state
 * - Accessible labeling
 * - Icon support (optional)
 */

export const InputField = ({
  id,
  label,
  type = 'text',
  placeholder,
  value,
  onChange,
  error,
  success = false,
  disabled = false,
  required = false,
  icon = null,
  helperText,
  multiline = false,
  ...rest
}) => {
  const [isFocused, setIsFocused] = useState(false)
  const inputProps = {
    id,
    placeholder,
    value,
    onChange,
    onFocus: () => setIsFocused(true),
    onBlur: () => setIsFocused(false),
    disabled,
    className: `${styles.input} ${error ? styles.error : ''} ${
      success ? styles.success : ''
    } ${isFocused ? styles.focused : ''} ${multiline ? styles.textarea : ''}`,
    spellCheck: type === 'text' || multiline ? 'true' : 'false',
    'aria-invalid': !!error,
    'aria-describedby': error ? `${id}-error` : helperText ? `${id}-helper` : undefined,
    ...rest,
    // autoComplete from rest takes priority; fallback based on type
    autoComplete: rest.autoComplete ?? (type === 'password' ? 'current-password' : 'on'),
  }

  return (
    <div className={styles.container}>
      {label && (
        <label htmlFor={id} className={styles.label}>
          {label}
          {required && <span className={styles.required}>*</span>}
        </label>
      )}

      <div className={styles.inputWrapper}>
        {icon && <span className={styles.icon}>{icon}</span>}
        {multiline ? (
          <textarea {...inputProps} rows={rest.rows || 4} />
        ) : (
          <input {...inputProps} type={type} />
        )}
      </div>

      {error && <p id={`${id}-error`} className={styles.errorMessage}>{error}</p>}
      {!error && helperText && (
        <p id={`${id}-helper`} className={styles.helperText}>{helperText}</p>
      )}
    </div>
  )
}

export default InputField
