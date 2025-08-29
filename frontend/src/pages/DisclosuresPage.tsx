import React from 'react';
import { useNavigate } from 'react-router-dom';
import Navbar from '../components/Navbar';
import Footer from '../components/Footer';

const DisclosuresPage: React.FC = () => {
  const navigate = useNavigate();
  return (
    <div className="disclosures-page" style={{ minHeight: '100vh', display: 'flex', flexDirection: 'column' }}>
      <Navbar onBrandClick={() => navigate('/')} />
      <section style={{ marginTop: 70, padding: '3rem 1.5rem', maxWidth: 900, margin: '70px auto 0', flex: '1 0 auto' }}>
        <h1 style={{ fontSize: '2rem', fontWeight: 800, color: '#202124', marginBottom: '1rem' }}>Disclosures</h1>
        <h2>No Financial Advice</h2>
        <p>All content is for demonstration and educational purposes only. No investment recommendations are made.</p>
        <h2>Data Sources</h2>
        <p>Sample and synthetic data may be displayed. No confidential or client data is used.</p>
        <h2>Conflicts and Compensation</h2>
        <p>There is no compensation, affiliate marketing, or paid partnerships associated with this project.</p>
        <h2>Regulatory Status</h2>
        <p>This project is not registered with any regulatory authority and does not provide regulated services.</p>
      </section>
      <Footer />
    </div>
  );
};

export default DisclosuresPage;


