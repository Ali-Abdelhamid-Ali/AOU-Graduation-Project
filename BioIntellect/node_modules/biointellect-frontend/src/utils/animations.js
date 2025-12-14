/**
 * Animation Utilities
 * 
 * Helper functions for Anime.js animations
 * Provides reusable animation effects throughout the app
 */

import anime from 'animejs'

/**
 * Fade In Animation
 */
export const fadeInAnimation = (element, duration = 800, delay = 0) => {
  return anime({
    targets: element,
    opacity: [0, 1],
    duration,
    delay,
    easing: 'easeInOutQuad'
  })
}

/**
 * Fade Out Animation
 */
export const fadeOutAnimation = (element, duration = 600, delay = 0) => {
  return anime({
    targets: element,
    opacity: [1, 0],
    duration,
    delay,
    easing: 'easeInOutQuad'
  })
}

/**
 * Slide In from Bottom
 */
export const slideInUpAnimation = (element, duration = 700, delay = 0) => {
  return anime({
    targets: element,
    opacity: [0, 1],
    translateY: [40, 0],
    duration,
    delay,
    easing: 'easeOutCubic'
  })
}

/**
 * Slide In from Top
 */
export const slideInDownAnimation = (element, duration = 700, delay = 0) => {
  return anime({
    targets: element,
    opacity: [0, 1],
    translateY: [-40, 0],
    duration,
    delay,
    easing: 'easeOutCubic'
  })
}

/**
 * Scale Pop Animation
 */
export const scalePopAnimation = (element, duration = 600, delay = 0) => {
  return anime({
    targets: element,
    opacity: [0, 1],
    scale: [0.8, 1],
    duration,
    delay,
    easing: 'easeOutElastic(1, .6)'
  })
}

/**
 * Rotate Animation
 */
export const rotateAnimation = (element, duration = 1000, delay = 0) => {
  return anime({
    targets: element,
    rotate: 360,
    duration,
    delay,
    easing: 'linear',
    loop: false
  })
}

/**
 * Pulse Animation (for buttons, icons)
 */
export const pulseAnimation = (element, duration = 1000) => {
  return anime({
    targets: element,
    scale: [
      { value: 1, duration: duration / 2, easing: 'easeInOutQuad' },
      { value: 1.05, duration: duration / 2, easing: 'easeInOutQuad' }
    ],
    duration: duration,
    loop: true
  })
}

/**
 * Bounce Animation
 */
export const bounceAnimation = (element, duration = 800, delay = 0) => {
  return anime({
    targets: element,
    translateY: [
      { value: -10, duration: duration / 4, easing: 'easeOutQuad' },
      { value: 0, duration: duration / 4, easing: 'easeInQuad' }
    ],
    duration: duration,
    delay,
    loop: false
  })
}

/**
 * Shake Animation (for errors)
 */
export const shakeAnimation = (element, duration = 600, delay = 0) => {
  return anime({
    targets: element,
    translateX: [
      { value: -5, duration: 100 },
      { value: 5, duration: 100 },
      { value: -5, duration: 100 },
      { value: 5, duration: 100 },
      { value: 0, duration: 100 }
    ],
    duration,
    delay,
    easing: 'linear'
  })
}

/**
 * Glow Animation (for success messages)
 */
export const glowAnimation = (element, duration = 2000) => {
  return anime({
    targets: element,
    boxShadow: [
      {
        value: '0 0 0 0 rgba(27, 126, 63, 0.7)',
        duration: duration / 2,
        easing: 'easeInOutQuad'
      },
      {
        value: '0 0 0 20px rgba(27, 126, 63, 0)',
        duration: duration / 2,
        easing: 'easeInOutQuad'
      }
    ],
    loop: true,
    duration
  })
}

/**
 * Stagger Animation (for lists)
 */
export const staggerAnimation = (elements, duration = 500, staggerDelay = 100) => {
  return anime({
    targets: elements,
    opacity: [0, 1],
    translateY: [20, 0],
    duration,
    delay: anime.stagger(staggerDelay),
    easing: 'easeOutCubic'
  })
}

export default {
  fadeInAnimation,
  fadeOutAnimation,
  slideInUpAnimation,
  slideInDownAnimation,
  scalePopAnimation,
  rotateAnimation,
  pulseAnimation,
  bounceAnimation,
  shakeAnimation,
  glowAnimation,
  staggerAnimation
}
