import { useEffect } from 'react'
import { motion, AnimatePresence } from 'framer-motion'
import styles from './Toast.module.css'

/**
 * Toast Component
 * 
 * Displays temporary notification messages
 * - Appears from the side with smooth animation
 * - Auto-dismisses after 7 seconds
 * - Centered on screen
 */

export const Toast = ({ message, type = 'success', isVisible, onClose }) => {
  useEffect(() => {
    if (isVisible) {
      const timer = setTimeout(() => {
        onClose()
      }, 7000) // 7 seconds

      return () => clearTimeout(timer)
    }
  }, [isVisible, onClose])

  return (
    <AnimatePresence>
      {isVisible && (
        <motion.div
          className={`${styles.toast} ${styles[type]}`}
          initial={{ x: 300, y: -50, opacity: 0, scale: 0.8 }}
          animate={{ x: 0, y: -50, opacity: 1, scale: 1 }}
          exit={{ x: 300, y: -50, opacity: 0, scale: 0.8 }}
          transition={{
            type: 'spring',
            stiffness: 300,
            damping: 30,
          }}
        >
          {message && (
            <div className={styles.content}>
              <span className={styles.message}>{message}</span>
            </div>
          )}
        </motion.div>
      )}
    </AnimatePresence>
  )
}

export default Toast
