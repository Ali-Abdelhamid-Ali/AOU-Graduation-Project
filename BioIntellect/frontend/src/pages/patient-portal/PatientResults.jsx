import { useState, useEffect } from 'react'
import { motion } from 'framer-motion'
import { useAuth } from '@/store/AuthContext'
import { useNavigate } from 'react-router-dom'
import { medicalService } from '@/services/medical.service'
import { Skeleton } from '@/components/ui/Skeleton'
import SkeletonText from '@/components/ui/SkeletonText'
import SkeletonCircle from '@/components/ui/SkeletonCircle'
import styles from './PatientResults.module.css'

export const PatientResults = () => {
    const { currentUser } = useAuth()
    const navigate = useNavigate()
    const [loading, setLoading] = useState(true)
    const [results, setResults] = useState([])

    useEffect(() => {
        const fetchRealResults = async () => {
            if (!currentUser?.id) {
                setLoading(false);
                return;
            }

            setLoading(true);
            try {
                // Fetch ECG and MRI results in parallel via MedicalService (Hardened API)
                const [ecgResults, mriResults] = await Promise.all([
                    medicalService.getEcgResults(currentUser.id),
                    medicalService.getMriResults(currentUser.id)
                ]);

                // Map and combine results
                const ecgMapped = (ecgResults || []).map(r => ({
                    id: `ecg-${r.id}`,
                    name: 'ECG Arrhythmia Scan',
                    date: r.analysis_completed_at ? r.analysis_completed_at.split('T')[0] : 'Pending',
                    status: r.confidence_score > 0.8 ? 'Normal' : 'Warning',
                    summary: r.primary_diagnosis || 'Automated classification completed.',
                    type: 'ecg'
                }));

                const mriMapped = (mriResults || []).map(r => ({
                    id: `mri-${r.id}`,
                    name: 'Brain MRI Segmentation',
                    date: r.analysis_completed_at ? r.analysis_completed_at.split('T')[0] : 'Pending',
                    status: (r.tumor_detected || r.tumor_detected === 'true') ? 'Critical' : 'Normal',
                    summary: r.tumor_detected ? `Tumor suspected: ${r.tumor_type || 'General'}` : 'No abnormal growths detected.',
                    type: 'mri'
                }));

                const combined = [...ecgMapped, ...mriMapped].sort((a, b) => {
                    const dateA = new Date(a.date).getTime() || 0;
                    const dateB = new Date(b.date).getTime() || 0;
                    return dateB - dateA;
                });

                setResults(combined);
            } catch (error) {
                console.error('Error fetching clinical results:', error);
            } finally {
                setLoading(false);
            }
        };

        fetchRealResults();
    }, [currentUser])

    const getStatusColor = (status) => {
        switch (status) {
            case 'Normal': return '#10b981';
            case 'Warning': return '#f59e0b';
            case 'Critical': return '#ef4444';
            default: return '#64748b';
        }
    }

    if (loading) {
        return (
            <div className={styles.container}>
                <div className={styles.header}>
                    <SkeletonText lines={1} width="300px" />
                    <SkeletonText lines={1} width="500px" />
                </div>
                <div className={styles.resultsGrid}>
                    {[1, 2, 3, 4].map(i => (
                        <div key={i} className={styles.resultCardSkeleton}>
                            <div className={styles.cardHeader}>
                                <Skeleton width="80px" height="20px" borderRadius="10px" />
                                <Skeleton width="60px" height="24px" borderRadius="20px" />
                            </div>
                            <SkeletonText lines={1} width="100%" />
                            <SkeletonText lines={2} width="100%" />
                            <Skeleton width="120px" height="36px" borderRadius="12px" />
                        </div>
                    ))}
                </div>
            </div>
        )
    }

    return (
        <motion.div
            className={styles.container}
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
        >
            <div className={styles.header}>
                <h1 className={styles.title}>Medical Analysis Results</h1>
                <p className={styles.subtitle}>View and monitor your clinical reports and AI-powered insights.</p>
            </div>

            <div className={styles.resultsGrid}>
                {results.map((result) => (
                    <motion.div
                        key={result.id}
                        className={styles.resultCard}
                        whileHover={{ y: -5, boxShadow: '0 12px 20px -5px rgba(0,0,0,0.1)' }}
                    >
                        <div className={styles.cardHeader}>
                            <span className={styles.date}>{result.date}</span>
                            <span
                                className={styles.statusBadge}
                                style={{ backgroundColor: `${getStatusColor(result.status)}15`, color: getStatusColor(result.status) }}
                            >
                                {result.status}
                            </span>
                        </div>
                        <h3 className={styles.resultName}>{result.name}</h3>
                        <p className={styles.summary}>{result.summary}</p>
                        <button
                            className={styles.viewDetails}
                            onClick={() => navigate(result.type === 'ecg' ? '/ecg-analysis' : '/mri-segmentation')}
                        >
                            View Full Report →
                        </button>
                    </motion.div>
                ))}
            </div>

            {results.length === 0 && (
                <div className={styles.emptyState}>
                    <span className={styles.emptyIcon}>📂</span>
                    <h3>No Results Found</h3>
                    <p>When your medical tests are processed, they will appear here.</p>
                </div>
            )}
        </motion.div>
    )
}
