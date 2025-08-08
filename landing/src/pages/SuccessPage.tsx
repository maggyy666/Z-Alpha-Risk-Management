import React, { useEffect, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import './SuccessPage.css';

const SuccessPage: React.FC = () => {
  const navigate = useNavigate();
  const [countdown, setCountdown] = useState(5);

  useEffect(() => {
    const timer = setInterval(() => {
      setCountdown(prev => {
        if (prev <= 1) {
          // Redirect to main app
          window.location.href = 'http://localhost:3000/introduction';
          return 0;
        }
        return prev - 1;
      });
    }, 1000);

    return () => clearInterval(timer);
  }, []);

  const handleRedirectNow = () => {
    window.location.href = 'http://localhost:3000/introduction';
  };

  return (
    <div className="success-page">
      <div className="success-container">
        <div className="success-content">
          <div className="success-icon">
            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
              <path d="M20 6L9 17l-5-5" />
            </svg>
          </div>
          
          <h1>Welcome to Z-Alpha Securities!</h1>
          <p className="success-message">
            You have successfully signed in. You will be redirected to your risk management dashboard in {countdown} seconds.
          </p>
          
          <div className="success-actions">
            <button className="btn-primary" onClick={handleRedirectNow}>
              Go to Dashboard Now
            </button>
            <button className="btn-secondary" onClick={() => navigate('/')}>
              Back to Landing
            </button>
          </div>

          <div className="loading-indicator">
            <div className="spinner"></div>
            <p>Preparing your dashboard...</p>
          </div>
        </div>
      </div>
    </div>
  );
};

export default SuccessPage;
