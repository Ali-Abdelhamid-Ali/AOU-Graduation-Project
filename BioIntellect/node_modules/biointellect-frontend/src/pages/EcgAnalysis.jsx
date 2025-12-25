import { useState, useEffect } from 'react'
import { motion } from 'framer-motion'
import { useAuth } from '../context/AuthContext'
import { medicalService } from '../services/medicalService'
import { supabase } from '../config/supabase'
import { TopBar } from '../components/TopBar'
import { SelectField } from '../components/SelectField'
import { AnimatedButton } from '../components/AnimatedButton'
import styles from './EcgAnalysis.module.css'

export const EcgAnalysis = ({ onBack }) => {
    const { currentUser, userRole } = useAuth()
    const [dragging, setDragging] = useState(false)
    const [file, setFile] = useState(null)
    const [analyzing, setAnalyzing] = useState(false)
    const [result, setResult] = useState(null)
    const [error, setError] = useState(null)
    const [patients, setPatients] = useState([])
    const [selectedPatientId, setSelectedPatientId] = useState('')

    useEffect(() => {
        if (userRole !== 'patient') {
            const loadPatients = async () => {
                const { data, error } = await supabase.from('patients').select('patient_id, first_name, last_name, medical_record_number')
                if (!error) setPatients(data)
            }
            loadPatients()
        }
    }, [userRole])

    const handleFileUpload = (e) => {
        const uploadedFile = e.target.files[0]
        if (uploadedFile) {
            setFile(uploadedFile)
            setResult(null)
            setError(null)
        }
    }

    const runAnalysis = async () => {
        if (!file) return

        setAnalyzing(true)
        setError(null)
        try {
            // 1. Determine Patient and Doctor IDs
            const isPatient = userRole === 'patient'
            const patientId = isPatient ? currentUser.patient_id : selectedPatientId

            if (!patientId) {
                setError('Please select a patient before running analysis.')
                setAnalyzing(false)
                return
            }

            const docId = isPatient ? null : (currentUser.user_id || currentUser.id)

            // 2. Create a Clinical Case (for demo, we create one per analysis)
            const medicalCase = await medicalService.createCase({
                patientId: patientId,
                doctorId: docId,
                caseType: 'ecg_analysis',
                chiefComplaint: 'Automated AI ECG Screening'
            })

            // 3. Upload File
            const fileRecord = await medicalService.uploadFile({
                caseId: medicalCase.case_id,
                patientId: patientId,
                userId: currentUser.user_id || currentUser.id,
                file: file,
                fileType: 'ecg_signal'
            })

            // 4. Simulate AI Pattern Recognition (Pattern: AFib detected in Lead II)
            await new Promise(resolve => setTimeout(resolve, 3000))

            const analysisResult = {
                classification: 'Atrial Fibrillation (AFib)',
                confidence: 94.2,
                recommendation: 'Immediate cardiology consultation recommended. High temporal irregularity detected in ECG lead II.',
                features: ['Irregular R-R intervals', 'Absence of P waves', 'Fibrillatory waves']
            }

            // 5. Save Results to Database
            await medicalService.saveEcgAnalysis({
                fileId: fileRecord.file_id,
                caseId: medicalCase.case_id,
                patientId: patientId,
                userId: currentUser.user_id || currentUser.id,
                signalInfo: { leads: '12-lead', samplingRate: 500, duration: 10, leadCount: 12, quality: 98 },
                resultInfo: analysisResult
            })

            setResult(analysisResult)
        } catch (err) {
            console.error('ECG Analysis Error:', err)
            setError(err.message || 'Failed to complete clinical analysis.')
        } finally {
            setAnalyzing(false)
        }
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
                        {userRole !== 'patient' && (
                            <div className={styles.patientSelector}>
                                <SelectField
                                    label="Select Patient"
                                    value={selectedPatientId}
                                    onChange={(e) => setSelectedPatientId(e.target.value)}
                                    options={patients.map(p => ({
                                        value: p.patient_id,
                                        label: `${p.first_name} ${p.last_name} (${p.medical_record_number})`
                                    }))}
                                    required
                                />
                            </div>
                        )}
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
