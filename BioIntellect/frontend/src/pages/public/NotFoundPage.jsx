import { useNavigate } from 'react-router-dom'

import { brandingConfig } from '@/config/brandingConfig'
import styles from './NotFoundPage.module.css'

export const NotFoundPage = () => {
  const navigate = useNavigate()

  return (
    <main className={styles.page}>
      <section className={styles.card}>
        <span className={styles.code}>404</span>
        <h1>Page not found</h1>
        <p>
          The requested screen is not connected to the current production routing map for {brandingConfig.brandName}.
        </p>

        <div className={styles.actions}>
          <button type="button" onClick={() => navigate(-1)}>
            Go back
          </button>
          <button type="button" className={styles.primary} onClick={() => navigate('/')}>
            Return home
          </button>
        </div>
      </section>
    </main>
  )
}

export default NotFoundPage
