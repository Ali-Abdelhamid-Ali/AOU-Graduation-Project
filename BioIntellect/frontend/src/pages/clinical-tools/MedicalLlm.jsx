import { useState, useEffect, useMemo, useRef, useCallback } from 'react'
import { motion, AnimatePresence } from 'framer-motion'
import { useAuth } from '@/store/AuthContext'
import { clinicalAPI, nlpChatAPI, patientsAPI } from '@/services/api'
import { getApiErrorMessage } from '@/utils/apiErrorUtils'
import { TopBar } from '@/components/layout/TopBar'
import { SelectField } from '@/components/ui/SelectField'
import { LlmDisclaimer } from '../../components/clinical/LlmDisclaimer'
import { PatientDisclaimer } from '../../components/clinical/PatientDisclaimer'
import { ROLES } from '@/config/roles'
import { toast, ToastContainer } from '@/components/ui/Toast'
import { ConfirmModal } from '@/components/ui/ConfirmModal'
import styles from './MedicalLlm.module.css'

const DEFAULT_MODEL_OPTIONS = [
    { value: 'cohere', label: 'Cohere Clinical' },
    { value: 'phi_qa', label: 'Phi Medical QA' },
    { value: 'medmo', label: 'MedMO Clinical' },
    { value: 'openai', label: 'OpenAI Clinical' },
]

const MODEL_PRIORITY = ['cohere', 'phi_qa', 'medmo', 'openai']

const IMAGE_EXTENSIONS = ['.png', '.jpg', '.jpeg', '.webp', '.dcm', '.nii', '.nii.gz']

const isImageFile = (fileName = '') => {
    const normalized = String(fileName).trim().toLowerCase()
    return IMAGE_EXTENSIONS.some((extension) => normalized.endsWith(extension))
}

const toDisplayMessage = (msg) => ({
    id: msg.id,
    role: msg.sender_type === 'llm' ? 'assistant' : 'user',
    content: msg.message_content,
    timestamp: new Date(msg.created_at),
})

const mergeUniqueById = (base, incoming) => {
    const map = new Map((base || []).map((item) => [item.id, item]))
    ;(incoming || []).forEach((item) => {
        if (item?.id) {
            map.set(item.id, item)
        }
    })
    return Array.from(map.values())
}

