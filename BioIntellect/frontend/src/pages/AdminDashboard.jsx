import { useState } from 'react'
import { motion } from 'framer-motion'
import { useAuth } from '../context/AuthContext'
import { InputField } from '../components/InputField'
import { SelectField } from '../components/SelectField'
import { AnimatedButton } from '../components/AnimatedButton'
import styles from './SignUp.module.css' // Reusing styles

export const AdminDashboard = ({ onLogout }) => {
    const { registerPatient, userRole, signOut } = useAuth()
    const [loading, setLoading] = useState(false)
    const [message, setMessage] = useState({ type: '', text: '' })

    const [formData, setFormData] = useState({
        first_name: '',
        last_name: '',
        email: '',
        password: '',
        date_of_birth: '',
        gender: '',
        phone: '',
        address: '',
    })

    // Only allow access if administrator (though routing should handle this)
    if (userRole !== 'administrator' && userRole !== 'doctor') { // Doctors/Admin logic overlap
        // Strict admin check can be done here or in App.jsx
    }

    const handleInputChange = (field, value) => {
        setFormData(prev => ({ ...prev, [field]: value }))
    }

    const handleRegister = async (e) => {
        e.preventDefault()

        // Basic validation
        if (!formData.email || !formData.password || !formData.first_name || !formData.last_name) {
            setMessage({ type: 'error', text: 'Please fill in all required fields.' })
            return
        }

        setLoading(true)
        setMessage({ type: '', text: '' })

        const result = await registerPatient({
            email: formData.email,
            password: formData.password,
            firstName: formData.first_name,
            lastName: formData.last_name,
            dateOfBirth: formData.date_of_birth,
            gender: formData.gender,
            phone: formData.phone,
            address: formData.address
        })

        if (result.success) {
            setMessage({
                type: 'success',
                text: `Patient registered successfully! MRN: ${result.mrn}`
            })
            // Reset form
            setFormData({
                first_name: '',
                last_name: '',
                email: '',
                password: '',
                date_of_birth: '',
                gender: '',
                phone: '',
                address: '',
            })
        } else {
            setMessage({ type: 'error', text: result.error || 'Registration failed.' })
        }
        setLoading(false)
    }

    const handleLogout = async () => {
        await signOut()
        if (onLogout) onLogout()
    }

    return (
        <div className={styles.pageWrapper}>
            <div style={{ position: 'absolute', top: 0, left: 0, right: 0, padding: '1rem', display: 'flex', justifyContent: 'space-between', zIndex: 10 }}>
                <h2 style={{ color: 'white', margin: 0 }}>BioIntellect Admin Console</h2>
                <button
                    onClick={handleLogout}
                    style={{
                        background: 'rgba(255,255,255,0.1)',
                        border: '1px solid rgba(255,255,255,0.2)',
                        padding: '8px 16px',
                        borderRadius: '8px',
                        color: 'white',
                        cursor: 'pointer'
                    }}
                >
                    Sign Out
                </button>
            </div>

            <div className={styles.container} style={{ marginTop: '60px' }}>
                <motion.div
                    className={styles.card}
                    initial={{ opacity: 0, y: 20 }}
                    animate={{ opacity: 1, y: 0 }}
                    style={{ maxWidth: '800px', width: '100%' }}
                >
                    <div className={styles.header}>
                        <h1 className={styles.title}>Register New Patient</h1>
                        <p className={styles.subtitle}>
                            Create a new patient record and account.
                        </p>
                    </div>

                    {message.text && (
                        <div className={message.type === 'error' ? styles.alertError : styles.alertSuccess} style={{ color: message.type === 'success' ? '#10b981' : '#ef4444', background: message.type === 'success' ? 'rgba(16, 185, 129, 0.1)' : 'rgba(239, 68, 68, 0.1)', padding: '10px', borderRadius: '8px', marginBottom: '1rem', textAlign: 'center' }}>
                            {message.text}
                        </div>
                    )}

                    <form onSubmit={handleRegister} className={styles.form}>
                        <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '1rem' }}>
                            <InputField
                                id="first_name"
                                label="First Name"
                                value={formData.first_name}
                                onChange={(e) => handleInputChange('first_name', e.target.value)}
                                required
                            />
                            <InputField
                                id="last_name"
                                label="Last Name"
                                value={formData.last_name}
                                onChange={(e) => handleInputChange('last_name', e.target.value)}
                                required
                            />
                        </div>

                        <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '1rem' }}>
                            <InputField
                                id="dob"
                                label="Date of Birth"
                                type="date"
                                value={formData.date_of_birth}
                                onChange={(e) => handleInputChange('date_of_birth', e.target.value)}
                                required
                            />
                            <SelectField
                                id="gender"
                                label="Gender"
                                value={formData.gender}
                                onChange={(e) => handleInputChange('gender', e.target.value)}
                                options={[
                                    { value: 'male', label: 'Male' },
                                    { value: 'female', label: 'Female' },
                                ]}
                                required
                            />
                        </div>

                        <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '1rem' }}>
                            <InputField
                                id="email"
                                label="Email Address"
                                type="email"
                                value={formData.email}
                                onChange={(e) => handleInputChange('email', e.target.value)}
                                required
                            />
                            <InputField
                                id="password"
                                label="Initial Password"
                                type="text" // Visible so Admin can share it
                                value={formData.password}
                                onChange={(e) => handleInputChange('password', e.target.value)}
                                required
                                placeholder="e.g. Patient2024!"
                            />
                        </div>

                        <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '1rem' }}>
                            <InputField
                                id="phone"
                                label="Phone Number"
                                value={formData.phone}
                                onChange={(e) => handleInputChange('phone', e.target.value)}
                                placeholder="+1 234..."
                            />
                            <InputField
                                id="address"
                                label="Address"
                                value={formData.address}
                                onChange={(e) => handleInputChange('address', e.target.value)}
                                placeholder="Full Address"
                            />
                        </div>

                        <AnimatedButton
                            type="submit"
                            variant="primary"
                            size="large"
                            fullWidth
                            isLoading={loading}
                            style={{ marginTop: '1rem' }}
                        >
                            Register Patient
                        </AnimatedButton>
                    </form>
                </motion.div>
            </div>
        </div>
    )
}
