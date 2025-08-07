import React from 'react';
import { Link, useLocation } from 'react-router-dom';
import Footer from './Footer';
import './DashboardLayout.css';

interface DashboardLayoutProps {
  children: React.ReactNode;
}

const DashboardLayout: React.FC<DashboardLayoutProps> = ({ children }) => {
  const location = useLocation();

  const isActive = (path: string) => {
    return location.pathname === path;
  };

  return (
    <div className="dashboard-layout">
      <header className="header">
        {/* Top navbar - Logo and User Info */}
        <div className="top-navbar">
          <div className="logo-container">
            <div className="logo">
              <div className="logo-icon">σ</div>
              <div className="logo-text">
                <span className="logo-main">Z-ALPHA</span>
                <span className="logo-separator">|</span>
                <span className="logo-sub">Securities</span>
              </div>
            </div>
          </div>
          <div className="user-info">
            <span className="logged-in-label">Logged in:</span>
            <span className="username">admin</span>
          </div>
        </div>
        
        {/* Bottom navbar - Navigation Tabs */}
        <div className="nav-tabs">
          <Link to="/introduction" className={`nav-tab ${isActive('/introduction') ? 'active' : ''}`}>
            Introduction
          </Link>
          <Link to="/portfolio-summary" className={`nav-tab ${isActive('/portfolio-summary') ? 'active' : ''}`}>
            Portfolio Summary
          </Link>
          <Link to="/realized-risk" className={`nav-tab ${isActive('/realized-risk') ? 'active' : ''}`}>
            Realized Risk
          </Link>
          <Link to="/forecast-risk" className={`nav-tab ${isActive('/forecast-risk') ? 'active' : ''}`}>
            Forecast Risk
          </Link>
          <Link to="/factor-exposure" className={`nav-tab ${isActive('/factor-exposure') ? 'active' : ''}`}>
            Factor Exposure
          </Link>
          <Link to="/stress-testing" className={`nav-tab ${isActive('/stress-testing') ? 'active' : ''}`}>
            Stress Testing
          </Link>
          <Link to="/concentration-risk" className={`nav-tab ${isActive('/concentration-risk') ? 'active' : ''}`}>
            Concentration Risk
          </Link>
          <Link to="/liquidity-risk" className={`nav-tab ${isActive('/liquidity-risk') ? 'active' : ''}`}>
            Liquidity Risk
          </Link>
          <Link to="/volatility-sizing" className={`nav-tab ${isActive('/volatility-sizing') ? 'active' : ''}`}>
            Volatility-Based Sizing
          </Link>
          <Link to="/user-profile" className={`nav-tab ${isActive('/user-profile') ? 'active' : ''}`}>
            User Profile
          </Link>
        </div>
      </header>
      <main className="main-content">
        {children}
      </main>
      <Footer />
    </div>
  );
};

export default DashboardLayout; 