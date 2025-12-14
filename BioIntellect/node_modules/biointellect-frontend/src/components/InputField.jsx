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
  ...rest
}) => {
  const [isFocused, setIsFocused] = useState(false)

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
        <input
          id={id}
          type={type}
          placeholder={placeholder}
          value={value}
          onChange={onChange}
          onFocus={() => setIsFocused(true)}
          onBlur={() => setIsFocused(false)}
          disabled={disabled}
          className={`${styles.input} ${error ? styles.error : ''} ${
            success ? styles.success : ''
          } ${isFocused ? styles.focused : ''}`}
          {...rest}
        />
      </div>

      {error && <p className={styles.errorMessage}>{error}</p>}
      {!error && helperText && (
        <p className={styles.helperText}>{helperText}</p>
      )}
    </div>
  )
}
