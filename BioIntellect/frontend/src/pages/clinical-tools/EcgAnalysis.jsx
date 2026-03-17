import { useState, useEffect } from 'react'
import { motion } from 'framer-motion'
import { useAuth } from '@/store/AuthContext'
import { patientsAPI } from '@/services/api'
import { medicalService } from '@/services/medical.service'
import { getApiErrorMessage } from '@/utils/apiErrorUtils'
import { TopBar } from '@/components/layout/TopBar'
import { SelectField } from '@/components/ui/SelectField'
import { AnimatedButton } from '@/components/ui/AnimatedButton'
import { EcgDisclaimer } from '../../components/clinical/EcgDisclaimer'
import { PatientDisclaimer } from '../../components/clinical/PatientDisclaimer'
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
    const [patientLoadError, setPatientLoadError] = useState('')

    useEffect(() => {
        if (userRole !== 'patient') {
            const loadPatients = async () => {
                try {
                    const response = await patientsAPI.list({ is_active: true, limit: 100 })
                    if (response.success) {
                        const loadedPatients = response.data || []
                        setPatients(loadedPatients)
                        setSelectedPatientId((current) => current || loadedPatients[0]?.id || '')
                        setPatientLoadError(
                            loadedPatients.length
                                ? ''
                                : 'No active patient records are available for this doctor account yet.'
                        )
                    }
                } catch (err) {
                    console.error('Failed to load patients:', err)
                    setPatients([])
                    setPatientLoadError(
                        getApiErrorMessage(err, 'Failed to load the patient list.')
                    )
                }
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
        if (!file || !currentUser?.id) return

        setAnalyzing(true)
        setError(null)
        try {
            // 1. Determine Patient and Doctor IDs
            const isPatient = userRole === 'patient'
            const patientId = isPatient ? currentUser.id : selectedPatientId

            if (!patientId) {
                setError('Please select a patient before running analysis.')
                setAnalyzing(false)
                return
            }

            const docId = isPatient ? null : (currentUser.id)

            // 2. Create a Clinical Case via Backend API
            const medicalCase = await medicalService.createCase({
                patientId: patientId,
                doctorId: docId,
                hospitalId: currentUser.hospital_id,
                caseType: 'ecg_analysis',
                chiefComplaint: 'Automated AI ECG Screening'
            })

            // 3. Upload File via Backend API
            const fileRecord = await medicalService.uploadFile({
                caseId: medicalCase.id,
                patientId: patientId,
                userId: currentUser.user_id || currentUser.id,
                file: file,
                fileType: 'ecg'
            })

            // 4. Run ECG Analysis via Backend API
            const analysisData = await medicalService.saveEcgAnalysis({
                fileId: fileRecord.id,
                caseId: medicalCase.id,
                patientId: patientId,
                userId: currentUser.user_id || currentUser.id
            })

            // Extract result from API response
            const aiResult = analysisData.result
            const classification =
                typeof aiResult.rhythm_classification === 'string' &&
                    aiResult.rhythm_classification.trim()
                    ? aiResult.rhythm_classification.trim()
                    : null
            const confidence =
                typeof aiResult.rhythm_confidence === 'number'
                    ? aiResult.rhythm_confidence * 100
                    : null
            const features = Array.isArray(aiResult.detected_conditions)
                ? aiResult.detected_conditions
                    .map((condition) => condition?.condition)
                    .filter(Boolean)
                : []

            setResult({
                classification,
                confidence,
                recommendation:
                    typeof aiResult.ai_interpretation === 'string' &&
                        aiResult.ai_interpretation.trim()
                        ? aiResult.ai_interpretation.trim()
                        : null,
                features,
                isComplete: Boolean(classification) && confidence !== null,
            })
        } catch (err) {
            console.error('ECG Analysis Error:', err)
            setError(err.message || 'Failed to complete clinical analysis.')
        } finally {
            setAnalyzing(false)
        }
    }

    return (
        <div className={styles.pageWrapper}>
            <TopBar
                onBack={onBack}
                userRole={userRole === 'doctor' ? 'Cardiologist' : userRole === 'patient' ? 'Patient' : 'Clinical Staff'}
            />

            <div className={styles.container}>
                <header className={styles.header}>
                    <h1>Cardiac Arrhythmia Detection</h1>
                    <p>Powered by BioIntellect CNN-Transformer Architecture</p>
                </header>

                {userRole === 'patient' ? <PatientDisclaimer /> : <EcgDisclaimer />}

                <div className={styles.mainGrid}>
                    <section className={styles.uploadCard}>
                        {userRole !== 'patient' && (
                            <div className={styles.patientSelector}>
                                <SelectField
                                    label="Select Patient"
                                    value={selectedPatientId}
                                    onChange={(e) => setSelectedPatientId(e.target.value)}
                                    options={patients.map(p => ({
                                        value: p.id,
                                        label: `${p.first_name} ${p.last_name} (${p.mrn})`
                                    }))}
                                    disabled={!patients.length}
                                    error={patientLoadError || undefined}
                                    helperText={
                                        !patientLoadError
                                            ? 'Choose the patient whose ECG study you want to analyze.'
                                            : undefined
                                    }
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

                        {error && (
                            <div className={styles.errorMessage}>{error}</div>
                        )}

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
                                    <span className={styles.label}>
                                        {result.isComplete ? 'Diagnostic Result' : 'Analysis Status'}
                                    </span>
                                    {result.isComplete ? (
                                        <div className={styles.confidenceBadge}>
                                            {result.confidence.toFixed(1)}% Confidence
                                        </div>
                                    ) : (
                                        <div className={styles.pendingBadge}>Awaiting analysis</div>
                                    )}
                                </div>
                                <h2 className={styles.classification}>
                                    {result.isComplete
                                        ? result.classification
                                        : 'Awaiting analysis'}
                                </h2>
                                {result.features.length > 0 ? (
                                    <div className={styles.featuresList}>
                                        {result.features.map((feature, index) => (
                                            <span key={index} className={styles.featureTag}>{feature}</span>
                                        ))}
                                    </div>
                                ) : null}
                                <div className={styles.recommendation}>
                                    <strong>{result.isComplete ? 'Clinical Advice:' : 'Status:'}</strong>
                                    <p>
                                        {result.isComplete
                                            ? result.recommendation || 'No clinical interpretation was returned.'
                                            : 'Analysis pending or incomplete. The ECG data was received, but the diagnostic output is not ready yet.'}
                                    </p>
                                </div>

                                <div className={styles.chartPlaceholder}>
                                    <p>Waveform preview is not available in this interface.</p>
                                </div>
                            </motion.div>
                        ) : (
                            <div className={styles.emptyState}>
                                <p>No ECG study analyzed yet. Upload a signal file to start the clinical workflow.</p>
                            </div>
                        )}
                    </section>
                </div>
            </div>
        </div>
    )
}
