import { motion } from 'framer-motion'
import { useAuth } from '@/store/AuthContext'
import { TopBar } from '@/components/layout/TopBar'
import { brandingConfig } from '@/config/brandingConfig'
import styles from './AdminDashboard.module.css'

// Professional Icon Imports
import analyticsIcon from '@/assets/images/icons/analytics.png'
import securityIcon from '@/assets/images/icons/security.png'
import insightsIcon from '@/assets/images/icons/insights.png'
import cardioIcon from '@/assets/images/icons/cardio.png'
import neuroIcon from '@/assets/images/icons/neuro.png'
import labIcon from '@/assets/images/icons/lab.png'

import { getAdminCards } from '@/config/dashboardCards'

export const AdminDashboard = (props) => {
    const {
        userRole,
        onLogout
    } = props;
    const { currentUser } = useAuth()
    const userSpecialty = currentUser?.specialty?.toLowerCase() || ''

    // Move handlers into a single object for the config function
    const handlers = {
        onCreatePatient: props.onCreatePatient,
        onCreateDoctor: props.onCreateDoctor,
        onCreateAdmin: props.onCreateAdmin,
        onEcgAnalysis: props.onEcgAnalysis,
        onMriSegmentation: props.onMriSegmentation,
        onMedicalLlm: props.onMedicalLlm,
        onPatientDirectory: props.onPatientDirectory
    };

    const cards = getAdminCards(userSpecialty, handlers).filter(card => {
        const medicalStaff = ['doctor', 'nurse'];
        const admins = ['super_admin', 'administrator', 'admin'];

        if (card.restricted && !admins.includes(userRole)) return false;
        if (card.clinical && !medicalStaff.includes(userRole) && !admins.includes(userRole)) return false;

        return true;
    }).sort((a, b) => {
        // Prioritize relevant modules to the top
        if (a.priority && !b.priority) return -1;
        if (!a.priority && b.priority) return 1;
        return 0;
    })

    return (
        <div className={styles.pageWrapper}>
            <TopBar userRole={userRole} onLogout={onLogout} />

            <main className={styles.main}>
                <motion.div
                    initial={{ opacity: 0, x: -20 }}
                    animate={{ opacity: 1, x: 0 }}
                    className={styles.hero}
                >
                    <div className={styles.heroTag}>SYSTEM OVERVIEW</div>
                    <h1 className={styles.heroTitle}>{brandingConfig.brandName}</h1>
                    <p className={styles.heroDesc}>
                        Administrative Command Center for {brandingConfig.hospitalName}. Manage identity and clinical research integrity within the system.
                    </p>
                </motion.div>

                <motion.div
                    className={styles.grid}
                    initial="hidden"
                    animate="visible"
                    variants={{
                        hidden: { opacity: 0 },
                        visible: {
                            opacity: 1,
                            transition: {
                                staggerChildren: 0.1
                            }
                        }
                    }}
                >
                    {cards.map((card) => (
                        <motion.div
                            key={card.id}
                            variants={{
                                hidden: { opacity: 0, y: 20 },
                                visible: { opacity: 1, y: 0 }
                            }}
                            whileHover={{ y: -8, boxShadow: 'var(--shadow-2xl)' }}
                            whileTap={{ scale: 0.98 }}
                            className={styles.card}
                            onClick={() => {
                                if (card.action) card.action()
                            }}
                        >
                            <div className={styles.iconWrapper} style={{ backgroundColor: card.color.startsWith('#') ? `${card.color}15` : 'rgba(0, 102, 204, 0.1)' }}>
                                <img src={card.icon} alt={card.title} className={styles.cardIconImg} />
                            </div>
                            <div className={styles.cardContent}>
                                <div className={styles.cardHeader}>
                                    <h3 className={styles.cardTitle}>{card.title}</h3>
                                    {card.tag && (
                                        <span className={styles.cardTag}>{card.tag}</span>
                                    )}
                                </div>
                                <p className={styles.cardDesc}>{card.description}</p>
                            </div>
                            <div className={styles.cardFooter} style={{ color: card.color }}>
                                Launch Module <span>&rarr;</span>
                            </div>
                        </motion.div>
                    ))}
                </motion.div>
            </main>
        </div>
    )
}
