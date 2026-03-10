import { clinicalAPI, filesAPI, llmAPI } from './api'

const unwrapData = (response, fallbackMessage) => {
  if (!response?.success) {
    throw new Error(response?.message || fallbackMessage)
  }

  return response.data
}

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
    const { fileId, caseId, patientId, signalInfo } = analysisData

    const signal = unwrapData(
      await clinicalAPI.createEcgSignal({
        file_id: fileId,
        patient_id: patientId,
        case_id: caseId,
        signal_data: {
          source: 'frontend_upload',
          lead_layout: signalInfo.leads || ['12-lead'],
          quality_score: signalInfo.quality || 95.0,
        },
        sampling_rate: signalInfo.samplingRate || 500,
        duration_seconds: signalInfo.duration || 10,
        lead_count: signalInfo.leadCount || 12,
        leads_available: Array.isArray(signalInfo.leads)
          ? signalInfo.leads
          : [signalInfo.leads || '12-lead'],
        quality_score: signalInfo.quality || 95.0,
      }),
      'Failed to create ECG signal'
    )

    const result = unwrapData(
      await clinicalAPI.analyzeEcg(signal.id),
      'Failed to run ECG analysis'
    )

    return { signal, result }
  },

  async saveMriAnalysis(analysisData) {
    const { caseId, patientId, scanInfo, fileId } = analysisData

    const scan = unwrapData(
      await clinicalAPI.createMriScan({
        file_id: fileId,
        patient_id: patientId,
        case_id: caseId,
        scan_type: scanInfo?.type || 'brain',
        sequence_type: scanInfo?.sequence || 'multi-modal',
        field_strength: 1.5,
        dicom_metadata: {
          source: 'frontend_upload',
          quality: scanInfo?.quality || 'good',
          uploaded_sequence: scanInfo?.sequence || 'multi-modal',
        },
      }),
      'Failed to create MRI scan'
    )

    const result = unwrapData(
      await clinicalAPI.analyzeMri(scan.id),
      'Failed to run MRI analysis'
    )

    return { scan, result }
  },

  async createMriScan(scanData) {
    const { fileId, patientId, caseId, sequenceType, dicomMetadata } = scanData

    return unwrapData(
      await clinicalAPI.createMriScan({
        file_id: fileId,
        patient_id: patientId,
        case_id: caseId,
        scan_type: 'brain',
        sequence_type: sequenceType || 'multi-modal',
        field_strength: 1.5,
        dicom_metadata: {
          source: 'frontend_upload',
          ...(dicomMetadata || {}),
        },
      }),
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
    const { patientId, doctorId, title } = convoData
    return unwrapData(
      await llmAPI.createConversation({
        patient_id: patientId,
        doctor_id: doctorId,
        title: title || 'Medical Consultation',
      }),
      'Failed to start conversation'
    )
  },

  async sendLlmMessage(messageData) {
    const { conversationId, content } = messageData
    const result = await llmAPI.sendMessage({
      conversation_id: conversationId,
      message_content: content,
    })

    if (!result.success) {
      throw new Error(result.message || 'Failed to send message')
    }

    return result.llm_response
  },

  async getMessages(conversationId) {
    return unwrapData(
      await llmAPI.getMessages(conversationId),
      'Failed to get messages'
    )
  },

  async getEcgResults(patientId) {
    const data = unwrapData(
      await clinicalAPI.listEcgResults(patientId),
      'Failed to load ECG results'
    )

    return data.map((item) => ({
      ...item,
      confidence_score:
        item.confidence_score ?? item.rhythm_confidence ?? item.risk_score ?? 0,
      primary_diagnosis:
        item.primary_diagnosis ??
        item.rhythm_classification ??
        item.ai_interpretation ??
        'ECG analysis completed.',
      analysis_completed_at: item.analysis_completed_at ?? item.created_at,
    }))
  },

  async getMriResults(patientId) {
    const data = unwrapData(
      await clinicalAPI.listMriResults(patientId),
      'Failed to load MRI results'
    )

    return data.map((item) => ({
      ...item,
      analysis_completed_at: item.analysis_completed_at ?? item.created_at,
      tumor_detected:
        item.tumor_detected ??
        Boolean(item.detected_abnormalities?.length || item.severity_score > 40),
      tumor_type:
        item.tumor_type ??
        item.detected_abnormalities?.[0]?.name ??
        item.ai_interpretation,
    }))
  },

  async reviewResult(tableName, resultId, data) {
    return unwrapData(
      await clinicalAPI.reviewResult(tableName, resultId, data),
      'Failed to review result'
    )
  },
}

export default medicalService
