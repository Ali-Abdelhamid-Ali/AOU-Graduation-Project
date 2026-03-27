import { clinicalAPI, filesAPI, nlpChatAPI } from './api'

const unwrapData = (response, fallbackMessage) => {
  if (!response?.success) {
    throw new Error(response?.message || fallbackMessage)
  }

  return response.data
}

const hasText = (value) => typeof value === 'string' && value.trim().length > 0

const pickFirstText = (...values) =>
  values.find((value) => hasText(value))?.trim() ?? null

const isDefined = (value) => value !== null && value !== undefined

const normalizeKnownBoolean = (value) => {
  if (value === true || value === false) {
    return value
  }

  if (typeof value === 'string') {
    const normalized = value.trim().toLowerCase()
    if (normalized === 'true') return true
    if (normalized === 'false') return false
  }

  return null
}

const normalizeEcgResult = (item = {}) => ({
  ...item,
  confidence_score:
    item.confidence_score ?? item.rhythm_confidence ?? item.risk_score ?? null,
  primary_diagnosis: pickFirstText(
    item.primary_diagnosis,
    item.rhythm_classification,
    item.ai_interpretation
  ),
  analysis_completed_at: item.analysis_completed_at ?? null,
})

const normalizeMriResult = (item = {}) => ({
  ...item,
  analysis_completed_at: item.analysis_completed_at ?? null,
  tumor_detected: normalizeKnownBoolean(item.tumor_detected),
  tumor_type: pickFirstText(item.tumor_type),
})

