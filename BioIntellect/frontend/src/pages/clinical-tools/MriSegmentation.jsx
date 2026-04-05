import { lazy, Suspense, useEffect, useMemo, useState } from 'react'
import { motion } from 'framer-motion'
import { useAuth } from '@/store/AuthContext'
import { medicalService } from '@/services/medical.service'
import { mriSegmentationService } from '@/services/clinical.service'
import { getApiErrorMessage } from '@/utils/apiErrorUtils'
import { ROLES } from '@/config/roles'
import { MriPatientView } from '../../components/clinical/MriPatientView'
import { MriDoctorView } from '../../components/clinical/MriDoctorView'
import { patientsAPI, usersAPI } from '@/services/api'
import { TopBar } from '@/components/layout/TopBar'
import { SelectField } from '@/components/ui/SelectField'
import { AnimatedButton } from '@/components/ui/AnimatedButton'
import styles from './MriSegmentation.module.css'

const MriVolumeViewer = lazy(() =>
  import('../../components/clinical/MriVolumeViewer').then((module) => ({
    default: module.MriVolumeViewer,
  }))
)

const MODALITIES = ['t1', 't1ce', 't2', 'flair']

const MODALITY_DETAILS = {
  t1: {
    title: 'T1',
    description: 'Baseline anatomy and structural boundaries.',
  },
  t1ce: {
    title: 'T1CE',
    description: 'Post-contrast sequence that highlights enhancing tumor tissue.',
  },
  t2: {
    title: 'T2',
    description: 'Fluid-sensitive view for edema and tissue heterogeneity.',
  },
  flair: {
    title: 'FLAIR',
    description: 'Suppresses CSF to make lesions and edema easier to isolate.',
  },
}

const WORKFLOW_STEPS = [
  {
    id: 'segment',
    title: 'Segmentation',
    description: 'Runs the 3D U-Net on the four uploaded sequences.',
  },
  {
    id: 'case',
    title: 'Case Record',
    description: 'Creates or prepares the clinical case shell.',
  },
  {
    id: 'uploads',
    title: 'Source Files',
    description: 'Stores each MRI sequence in the patient record.',
  },
  {
    id: 'scan',
    title: 'MRI Scan',
    description: 'Creates the MRI scan row and attaches sequence metadata.',
  },
  {
    id: 'result',
    title: 'Structured Result',
    description: 'Persists the segmentation findings and measurements.',
  },
]

const EMPTY_WORKFLOW_STATUS = {
  segment: 'idle',
  case: 'idle',
  uploads: 'idle',
  scan: 'idle',
  result: 'idle',
}

const WORKFLOW_STATUS_LABELS = {
  idle: 'Pending',
  running: 'In Progress',
  success: 'Done',
  error: 'Needs Attention',
  skipped: 'On-demand',
}

const EMPTY_SOURCE_FILE_STATUS = {
  t1: 'idle',
  t1ce: 'idle',
  t2: 'idle',
  flair: 'idle',
}

const SOURCE_FILE_STATUS_LABELS = {
  idle: 'Not started',
  pending: 'Pending',
  saving: 'Saving',
  saved: 'Saved',
  failed: 'Failed',
}

const buildDetectedAbnormalities = (regions = []) =>
  regions
    .filter((region) => region.present && Number(region.volume_cm3 || 0) > 0)
    .map((region) => ({
      name: region.class_name,
      class_id: region.class_id,
      volume_cm3: region.volume_cm3,
      percentage: region.percentage,
      severity:
        region.class_id === 3
          ? 'high'
          : region.class_id === 2
            ? 'moderate'
            : 'low',
    }))

const buildSeverityScore = (severity, totalVolume) => {
  const clampedVolume = Math.min(Number(totalVolume || 0), 40)
  const baseScore = {
    normal: 5,
    low: 35,
    moderate: 60,
    high: 85,
  }[severity.level] || 0

  return Math.min(100, Math.round(baseScore + clampedVolume * 0.4))
}

const formatSegmentationResult = (segmentationResult) => {
  const severity = mriSegmentationService.getSeverityClassification(segmentationResult)

  return {
    caseId: segmentationResult.case_id,
    modelVersion: segmentationResult.model_info?.version,
    modelName: segmentationResult.model_info?.name,
    timestamp: segmentationResult.inference_timestamp,
    tumorDetected: segmentationResult.tumor_detected,
    totalVolume: segmentationResult.total_volume_cm3,
    regions: segmentationResult.regions || [],
    confidence:
      segmentationResult.prediction_confidence?.overall ??
      segmentationResult.prediction_confidence ??
      0,
    confidenceBreakdown: segmentationResult.prediction_confidence || {},
    severity,
    disclaimer: segmentationResult.disclaimer,
    requiresReview: segmentationResult.requires_review,
    visualization: segmentationResult.visualization,
    measurements: segmentationResult.measurements || {},
    processingMetadata: segmentationResult.processing_metadata || {},
    aiInterpretation: segmentationResult.ai_interpretation,
    aiRecommendations: segmentationResult.ai_recommendations || [],
    metrics: segmentationResult.metrics || {},
    rawOutput: segmentationResult,
  }
}

