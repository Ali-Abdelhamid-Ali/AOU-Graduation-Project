import { useState, useEffect } from 'react'
import { motion } from 'framer-motion'
import { useAuth } from '@/store/AuthContext'
import { medicalService } from '@/services/medical.service'
import { mriSegmentationService } from '@/services/clinical.service'
import { Medical3DViewer } from '../../components/clinical/Medical3DViewer'
import { MriPatientView } from '../../components/clinical/MriPatientView'
import { MriDoctorView } from '../../components/clinical/MriDoctorView'
import { patientsAPI } from '@/services/api'
import { TopBar } from '@/components/layout/TopBar'
import { SelectField } from '@/components/ui/SelectField'
import { AnimatedButton } from '@/components/ui/AnimatedButton'
import styles from './MriSegmentation.module.css'

export const MriSegmentation = ({ onBack }) => {
    const { currentUser, userRole } = useAuth()

    // State
    const [files, setFiles] = useState({
        t1: null,
        t1ce: null,
        t2: null,
        flair: null
    })
    const [analyzing, setAnalyzing] = useState(false)
    const [result, setResult] = useState(null)
    const [error, setError] = useState(null)
    const [patients, setPatients] = useState([])
    const [selectedPatientId, setSelectedPatientId] = useState('')
    const [modelInfo, setModelInfo] = useState(null)
    const [showConfirmation, setShowConfirmation] = useState(false)
    const [doctorConfirmed, setDoctorConfirmed] = useState(false)
    const [savedResultId, setSavedResultId] = useState(null)

    // Load patients for non-patient users
    useEffect(() => {
        if (userRole !== 'patient') {
            const loadPatients = async () => {
                try {
                    const response = await patientsAPI.list()
                    if (response.success) {
                        setPatients(response.data)
                    }
                } catch (err) {
                    console.error('Failed to load patients:', err)
                }
            }
            loadPatients()
        }
    }, [userRole])

    // Load model info on mount
    useEffect(() => {
        const loadModelInfo = async () => {
            try {
                const info = await mriSegmentationService.getModelInfo()
                setModelInfo(info)
            } catch (err) {
                console.warn('Could not fetch model info:', err)
            }
        }
        loadModelInfo()
    }, [])

    const handleFileUpload = (modality) => (e) => {
        const uploadedFile = e.target.files[0]
        if (uploadedFile) {
            setFiles(prev => ({ ...prev, [modality]: uploadedFile }))
            setResult(null)
            setError(null)
        }
    }

    const allFilesUploaded = files.t1 && files.t1ce && files.t2 && files.flair

    const runAnalysis = async () => {
        if (!allFilesUploaded || !currentUser?.id) return

        setAnalyzing(true)
        setError(null)
        setResult(null)

        try {
            const isPatient = userRole === 'patient'
            const patientId = isPatient ? currentUser.id : selectedPatientId

            if (!patientId && !isPatient) {
                setError('Please select a patient before running analysis.')
                setAnalyzing(false)
                return
            }

            const docId = isPatient ? null : currentUser.id
            const medicalCase = await medicalService.createCase({
                patientId: patientId,
                doctorId: docId,
                caseType: 'mri_segmentation',
                chiefComplaint: 'Brain MRI Volumetric Study - AI Segmentation'
            })

            const segmentationResult = await mriSegmentationService.runSegmentation(
                files,
                { patientId }
            )

            const severity = mriSegmentationService.getSeverityClassification(segmentationResult)

            const formattedResult = {
                caseId: segmentationResult.case_id,
                modelVersion: segmentationResult.model_info.version,
                modelName: segmentationResult.model_info.name,
                timestamp: segmentationResult.inference_timestamp,
                tumorDetected: segmentationResult.tumor_detected,
                totalVolume: segmentationResult.total_volume_cm3,
                regions: segmentationResult.regions,
                confidence: segmentationResult.prediction_confidence,
                severity: severity,
                disclaimer: segmentationResult.disclaimer,
                requiresReview: segmentationResult.requires_review
            }

            const saved = await medicalService.saveMriAnalysis({
                caseId: medicalCase.id,
                patientId: patientId,
                userId: currentUser.id,
                scanInfo: { quality: 'excellent' },
                resultInfo: {
                    tumorDetected: segmentationResult.tumor_detected,
                    type: severity.label,
                    volume: segmentationResult.total_volume_cm3.toString(),
                    location: 'Brain',
                    maskDetails: {
                        edema: segmentationResult.regions.find(r => r.class_id === 2)?.volume_cm3 || 0,
                        enhancing: segmentationResult.regions.find(r => r.class_id === 3)?.volume_cm3 || 0,
                        necrosis: segmentationResult.regions.find(r => r.class_id === 1)?.volume_cm3 || 0
                    },
                    recommendation: severity.description
                }
            })

            setResult(formattedResult)
            setSavedResultId(saved.result.id)

            if (userRole !== 'patient') {
                setShowConfirmation(true)
            }

        } catch (err) {
            console.error('MRI Segmentation Error:', err)
            setError(err.message || 'Clinical neuro-imaging analysis failed.')
        } finally {
            setAnalyzing(false)
        }
    }

    const handleDoctorConfirmation = async () => {
        if (!doctorConfirmed || !savedResultId) return

        try {
            await medicalService.reviewResult('mri_results', savedResultId, {
                is_reviewed: true,
                doctor_agrees_with_ai: true
            })
            setShowConfirmation(false)
        } catch (err) {
            console.error('Failed to save confirmation:', err)
            setError('Failed to confirm result. Please try again.')
        }
    }

    return (
        <div className={styles.pageWrapper}>
            <TopBar onBack={onBack} userRole={userRole === 'doctor' ? 'Neurologist' : 'Patient'} />

            <div className={styles.container}>
                <header className={styles.header}>
                    <h1>Brain MRI Segmentation</h1>
                    <p>Powered by BioIntellect 3D U-Net Deep Learning Model</p>
                    {modelInfo && (
                        <span className={styles.versionBadge}>
                            v{modelInfo.version}
                        </span>
                    )}
                </header>

                <div className={styles.mainGrid}>
                    <section className={styles.controlPanel}>
                        {userRole !== 'patient' && (
                            <div className={styles.patientSelector} style={{ marginBottom: '1.5rem' }}>
                                <SelectField
                                    label="Select Patient"
                                    value={selectedPatientId}
                                    onChange={(e) => setSelectedPatientId(e.target.value)}
                                    options={patients.map(p => ({
                                        value: p.id,
                                        label: `${p.first_name} ${p.last_name || ''} (${p.mrn})`
                                    }))}
                                    required
                                />
                            </div>
                        )}

                        <div className={styles.card}>
                            <h3>MRI Modalities</h3>
                            <p className={styles.hint}>
                                Upload all 4 required MRI sequences for accurate segmentation.
                            </p>

                            <div className={styles.modalityGrid}>
                                {['t1', 't1ce', 't2', 'flair'].map(mod => (
                                    <div key={mod} className={styles.modalityUpload}>
                                        <label
                                            htmlFor={`upload-${mod}`}
                                            className={`${styles.uploadBox} ${files[mod] ? styles.hasFile : ''}`}
                                        >
                                            <input
                                                type="file"
                                                id={`upload-${mod}`}
                                                className={styles.hiddenInput}
                                                onChange={handleFileUpload(mod)}
                                                accept=".nii,.nii.gz"
                                            />
                                            <span className={styles.modLabel}>{mod.toUpperCase()}</span>
                                            {files[mod] ? (
                                                <span className={styles.checkmark}>✓</span>
                                            ) : (
                                                <span className={styles.uploadIcon}>📥</span>
                                            )}
                                        </label>
                                    </div>
                                ))}
                            </div>

                            {error && (
                                <div className={styles.errorMessage}>
                                    {error}
                                </div>
                            )}

                            <AnimatedButton
                                variant="primary"
                                isLoading={analyzing}
                                onClick={runAnalysis}
                                disabled={!allFilesUploaded}
                                style={{ width: '100%', marginTop: '2rem' }}
                            >
                                {analyzing ? 'Analyzing...' : 'Run Segmentation'}
                            </AnimatedButton>
                        </div>

                        {result && (
                            userRole === 'patient'
                                ? <MriPatientView result={result} />
                                : <MriDoctorView result={result} />
                        )}
                    </section>

                    <section className={styles.visualizationPanel}>
                        <div className={styles.vizCard}>
                            <div className={styles.vizHeader}>
                                <h3>3D Volumetric View</h3>
                                {result && (
                                    <span
                                        className={styles.statusBadge}
                                        style={{ backgroundColor: result.severity?.color }}
                                    >
                                        {result.severity?.label || 'Analysis Complete'}
                                    </span>
                                )}
                            </div>

                            <div className={styles.viewport}>
                                <Medical3DViewer result={result} isLoading={analyzing} />
                            </div>
                        </div>

                        {result && userRole !== 'patient' && (
                            <motion.div
                                className={styles.reportSection}
                                initial={{ opacity: 0 }}
                                animate={{ opacity: 1 }}
                            >
                                <h4>Clinical Summary</h4>
                                <div className={styles.clinicalAdvice}>
                                    <strong>Findings:</strong> {result.severity.label}
                                    <br />
                                    <strong>Recommendation:</strong> {result.severity.description}
                                </div>
                                <p className={styles.disclaimerSmall}>
                                    ⚠️ {result.disclaimer}
                                </p>
                            </motion.div>
                        )}
                    </section>
                </div>
            </div>

            {showConfirmation && (
                <div className={styles.modalOverlay}>
                    <motion.div
                        className={styles.confirmationModal}
                        initial={{ scale: 0.9, opacity: 0 }}
                        animate={{ scale: 1, opacity: 1 }}
                    >
                        <h3>Physician Review Confirmation</h3>
                        <p>
                            Before saving this result to the patient record, please confirm:
                        </p>
                        <label className={styles.checkboxLabel}>
                            <input
                                type="checkbox"
                                checked={doctorConfirmed}
                                onChange={(e) => setDoctorConfirmed(e.target.checked)}
                            />
                            I have reviewed the AI segmentation output and understand this is
                            a Clinical Decision Support tool, not a final diagnosis.
                        </label>
                        <div className={styles.modalActions}>
                            <button
                                className={styles.cancelBtn}
                                onClick={() => setShowConfirmation(false)}
                            >
                                Cancel
                            </button>
                            <button
                                className={styles.confirmBtn}
                                onClick={handleDoctorConfirmation}
                                disabled={!doctorConfirmed}
                            >
                                Confirm & Save
                            </button>
                        </div>
                    </motion.div>
                </div>
            )}
        </div>
    )
}
