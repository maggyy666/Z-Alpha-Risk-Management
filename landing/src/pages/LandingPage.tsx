import React from 'react';
import { useNavigate } from 'react-router-dom';
import './LandingPage.css';

const LandingPage: React.FC = () => {
  const navigate = useNavigate();

  const handleGetStarted = () => {
    navigate('/login');
  };

  return (
    <div className="landing-page">
      <header className="landing-header">
        <div className="logo">
          <h1>Z-Alpha Securities</h1>
          <p>Advanced Risk Management System</p>
        </div>
      </header>

      <main className="landing-main">
        <section className="hero-section">
          <div className="hero-content">
            <h1>Professional Risk Management Platform</h1>
            <p className="hero-subtitle">
              Advanced portfolio analysis, volatility forecasting, and comprehensive risk metrics 
              for institutional-grade investment management.
            </p>
            
            <div className="hero-features">
              <div className="feature">
                <h3>📊 Portfolio Analytics</h3>
                <p>Real-time portfolio risk assessment and performance tracking</p>
              </div>
              <div className="feature">
                <h3>📈 Volatility Forecasting</h3>
                <p>Advanced EGARCH and EWMA models for volatility prediction</p>
              </div>
              <div className="feature">
                <h3>🎯 Factor Exposure</h3>
                <p>Comprehensive factor analysis and correlation insights</p>
              </div>
              <div className="feature">
                <h3>⚡ Stress Testing</h3>
                <p>Historical scenario analysis and regime detection</p>
              </div>
            </div>

            <div className="cta-buttons">
              <button className="btn-primary" onClick={handleGetStarted}>
                Get Started
              </button>
              <button className="btn-secondary">
                Learn More
              </button>
            </div>
          </div>
        </section>

        <section className="features-section">
          <h2>Key Features</h2>
          <div className="features-grid">
            <div className="feature-card">
              <h3>Real-time Data</h3>
              <p>Live market data integration with IBKR and external sources</p>
            </div>
            <div className="feature-card">
              <h3>Risk Metrics</h3>
              <p>VaR, CVaR, volatility, and drawdown analysis</p>
            </div>
            <div className="feature-card">
              <h3>Portfolio Optimization</h3>
              <p>Concentration risk and liquidity analysis</p>
            </div>
            <div className="feature-card">
              <h3>Advanced Analytics</h3>
              <p>Rolling forecasts and regime detection</p>
            </div>
          </div>
        </section>
      </main>

      <footer className="landing-footer">
        <p>&copy; 2024 Z-Alpha Securities. All rights reserved.</p>
      </footer>
    </div>
  );
};

export default LandingPage;
