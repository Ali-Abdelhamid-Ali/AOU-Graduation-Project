import { useState, useEffect } from 'react'
import { motion } from 'framer-motion'
import { useAuth } from '../context/AuthContext'
import { medicalService } from '../services/medicalService'
import { patientsAPI } from '../services/api'
import { TopBar } from '../components/TopBar'
import { SelectField } from '../components/SelectField'
import { AnimatedButton } from '../components/AnimatedButton'
import styles from './MriSegmentation.module.css'

export const MriSegmentation = ({ onBack }) => {
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
                try {
                    const response = await patientsAPI.list({ is_active: true, limit: 100 })
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
            const isPatient = userRole === 'patient'
            const patientId = isPatient ? currentUser.id : selectedPatientId

            if (!patientId) {
                setError('Please select a patient before running analysis.')
                setAnalyzing(false)
                return
            }

            const docId = isPatient ? null : (currentUser.id)

            // Create a Medical Case
            const medicalCase = await medicalService.createCase({
                patientId: patientId,
                doctorId: docId,
                caseType: 'mri_segmentation',
                chiefComplaint: 'AI-Powered MRI Brain Segmentation'
            })

            // Upload File
            const fileRecord = await medicalService.uploadFile({
                caseId: medicalCase.id,
                patientId: patientId,
                userId: currentUser.user_id || currentUser.id,
                file: file,
                fileType: 'mri_scan'
            })

            // Run MRI Segmentation Analysis
            const analysisData = await medicalService.saveMriAnalysis({
                fileId: fileRecord.id,
                caseId: medicalCase.id,
                patientId: patientId,
                scanInfo: {
                    type: 'brain',
                    sequence: 'T1ce'
                }
            })

            const aiResult = analysisData.result

            setResult({
                segmentedRegions: aiResult.segmented_regions || [],
                abnormalities: aiResult.detected_abnormalities || [],
                interpretation: aiResult.ai_interpretation,
                recommendations: aiResult.ai_recommendations || [],
                measurements: aiResult.measurements || {},
                severityScore: aiResult.severity_score
            })
        } catch (err) {
            console.error('MRI Analysis Error:', err)
            setError(err.message || 'Failed to complete MRI analysis.')
        } finally {
            setAnalyzing(false)
        }
    }

    return (
        <div className={styles.pageWrapper}>
            <TopBar onBack={onBack} userRole="Neurologist" />

            <div className={styles.container}>
                <header className={styles.header}>
                    <h1>MRI Brain Tumor Segmentation</h1>
                    <p>3D U-Net Architecture with Multi-Modal Fusion</p>
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
                                        value: p.id,
                                        label: `${p.first_name} ${p.last_name} (${p.mrn})`
                                    }))}
                                    required
                                />
                            </div>
                        )}
                        <h3>Upload MRI Scans</h3>
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
                            <div className={styles.uploadIcon}>🧠</div>
                            {file ? (
                                <div className={styles.fileInfo}>
                                    <span className={styles.fileName}>{file.name}</span>
                                    <span className={styles.fileSize}>{(file.size / 1024).toFixed(2)} KB</span>
                                </div>
                            ) : (
                                <p>Upload MRI DICOM/NIfTI Files (.nii, .dcm)</p>
                            )}
                            <input type="file" onChange={handleFileUpload} className={styles.hiddenInput} id="mriUpload" accept=".nii,.nii.gz,.dcm" />
                            <label htmlFor="mriUpload" className={styles.browseButton}>Select File</label>
                        </div>

                        <div className={styles.modalityInfo}>
                            <h4>Accepted Modalities</h4>
                            <div className={styles.modalityTags}>
                                <span>T1</span>
                                <span>T1ce</span>
                                <span>T2</span>
                                <span>FLAIR</span>
                            </div>
                        </div>

                        {error && <div className={styles.errorMessage}>{error}</div>}

                        {file && !result && (
                            <AnimatedButton
                                variant="primary"
                                isLoading={analyzing}
                                onClick={runAnalysis}
                                style={{ width: '100%', marginTop: '1.5rem' }}
                            >
                                Run Segmentation
                            </AnimatedButton>
                        )}
                    </section>

                    <section className={styles.resultsArea}>
                        {analyzing ? (
                            <div className={styles.analyzingState}>
                                <div className={styles.loader}></div>
                                <h4>Running 3D Convolutions...</h4>
                                <p>Analyzing volumetric data with attention mechanisms</p>
                            </div>
                        ) : result ? (
                            <motion.div
                                className={styles.resultCard}
                                initial={{ opacity: 0, scale: 0.95 }}
                                animate={{ opacity: 1, scale: 1 }}
                            >
                                <div className={styles.resultHeader}>
                                    <span className={styles.label}>Segmentation Results</span>
                                    {result.severityScore && (
                                        <div className={styles.severityBadge}>
                                            Severity: {result.severityScore.toFixed(1)}%
                                        </div>
                                    )}
                                </div>

                                <div className={styles.segmentationGrid}>
                                    {result.segmentedRegions.map((region, i) => (
                                        <div key={i} className={styles.segmentItem}>
                                            <span className={styles.regionName}>{region.region?.replace(/_/g, ' ')}</span>
                                            <span className={styles.regionVolume}>{region.volume_ml?.toFixed(1)} ml</span>
                                        </div>
                                    ))}
                                </div>

                                {result.abnormalities.length > 0 && (
                                    <div className={styles.abnormalities}>
                                        <h4>Detected Abnormalities</h4>
                                        {result.abnormalities.map((ab, i) => (
                                            <div key={i} className={styles.abnormalityItem}>
                                                <strong>{ab.finding}</strong>
                                                <span>Location: {ab.location}</span>
                                                <span>Confidence: {(ab.confidence * 100).toFixed(0)}%</span>
                                            </div>
                                        ))}
                                    </div>
                                )}

                                <div className={styles.interpretation}>
                                    <h4>AI Interpretation</h4>
                                    <p>{result.interpretation}</p>
                                </div>

                                {result.recommendations.length > 0 && (
                                    <div className={styles.recommendations}>
                                        <h4>Recommendations</h4>
                                        <ul>
                                            {result.recommendations.map((rec, i) => (
                                                <li key={i}>{rec}</li>
                                            ))}
                                        </ul>
                                    </div>
                                )}

                                <div className={styles.visualPlaceholder}>
                                    <div className={styles.brainSlice}></div>
                                    <p>3D Volumetric Segmentation Overlay</p>
                                </div>
                            </motion.div>
                        ) : (
                            <div className={styles.emptyState}>
                                <p>Upload MRI scans to begin AI-powered segmentation and tumor detection.</p>
                            </div>
                        )}
                    </section>
                </div>
            </div>
        </div>
    )
}
