import { fireEvent, render, screen, waitFor } from '@testing-library/react'
import { describe, expect, it, beforeEach, vi } from 'vitest'

import { MriSegmentation } from './MriSegmentation'

const createCase = vi.fn()
const uploadFile = vi.fn()
const getModelInfo = vi.fn()
const runSegmentation = vi.fn()
const getSeverityClassification = vi.fn()

vi.mock('@/store/AuthContext', () => ({
  useAuth: () => ({
    currentUser: {
      id: 'patient-1',
      hospital_id: 'hospital-1',
      first_name: 'Ali',
      last_name: 'Patient',
      mrn: 'MRN-100',
    },
    userRole: 'patient',
  }),
}))

vi.mock('@/services/medical.service', () => ({
  medicalService: {
    createCase: (...args) => createCase(...args),
    uploadFile: (...args) => uploadFile(...args),
    createMriScan: vi.fn(),
    saveMriSegmentationResult: vi.fn(),
    reviewResult: vi.fn(),
  },
}))

vi.mock('@/services/clinical.service', () => ({
  mriSegmentationService: {
    getModelInfo: (...args) => getModelInfo(...args),
    runSegmentation: (...args) => runSegmentation(...args),
    getSeverityClassification: (...args) => getSeverityClassification(...args),
  },
}))

vi.mock('@/services/api', () => ({
  patientsAPI: {
    list: vi.fn(),
  },
}))

vi.mock('../../components/clinical/MriVolumeViewer', () => ({
  MriVolumeViewer: () => <div>viewer-ready</div>,
}))

vi.mock('../../components/clinical/MriPatientView', () => ({
  MriPatientView: () => <div>patient-summary</div>,
}))

vi.mock('../../components/clinical/MriDoctorView', () => ({
  MriDoctorView: () => <div>doctor-summary</div>,
}))

vi.mock('@/components/layout/TopBar', () => ({
  TopBar: () => <div>top-bar</div>,
}))

vi.mock('@/components/ui/SelectField', () => ({
  SelectField: ({ label, value, onChange, options = [] }) => (
    <label>
      {label}
      <select value={value} onChange={onChange}>
        {options.map((option) => (
          <option key={option.value} value={option.value}>
            {option.label}
          </option>
        ))}
      </select>
    </label>
  ),
}))

vi.mock('@/components/ui/AnimatedButton', () => ({
  AnimatedButton: ({ children, onClick, disabled, isLoading }) => (
    <button type="button" onClick={onClick} disabled={disabled}>
      {isLoading ? 'Loading' : children}
    </button>
  ),
}))

describe('MriSegmentation', () => {
  beforeEach(() => {
    createCase.mockReset()
    uploadFile.mockReset()
    getModelInfo.mockReset()
    runSegmentation.mockReset()
    getSeverityClassification.mockReset()

    getModelInfo.mockResolvedValue({
      version: '2026.03',
      name: 'BioIntellect Brain MRI 3D U-Net',
      release_date: '2026-03-01',
    })
    getSeverityClassification.mockReturnValue({
      level: 'high',
      color: '#ff9800',
      label: 'Significant Finding',
      description: 'Large region detected. Urgent clinical review recommended.',
    })
    createCase.mockResolvedValue({ id: 'case-1' })
    runSegmentation.mockResolvedValue({
      case_id: 'seg-case-1',
      model_info: {
        version: '2026.03',
        name: 'BioIntellect Brain MRI 3D U-Net',
      },
      inference_timestamp: '2026-03-10T20:34:00Z',
      tumor_detected: true,
      total_volume_cm3: 12.5,
      regions: [
        {
          class_id: 2,
          class_name: 'Peritumoral Edema',
          present: true,
          volume_cm3: 12.5,
          percentage: 100,
          color: [80, 255, 80],
        },
      ],
      prediction_confidence: {
        overall: 0.964,
        tumor_presence: 0.98,
        segmentation_quality: 0.999,
      },
      disclaimer: 'AI output supports review only and must be confirmed by a clinician.',
      requires_review: true,
      visualization: {},
      measurements: {
        largest_diameter_mm: 35.2,
        voxel_volume_mm3: 6.35,
        effective_spacing_mm: [2.14, 2.14, 1.38],
      },
      processing_metadata: {},
      ai_interpretation:
        'Predicted abnormal enhancing intracranial lesion with volumetric segmentation.',
      ai_recommendations: ['Urgent neuroradiology review recommended.'],
    })
  })

  it('keeps segmentation results visible when record sync fails', async () => {
    uploadFile.mockRejectedValue({
      detail:
        "{'statusCode': 400, 'error': InvalidRequest, 'message': mime type application/octet-stream is not supported}",
    })

    const { container } = render(<MriSegmentation onBack={vi.fn()} />)

    const fileInputs = Array.from(container.querySelectorAll('input[type="file"]'))
    expect(fileInputs).toHaveLength(4)

    for (const [index, input] of fileInputs.entries()) {
      const names = ['t1.nii.gz', 't1ce.nii.gz', 't2.nii.gz', 'flair.nii.gz']
      fireEvent.change(input, {
        target: {
          files: [new File(['nifti'], names[index], { type: 'application/x-gzip' })],
        },
      })
    }

    fireEvent.click(screen.getByText('Run Segmentation'))

    await waitFor(() => {
      expect(screen.getByText('Segmentation completed, but record sync needs attention')).toBeTruthy()
    })

    expect(
      screen.getAllByText('Segmentation completed, but saving the MRI source files failed.')
        .length
    ).toBeGreaterThanOrEqual(1)
    expect(screen.getByText('Technical details')).toBeTruthy()
    expect(screen.getByText('Retry Record Sync')).toBeTruthy()
    expect(screen.getByText('Source File Persistence')).toBeTruthy()
    expect(screen.getByText('patient-summary')).toBeTruthy()
    expect(screen.getByText('viewer-ready')).toBeTruthy()
  })
})
