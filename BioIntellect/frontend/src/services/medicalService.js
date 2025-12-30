/**
 * Medical Service - Uses Backend API for all operations
 * Flow: Frontend -> FastAPI Backend -> Supabase
 */

import { casesAPI, filesAPI, ecgAPI, mriAPI, llmAPI, patientsAPI } from './api';

export const medicalService = {
    /**
     * Create a new medical case
     */
    async createCase(caseData) {
        const { patientId, doctorId, caseType, priority, chiefComplaint } = caseData;

        const result = await casesAPI.create({
            patient_id: patientId,
            assigned_doctor_id: doctorId,
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
        const { caseId, patientId, userId, file, fileType, description } = fileData;

        const result = await filesAPI.upload(
            file,
            caseId,
            patientId,
            fileType,
            description
        );

        if (!result.success) {
            throw new Error(result.message || 'Failed to upload file');
        }

        return result.data;
    },

    /**
     * Save ECG Signal and run analysis
     */
    async saveEcgAnalysis(analysisData) {
        const { fileId, caseId, patientId, signalInfo, resultInfo } = analysisData;

        // Create ECG signal record
        const signalResult = await ecgAPI.createSignal({
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
        const analysisResult = await ecgAPI.analyze({
            signal_id: signalResult.data.id,
            patient_id: patientId,
            case_id: caseId
        });

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
        const { caseId, patientId, scanInfo, resultInfo, fileId } = analysisData;

        // Create MRI scan record
        const scanResult = await mriAPI.createScan({
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
        const analysisResult = await mriAPI.analyze({
            scan_id: scanResult.data.id,
            patient_id: patientId,
            case_id: caseId
        });

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
        const result = await patientsAPI.getHistory(patientId);

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
            conversation_type: doctorId ? 'doctor_llm' : 'patient_llm',
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
            message_content: content,
            message_type: 'text'
        });

        if (!result.success) {
            throw new Error('Failed to send message');
        }

        return {
            userMessage: result.user_message,
            llmResponse: result.llm_response
        };
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
        const result = await ecgAPI.listResults({ patient_id: patientId });
        return result.success ? result.data : [];
    },

    /**
     * Get MRI results for a patient
     */
    async getMriResults(patientId) {
        const result = await mriAPI.listResults({ patient_id: patientId });
        return result.success ? result.data : [];
    }
};

export default medicalService;
