import { useState } from 'react'
import { motion } from 'framer-motion'
import { useAuth } from '../context/AuthContext'
import { TopBar } from '../components/TopBar'
import { InputField } from '../components/InputField'
import { SelectField } from '../components/SelectField'
import { AnimatedButton } from '../components/AnimatedButton'
import { specialtyOptions } from '../constants/options'
import styles from './CreateDoctor.module.css'

export const CreateDoctor = ({ onBack, onComplete, userRole }) => {
    const { registerDoctor, isLoading, error, clearError } = useAuth()

    const [formData, setFormData] = useState({
        fullName: '',
        email: '',
        password: '',
        confirmPassword: '',
        specialty: 'physician',
        phone: '',
        licenseNumber: ''
    })

    const [validationErrors, setValidationErrors] = useState({})
    const [success, setSuccess] = useState(false)

    const handleInputChange = (field, value) => {
        setFormData(prev => ({ ...prev, [field]: value }))
        if (validationErrors[field]) {
            setValidationErrors(prev => ({ ...prev, [field]: '' }))
        }
        clearError()
    }

    const validateForm = () => {
        const errors = {}
        if (!formData.fullName.trim()) errors.fullName = 'Full name is required'
        if (!formData.email.trim()) errors.email = 'Email is required'
        if (!formData.licenseNumber.trim()) errors.licenseNumber = 'License number is required'

        const passwordRegex = /^(?=.*[a-z])(?=.*[A-Z])(?=.*\d)(?=.*[!@#$%^&*()_+\-=[\]{};':"\\|,.<>/?`~]).{16,}$/
        if (!formData.password) {
            errors.password = 'Password is required'
        } else if (!passwordRegex.test(formData.password)) {
            errors.password = 'Password must be 16+ chars with mixed cases, digits & symbols'
        }

        if (formData.password !== formData.confirmPassword) {
            errors.confirmPassword = 'Passwords do not match'
        }

        setValidationErrors(errors)
        return Object.keys(errors).length === 0
    }

    const handleSubmit = async (e) => {
        e.preventDefault()
        if (!validateForm()) return

        const result = await registerDoctor(formData)
        if (result.success) {
            setSuccess(true)
        }
    }

    if (success) {
        return (
            <div className={styles.pageWrapper}>
                <TopBar userRole="administrator" onBack={() => {
                    setSuccess(false); setFormData({
                        fullName: '', email: '', password: '', confirmPassword: '', specialty: 'physician', phone: '', licenseNumber: ''
                    })
                }} />
                <div className={styles.container}>
                    <motion.div
                        className={styles.card}
                        initial={{ opacity: 0, scale: 0.95 }}
                        animate={{ opacity: 1, scale: 1 }}
                    >
                        <div className={styles.successView}>
                            <div className={styles.successIcon}>🛡️</div>
                            <h2 className={styles.title}>Account Provisioned</h2>
                            <p className={styles.subtitle}>
                                Doctor <strong>{formData.fullName}</strong> has been successfully registered.
                                <br /><br />
                                <span style={{ color: 'var(--color-primary)', fontWeight: '600' }}>
                                    ⚠️ ACTION REQUIRED: An activation email has been sent. The doctor must confirm their email before they can sign in.
                                </span>
                            </p>
                            <div className={styles.successActions}>
                                <AnimatedButton variant="primary" fullWidth onClick={() => {
                                    setSuccess(false); setFormData({
                                        fullName: '', email: '', password: '', confirmPassword: '', specialty: 'physician', phone: '', licenseNumber: ''
                                    })
                                }}>Provision Another Staff Member</AnimatedButton>
                                <AnimatedButton variant="secondary" fullWidth onClick={onBack}>Return to Dashboard</AnimatedButton>
                            </div>
                        </div>
                    </motion.div>
                </div>
            </div>
        )
    }

    return (
        <div className={styles.pageWrapper}>
            <TopBar userRole={userRole} onBack={onBack} />
            <div className={styles.container}>
                <motion.div
                    className={styles.card}
                    initial="hidden"
                    animate="visible"
                    variants={{
                        hidden: { opacity: 0, scale: 0.98 },
                        visible: {
                            opacity: 1,
                            scale: 1,
                            transition: {
                                duration: 0.8,
                                ease: [0.22, 1, 0.36, 1],
                                staggerChildren: 0.15
                            }
                        }
                    }}
                >
                    <div className={styles.header}>
                        <h1 className={styles.title}>Provision Medical Staff</h1>
                        <p className={styles.subtitle}>Add a new healthcare practitioner to the clinical network according to system schema.</p>
                    </div>

                    {error && <div className={styles.alertError}>{error}</div>}

                    <form onSubmit={handleSubmit} className={styles.form}>
                        <div className={styles.grid}>
                            <InputField
                                label="Professional Full Name"
                                placeholder="Dr. Ahmed Ali"
                                value={formData.fullName}
                                onChange={(e) => handleInputChange('fullName', e.target.value)}
                                error={validationErrors.fullName}
                                required
                                autoComplete="name"
                            />
                            <InputField
                                label="Medical Email"
                                type="email"
                                placeholder="a.ali@biointellect.com"
                                value={formData.email}
                                onChange={(e) => handleInputChange('email', e.target.value)}
                                error={validationErrors.email}
                                required
                                autoComplete="username"
                            />
                            <SelectField
                                label="Clinical Specialty / Role"
                                options={specialtyOptions}
                                value={formData.specialty}
                                onChange={(e) => handleInputChange('specialty', e.target.value)}
                            />
                            <InputField
                                label="Medical License Number"
                                placeholder="LIC-XXXXXX"
                                value={formData.licenseNumber}
                                onChange={(e) => handleInputChange('licenseNumber', e.target.value)}
                                error={validationErrors.licenseNumber}
                                required
                            />
                            <InputField
                                label="Security Password"
                                type="password"
                                placeholder="••••••••••••••••"
                                value={formData.password}
                                onChange={(e) => handleInputChange('password', e.target.value)}
                                error={validationErrors.password}
                                required
                                autoComplete="new-password"
                            />
                            <InputField
                                label="Confirm Password"
                                type="password"
                                placeholder="••••••••••••••••"
                                value={formData.confirmPassword}
                                onChange={(e) => handleInputChange('confirmPassword', e.target.value)}
                                error={validationErrors.confirmPassword}
                                required
                                autoComplete="new-password"
                            />
                            <div className={styles.fullGrid}>
                                <InputField
                                    label="Phone Number"
                                    placeholder="+20 1XX XXX XXXX"
                                    value={formData.phone}
                                    onChange={(e) => handleInputChange('phone', e.target.value)}
                                />
                            </div>
                        </div>

                        <AnimatedButton
                            type="submit"
                            variant="primary"
                            size="large"
                            fullWidth
                            isLoading={isLoading}
                        >
                            Provision Account & Grant Access
                        </AnimatedButton>
                    </form>
                </motion.div>
            </div>
        </div>
    )
}
