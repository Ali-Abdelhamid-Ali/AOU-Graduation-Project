import { useState } from 'react'
import styles from './InputField.module.css' // Reusing InputField styles for consistency

/**
 * SelectField Component
 * 
 * Reusable dropdown component
 * 
 * Props:
 * - id, label, value, onChange, options, error, required
 * - options: Array of { value: string, label: string }
 */

export const SelectField = ({
    id,
    label,
    value,
    onChange,
    options = [],
    error,
    required = false,
    helperText,
    disabled = false,
    placeholder = 'Select an option'
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
                <select
                    id={id}
                    value={value}
                    onChange={onChange}
                    onFocus={() => setIsFocused(true)}
                    onBlur={() => setIsFocused(false)}
                    disabled={disabled}
                    className={`${styles.input} ${styles.select} ${error ? styles.error : ''} ${isFocused ? styles.focused : ''
                        } ${!value ? styles.placeholder : ''}`}
                >
                    <option value="" disabled>
                        {placeholder}
                    </option>
                    {options.map((opt) => (
                        <option key={opt.value} value={opt.value}>
                            {opt.label}
                        </option>
                    ))}
                </select>
                {/* Dropdown Arrow Icon */}
                <div className={styles.selectArrow} />
            </div>

            {error && <p className={styles.errorMessage}>{error}</p>}
            {!error && helperText && (
                <p className={styles.helperText}>{helperText}</p>
            )}
        </div>
    )
}
