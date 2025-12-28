import { useState, useEffect } from 'react'
import { useForm } from 'react-hook-form'
import { zodResolver } from '@hookform/resolvers/zod'
import { motion, AnimatePresence } from 'framer-motion'
import { signupSchema, SignupSchema } from '../../utils/validation'
import { signUp } from '../../lib/auth'
import { useGeography } from '../../hooks/useGeography'
import { AnimatedButton } from '../AnimatedButton'

interface SignupFormProps {
    initialRole?: 'admin' | 'doctor' | 'nurse' | 'patient' | 'super_admin'
    onSuccess?: () => void
    onLoginClick?: () => void
}

export const SignupForm = ({ initialRole = 'patient', onSuccess, onLoginClick }: SignupFormProps) => {
    const [serverError, setServerError] = useState<string | null>(null)
    const [successMsg, setSuccessMsg] = useState<string | null>(null)
    const { countries, regions, hospitals, selectCountry, selectRegion } = useGeography()

    const {
        register,
        handleSubmit,
        watch,
        formState: { errors, isSubmitting },
    } = useForm<SignupSchema>({
        resolver: zodResolver(signupSchema),
        defaultValues: {
            role: initialRole,
            gender: 'male',
            country_id: '',
            region_id: '',
            hospital_id: '',
            first_name: '',
            last_name: '',
            email: '',
            password: '',
            license_number: '',
            date_of_birth: ''
        }
    })

    // Watch fields for dynamic logic
    const selectedRole = watch('role')
    const selectedCountry = watch('country_id')
    const selectedRegion = watch('region_id')

    // Effect to load initial country if needed
    useEffect(() => {
        if (countries.length > 0 && !selectedCountry) {
            const egypt = countries.find(c => c.country_name === 'Egypt')
            if (egypt) {
                selectCountry(egypt.country_id)
            }
        }
    }, [countries])

    const onSubmit = async (data: SignupSchema) => {
        setServerError(null)
        setSuccessMsg(null)

        // Explicitly cast or map data to ensure it matches the API expectations if needed
        // But SignupSchema now matches SignupFormData mostly
        const result = await signUp(data as any) // Cast to any to avoid strict type mismatch if minor diffs exist

        if (result.success) {
            setSuccessMsg('Account created successfully! Please check your email for verification.')
            if (onSuccess) {
                setTimeout(onSuccess, 2000)
            }
        } else {
            setServerError(result.error || 'Registration failed')
        }
    }

    // Animation variants
    const fadeIn = {
        hidden: { opacity: 0, y: 10 },
        visible: { opacity: 1, y: 0 }
    }

    return (
        <div className="w-full max-w-2xl mx-auto p-6 bg-white rounded-xl shadow-lg border border-gray-100 dark:bg-slate-800 dark:border-slate-700">
            <div className="mb-8 text-center">
                <h2 className="text-3xl font-bold bg-gradient-to-r from-blue-600 to-teal-500 bg-clip-text text-transparent">
                    Create Account
                </h2>
                <p className="text-gray-500 mt-2">Join BioIntellect Medical System</p>
            </div>

            {serverError && (
                <motion.div
                    initial="hidden" animate="visible" variants={fadeIn}
                    className="mb-6 p-4 bg-red-50 border border-red-200 rounded-lg flex items-center gap-3 text-red-700"
                >
                    <span>⚠️ {serverError}</span>
                </motion.div>
            )}

            {successMsg && (
                <motion.div
                    initial="hidden" animate="visible" variants={fadeIn}
                    className="mb-6 p-4 bg-green-50 border border-green-200 rounded-lg flex items-center gap-3 text-green-700"
                >
                    <span>✅ {successMsg}</span>
                </motion.div>
            )}

            <form onSubmit={handleSubmit(onSubmit)} className="space-y-6">

                {/* Role Selection */}
                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                    <div>
                        <label className="block text-sm font-medium text-gray-700 mb-1">Role</label>
                        <select
                            {...register('role')}
                            className="w-full p-2.5 rounded-lg border border-gray-300 focus:ring-2 focus:ring-blue-500 transition-all bg-white"
                        >
                            <option value="admin">Administrator</option>
                            <option value="doctor">Doctor</option>
                            <option value="nurse">Nurse</option>
                            <option value="patient">Patient</option>
                            <option value="super_admin">Super Admin</option>
                        </select>
                        {errors.role && <p className="text-red-500 text-sm mt-1">{errors.role.message}</p>}
                    </div>
                </div>

                {/* Personal Info */}
                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                    <div>
                        <label className="block text-sm font-medium text-gray-700 mb-1">First Name</label>
                        <input
                            {...register('first_name')}
                            className="w-full p-2.5 rounded-lg border border-gray-300 focus:ring-2 focus:ring-blue-500"
                            placeholder="First Name"
                        />
                        {errors.first_name && <p className="text-red-500 text-sm mt-1">{errors.first_name.message}</p>}
                    </div>
                    <div>
                        <label className="block text-sm font-medium text-gray-700 mb-1">Last Name</label>
                        <input
                            {...register('last_name')}
                            className="w-full p-2.5 rounded-lg border border-gray-300 focus:ring-2 focus:ring-blue-500"
                            placeholder="Last Name"
                        />
                        {errors.last_name && <p className="text-red-500 text-sm mt-1">{errors.last_name.message}</p>}
                    </div>
                </div>

                {/* Email & Password */}
                <div>
                    <label className="block text-sm font-medium text-gray-700 mb-1">Email Address</label>
                    <input
                        {...register('email')}
                        type="email"
                        className="w-full p-2.5 rounded-lg border border-gray-300 focus:ring-2 focus:ring-blue-500"
                        placeholder="name@hospital.com"
                    />
                    {errors.email && <p className="text-red-500 text-sm mt-1">{errors.email.message}</p>}
                </div>

                <div>
                    <label className="block text-sm font-medium text-gray-700 mb-1">Password</label>
                    <input
                        {...register('password')}
                        type="password"
                        className="w-full p-2.5 rounded-lg border border-gray-300 focus:ring-2 focus:ring-blue-500"
                        placeholder="••••••••"
                    />
                    {errors.password && <p className="text-red-500 text-sm mt-1">{errors.password.message}</p>}
                </div>

                {/* Dynamic Fields */}
                <AnimatePresence>

                    {/* Hospital Selection (Not for Super Admin) */}
                    {selectedRole !== 'super_admin' && (
                        <motion.div
                            initial={{ opacity: 0, height: 0 }}
                            animate={{ opacity: 1, height: 'auto' }}
                            exit={{ opacity: 0, height: 0 }}
                            className="space-y-4"
                        >
                            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                                {/* Geography Simulators for UI only - controlled manually or via additional logic */}
                                {/* Note: In a real app we'd bind these to form state better, keeping it simple for now */}

                                <div>
                                    <label className="block text-sm font-medium text-gray-700 mb-1">Country</label>
                                    <select
                                        className="w-full p-2.5 rounded-lg border border-gray-300"
                                        onChange={(e) => {
                                            selectCountry(e.target.value)
                                        }}
                                    >
                                        <option value="">Select Country</option>
                                        {countries.map(c => (
                                            <option key={c.country_id} value={c.country_id}>{c.country_name}</option>
                                        ))}
                                    </select>
                                </div>
                                <div>
                                    <label className="block text-sm font-medium text-gray-700 mb-1">Region</label>
                                    <select
                                        className="w-full p-2.5 rounded-lg border border-gray-300"
                                        onChange={(e) => {
                                            selectRegion(e.target.value)
                                        }}
                                    >
                                        <option value="">Select Region</option>
                                        {regions.map(r => (
                                            <option key={r.region_id} value={r.region_id}>{r.region_name}</option>
                                        ))}
                                    </select>
                                </div>
                            </div>

                            <div>
                                <label className="block text-sm font-medium text-gray-700 mb-1">
                                    Hospital {['admin', 'doctor', 'nurse'].includes(selectedRole) && <span className="text-red-500">*</span>}
                                </label>
                                <select
                                    {...register('hospital_id')}
                                    className="w-full p-2.5 rounded-lg border border-gray-300 focus:ring-2 focus:ring-blue-500"
                                >
                                    <option value="">Select Hospital</option>
                                    {hospitals.map(h => (
                                        <option key={h.hospital_id} value={h.hospital_id}>{h.hospital_name}</option>
                                    ))}
                                </select>
                                {errors.hospital_id && <p className="text-red-500 text-sm mt-1">{errors.hospital_id.message}</p>}
                            </div>
                        </motion.div>
                    )}

                    {/* Doctor Specific */}
                    {selectedRole === 'doctor' && (
                        <motion.div
                            initial={{ opacity: 0, height: 0 }}
                            animate={{ opacity: 1, height: 'auto' }}
                            className="pt-2"
                        >
                            <label className="block text-sm font-medium text-gray-700 mb-1">License Number</label>
                            <input
                                {...register('license_number')}
                                className="w-full p-2.5 rounded-lg border border-gray-300 focus:ring-2 focus:ring-blue-500"
                                placeholder="MED-12345"
                            />
                            {errors.license_number && <p className="text-red-500 text-sm mt-1">{errors.license_number.message}</p>}
                        </motion.div>
                    )}
                </AnimatePresence>

                <div className="pt-4">
                    <AnimatedButton
                        type="submit"
                        variant="primary"
                        size="large"
                        fullWidth
                        isLoading={isSubmitting}
                        disabled={isSubmitting}
                    >
                        {isSubmitting ? 'Creating Account...' : 'Create Account'}
                    </AnimatedButton>
                </div>

                <div className="text-center text-sm text-gray-500">
                    Already have an account?{' '}
                    <button type="button" onClick={onLoginClick} className="text-blue-600 hover:text-blue-700 font-medium">
                        Sign in
                    </button>
                </div>
            </form>
        </div>
    )
}
