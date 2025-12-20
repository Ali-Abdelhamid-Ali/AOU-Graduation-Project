import { motion } from 'framer-motion'
import { useAuth } from '../context/AuthContext'
import { TopBar } from '../components/TopBar'
import { brandingConfig } from '../config/brandingConfig'
import styles from './AdminDashboard.module.css'

export const AdminDashboard = ({
    userRole,
    onLogout,
    onCreatePatient,
    onCreateDoctor,
    onEcgAnalysis,
    onMriSegmentation,
    onMedicalLlm
}) => {
    const { currentUser, signOut } = useAuth()

    const cards = [
        {
            id: 'doctors',
            title: 'Medical Staff',
            description: 'Administrative control over medical practitioner credentials and access levels.',
            icon: '🛡️',
            action: onCreateDoctor,
            color: '#10b981',
            tag: 'NEW'
        },
        {
            id: 'reg',
            title: 'Patient Management',
            description: 'Execute high-security patient provisioning and clinical record initialization.',
            icon: '📋',
            action: onCreatePatient,
            color: 'var(--color-primary)',
            tag: 'CORE'
        },
        {
            id: 'proj',
            title: 'Medical Advisor LLM',
            description: 'Interactive AI-based clinical decision support and medical knowledge retrieval.',
            icon: '💬',
            action: onMedicalLlm,
            color: '#6366f1',
            tag: 'LIVE'
        },
        {
            id: 'ecg',
            title: 'ECG Cardiac Analysis',
            description: 'CNN-Transformer based arrhythmia classification and temporal signal diagnostics.',
            icon: '❤️',
            action: onEcgAnalysis,
            color: '#ef4444',
            tag: 'AI'
        },
        {
            id: 'mri',
            title: 'Brain MRI Segmentation',
            description: '3D U-Net powered brain tumor delineation and volumetric segmentation.',
            icon: '🧠',
            action: onMriSegmentation,
            color: '#3b82f6',
            tag: 'AI'
        },
        {
            id: 'audit',
            title: 'Security Logs',
            description: 'Immutable audit trails and system-wide security event monitoring.',
            icon: '🔐',
            action: () => alert('Audit logs under security review.'),
            color: '#f59e0b'
        }
    ]

    const handleLogout = async () => {
        await signOut()
        onLogout()
    }

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
                            <div className={styles.iconWrapper} style={{ background: `${card.color}15` }}>
                                {card.icon}
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
