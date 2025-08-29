import React from 'react';
import './Footer.css';

const Footer: React.FC = () => {
  return (
    <footer className="dashboard-footer">
      <div className="dashboard-footer-content">
        <div className="dashboard-footer-section">
          <div className="dashboard-company-info">
            <h3 className="dashboard-company-name">Z-Alpha Securities</h3>
            <p className="dashboard-company-address">
              350 Park Avenue, 20th Floor<br />
              New York, NY 10022<br />
              United States
            </p>
          </div>
        </div>
        
        <div className="dashboard-footer-section">
          <div className="dashboard-contact-info">
            <p className="dashboard-phone">+1 (212) 555-0123</p>
            <p className="dashboard-email">info@zalpha-securities.com</p>
          </div>
        </div>
        
        <div className="dashboard-footer-section">
          <div className="dashboard-legal-info">
            <p className="dashboard-copyright">
              © 2024 Z-Alpha Securities LLC. All rights reserved.
            </p>
            <p className="dashboard-registration">
              SEC Registered Investment Advisor
            </p>
          </div>
        </div>
      </div>
    </footer>
  );
};

export default Footer;