export const MedicalLlm = ({ onBack }) => {
    const { currentUser, userRole } = useAuth()

    const [messages, setMessages] = useState([])
    const [inputValue, setInputValue] = useState('')
    const [isLoading, setIsLoading] = useState(false)
    const [conversations, setConversations] = useState([])
    const [currentConversation, setCurrentConversation] = useState(null)
    // Per-conversation isolated project_id for scoped vector storage.
    // Set when a conversation is created or loaded, used for all uploads/queries.
    const [conversationProjectId, setConversationProjectId] = useState(null)

    const [patients, setPatients] = useState([])
    const [selectedPatientId, setSelectedPatientId] = useState(null)
    const [patientSearchTerm, setPatientSearchTerm] = useState('')
    const [patientLoadError, setPatientLoadError] = useState('')

    const [availableContextFiles, setAvailableContextFiles] = useState([])
    const [availableImageFiles, setAvailableImageFiles] = useState([])
    const [selectedContextFileIds, setSelectedContextFileIds] = useState([])
    const [selectedImageFileIds, setSelectedImageFileIds] = useState([])
    // IDs of files the doctor uploaded in this session — always injected into
    // every query regardless of the checkbox selection above.
    const [uploadedDocIds, setUploadedDocIds] = useState([])
    const [uploadedImageIds, setUploadedImageIds] = useState([])

    const [modelOptions, setModelOptions] = useState(DEFAULT_MODEL_OPTIONS)
    const [selectedModelBackend, setSelectedModelBackend] = useState(DEFAULT_MODEL_OPTIONS[0].value)

    const [isUploadingAttachments, setIsUploadingAttachments] = useState(false)
    const [error, setError] = useState(null)
    const [conversationOffset, setConversationOffset] = useState(0)
    const [hasMoreConversations, setHasMoreConversations] = useState(true)
    const [conversationCount, setConversationCount] = useState(0)
    const MAX_CONVERSATIONS = 30
    const [confirmModal, setConfirmModal] = useState({ isOpen: false, title: '', message: '', onConfirm: null })

    const messagesEndRef = useRef(null)
    const composerUploadInputRef = useRef(null)
    const messageCacheRef = useRef(new Map())

    // medmo: inline file content injected silently into the next prompt
    const [medmoInlineContent, setMedmoInlineContent] = useState([])

    const isPatient = userRole === ROLES.PATIENT
    const projectId = currentUser?.hospital_id || ''

    // Extract the per-conversation project_id from a conversation object
    const getConvProjectId = (conv) =>
        conv?.conversation_project_id ||
        conv?.metadata?.conversation_project_id ||
        null

    const filteredPatients = useMemo(() => {
        const query = patientSearchTerm.trim().toLowerCase()
        if (!query) {
            return patients
        }

        return patients.filter((patient) => {
            const firstName = String(patient.first_name || '').toLowerCase()
            const lastName = String(patient.last_name || '').toLowerCase()
            const fullName = `${firstName} ${lastName}`.trim()
            const mrn = String(patient.mrn || '').toLowerCase()
            const id = String(patient.id || '').toLowerCase()
            return fullName.includes(query) || mrn.includes(query) || id.includes(query)
        })
    }, [patients, patientSearchTerm])

    const selectedPatient = useMemo(
        () => patients.find((patient) => patient.id === selectedPatientId) || null,
        [patients, selectedPatientId]
    )

    const selectedConversationPatientContext = useMemo(() => {
        const metadata = currentConversation?.metadata
        if (!metadata || typeof metadata !== 'object') {
            return null
        }
        return metadata.patient_context || null
    }, [currentConversation])

    const selectedModelLabel = useMemo(() => {
        const selected = modelOptions.find((item) => item.value === selectedModelBackend)
        return selected?.label || selectedModelBackend
    }, [modelOptions, selectedModelBackend])

    const selectedContextCount = selectedContextFileIds.length
    const selectedImageCount = selectedImageFileIds.length

    useEffect(() => {
        messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' })
    }, [messages])

    useEffect(() => {
        if (!isPatient) {
            const loadPatients = async () => {
                try {
                    const response = await patientsAPI.list({ is_active: true, limit: 100 })
                    if (response.success) {
                        const loadedPatients = response.data || []
                        setPatients(loadedPatients)
                        setSelectedPatientId(null)
                        setPatientLoadError(
                            loadedPatients.length
                                ? ''
                                : 'No active patient records are available for this doctor account yet.'
                        )
                    }
                } catch (err) {
                    setPatients([])
                    setPatientLoadError(getApiErrorMessage(err, 'Failed to load the patient list.'))
                }
            }
            loadPatients()
        }
    }, [isPatient])

    useEffect(() => {
        const loadModels = async () => {
            try {
                const response = await nlpChatAPI.listModels()
                if (!response.success) {
                    return
                }
                const payload = response.data || {}
                const enabledModels = Array.isArray(payload.models)
                    ? payload.models
                        .filter((item) => item?.enabled)
                        .map((item) => ({
                            value: item.backend,
                            label: item.label || item.backend,
                        }))
                    : []

                if (enabledModels.length > 0) {
                    const orderedEnabledModels = [
                        ...enabledModels,
                    ].sort((a, b) => {
                        const indexA = MODEL_PRIORITY.indexOf(a.value)
                        const indexB = MODEL_PRIORITY.indexOf(b.value)
                        const weightA = indexA === -1 ? MODEL_PRIORITY.length : indexA
                        const weightB = indexB === -1 ? MODEL_PRIORITY.length : indexB
                        return weightA - weightB
                    })

                    setModelOptions(orderedEnabledModels)
                    setSelectedModelBackend((prev) => {
                        if (orderedEnabledModels.some((model) => model.value === prev)) {
                            return prev
                        }

                        const cohereMatch = orderedEnabledModels.find((model) => model.value === 'cohere')
                        if (cohereMatch) {
                            return cohereMatch.value
                        }

                        const phiMatch = orderedEnabledModels.find((model) => model.value === 'phi_qa')
                        if (phiMatch) {
                            return phiMatch.value
                        }

                        const defaultBackend = String(payload.default_backend || '').trim().toLowerCase()
                        const defaultMatch = orderedEnabledModels.find((model) => model.value === defaultBackend)
                        return defaultMatch?.value || orderedEnabledModels[0].value
                    })
                }
            } catch {
                // Keep fallback options if model listing fails.
            }
        }

        if (projectId) {
            loadModels()
        }
    }, [projectId])

    useEffect(() => {
        if (isPatient || !selectedPatientId) {
            setAvailableContextFiles([])
            setAvailableImageFiles([])
            return
        }

        const loadContextSources = async () => {
            try {
                const [ecgResponse, mriResponse] = await Promise.all([
                    clinicalAPI.listEcgResults(selectedPatientId),
                    clinicalAPI.listMriResults(selectedPatientId),
                ])

                if (ecgResponse?.success) {
                    const ecgItems = Array.isArray(ecgResponse.data) ? ecgResponse.data : []
                    setAvailableContextFiles(
                        ecgItems.slice(0, 20).map((item) => ({
                            id: String(item.id),
                            label: `ECG ${item.id?.slice?.(0, 8) || item.id} • ${item.analysis_status || 'unknown'}`,
                        }))
                    )
                } else {
                    setAvailableContextFiles([])
                }

                if (mriResponse?.success) {
                    const mriItems = Array.isArray(mriResponse.data) ? mriResponse.data : []
                    setAvailableImageFiles(
                        mriItems.slice(0, 20).map((item) => ({
                            id: String(item.id),
                            label: `MRI ${item.id?.slice?.(0, 8) || item.id} • ${item.analysis_status || 'unknown'}`,
                        }))
                    )
                } else {
                    setAvailableImageFiles([])
                }
            } catch {
                setAvailableContextFiles([])
                setAvailableImageFiles([])
            }
        }

        loadContextSources()
    }, [isPatient, selectedPatientId])

    const CONVERSATIONS_PAGE_SIZE = 50

    const loadConversationsPage = useCallback(async (offset = 0, append = false) => {
        try {
            const params = { limit: CONVERSATIONS_PAGE_SIZE, offset }
            if (isPatient && currentUser?.id) {
                params.patient_id = currentUser.id
            } else if (currentUser?.id) {
                params.doctor_id = currentUser.id
            }
            const response = await nlpChatAPI.listConversations(projectId, params)
            if (response.success) {
                const rows = Array.isArray(response.data) ? response.data : []
                setConversations((prev) => append ? [...prev, ...rows] : rows)
                setConversationOffset(offset + rows.length)
                setHasMoreConversations(rows.length >= CONVERSATIONS_PAGE_SIZE)
            }
        } catch {
            if (!append) setConversations([])
        }
    }, [isPatient, currentUser?.id, projectId])

    useEffect(() => {
        if (currentUser?.id && projectId) {
            setConversationOffset(0)
            setHasMoreConversations(true)
            loadConversationsPage(0, false)
        }
    }, [currentUser?.id, isPatient, projectId, loadConversationsPage])

    useEffect(() => {
        if (!isPatient && currentUser?.id) {
            const fetchCount = async () => {
                try {
                    const response = await nlpChatAPI.listConversationCount()
                    if (response.success && response.data) {
                        setConversationCount(response.data.count ?? 0)
                    }
                } catch {
                    // silently ignore — count is informational only
                }
            }
            fetchCount()
        }
    }, [isPatient, currentUser?.id])

    const loadMoreConversations = () => {
        if (hasMoreConversations) {
            loadConversationsPage(conversationOffset, true)
        }
    }

    const formatConversationTime = (value) => {
        if (!value) {
            return 'No activity yet'
        }

        return new Date(value).toLocaleString([], {
            dateStyle: 'medium',
            timeStyle: 'short',
        })
    }

    const loadConversation = async (conversation) => {
        setError(null)
        setCurrentConversation(conversation)
        setConversationProjectId(getConvProjectId(conversation))
        // Sync the patient selector to match the conversation's patient so the
        // context injected into subsequent messages is always consistent.
        if (!isPatient && conversation?.patient_id) {
            setSelectedPatientId(conversation.patient_id)
        }

        const cached = messageCacheRef.current.get(conversation.id)
        if (cached) {
            setMessages(cached)
            return
        }

        try {
            const response = await nlpChatAPI.getMessages(projectId, conversation.id)
            if (response.success) {
                const rows = Array.isArray(response.data) ? response.data : []
                const displayMessages = rows.map(toDisplayMessage)
                messageCacheRef.current.set(conversation.id, displayMessages)
                setMessages(displayMessages)
            }
        } catch (err) {
            setError(getApiErrorMessage(err, 'Failed to load conversation messages.'))
        }
    }

    const startNewConversation = async () => {
        setError(null)
        try {
            if (!projectId) {
                setError('Hospital project is not available for this account')
                return
            }

            const patientId = isPatient ? currentUser?.id : selectedPatientId
            if (!patientId) {
                setError('Please select a patient first')
                return
            }

            const response = await nlpChatAPI.createConversation(projectId, {
                conversation_type: isPatient ? 'patient_llm' : 'doctor_llm',
                patient_id: patientId,
                doctor_id: isPatient ? null : currentUser?.id,
                hospital_id: currentUser?.hospital_id,
                title: 'Medical Consultation',
            })

            if (response.success) {
                setCurrentConversation(response.data)
                setConversationProjectId(getConvProjectId(response.data))
                setMessages([])
                setSelectedContextFileIds([])
                setSelectedImageFileIds([])
                setUploadedDocIds([])
                setUploadedImageIds([])
                setConversations((prev) => [response.data, ...prev.filter((item) => item.id !== response.data.id)])
                setConversationCount((prev) => prev + 1)
            }
        } catch (err) {
            setError(getApiErrorMessage(err, 'Failed to start conversation.'))
        }
    }

    const archiveConversation = useCallback(async (conversation) => {
        setConfirmModal({
            isOpen: true,
            title: 'Archive Conversation',
            message: `Archive "${conversation.title || 'Medical Consultation'}"? It will no longer appear in your active list.`,
            onConfirm: async () => {
                setConfirmModal((prev) => ({ ...prev, isOpen: false }))
                try {
                    const response = await nlpChatAPI.archiveConversation(projectId, conversation.id)
                    if (response.success) {
                        setConversations((prev) => prev.filter((c) => c.id !== conversation.id))
                        setConversationCount((prev) => Math.max(0, prev - 1))
                        if (currentConversation?.id === conversation.id) {
                            setCurrentConversation(null)
                            setConversationProjectId(null)
                            setMessages([])
                        }
                        toast.success('Conversation archived.')
                    }
                } catch (err) {
                    toast.error(getApiErrorMessage(err, 'Failed to archive conversation.'))
                }
            },
        })
    }, [projectId, currentConversation])

    const MAX_FILE_SIZE = 50 * 1024 * 1024 // 50 MB

    // Read a file as plain text (best-effort; binary files return empty string)
    const _readFileAsText = (file) =>
        new Promise((resolve) => {
            const reader = new FileReader()
            reader.onload = (e) => resolve(e.target?.result || '')
            reader.onerror = () => resolve('')
            reader.readAsText(file)
        })

    const handleFileInputChange = async (event) => {
        const files = Array.from(event.target.files || [])
        event.target.value = ''

        if (!files.length) return
        if (!projectId) {
            setError('Hospital project is not available for this account')
            return
        }
        const patientId = isPatient ? currentUser?.id : selectedPatientId
        if (!patientId) {
            setError('Please select a patient before uploading attachments')
            return
        }
        const oversized = files.filter((f) => f.size > MAX_FILE_SIZE)
        if (oversized.length > 0) {
            setError(`${oversized.length} file(s) exceed the 50 MB limit: ${oversized.map((f) => f.name).join(', ')}`)
            return
        }

        // ── MedMo: silent direct injection — read files as text, no upload, no UI feedback ──
        if (selectedModelBackend === 'medmo') {
            const chunks = await Promise.all(
                files.map(async (file) => {
                    const text = await _readFileAsText(file)
                    return text ? `[File: ${file.name}]\n${text}` : null
                })
            )
            const valid = chunks.filter(Boolean)
            if (valid.length) {
                setMedmoInlineContent((prev) => [...prev, ...valid])
            }
            return
        }

        // ── All other models: normal RAG upload pipeline ──
        setIsUploadingAttachments(true)
        setError(null)

        try {
            const formData = new FormData()
            files.forEach((file) => formData.append('files', file))
            if (!isPatient && patientId) {
                formData.append('patient_id', String(patientId))
            }
            if (conversationProjectId) {
                formData.append('conversation_project_id', conversationProjectId)
            }

            const response = await nlpChatAPI.uploadAttachments(projectId, formData)
            if (!response.success) {
                toast.error('Upload completed with warnings.')
                return
            }

            const payload = response.data || {}
            // Only treat files as indexed if they appear in documents/images — NOT in rejected.
            // A file in rejected was NOT embedded in the vector DB and must not be sent as a filter.
            const docs = Array.isArray(payload.documents) ? payload.documents : []
            const images = Array.isArray(payload.images) ? payload.images : []
            const rejected = Array.isArray(payload.rejected) ? payload.rejected : []

            if (rejected.length && !docs.length && !images.length) {
                // Everything was rejected — surface the reason to the doctor
                const reasons = rejected.map((r) => `${r.file}: ${r.reason}`).join('\n')
                toast.error(`File upload failed:\n${reasons}`)
                setError(`Upload failed — ${rejected[0]?.reason || 'indexing error'}`)
                return
            }

            setAvailableContextFiles((prev) => mergeUniqueById(prev, docs))
            setAvailableImageFiles((prev) => mergeUniqueById(prev, images))

            if (docs.length) {
                const docIds = docs.map((d) => d.id)
                setSelectedContextFileIds((prev) => [...new Set([...prev, ...docIds])])
                // Track uploaded IDs separately so they are always sent to the
                // backend even if the user unchecks them in the sidebar.
                setUploadedDocIds((prev) => [...new Set([...prev, ...docIds])])
            }
            if (images.length) {
                const imgIds = images.map((img) => img.id)
                setSelectedImageFileIds((prev) => [...new Set([...prev, ...imgIds])])
                setUploadedImageIds((prev) => [...new Set([...prev, ...imgIds])])
            }

            const noticeParts = []
            if (docs.length) noticeParts.push(`${docs.length} document(s) indexed`)
            if (images.length) noticeParts.push(`${images.length} image(s) ready`)
            if (rejected.length) noticeParts.push(`${rejected.length} rejected`)
            toast.success(noticeParts.length ? `Uploaded: ${noticeParts.join(', ')}` : 'Upload completed.')
        } catch (err) {
            const reason = getApiErrorMessage(err, 'Upload failed')
            toast.error(`Upload failed: ${reason}`)
            setError(reason)
        } finally {
            setIsUploadingAttachments(false)
        }
    }

    // Detect language from text content
    const detectLanguage = (text) => {
        if (!text) return 'en'
        const arabicRegex = /[\u0600-\u06FF]/g
        const arabicChars = text.match(arabicRegex) || []
        const arabicRatio = arabicChars.length / text.length
        return arabicRatio > 0.3 ? 'ar' : 'en'
    }

    const sendMessage = async () => {
        if (!inputValue.trim() || isLoading) {
            return
        }
        if (!projectId) {
            setError('Hospital project is not available for this account')
            return
        }

        // Auto-create conversation if none exists; keep local ref for the closure below
        let activeConversation = currentConversation
        if (!activeConversation) {
            const patientId = isPatient ? currentUser?.id : selectedPatientId
            if (!patientId) {
                setError('Please select a patient first')
                return
            }
            try {
                const convResponse = await nlpChatAPI.createConversation(projectId, {
                    conversation_type: isPatient ? 'patient_llm' : 'doctor_llm',
                    patient_id: patientId,
                    doctor_id: isPatient ? null : currentUser?.id,
                    hospital_id: currentUser?.hospital_id,
                    title: 'Medical Consultation',
                })
                if (!convResponse.success) {
                    setError('Failed to start conversation')
                    return
                }
                activeConversation = convResponse.data
                setCurrentConversation(activeConversation)
                setConversationProjectId(getConvProjectId(activeConversation))
                setConversations((prev) => [activeConversation, ...prev.filter((item) => item.id !== activeConversation.id)])
                setConversationCount((prev) => prev + 1)
            } catch (err) {
                setError(getApiErrorMessage(err, 'Failed to start conversation.'))
                return
            }
        }

        const outgoingMessage = inputValue
        const assistantMessageId = `assistant-${Date.now()}`
        const detectedLanguage = detectLanguage(outgoingMessage)

        // MedMo: prepend any silently-injected file content to the prompt sent to the backend.
        // The visible message in the chat stays as the user typed it — only the API payload changes.
        const medmoPrefix =
            selectedModelBackend === 'medmo' && medmoInlineContent.length
                ? medmoInlineContent.join('\n\n') + '\n\n'
                : ''
        const promptForApi = medmoPrefix ? `${medmoPrefix}${outgoingMessage}` : outgoingMessage
        // Clear consumed inline content so it isn't re-sent on the next turn
        if (medmoPrefix) setMedmoInlineContent([])

        const userMessage = {
            id: Date.now(),
            role: 'user',
            content: outgoingMessage,
            timestamp: new Date(),
        }

        const assistantMessage = {
            id: assistantMessageId,
            role: 'assistant',
            content: 'Generating response...',
            timestamp: new Date(),
        }

        const chatHistoryPayload = messages
            .filter((message) => message.content)
            .map((message) => ({
                role: message.role === 'assistant' ? 'assistant' : 'user',
                content: message.content,
            }))

        setMessages((prev) => [...prev, userMessage, assistantMessage])
        setInputValue('')
        setIsLoading(true)
        setError(null)

        try {
            // Always include uploaded file IDs so the retrieval filter finds the
            // doctor's uploaded documents even if they were unchecked in the sidebar.
            const effectiveContextIds = [...new Set([...selectedContextFileIds, ...uploadedDocIds])]
            const effectiveImageIds = [...new Set([...selectedImageFileIds, ...uploadedImageIds])]

            const activeConvProjectId = getConvProjectId(activeConversation) || conversationProjectId || undefined
            const response = await nlpChatAPI.answerQuestion(projectId, {
                text: promptForApi,
                top_k: 3,
                conversation_id: activeConversation.id,
                patient_id: isPatient ? undefined : selectedPatientId,
                language: detectedLanguage,
                chat_history: chatHistoryPayload,
                model_backend: selectedModelBackend,
                context_file_ids: effectiveContextIds,
                image_file_ids: effectiveImageIds,
                conversation_project_id: activeConvProjectId,
            })

            if (response.success && response.data) {
                const { answer, assistant_message, sources } = response.data

                setMessages((prev) => {
                    const updated = prev.map((item) =>
                        item.id === assistantMessageId
                            ? {
                                  ...item,
                                  id: assistant_message?.id || item.id,
                                  content: answer || 'No response received.',
                                  sources: sources || assistant_message?.metadata?.sources || [],
                                  timestamp: new Date(),
                              }
                            : item
                    )
                    if (activeConversation?.id) {
                        messageCacheRef.current.set(activeConversation.id, updated)
                    }
                    return updated
                })
            } else if (response) {
                // Handle case where response doesn't have success wrapper
                // but still contains data (direct response from API)
                const { answer, assistant_message, sources } = response.data || response
                const finalAnswer = answer || 'No response received.'

                if (finalAnswer) {
                    setMessages((prev) => {
                        const updated = prev.map((item) =>
                            item.id === assistantMessageId
                                ? {
                                      ...item,
                                      id: assistant_message?.id || item.id,
                                      content: finalAnswer,
                                      sources: sources || assistant_message?.metadata?.sources || [],
                                      timestamp: new Date(),
                                  }
                                : item
                        )
                        if (activeConversation?.id) {
                            messageCacheRef.current.set(activeConversation.id, updated)
                        }
                        return updated
                    })
                }
            }
        } catch (err) {
            const msg = getApiErrorMessage(err, 'Failed to send message')
            setMessages((prev) =>
                prev.map((item) =>
                    item.id === assistantMessageId
                        ? { ...item, isError: true, errorMessage: msg, content: '', timestamp: new Date() }
                        : item
                )
            )
            setError(msg)
        } finally {
            setIsLoading(false)
        }
    }

    const handleKeyPress = (e) => {
        if (e.key === 'Enter' && !e.shiftKey) {
            e.preventDefault()
            sendMessage()
        }
    }

    return (
        <div className={styles.pageWrapper}>
            <TopBar onBack={onBack} userRole={isPatient ? 'Patient' : 'Physician'} />

            <div className={styles.container}>
                <aside className={styles.sidebar}>
                    <div className={styles.sidebarHeader}>
                        <div>
                            <h3>Clinical Chat Workspace</h3>
                            <p className={styles.sidebarSubtitle}>Select patient, model, and context before sending.</p>
                            {!isPatient && (
                                <p
                                    className={styles.conversationCountBadge}
                                    style={conversationCount >= 25 ? { color: 'var(--color-warning, #f59e0b)' } : undefined}
                                >
                                    {conversationCount} / {MAX_CONVERSATIONS} conversations
                                </p>
                            )}
                        </div>
                        <button onClick={startNewConversation} className={styles.newChatBtn}>
                            + New Chat
                        </button>
                    </div>

                    {!isPatient && (
                        <div className={styles.controlPanel}>
                            <div className={`${styles.contextItem} ${styles.patientSelect}`}>
                                <label className={styles.patientSearchLabel} htmlFor="patient-search-input">
                                    Search Patient (Name / MRN / ID)
                                </label>
                                <input
                                    id="patient-search-input"
                                    className={styles.patientSearchInput}
                                    type="text"
                                    value={patientSearchTerm}
                                    onChange={(event) => setPatientSearchTerm(event.target.value)}
                                    placeholder="e.g. ahmed, MRN-1021, uuid"
                                />
                                <SelectField
                                    label="Select Patient"
                                    value={selectedPatientId ?? ''}
                                    onChange={(e) => {
                                        const newId = e.target.value || null
                                        setSelectedPatientId(newId)
                                        // Clear the active conversation when the patient changes
                                        // so the next message always belongs to the correct patient.
                                        if (newId !== selectedPatientId) {
                                            setCurrentConversation(null)
                                            setConversationProjectId(null)
                                            setMessages([])
                                            setSelectedContextFileIds([])
                                            setSelectedImageFileIds([])
                                            setUploadedDocIds([])
                                            setUploadedImageIds([])
                                        }
                                    }}
                                    options={filteredPatients.map((p) => ({
                                        value: p.id,
                                        label: `${p.first_name} ${p.last_name}${p.mrn ? ` • ${p.mrn}` : ''}`,
                                    }))}
                                    disabled={!filteredPatients.length}
                                    error={patientLoadError || undefined}
                                    helperText={
                                        !patientLoadError
                                            ? 'Choose the patient whose conversation context you want to open.'
                                            : undefined
                                    }
                                />
                                {!patientLoadError && patients.length > 0 && !filteredPatients.length ? (
                                    <p className={styles.patientSearchEmpty}>No patients match this search term.</p>
                                ) : null}
                            </div>

                            <div className={styles.contextItem}>
                                <strong>Model</strong>
                                <SelectField
                                    id="doctor-chat-model"
                                    value={selectedModelBackend}
                                    onChange={(event) => {
                                        const newBackend = event.target.value
                                        setSelectedModelBackend(newBackend)
                                        // Clear MedMo inline buffer when switching away from MedMo
                                        if (newBackend !== 'medmo') setMedmoInlineContent([])
                                        const label = modelOptions.find((m) => m.value === newBackend)?.label || newBackend
                                        toast.info(`Switched to ${label}`)
                                    }}
                                    options={modelOptions}
                                    placeholder="Select model"
                                    helperText="Doctor can switch between available clinical models per conversation."
                                />
                            </div>

                            <div className={`${styles.contextItem} ${styles.contextGroup}`}>
                                <strong>Context Sources (optional)</strong>
                                <div className={styles.contextSourcesList}>
                                    {availableContextFiles.map((file) => (
                                        <label key={file.id} className={styles.contextSourceItem}>
                                            <input
                                                type="checkbox"
                                                checked={selectedContextFileIds.includes(file.id)}
                                                onChange={(event) => {
                                                    if (event.target.checked) {
                                                        setSelectedContextFileIds((prev) => [...new Set([...prev, file.id])])
                                                    } else {
                                                        setSelectedContextFileIds((prev) => prev.filter((id) => id !== file.id))
                                                    }
                                                }}
                                            />
                                            <span>{file.label}</span>
                                        </label>
                                    ))}
                                    {availableContextFiles.length === 0 ? (
                                        <p className={styles.contextSourceEmpty}>No recent ECG records found for context.</p>
                                    ) : null}
                                </div>
                            </div>

                            <div className={`${styles.contextItem} ${styles.contextGroup}`}>
                                <strong>Image Context (optional)</strong>
                                <div className={styles.contextSourcesList}>
                                    {availableImageFiles.map((file) => (
                                        <label key={file.id} className={styles.contextSourceItem}>
                                            <input
                                                type="checkbox"
                                                checked={selectedImageFileIds.includes(file.id)}
                                                onChange={(event) => {
                                                    if (event.target.checked) {
                                                        setSelectedImageFileIds((prev) => [...new Set([...prev, file.id])])
                                                    } else {
                                                        setSelectedImageFileIds((prev) => prev.filter((id) => id !== file.id))
                                                    }
                                                }}
                                            />
                                            <span>{file.label}</span>
                                        </label>
                                    ))}
                                    {availableImageFiles.length === 0 ? (
                                        <p className={styles.contextSourceEmpty}>No recent MRI records found for context.</p>
                                    ) : null}
                                </div>
                            </div>
                        </div>
                    )}

                    <div className={`${styles.contextItem} ${styles.conversationSection}`}>
                        <div className={styles.sectionHeadingRow}>
                            <strong>Recent Conversations</strong>
                            <span className={styles.sectionCount}>{conversations.length}</span>
                        </div>
                        {conversations.length > 0 ? (
                            <div className={styles.conversationList}>
                                {conversations.map((conversation) => (
                                    <div key={conversation.id} className={styles.conversationRow}>
                                        <button
                                            type="button"
                                            className={`${styles.conversationButton} ${currentConversation?.id === conversation.id ? styles.conversationButtonActive : ''}`}
                                            onClick={() => loadConversation(conversation)}
                                        >
                                            <span>{conversation.title || 'Medical Consultation'}</span>
                                            <span className={styles.conversationMeta}>
                                                {formatConversationTime(conversation.updated_at || conversation.created_at)}
                                            </span>
                                        </button>
                                        {!isPatient && (
                                            <button
                                                type="button"
                                                className={styles.archiveBtn}
                                                title="Archive conversation"
                                                onClick={(e) => { e.stopPropagation(); archiveConversation(conversation) }}
                                            >
                                                &#x2713;
                                            </button>
                                        )}
                                    </div>
                                ))}
                                {hasMoreConversations ? (
                                    <button
                                        type="button"
                                        className={styles.loadMoreButton}
                                        onClick={loadMoreConversations}
                                    >
                                        Load older conversations
                                    </button>
                                ) : null}
                            </div>
                        ) : (
                            <p className={styles.emptyConversationState}>
                                Start a new conversation to create a reusable clinical thread.
                            </p>
                        )}
                    </div>
                    <div className={styles.disclaimer}>
                        {userRole === ROLES.PATIENT ? <PatientDisclaimer /> : <LlmDisclaimer />}
                    </div>
                </aside>

                <main className={styles.chatArea}>
                    <div className={styles.chatHeader}>
                        <div>
                            <h2>
                                {currentConversation
                                    ? currentConversation.title || 'Medical Consultation'
                                    : 'BioIntellect Medical AI'}
                            </h2>
                            <p>AI-powered medical assistance with clinical knowledge</p>
                            <div className={styles.chatMetaRow}>
                                <span className={styles.metaChip}>{selectedModelLabel}</span>
                                <span className={styles.metaChip}>{selectedContextCount} docs</span>
                                <span className={styles.metaChip}>{selectedImageCount} images</span>
                                {currentConversation?.id ? <span className={styles.metaChip}>Live conversation</span> : null}
                            </div>
                        </div>
                        {!isPatient && selectedPatient ? (
                            <div className={styles.patientContextCard}>
                                <strong>
                                    {selectedPatient.first_name} {selectedPatient.last_name}
                                </strong>
                                <span>{selectedPatient.mrn || selectedPatient.id}</span>
                                {selectedConversationPatientContext?.medical_history ? (
                                    <span className={styles.patientHistoryMeta}>
                                        Cases: {selectedConversationPatientContext.medical_history.recent_cases?.length || 0} |
                                        ECG: {selectedConversationPatientContext.medical_history.recent_ecg_results?.length || 0} |
                                        MRI: {selectedConversationPatientContext.medical_history.recent_mri_results?.length || 0}
                                    </span>
                                ) : null}
                            </div>
                        ) : null}
                    </div>

                    {error ? <div className={styles.errorBanner}>{error}</div> : null}

                    <div className={styles.messagesContainer}>
                        {messages.length === 0 && !currentConversation ? (
                            <div className={styles.welcomeMessage}>
                                <h3>Welcome to BioIntellect Medical AI</h3>
                                <p>Start a new conversation to get AI-powered medical assistance.</p>
                                <div className={styles.suggestedQuestions}>
                                    <h4>Suggested Topics:</h4>
                                    <button onClick={() => setInputValue('Explain my recent ECG results')}>
                                        Explain my recent ECG results
                                    </button>
                                    <button onClick={() => setInputValue('What do my MRI findings mean?')}>
                                        What do my MRI findings mean?
                                    </button>
                                    <button onClick={() => setInputValue('Tell me about common cardiac conditions')}>
                                        Common cardiac conditions
                                    </button>
                                </div>
                            </div>
                        ) : null}

                        <AnimatePresence>
                            {messages.map((message) => {
                                const isEmptyAssistantPlaceholder =
                                    message.role === 'assistant' &&
                                    !message.isError &&
                                    !String(message.content || '').trim()

                                if (isEmptyAssistantPlaceholder) {
                                    return null
                                }

                                return (
                                    <motion.div
                                        key={message.id}
                                        initial={{ opacity: 0, y: 20 }}
                                        animate={{ opacity: 1, y: 0 }}
                                        exit={{ opacity: 0 }}
                                        className={`${styles.message} ${styles[message.role]}`}
                                    >
                                        <div className={styles.messageAvatar}>{message.role === 'assistant' ? 'AI' : isPatient ? 'ME' : 'DR'}</div>
                                        <div className={styles.messageContent}>
                                            {message.isError ? (
                                                <p className={`${styles.messageText} ${styles.messageError}`}>
                                                    {message.content && <span>{message.content}</span>}
                                                    <span className={styles.errorLabel}>{message.errorMessage || 'An error occurred'}</span>
                                                </p>
                                            ) : (
                                                <p className={styles.messageText}>{message.content}</p>
                                            )}
                                            {message.role === 'assistant' &&
                                                Array.isArray(message.sources) &&
                                                message.sources.length > 0 && (
                                                    <div className={styles.messageSources}>
                                                        <div className={styles.messageSourcesTitle}>
                                                            Sources
                                                        </div>
                                                        <ul className={styles.messageSourcesList}>
                                                            {message.sources.map((src) => (
                                                                <li
                                                                    key={`${message.id}-src-${src.doc_no}`}
                                                                    className={styles.messageSourceItem}
                                                                    title={src.preview || ''}
                                                                >
                                                                    <span className={styles.messageSourceBadge}>
                                                                        {src.doc_no}
                                                                    </span>
                                                                    <span className={styles.messageSourceName}>
                                                                        {src.file_name || 'unknown document'}
                                                                    </span>
                                                                    {src.chunk_index !== undefined &&
                                                                        src.chunk_index !== null && (
                                                                            <span
                                                                                className={styles.messageSourceMeta}
                                                                            >
                                                                                chunk #{src.chunk_index}
                                                                            </span>
                                                                        )}
                                                                    {typeof src.score === 'number' && (
                                                                        <span
                                                                            className={styles.messageSourceMeta}
                                                                        >
                                                                            score {src.score.toFixed(2)}
                                                                        </span>
                                                                    )}
                                                                </li>
                                                            ))}
                                                        </ul>
                                                    </div>
                                                )}
                                            <span className={styles.messageTime}>
                                                {message.timestamp.toLocaleTimeString([], {
                                                    hour: '2-digit',
                                                    minute: '2-digit',
                                                })}
                                            </span>
                                        </div>
                                    </motion.div>
                                )
                            })}
                        </AnimatePresence>

                        <div ref={messagesEndRef} />
                    </div>

                    <div className={styles.inputArea}>
                        <div className={styles.composerArea}>
                            <textarea
                                value={inputValue}
                                onChange={(e) => setInputValue(e.target.value)}
                                onKeyDown={handleKeyPress}
                                placeholder={
                                    !isPatient && !selectedPatientId
                                        ? 'Select a patient to begin chatting...'
                                        : 'Type your medical question...'
                                }
                                disabled={(!isPatient && !selectedPatientId) || isLoading}
                                rows={2}
                            />
                            <div className={styles.composerHintRow}>
                                <span>
                                    Enter to send, Shift+Enter for new line.
                                </span>
                                <span>
                                    Context: {selectedContextCount} docs, {selectedImageCount} images.
                                </span>
                            </div>
                        </div>
                        <button
                            type="button"
                            className={styles.attachButton}
                            onClick={() => composerUploadInputRef.current?.click()}
                            disabled={isUploadingAttachments}
                        >
                            Attach
                        </button>
                        <button
                            onClick={sendMessage}
                            disabled={!inputValue.trim() || isLoading || (!isPatient && !selectedPatientId)}
                            className={styles.sendButton}
                        >
                            Send
                        </button>
                        <input
                            ref={composerUploadInputRef}
                            type="file"
                            multiple
                            onChange={handleFileInputChange}
                            className={styles.hiddenInput}
                        />
                    </div>

                    <div className={styles.safetyNotice}>
                        Safety notice: Model output may contain mistakes and must be validated against patient records and clinical guidelines.
                    </div>
                </main>
            </div>

            <ToastContainer />

            <ConfirmModal
                isOpen={confirmModal.isOpen}
                title={confirmModal.title}
                message={confirmModal.message}
                confirmLabel="Archive"
                variant="danger"
                onConfirm={confirmModal.onConfirm}
                onCancel={() => setConfirmModal((prev) => ({ ...prev, isOpen: false }))}
            />
        </div>
    )
}
