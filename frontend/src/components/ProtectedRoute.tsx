import React from 'react';
import { Navigate } from 'react-router-dom';
import { useSession } from '../contexts/SessionContext';

interface ProtectedRouteProps {
  children: React.ReactNode;
}

const ProtectedRoute: React.FC<ProtectedRouteProps> = ({ children }) => {
  const { session, loading } = useSession();

  console.log('ProtectedRoute - session:', session, 'loading:', loading);

  // Show loading while checking session
  if (loading) {
    return (
      <div style={{
        display: 'flex',
        justifyContent: 'center',
        alignItems: 'center',
        height: '100vh',
        backgroundColor: '#0a0a0a',
        color: '#ffffff'
      }}>
        <div>Loading...</div>
      </div>
    );
  }

  // Redirect to login if no session
  if (!session || !session.logged_in) {
    console.log('No session found, redirecting to login');
    window.location.href = 'http://localhost:3001';
    return null;
  }

  console.log('Session found, rendering children');

  // Render children if authenticated
  return <>{children}</>;
};

export default ProtectedRoute;
