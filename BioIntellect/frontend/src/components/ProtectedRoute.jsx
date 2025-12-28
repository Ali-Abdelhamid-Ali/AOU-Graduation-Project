import { Navigate, useLocation } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';

/**
 * ProtectedRoute Component
 * Enforces authentication and role-based access control (RBAC).
 * 
 * @param {Element} children - The component to render if authorized
 * @param {Array} allowedRoles - Array of roles permitted to access this route
 */
export const ProtectedRoute = ({ children, allowedRoles = [] }) => {
    const { isAuthenticated, userRole, isLoading, mustResetPassword } = useAuth();
    const location = useLocation();

    if (isLoading) {
        return <div className="loading-screen">Authenticating Biosystem...</div>;
    }

    if (!isAuthenticated) {
        // Redirect to home if not authenticated
        return <Navigate to="/" state={{ from: location }} replace />;
    }

    if (mustResetPassword && location.pathname !== '/force-password-reset') {
        return <Navigate to="/force-password-reset" replace />;
    }

    if (allowedRoles.length > 0 && !allowedRoles.includes(userRole)) {
        // Prevent Infinite Redirect Loop:
        // Only navigate if the target fallback path is different from the current path.
        const fallbackPath = userRole === 'patient' ? '/patient-dashboard' : '/admin-dashboard';

        if (location.pathname !== fallbackPath) {
            return <Navigate to={fallbackPath} replace />;
        } else {
            // If we are already on the fallback path but still unauthorized, 
            // fallback further to the home page to break the loop.
            return <Navigate to="/" replace />;
        }
    }

    return children;
};
