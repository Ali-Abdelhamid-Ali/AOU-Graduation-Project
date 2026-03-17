import { Navigate, useLocation } from 'react-router-dom';
import { useAuth } from '@/store/AuthContext';
import { getDashboardHomeRoute } from '@/utils/dashboardRoutes';

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
        return <Navigate to="/login" state={{ from: location }} replace />;
    }

    if (mustResetPassword && location.pathname !== '/force-password-reset') {
        return <Navigate to="/force-password-reset" replace />;
    }

    if (allowedRoles.length > 0 && !allowedRoles.includes(userRole)) {
        // Prevent Infinite Redirect Loop:
        // Only navigate if the target fallback path is different from the current path.
        const fallbackPath = getDashboardHomeRoute(userRole);

        if (location.pathname !== fallbackPath) {
            return <Navigate to={fallbackPath} replace />;
        } else {
            return <Navigate to="/" replace />;
        }
    }

    return children;
};
