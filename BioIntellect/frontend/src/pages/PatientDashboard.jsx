import { useState, useEffect } from 'react'
import { motion } from 'framer-motion'
import { useAuth } from '../context/AuthContext'
import { useNavigate } from 'react-router-dom'
import { supabase } from '../config/supabase'
import { medicalService } from '../services/medicalService'
import { Skeleton, SkeletonText, SkeletonCircle } from '../components/Skeleton'
import styles from './PatientDashboard.module.css'

// Professional Icon Imports
import cardioIcon from '../images/icons/cardio.png'
import neuroIcon from '../images/icons/neuro.png'
import insightsIcon from '../images/icons/insights.png'

export const PatientDashboard = () => {
    const { currentUser } = useAuth()
    const navigate = useNavigate()
    const [loading, setLoading] = useState(true)
    const [stats, setStats] = useState({
        totalReports: 0,
        nextAppointment: 'None scheduled',
        lastAnalysis: 'Loading...',
        healthScore: 100
    })

    useEffect(() => {
        const fetchRealStats = async () => {
            // VULNERABILITY MITIGATION: Only fetch if we have a valid clinical ID
            if (!currentUser?.id) {
                // If currentUser is definitively null (not just loading), stop local loading
                setLoading(false);
                return;
            }

            setLoading(true);
            try {
                // 1. Fetch Total Reports (ECG + MRI)
                const [ecgCount, mriCount] = await Promise.all([
                    supabase.from('ecg_results').select('id', { count: 'exact', head: true }).eq('patient_id', currentUser.id),
                    supabase.from('mri_segmentation_results').select('id', { count: 'exact', head: true }).eq('patient_id', currentUser.id)
                ])

                // 2. Fetch Next Appointment
                const { data: nextApt } = await supabase
                    .from('appointments')
                    .select('appointment_date, appointment_time')
                    .eq('patient_id', currentUser.id)
                    .gte('appointment_date', new Date().toISOString().split('T')[0])
                    .order('appointment_date', { ascending: true })
                    .limit(1)
                    .maybeSingle();

                // 3. Fetch Last Analysis Status
                const history = await medicalService.getPatientHistory(currentUser.id);
                const latest = history && history.length > 0 ? history[0] : null;

                let lastStatus = 'No records';
                if (latest) {
                    const ecg = latest.ecg_results?.[0];
                    const mri = latest.mri_segmentation_results?.[0];
                    if (ecg) lastStatus = ecg.confidence_score > 0.8 ? 'Normal' : 'Review Needed';
                    if (mri) {
                        // MRI status takes priority if both exist and are critical
                        if (mri.tumor_detected) lastStatus = 'Critical';
                        else if (!ecg) lastStatus = 'Normal';
                    }
                }

                setStats({
                    totalReports: (ecgCount?.count || 0) + (mriCount?.count || 0),
                    nextAppointment: nextApt ? `${nextApt.appointment_date}` : 'Not scheduled',
                    lastAnalysis: lastStatus,
                    healthScore: 100 // Could be calculated based on latest results
                })
            } catch (error) {
                console.error('Error fetching dashboard stats:', error)
            } finally {
                setLoading(false)
            }
        }

        fetchRealStats()
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
                    {/* Simplified Chart Visual */}
                    <div className={styles.chartBar} style={{ height: '60%' }} />
                    <div className={styles.chartBar} style={{ height: '80%' }} />
                    <div className={styles.chartBar} style={{ height: '40%' }} />
                    <div className={styles.chartBar} style={{ height: '90%' }} />
                    <div className={styles.chartBar} style={{ height: '70%' }} />
                </div>
            </section>
        </motion.div>
    )
}