const formatPercent = (value) =>
  typeof value === 'number' ? `${(value * 100).toFixed(1)}%` : 'N/A'

const formatVolume = (value) => `${Number(value || 0).toFixed(2)} cm3`

const formatFileSize = (file) => {
  if (!file?.size) return 'No file selected'

  const sizeInMb = file.size / (1024 * 1024)
  if (sizeInMb >= 1) {
    return `${sizeInMb.toFixed(2)} MB`
  }

  return `${(file.size / 1024).toFixed(1)} KB`
}

const formatTimestamp = (value) => {
  if (!value) return 'Not available'

  try {
    return new Intl.DateTimeFormat('en-GB', {
      dateStyle: 'medium',
      timeStyle: 'short',
    }).format(new Date(value))
  } catch {
    return value
  }
}

const extractErrorDetails = (error, fallback = '') => {
  const candidates = [error?.detail, error?.message, error]

  for (const candidate of candidates) {
    if (typeof candidate === 'string' && candidate.trim()) {
      return candidate.trim()
    }

    if (candidate && typeof candidate === 'object') {
      if (typeof candidate.message === 'string' && candidate.message.trim()) {
        return candidate.message.trim()
      }

      try {
        return JSON.stringify(candidate, null, 2)
      } catch {
        continue
      }
    }
  }

  return fallback
}

const normalizeErrorMessage = (error, fallback) => {
  const message = extractErrorDetails(error, fallback)
  if (!message) {
    return fallback
  }

  if (
    message.includes('application/octet-stream is not supported') ||
    message.includes('application/x-gzip')
  ) {
    return 'Segmentation completed, but saving the MRI source files failed.'
  }

  return message
}

const getFeedbackTone = (status) => {
  if (status === 'failed') return 'warning'
  if (status === 'saved') return 'success'
  return 'info'
}

const extractPatientRows = (payload) => {
  if (Array.isArray(payload)) return payload
  if (Array.isArray(payload?.data)) return payload.data
  if (Array.isArray(payload?.data?.data)) return payload.data.data
  if (Array.isArray(payload?.patients)) return payload.patients
  if (Array.isArray(payload?.data?.patients)) return payload.data.patients
  return []
}

