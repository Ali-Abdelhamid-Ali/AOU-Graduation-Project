import { useEffect } from 'react'

// Simple draggable hook with localStorage persistence.
// Usage: const ref = useRef(); useDraggable(ref, 'unique-key')
export default function useDraggable(ref, storageKey) {
  useEffect(() => {
    const el = ref?.current
    if (!el || !storageKey) return

    const storageName = `layout_pos_${storageKey}`

    // Restore saved position
    try {
      const raw = localStorage.getItem(storageName)
      if (raw) {
        const { x, y } = JSON.parse(raw)
        el.style.transform = `translate(${x}px, ${y}px)`
        el.dataset._dx = x
        el.dataset._dy = y
      }
    } catch (e) {
      // ignore
    }

    let dragging = false
    let startX = 0
    let startY = 0
    let origX = 0
    let origY = 0

    const isLayoutMode = () => localStorage.getItem('layout_mode') === 'true'

    const onPointerDown = (ev) => {
      if (!isLayoutMode()) return
      ev.preventDefault()
      dragging = true
      const point = ev.touches ? ev.touches[0] : ev
      startX = point.clientX
      startY = point.clientY
      origX = parseFloat(el.dataset._dx || 0)
      origY = parseFloat(el.dataset._dy || 0)
      document.addEventListener('pointermove', onPointerMove)
      document.addEventListener('pointerup', onPointerUp)
      document.addEventListener('touchmove', onPointerMove, { passive: false })
      document.addEventListener('touchend', onPointerUp)
      el.style.transition = 'transform 0s'
      el.style.zIndex = 9999
    }

    const onPointerMove = (ev) => {
      if (!dragging) return
      ev.preventDefault()
      const point = ev.touches ? ev.touches[0] : ev
      const dx = point.clientX - startX
      const dy = point.clientY - startY
      const nx = origX + dx
      const ny = origY + dy
      el.style.transform = `translate(${nx}px, ${ny}px)`
      el.dataset._dx = nx
      el.dataset._dy = ny
    }

    const onPointerUp = () => {
      if (!dragging) return
      dragging = false
      document.removeEventListener('pointermove', onPointerMove)
      document.removeEventListener('pointerup', onPointerUp)
      document.removeEventListener('touchmove', onPointerMove)
      document.removeEventListener('touchend', onPointerUp)
      el.style.transition = 'transform 160ms ease'
      el.style.zIndex = ''
      // Persist
      try {
        const x = parseFloat(el.dataset._dx || 0)
        const y = parseFloat(el.dataset._dy || 0)
        localStorage.setItem(storageName, JSON.stringify({ x, y }))
      } catch (e) {
        // ignore
      }
    }

    el.addEventListener('pointerdown', onPointerDown)
    el.addEventListener('touchstart', onPointerDown, { passive: false })

    // Clean up
    return () => {
      el.removeEventListener('pointerdown', onPointerDown)
      el.removeEventListener('touchstart', onPointerDown)
      document.removeEventListener('pointermove', onPointerMove)
      document.removeEventListener('pointerup', onPointerUp)
      document.removeEventListener('touchmove', onPointerMove)
      document.removeEventListener('touchend', onPointerUp)
    }
  }, [ref, storageKey])
}
