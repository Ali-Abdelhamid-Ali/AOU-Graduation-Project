import { render, screen } from '@testing-library/react'
import { beforeEach, describe, expect, it, vi } from 'vitest'
import { MemoryRouter, Route, Routes } from 'react-router-dom'

import { ProtectedRoute } from './ProtectedRoute'

const authState = {
  isAuthenticated: false,
  userRole: null,
  isLoading: false,
  mustResetPassword: false,
}

vi.mock('@/store/AuthContext', () => ({
  useAuth: () => authState,
}))

describe('ProtectedRoute', () => {
  beforeEach(() => {
    authState.isAuthenticated = false
    authState.userRole = null
    authState.isLoading = false
    authState.mustResetPassword = false
  })

  it('redirects unauthenticated users to the login page', () => {
    render(
      <MemoryRouter initialEntries={['/patient-dashboard']}>
        <Routes>
          <Route path="/login" element={<div>Login Screen</div>} />
          <Route
            path="/patient-dashboard"
            element={
              <ProtectedRoute>
                <div>Protected Content</div>
              </ProtectedRoute>
            }
          />
        </Routes>
      </MemoryRouter>
    )

    expect(screen.getByText('Login Screen')).toBeInTheDocument()
    expect(screen.queryByText('Protected Content')).not.toBeInTheDocument()
  })
})
