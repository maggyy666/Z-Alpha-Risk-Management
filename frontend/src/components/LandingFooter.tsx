import React from 'react';
import { Linkedin, Facebook, Instagram, Youtube } from 'lucide-react';
import { useNavigate } from 'react-router-dom';
import './LandingFooter.css';

export const LandingFooter: React.FC = () => {
  const navigate = useNavigate();
  const social = [
    { icon: Linkedin, name: 'LinkedIn' },
    { icon: Facebook, name: 'Facebook' },
    { icon: Instagram, name: 'Instagram' },
    { icon: Youtube, name: 'YouTube' },
  ];

  return (
    <footer className="landing-page-footer">
      <div className="landing-page-container">
        <div className="landing-page-footer-top">
          <div className="landing-page-brand">
            <div className="landing-page-brand-row">
              <div className="landing-page-brand-mark">α</div>
              <div className="landing-page-brand-text">
                <span className="landing-page-brand-main">Z-Alpha</span>
                <span className="landing-page-brand-sep">|</span>
                <span className="landing-page-brand-sub">Capital</span>
              </div>
            </div>
            <div className="landing-page-brand-address">
              350 Park Avenue, 20th Floor<br />
              New York, NY 10022<br />
              United States
            </div>
          </div>

          <nav className="landing-page-footer-links">
            <a href="#" onClick={(e) => { e.preventDefault(); navigate('/who-we-are'); }}>Who We Are</a>
            <a href="#" onClick={(e) => { e.preventDefault(); navigate('/risk-solutions'); }}>What We Do</a>
            <a href="#" onClick={(e) => { e.preventDefault(); navigate('/research-insights'); }}>News & Insights</a>
            <a href="#" onClick={(e) => { e.preventDefault(); navigate('/careers'); }}>Careers</a>
          </nav>
        </div>

        <div className="landing-page-footer-sep" />

        <div className="landing-page-footer-bottom">
          <div className="landing-page-legal-links">
            <a href="#" onClick={(e) => { e.preventDefault(); navigate('/privacy'); }}>Privacy</a>
            <a href="#" onClick={(e) => { e.preventDefault(); navigate('/terms'); }}>Terms of Use</a>
            <a href="#" onClick={(e) => { e.preventDefault(); navigate('/notices'); }}>Notices</a>
            <a href="#" onClick={(e) => { e.preventDefault(); navigate('/disclosures'); }}>Disclosures</a>
          </div>
          <div className="landing-page-copyright">
            Copyright © Z-Alpha Capital LLC or one of its affiliates. All rights reserved.
          </div>
          <div className="landing-page-social">
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

export default LandingFooter;
