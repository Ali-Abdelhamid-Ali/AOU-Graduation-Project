import { Component, Suspense, useMemo, useEffect, useRef } from 'react'
import { Canvas, useThree } from '@react-three/fiber'
import { Html, OrbitControls, useGLTF } from '@react-three/drei'
import { Box3, Vector3 } from 'three'
import styles from './Medical3DViewer.module.css'

const MODEL_PATHS = {
  brain: `${import.meta.env.BASE_URL}models/brain/brain.glb`,
  heart: `${import.meta.env.BASE_URL}models/heart/heart.glb`,
}

const MODEL_CONFIG = {
  brain: {
    label: 'Brain MRI Model',
    rotation: [0.12, 0.28, 0],
  },
  heart: {
    label: 'Cardiac 3D Model',
    rotation: [0.3, -0.5, 0],
  },
}

class ViewerErrorBoundary extends Component {
  constructor(props) {
    super(props)
    this.state = { hasError: false }
  }

  static getDerivedStateFromError() {
    return { hasError: true }
  }

  componentDidCatch(error) {
    console.error('ProjectInfoModelViewer failed to render:', error)
  }

  render() {
    if (this.state.hasError) {
      return (
        <div className={styles.loadingContainer}>
          <p className={styles.loadingText}>The 3D model could not be loaded.</p>
        </div>
      )
    }

    return this.props.children
  }
}

// Computes world-space bounding box of all meshes, centres the scene on it,
// then fits the camera so the model fills the view — no Bounds component needed.
const AutoFitModel = ({ type }) => {
  const modelType = MODEL_PATHS[type] ? type : 'brain'
  const { scene } = useGLTF(MODEL_PATHS[modelType])
  const config = MODEL_CONFIG[modelType]
  const { camera } = useThree()
  const groupRef = useRef()

  const clonedScene = useMemo(() => {
    const nextScene = scene.clone()
    nextScene.traverse((node) => {
      if (!node.isMesh || !node.material) return
      const mats = Array.isArray(node.material) ? node.material : [node.material]
      mats.forEach((m) => { m.needsUpdate = true })
    })
    return nextScene
  }, [scene])

  useEffect(() => {
    if (!groupRef.current) return

    // compute true world-space bounding box after mount
    groupRef.current.updateMatrixWorld(true)
    const box = new Box3().setFromObject(groupRef.current)
    const center = new Vector3()
    const size = new Vector3()
    box.getCenter(center)
    box.getSize(size)

    // reposition group so its centre is at origin
    groupRef.current.position.sub(center)

    // fit camera: move back far enough that the whole model is visible
    const maxDim = Math.max(size.x, size.y, size.z)
    const fovRad = (camera.fov * Math.PI) / 180
    const dist = (maxDim / 2 / Math.tan(fovRad / 2)) * 1.25
    camera.position.set(0, 0, dist)
    camera.near = dist * 0.01
    camera.far = dist * 10
    camera.updateProjectionMatrix()
  }, [clonedScene, camera])

  return (
    <group ref={groupRef} rotation={config.rotation}>
      <primitive object={clonedScene} />
    </group>
  )
}

const CanvasLoader = () => (
  <Html center>
    <div className={styles.loaderPill}>Loading 3D model...</div>
  </Html>
)

const LIGHTING = {
  // Heart: warm neutral — let the model's own red/muscle textures show
  heart: {
    ambient:    { intensity: 0.75, color: '#ffffff' },
    hemisphere: { sky: '#ffe8e8', ground: '#1a0404', intensity: 0.55 },
    key:        { position: [4, 7, 5],    intensity: 1.9, color: '#ffffff' },
    fill:       { position: [-5, 2, 4],   intensity: 0.85, color: '#ffe0e0' },
    rim:        { position: [0, -3, -4],  intensity: 0.5,  color: '#ff3333' },
    back:       { position: [0, 6, -4],   intensity: 0.3,  color: '#ffcccc' },
  },
  // Brain: pinkish-grey flesh tone with blood-vessel red rim
  brain: {
    ambient:    { intensity: 0.55, color: '#ffe4d6' },
    hemisphere: { sky: '#ffcdb8', ground: '#1a0808', intensity: 0.5 },
    key:        { position: [4, 7, 5],    intensity: 1.8, color: '#fff0e8' },
    fill:       { position: [-5, 2, 4],   intensity: 0.9, color: '#ffd6c0' },
    rim:        { position: [-1, -2, -5], intensity: 0.9, color: '#cc2200' },  // blood-red rim
    back:       { position: [2, 5, -4],   intensity: 0.5, color: '#ff8866' },  // warm back glow
  },
}

export const ProjectInfoModelViewer = ({ type = 'brain' }) => {
  const modelType = MODEL_PATHS[type] ? type : 'brain'
  const lt = LIGHTING[modelType]

  return (
    <div className={styles.viewerContainer}>
      <ViewerErrorBoundary>
        <Canvas
          className={styles.canvas}
          camera={{ position: [0, 0, 3.8], fov: 40 }}
          dpr={[1, 1.8]}
          gl={{ antialias: true, alpha: true }}
        >
          {/* transparent background — lets CSS glow show through */}
          <ambientLight intensity={lt.ambient.intensity} color={lt.ambient.color} />
          <hemisphereLight args={[lt.hemisphere.sky, lt.hemisphere.ground, lt.hemisphere.intensity]} />
          <directionalLight position={lt.key.position}  intensity={lt.key.intensity}  color={lt.key.color}  castShadow />
          <directionalLight position={lt.fill.position} intensity={lt.fill.intensity} color={lt.fill.color} />
          <directionalLight position={lt.rim.position}  intensity={lt.rim.intensity}  color={lt.rim.color} />
          <directionalLight position={lt.back.position} intensity={lt.back.intensity} color={lt.back.color} />

          <Suspense fallback={<CanvasLoader />}>
            <AutoFitModel type={modelType} />
          </Suspense>

          <OrbitControls
            autoRotate
            autoRotateSpeed={modelType === 'heart' ? 1.4 : 0.7}
            enablePan={false}
            enableZoom={false}
            minPolarAngle={Math.PI / 2.8}
            maxPolarAngle={Math.PI / 1.6}
          />
        </Canvas>
      </ViewerErrorBoundary>

      <div className={styles.overlay}>
        <span className={styles.badge}>{MODEL_CONFIG[modelType].label}</span>
      </div>
    </div>
  )
}

useGLTF.preload(MODEL_PATHS.brain)
useGLTF.preload(MODEL_PATHS.heart)


export default ProjectInfoModelViewer