export const MriSegmentation = ({ onBack }) => {
  const { currentUser, userRole } = useAuth()
  const [files, setFiles] = useState({
    t1: null,
    t1ce: null,
    t2: null,
    flair: null,
  })
  const [analyzing, setAnalyzing] = useState(false)
  const [result, setResult] = useState(null)
  const [analysisError, setAnalysisError] = useState(null)
  const [patients, setPatients] = useState([])
  const [selectedPatientId, setSelectedPatientId] = useState('')
  const [patientLoadError, setPatientLoadError] = useState('')
  const [modelInfo, setModelInfo] = useState(null)
  const [savedResultId, setSavedResultId] = useState(null)
  const [workflowStatus, setWorkflowStatus] = useState(EMPTY_WORKFLOW_STATUS)
  const [workflowMessage, setWorkflowMessage] = useState(
    'Upload the four MRI sequences to prepare the 3D segmentation workflow.'
  )
  const [saveToRecord, setSaveToRecord] = useState(true)
  const [recordSyncState, setRecordSyncState] = useState({
    status: 'idle',
    message: '',
    technicalDetails: '',
  })
  const [persistenceDraft, setPersistenceDraft] = useState(null)
  const [sourceFileStatus, setSourceFileStatus] = useState({
    ...EMPTY_SOURCE_FILE_STATUS,
  })

  useEffect(() => {
    if (userRole !== 'patient') {
      let cancelled = false

      const loadPatients = async () => {
        const scopedParams = {
          limit: 100,
          offset: 0,
          is_active: true,
          ...(currentUser?.hospital_id ? { hospital_id: currentUser.hospital_id } : {}),
        }

        const fallbackParams = {
          limit: 100,
          offset: 0,
        }

        let loadedPatients = []
        let lastError = null

        try {
          const response = await patientsAPI.list(scopedParams)
          loadedPatients = extractPatientRows(response)
        } catch (loadError) {
          lastError = loadError

          // Fallbacks are attempted only on actual errors, not on empty results.
          try {
            const response = await patientsAPI.list(fallbackParams)
            loadedPatients = extractPatientRows(response)
            lastError = null
          } catch (fallbackError) {
            lastError = fallbackError
          }

          if (!loadedPatients.length) {
            try {
              const response = await usersAPI.list('patients', scopedParams)
              loadedPatients = extractPatientRows(response)
            } catch (usersLoadError) {
              lastError = usersLoadError
            }
          }
        }

        if (cancelled) return

        if (loadedPatients.length) {
          setPatients(loadedPatients)
          setSelectedPatientId((current) => current || loadedPatients[0]?.id || '')
          setPatientLoadError('')
          return
        }

        setPatients([])
        setSelectedPatientId('')
        if (lastError) {
          console.error('Failed to load patients:', lastError)
          setPatientLoadError(
            getApiErrorMessage(lastError, 'Failed to load the patient list.')
          )
        } else {
          setPatientLoadError('No patient records are available for this doctor account yet.')
        }
      }

      loadPatients()

      return () => {
        cancelled = true
      }
    }

    return undefined
  }, [currentUser?.hospital_id, userRole])

  useEffect(() => {
    let cancelled = false

    const loadModelInfo = async () => {
      try {
        const info = await mriSegmentationService.getModelInfo()
        if (cancelled) return
        setModelInfo(info)
      } catch (loadError) {
        console.warn('Could not fetch model info:', loadError)
      }
    }

    loadModelInfo()

    return () => {
      cancelled = true
    }
  }, [])

  const selectedPatient = useMemo(() => {
    if (userRole === ROLES.PATIENT) {
      return currentUser || null
    }

    return patients.find((patient) => patient.id === selectedPatientId) || null
  }, [currentUser, patients, selectedPatientId, userRole])

  const uploadedCount = useMemo(
    () => MODALITIES.filter((modality) => Boolean(files[modality])).length,
    [files]
  )

  const allFilesUploaded = uploadedCount === MODALITIES.length

  const presentRegions = useMemo(
    () =>
      (result?.regions || []).filter(
        (region) => region.present && Number(region.volume_cm3 || 0) > 0
      ),
    [result]
  )

  const workflowStepsInPlay = useMemo(
    () =>
      WORKFLOW_STEPS.filter((step) => workflowStatus[step.id] !== 'skipped').length ||
      1,
    [workflowStatus]
  )

  const completedWorkflowSteps = useMemo(
    () =>
      WORKFLOW_STEPS.filter((step) => workflowStatus[step.id] === 'success').length,
    [workflowStatus]
  )

  const workflowProgress = Math.round(
    (completedWorkflowSteps / workflowStepsInPlay) * 100
  )

  const overviewCards = result
    ? [
        {
          label: 'Severity',
          value: result.severity?.label || 'Analysis Complete',
          helper: 'Clinical triage impression based on segmented tissue burden.',
        },
        {
          label: 'Confidence',
          value: formatPercent(
            typeof result.confidence === 'number'
              ? result.confidence
              : result.confidenceBreakdown?.overall
          ),
          helper: 'Overall certainty returned by the segmentation service.',
        },
        {
          label: 'Total Volume',
          value: formatVolume(result.totalVolume),
          helper: 'Combined segmented abnormal volume across active classes.',
        },
        {
          label: 'Detected Regions',
          value: String(presentRegions.length),
          helper: 'Number of segmented classes with non-zero volume.',
        },
      ]
    : []

  const confidenceBreakdown = result
    ? [
        {
          label: 'Overall confidence',
          value: formatPercent(result.confidenceBreakdown?.overall),
          helper: 'Composite confidence score from the model output.',
        },
        {
          label: 'Tumor presence',
          value: formatPercent(result.confidenceBreakdown?.tumor_presence),
          helper: 'How strongly the model believes abnormal tissue is present.',
        },
        {
          label: 'Segmentation quality',
          value: formatPercent(result.confidenceBreakdown?.segmentation_quality),
          helper: 'How internally consistent the produced mask appears.',
        },
      ]
    : []

  const measurementItems = result
    ? [
        {
          label: 'Largest diameter',
          value: result.measurements?.largest_diameter_mm
            ? `${Number(result.measurements.largest_diameter_mm).toFixed(1)} mm`
            : 'Not available',
        },
        {
          label: 'Voxel volume',
          value: result.measurements?.voxel_volume_mm3
            ? `${Number(result.measurements.voxel_volume_mm3).toFixed(4)} mm3`
            : 'Not available',
        },
        {
          label: 'Effective spacing',
          value: Array.isArray(result.measurements?.effective_spacing_mm)
            ? result.measurements.effective_spacing_mm
                .map((item) => Number(item || 0).toFixed(2))
                .join(' x ') + ' mm'
            : 'Not available',
        },
        {
          label: 'Inference time',
          value: formatTimestamp(result.timestamp),
        },
      ]
    : []

  const syncActionLabel =
    recordSyncState.status === 'failed'
      ? 'Retry Record Sync'
      : 'Save to Patient Record'

  const showSyncAction =
    Boolean(result) && !savedResultId && (recordSyncState.status === 'failed' || !saveToRecord)

  const resetRunState = () => {
    setResult(null)
    setAnalysisError(null)
    setSavedResultId(null)
    setWorkflowStatus(EMPTY_WORKFLOW_STATUS)
    setWorkflowMessage(
      'Upload the four MRI sequences to prepare the 3D segmentation workflow.'
    )
    setRecordSyncState({ status: 'idle', message: '', technicalDetails: '' })
    setPersistenceDraft(null)
    setSourceFileStatus({ ...EMPTY_SOURCE_FILE_STATUS })
  }

  const updateWorkflowStep = (step, status) => {
    setWorkflowStatus((current) => ({
      ...current,
      [step]: status,
    }))
  }

  const hydrateSourceFileStatus = (uploadedFiles = {}, activeModality = null) => {
    setSourceFileStatus(
      MODALITIES.reduce((nextState, modality) => {
        if (uploadedFiles[modality]) {
          nextState[modality] = 'saved'
        } else if (activeModality === modality) {
          nextState[modality] = 'saving'
        } else {
          nextState[modality] = 'pending'
        }

        return nextState
      }, {})
    )
  }

  const handleFileUpload = (modality) => (event) => {
    const uploadedFile = event.target.files[0]
    if (!uploadedFile) return

    setFiles((current) => ({ ...current, [modality]: uploadedFile }))
    resetRunState()
  }

  const handleClearFiles = () => {
    setFiles({
      t1: null,
      t1ce: null,
      t2: null,
      flair: null,
    })
    resetRunState()
  }

  const persistSegmentationToRecord = async (draft) => {
    if (!draft) return null

    const hospitalId = currentUser?.hospital_id || selectedPatient?.hospital_id
    const workingDraft = {
      ...draft,
      uploadedFiles: { ...(draft.uploadedFiles || {}) },
    }

    let activeStep = 'case'
    let activeUploadModality = null
    setRecordSyncState({
      status: 'saving',
      message: 'Saving AI output, source files, and structured findings to the patient record.',
      technicalDetails: '',
    })
    hydrateSourceFileStatus(workingDraft.uploadedFiles)

    try {
      if (!workingDraft.medicalCase) {
        activeStep = 'case'
        updateWorkflowStep('case', 'running')
        setWorkflowMessage('Creating the clinical case shell for this MRI study.')
        workingDraft.medicalCase = await medicalService.createCase({
          patientId: workingDraft.patientId,
          doctorId: workingDraft.isPatient ? null : currentUser?.id,
          hospitalId,
          caseType: 'mri_segmentation',
          chiefComplaint: 'Brain MRI volumetric study - AI segmentation',
        })
        updateWorkflowStep('case', 'success')
        setPersistenceDraft({ ...workingDraft, uploadedFiles: { ...workingDraft.uploadedFiles } })
      }

      activeStep = 'uploads'
      updateWorkflowStep('uploads', 'running')
      const uploadedFiles = []

      for (const modality of MODALITIES) {
        if (!workingDraft.uploadedFiles[modality]) {
          activeUploadModality = modality
          hydrateSourceFileStatus(workingDraft.uploadedFiles, modality)
          setWorkflowMessage(
            `Uploading ${MODALITY_DETAILS[modality].title} to the patient record.`
          )
          const fileRecord = await medicalService.uploadFile({
            caseId: workingDraft.medicalCase.id,
            patientId: workingDraft.patientId,
            userId: currentUser?.user_id || currentUser?.id,
            file: files[modality],
            fileType: 'mri',
            description: `${MODALITY_DETAILS[modality].title} modality uploaded for MRI segmentation`,
          })

          workingDraft.uploadedFiles[modality] = {
            modality,
            file: files[modality],
            record: fileRecord,
          }
          activeUploadModality = null
          hydrateSourceFileStatus(workingDraft.uploadedFiles)
          setPersistenceDraft({
            ...workingDraft,
            uploadedFiles: { ...workingDraft.uploadedFiles },
          })
        }

        uploadedFiles.push(workingDraft.uploadedFiles[modality])
      }

      updateWorkflowStep('uploads', 'success')

      if (!workingDraft.scan) {
        activeStep = 'scan'
        updateWorkflowStep('scan', 'running')
        setWorkflowMessage('Building the MRI scan record and attaching modality metadata.')

        const representativeUpload =
          uploadedFiles.find((item) => item.modality === 'flair') || uploadedFiles[0]

        workingDraft.scan = await medicalService.createMriScan({
          fileId: representativeUpload.record.id,
          patientId: workingDraft.patientId,
          caseId: workingDraft.medicalCase.id,
          dicomMetadata: {
            source: 'frontend_upload',
            ai_case_id: workingDraft.segmentationResult.case_id,
            primary_filename: representativeUpload.file.name,
            available_modalities: uploadedFiles.map((item) => item.modality),
            modality_file_ids: Object.fromEntries(
              uploadedFiles.map((item) => [item.modality, item.record.id])
            ),
            modality_files: uploadedFiles.map((item) => ({
              modality: item.modality,
              file_id: item.record.id,
              file_name: item.file.name,
            })),
            processing_metadata: workingDraft.segmentationResult.processing_metadata,
            visualization: workingDraft.segmentationResult.visualization,
          },
        })

        updateWorkflowStep('scan', 'success')
        setPersistenceDraft({
          ...workingDraft,
          uploadedFiles: { ...workingDraft.uploadedFiles },
        })
      }

      activeStep = 'result'
      updateWorkflowStep('result', 'running')
      setWorkflowMessage('Saving volumetric findings, recommendations, and raw output.')

      const savedResult = await medicalService.saveMriSegmentationResult({
        scan_id: workingDraft.scan.id,
        patient_id: workingDraft.patientId,
        case_id: workingDraft.medicalCase.id,
        analyzed_by_model:
          workingDraft.segmentationResult.model_info?.name ||
          'BioIntellect Brain MRI 3D U-Net',
        model_version: workingDraft.segmentationResult.model_info?.version || null,
        analysis_status: 'completed',
        segmentation_mask_path:
          workingDraft.segmentationResult.labels_filename ||
          workingDraft.segmentationResult.visualization?.labels_url ||
          null,
        segmented_regions: workingDraft.segmentationResult.regions || [],
        tumor_detected: workingDraft.segmentationResult.tumor_detected,
        confidence_score:
          workingDraft.segmentationResult.prediction_confidence?.overall || 0,
        detected_abnormalities: buildDetectedAbnormalities(
          workingDraft.segmentationResult.regions
        ),
        measurements: {
          ...(workingDraft.segmentationResult.measurements || {}),
          total_volume_cm3: workingDraft.segmentationResult.total_volume_cm3,
          processing_metadata: workingDraft.segmentationResult.processing_metadata,
        },
        ai_interpretation:
          workingDraft.segmentationResult.ai_interpretation ||
          workingDraft.formattedResult.severity.description,
        ai_recommendations:
          workingDraft.segmentationResult.ai_recommendations?.length > 0
            ? workingDraft.segmentationResult.ai_recommendations
            : [workingDraft.formattedResult.severity.description],
        severity_score: buildSeverityScore(
          workingDraft.formattedResult.severity,
          workingDraft.segmentationResult.total_volume_cm3
        ),
        raw_output: workingDraft.segmentationResult,
      })

      updateWorkflowStep('result', 'success')
      setSavedResultId(savedResult.id)
      setWorkflowMessage('Segmentation and all supporting records were saved successfully.')
      setRecordSyncState({
        status: 'saved',
        message:
          'The segmentation output, uploaded MRI sequences, scan metadata, and structured result were saved to the patient record.',
        technicalDetails: '',
      })
      setPersistenceDraft({
        ...workingDraft,
        savedResult,
        uploadedFiles: { ...workingDraft.uploadedFiles },
      })

      return savedResult
    } catch (syncError) {
      console.error('MRI record sync error:', syncError)
      updateWorkflowStep(activeStep, 'error')
      if (activeStep === 'uploads' && activeUploadModality) {
        setSourceFileStatus((current) => ({
          ...current,
          [activeUploadModality]: 'failed',
        }))
      }
      const message = normalizeErrorMessage(
        syncError,
        'Segmentation completed, but the record sync workflow failed.'
      )
      const technicalDetails = extractErrorDetails(syncError, '')
      setWorkflowMessage(message)
      setRecordSyncState({
        status: 'failed',
        message,
        technicalDetails,
      })
      setPersistenceDraft({
        ...workingDraft,
        uploadedFiles: { ...workingDraft.uploadedFiles },
      })
      return null
    }
  }

  const runAnalysis = async () => {
    if (!allFilesUploaded || !currentUser?.id) return

    setAnalyzing(true)
    setAnalysisError(null)
    setResult(null)
    setSavedResultId(null)
    setPersistenceDraft(null)
    setRecordSyncState({ status: 'idle', message: '', technicalDetails: '' })
    setSourceFileStatus(
      saveToRecord
        ? MODALITIES.reduce((nextState, modality) => {
            nextState[modality] = 'pending'
            return nextState
          }, {})
        : { ...EMPTY_SOURCE_FILE_STATUS }
    )
    setWorkflowStatus(
      saveToRecord
        ? { ...EMPTY_WORKFLOW_STATUS, segment: 'running' }
        : {
            segment: 'running',
            case: 'skipped',
            uploads: 'skipped',
            scan: 'skipped',
            result: 'skipped',
          }
    )

    try {
      const isPatient = userRole === ROLES.PATIENT
      const patientId = isPatient ? currentUser.id : selectedPatientId

      if (!patientId) {
        setAnalysisError('Select a patient before running the MRI workflow.')
        setWorkflowStatus({
          ...EMPTY_WORKFLOW_STATUS,
          segment: 'error',
        })
        setWorkflowMessage('A patient must be selected before analysis can start.')
        return
      }

      setWorkflowMessage(
        'Running the 3D U-Net on the four uploaded MRI sequences and generating the label map.'
      )

      const segmentationResult = await mriSegmentationService.runSegmentation(files, {
        patientId,
      })

      const formattedResult = formatSegmentationResult(segmentationResult)
      const draft = {
        patientId,
        isPatient,
        segmentationResult,
        formattedResult,
        medicalCase: null,
        uploadedFiles: {},
        scan: null,
      }

      setResult(formattedResult)
      setPersistenceDraft(draft)
      updateWorkflowStep('segment', 'success')

      if (saveToRecord) {
        setWorkflowMessage(
          'Segmentation completed. Continuing with patient-record synchronization.'
        )
        await persistSegmentationToRecord(draft)
      } else {
        setWorkflowMessage(
          'Segmentation completed. Auto-save is off, so no patient record was created yet.'
        )
        setRecordSyncState({
          status: 'skipped',
          message:
            'Auto-save is currently off. Review the AI output first, then save it to the patient record when you are satisfied.',
          technicalDetails: '',
        })
      }
    } catch (analysisErr) {
      console.error('MRI Segmentation Error:', analysisErr)
      setAnalysisError(
        normalizeErrorMessage(
          analysisErr,
          'Clinical neuro-imaging analysis failed before a structured result could be generated.'
        )
      )
      setWorkflowStatus((current) => ({
        ...current,
        segment: 'error',
      }))
      setWorkflowMessage('Segmentation failed before a clinical record could be created.')
    } finally {
      setAnalyzing(false)
    }
  }

  const handleSaveResult = async () => {
    if (!persistenceDraft) return

    setAnalyzing(true)
    await persistSegmentationToRecord(persistenceDraft)
    setAnalyzing(false)
  }

  return (
    <div className={styles.pageWrapper}>
      <TopBar
        onBack={onBack}
        userRole={userRole === ROLES.DOCTOR ? 'Neurologist' : 'Patient'}
      />

      <div className={styles.container}>
        <header className={styles.header}>
          <div>
            <h1>Brain MRI Segmentation</h1>
            <p>
              Upload all four sequences, inspect the 3D tumor map, and keep full control
              over whether the analysis is synchronized to the patient record.
            </p>
          </div>

          <div className={styles.headerMeta}>
            {modelInfo && <span className={styles.versionBadge}>Model v{modelInfo.version}</span>}
            <span className={styles.headerPill}>{uploadedCount}/4 sequences ready</span>
            <span className={styles.headerPill}>
              {saveToRecord ? 'Auto-save enabled' : 'Review-only mode'}
            </span>
          </div>
        </header>

        <div className={styles.mainGrid}>
          <section className={styles.controlPanel}>
            <div className={`${styles.card} ${styles.workflowCard}`}>
              <div className={styles.sectionHeader}>
                <div>
                  <h3>Workflow Status</h3>
                  <p>Every stage is tracked separately, so you can tell analysis from record sync.</p>
                </div>
                <span className={styles.progressBadge}>{workflowProgress}% complete</span>
              </div>

              <div className={styles.progressBar}>
                <span style={{ inlineSize: `${workflowProgress}%` }} />
              </div>

              <p className={styles.workflowMessage}>{workflowMessage}</p>

              <div className={styles.workflowList}>
                {WORKFLOW_STEPS.map((step) => (
                  <div
                    key={step.id}
                    className={styles.workflowItem}
                    data-status={workflowStatus[step.id]}
                  >
                    <div className={styles.workflowIndicator} />
                    <div className={styles.workflowCopy}>
                      <div className={styles.workflowTitleRow}>
                        <strong>{step.title}</strong>
                        <span>{WORKFLOW_STATUS_LABELS[workflowStatus[step.id]]}</span>
                      </div>
                      <p>{step.description}</p>
                    </div>
                  </div>
                ))}
              </div>
            </div>

            <div className={styles.card}>
              <div className={styles.sectionHeader}>
                <div>
                  <h3>Context & Controls</h3>
                  <p>Choose the patient, review the model build, and decide if outputs should be stored.</p>
                </div>
              </div>

              {userRole !== 'patient' && (
                <div className={styles.patientSelector}>
                  <SelectField
                    label="Select Patient"
                    value={selectedPatientId}
                    onChange={(event) => setSelectedPatientId(event.target.value)}
                    options={patients.map((patient) => ({
                      value: patient.id,
                      label: `${patient.first_name} ${patient.last_name || ''} (${patient.mrn})`,
                    }))}
                    disabled={!patients.length}
                    error={patientLoadError || undefined}
                    helperText={
                      !patientLoadError
                        ? 'Choose the patient whose MRI study will receive this segmentation run.'
                        : undefined
                    }
                    required
                  />
                </div>
              )}

              <div className={styles.contextGrid}>
                <div className={styles.contextCard}>
                  <span>Patient</span>
                  <strong>
                    {selectedPatient
                      ? `${selectedPatient.first_name || ''} ${selectedPatient.last_name || ''}`.trim() ||
                        selectedPatient.email ||
                        'Selected patient'
                      : 'No patient selected'}
                  </strong>
                  <small>
                    {selectedPatient?.mrn
                      ? `MRN: ${selectedPatient.mrn}`
                      : userRole === ROLES.PATIENT
                        ? 'Your own MRI workflow'
                        : 'Pick a patient to continue'}
                  </small>
                </div>

                <div className={styles.contextCard}>
                  <span>Model Build</span>
                  <strong>{modelInfo?.name || 'BioIntellect Brain MRI 3D U-Net'}</strong>
                  <small>
                    {modelInfo?.release_date
                      ? `Released ${modelInfo.release_date}`
                      : 'Model metadata unavailable'}
                  </small>
                </div>
              </div>

              <label className={styles.toggleRow}>
                <div>
                  <strong>Automatically save to patient record</strong>
                  <p>
                    Turn this off if you want to inspect the segmentation first and save it
                    manually later.
                  </p>
                </div>
                <input
                  type="checkbox"
                  checked={saveToRecord}
                  onChange={(event) => setSaveToRecord(event.target.checked)}
                />
              </label>
            </div>

            <div className={styles.card}>
              <div className={styles.sectionHeader}>
                <div>
                  <h3>Required MRI Sequences</h3>
                  <p>
                    Each upload slot explains what that sequence contributes to the model.
                  </p>
                </div>
                <button
                  type="button"
                  className={styles.inlineAction}
                  onClick={handleClearFiles}
                  disabled={uploadedCount === 0 || analyzing}
                >
                  Clear All
                </button>
              </div>

              <div className={styles.modalityGrid}>
                {MODALITIES.map((modality) => (
                  <div key={modality} className={styles.modalityUpload}>
                    <label
                      htmlFor={`upload-${modality}`}
                      className={`${styles.uploadBox} ${
                        files[modality] ? styles.hasFile : ''
                      }`}
                    >
                      <input
                        type="file"
                        id={`upload-${modality}`}
                        className={styles.hiddenInput}
                        onChange={handleFileUpload(modality)}
                        accept=".nii,.nii.gz"
                      />
                      <div className={styles.modalityHeader}>
                        <span className={styles.modLabel}>
                          {MODALITY_DETAILS[modality].title}
                        </span>
                        <span className={styles.modStatus}>
                          {files[modality] ? 'Ready' : 'Pending'}
                        </span>
                      </div>
                      <p className={styles.modalityDescription}>
                        {MODALITY_DETAILS[modality].description}
                      </p>
                      <span className={styles.modFileName}>
                        {files[modality]?.name || 'Select a NIfTI file'}
                      </span>
                      <span className={styles.modFileMeta}>
                        {files[modality]
                          ? `${formatFileSize(files[modality])} • ${files[modality].name
                              .split('.')
                              .slice(-2)
                              .join('.')}`
                          : 'Accepted formats: .nii or .nii.gz'}
                      </span>
                    </label>
                  </div>
                ))}
              </div>

              <div className={styles.uploadFooter}>
                <span>{uploadedCount}/4 sequences uploaded</span>
                <span>For best results, use sequences from the same study and alignment.</span>
              </div>

              {analysisError && (
                <div className={styles.feedbackBanner} data-tone="error">
                  <strong>Segmentation could not start</strong>
                  <p>{analysisError}</p>
                </div>
              )}

              {result && recordSyncState.status !== 'idle' && (
                <div
                  className={styles.feedbackBanner}
                  data-tone={getFeedbackTone(recordSyncState.status)}
                >
                  <strong>
                    {recordSyncState.status === 'failed'
                      ? 'Segmentation completed, but record sync needs attention'
                      : recordSyncState.status === 'saved'
                        ? 'Patient record synchronized'
                        : 'Review-only mode'}
                  </strong>
                  <p>{recordSyncState.message}</p>
                  {recordSyncState.technicalDetails &&
                    recordSyncState.status === 'failed' && (
                      <details className={styles.technicalDetails}>
                        <summary>Technical details</summary>
                        <pre>{recordSyncState.technicalDetails}</pre>
                      </details>
                    )}
                </div>
              )}

              {result &&
                (saveToRecord ||
                  recordSyncState.status === 'failed' ||
                  recordSyncState.status === 'saved') && (
                  <div className={styles.sourceFilePanel}>
                    <div className={styles.sectionHeader}>
                      <div>
                        <h3>Source File Persistence</h3>
                        <p>Track which MRI sequence has already been stored in the patient record.</p>
                      </div>
                    </div>

                    <div className={styles.sourceFileList}>
                      {MODALITIES.map((modality) => (
                        <div
                          key={modality}
                          className={styles.sourceFileItem}
                          data-status={sourceFileStatus[modality]}
                        >
                          <div>
                            <strong>{MODALITY_DETAILS[modality].title}</strong>
                            <small>
                              {persistenceDraft?.uploadedFiles?.[modality]?.record?.file_name ||
                                files[modality]?.name ||
                                'Waiting for upload'}
                            </small>
                          </div>
                          <span>
                            {SOURCE_FILE_STATUS_LABELS[sourceFileStatus[modality]]}
                          </span>
                        </div>
                      ))}
                    </div>
                  </div>
                )}

              <div className={styles.actionRow}>
                <AnimatedButton
                  variant="primary"
                  isLoading={analyzing}
                  onClick={runAnalysis}
                  disabled={!allFilesUploaded}
                  fullWidth
                >
                  {analyzing ? 'Running Analysis' : 'Run Segmentation'}
                </AnimatedButton>

                {showSyncAction && (
                  <AnimatedButton
                    variant="outline"
                    onClick={handleSaveResult}
                    disabled={analyzing}
                    fullWidth
                  >
                    {syncActionLabel}
                  </AnimatedButton>
                )}
              </div>
            </div>

            {result &&
              (userRole === ROLES.PATIENT ? (
                <MriPatientView result={result} />
              ) : (
                <MriDoctorView result={result} />
              ))}
          </section>

          <section className={styles.visualizationPanel}>
            {result ? (
              <div className={styles.overviewGrid}>
                {overviewCards.map((card) => (
                  <div key={card.label} className={styles.overviewCard}>
                    <span>{card.label}</span>
                    <strong>{card.value}</strong>
                    <small>{card.helper}</small>
                  </div>
                ))}
              </div>
            ) : (
              <div className={styles.emptySummaryCard}>
                <h3>What this workspace does</h3>
                <p>
                  After you upload the four MRI sequences, the system generates a 3D
                  segmentation mask, visualizes it, estimates volumetric burden, and can
                  optionally store the output in the patient record.
                </p>
              </div>
            )}

            <div className={styles.vizCard}>
              <div className={styles.vizHeader}>
                <div>
                  <h3>3D Volumetric Viewer</h3>
                  <p>
                    Rotate the volume, switch modalities, control opacity, and isolate
                    individual tumor classes.
                  </p>
                </div>
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
                <Suspense
                  fallback={
                    <div className={styles.viewerFallback}>
                      <div className={styles.viewerSpinner} />
                      <span>Loading volumetric viewer...</span>
                    </div>
                  }
                >
                  <MriVolumeViewer result={result} isLoading={analyzing} />
                </Suspense>
              </div>
            </div>

            {result && (
              <div className={styles.insightGrid}>
                <motion.div
                  className={styles.insightCard}
                  initial={{ opacity: 0, y: 10 }}
                  animate={{ opacity: 1, y: 0 }}
                >
                  <h4>Region Breakdown</h4>
                  <p className={styles.cardLead}>
                    Volume and class contribution for every detected region.
                  </p>
                  <div className={styles.regionList}>
                    {presentRegions.length > 0 ? (
                      presentRegions.map((region, idx) => (
                        <div key={`${region.class_id ?? idx}-${idx}`} className={styles.regionRow}>
                          <div className={styles.regionRowHeader}>
                            <div className={styles.regionTitle}>
                              <span
                                className={styles.regionDot}
                                style={{
                                  backgroundColor: `rgb(${(region.color || [255, 255, 255]).join(',')})`,
                                }}
                              />
                              <strong>{region.class_name || `Class ${region.class_id}`}</strong>
                            </div>
                            <span>{formatVolume(region.volume_cm3)}</span>
                          </div>
                          <div className={styles.regionBar}>
                            <span
                              style={{
                                inlineSize: `${Math.min(Number(region.percentage || 0), 100)}%`,
                                backgroundColor: `rgb(${(region.color || [255, 255, 255]).join(',')})`,
                              }}
                            />
                          </div>
                          <small>
                            {Number(region.percentage || 0).toFixed(1)}% of segmented volume
                          </small>
                        </div>
                      ))
                    ) : (
                      <div className={styles.emptyListState}>
                        No abnormal segmented regions were reported for this case.
                      </div>
                    )}
                  </div>
                </motion.div>

                <motion.div
                  className={styles.insightCard}
                  initial={{ opacity: 0, y: 10 }}
                  animate={{ opacity: 1, y: 0 }}
                  transition={{ delay: 0.05 }}
                >
                  <h4>Confidence & Measurements</h4>
                  <p className={styles.cardLead}>
                    Model confidence indicators and geometry-derived measurements.
                  </p>

                  <div className={styles.detailStack}>
                    {confidenceBreakdown.map((item) => (
                      <div key={item.label} className={styles.detailItem}>
                        <div>
                          <strong>{item.label}</strong>
                          <small>{item.helper}</small>
                        </div>
                        <span>{item.value}</span>
                      </div>
                    ))}
                  </div>

                  <div className={styles.detailStack}>
                    {measurementItems.map((item) => (
                      <div key={item.label} className={styles.detailItem}>
                        <div>
                          <strong>{item.label}</strong>
                        </div>
                        <span>{item.value}</span>
                      </div>
                    ))}
                  </div>
                </motion.div>

                <motion.div
                  className={styles.insightCard}
                  initial={{ opacity: 0, y: 10 }}
                  animate={{ opacity: 1, y: 0 }}
                  transition={{ delay: 0.1 }}
                >
                  <h4>Interpretation & Next Steps</h4>
                  <p className={styles.cardLead}>
                    Clear narrative summary of what the AI is reporting and what to do next.
                  </p>

                  <div className={styles.calloutBox}>
                    <strong>AI Interpretation</strong>
                    <p>{result.aiInterpretation || result.severity?.description}</p>
                  </div>

                  <div className={styles.recommendationList}>
                    {(result.aiRecommendations || []).length > 0 ? (
                      result.aiRecommendations.map((item, index) => (
                        <div key={`${item}-${index}`} className={styles.recommendationItem}>
                          <span>{index + 1}</span>
                          <p>{item}</p>
                        </div>
                      ))
                    ) : (
                      <div className={styles.emptyListState}>
                        No additional AI recommendations were returned.
                      </div>
                    )}
                  </div>

                  <p className={styles.disclaimerSmall}>{result.disclaimer}</p>
                </motion.div>
              </div>
            )}
          </section>
        </div>
      </div>

    </div>
  )
}

export default MriSegmentation
