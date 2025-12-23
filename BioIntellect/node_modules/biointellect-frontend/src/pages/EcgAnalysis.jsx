import { useState } from 'react'
import { motion } from 'framer-motion'
import { TopBar } from '../components/TopBar'
import { AnimatedButton } from '../components/AnimatedButton'
import styles from './EcgAnalysis.module.css'

export const EcgAnalysis = ({ onBack }) => {
    const [dragging, setDragging] = useState(false)
    const [file, setFile] = useState(null)
    const [analyzing, setAnalyzing] = useState(false)
    const [result, setResult] = useState(null)

    const handleFileUpload = (e) => {
        const uploadedFile = e.target.files[0]
        if (uploadedFile) {
            setFile(uploadedFile)
            setResult(null)
        }
    }

    const runAnalysis = () => {
        setAnalyzing(true)
        // Simulate CNN-Transformer analysis
        setTimeout(() => {
            setResult({
                classification: 'Atrial Fibrillation (AFib)',
                confidence: 94.2,
                recommendation: 'Immediate cardiology consultation recommended. High temporal irregularity detected in ECG lead II.',
                features: ['Irregular R-R intervals', 'Absence of P waves', 'Fibrillatory waves']
            })
            setAnalyzing(false)
        }, 3000)
    }

    return (
        <div className={styles.pageWrapper}>
            <TopBar onBack={onBack} userRole="Cardiologist" />

            <div className={styles.container}>
                <header className={styles.header}>
                    <h1>Cardiac Arrhythmia Detection</h1>
                    <p>Powered by BioIntellect CNN-Transformer Architecture</p>
                </header>

                <div className={styles.mainGrid}>
                    <section className={styles.uploadCard}>
                        <h3>Upload ECG Data</h3>
                        <div
                            className={`${styles.dropZone} ${dragging ? styles.dragActive : ''} ${file ? styles.hasFile : ''}`}
                            onDragOver={(e) => { e.preventDefault(); setDragging(true); }}
                            onDragLeave={() => setDragging(false)}
                            onDrop={(e) => {
                                e.preventDefault()
                                setDragging(false)
                                if (e.dataTransfer.files[0]) setFile(e.dataTransfer.files[0])
                            }}
                        >
                            <div className={styles.uploadIcon}>📈</div>
                            {file ? (
                                <div className={styles.fileInfo}>
                                    <span className={styles.fileName}>{file.name}</span>
                                    <span className={styles.fileSize}>{(file.size / 1024).toFixed(2)} KB</span>
                                </div>
                            ) : (
                                <p>Drag & drop ECG signal file (WFDB, CSV, or Raw) or <strong>Browse</strong></p>
                            )}
                            <input type="file" onChange={handleFileUpload} className={styles.hiddenInput} id="ecgUpload" />
                            <label htmlFor="ecgUpload" className={styles.browseButton}>Select File</label>
                        </div>

                        {file && !result && (
                            <AnimatedButton
                                variant="primary"
                                isLoading={analyzing}
                                onClick={runAnalysis}
                                style={{ width: '100%', marginTop: '1.5rem' }}
                            >
                                Run AI Analysis
                            </AnimatedButton>
                        )}
                    </section>

                    <section className={styles.resultsArea}>
                        {analyzing ? (
                            <div className={styles.analyzingState}>
                                <div className={styles.loader}></div>
                                <h4>Processing Temporal Sequences...</h4>
                                <p>Deploying transformer models for pattern recognition</p>
                            </div>
                        ) : result ? (
                            <motion.div
                                className={styles.resultCard}
                                initial={{ opacity: 0, scale: 0.95 }}
                                animate={{ opacity: 1, scale: 1 }}
                            >
                                <div className={styles.resultHeader}>
                                    <span className={styles.label}>Diagnostic Result</span>
                                    <div className={styles.confidenceBadge}>{result.confidence}% Confidence</div>
                                </div>
                                <h2 className={styles.classification}>{result.classification}</h2>
                                <div className={styles.featuresList}>
                                    {result.features.map((f, i) => (
                                        <span key={i} className={styles.featureTag}>{f}</span>
                                    ))}
                                </div>
                                <div className={styles.recommendation}>
                                    <strong>Clinical Advice:</strong>
                                    <p>{result.recommendation}</p>
                                </div>

                                <div className={styles.chartPlaceholder}>
                                    {/* Placeholder for ECG Waveform Visualization */}
                                    <div className={styles.wave}></div>
                                    <p>ECG Waveform Visualization Lead II</p>
                                </div>
                            </motion.div>
                        ) : (
                            <div className={styles.emptyState}>
                                <p>No data analyzed yet. Upload an ECG signal to start diagnostic detection.</p>
                            </div>
                        )}
                    </section>
                </div>
            </div>
        </div>
    )
}
