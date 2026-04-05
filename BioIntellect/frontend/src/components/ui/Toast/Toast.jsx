import { useState, useEffect, useCallback } from 'react'
import { motion, AnimatePresence } from 'framer-motion'
import styles from './Toast.module.css'

let toastListeners = []
let toastId = 0

export const toast = {
  show(message, type = 'info', duration = 4000) {
    const id = ++toastId
    toastListeners.forEach(fn => fn({ id, message, type, duration }))
    return id
  },
  success(message, duration) { return this.show(message, 'success', duration) },
  error(message, duration) { return this.show(message, 'error', duration) },
  warning(message, duration) { return this.show(message, 'warning', duration) },
  info(message, duration) { return this.show(message, 'info', duration) },
}

export const ToastContainer = () => {
  const [toasts, setToasts] = useState([])

  useEffect(() => {
    const listener = (newToast) => {
      setToasts(prev => [...prev, newToast])
      if (newToast.duration > 0) {
        setTimeout(() => {
          setToasts(prev => prev.filter(t => t.id !== newToast.id))
        }, newToast.duration)
      }
    }
    toastListeners.push(listener)
    return () => { toastListeners = toastListeners.filter(fn => fn !== listener) }
  }, [])

  const dismiss = useCallback((id) => {
    setToasts(prev => prev.filter(t => t.id !== id))
  }, [])

  return (
    <div className={styles.container}>
      <AnimatePresence>
        {toasts.map(t => (
          <motion.div
            key={t.id}
            className={`${styles.toast} ${styles[t.type]}`}
            initial={{ opacity: 0, x: 60, scale: 0.9 }}
            animate={{ opacity: 1, x: 0, scale: 1 }}
            exit={{ opacity: 0, x: 60, scale: 0.9 }}
            transition={{ duration: 0.25 }}
          >
            <span className={styles.message}>{t.message}</span>
            <button className={styles.dismiss} onClick={() => dismiss(t.id)} aria-label="Dismiss">×</button>
            {t.duration > 0 && (
              <motion.div
                className={styles.progress}
                initial={{ scaleX: 1 }}
                animate={{ scaleX: 0 }}
                transition={{ duration: t.duration / 1000, ease: 'linear' }}
              />
            )}
          </motion.div>
        ))}
      </AnimatePresence>
    </div>
  )
}
