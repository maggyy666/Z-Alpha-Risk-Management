import React from 'react';
import { useNavigate } from 'react-router-dom';
import Navbar from '../components/Navbar';
import Footer from '../components/Footer';

const NoticesPage: React.FC = () => {
  const navigate = useNavigate();
  return (
    <div className="notices-page" style={{ minHeight: '100vh', display: 'flex', flexDirection: 'column' }}>
      <Navbar onBrandClick={() => navigate('/')} />
      <section style={{ marginTop: 70, padding: '3rem 1.5rem', maxWidth: 900, margin: '70px auto 0', flex: '1 0 auto' }}>
        <h1 style={{ fontSize: '2rem', fontWeight: 800, color: '#202124', marginBottom: '1rem' }}>Notices</h1>
        <h2>Academic Project Notice</h2>
        <p>This site is part of a Master’s thesis (Informatics) at Politechnika Krakowska and is not a commercial service.</p>
        <h2>Fictitious Content</h2>
        <p>Names, numbers and statistics are fabricated solely to present design and system capabilities.</p>
        <h2>Third-Party Terms</h2>
        <p>Any mention of IBKR/TWS is compliant with their Terms of Service; no direct public API access is offered; all demos are session-scoped.</p>
      </section>
      <Footer />
    </div>
  );
};

export default NoticesPage;


