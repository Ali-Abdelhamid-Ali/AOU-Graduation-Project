import { useEffect, useMemo, useRef, useState } from 'react'
import '@kitware/vtk.js/Rendering/Profiles/Geometry'
import '@kitware/vtk.js/Rendering/Profiles/Volume'
import vtkColorTransferFunction from '@kitware/vtk.js/Rendering/Core/ColorTransferFunction'
import vtkDataArray from '@kitware/vtk.js/Common/Core/DataArray'
import vtkGenericRenderWindow from '@kitware/vtk.js/Rendering/Misc/GenericRenderWindow'
import vtkImageData from '@kitware/vtk.js/Common/DataModel/ImageData'
import vtkPiecewiseFunction from '@kitware/vtk.js/Common/DataModel/PiecewiseFunction'
import vtkVolume from '@kitware/vtk.js/Rendering/Core/Volume'
import vtkVolumeMapper from '@kitware/vtk.js/Rendering/Core/VolumeMapper'
import { mriSegmentationService } from '@/services/clinical.service'
import { parseNumpyFile } from '@/utils/parseNumpyFile'
import styles from './MriVolumeViewer.module.css'

const MODALITY_ORDER = ['t1', 't1ce', 't2', 'flair']
const MODALITY_LABELS = {
  t1: 'T1',
  t1ce: 'T1CE',
  t2: 'T2',
  flair: 'FLAIR',
}

const CLASS_CONFIG = {
  1: {
    label: 'Necrotic / Non-Enhancing Core',
    color: [255, 80, 80],
  },
  2: {
    label: 'Peritumoral Edema',
    color: [80, 255, 80],
  },
  3: {
    label: 'Enhancing Tumor',
    color: [80, 80, 255],
  },
}

const VISUAL_PRESETS = {
  balanced: {
    label: 'Balanced',
    description: 'Blend anatomy and segmentation evenly.',
  },
  tumorFocus: {
    label: 'Tumor Focus',
    description: 'Dim anatomy to isolate tumor-bearing regions.',
  },
  edemaFocus: {
    label: 'Edema Focus',
    description: 'Highlight surrounding edema distribution.',
  },
  anatomy: {
    label: 'Anatomy First',
    description: 'Keep brain anatomy dominant with lighter overlay.',
  },
}

const buildDefaultVisibility = (classes = []) =>
  classes.reduce(
    (accumulator, item) => ({
      ...accumulator,
      [item.class_id]: true,
    }),
    { 1: true, 2: true, 3: true }
  )

const getCaseId = (result) => result?.caseId || result?.case_id || null

const getSpacingXYZ = (spacing = []) => {
  if (!Array.isArray(spacing) || spacing.length !== 3) {
    return [1, 1, 1]
  }

  return [spacing[2] || 1, spacing[1] || 1, spacing[0] || 1]
}

const getDimensionsXYZ = (shape = []) => {
  if (!Array.isArray(shape) || shape.length !== 3) {
    throw new Error('Invalid MRI label shape.')
  }

  return [shape[2], shape[1], shape[0]]
}

const getChannelScalars = (imageDataset, modality) => {
  const modalityIndex = MODALITY_ORDER.indexOf(modality)
  const [channels, depth, height, width] = imageDataset.shape
  if (modalityIndex < 0 || channels <= modalityIndex) {
    throw new Error(`Unsupported MRI modality selected: ${modality}`)
  }

  const voxelsPerChannel = depth * height * width
  const start = modalityIndex * voxelsPerChannel
  const end = start + voxelsPerChannel
  return new Float32Array(imageDataset.data.slice(start, end))
}

const computeScalarRange = (values) => {
  let min = Number.POSITIVE_INFINITY
  let max = Number.NEGATIVE_INFINITY

  for (let index = 0; index < values.length; index += 1) {
    const value = values[index]
    if (value === 0) continue
    if (value < min) min = value
    if (value > max) max = value
  }

  if (!Number.isFinite(min) || !Number.isFinite(max) || min === max) {
    return { min: -1, max: 1 }
  }

  return { min, max }
}

const createImageData = ({ scalars, label, dimensions, spacing }) => {
  const imageData = vtkImageData.newInstance()
  imageData.setDimensions(...dimensions)
  imageData.setSpacing(...spacing)
  imageData.getPointData().setScalars(
    vtkDataArray.newInstance({
      name: label,
      values: scalars,
      numberOfComponents: 1,
    })
  )
  return imageData
}

const clampOpacity = (value) => Math.max(0, Math.min(value, 1))

