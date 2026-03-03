/**
 * MRI Segmentation Service
 * Handles communication with the FastAPI backend for brain tumor segmentation.
 * Medical-grade API client with proper error handling and audit support.
 */

const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000'

/**
 * @typedef {Object} TumorRegion
 * @property {number} class_id
 * @property {string} class_name
 * @property {number} volume_voxels
 * @property {number} volume_mm3
 * @property {number} volume_cm3
 * @property {number} percentage
 */

/**
 * @typedef {Object} ModelInfo
 * @property {string} name
 * @property {string} version
 * @property {string} checksum
 * @property {string} release_date
 */

/**
 * @typedef {Object} SegmentationResult
 * @property {string} case_id
 * @property {string} inference_timestamp
 * @property {ModelInfo} model_info
 * @property {string} input_checksum
 * @property {number[]} input_shape
 * @property {boolean} tumor_detected
 * @property {TumorRegion[]} regions
 * @property {number} total_volume_cm3
 * @property {Object} prediction_confidence
 * @property {string} labels_filename
 * @property {string} image_filename
 * @property {boolean} requires_review
 * @property {string} disclaimer
 */

export const mriSegmentationService = {
    /**
     * Get current model version information.
     * Useful for audit trails and compliance.
     * @returns {Promise<ModelInfo>}
     */
    async getModelInfo() {
        const response = await fetch(`${API_BASE_URL}/api/v1/model/info`)

        if (!response.ok) {
            throw new Error('Failed to fetch model information')
        }

        return response.json()
    },

    /**
     * Run brain tumor segmentation on uploaded MRI scans.
     * Requires all 4 BraTS modalities: T1, T1ce, T2, FLAIR.
     * 
     * @param {Object} files - Object containing the 4 MRI files
     * @param {File} files.t1 - T1-weighted MRI
     * @param {File} files.t1ce - T1-contrast enhanced MRI
     * @param {File} files.t2 - T2-weighted MRI
     * @param {File} files.flair - FLAIR MRI
     * @param {Object} options - Additional options
     * @param {string} [options.patientId] - Patient ID for linking results
     * @param {function} [options.onProgress] - Progress callback
     * @returns {Promise<SegmentationResult>}
     */
    async runSegmentation(files, options = {}) {
        const { t1, t1ce, t2, flair } = files

        // Validate required files
        if (!t1 || !t1ce || !t2 || !flair) {
            throw new Error('All 4 MRI modalities are required: T1, T1ce, T2, FLAIR')
        }

        // Validate file types
        const validExtensions = ['.nii', '.nii.gz']
        for (const [name, file] of Object.entries(files)) {
            const ext = file.name.toLowerCase()
            if (!validExtensions.some(e => ext.endsWith(e))) {
                throw new Error(`Invalid file format for ${name}. Expected NIfTI (.nii or .nii.gz)`)
            }
        }

        // Prepare form data
        const formData = new FormData()
        formData.append('t1', t1)
        formData.append('t1ce', t1ce)
        formData.append('t2', t2)
        formData.append('flair', flair)

        // Build URL with optional patient ID
        let url = `${API_BASE_URL}/api/v1/mri/segment`
        if (options.patientId) {
            url += `?patient_id=${encodeURIComponent(options.patientId)}`
        }

        // Make request with timeout
        const controller = new AbortController()
        const timeout = setTimeout(() => controller.abort(), 300000) // 5 minute timeout

        try {
            const response = await fetch(url, {
                method: 'POST',
                body: formData,
                signal: controller.signal
            })

            clearTimeout(timeout)

            if (!response.ok) {
                const errorData = await response.json().catch(() => ({}))
                throw new Error(errorData.detail || `Segmentation failed: ${response.status}`)
            }

            return response.json()
        } catch (error) {
            clearTimeout(timeout)

            if (error.name === 'AbortError') {
                throw new Error('Segmentation request timed out. Please try again.')
            }

            throw error
        }
    },

    /**
     * Get patient-friendly view of segmentation results.
     * Uses simplified, non-alarming language.
     * 
     * @param {string} caseId - Case ID from segmentation result
     * @returns {Promise<Object>}
     */
    async getPatientFriendlyResult(caseId) {
        const response = await fetch(
            `${API_BASE_URL}/api/v1/mri/result/${caseId}/patient-view`
        )

        if (!response.ok) {
            throw new Error('Failed to fetch patient-friendly result')
        }

        return response.json()
    },

    /**
     * Download segmentation output file.
     * 
     * @param {string} filename - Output filename
     * @returns {Promise<ArrayBuffer>}
     */
    async downloadOutputFile(filename) {
        const response = await fetch(`${API_BASE_URL}/api/v1/outputs/${filename}`)

        if (!response.ok) {
            throw new Error('Failed to download output file')
        }

        return response.arrayBuffer()
    },

    /**
     * Format tumor volume for display.
     * 
     * @param {number} volumeCm3 - Volume in cubic centimeters
     * @param {boolean} isPatient - Whether this is for patient display
     * @returns {string}
     */
    formatVolume(volumeCm3, isPatient = false) {
        if (isPatient) {
            // Simplified for patient view
            if (volumeCm3 < 1) {
                return 'Small area detected'
            } else if (volumeCm3 < 10) {
                return 'Moderate area detected'
            } else {
                return 'Significant area detected'
            }
        }

        // Clinical format for doctors
        return `${volumeCm3.toFixed(2)} cm³`
    },

    /**
     * Get clinical severity classification.
     * 
     * @param {SegmentationResult} result - Segmentation result
     * @returns {Object} Severity classification with level and description
     */
    getSeverityClassification(result) {
        const totalVolume = result.total_volume_cm3
        const hasEnhancing = result.regions.some(r => r.class_id === 3 && r.volume_cm3 > 0)

        if (!result.tumor_detected || totalVolume === 0) {
            return {
                level: 'normal',
                color: '#4CAF50',
                label: 'No Abnormalities Detected',
                description: 'AI analysis did not detect tumor presence.'
            }
        }

        if (totalVolume < 5 && !hasEnhancing) {
            return {
                level: 'low',
                color: '#8BC34A',
                label: 'Low Grade Finding',
                description: 'Small region detected. Recommend clinical correlation.'
            }
        }

        if (totalVolume < 20) {
            return {
                level: 'moderate',
                color: '#FFC107',
                label: 'Moderate Finding',
                description: 'Significant region detected. Further evaluation recommended.'
            }
        }

        return {
            level: 'high',
            color: '#FF9800',
            label: 'Significant Finding',
            description: 'Large region detected. Urgent clinical review recommended.'
        }
    },

    /**
     * Map clinical class names to patient-friendly terms.
     * 
     * @param {string} clinicalName - Clinical class name
     * @returns {string} Patient-friendly name
     */
    getPatientFriendlyClassName(clinicalName) {
        const mapping = {
            'Necrotic/Non-Enhancing Tumor Core': 'Central Region',
            'Peritumoral Edema': 'Surrounding Area',
            'Enhancing Tumor': 'Active Region'
        }
        return mapping[clinicalName] || 'Region of Interest'
    }
}

export default mriSegmentationService
