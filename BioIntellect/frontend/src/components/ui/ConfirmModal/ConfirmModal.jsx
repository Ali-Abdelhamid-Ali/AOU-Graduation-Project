import { motion, AnimatePresence } from 'framer-motion'
import styles from './ConfirmModal.module.css'

export const ConfirmModal = ({ isOpen, title, message, confirmLabel = 'Confirm', cancelLabel = 'Cancel', variant = 'primary', onConfirm, onCancel }) => (
  <AnimatePresence>
    {isOpen && (
      <>
        <motion.div
          className={styles.backdrop}
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          exit={{ opacity: 0 }}
          onClick={onCancel}
        />
        <motion.div
          className={styles.modal}
          initial={{ opacity: 0, scale: 0.92 }}
          animate={{ opacity: 1, scale: 1 }}
          exit={{ opacity: 0, scale: 0.92 }}
          transition={{ duration: 0.2 }}
          role="dialog"
          aria-modal="true"
        >
          {title && <h3 className={styles.title}>{title}</h3>}
          {message && <p className={styles.message}>{message}</p>}
          <div className={styles.actions}>
            <button className={styles.cancel} onClick={onCancel}>{cancelLabel}</button>
            <button className={`${styles.confirm} ${styles[variant]}`} onClick={onConfirm}>{confirmLabel}</button>
          </div>
        </motion.div>
      </>
    )}
  </AnimatePresence>
)
