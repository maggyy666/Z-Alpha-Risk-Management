import React, { useEffect } from 'react';
import { BrowserRouter as Router, Routes, Route, Navigate, useLocation } from 'react-router-dom';
import LandingPage from './pages/LandingPage';
import LoginPage from './pages/LoginPage';
import SuccessPage from './pages/SuccessPage';
import RiskSolutionsPage from './pages/RiskSolutionsPage';
import WhoWeArePage from './pages/WhoWeArePage';
import ResearchInsightsPage from './pages/ResearchInsightsPage';
import CareersPage from './pages/CareersPage';
import PrivacyPage from './pages/PrivacyPage';
import TermsPage from './pages/TermsPage';
import NoticesPage from './pages/NoticesPage';
import DisclosuresPage from './pages/DisclosuresPage';
import './App.css';

function App() {
  // Scroll to top on route change
  const ScrollToTop: React.FC = () => {
    const { pathname } = useLocation();
    useEffect(() => {
      window.scrollTo({ top: 0, left: 0, behavior: 'instant' as ScrollBehavior });
    }, [pathname]);
    return null;
  };

  return (
    <Router>
      <div className="App">
        <ScrollToTop />
        <Routes>
          <Route path="/" element={<LandingPage />} />
          <Route path="/login" element={<LoginPage />} />
          <Route path="/success" element={<SuccessPage />} />
          <Route path="/risk-solutions" element={<RiskSolutionsPage />} />
          <Route path="/who-we-are" element={<WhoWeArePage />} />
          <Route path="/research-insights" element={<ResearchInsightsPage />} />
          <Route path="/careers" element={<CareersPage />} />
          <Route path="/privacy" element={<PrivacyPage />} />
          <Route path="/terms" element={<TermsPage />} />
          <Route path="/notices" element={<NoticesPage />} />
          <Route path="/disclosures" element={<DisclosuresPage />} />
          <Route path="/app" element={<Navigate to="http://localhost:3000/introduction" replace />} />
        </Routes>
      </div>
    </Router>
  );
}

export default App;
