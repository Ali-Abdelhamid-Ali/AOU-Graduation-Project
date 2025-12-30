import { useState, useEffect, useRef } from 'react'
import { motion, AnimatePresence } from 'framer-motion'
import { useAuth } from '../context/AuthContext'
import { llmAPI, patientsAPI } from '../services/api'
import { TopBar } from '../components/TopBar'
import { SelectField } from '../components/SelectField'
import styles from './MedicalLlm.module.css'

export const MedicalLlm = ({ onBack }) => {
    const { currentUser, userRole } = useAuth()
    const [messages, setMessages] = useState([])
    const [inputValue, setInputValue] = useState('')
    const [isLoading, setIsLoading] = useState(false)
    const [conversations, setConversations] = useState([])
    const [currentConversation, setCurrentConversation] = useState(null)
    const [patients, setPatients] = useState([])
    const [selectedPatientId, setSelectedPatientId] = useState('')
    const [error, setError] = useState(null)
    const messagesEndRef = useRef(null)
    const isPatient = userRole === 'patient'

    // Load patients for doctors
    useEffect(() => {
        if (!isPatient) {
            const loadPatients = async () => {
                try {
                    const response = await patientsAPI.list({ is_active: true, limit: 100 })
                    if (response.success) {
                        setPatients(response.data)
                        if (response.data.length > 0) {
                            setSelectedPatientId(response.data[0].id)
                        }
                    }
                } catch (err) {
                    console.error('Failed to load patients:', err)
                }
            }
            loadPatients()
        }
    }, [isPatient])

    // Load conversations
    useEffect(() => {
        const loadConversations = async () => {
            try {
                const params = {}
                if (isPatient && currentUser?.id) {
                    params.patient_id = currentUser.id
                } else if (currentUser?.id) {
                    params.doctor_id = currentUser.id
                }
                const response = await llmAPI.listConversations(params)
                if (response.success) {
                    setConversations(response.data)
                }
            } catch (err) {
                console.error('Failed to load conversations:', err)
            }
        }
        if (currentUser?.id) {
            loadConversations()
        }
    }, [currentUser, isPatient])

    // Auto-scroll to bottom
    useEffect(() => {
        messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' })
    }, [messages])

    const startNewConversation = async () => {
        setError(null)
        try {
            const patientId = isPatient ? currentUser.id : selectedPatientId
            if (!patientId) {
                setError('Please select a patient first')
                return
            }

            const response = await llmAPI.createConversation({
                conversation_type: isPatient ? 'patient_llm' : 'doctor_llm',
                patient_id: patientId,
                doctor_id: isPatient ? null : currentUser.id,
                title: 'Medical Consultation'
            })

            if (response.success) {
                setCurrentConversation(response.data)
                setMessages([])
                setConversations(prev => [response.data, ...prev])
            }
        } catch (err) {
            setError(err.message || 'Failed to start conversation')
        }
    }

    const loadConversation = async (conversation) => {
        setCurrentConversation(conversation)
        try {
            const response = await llmAPI.getMessages(conversation.id)
            if (response.success) {
                setMessages(response.data.map(msg => ({
                    id: msg.id,
                    role: msg.sender_type === 'llm' ? 'assistant' : 'user',
                    content: msg.message_content,
                    timestamp: new Date(msg.created_at)
                })))
            }
        } catch (err) {
            console.error('Failed to load messages:', err)
        }
    }

    const sendMessage = async () => {
        if (!inputValue.trim() || isLoading) return
        if (!currentConversation) {
            setError('Please start a new conversation first')
            return
        }

        const userMessage = {
            id: Date.now(),
            role: 'user',
            content: inputValue,
            timestamp: new Date()
        }

        setMessages(prev => [...prev, userMessage])
        setInputValue('')
        setIsLoading(true)
        setError(null)

        try {
            const response = await llmAPI.sendMessage({
                conversation_id: currentConversation.id,
                message_content: inputValue,
                message_type: 'text'
            })

            if (response.success && response.llm_response) {
                const aiMessage = {
                    id: response.llm_response.id,
                    role: 'assistant',
                    content: response.llm_response.message_content,
                    timestamp: new Date(response.llm_response.created_at)
                }
                setMessages(prev => [...prev, aiMessage])
            }
        } catch (err) {
            setError(err.message || 'Failed to send message')
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
                        <h3>Conversations</h3>
                        <button onClick={startNewConversation} className={styles.newChatBtn}>
                            + New Chat
                        </button>
                    </div>

                    {!isPatient && (
                        <div className={styles.patientSelect}>
                            <SelectField
                                label="Select Patient"
                                value={selectedPatientId}
                                onChange={(e) => setSelectedPatientId(e.target.value)}
                                options={patients.map(p => ({
                                    value: p.id,
                                    label: `${p.first_name} ${p.last_name}`
                                }))}
                            />
                        </div>
                    )}

                    <div className={styles.conversationList}>
                        {conversations.map(conv => (
                            <div
                                key={conv.id}
                                className={`${styles.conversationItem} ${currentConversation?.id === conv.id ? styles.active : ''}`}
                                onClick={() => loadConversation(conv)}
                            >
                                <span className={styles.convTitle}>{conv.title || 'Medical Consultation'}</span>
                                <span className={styles.convDate}>
                                    {new Date(conv.created_at).toLocaleDateString()}
                                </span>
                            </div>
                        ))}
                    </div>
                </aside>

                <main className={styles.chatArea}>
                    <div className={styles.chatHeader}>
                        <h2>
                            {currentConversation 
                                ? (currentConversation.title || 'Medical Consultation')
                                : 'BioIntellect Medical AI'
                            }
                        </h2>
                        <p>AI-powered medical assistance with clinical knowledge</p>
                    </div>

                    {error && (
                        <div className={styles.errorBanner}>{error}</div>
                    )}

                    <div className={styles.messagesContainer}>
                        {messages.length === 0 && !currentConversation && (
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
                        )}

                        <AnimatePresence>
                            {messages.map((message) => (
                                <motion.div
                                    key={message.id}
                                    initial={{ opacity: 0, y: 20 }}
                                    animate={{ opacity: 1, y: 0 }}
                                    exit={{ opacity: 0 }}
                                    className={`${styles.message} ${styles[message.role]}`}
                                >
                                    <div className={styles.messageAvatar}>
                                        {message.role === 'assistant' ? '🤖' : '👤'}
                                    </div>
                                    <div className={styles.messageContent}>
                                        <p>{message.content}</p>
                                        <span className={styles.messageTime}>
                                            {message.timestamp.toLocaleTimeString()}
                                        </span>
                                    </div>
                                </motion.div>
                            ))}
                        </AnimatePresence>

                        {isLoading && (
                            <div className={`${styles.message} ${styles.assistant}`}>
                                <div className={styles.messageAvatar}>🤖</div>
                                <div className={styles.messageContent}>
                                    <div className={styles.typingIndicator}>
                                        <span></span><span></span><span></span>
                                    </div>
                                </div>
                            </div>
                        )}

                        <div ref={messagesEndRef} />
                    </div>

                    <div className={styles.inputArea}>
                        <textarea
                            value={inputValue}
                            onChange={(e) => setInputValue(e.target.value)}
                            onKeyPress={handleKeyPress}
                            placeholder={currentConversation 
                                ? "Type your medical question..." 
                                : "Start a new conversation to begin chatting..."}
                            disabled={!currentConversation || isLoading}
                            rows={1}
                        />
                        <button
                            onClick={sendMessage}
                            disabled={!inputValue.trim() || isLoading || !currentConversation}
                            className={styles.sendButton}
                        >
                            Send
                        </button>
                    </div>

                    <div className={styles.disclaimer}>
                        <p>
                            ⚠️ This AI assistant provides general medical information only. 
                            It does not replace professional medical advice, diagnosis, or treatment.
                        </p>
                    </div>
                </main>
            </div>
        </div>
    )
}
