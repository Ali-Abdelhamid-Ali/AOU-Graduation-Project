/**
 * Custom Animation Hooks
 * 
 * Reusable React hooks for animations with Anime.js and Framer Motion
 */

import { useEffect, useRef } from 'react'
import anime from 'animejs'

/**
 * Hook to trigger Anime.js animation on mount
 */
export const useAnimeOnMount = (animationConfig = {}) => {
  const elementRef = useRef(null)

  useEffect(() => {
    if (elementRef.current) {
      anime({
        targets: elementRef.current,
        ...animationConfig,
        duration: animationConfig.duration || 800,
        easing: animationConfig.easing || 'easeInOutQuad'
      })
    }
  }, [animationConfig])

  return elementRef
}

/**
 * Hook to trigger animation on element appearance
 */
export const useAnimeOnScroll = (animationConfig = {}) => {
  const elementRef = useRef(null)

  useEffect(() => {
    const observer = new IntersectionObserver(([entry]) => {
      if (entry.isIntersecting) {
        anime({
          targets: elementRef.current,
          ...animationConfig,
          duration: animationConfig.duration || 800,
          easing: animationConfig.easing || 'easeOutCubic'
        })
        observer.unobserve(entry.target)
      }
    })

    if (elementRef.current) {
      observer.observe(elementRef.current)
    }

    return () => observer.disconnect()
  }, [animationConfig])

  return elementRef
}

/**
 * Hook for stagger animations on list items
 */
export const useStaggerAnimation = (items = [], animationConfig = {}) => {
  const containerRef = useRef(null)

  useEffect(() => {
    if (containerRef.current && items.length > 0) {
      const children = containerRef.current.children

      anime({
        targets: children,
        opacity: [0, 1],
        translateY: [20, 0],
        duration: animationConfig.duration || 500,
        delay: anime.stagger(animationConfig.staggerDelay || 100),
        easing: animationConfig.easing || 'easeOutCubic'
      })
    }
  }, [items, animationConfig])

  return containerRef
}

/**
 * Hook for fade in/out animations
 */
export const useFadeAnimation = (trigger = true) => {
  const elementRef = useRef(null)

  useEffect(() => {
    if (elementRef.current) {
      anime({
        targets: elementRef.current,
        opacity: trigger ? 1 : 0,
        duration: 600,
        easing: 'easeInOutQuad'
      })
    }
  }, [trigger])

  return elementRef
}

/**
 * Hook for slide in animations
 */
export const useSlideInAnimation = (trigger = true, direction = 'up') => {
  const elementRef = useRef(null)

  useEffect(() => {
    if (elementRef.current) {
      const translateConfig = {
        up: { translateY: [40, 0] },
        down: { translateY: [-40, 0] },
        left: { translateX: [40, 0] },
        right: { translateX: [-40, 0] }
      }

      anime({
        targets: elementRef.current,
        opacity: trigger ? [0, 1] : [1, 0],
        ...translateConfig[direction],
        duration: 700,
        easing: 'easeOutCubic'
      })
    }
  }, [trigger, direction])

  return elementRef
}

export default {
  useAnimeOnMount,
  useAnimeOnScroll,
  useStaggerAnimation,
  useFadeAnimation,
  useSlideInAnimation
}
