import React from 'react';
import { Linkedin, Facebook, Instagram, Youtube } from 'lucide-react';
import { useNavigate } from 'react-router-dom';
import './Footer.css';

export const Footer: React.FC = () => {
  const navigate = useNavigate();
  const social = [
    { icon: Linkedin, name: 'LinkedIn' },
    { icon: Facebook, name: 'Facebook' },
    { icon: Instagram, name: 'Instagram' },
    { icon: Youtube, name: 'YouTube' },
  ];

  return (
    <footer className="zalpha-footer">
      <div className="container">
        <div className="footer-top">
          <button className="brand" onClick={() => navigate('/')} aria-label="Home">
            <div className="brand-row">
              <div className="brand-mark">α</div>
              <div className="brand-text">
                <span className="brand-main">Z-Alpha</span>
                <span className="brand-sep">|</span>
                <span className="brand-sub">Capital</span>
              </div>
            </div>
            <div className="brand-address">
              350 Park Avenue, 20th Floor<br />
              New York, NY 10022<br />
              United States
            </div>
          </button>

          <nav className="footer-links">
            <a href="#" onClick={(e) => { e.preventDefault(); navigate('/who-we-are'); }}>Who We Are</a>
            <a href="#" onClick={(e) => { e.preventDefault(); navigate('/risk-solutions'); }}>What We Do</a>
            <a href="#" onClick={(e) => { e.preventDefault(); navigate('/research-insights'); }}>News & Insights</a>
            <a href="#" onClick={(e) => { e.preventDefault(); navigate('/careers'); }}>Careers</a>
          </nav>
        </div>

        <div className="footer-sep" />

        <div className="footer-bottom">
          <div className="legal-links">
            <a href="#" onClick={(e) => { e.preventDefault(); navigate('/privacy'); }}>Privacy</a>
            <a href="#" onClick={(e) => { e.preventDefault(); navigate('/terms'); }}>Terms of Use</a>
            <a href="#" onClick={(e) => { e.preventDefault(); navigate('/notices'); }}>Notices</a>
            <a href="#" onClick={(e) => { e.preventDefault(); navigate('/disclosures'); }}>Disclosures</a>
          </div>
          <div className="copyright">
            Copyright © Z-Alpha Capital LLC or one of its affiliates. All rights reserved.
          </div>
          <div className="social">
            {social.map(({ icon: Icon, name }) => (
              <a key={name} href="#" aria-label={name}>
                <Icon size={16} />
              </a>
            ))}
          </div>
        </div>

      </div>
    </footer>
  );
};

export default Footer;


