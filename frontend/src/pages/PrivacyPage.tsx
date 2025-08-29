import React, { useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import Navbar from '../components/Navbar';
import Footer from '../components/Footer';

const PrivacyPage: React.FC = () => {
  const navigate = useNavigate();
  useEffect(() => { window.scrollTo(0, 0); }, []);
  return (
    <div className="privacy-page" style={{ minHeight: '100vh', display: 'flex', flexDirection: 'column' }}>
      <Navbar onBrandClick={() => navigate('/')} />
      <section style={{ marginTop: 70, padding: '3rem 1.5rem', maxWidth: 900, marginLeft: 'auto', marginRight: 'auto', flex: '1 0 auto' }}>
        <h1 style={{ fontSize: '2rem', fontWeight: 800, color: '#202124', marginBottom: '1rem' }}>Privacy Policy</h1>
        <p style={{ color: '#5f6368' }}>
          This website is a non-commercial academic project created as part of a Master’s thesis in Computer Science at the Cracow University of Technology (Politechnika Krakowska).
          All names, numbers, statistics and claims presented here are fictitious and serve only a design and demonstration purpose.
        </p>
        <h2>Personal Data</h2>
        <p>
          We do not sell or share personal data. Any session-based authentication is local to the user and exists solely to demonstrate application flows.
          No production data is processed. Data displayed in dashboards is synthetic or sample-based.
        </p>
        <h2>IBKR/TWS and Third-Party Services</h2>
        <p>
          Where Interactive Brokers (IBKR) TWS or API integrations are referenced, this project uses only session-scoped access in accordance with IBKR Terms of Service.
          There is no direct, persistent or privileged API connection provided to the public. Integrations are illustrative and not intended for trading.
        </p>
        <h2>Cookies</h2>
        <p>Only strictly necessary cookies (if any) are used to support session flows for demonstration. No marketing or tracking cookies are used.</p>
        <h2>No Financial Advice</h2>
        <p>
          Nothing on this site constitutes financial, investment, legal or tax advice. The author has no professional certification in these areas and provides no binding guidance.
        </p>
        <h2>Contact</h2>
        <p>For academic inquiries only, please contact the project author through the repository issues or provided academic channels.</p>
      </section>
      <Footer />
    </div>
  );
};

export default PrivacyPage;


