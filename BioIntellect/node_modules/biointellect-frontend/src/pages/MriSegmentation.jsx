import { useState } from 'react'
import { motion } from 'framer-motion'
import { TopBar } from '../components/TopBar'
import { AnimatedButton } from '../components/AnimatedButton'
import styles from './MriSegmentation.module.css'

export const MriSegmentation = ({ onBack }) => {
    const [analyzing, setAnalyzing] = useState(false)
    const [result, setResult] = useState(null)
    const [selectedSequence, setSelectedSequence] = useState('T1ce')

    const runAnalysis = () => {
        setAnalyzing(true)
        setTimeout(() => {
            setResult({
                type: 'Glioblastoma Multiforme',
                volume: '42.5 cm³',
                location: 'Right Frontal Lobe',
                maskDetails: {
                    edema: '15.2 cm³',
                    enhancing: '21.0 cm³',
                    necrosis: '6.3 cm³'
                },
                recommendation: 'Urgent neurosurgical consultation. The tumor shows significant mass effect on the lateral ventricles.'
            })
            setAnalyzing(false)
        }, 4000)
    }

    return (
        <div className={styles.pageWrapper}>
            <TopBar onBack={onBack} userRole="Neurologist" />

            <div className={styles.container}>
                <header className={styles.header}>
                    <h1>Brain MRI Segmentation</h1>
                    <p>Powered by BioIntellect 3D U-Net Deep Learning Model</p>
                </header>

                <div className={styles.mainGrid}>
                    <section className={styles.controlPanel}>
                        <div className={styles.card}>
                            <h3>Sequence Selection</h3>
                            <div className={styles.sequenceGrid}>
                                {['T1', 'T1ce', 'T2', 'FLAIR'].map(seq => (
                                    <button
                                        key={seq}
                                        className={`${styles.seqBtn} ${selectedSequence === seq ? styles.activeSeq : ''}`}
                                        onClick={() => setSelectedSequence(seq)}
                                    >
                                        {seq}
                                    </button>
                                ))}
                            </div>
                            <p className={styles.hint}>Multi-modal integration required for precise volumetric calculation.</p>

                            <div className={styles.uploadBox}>
                                <span>📥</span>
                                <p>Upload NIfTI / DICOM</p>
                            </div>

                            <AnimatedButton
                                variant="primary"
                                loading={analyzing}
                                onClick={runAnalysis}
                                style={{ width: '100%', marginTop: '2rem' }}
                            >
                                Calculate Segments
                            </AnimatedButton>
                        </div>

                        {result && (
                            <motion.div
                                className={styles.card + ' ' + styles.statsCard}
                                initial={{ opacity: 0, y: 10 }}
                                animate={{ opacity: 1, y: 0 }}
                            >
                                <h3>Volumetric Stats</h3>
                                <div className={styles.statList}>
                                    <div className={styles.statRow}>
                                        <span>Whole Tumor:</span>
                                        <strong>{result.volume}</strong>
                                    </div>
                                    <div className={styles.statRow}>
                                        <span>Enhancing Core:</span>
                                        <strong style={{ color: 'var(--color-error)' }}>{result.maskDetails.enhancing}</strong>
                                    </div>
                                    <div className={styles.statRow}>
                                        <span>Peritumoral Edema:</span>
                                        <strong style={{ color: 'var(--color-primary)' }}>{result.maskDetails.edema}</strong>
                                    </div>
                                </div>
                            </motion.div>
                        )}
                    </section>

                    <section className={styles.visualizationPanel}>
                        <div className={styles.vizCard}>
                            <div className={styles.vizHeader}>
                                <h3>3D Volumetric View</h3>
                                {result && <span className={styles.statusBadge}>Analysis Complete</span>}
                            </div>

                            <div className={styles.viewport}>
                                {analyzing ? (
                                    <div className={styles.scanningLine}></div>
                                ) : result ? (
                                    <div className={styles.brainOverlay}>
                                        {/* Symbolic representation of segmented brain tumor */}
                                        <div className={styles.tumorMask}></div>
                                    </div>
                                ) : (
                                    <div className={styles.emptyView}>
                                        <div className={styles.brainIcon}>🧠</div>
                                        <p>Awaiting Sequence Upload</p>
                                    </div>
                                )}
                            </div>

                            <div className={styles.vizControls}>
                                <span>Slice: 72/144</span>
                                <div className={styles.sliderPlaceholder}></div>
                            </div>
                        </div>

                        {result && (
                            <motion.div
                                className={styles.reportSection}
                                initial={{ opacity: 0 }}
                                animate={{ opacity: 1 }}
                            >
                                <h4>Diagnostic Analysis</h4>
                                <p><strong>Pathological Impression:</strong> {result.type}</p>
                                <p><strong>Anatomical Location:</strong> {result.location}</p>
                                <div className={styles.clinicalAdvice}>
                                    {result.recommendation}
                                </div>
                            </motion.div>
                        )}
                    </section>
                </div>
            </div>
        </div>
    )
}
