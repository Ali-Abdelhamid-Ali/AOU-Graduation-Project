/**
 * Medical Service - Uses Backend API for all operations
 * Flow: Frontend -> FastAPI Backend -> Supabase
 */

import { clinicalAPI, filesAPI, llmAPI, patientsAPI } from './api';

export const medicalService = {
    /**
     * Create a new medical case
     */
    async createCase(caseData) {
        const { patientId, doctorId, caseType, priority, chiefComplaint } = caseData;

        const result = await clinicalAPI.createCase({
            patient_id: patientId,
            assigned_doctor_id: doctorId,
            case_type: caseType || 'comprehensive',
            priority: priority || 'normal',
            chief_complaint: chiefComplaint || `${caseType || 'general'} analysis`
        });

        if (!result.success) {
            throw new Error(result.message || 'Failed to create case');
        }

        return result.data;
    },

    /**
     * Upload a medical file
     */
    async uploadFile(fileData) {
        const { caseId, patientId, file, fileType, description } = fileData;

        const formData = new FormData();
        formData.append('file', file);
        formData.append('case_id', caseId);
        formData.append('patient_id', patientId);
        formData.append('file_type', fileType);
        if (description) formData.append('description', description);

        const result = await filesAPI.upload(formData);

        if (!result.success) {
            throw new Error(result.message || 'Failed to upload file');
        }

        return result.data;
    },

    /**
     * Save ECG Signal and run analysis
     */
    async saveEcgAnalysis(analysisData) {
        const { fileId, caseId, patientId, signalInfo } = analysisData;

        // Create ECG signal record
        const signalResult = await clinicalAPI.createEcgSignal({
            file_id: fileId,
            patient_id: patientId,
            case_id: caseId,
            sampling_rate: signalInfo.samplingRate || 500,
            duration_seconds: signalInfo.duration || 10,
            lead_count: signalInfo.leadCount || 12,
            leads_available: signalInfo.leads || ['12-lead'],
            quality_score: signalInfo.quality || 95.0
        });

        if (!signalResult.success) {
            throw new Error('Failed to create ECG signal');
        }

        // Run analysis
        const analysisResult = await clinicalAPI.analyzeEcg(signalResult.data.id);

        if (!analysisResult.success) {
            throw new Error('Failed to run ECG analysis');
        }

        return {
            signal: signalResult.data,
            result: analysisResult.data
        };
    },

    /**
     * Save MRI Scan and run segmentation analysis
     */
    async saveMriAnalysis(analysisData) {
        const { caseId, patientId, scanInfo, fileId } = analysisData;

        // Create MRI scan record
        const scanResult = await clinicalAPI.createMriScan({
            file_id: fileId || caseId, // Use case_id as placeholder if no file
            patient_id: patientId,
            case_id: caseId,
            scan_type: scanInfo?.type || 'brain',
            sequence_type: scanInfo?.sequence || 'T1',
            field_strength: 1.5
        });

        if (!scanResult.success) {
            throw new Error('Failed to create MRI scan');
        }

        // Run segmentation analysis
        const analysisResult = await clinicalAPI.analyzeMri(scanResult.data.id);

        if (!analysisResult.success) {
            throw new Error('Failed to run MRI analysis');
        }

        return {
            scan: scanResult.data,
            result: analysisResult.data
        };
    },

    /**
     * Fetch patient history (cases and results)
     */
    async getPatientHistory(patientId) {
        const result = await clinicalAPI.getHistory(patientId);

        if (!result.success) {
            throw new Error('Failed to get patient history');
        }

        return result.data;
    },

    /**
     * Start an LLM conversation
     */
    async startConversation(convoData) {
        const { patientId, doctorId, title } = convoData;

        const result = await llmAPI.createConversation({
            patient_id: patientId,
            doctor_id: doctorId,
            title: title || 'Medical Consultation'
        });

        if (!result.success) {
            throw new Error('Failed to start conversation');
        }

        return result.data;
    },

    /**
     * Send an LLM message and get response
     */
    async sendLlmMessage(messageData) {
        const { conversationId, content } = messageData;

        const result = await llmAPI.sendMessage({
            conversation_id: conversationId,
            message_content: content
        });

        if (!result.success) {
            throw new Error('Failed to send message');
        }

        return result.data;
    },

    /**
     * Fetch conversation messages
     */
    async getMessages(conversationId) {
        const result = await llmAPI.getMessages(conversationId);

        if (!result.success) {
            throw new Error('Failed to get messages');
        }

        return result.data;
    },

    /**
     * Get ECG results for a patient
     */
    async getEcgResults(patientId) {
        const result = await clinicalAPI.listEcgResults(patientId);
        return result.success ? result.data : [];
    },

    /**
     * Get MRI results for a patient
     */
    async getMriResults(patientId) {
        const result = await clinicalAPI.listMriResults(patientId);
        return result.success ? result.data : [];
    },

    /**
     * Review and confirm a clinical result
     */
    async reviewResult(tableName, resultId, data) {
        const result = await clinicalAPI.reviewResult(tableName, resultId, data);
        if (!result.success) {
            throw new Error(result.message || 'Failed to review result');
        }
        return result.data;
    }
};

export default medicalService;
