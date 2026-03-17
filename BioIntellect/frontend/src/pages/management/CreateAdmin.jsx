import { useState, useEffect, useMemo } from 'react'
import { motion } from 'framer-motion'
import { useAuth } from '@/store/AuthContext'
import { useGeography } from '@/hooks/useGeography'
import { TopBar } from '@/components/layout/TopBar'
import { InputField } from '@/components/ui/InputField'
import { SelectField } from '@/components/ui/SelectField'
import SearchableSelect from '@/components/ui/SearchableSelect'
import { AnimatedButton } from '@/components/ui/AnimatedButton'
import { validateMinimumPassword } from '@/utils/userFormUtils'
import styles from './CreateDoctor.module.css' // Reusing styles for consistency
import { adminOptions } from '@/config/options'

const CreateAdmin = ({ onBack, userRole }) => {
    const { registerAdmin, isLoading, error, clearError } = useAuth()
    const {
        countries,
        regions,
        hospitals,
        selectCountry,
        selectRegion,
        resolveNames
    } = useGeography()

    const [formData, setFormData] = useState({
        firstName: '',
        lastName: '',
        email: '',
        role: '',
        password: '',
        confirmPassword: '',
        phone: '',
        department: '',
        employeeId: '',
        countryId: '',
        regionId: '',
        hospitalId: ''
    })

    const [validationErrors, setValidationErrors] = useState({})
    const [success, setSuccess] = useState(false)
    const defaultCountryId = useMemo(() => {
        if (!countries.length) {
            return ''
        }

        return countries.find((country) => country.country_name === 'Egypt')?.country_id || countries[0].country_id
    }, [countries])

    const handleInputChange = (field, value) => {
        setFormData(prev => ({ ...prev, [field]: value }))
        if (validationErrors[field]) {
            setValidationErrors(prev => ({ ...prev, [field]: '' }))
        }
        clearError()
    }

    const onCountryChange = (e) => {
        const val = e.target.value
        handleInputChange('countryId', val)
        handleInputChange('regionId', '')
        handleInputChange('hospitalId', '')
        selectCountry(val)
    }

    const onRegionChange = (e) => {
        const val = e.target.value
        handleInputChange('regionId', val)
        handleInputChange('hospitalId', '')
        selectRegion(val)
    }

    // Set default country (Egypt) once countries are loaded
    useEffect(() => {
        if (!defaultCountryId || formData.countryId) {
            return
        }

        setFormData(prev => ({ ...prev, countryId: defaultCountryId }))
        selectCountry(defaultCountryId)
    }, [defaultCountryId, formData.countryId, selectCountry])

    const validateForm = () => {
        const errors = {}
        if (!formData.firstName.trim()) errors.firstName = 'First name is required'
        if (!formData.lastName.trim()) errors.lastName = 'Last name is required'
        if (!formData.email.trim()) errors.email = 'Administrative email is required'
        if (!formData.role) errors.role = 'System Role is required'
        if (!formData.hospitalId) errors.hospitalId = 'Assigned hospital is required'

        if (!formData.password) {
            errors.password = 'Password is required'
        } else {
            const passwordError = validateMinimumPassword(formData.password, 8)
            if (passwordError) {
                errors.password = passwordError
            }
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

        // Standardized Payload Construction
        const payload = resolveNames(formData);

        const result = await registerAdmin(payload)
        if (result.success) {
            setSuccess(true)
        }
    }

    if (success) {
        return (
            <div className={styles.pageWrapper}>
                <TopBar userRole="admin" onBack={() => {
                    setSuccess(false); setFormData({
                        firstName: '', lastName: '',
                        email: '', role: '', password: '', confirmPassword: '',
                        phone: '', department: '', employeeId: '',
                        countryId: '', regionId: '', hospitalId: ''
                    })
                }} />
                <div className={styles.container}>
                    <motion.div className={styles.card} initial={{ opacity: 0, scale: 0.95 }} animate={{ opacity: 1, scale: 1 }}>
                        <div className={styles.successView}>
                            <div className={styles.successIcon}>🔑</div>
                            <h2 className={styles.title}>Admin Access Granted</h2>
                            <p className={styles.subtitle}>
                                <strong>{formData.firstName} {formData.lastName}</strong> provisioned as {formData.role === 'admin' ? 'Administrator' : 'Super Admin'}.
                                <br /><br />
                                <span style={{ color: 'var(--color-primary)', fontWeight: '600' }}>
                                    Account created successfully. Share login credentials manually through your approved administrative onboarding process.
                                </span>
                            </p>
                            <div className={styles.successActions}>
                                <AnimatedButton variant="primary" fullWidth onClick={() => {
                                    setSuccess(false); setFormData({
                                        firstName: '', lastName: '',
                                        email: '', role: '', password: '', confirmPassword: '',
                                        phone: '', department: '', employeeId: '',
                                        countryId: '', regionId: '', hospitalId: ''
                                    })
                                }}>Provision Another Administrator</AnimatedButton>
                                <AnimatedButton variant="secondary" fullWidth onClick={onBack}>Back to Dashboard</AnimatedButton>
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
                <motion.div className={styles.card} initial="hidden" animate="visible" variants={{
                    hidden: { opacity: 0, y: 20 },
                    visible: { opacity: 1, y: 0, transition: { duration: 0.5 } }
                }}>
                    <div className={styles.header}>
                        <h1 className={styles.title}>Provision Secondary Administrator</h1>
                        <p className={styles.subtitle}>Grant administrative access to BioIntellect infrastructure.</p>
                    </div>

                    {error && <div className={styles.alertError}>{error}</div>}

                    <form onSubmit={handleSubmit} className={styles.form}>
                        <div className={styles.grid}>
                            <div className={styles.grid2}>
                                <InputField
                                    label="First Name (English)"
                                    placeholder="Admin"
                                    value={formData.firstName}
                                    onChange={(e) => handleInputChange('firstName', e.target.value)}
                                    error={validationErrors.firstName}
                                    required
                                />
                                <InputField
                                    label="Last Name (English)"
                                    placeholder="User"
                                    value={formData.lastName}
                                    onChange={(e) => handleInputChange('lastName', e.target.value)}
                                    error={validationErrors.lastName}
                                    required
                                />
                            </div>
                            <InputField
                                label="System Email"
                                type="email"
                                placeholder="admin@biointellect.com"
                                value={formData.email}
                                onChange={(e) => handleInputChange('email', e.target.value)}
                                error={validationErrors.email}
                                required
                            />
                            <SelectField
                                label="System Role"
                                value={formData.role}
                                onChange={(e) => handleInputChange('role', e.target.value)}
                                options={adminOptions}
                                required
                                error={validationErrors.role}
                            />
                            <InputField
                                label="Phone Number"
                                placeholder="+20 1XX XXX XXXX"
                                value={formData.phone}
                                onChange={(e) => handleInputChange('phone', e.target.value)}
                            />
                            <InputField
                                label="Department"
                                placeholder="IT / Engineering"
                                value={formData.department}
                                onChange={(e) => handleInputChange('department', e.target.value)}
                            />
                            <InputField
                                label="Employee ID"
                                value={formData.employeeId}
                                onChange={(e) => handleInputChange('employeeId', e.target.value)}
                            />
                            <SearchableSelect
                                label="Country"
                                value={formData.countryId}
                                onChange={onCountryChange}
                                options={countries.map(c => ({ value: c.country_id, label: c.country_name, flag_url: c.flag_url }))}
                                isCountry
                                required
                            />
                            <SearchableSelect
                                label="Region"
                                value={formData.regionId}
                                onChange={onRegionChange}
                                options={regions.map(r => ({ value: r.region_id, label: r.region_name }))}
                                required
                                disabled={!formData.countryId}
                            />
                            <SearchableSelect
                                label="Assigned Hospital"
                                value={formData.hospitalId}
                                onChange={(e) => handleInputChange('hospitalId', e.target.value)}
                                options={hospitals.map(h => ({ value: h.hospital_id, label: h.hospital_name }))}
                                required
                                disabled={!formData.regionId}
                                error={validationErrors.hospitalId}
                            />
                            <InputField
                                label="Security Password"
                                type="password"
                                value={formData.password}
                                onChange={(e) => handleInputChange('password', e.target.value)}
                                error={validationErrors.password}
                                required
                            />
                            <InputField
                                label="Confirm Password"
                                type="password"
                                value={formData.confirmPassword}
                                onChange={(e) => handleInputChange('confirmPassword', e.target.value)}
                                error={validationErrors.confirmPassword}
                                required
                            />
                        </div>

                        <AnimatedButton
                            type="submit"
                            variant="primary"
                            size="large"
                            fullWidth
                            isLoading={isLoading}
                            style={{ marginTop: '1.5rem' }}
                        >
                            Authorize Administrator Credentials
                        </AnimatedButton>
                    </form>
                </motion.div>
            </div>
        </div>
    )
}

export default CreateAdmin
