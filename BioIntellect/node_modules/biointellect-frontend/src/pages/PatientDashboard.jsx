import { useState, useEffect } from 'react'
import { motion } from 'framer-motion'
import { useAuth } from '../context/AuthContext'
import { TopBar } from '../components/TopBar'
import { InputField } from '../components/InputField'
import { SelectField } from '../components/SelectField'
import { AnimatedButton } from '../components/AnimatedButton'
import { supabase } from '../config/supabase'
import styles from './PatientDashboard.module.css'

export const PatientDashboard = ({ onLogout }) => {
    const { currentUser, userRole, signOut } = useAuth()
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
        phone_number: '',
        address: '',
        medical_history: '',
    })

    useEffect(() => {
        if (currentUser) {
            fetchProfile()
        }
    }, [currentUser])

    const fetchProfile = async () => {
        try {
            setLoading(true)

            // We need to fetch from the 'patients' table
            // The Link is via email or we can search by created user_id if we stored it properly in users table too
            // But based on logic, we have email in currentUser

            const { data, error } = await supabase
                .from('patients')
                .select('*')
                .eq('email', currentUser.email)
                .single()

            if (error) throw error

            setProfile(data)
            setFormData({
                first_name: data.first_name || '',
                last_name: data.last_name || '',
                date_of_birth: data.date_of_birth || '',
                gender: data.gender || '',
                phone_number: data.phone_number || '',
                address: data.address || '',
                medical_history: data.medical_history || '',
            })
        } catch (error) {
            console.error('Error loading patient data:', error.message)
            setMessage({ type: 'error', text: 'Failed to load profile data.' })
        } finally {
            setLoading(false)
        }
    }

    const handleUpdate = async (e) => {
        e.preventDefault()
        try {
            setUploading(true)
            const { error } = await supabase
                .from('patients')
                .update({
                    // Allowed fields to update
                    phone_number: formData.phone_number,
                    address: formData.address,
                    // gender/dob usually fixed but allow if needed or restriction logic applied here
                    gender: formData.gender,
                    date_of_birth: formData.date_of_birth,
                    first_name: formData.first_name,
                    last_name: formData.last_name
                })
                .eq('patient_id', profile.patient_id)

            if (error) throw error

            setMessage({ type: 'success', text: 'Profile updated successfully!' })
            setEditMode(false)
            fetchProfile()

            // Clear message after 3 seconds
            setTimeout(() => setMessage({ type: '', text: '' }), 3000)
        } catch (error) {
            setMessage({ type: 'error', text: error.message })
        } finally {
            setUploading(false)
        }
    }

    const handleLogout = async () => {
        await signOut()
        if (onLogout) onLogout()
    }

    if (loading) {
        return (
            <div className={styles.loading}>
                <p>Loading patient profile...</p>
            </div>
        )
    }

    return (
        <div className={styles.pageWrapper}>
            <TopBar userRole={userRole} onLogout={onLogout} />

            <main className={styles.main}>
                <motion.div
                    className={styles.hero}
                    initial={{ opacity: 0, y: -20 }}
                    animate={{ opacity: 1, y: 0 }}
                >
                    <h1 className={styles.title}>Welcome, {profile?.first_name}</h1>
                    <div className={styles.mrnWrapper}>
                        <span className={styles.mrnLabel}>MRN:</span>
                        <span className={styles.mrnValue}>{profile?.medical_record_number}</span>
                    </div>
                </motion.div>

                {message.text && (
                    <motion.div
                        className={message.type === 'success' ? styles.alertSuccess : styles.alertError}
                        initial={{ opacity: 0, scale: 0.95 }}
                        animate={{ opacity: 1, scale: 1 }}
                    >
                        {message.text}
                    </motion.div>
                )}

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
                        <h2 className={styles.cardTitle}>Personal Information</h2>
                        <div className={styles.headerActions}>
                            {!editMode ? (
                                <button className={styles.editButton} onClick={() => setEditMode(true)}>
                                    Edit Profile
                                </button>
                            ) : (
                                <>
                                    <button className={styles.cancelButton} onClick={() => { setEditMode(false); fetchProfile(); }}>
                                        Cancel
                                    </button>
                                </>
                            )}
                        </div>
                    </div>

                    <form onSubmit={handleUpdate} className={styles.form}>
                        <div className={styles.grid}>
                            <InputField
                                id="first_name"
                                label="First Name"
                                value={formData.first_name}
                                onChange={(e) => setFormData({ ...formData, first_name: e.target.value })}
                                disabled={!editMode}
                                required
                                autoComplete="given-name"
                            />
                            <InputField
                                id="last_name"
                                label="Last Name"
                                value={formData.last_name}
                                onChange={(e) => setFormData({ ...formData, last_name: e.target.value })}
                                disabled={!editMode}
                                required
                                autoComplete="family-name"
                            />
                            <InputField
                                id="dob"
                                label="Date of Birth"
                                type="date"
                                value={formData.date_of_birth}
                                onChange={(e) => setFormData({ ...formData, date_of_birth: e.target.value })}
                                disabled={!editMode}
                                required
                                autoComplete="bday"
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
                                autoComplete="sex"
                            />
                            <InputField
                                id="phone"
                                label="Phone Number"
                                value={formData.phone_number}
                                onChange={(e) => setFormData({ ...formData, phone_number: e.target.value })}
                                disabled={!editMode}
                                placeholder="+1 (555) 000-0000"
                                autoComplete="tel"
                            />
                            <InputField
                                id="address"
                                label="Primary Address"
                                value={formData.address}
                                onChange={(e) => setFormData({ ...formData, address: e.target.value })}
                                disabled={!editMode}
                                placeholder="123 Medical Way, Health City"
                                autoComplete="street-address"
                            />
                        </div>

                        <div className={styles.section}>
                            <h3 className={styles.sectionTitle}>Account Details</h3>
                            <div className={styles.infoRow}>
                                <span className={styles.infoLabel}>Email Address</span>
                                <span className={styles.infoValue}>{currentUser?.email}</span>
                            </div>
                            <div className={styles.infoRow}>
                                <span className={styles.infoLabel}>Account Status</span>
                                <span className={styles.infoValue} style={{ color: 'var(--color-success)' }}>Active</span>
                            </div>
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
                                    Save Changes
                                </AnimatedButton>
                            </motion.div>
                        )}
                    </form>
                </motion.div>
            </main>
        </div>
    )
}
