import React from 'react';
import { useNavigate } from 'react-router-dom';
import Navbar from '../components/Navbar';
import Footer from '../components/Footer';

const TermsPage: React.FC = () => {
  const navigate = useNavigate();
  return (
    <div className="terms-page" style={{ minHeight: '100vh', display: 'flex', flexDirection: 'column' }}>
      <Navbar onBrandClick={() => navigate('/')} />
      <section style={{ marginTop: 70, padding: '3rem 1.5rem', maxWidth: 900, margin: '70px auto 0', flex: '1 0 auto' }}>
        <h1 style={{ fontSize: '2rem', fontWeight: 800, color: '#202124', marginBottom: '1rem' }}>Terms of Use</h1>
        <p style={{ color: '#5f6368' }}>
          This site is an academic, non-commercial project. By using it, you acknowledge that all content is for demonstration only and may be incomplete, inaccurate or fictitious.
        </p>
        <h2>License and Access</h2>
        <p>You are granted a limited, non-exclusive right to view the site solely for academic evaluation. No redistribution, resale or production deployment is permitted.</p>
        <h2>Prohibited Uses</h2>
        <ul>
          <li>No trading activity or reliance on the output for investment decisions.</li>
          <li>No attempts to bypass session boundaries or access third-party APIs beyond permitted flows.</li>
          <li>No scraping, reverse engineering or unauthorized data collection.</li>
        </ul>
        <h2>Disclaimer</h2>
        <p>All information is provided “as is,” without warranties of any kind. The author is not liable for any damages arising from use of the site.</p>
        <h2>Affiliations</h2>
        <p>References to IBKR/TWS are illustrative. Any interactions comply with their Terms of Service and are session-scoped only.</p>
      </section>
      <Footer />
    </div>
  );
};

export default TermsPage;


