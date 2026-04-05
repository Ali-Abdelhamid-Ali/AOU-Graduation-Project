import { useMemo } from 'react'
import { useNavigate } from 'react-router-dom'

import { ROLES } from '@/config/roles'
import { useAuth } from '@/store/AuthContext'
import styles from './AdminPanels.module.css'

export const AdminProvisioning = () => {
  const navigate = useNavigate()
  const { currentUser } = useAuth()

  const normalizedRole = currentUser?.user_role
  const isSuperAdmin = normalizedRole === ROLES.SUPER_ADMIN

  const quickActions = useMemo(() => {
    if (isSuperAdmin) {
      return [
        { title: 'Add Super Admin', description: 'Provision another root-level operator with full governance permissions.', action: () => navigate('/create-admin') },
        { title: 'Add Administrator', description: 'Provision another administrative operator with scoped access.', action: () => navigate('/create-admin') },
        { title: 'Add Doctor', description: 'Create a clinician profile and assign medical metadata.', action: () => navigate('/create-doctor') },
        { title: 'Add Patient', description: 'Register a patient identity and baseline demographics.', action: () => navigate('/create-patient') },
        { title: 'Open Registry', description: 'Move into the patient registry page inside the admin workspace tree.', action: () => navigate('/admin-dashboard/patients') },
      ]
    }
    return [
      { title: 'Add Doctor', description: 'Create a new clinician profile and assign role metadata.', action: () => navigate('/create-doctor') },
      { title: 'Add Patient', description: 'Register a new patient identity and baseline demographics.', action: () => navigate('/create-patient') },
      { title: 'Open Registry', description: 'Review the patient registry.', action: () => navigate('/admin-dashboard/patients') },
    ]
  }, [isSuperAdmin, navigate])

  return (
    <>
      <section className={styles.heroSection}>
        <div>
          <span className={styles.kicker}>Provisioning hub</span>
          <h2>Onboard the right role without leaving the admin workspace tree</h2>
          <p>
            This page turns the old quick-action block into a real route. Each button here opens an
            actual form or operational destination, not a decorative placeholder.
          </p>
        </div>
      </section>

      <section className={styles.splitGrid}>
        <article className={styles.panel}>
          <div className={styles.panelHeading}>
            <div>
              <h3>Quick Actions</h3>
              <p>Only actions backed by the current production permissions are exposed here.</p>
            </div>
          </div>
          <div className={styles.actionGrid}>
            {quickActions.map((item) => (
              <button key={item.title} type="button" className={styles.actionCard} onClick={item.action}>
                <strong>{item.title}</strong>
                <p>{item.description}</p>
              </button>
            ))}
          </div>
        </article>

        <article className={styles.panel}>
          <div className={styles.panelHeading}>
            <div>
              <h3>Provisioning Guidance</h3>
              <p>Keep this flow honest to the permissions and modules that exist today.</p>
            </div>
          </div>
          <div className={styles.healthGrid}>
            <div className={styles.healthMetric}>
              <span>Super Admin Creation</span>
              <strong>{isSuperAdmin ? 'Enabled' : 'Restricted'}</strong>
              <span className={`${styles.badge} ${isSuperAdmin ? styles.toneSuccess : styles.toneWarning}`}>
                {isSuperAdmin ? 'allowed' : 'guarded'}
              </span>
            </div>
            <div className={styles.healthMetric}>
              <span>Administrator Creation</span>
              <strong>{isSuperAdmin ? 'Enabled' : 'Restricted'}</strong>
              <span className={`${styles.badge} ${isSuperAdmin ? styles.toneSuccess : styles.toneWarning}`}>
                {isSuperAdmin ? 'allowed' : 'guarded'}
              </span>
            </div>
            <div className={styles.healthMetric}>
              <span>Doctor Creation</span>
              <strong>Enabled</strong>
              <span className={`${styles.badge} ${styles.toneSuccess}`}>allowed</span>
            </div>
            <div className={styles.healthMetric}>
              <span>Patient Intake</span>
              <strong>Enabled</strong>
              <span className={`${styles.badge} ${styles.toneSuccess}`}>allowed</span>
            </div>
          </div>
        </article>
      </section>
    </>
  )
}

export default AdminProvisioning

