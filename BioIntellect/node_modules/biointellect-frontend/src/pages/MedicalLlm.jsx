import { useState, useEffect, useRef } from 'react'
import { motion, AnimatePresence } from 'framer-motion'
import { useAuth } from '../context/AuthContext'
import { medicalService } from '../services/medicalService'
import { TopBar } from '../components/TopBar'
import styles from './MedicalLlm.module.css'

export const MedicalLlm = ({ onBack }) => {
    const { currentUser, userRole } = useAuth()
    const [messages, setMessages] = useState([
        { role: 'assistant', content: 'Welcome to BioIntellect Clinical QA. I am an AI assistant fine-tuned on medical literature to support your diagnostic decision-making. How can I assist you today?' }
    ])
    const [input, setInput] = useState('')
    const [isTyping, setIsTyping] = useState(false)
    const [conversation, setConversation] = useState(null)
    const chatEndRef = useRef(null)

    const scrollToBottom = () => {
        chatEndRef.current?.scrollIntoView({ behavior: 'smooth' })
    }

    useEffect(() => {
        scrollToBottom()
    }, [messages, isTyping])

    useEffect(() => {
        const initConversation = async () => {
            try {
                const isPatient = userRole === 'patient'
                const pId = isPatient ? currentUser.patient_id : null
                const dId = isPatient ? null : (currentUser.user_id || currentUser.id)

                const convo = await medicalService.startConversation({
                    patientId: pId,
                    doctorId: dId,
                    title: 'BioIntellect AI Consultation'
                })
                setConversation(convo)
            } catch (err) {
                console.error('Failed to init LLM conversation:', err)
            }
        }
        initConversation()
    }, [currentUser, userRole])

    const handleSend = async () => {
        if (!input.trim() || !conversation) return

        const userContent = input
        const userMsg = { role: 'user', content: userContent }
        setMessages(prev => [...prev, userMsg])
        setInput('')
        setIsTyping(true)

        try {
            // 1. Save User Message
            await medicalService.saveLlmMessage({
                conversationId: conversation.conversation_id,
                senderId: userRole === 'patient' ? currentUser.patient_id : (currentUser.user_id || currentUser.id),
                senderRole: userRole === 'patient' ? 'patient' : 'doctor',
                content: userContent
            })

            // 2. Simulate Medical LLM Response logic
            await new Promise(resolve => setTimeout(resolve, 2000))

            let response = "I've analyzed your query against current clinical guidelines. Regarding this condition, medical literature suggests that early intervention combined with multimodal diagnostic analysis (ECG/MRI) significantly improves patient outcomes."

            if (userContent.toLowerCase().includes('heart') || userContent.toLowerCase().includes('ecg')) {
                response = "For suspected cardiac arrhythmia, BioIntellect utilizes a CNN-Transformer architecture. Studies show these models achieve >97% accuracy on the MIT-BIH dataset. I recommend reviewing the latest lead II waveform analysis."
            } else if (userContent.toLowerCase().includes('brain') || userContent.toLowerCase().includes('mri')) {
                response = "Brain tumor segmentation in BioIntellect is handled by a 36-layer 3D U-Net. For enhancing core tumors, volumetric quantification is essential. I can analyze the DICOM metadata once a sequence is uploaded."
            }

            // 3. Save AI Message
            await medicalService.saveLlmMessage({
                conversationId: conversation.conversation_id,
                senderId: 'ai',
                senderRole: 'ai',
                content: response
            })

            setMessages(prev => [...prev, { role: 'assistant', content: response }])
        } catch (err) {
            console.error('LLM Message Error:', err)
        } finally {
            setIsTyping(false)
        }
    }

    return (
        <div className={styles.pageWrapper}>
            <TopBar onBack={onBack} userRole="Physician" />

            <div className={styles.container}>
                <aside className={styles.sidebar}>
                    <div className={styles.sidebarHeader}>
                        <h3>Clinical Context</h3>
                        <span className={styles.activeTag}>SECURE MODE</span>
                    </div>
                    <div className={styles.contextList}>
                        <div className={styles.contextItem}>
                            <strong>Knowledge Source</strong>
                            <p>PubMed & ClinicalTrials.gov (2025)</p>
                        </div>
                        <div className={styles.contextItem}>
                            <strong>Model</strong>
                            <p>BioIntellect-Med-LLM-7B</p>
                        </div>
                    </div>
                    <div className={styles.disclaimer}>
                        IMPORTANT: This AI is for decision support only. Final clinical judgment rests with the physician.
                    </div>
                </aside>

                <main className={styles.chatArea}>
                    <div className={styles.chatHeader}>
                        <h2>Interactive Medical Advisor</h2>
                        <span className={styles.onlineStatus}>System Active</span>
                    </div>

                    <div className={styles.messagesContainer}>
                        <AnimatePresence>
                            {messages.map((msg, i) => (
                                <motion.div
                                    key={i}
                                    initial={{ opacity: 0, y: 10 }}
                                    animate={{ opacity: 1, y: 0 }}
                                    className={`${styles.message} ${msg.role === 'assistant' ? styles.assistant : styles.user}`}
                                >
                                    <div className={styles.msgAvatar}>
                                        {msg.role === 'assistant' ? '🤖' : '👨‍⚕️'}
                                    </div>
                                    <div className={styles.msgContent}>
                                        {msg.content}
                                    </div>
                                </motion.div>
                            ))}
                        </AnimatePresence>
                        {isTyping && (
                            <div className={styles.typingIndicator}>
                                <span></span><span></span><span></span>
                            </div>
                        )}
                        <div ref={chatEndRef} />
                    </div>

                    <div className={styles.inputWrapper}>
                        <input
                            type="text"
                            placeholder="Ask about symptoms, diagnostic interpretations, or clinical guidelines..."
                            value={input}
                            onChange={(e) => setInput(e.target.value)}
                            onKeyPress={(e) => e.key === 'Enter' && handleSend()}
                        />
                        <button onClick={handleSend} className={styles.sendBtn}>
                            <svg viewBox="0 0 24 24" width="24" height="24">
                                <path fill="currentColor" d="M2.01 21L23 12 2.01 3 2 10l15 2-15 2z" />
                            </svg>
                        </button>
                    </div>
                </main>
            </div>
        </div>
    )
}