const configureBaseVolume = ({
  imageData,
  range,
  baseOpacityScale,
  useShading,
}) => {
  const mapper = vtkVolumeMapper.newInstance()
  mapper.setInputData(imageData)
  mapper.setSampleDistance(useShading ? 0.7 : 0.9)

  const volume = vtkVolume.newInstance()
  volume.setMapper(mapper)

  const colorTransfer = vtkColorTransferFunction.newInstance()
  colorTransfer.addRGBPoint(range.min, 0.0, 0.0, 0.0)
  colorTransfer.addRGBPoint(
    range.min + (range.max - range.min) * 0.4,
    0.35,
    0.35,
    0.38
  )
  colorTransfer.addRGBPoint(range.max, 1.0, 1.0, 1.0)

  const opacity = vtkPiecewiseFunction.newInstance()
  opacity.addPoint(range.min, 0.0)
  opacity.addPoint(range.min + (range.max - range.min) * 0.2, 0.0)
  opacity.addPoint(
    range.min + (range.max - range.min) * 0.55,
    clampOpacity(0.08 * baseOpacityScale)
  )
  opacity.addPoint(range.max, clampOpacity(0.35 * baseOpacityScale))

  const property = volume.getProperty()
  property.setRGBTransferFunction(0, colorTransfer)
  property.setScalarOpacity(0, opacity)
  property.setScalarOpacityUnitDistance(0, 2.5)
  property.setInterpolationTypeToLinear()
  property.setShade(useShading)
  property.setAmbient(useShading ? 0.2 : 0.55)
  property.setDiffuse(useShading ? 0.85 : 0.35)
  property.setSpecular(useShading ? 0.15 : 0.0)
  property.setSpecularPower(useShading ? 10.0 : 1.0)

  return volume
}

const configureLabelVolume = ({
  imageData,
  overlayOpacity,
  classVisibility,
  classes,
}) => {
  const mapper = vtkVolumeMapper.newInstance()
  mapper.setInputData(imageData)
  mapper.setSampleDistance(0.7)

  const volume = vtkVolume.newInstance()
  volume.setMapper(mapper)

  const colorTransfer = vtkColorTransferFunction.newInstance()
  colorTransfer.addRGBPoint(0, 0.0, 0.0, 0.0)

  const opacity = vtkPiecewiseFunction.newInstance()
  opacity.addPoint(0, 0.0)
  opacity.addPoint(0.5, 0.0)

  classes.forEach((item) => {
    const classId = item.class_id
    const [red, green, blue] = item.color || CLASS_CONFIG[classId]?.color || [255, 255, 255]
    const isVisible = item.present !== false && classVisibility[classId] !== false
    const classOpacity = isVisible ? overlayOpacity : 0

    colorTransfer.addRGBPoint(classId, red / 255, green / 255, blue / 255)
    opacity.addPoint(classId - 0.01, classOpacity)
    opacity.addPoint(classId, classOpacity)
    opacity.addPoint(classId + 0.01, classOpacity)
  })

  opacity.addPoint(4, 0.0)

  const property = volume.getProperty()
  property.setRGBTransferFunction(0, colorTransfer)
  property.setScalarOpacity(0, opacity)
  property.setScalarOpacityUnitDistance(0, 0.8)
  property.setInterpolationTypeToNearest()
  property.setShade(false)

  return volume
}

const buildVisualizationClasses = (result) => {
  const classes = result?.visualization?.classes
  if (Array.isArray(classes) && classes.length > 0) {
    return classes
  }

  return Object.entries(CLASS_CONFIG).map(([classId, config]) => ({
    class_id: Number(classId),
    class_name: config.label,
    color: config.color,
    present: true,
  }))
}

const formatSpacing = (spacing) => {
  if (!Array.isArray(spacing) || spacing.length !== 3) {
    return '1.00 x 1.00 x 1.00 mm'
  }

  return spacing.map((value) => Number(value || 0).toFixed(2)).join(' x ') + ' mm'
}

