import { Component, Suspense, useMemo } from 'react'
import { Canvas } from '@react-three/fiber'
import { Bounds, Html, OrbitControls, useGLTF } from '@react-three/drei'
import { Box3, Vector3 } from 'three'
import styles from './Medical3DViewer.module.css'

const MODEL_PATHS = {
  brain: `${import.meta.env.BASE_URL}models/brain/brain.glb`,
  heart: `${import.meta.env.BASE_URL}models/heart/heart.gltf`
}

const MODEL_CONFIG = {
  brain: {
    label: 'Brain MRI Model',
    rotation: [0.12, 0.28, 0],
    scale: 1.02,
    offset: [0, -0.02, 0]
  },
  heart: {
    label: 'Cardiac 3D Model',
    rotation: [0.3, -0.5, 0],
    scale: 1.14,
    offset: [0.04, -0.025, 0]
  }
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
    console.error('Medical3DViewer failed to render:', error)
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

const ModelAsset = ({ type }) => {
  const modelType = MODEL_PATHS[type] ? type : 'brain'
  const { scene } = useGLTF(MODEL_PATHS[modelType])
  const config = MODEL_CONFIG[modelType]
  const clonedScene = useMemo(() => {
    const nextScene = scene.clone()

    // Keep asset materials intact, while ensuring maps render as-authored.
    nextScene.traverse((node) => {
      if (!node.isMesh || !node.material) return

      const materials = Array.isArray(node.material) ? node.material : [node.material]
      materials.forEach((material) => {
        material.needsUpdate = true
      })
    })

    // Center on visible mesh bounds instead of the scene root.
    nextScene.updateMatrixWorld(true)
    const combinedBounds = new Box3()
    const meshBounds = new Box3()
    const meshCenter = new Vector3()
    let hasMeshBounds = false

    nextScene.traverse((node) => {
      if (!node.isMesh || !node.geometry) return

      if (!node.geometry.boundingBox) {
        node.geometry.computeBoundingBox()
      }

      meshBounds.copy(node.geometry.boundingBox).applyMatrix4(node.matrixWorld)
      if (!hasMeshBounds) {
        combinedBounds.copy(meshBounds)
        hasMeshBounds = true
        return
      }

      combinedBounds.union(meshBounds)
    })

    if (hasMeshBounds) {
      combinedBounds.getCenter(meshCenter)
      nextScene.position.sub(meshCenter)
    }

    return nextScene
  }, [scene])

  return (
    <group position={config.offset}>
      <group rotation={config.rotation} scale={config.scale}>
        <primitive object={clonedScene} />
      </group>
    </group>
  )
}

const CanvasLoader = () => (
  <Html center>
    <div className={styles.loaderPill}>Loading 3D model...</div>
  </Html>
)

export const Medical3DViewer = ({ result, isLoading = false, type = 'brain' }) => {
  const modelType = MODEL_PATHS[type] ? type : 'brain'
  const badgeLabel = result?.severity?.label || MODEL_CONFIG[modelType].label

  if (isLoading) {
    return (
      <div className={styles.loadingContainer}>
        <div className={styles.spinner} />
        <p className={styles.loadingText}>Preparing 3D reconstruction...</p>
      </div>
    )
  }

  return (
    <div className={styles.viewerContainer}>
      <ViewerErrorBoundary>
        <Canvas
          className={styles.canvas}
          camera={{ position: [0, 0, 4.5], fov: 35 }}
          dpr={[1, 1.8]}
          gl={{ antialias: true, alpha: true }}
        >
          <color attach="background" args={['#04070b']} />
          <ambientLight intensity={1.05} color="#ffffff" />
          <hemisphereLight args={['#ffffff', '#4b5563', 0.8]} />
          <directionalLight position={[4, 6, 5]} intensity={1.7} color="#ffffff" />
          <directionalLight position={[-4, -2, -3]} intensity={0.6} color="#ffffff" />

          <Suspense fallback={<CanvasLoader />}>
            <Bounds fit clip observe margin={1.45}>
              <ModelAsset type={modelType} />
            </Bounds>
          </Suspense>

          <OrbitControls
            autoRotate
            autoRotateSpeed={modelType === 'heart' ? 1.6 : 0.9}
            enablePan={false}
            enableZoom={false}
            minPolarAngle={Math.PI / 2.6}
            maxPolarAngle={Math.PI / 1.7}
          />
        </Canvas>
      </ViewerErrorBoundary>

      <div className={styles.overlay}>
        <span className={styles.badge}>{badgeLabel}</span>
      </div>
    </div>
  )
}

useGLTF.preload(MODEL_PATHS.brain)
useGLTF.preload(MODEL_PATHS.heart)

export default Medical3DViewer
