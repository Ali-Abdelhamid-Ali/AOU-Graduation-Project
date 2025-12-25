import { supabase } from '../config/supabase'

/**
 * Service for handling all medical data interactions
 * Aligned with 2024 SQL Schema (id as primary key)
 */
export const medicalService = {
    /**
     * Create a new medical case
     */
    async createCase(caseData) {
        const { patientId, doctorId, caseType, priority, chiefComplaint } = caseData

        // Generate case number: CASE-YYYYMMDD-XXXX
        const dateStr = new Date().toISOString().slice(0, 10).replace(/-/g, '')
        const rand = Math.floor(Math.random() * 10000).toString().padStart(4, '0')
        const caseNumber = `CASE-${dateStr}-${rand}`

        const { data, error } = await supabase
            .from('medical_cases')
            .insert({
                case_number: caseNumber,
                patient_id: patientId,
                assigned_doctor_id: doctorId,
                case_type: caseType || 'comprehensive',
                case_status: 'open',
                priority: priority || 'normal',
                chief_complaint: chiefComplaint || '',
                case_date: new Date().toISOString().split('T')[0]
            })
            .select()
            .single()

        if (error) throw error
        return data // contains .id
    },

    /**
     * Calculate SHA-256 checksum of a file
     */
    async calculateChecksum(file) {
        const arrayBuffer = await file.arrayBuffer()
        const hashBuffer = await crypto.subtle.digest('SHA-256', arrayBuffer)
        const hashArray = Array.from(new Uint8Array(hashBuffer))
        const hashHex = hashArray.map(b => b.toString(16).padStart(2, '0')).join('')
        return hashHex
    },

    /**
     * Upload a medical file and record it in medical_files table
     */
    async uploadFile(fileData) {
        const { caseId, patientId, userId, file, fileType } = fileData

        const fileExt = file.name.split('.').pop()
        const fileName = `${Math.random().toString(36).substring(2)}_${Date.now()}.${fileExt}`
        const storagePath = `${patientId}/${caseId}/${fileName}`

        const checksum = await this.calculateChecksum(file)

        const { error: storageError } = await supabase.storage
            .from('medical-files')
            .upload(storagePath, file)

        if (storageError) throw storageError

        const { data: fileRecord, error: fileError } = await supabase
            .from('medical_files')
            .insert({
                case_id: caseId,
                patient_id: patientId,
                uploaded_by: userId,
                file_name: file.name,
                file_type: fileType,
                file_format: fileExt,
                file_size_bytes: file.size,
                storage_bucket: 'medical-files',
                storage_path: storagePath,
                file_checksum: checksum,
                is_processed: false,
                processing_status: 'pending'
            })
            .select()
            .single()

        if (fileError) throw fileError
        return fileRecord // contains .id
    },

    /**
     * Save ECG Signal and Results
     */
    async saveEcgAnalysis(analysisData) {
        const { fileId, caseId, patientId, userId, signalInfo, resultInfo } = analysisData

        const { data: signal, error: signalError } = await supabase
            .from('ecg_signals')
            .insert({
                file_id: fileId,
                case_id: caseId,
                patient_id: patientId,
                lead_configuration: signalInfo.leads || '12-lead',
                sampling_rate: signalInfo.samplingRate || 500,
                signal_duration_seconds: signalInfo.duration || 10,
                number_of_leads: signalInfo.leadCount || 12,
                signal_quality_score: signalInfo.quality || 95.0
            })
            .select()
            .single()

        if (signalError) throw signalError

        const { data: result, error: resultError } = await supabase
            .from('ecg_results')
            .insert({
                signal_id: signal.id,
                case_id: caseId,
                patient_id: patientId,
                analyzed_by: userId,
                primary_diagnosis: resultInfo.classification,
                confidence_score: resultInfo.confidence,
                recommendations: resultInfo.recommendation,
                detected_arrhythmias: { features: resultInfo.features },
                analysis_started_at: new Date(Date.now() - 3000).toISOString(),
                analysis_completed_at: new Date().toISOString(),
                review_status: 'pending'
            })
            .select()
            .single()

        if (resultError) throw resultError
        return { signal, result }
    },

    /**
     * Save MRI Scan and Segmentation Results
     */
    async saveMriAnalysis(analysisData) {
        const { caseId, patientId, userId, scanInfo, resultInfo } = analysisData

        const { data: scan, error: scanError } = await supabase
            .from('mri_scans')
            .insert({
                case_id: caseId,
                patient_id: patientId,
                scan_date: new Date().toISOString().split('T')[0],
                image_quality: scanInfo.quality || 'excellent',
                all_sequences_present: true
            })
            .select()
            .single()

        if (scanError) throw scanError

        const { data: result, error: resultError } = await supabase
            .from('mri_segmentation_results')
            .insert({
                scan_id: scan.id,
                case_id: caseId,
                patient_id: patientId,
                analyzed_by: userId,
                tumor_detected: resultInfo.tumorDetected !== false,
                tumor_type: resultInfo.type,
                whole_tumor_volume: parseFloat(resultInfo.volume) || 0,
                edema_volume: parseFloat(resultInfo.maskDetails?.edema) || 0,
                enhancing_tumor_volume: parseFloat(resultInfo.maskDetails?.enhancing) || 0,
                necrotic_core_volume: parseFloat(resultInfo.maskDetails?.necrosis) || 0,
                tumor_location: { description: resultInfo.location },
                recommendations: resultInfo.recommendation,
                analysis_started_at: new Date(Date.now() - 4000).toISOString(),
                analysis_completed_at: new Date().toISOString(),
                review_status: 'pending'
            })
            .select()
            .single()

        if (resultError) throw resultError
        return { scan, result }
    },

    /**
     * Fetch patient history (cases and results)
     */
    async getPatientHistory(patientId) {
        const { data, error } = await supabase
            .from('medical_cases')
            .select(`
                *,
                ecg_results (*),
                mri_segmentation_results (*)
            `)
            .eq('patient_id', patientId)
            .order('created_at', { ascending: false })

        if (error) throw error
        return data
    },

    /**
     * Start an LLM conversation
     */
    async startConversation(convoData) {
        const { patientId, doctorId, title } = convoData
        const { data, error } = await supabase
            .from('llm_conversations')
            .insert({
                patient_id: patientId,
                doctor_id: doctorId,
                title: title || 'New Medical Inquiry'
            })
            .select()
            .single()

        if (error) throw error
        return data // contains .id
    },

    /**
     * Save an LLM message
     */
    async saveLlmMessage(messageData) {
        const { conversationId, senderId, senderRole, content } = messageData
        const { data, error } = await supabase
            .from('llm_messages')
            .insert({
                conversation_id: conversationId,
                sender_id: senderId === 'ai' ? null : senderId,
                sender_role: senderRole,
                content: content
            })
            .select()
            .single()

        if (error) throw error

        // Update last_message_at in conversation
        await supabase
            .from('llm_conversations')
            .update({ last_message_at: new Date().toISOString() })
            .eq('id', conversationId)

        return data
    },

    /**
     * Fetch conversation messages
     */
    async getMessages(conversationId) {
        const { data, error } = await supabase
            .from('llm_messages')
            .select('*')
            .eq('conversation_id', conversationId)
            .order('sent_at', { ascending: true })

        if (error) throw error
        return data
    }
}
