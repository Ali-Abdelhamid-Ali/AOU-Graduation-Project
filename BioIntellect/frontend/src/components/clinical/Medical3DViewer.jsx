 
import styles from './Medical3DViewer.module.css'

export const Medical3DViewer = ({ result, isLoading = false }) => {
  if (isLoading) {
    return (
      <div className={styles.loadingContainer}>
        <div className={styles.spinner} />
        <p className={styles.loadingText}>Preparing 3D reconstruction...</p>
      </div>
    )
  }

  return (
    <div className={styles.viewerContainer}>
      <canvas className={styles.canvas} aria-label="MRI 3D visualization placeholder" />
      <div className={styles.overlay}>
        <span className={styles.badge}>
          {result?.severity?.label || 'No Segmentation Loaded'}
        </span>
      </div>
    </div>
  )
}

export default Medical3DViewer
