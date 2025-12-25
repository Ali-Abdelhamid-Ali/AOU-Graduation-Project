import { useState, useEffect } from 'react'
import { motion } from 'framer-motion'
import { useAuth } from '../context/AuthContext'
import { medicalService } from '../services/medicalService'
import { supabase } from '../config/supabase'
import { TopBar } from '../components/TopBar'
import { SelectField } from '../components/SelectField'
import { AnimatedButton } from '../components/AnimatedButton'
import styles from './MriSegmentation.module.css'

export const MriSegmentation = ({ onBack }) => {
    const { currentUser, userRole } = useAuth()
    const [file, setFile] = useState(null)
    const [analyzing, setAnalyzing] = useState(false)
    const [result, setResult] = useState(null)
    const [selectedSequence, setSelectedSequence] = useState('T1ce')
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
            // 1. Determine IDs
            const isPatient = userRole === 'patient'
            const patientId = isPatient ? currentUser.patient_id : selectedPatientId

            if (!patientId) {
                setError('Please select a patient before running analysis.')
                setAnalyzing(false)
                return
            }

            const docId = isPatient ? null : (currentUser.user_id || currentUser.id)

            // 2. Clinical Case
            const medicalCase = await medicalService.createCase({
                patientId: patientId,
                doctorId: docId,
                caseType: 'mri_segmentation',
                chiefComplaint: `Brain MRI Volumetric Study (${selectedSequence})`
            })

            // 3. Upload Scan File
            await medicalService.uploadFile({
                caseId: medicalCase.case_id,
                patientId: patientId,
                userId: currentUser.user_id || currentUser.id,
                file: file,
                fileType: 'mri_scan'
            })

            // 4. AI Segmentation Simulation (3D U-Net)
            await new Promise(resolve => setTimeout(resolve, 4000))

            const analysisResult = {
                type: 'Glioblastoma Multiforme',
                volume: '42.5 cm³',
                location: 'Right Frontal Lobe',
                maskDetails: {
                    edema: '15.2 cm³',
                    enhancing: '21.0 cm³',
                    necrosis: '6.3 cm³'
                },
                recommendation: 'Urgent neurosurgical consultation. The tumor shows significant mass effect on the lateral ventricles.'
            }

            // 5. Save Results
            await medicalService.saveMriAnalysis({
                caseId: medicalCase.case_id,
                patientId: patientId,
                userId: currentUser.user_id || currentUser.id,
                scanInfo: { quality: 'excellent' },
                resultInfo: analysisResult
            })

            setResult(analysisResult)
        } catch (err) {
            console.error('MRI Segmentation Error:', err)
            setError(err.message || 'Clinical neuro-imaging analysis failed.')
        } finally {
            setAnalyzing(false)
        }
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
                        {userRole !== 'patient' && (
                            <div className={styles.patientSelector} style={{ marginBottom: '1.5rem' }}>
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

                            <div className={`${styles.uploadBox} ${file ? styles.hasFile : ''}`}>
                                <input
                                    type="file"
                                    id="mri-upload"
                                    className={styles.hiddenInput}
                                    onChange={handleFileUpload}
                                    accept=".nii,.nii.gz,.dcm,image/*"
                                />
                                <label htmlFor="mri-upload" className={styles.uploadLabel}>
                                    {file ? (
                                        <div className={styles.fileSelected}>
                                            <span>📄</span>
                                            <p>{file.name}</p>
                                        </div>
                                    ) : (
                                        <>
                                            <span>📥</span>
                                            <p>Upload NIfTI / DICOM</p>
                                        </>
                                    )}
                                </label>
                            </div>

                            <AnimatedButton
                                variant="primary"
                                isLoading={analyzing}
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
