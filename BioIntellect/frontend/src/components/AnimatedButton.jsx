import { useState, useRef, useEffect } from 'react'
import { motion } from 'framer-motion'
import anime from 'animejs'
import styles from './AnimatedButton.module.css'

/**
 * Animated Button Component
 * 
 * Advanced button with Anime.js and Framer Motion animations
 * Features:
 * - Multiple variants (primary, secondary, outline)
 * - Multiple sizes (small, medium, large)
 * - Loading state with spinner
 * - Disabled state
 * - Smooth animations with Anime.js and Framer Motion
 * - Ripple effect on click
 */

export const AnimatedButton = ({
  children,
  onClick,
  variant = 'primary',
  size = 'medium',
  disabled = false,
  isLoading = false,
  type = 'button',
  fullWidth = false,
  className = '',
  icon = null
}) => {
  const buttonRef = useRef(null)
  const [isHovering, setIsHovering] = useState(false)

  /**
   * Handle hover animation with Anime.js
   */
  useEffect(() => {
    if (isHovering && buttonRef.current && !disabled && !isLoading) {
      anime({
        targets: buttonRef.current,
        scale: 1.02,
        duration: 300,
        easing: 'easeOutCubic'
      })
    }
  }, [isHovering, disabled, isLoading])

  /**
   * Handle click animation
   */
  const handleClick = (e) => {
    if (disabled || isLoading) return

    // Pulse animation on click
    if (buttonRef.current) {
      anime({
        targets: buttonRef.current,
        scale: [1, 0.98, 1],
        duration: 500,
        easing: 'easeOutCubic'
      })
    }

    onClick?.(e)
  }

  /**
   * Handle mouse enter
   */
  const handleMouseEnter = () => {
    if (!disabled && !isLoading) {
      setIsHovering(true)
    }
  }

  /**
   * Handle mouse leave
   */
  const handleMouseLeave = () => {
    setIsHovering(false)
    if (buttonRef.current) {
      anime({
        targets: buttonRef.current,
        scale: 1,
        duration: 300,
        easing: 'easeOutCubic'
      })
    }
  }

  const classNames = [
    styles.button,
    styles[variant],
    styles[size],
    fullWidth && styles.fullWidth,
    className
  ]
    .filter(Boolean)
    .join(' ')

  return (
    <motion.button
      ref={buttonRef}
      className={classNames}
      onClick={handleClick}
      onMouseEnter={handleMouseEnter}
      onMouseLeave={handleMouseLeave}
      disabled={disabled || isLoading}
      type={type}
      initial={{ opacity: 0, y: 10 }}
      animate={{ opacity: 1, y: 0 }}
      whileHover={{ y: -3, boxShadow: 'var(--shadow-lg)' }}
      whileTap={{ scale: 0.97 }}
      transition={{ type: 'spring', stiffness: 400, damping: 25 }}
    >
      {isLoading ? (
        <>
          <span className={styles.spinner} />
          Processing...
        </>
      ) : (
        <>
          {icon && <span>{icon}</span>}
          {children}
        </>
      )}
    </motion.button>
  )
}
