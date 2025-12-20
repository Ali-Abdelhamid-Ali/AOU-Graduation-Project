import { useState } from 'react'
import { motion, AnimatePresence } from 'framer-motion'
import { useAuth } from '../context/AuthContext'
import { TopBar } from '../components/TopBar'
import { InputField } from '../components/InputField'
import { SelectField } from '../components/SelectField'
import { AnimatedButton } from '../components/AnimatedButton'
import styles from './CreatePatient.module.css'

export const CreatePatient = ({ onBack, onComplete, userRole }) => {
    const { registerPatient, isLoading: authLoading } = useAuth()
    const [loading, setLoading] = useState(false)
    const [error, setError] = useState(null)
    const [success, setSuccess] = useState(null)
    const [showPassword, setShowPassword] = useState(false)

    // Production Policy: Default retention period is 5 years from today
    const getDefaultRetentionDate = () => {
        const date = new Date()
        date.setFullYear(date.getFullYear() + 5)
        return date.toISOString().split('T')[0]
    }

    const [formData, setFormData] = useState({
        email: '',
        password: '',
        firstName: '',
        lastName: '',
        dateOfBirth: '',
        gender: 'male',
        bloodType: '',
        phone: '',
        address: '',
        city: '',
        country: 'Egypt',
        allergies: '',
        chronicConditions: '',
        emergencyContactName: '',
        emergencyContactPhone: '',
        emergencyContactRelation: '',
        currentMedications: '',
        consentGiven: false,
        dataRetentionUntil: getDefaultRetentionDate()
    })

    const validatePassword = (pass) => {
        if (pass.length < 16) return "Password must be at least 16 characters long."
        if (!/[a-z]/.test(pass)) return "Password must contain at least one lowercase letter (a-z)."
        if (!/[A-Z]/.test(pass)) return "Password must contain at least one uppercase letter (A-Z)."
        if (!/[0-9]/.test(pass)) return "Password must contain at least one digit (0-9)."
        if (!/[!@#$%^&*()_+\-=[\]{};':"\\|,.<>/?./`~]/.test(pass)) return "Password must contain at least one special character."
        return null
    }

    const handleInputChange = (field, value) => {
        setFormData(prev => ({ ...prev, [field]: value }))
        setError(null)
    }

    const handleSubmit = async (e) => {
        e.preventDefault()

        const passwordError = validatePassword(formData.password)
        if (passwordError) {
            setError(passwordError)
            return
        }

        setLoading(true)
        setError(null)
        setSuccess(null)

        // Parse list fields and object fields
        const payload = {
            ...formData,
            allergies: formData.allergies ? formData.allergies.split(',').map(s => s.trim()).filter(Boolean) : [],
            chronicConditions: formData.chronicConditions ? formData.chronicConditions.split(',').map(s => s.trim()).filter(Boolean) : [],
            currentMedications: formData.currentMedications ? { medications: formData.currentMedications } : {}
        }

        const result = await registerPatient(payload)

        if (result.success) {
            setSuccess({
                message: 'Clinical record initialized and account provisioned!',
                mrn: result.mrn
            })
            // Reset form
            setFormData({
                email: '', password: '', firstName: '', lastName: '',
                dateOfBirth: '', gender: 'male', bloodType: '', phone: '',
                address: '', city: '', country: 'Egypt', allergies: '',
                chronicConditions: '', emergencyContactName: '',
                emergencyContactPhone: '', emergencyContactRelation: '',
                currentMedications: '', consentGiven: false, dataRetentionUntil: getDefaultRetentionDate()
            })
        } else {
            setError(result.error || 'Registration failed')
        }
        setLoading(false)
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
                        <div className={styles.headerTop}>
                            <span className={styles.unitTag}>CLINICAL PROVISIONING UNIT</span>
                        </div>
                        <h1 className={styles.title}>Patient Enrollment</h1>
                        <p className={styles.subtitle}>Establishing secure identities and immutable clinical records according to the BioIntellect schema.</p>
                    </div>

                    <AnimatePresence mode="wait">
                        {error && (
                            <motion.div
                                initial={{ opacity: 0, height: 0 }}
                                animate={{ opacity: 1, height: 'auto' }}
                                exit={{ opacity: 0, height: 0 }}
                                className={styles.alertError}
                            >
                                {error}
                            </motion.div>
                        )}
                        {success && (
                            <motion.div
                                initial={{ opacity: 0, height: 0 }}
                                animate={{ opacity: 1, height: 'auto' }}
                                className={styles.alertSuccess}
                            >
                                <div className={styles.successTitle}>{success.message}</div>
                                <div className={styles.successDetail}>
                                    Assigned MRN: <code className={styles.mrnCode}>{success.mrn}</code>
                                </div>
                            </motion.div>
                        )}
                    </AnimatePresence>

                    <form onSubmit={handleSubmit} className={styles.form}>

                        {/* Section 1: Security */}
                        <section className={styles.section}>
                            <div className={styles.sectionHeader}>
                                <div className={styles.sectionNumber}>1</div>
                                <h3 className={styles.sectionTitle}>System Credentials</h3>
                            </div>
                            <div className={`${styles.grid} ${styles.grid2}`}>
                                <InputField
                                    id="email"
                                    label="Administrative Email"
                                    type="email"
                                    placeholder="p.account@biointellect.org"
                                    value={formData.email}
                                    onChange={(e) => handleInputChange('email', e.target.value)}
                                    required
                                    autoComplete="username"
                                />
                                <div className={styles.passwordWrapper}>
                                    <InputField
                                        id="password"
                                        label="Provisioning Password"
                                        type={showPassword ? "text" : "password"}
                                        placeholder="Secure 16+ char string"
                                        value={formData.password}
                                        onChange={(e) => handleInputChange('password', e.target.value)}
                                        required
                                        autoComplete="new-password"
                                    />
                                    <button
                                        type="button"
                                        onClick={() => setShowPassword(!showPassword)}
                                        className={styles.togglePassword}
                                    >
                                        {showPassword ? "HIDE" : "SHOW"}
                                    </button>
                                </div>
                            </div>
                        </section>

                        {/* Section 2: Personal Identity */}
                        <section className={styles.section}>
                            <div className={styles.sectionHeader}>
                                <div className={styles.sectionNumber}>2</div>
                                <h3 className={styles.sectionTitle}>Patient Persona</h3>
                            </div>
                            <div className={`${styles.grid} ${styles.grid3}`}>
                                <InputField label="First Name" value={formData.firstName} onChange={(e) => handleInputChange('firstName', e.target.value)} required autoComplete="given-name" />
                                <InputField label="Last Name" value={formData.lastName} onChange={(e) => handleInputChange('lastName', e.target.value)} required autoComplete="family-name" />
                                <InputField label="Date of Birth" type="date" value={formData.dateOfBirth} onChange={(e) => handleInputChange('dateOfBirth', e.target.value)} required autoComplete="bday" />
                                <SelectField
                                    label="Gender Identification"
                                    value={formData.gender}
                                    onChange={(e) => handleInputChange('gender', e.target.value)}
                                    options={[{ value: 'male', label: 'Male' }, { value: 'female', label: 'Female' }]}
                                    required
                                />
                                <SelectField
                                    label="Blood Type"
                                    value={formData.bloodType}
                                    onChange={(e) => handleInputChange('bloodType', e.target.value)}
                                    options={['A+', 'A-', 'B+', 'B-', 'AB+', 'AB-', 'O+', 'O-'].map(t => ({ value: t, label: t }))}
                                />
                                <InputField label="Phone Number" value={formData.phone} onChange={(e) => handleInputChange('phone', e.target.value)} autoComplete="tel" />
                            </div>
                        </section>

                        {/* Section 3: Contact & Logistics */}
                        <section className={styles.section}>
                            <div className={styles.sectionHeader}>
                                <div className={styles.sectionNumber}>3</div>
                                <h3 className={styles.sectionTitle}>Residence & Logistics</h3>
                            </div>
                            <div className={`${styles.grid} ${styles.grid3}`}>
                                <InputField label="Country" value={formData.country} onChange={(e) => handleInputChange('country', e.target.value)} autoComplete="country-name" />
                                <InputField label="City" value={formData.city} onChange={(e) => handleInputChange('city', e.target.value)} autoComplete="address-level2" />
                                <InputField label="Permanent Address" value={formData.address} onChange={(e) => handleInputChange('address', e.target.value)} autoComplete="street-address" />
                            </div>
                        </section>

                        {/* Section 4: Emergency Contacts */}
                        <section className={styles.section}>
                            <div className={styles.sectionHeader}>
                                <div className={styles.sectionNumber}>4</div>
                                <h3 className={styles.sectionTitle}>Emergency Network</h3>
                            </div>
                            <div className={`${styles.grid} ${styles.grid3}`}>
                                <InputField label="Contact Name" value={formData.emergencyContactName} onChange={(e) => handleInputChange('emergencyContactName', e.target.value)} />
                                <InputField label="Contact Phone" value={formData.emergencyContactPhone} onChange={(e) => handleInputChange('emergencyContactPhone', e.target.value)} />
                                <InputField label="Relationship" value={formData.emergencyContactRelation} onChange={(e) => handleInputChange('emergencyContactRelation', e.target.value)} />
                            </div>
                        </section>

                        {/* Section 5: Clinical History */}
                        <section className={styles.section}>
                            <div className={styles.sectionHeader}>
                                <div className={styles.sectionNumber}>5</div>
                                <h3 className={styles.sectionTitle}>Clinical Baseline</h3>
                            </div>
                            <div className={`${styles.grid} ${styles.grid2}`}>
                                <InputField label="Known Allergies (comma separated)" placeholder="E.g. Penicillin, Peanuts" value={formData.allergies} onChange={(e) => handleInputChange('allergies', e.target.value)} />
                                <InputField label="Chronic Conditions (comma separated)" placeholder="E.g. Diabetes Type II, Hypertension" value={formData.chronicConditions} onChange={(e) => handleInputChange('chronicConditions', e.target.value)} />
                                <InputField label="Current Medications" placeholder="List medications and dosages..." value={formData.currentMedications} onChange={(e) => handleInputChange('currentMedications', e.target.value)} multiline />
                                <InputField label="Data Retention Until" type="date" value={formData.dataRetentionUntil} onChange={(e) => handleInputChange('dataRetentionUntil', e.target.value)} helperText="End date for the clinical data storage policy." />
                            </div>
                        </section>

                        {/* Section 6: Legal Consent */}
                        <section className={styles.consentSection}>
                            <input
                                type="checkbox"
                                id="consent"
                                checked={formData.consentGiven}
                                onChange={(e) => handleInputChange('consentGiven', e.target.checked)}
                                className={styles.checkbox}
                            />
                            <div className={styles.consentContent}>
                                <label htmlFor="consent" className={styles.consentLabel}>Mandatory Patient Consent</label>
                                <p className={styles.consentText}>
                                    By checking this, you confirm that the patient has provided explicit legal consent for their medical data to be processed within the BioIntellect system according to the established retention period.
                                </p>
                            </div>
                        </section>

                        <AnimatedButton
                            type="submit"
                            variant="primary"
                            size="large"
                            fullWidth
                            disabled={!formData.consentGiven}
                            isLoading={loading || authLoading}
                            className={styles.submitButton}
                            style={{
                                opacity: formData.consentGiven ? 1 : 0.6,
                                cursor: formData.consentGiven ? 'pointer' : 'not-allowed'
                            }}
                        >
                            Finalize Enrollment & Deploy Account
                        </AnimatedButton>
                    </form>
                </motion.div>
            </div>
        </div>
    )
}
