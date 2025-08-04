import React from 'react';
import { Link, useLocation } from 'react-router-dom';
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
        <h1 className="logo">Daisy Risk Engine Dashboard</h1>
        <div className="nav-tabs">
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
          <Link to="/reconstructed-prices" className={`nav-tab ${isActive('/reconstructed-prices') ? 'active' : ''}`}>
            Reconstructed Prices
          </Link>
          <Link to="/themes-proxies" className={`nav-tab ${isActive('/themes-proxies') ? 'active' : ''}`}>
            Themes & Proxies
          </Link>
        </div>
      </header>
      <main className="main-content">
        {children}
      </main>
    </div>
  );
};

export default DashboardLayout; 