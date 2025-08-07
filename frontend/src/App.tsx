import React from 'react';
import { BrowserRouter as Router, Routes, Route, Navigate } from 'react-router-dom';
import './App.css';
import DashboardLayout from './components/DashboardLayout';
import IntroductionPage from './pages/IntroductionPage';
import PortfolioSummaryPage from './pages/PortfolioSummaryPage';
import VolatilitySizingPage from './pages/VolatilitySizingPage';
import FactorExposurePage from './pages/FactorExposurePage';
import ConcentrationRiskPage from './pages/ConcentrationRiskPage';
import StressTestingPage from './pages/StressTestingPage';
import ForecastRiskPage from './pages/ForecastRiskPage';
import UserProfilePage from './pages/UserProfilePage';

function App() {
  return (
    <Router>
      <div className="App">
              <Routes>
        <Route path="/" element={<Navigate to="/introduction" replace />} />
        <Route path="/introduction" element={
          <DashboardLayout>
            <IntroductionPage />
          </DashboardLayout>
        } />
        <Route path="/portfolio-summary" element={
          <DashboardLayout>
            <PortfolioSummaryPage />
          </DashboardLayout>
        } />
        <Route path="/volatility-sizing" element={
          <DashboardLayout>
            <VolatilitySizingPage />
          </DashboardLayout>
        } />
        <Route path="/factor-exposure" element={
          <DashboardLayout>
            <FactorExposurePage />
          </DashboardLayout>
        } />
        <Route path="/concentration-risk" element={
          <DashboardLayout>
            <ConcentrationRiskPage />
          </DashboardLayout>
        } />
        <Route path="/stress-testing" element={
          <DashboardLayout>
            <StressTestingPage />
          </DashboardLayout>
        } />
        <Route path="/forecast-risk" element={
          <DashboardLayout>
            <ForecastRiskPage />
          </DashboardLayout>
        } />
        <Route path="/user-profile" element={
          <DashboardLayout>
            <UserProfilePage />
          </DashboardLayout>
        } />
      </Routes>
      </div>
    </Router>
  );
}

export default App;
