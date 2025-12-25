import { useState, useEffect } from 'react'
import { motion } from 'framer-motion'
import { useAuth } from '../context/AuthContext'
import { TopBar } from '../components/TopBar'
import { InputField } from '../components/InputField'
import { SelectField } from '../components/SelectField'
import { AnimatedButton } from '../components/AnimatedButton'
import { supabase } from '../config/supabase'
import styles from './PatientDashboard.module.css'

// Professional Icon Imports
import cardioIcon from '../images/icons/cardio.png'
import neuroIcon from '../images/icons/neuro.png'
import insightsIcon from '../images/icons/insights.png'

export const PatientDashboard = ({
    onLogout,
    onEcgAnalysis,
    onMriSegmentation,
    onMedicalLlm
}) => {
    const { currentUser, userRole } = useAuth()
    const [loading, setLoading] = useState(true)
    const [uploading, setUploading] = useState(false)
    const [profile, setProfile] = useState(null)
    const [editMode, setEditMode] = useState(false)
    const [message, setMessage] = useState({ type: '', text: '' })

    const [formData, setFormData] = useState({
        first_name: '',
        last_name: '',
        date_of_birth: '',
        gender: '',
        phone: '',
        address: '',
        medical_history: '',
    })

    const modules = [
        {
            id: 'ecg',
            title: 'ECG Analysis',
            description: 'Monitor your cardiac health with AI-powered arrhythmia detection.',
            icon: cardioIcon,
            action: onEcgAnalysis,
            color: '#ef4444'
        },
        {
            id: 'mri',
            title: 'Brain Imaging',
            description: 'View 3D volumetric segmentation of neural MRI scans.',
            icon: neuroIcon,
            action: onMriSegmentation,
            color: '#3b82f6'
        },
        {
            id: 'llm',
            title: 'Medical Advisor',
            description: 'Consult with the BioIntellect AI for health-related queries.',
            icon: insightsIcon,
            action: onMedicalLlm,
            color: '#6366f1'
        }
    ]

    const fetchProfile = async () => {
        try {
            setLoading(true)
            // Use user_id for authoritative lookup linked to auth.users
            const { data, error } = await supabase
                .from('patients')
                .select('*, hospitals(hospital_name_en)')
                .eq('user_id', currentUser.user_id || currentUser.id)
                .maybeSingle()

            if (error) throw error
            if (!data) throw new Error('Clinical profile not found.')

            setProfile(data)
            setFormData({
                first_name: data.first_name || '',
                last_name: data.last_name || '',
                date_of_birth: data.date_of_birth || '',
                gender: data.gender || '',
                phone: data.phone || '',
                address: data.address || '',
                medical_history: data.medical_history || '',
            })
        } catch (error) {
            console.error('Error loading patient data:', error.message)
            setMessage({ type: 'error', text: 'Failed to synchronize clinical profile.' })
        } finally {
            setLoading(false)
        }
    }

    useEffect(() => {
        if (currentUser) {
            fetchProfile()
        }
    }, [currentUser])

    const handleUpdate = async (e) => {
        e.preventDefault()
        try {
            setUploading(true)
            const { error } = await supabase
                .from('patients')
                .update({
                    phone: formData.phone,
                    address: formData.address,
                    gender: formData.gender,
                    date_of_birth: formData.date_of_birth,
                    first_name: formData.first_name,
                    last_name: formData.last_name
                })
                .eq('id', profile.id)

            if (error) throw error

            setMessage({ type: 'success', text: 'Clinical record updated successfully!' })
            setEditMode(false)
            fetchProfile()

            setTimeout(() => setMessage({ type: '', text: '' }), 3000)
        } catch (error) {
            setMessage({ type: 'error', text: error.message })
        } finally {
            setUploading(false)
        }
    }

    if (loading) {
        return (
            <div className={styles.loading}>
                <div className={styles.spinner} />
                <p>Establishing Secure Clinical Session...</p>
            </div>
        )
    }

    return (
        <div className={styles.pageWrapper}>
            <TopBar userRole={userRole} onLogout={onLogout} />

            <main className={styles.main}>
                {message.text && (
                    <div style={{
                        padding: '1rem',
                        margin: '1rem auto',
                        maxWidth: '1200px',
                        borderRadius: '8px',
                        backgroundColor: message.type === 'error' ? '#fee2e2' : '#dcfce7',
                        color: message.type === 'error' ? '#ef4444' : '#16a34a',
                        border: `1px solid ${message.type === 'error' ? '#fca5a5' : '#86efac'}`
                    }}>
                        {message.text}
                    </div>
                )}
                <motion.div
                    className={styles.hero}
                    initial={{ opacity: 0, y: -20 }}
                    animate={{ opacity: 1, y: 0 }}
                >
                    <div className={styles.heroBadge}>PATIENT PORTAL</div>
                    <h1 className={styles.title}>Welcome, {profile?.first_name}</h1>
                    <div className={styles.mrnWrapper}>
                        <span className={styles.mrnLabel}>Medical Record Number:</span>
                        <span className={styles.mrnValue}>{profile?.medical_record_number}</span>
                    </div>
                </motion.div>

                {/* Clinical Modules Section */}
                <section className={styles.modulesSection}>
                    <h2 className={styles.sectionTitle}>Available Medical Modules</h2>
                    <div className={styles.moduleGrid}>
                        {modules.map((module) => (
                            <motion.div
                                key={module.id}
                                className={styles.moduleCard}
                                whileHover={{ y: -5, boxShadow: 'var(--shadow-xl)' }}
                                whileTap={{ scale: 0.98 }}
                                onClick={module.action}
                            >
                                <div className={styles.moduleIconBox} style={{ backgroundColor: `${module.color}15` }}>
                                    <img src={module.icon} alt={module.title} className={styles.moduleIconImg} />
                                </div>
                                <div className={styles.moduleInfo}>
                                    <h3 className={styles.moduleTitle}>{module.title}</h3>
                                    <p className={styles.moduleDesc}>{module.description}</p>
                                </div>
                                <div className={styles.moduleAction} style={{ color: module.color }}>
                                    Launch Module &rarr;
                                </div>
                            </motion.div>
                        ))}
                    </div>
                </section>

                <div className={styles.divider} />

                <motion.div
                    className={styles.card}
                    initial="hidden"
                    animate="visible"
                    variants={{
                        hidden: { opacity: 0, y: 30 },
                        visible: {
                            opacity: 1,
                            y: 0,
                            transition: {
                                duration: 0.6,
                                ease: [0.22, 1, 0.36, 1],
                                staggerChildren: 0.1
                            }
                        }
                    }}
                >
                    <div className={styles.cardHeader}>
                        <h2 className={styles.cardTitle}>Personal Health Identity</h2>
                        <div className={styles.headerActions}>
                            {!editMode ? (
                                <button className={styles.editButton} onClick={() => setEditMode(true)}>
                                    Edit Information
                                </button>
                            ) : (
                                <button className={styles.cancelButton} onClick={() => { setEditMode(false); fetchProfile(); }}>
                                    Cancel Changes
                                </button>
                            )}
                        </div>
                    </div>

                    <form onSubmit={handleUpdate} className={styles.form}>
                        {/* Form contents remain the same as before */}
                        <div className={styles.grid}>
                            <InputField
                                id="first_name"
                                label="First Name"
                                value={formData.first_name}
                                onChange={(e) => setFormData({ ...formData, first_name: e.target.value })}
                                disabled={!editMode}
                                required
                            />
                            <InputField
                                id="last_name"
                                label="Last Name"
                                value={formData.last_name}
                                onChange={(e) => setFormData({ ...formData, last_name: e.target.value })}
                                disabled={!editMode}
                                required
                            />
                            <InputField
                                id="dob"
                                label="Date of Birth"
                                type="date"
                                value={formData.date_of_birth}
                                onChange={(e) => setFormData({ ...formData, date_of_birth: e.target.value })}
                                disabled={!editMode}
                                required
                            />
                            <SelectField
                                id="gender"
                                label="Gender"
                                value={formData.gender}
                                onChange={(e) => setFormData({ ...formData, gender: e.target.value })}
                                options={[
                                    { value: 'male', label: 'Male' },
                                    { value: 'female', label: 'Female' },
                                ]}
                                disabled={!editMode}
                                required
                            />
                            <InputField
                                id="phone"
                                label="Phone Number"
                                value={formData.phone}
                                onChange={(e) => setFormData({ ...formData, phone: e.target.value })}
                                disabled={!editMode}
                            />
                            <InputField
                                id="address"
                                label="Primary Address"
                                value={formData.address}
                                onChange={(e) => setFormData({ ...formData, address: e.target.value })}
                                disabled={!editMode}
                            />
                        </div>

                        {editMode && (
                            <motion.div
                                style={{ marginTop: 'var(--spacing-xl)' }}
                                initial={{ opacity: 0, y: 10 }}
                                animate={{ opacity: 1, y: 0 }}
                            >
                                <AnimatedButton
                                    type="submit"
                                    variant="primary"
                                    size="large"
                                    fullWidth
                                    isLoading={uploading}
                                >
                                    Confirm Update
                                </AnimatedButton>
                            </motion.div>
                        )}
                    </form>
                </motion.div>
            </main>
        </div>
    )
}

