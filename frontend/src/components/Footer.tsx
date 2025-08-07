import React from 'react';
import './Footer.css';

const Footer: React.FC = () => {
  return (
    <footer className="footer">
      <div className="footer-content">
        <div className="footer-section">
          <div className="company-info">
            <h3 className="company-name">Z-Alpha Securities</h3>
            <p className="company-address">
              350 Park Avenue, 20th Floor<br />
              New York, NY 10022<br />
              United States
            </p>
          </div>
        </div>
        
        <div className="footer-section">
          <div className="contact-info">
            <p className="phone">+1 (212) 555-0123</p>
            <p className="email">info@zalpha-securities.com</p>
          </div>
        </div>
        
        <div className="footer-section">
          <div className="legal-info">
            <p className="copyright">
              © 2024 Z-Alpha Securities LLC. All rights reserved.
            </p>
            <p className="registration">
              SEC Registered Investment Advisor
            </p>
          </div>
        </div>
      </div>
    </footer>
  );
};

export default Footer; 