export const MriVolumeViewer = ({ result, isLoading = false }) => {
  const containerRef = useRef(null)
  const viewerRef = useRef(null)
  const resizeHandlerRef = useRef(null)

  const classes = useMemo(() => buildVisualizationClasses(result), [result])
  const [selectedModality, setSelectedModality] = useState(
    result?.visualization?.default_modality || 't1ce'
  )
  const [overlayOpacity, setOverlayOpacity] = useState(0.55)
  const [baseOpacityScale, setBaseOpacityScale] = useState(1)
  const [shadingEnabled, setShadingEnabled] = useState(true)
  const [activePreset, setActivePreset] = useState('balanced')
  const [classVisibility, setClassVisibility] = useState(() =>
    buildDefaultVisibility(classes)
  )
  const [datasets, setDatasets] = useState(null)
  const [viewerError, setViewerError] = useState(null)
  const [viewerLoading, setViewerLoading] = useState(false)

  useEffect(() => {
    setSelectedModality(result?.visualization?.default_modality || 't1ce')
    setOverlayOpacity(0.55)
    setBaseOpacityScale(1)
    setShadingEnabled(true)
    setActivePreset('balanced')
    setClassVisibility(buildDefaultVisibility(classes))
  }, [classes, result])

  useEffect(() => {
    const caseId = getCaseId(result)
    const visualization = result?.visualization
    if (!caseId || !visualization?.image_url || !visualization?.labels_url) {
      setDatasets(null)
      return undefined
    }

    let isActive = true
    setViewerLoading(true)
    setViewerError(null)

    const loadDatasets = async () => {
      try {
        const [imageBuffer, labelBuffer] = await Promise.all([
          mriSegmentationService.getVisualizationArtifact(caseId, 'image'),
          mriSegmentationService.getVisualizationArtifact(caseId, 'labels'),
        ])

        if (!isActive) return

        const imageDataset = parseNumpyFile(imageBuffer)
        const labelDataset = parseNumpyFile(labelBuffer)
        setDatasets({ imageDataset, labelDataset })
      } catch (error) {
        if (!isActive) return
        console.error('Failed to load MRI visualization artifacts:', error)
        setViewerError(error.message || 'Failed to load MRI visualization artifacts.')
        setDatasets(null)
      } finally {
        if (isActive) {
          setViewerLoading(false)
        }
      }
    }

    loadDatasets()

    return () => {
      isActive = false
    }
  }, [result])

  useEffect(() => {
    if (!containerRef.current || !datasets || isLoading) {
      return undefined
    }

    let isDisposed = false
    setViewerError(null)
    const containerElement = containerRef.current

    const visualization = result?.visualization || {}
    const spacing = getSpacingXYZ(visualization.spacing_mm)

    try {
      const labelDimensions = getDimensionsXYZ(datasets.labelDataset.shape)
      const baseScalars = getChannelScalars(datasets.imageDataset, selectedModality)
      const labelScalars = new Uint8Array(datasets.labelDataset.data)
      const scalarRange = computeScalarRange(baseScalars)

      const baseImage = createImageData({
        scalars: baseScalars,
        label: `${selectedModality}-volume`,
        dimensions: labelDimensions,
        spacing,
      })

      const labelImage = createImageData({
        scalars: labelScalars,
        label: 'label-volume',
        dimensions: labelDimensions,
        spacing,
      })

      const genericRenderWindow = vtkGenericRenderWindow.newInstance({
        background: [0.01, 0.03, 0.07],
      })
      genericRenderWindow.setContainer(containerElement)
      genericRenderWindow.resize()

      const renderer = genericRenderWindow.getRenderer()
      const renderWindow = genericRenderWindow.getRenderWindow()
      renderer.removeAllVolumes()

      const baseVolume = configureBaseVolume({
        imageData: baseImage,
        range: scalarRange,
        baseOpacityScale,
        useShading: shadingEnabled,
      })
      const labelVolume = configureLabelVolume({
        imageData: labelImage,
        overlayOpacity,
        classVisibility,
        classes,
      })

      renderer.addVolume(baseVolume)
      renderer.addVolume(labelVolume)
      renderer.resetCamera()
      renderWindow.render()

      const handleResize = () => {
        if (isDisposed) return
        genericRenderWindow.resize()
        renderWindow.render()
      }

      resizeHandlerRef.current = handleResize
      window.addEventListener('resize', handleResize)

      viewerRef.current = {
        genericRenderWindow,
        renderWindow,
        renderer,
      }
    } catch (error) {
      console.error('Failed to initialize MRI volume viewer:', error)
      setViewerError(error.message || 'Failed to initialize MRI volume viewer.')
    }

    return () => {
      isDisposed = true
      if (resizeHandlerRef.current) {
        window.removeEventListener('resize', resizeHandlerRef.current)
        resizeHandlerRef.current = null
      }

      if (viewerRef.current?.renderer) {
        viewerRef.current.renderer.removeAllVolumes()
      }

      if (viewerRef.current?.genericRenderWindow) {
        viewerRef.current.genericRenderWindow.delete()
      }

      viewerRef.current = null
      if (containerElement) {
        containerElement.innerHTML = ''
      }
    }
  }, [
    baseOpacityScale,
    classVisibility,
    classes,
    datasets,
    isLoading,
    overlayOpacity,
    result,
    selectedModality,
    shadingEnabled,
  ])

  const resetCamera = () => {
    const renderer = viewerRef.current?.renderer
    const renderWindow = viewerRef.current?.renderWindow
    if (!renderer || !renderWindow) return

    renderer.resetCamera()
    renderWindow.render()
  }

  const handleToggleClass = (classId) => {
    setActivePreset('balanced')
    setClassVisibility((current) => ({
      ...current,
      [classId]: !current[classId],
    }))
  }

  const handleShowAllClasses = () => {
    setActivePreset('balanced')
    setClassVisibility(
      classes.reduce(
        (accumulator, item) => ({
          ...accumulator,
          [item.class_id]: true,
        }),
        {}
      )
    )
  }

  const handleHideAllClasses = () => {
    setActivePreset('balanced')
    setClassVisibility(
      classes.reduce(
        (accumulator, item) => ({
          ...accumulator,
          [item.class_id]: false,
        }),
        {}
      )
    )
  }

  const applyPreset = (presetKey) => {
    const defaultVisibility = buildDefaultVisibility(classes)
    setActivePreset(presetKey)

    if (presetKey === 'tumorFocus') {
      setOverlayOpacity(0.8)
      setBaseOpacityScale(0.45)
      setShadingEnabled(true)
      setClassVisibility({
        ...defaultVisibility,
        2: false,
      })
      return
    }

    if (presetKey === 'edemaFocus') {
      setOverlayOpacity(0.85)
      setBaseOpacityScale(0.5)
      setShadingEnabled(false)
      setClassVisibility({
        ...defaultVisibility,
        1: false,
        3: false,
      })
      return
    }

    if (presetKey === 'anatomy') {
      setOverlayOpacity(0.25)
      setBaseOpacityScale(1.15)
      setShadingEnabled(true)
      setClassVisibility(defaultVisibility)
      return
    }

    setOverlayOpacity(0.55)
    setBaseOpacityScale(1)
    setShadingEnabled(true)
    setClassVisibility(defaultVisibility)
  }

  const availableModalities =
    result?.visualization?.modalities?.filter((item) => MODALITY_ORDER.includes(item)) ||
    MODALITY_ORDER

  const visibleClasses = classes.filter(
    (item) => item.present !== false && classVisibility[item.class_id] !== false
  )

  const metadataItems = [
    {
      label: 'Volume shape',
      value:
        result?.visualization?.label_shape_dhw?.join(' x ') ||
        result?.processingMetadata?.shape_after_resample?.join(' x ') ||
        'Unknown',
    },
    {
      label: 'Voxel spacing',
      value: formatSpacing(result?.visualization?.spacing_mm),
    },
    {
      label: 'Visible classes',
      value: `${visibleClasses.length}/${classes.length}`,
    },
    {
      label: 'Navigation',
      value: 'Drag to rotate, scroll to zoom.',
    },
  ]

  if (isLoading) {
    return (
      <div className={styles.stateContainer}>
        <div className={styles.spinner} />
        <p className={styles.stateText}>Preparing volumetric reconstruction...</p>
      </div>
    )
  }

  if (viewerError) {
    return (
      <div className={styles.stateContainer}>
        <p className={styles.stateText}>{viewerError}</p>
      </div>
    )
  }

  if (!result?.visualization?.image_url || !result?.visualization?.labels_url) {
    return (
      <div className={styles.stateContainer}>
        <p className={styles.stateText}>
          Run segmentation to load the MRI volume and label map.
        </p>
      </div>
    )
  }

  return (
    <div className={styles.viewerShell}>
      <div className={styles.toolbar}>
        <div className={styles.group}>
          <span className={styles.groupLabel}>Modality</span>
          {availableModalities.map((modality) => (
            <button
              key={modality}
              type="button"
              className={`${styles.toggleButton} ${
                selectedModality === modality ? styles.toggleButtonActive : ''
              }`}
              onClick={() => setSelectedModality(modality)}
            >
              {MODALITY_LABELS[modality] || modality.toUpperCase()}
            </button>
          ))}
        </div>

        <button type="button" className={styles.resetButton} onClick={resetCamera}>
          Reset Camera
        </button>
      </div>

      <div className={styles.viewportFrame}>
        {viewerLoading && (
          <div className={styles.loadingOverlay}>
            <div className={styles.spinner} />
            <span>Loading MRI artifacts...</span>
          </div>
        )}
        <div ref={containerRef} className={styles.viewport} />
      </div>

      <div className={styles.controls}>
        <div className={styles.controlCard}>
          <div className={styles.controlHeader}>
            <span className={styles.groupLabel}>Viewer Presets</span>
            <p className={styles.helpText}>
              Choose a preset to quickly emphasize anatomy, tumor core, or edema.
            </p>
          </div>
          <div className={styles.presetGrid}>
            {Object.entries(VISUAL_PRESETS).map(([presetKey, preset]) => (
              <button
                key={presetKey}
                type="button"
                className={`${styles.presetButton} ${
                  activePreset === presetKey ? styles.presetButtonActive : ''
                }`}
                onClick={() => applyPreset(presetKey)}
              >
                <span>{preset.label}</span>
                <small>{preset.description}</small>
              </button>
            ))}
          </div>
        </div>

        <div className={styles.controlCard}>
          <div className={styles.controlHeader}>
            <span className={styles.groupLabel}>Segmentation Classes</span>
            <div className={styles.inlineActions}>
              <button type="button" className={styles.textButton} onClick={handleShowAllClasses}>
                Show All
              </button>
              <button type="button" className={styles.textButton} onClick={handleHideAllClasses}>
                Hide All
              </button>
            </div>
          </div>
          <div className={styles.classList}>
            {classes.map((item) => {
              const classId = item.class_id
              const color = item.color || CLASS_CONFIG[classId]?.color || [255, 255, 255]
              return (
                <label
                  key={classId}
                  className={`${styles.classItem} ${
                    item.present === false ? styles.classItemDisabled : ''
                  }`}
                >
                  <input
                    type="checkbox"
                    checked={classVisibility[classId] !== false}
                    disabled={item.present === false}
                    onChange={() => handleToggleClass(classId)}
                  />
                  <span
                    className={styles.colorDot}
                    style={{
                      backgroundColor: `rgb(${color[0]}, ${color[1]}, ${color[2]})`,
                    }}
                  />
                  <span className={styles.classText}>
                    <strong>{item.class_name || CLASS_CONFIG[classId]?.label}</strong>
                    <small>
                      {item.present === false ? 'Not present in this case' : 'Visible in overlay'}
                    </small>
                  </span>
                </label>
              )
            })}
          </div>
        </div>

        <div className={styles.controlCard}>
          <div className={styles.controlHeader}>
            <span className={styles.groupLabel}>Rendering Controls</span>
            <p className={styles.helpText}>
              Tune how strongly the anatomy volume and colored labels appear.
            </p>
          </div>

          <div className={styles.sliderStack}>
            <label className={styles.sliderGroup} htmlFor="overlay-opacity">
              <span>
                <strong>Overlay opacity</strong>
                <small>Controls how intense the tumor mask appears.</small>
              </span>
              <div className={styles.sliderRow}>
                <input
                  id="overlay-opacity"
                  type="range"
                  min="0"
                  max="100"
                  value={Math.round(overlayOpacity * 100)}
                  onChange={(event) => {
                    setActivePreset('balanced')
                    setOverlayOpacity(Number(event.target.value) / 100)
                  }}
                />
                <span>{Math.round(overlayOpacity * 100)}%</span>
              </div>
            </label>

            <label className={styles.sliderGroup} htmlFor="anatomy-opacity">
              <span>
                <strong>Anatomy opacity</strong>
                <small>Controls the visibility of the MRI volume itself.</small>
              </span>
              <div className={styles.sliderRow}>
                <input
                  id="anatomy-opacity"
                  type="range"
                  min="20"
                  max="150"
                  value={Math.round(baseOpacityScale * 100)}
                  onChange={(event) => {
                    setActivePreset('balanced')
                    setBaseOpacityScale(Number(event.target.value) / 100)
                  }}
                />
                <span>{Math.round(baseOpacityScale * 100)}%</span>
              </div>
            </label>
          </div>

          <label className={styles.switchRow}>
            <span className={styles.classText}>
              <strong>Cinematic lighting</strong>
              <small>Enable shading for more depth cues and contour definition.</small>
            </span>
            <input
              type="checkbox"
              checked={shadingEnabled}
              onChange={(event) => {
                setActivePreset('balanced')
                setShadingEnabled(event.target.checked)
              }}
            />
          </label>
        </div>
      </div>

      <div className={styles.metadataGrid}>
        {metadataItems.map((item) => (
          <div key={item.label} className={styles.metadataCard}>
            <span>{item.label}</span>
            <strong>{item.value}</strong>
          </div>
        ))}
      </div>
    </div>
  )
}

export default MriVolumeViewer
