import React from 'react';
import { BrowserRouter as Router, Routes, Route, Navigate } from 'react-router-dom';
import './App.css';
import { SessionProvider } from './contexts/SessionContext';
import ProtectedRoute from './components/ProtectedRoute';
import DashboardLayout from './components/DashboardLayout';
import IntroductionPage from './pages/IntroductionPage';
import PortfolioSummaryPage from './pages/PortfolioSummaryPage';
import VolatilitySizingPage from './pages/VolatilitySizingPage';
import FactorExposurePage from './pages/FactorExposurePage';
import ConcentrationRiskPage from './pages/ConcentrationRiskPage';
import StressTestingPage from './pages/StressTestingPage';
import ForecastRiskPage from './pages/ForecastRiskPage';
import UserProfilePage from './pages/UserProfilePage';
import RealizedRiskPage from './pages/RealizedRiskPage';
import LiquidityRiskPage from './pages/LiquidityRiskPage';

function App() {
  return (
    <SessionProvider>
      <Router>
        <div className="App">
          <Routes>
        <Route path="/" element={<Navigate to="/introduction" replace />} />
        <Route path="/introduction" element={
          <ProtectedRoute>
            <DashboardLayout>
              <IntroductionPage />
            </DashboardLayout>
          </ProtectedRoute>
        } />
        <Route path="/portfolio-summary" element={
          <ProtectedRoute>
            <DashboardLayout>
              <PortfolioSummaryPage />
            </DashboardLayout>
          </ProtectedRoute>
        } />
        <Route path="/realized-risk" element={
          <ProtectedRoute>
            <DashboardLayout>
              <RealizedRiskPage />
            </DashboardLayout>
          </ProtectedRoute>
        } />
        <Route path="/volatility-sizing" element={
          <ProtectedRoute>
            <DashboardLayout>
              <VolatilitySizingPage />
            </DashboardLayout>
          </ProtectedRoute>
        } />
        <Route path="/factor-exposure" element={
          <ProtectedRoute>
            <DashboardLayout>
              <FactorExposurePage />
            </DashboardLayout>
          </ProtectedRoute>
        } />
        <Route path="/concentration-risk" element={
          <ProtectedRoute>
            <DashboardLayout>
              <ConcentrationRiskPage />
            </DashboardLayout>
          </ProtectedRoute>
        } />
        <Route path="/stress-testing" element={
          <ProtectedRoute>
            <DashboardLayout>
              <StressTestingPage />
            </DashboardLayout>
          </ProtectedRoute>
        } />
        <Route path="/forecast-risk" element={
          <ProtectedRoute>
            <DashboardLayout>
              <ForecastRiskPage />
            </DashboardLayout>
          </ProtectedRoute>
        } />
        <Route path="/liquidity-risk" element={
          <ProtectedRoute>
            <DashboardLayout>
              <LiquidityRiskPage />
            </DashboardLayout>
          </ProtectedRoute>
        } />
        <Route path="/user-profile" element={
          <ProtectedRoute>
            <DashboardLayout>
              <UserProfilePage />
            </DashboardLayout>
          </ProtectedRoute>
        } />
          </Routes>
        </div>
      </Router>
    </SessionProvider>
  );
}

export default App;
