import React, { useState, useEffect, useRef, Suspense } from 'react'
import { Canvas, useFrame, useLoader } from '@react-three/fiber'
import { GLTFLoader } from 'three/examples/jsm/loaders/GLTFLoader'

/**
 * useInView Hook
 * Utility to detect when an element enters the viewport.
 */
const useInView = (options) => {
  const [isInView, setIsInView] = useState(false)
  const ref = useRef(null)

  useEffect(() => {
    const observer = new IntersectionObserver(([entry]) => {
      if (entry.isIntersecting) {
        setIsInView(true)
        observer.unobserve(entry.target) // Load once
      }
    }, options)

    if (ref.current) {
      observer.observe(ref.current)
    }

    return () => {
      if (ref.current) {
        observer.unobserve(ref.current)
      }
    }
  }, [options])

  return [ref, isInView]
}

const ModelPlaceholder = () => (
  <div style={{
    width: '100%',
    height: '100%',
    display: 'flex',
    alignItems: 'center',
    justifyContent: 'center',
    background: 'rgba(0,0,0,0.05)',
    borderRadius: '20px',
    color: 'var(--color-primary-light)',
    fontSize: '0.8rem',
    letterSpacing: '2px'
  }}>
    SYNCHRONIZING_VOLUMETRIC_DATA...
  </div>
)

const HeartModel = () => {
  return (
    <div style={{ width: '100%', height: '100%', borderRadius: '20px', overflow: 'hidden', position: 'relative' }}>
      <iframe
        title="3D Animated Realistic Human Heart"
        frameBorder="0"
        allowFullScreen
        allow="autoplay; fullscreen; xr-spatial-tracking"
        style={{ width: '100%', height: '110%', marginTop: '-5%', border: 'none' }}
        // Hardened production parameters: Zero UI, forced transparency, no inspector
        src="https://sketchfab.com/models/168b474fba564f688048212e99b4159d/embed?autostart=1&ui_controls=0&ui_infos=0&ui_inspector=0&ui_stop=0&ui_watermark=0&transparent=1&ui_animations=0&ui_hint=0&ui_help=0&ui_settings=0&ui_vr=0&ui_fullscreen=0&ui_ar=0&dnt=1"
      />
    </div>
  )
}

const BrainModel = () => {
  return (
    <div style={{ width: '100%', height: '100%', borderRadius: '20px', overflow: 'hidden', position: 'relative' }}>
      <iframe
        title="3D Animated Realistic Human Brain"
        frameBorder="0"
        allowFullScreen
        allow="autoplay; fullscreen; xr-spatial-tracking"
        style={{ width: '100%', height: '110%', marginTop: '-5%', border: 'none' }}
        // Production parameters optimized for clarity and reduced noise
        src="https://sketchfab.com/models/2df234faaddc44428751b3834e40259e/embed?autostart=1&ui_controls=0&ui_infos=0&ui_inspector=0&ui_stop=0&ui_watermark=0&transparent=1&ui_animations=0&ui_hint=0&ui_help=0&ui_settings=0&ui_vr=0&ui_fullscreen=0&ui_ar=0&dnt=1"
      />
    </div>
  )
}

/**
 * Hybrid 3D Viewer Component
 * Implements Intersection Observer to prevent blocking FCP.
 */
export const Medical3DViewer = ({ type = 'heart' }) => {
  const [containerRef, isInView] = useInView({ threshold: 0.1 })

  return (
    <div ref={containerRef} style={{ width: '100%', height: '100%' }}>
      {isInView ? (
        <Suspense fallback={<ModelPlaceholder />}>
          {type === 'heart' ? <HeartModel /> : <BrainModel />}
        </Suspense>
      ) : (
        <ModelPlaceholder />
      )}
    </div>
  )
}
