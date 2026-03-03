import { useState, useEffect } from 'react'
import { motion } from 'framer-motion'
import { useAuth } from '@/store/AuthContext'
import { useNavigate } from 'react-router-dom'
import { analyticsAPI } from '@/services/api'
import { Skeleton } from '@/components/ui/Skeleton'
import SkeletonText from '@/components/ui/SkeletonText'
import SkeletonCircle from '@/components/ui/SkeletonCircle'
import styles from './PatientDashboard.module.css'

// Professional Icon Imports
import cardioIcon from '@/assets/images/icons/cardio.png'
import neuroIcon from '@/assets/images/icons/neuro.png'
import insightsIcon from '@/assets/images/icons/insights.png'

export const PatientDashboard = () => {
    const { currentUser } = useAuth()
    const navigate = useNavigate()
    const [loading, setLoading] = useState(true)
    const [stats, setStats] = useState({
        totalReports: 0,
        nextAppointment: 'None scheduled',
        lastAnalysis: 'Loading...',
        healthScore: 100,
        trends: []
    })

    useEffect(() => {
        const fetchDashboardData = async () => {
            if (!currentUser?.id) {
                setLoading(false);
                return;
            }

            setLoading(true);
            try {
                const response = await analyticsAPI.getDashboardStats()
                if (response.success) {
                    const data = response.data
                    setStats({
                        totalReports: data.total_reports || 0,
                        nextAppointment: data.next_appointment || 'Not scheduled',
                        lastAnalysis: data.last_analysis || 'Stable',
                        healthScore: data.health_score || 100,
                        trends: data.trends || []
                    })
                }
            } catch (error) {
                console.error('Error fetching dashboard stats:', error)
            } finally {
                setLoading(false)
            }
        }

        fetchDashboardData()
    }, [currentUser])

    const quickLinks = [
        { id: 'ecg', title: 'ECG Analysis', icon: cardioIcon, color: '#ef4444', path: '/ecg-analysis' },
        { id: 'mri', title: 'Brain Imaging', icon: neuroIcon, color: '#3b82f6', path: '/mri-segmentation' },
        { id: 'llm', title: 'Medical Advisor', icon: insightsIcon, color: '#6366f1', path: '/medical-llm' }
    ]

    if (loading) {
        return (
            <div className={styles.loadingGrid}>
                <div className={styles.heroSkeleton}>
                    <Skeleton height="180px" borderRadius="24px" />
                </div>
                <div className={styles.statsSkeleton}>
                    {[1, 2, 3].map(i => (
                        <div key={i} className={styles.skeletonCard}>
                            <SkeletonCircle size="40px" />
                            <SkeletonText lines={2} width="120px" />
                        </div>
                    ))}
                </div>
                <div className={styles.moduleSkeleton}>
                    <SkeletonText lines={1} width="200px" />
                    <div className={styles.moduleGridSkeleton}>
                        {[1, 2, 3].map(i => (
                            <Skeleton key={i} height="80px" borderRadius="16px" />
                        ))}
                    </div>
                </div>
            </div>
        )
    }

    return (
        <motion.div
            className={styles.container}
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
        >
            <section className={styles.hero}>
                <div className={styles.heroContent}>
                    <h1 className={styles.welcomeText}>
                        Welcome back, <span className={styles.highlight}>{currentUser?.first_name}</span>
                    </h1>
                    <p className={styles.heroSubtitle}>Your clinical overview and AI health insights are ready.</p>
                </div>
                <div className={styles.heroStats}>
                    <div className={styles.statBox}>
                        <span className={styles.statValue}>{stats.healthScore}%</span>
                        <span className={styles.statLabel}>Health Score</span>
                    </div>
                </div>
            </section>

            <div className={styles.statsGrid}>
                <motion.div className={styles.statCard} whileHover={{ y: -5 }}>
                    <div className={styles.cardHeader}>
                        <span className={styles.cardIcon}>📄</span>
                        <h3 className={styles.cardTitle}>Total Reports</h3>
                    </div>
                    <p className={styles.cardValue}>{stats.totalReports}</p>
                    <span className={styles.cardTrend}>+2 this month</span>
                </motion.div>

                <motion.div className={styles.statCard} whileHover={{ y: -5 }}>
                    <div className={styles.cardHeader}>
                        <span className={styles.cardIcon}>📅</span>
                        <h3 className={styles.cardTitle}>Next Appointment</h3>
                    </div>
                    <p className={styles.cardValue}>{stats.nextAppointment}</p>
                    <span className={styles.cardTrend}>General Checkup</span>
                </motion.div>

                <motion.div className={styles.statCard} whileHover={{ y: -5 }}>
                    <div className={styles.cardHeader}>
                        <span className={styles.cardIcon}>🧪</span>
                        <h3 className={styles.cardTitle}>Last Analysis</h3>
                    </div>
                    <p className={styles.cardValue}>{stats.lastAnalysis}</p>
                    <span className={styles.cardTrend}>Stable condition</span>
                </motion.div>
            </div>

            <section className={styles.quickModules}>
                <h2 className={styles.sectionTitle}>Medical AI Modules</h2>
                <div className={styles.moduleGrid}>
                    {quickLinks.map((module) => (
                        <motion.div
                            key={module.id}
                            className={styles.moduleCard}
                            whileHover={{ scale: 1.02 }}
                            whileTap={{ scale: 0.98 }}
                            onClick={() => navigate(module.path)}
                        >
                            <div className={styles.moduleIcon} style={{ backgroundColor: `${module.color}15` }}>
                                <img src={module.icon} alt={module.title} />
                            </div>
                            <div className={styles.moduleInfo}>
                                <h3>{module.title}</h3>
                                <p>Access specialized AI diagnostic tools.</p>
                            </div>
                        </motion.div>
                    ))}
                </div>
            </section>

            <section className={styles.recentActivity}>
                <h2 className={styles.sectionTitle}>Recent Health Trends</h2>
                <div className={styles.chartPlaceholder}>
                    {stats.trends.map((t, i) => (
                        <div key={i} className={styles.chartBar} style={{ height: `${t.score}%` }} title={`${t.date}: ${t.score}%`} />
                    ))}
                </div>
            </section>
        </motion.div>
    )
}
