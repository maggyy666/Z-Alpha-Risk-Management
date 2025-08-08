import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { apiService } from '../services/api';
import './LoginPage.css';

const LoginPage: React.FC = () => {
  const navigate = useNavigate();
  const [formData, setFormData] = useState({
    email: '',
    password: ''
  });
  const [errors, setErrors] = useState<{[key: string]: string}>({});
  const [isLoading, setIsLoading] = useState(false);

  const handleInputChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const { name, value } = e.target;
    setFormData(prev => ({
      ...prev,
      [name]: value
    }));
    // Clear error when user starts typing
    if (errors[name]) {
      setErrors(prev => ({
        ...prev,
        [name]: ''
      }));
    }
  };

  const validateForm = () => {
    const newErrors: {[key: string]: string} = {};

    if (!formData.email) {
      newErrors.email = 'Email is required';
    } else if (!/\S+@\S+\.\S+/.test(formData.email)) {
      newErrors.email = 'Email is invalid';
    }

    if (!formData.password) {
      newErrors.password = 'Password is required';
    } else if (formData.password.length < 6) {
      newErrors.password = 'Password must be at least 6 characters';
    }

    setErrors(newErrors);
    return Object.keys(newErrors).length === 0;
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    
    if (!validateForm()) {
      return;
    }

    setIsLoading(true);
    
    try {
      const response = await apiService.login({
        username: formData.email,
        password: formData.password
      });
      
      if (response.success) {
        // Save session to localStorage
        const sessionData = {
          username: response.username || formData.email,
          email: formData.email,
          logged_in: true
        };
        console.log('Saving session:', sessionData);
        localStorage.setItem('zalpha_session', JSON.stringify(sessionData));
        
        console.log('Session saved, navigating to success');
        navigate('/success');
      } else {
        console.log('Login failed:', response.message);
        setErrors({ general: response.message });
      }
    } catch (error) {
      setErrors({ general: 'Network error. Please try again.' });
    } finally {
      setIsLoading(false);
    }
  };

  const handleBackToLanding = () => {
    navigate('/');
  };

  return (
    <div className="login-page">
      <div className="login-container">
        <header className="login-header">
          <button className="back-button" onClick={handleBackToLanding}>
            ← Back to Landing
          </button>
          <div className="logo">
            <h1>Z-Alpha Securities</h1>
          </div>
        </header>

        <div className="login-form-container">
          <div className="login-form-wrapper">
            <h2>Welcome Back</h2>
            <p className="login-subtitle">Sign in to access your risk management dashboard</p>

            <form className="login-form" onSubmit={handleSubmit}>
              <div className="form-group">
                <label htmlFor="email">Email Address</label>
                <input
                  type="email"
                  id="email"
                  name="email"
                  value={formData.email}
                  onChange={handleInputChange}
                  className={errors.email ? 'error' : ''}
                  placeholder="Enter your email"
                />
                {errors.email && <span className="error-message">{errors.email}</span>}
              </div>

              <div className="form-group">
                <label htmlFor="password">Password</label>
                <input
                  type="password"
                  id="password"
                  name="password"
                  value={formData.password}
                  onChange={handleInputChange}
                  className={errors.password ? 'error' : ''}
                  placeholder="Enter your password"
                />
                {errors.password && <span className="error-message">{errors.password}</span>}
              </div>

              <button 
                type="submit" 
                className="login-button"
                disabled={isLoading}
              >
                {isLoading ? 'Signing In...' : 'Sign In'}
              </button>
              
              {errors.general && (
                <div className="error-message general-error">
                  {errors.general}
                </div>
              )}
            </form>

            <div className="login-footer">
              <p>Don't have an account? <button className="link-button">Contact Sales</button></p>
              <p><button className="link-button">Forgot Password?</button></p>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default LoginPage;