export const medicalService = {
  async createCase(caseData) {
    const {
      patientId,
      doctorId,
      hospitalId,
      caseType,
      priority,
      chiefComplaint,
    } = caseData

    if (!patientId) {
      throw new Error('Patient identifier is required to create a case.')
    }

    if (!hospitalId) {
      throw new Error('Hospital identifier is required to create a case.')
    }

    return unwrapData(
      await clinicalAPI.createCase({
        patient_id: patientId,
        hospital_id: hospitalId,
        assigned_doctor_id: doctorId || null,
        created_by_doctor_id: doctorId || null,
        case_type: caseType || 'comprehensive',
        priority: priority || 'normal',
        chief_complaint: chiefComplaint || `${caseType || 'general'} analysis`,
      }),
      'Failed to create case'
    )
  },

  async uploadFile(fileData) {
    const { caseId, patientId, file, fileType, description } = fileData
    const normalizedType =
      fileType === 'ecg_signal' ? 'ecg' : fileType === 'mri_scan' ? 'mri' : fileType

    const formData = new FormData()
    formData.append('file', file)
    formData.append('case_id', caseId)
    formData.append('patient_id', patientId)
    formData.append('file_type', normalizedType)
    if (description) {
      formData.append('description', description)
    }

    const result = await filesAPI.upload(formData)
    if (!result.success) {
      throw new Error(result.message || 'Failed to upload file')
    }

    return result.data
  },

  async saveEcgAnalysis(analysisData) {
    const { fileId, caseId, patientId, signalInfo = {} } = analysisData
    const leads = Array.isArray(signalInfo.leads)
      ? signalInfo.leads.filter(Boolean)
      : hasText(signalInfo.leads)
        ? [signalInfo.leads.trim()]
        : []
    const signalPayload = {
      file_id: fileId,
      patient_id: patientId,
      case_id: caseId,
      signal_data: {
        source: 'frontend_upload',
      },
    }

    if (leads.length > 0) {
      signalPayload.signal_data.lead_layout = leads
      signalPayload.leads_available = leads
    }

    if (isDefined(signalInfo.samplingRate)) {
      signalPayload.sampling_rate = signalInfo.samplingRate
    }

    if (isDefined(signalInfo.duration)) {
      signalPayload.duration_seconds = signalInfo.duration
    }

    if (isDefined(signalInfo.leadCount)) {
      signalPayload.lead_count = signalInfo.leadCount
    } else if (leads.length > 0) {
      signalPayload.lead_count = leads.length
    }

    if (isDefined(signalInfo.quality)) {
      signalPayload.signal_data.quality_score = signalInfo.quality
      signalPayload.quality_score = signalInfo.quality
    }

    const signal = unwrapData(
      await clinicalAPI.createEcgSignal(signalPayload),
      'Failed to create ECG signal'
    )

    const result = unwrapData(
      await clinicalAPI.analyzeEcg(signal.id),
      'Failed to run ECG analysis'
    )

    return { signal, result }
  },

  async saveMriAnalysis(analysisData) {
    const { caseId, patientId, scanInfo = {}, fileId } = analysisData
    const scanPayload = {
      file_id: fileId,
      patient_id: patientId,
      case_id: caseId,
      dicom_metadata: {
        source: 'frontend_upload',
      },
    }

    if (hasText(scanInfo.type)) {
      scanPayload.scan_type = scanInfo.type.trim()
    }

    if (hasText(scanInfo.sequence)) {
      scanPayload.sequence_type = scanInfo.sequence.trim()
      scanPayload.dicom_metadata.uploaded_sequence = scanInfo.sequence.trim()
    }

    if (isDefined(scanInfo.fieldStrength)) {
      scanPayload.field_strength = scanInfo.fieldStrength
    }

    if (hasText(scanInfo.quality)) {
      scanPayload.dicom_metadata.quality = scanInfo.quality.trim()
    }

    const scan = unwrapData(
      await clinicalAPI.createMriScan(scanPayload),
      'Failed to create MRI scan'
    )

    const result = unwrapData(
      await clinicalAPI.analyzeMri(scan.id),
      'Failed to run MRI analysis'
    )

    return { scan, result }
  },

  async createMriScan(scanData) {
    const {
      fileId,
      patientId,
      caseId,
      sequenceType,
      scanType,
      fieldStrength,
      dicomMetadata,
    } = scanData
    const payload = {
      file_id: fileId,
      patient_id: patientId,
      case_id: caseId,
      dicom_metadata: {
        source: 'frontend_upload',
        ...(dicomMetadata || {}),
      },
    }

    if (hasText(scanType)) {
      payload.scan_type = scanType.trim()
    }

    if (hasText(sequenceType)) {
      payload.sequence_type = sequenceType.trim()
    }

    if (isDefined(fieldStrength)) {
      payload.field_strength = fieldStrength
    }

    return unwrapData(
      await clinicalAPI.createMriScan(payload),
      'Failed to create MRI scan'
    )
  },

  async saveMriSegmentationResult(resultData) {
    return unwrapData(
      await clinicalAPI.createMriResult(resultData),
      'Failed to save MRI segmentation result'
    )
  },

  async getPatientHistory(patientId) {
    return unwrapData(
      await clinicalAPI.getHistory(patientId),
      'Failed to get patient history'
    )
  },

  async startConversation(convoData) {
    const { patientId, projectId, title } = convoData
    if (!projectId) {
      throw new Error('projectId is required')
    }

    return unwrapData(
      await nlpChatAPI.createConversation(projectId, {
        patient_id: patientId,
        title: title || 'Medical Consultation',
      }),
      'Failed to start conversation'
    )
  },

  async sendLlmMessage(messageData) {
    const { projectId, conversationId, content, patientId } = messageData
    if (!projectId) {
      throw new Error('projectId is required')
    }

    let latestAssistantMessage = null
    await nlpChatAPI.streamAnswer(
      projectId,
      {
        text: content,
        conversation_id: conversationId,
        patient_id: patientId,
        top_k: 3,
      },
      {
        onDone: (payload) => {
          latestAssistantMessage = payload?.assistant_message || null
        },
        onError: (payload) => {
          throw new Error(payload?.message || 'Failed to send message')
        },
      }
    )

    return latestAssistantMessage
  },

  async getMessages(projectId, conversationId) {
    if (!projectId) {
      throw new Error('projectId is required')
    }

    return unwrapData(
      await nlpChatAPI.getMessages(projectId, conversationId),
      'Failed to get messages'
    )
  },

  async getEcgResults(patientId) {
    const data = unwrapData(
      await clinicalAPI.listEcgResults(patientId),
      'Failed to load ECG results'
    )

    return data.map(normalizeEcgResult)
  },

  async getEcgResultById(resultId) {
    return normalizeEcgResult(
      unwrapData(await clinicalAPI.getEcgResult(resultId), 'Failed to load ECG result')
    )
  },

  async getMriResults(patientId) {
    const data = unwrapData(
      await clinicalAPI.listMriResults(patientId),
      'Failed to load MRI results'
    )

    return data.map(normalizeMriResult)
  },

  async getMriResultById(resultId) {
    return normalizeMriResult(
      unwrapData(await clinicalAPI.getMriResult(resultId), 'Failed to load MRI result')
    )
  },
}

export default medicalService
