import { createContext, useContext, useState, useCallback, useEffect } from 'react'
import { Toast } from '../components/Toast'

const ToastContext = createContext()

export const useToast = () => {
  const context = useContext(ToastContext)
  if (!context) {
    throw new Error('useToast must be used within ToastProvider')
  }
  return context
}

export const ToastProvider = ({ children }) => {
  const [toast, setToast] = useState({
    message: '',
    type: 'success',
    isVisible: false,
  })

  const showToast = useCallback((message, type = 'success') => {
    setToast({
      message,
      type,
      isVisible: true,
    })
  }, [])

  const hideToast = useCallback(() => {
    setToast((prev) => ({
      ...prev,
      isVisible: false,
    }))
  }, [])

  // Inject toast function to AuthContext
  useEffect(() => {
    if (typeof window !== 'undefined' && window.__setAuthToast) {
      window.__setAuthToast(showToast)
    }
  }, [showToast])

  return (
    <ToastContext.Provider value={{ showToast, hideToast }}>
      {children}
      <Toast
        message={toast.message}
        type={toast.type}
        isVisible={toast.isVisible}
        onClose={hideToast}
      />
    </ToastContext.Provider>
  )
}

