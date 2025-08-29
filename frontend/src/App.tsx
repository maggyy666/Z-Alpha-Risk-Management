import React from 'react';
import { BrowserRouter as Router, Routes, Route, Navigate } from 'react-router-dom';
import './App.css';
import { SessionProvider } from './contexts/SessionContext';

// Import CSS dla dashboard pages
import './pages/IntroductionPage.css';
import ProtectedRoute from './components/ProtectedRoute';
import DashboardLayout from './components/DashboardLayout';
import Navbar from './components/Navbar';
import LandingFooter from './components/LandingFooter';

// Landing pages
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

// Dashboard pages
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
            {/* Landing page routes */}
            <Route path="/" element={
              <div className="landing-app">
                <Navbar 
                  onClientLogin={() => window.location.href = '/login'}
                  onNavigate={(key) => {
                    const routes = {
                      'who-we-are': '/who-we-are',
                      'risk-solutions': '/risk-solutions',
                      'research-insights': '/research-insights',
                      'careers': '/careers'
                    };
                    window.location.href = routes[key as keyof typeof routes] || '/';
                  }}
                  onBrandClick={() => window.location.href = '/'}
                />
                <LandingPage />
              </div>
            } />
            
            <Route path="/login" element={
              <div className="landing-app">
                <Navbar 
                  onClientLogin={() => window.location.href = '/login'}
                  onNavigate={(key) => {
                    const routes = {
                      'who-we-are': '/who-we-are',
                      'risk-solutions': '/risk-solutions',
                      'research-insights': '/research-insights',
                      'careers': '/careers'
                    };
                    window.location.href = routes[key as keyof typeof routes] || '/';
                  }}
                  onBrandClick={() => window.location.href = '/'}
                />
                <LoginPage />
                <LandingFooter />
              </div>
            } />
            
            <Route path="/success" element={
              <div className="landing-app">
                <Navbar 
                  onClientLogin={() => window.location.href = '/login'}
                  onNavigate={(key) => {
                    const routes = {
                      'who-we-are': '/who-we-are',
                      'risk-solutions': '/risk-solutions',
                      'research-insights': '/research-insights',
                      'careers': '/careers'
                    };
                    window.location.href = routes[key as keyof typeof routes] || '/';
                  }}
                  onBrandClick={() => window.location.href = '/'}
                />
                <SuccessPage />
                <LandingFooter />
              </div>
            } />
            
            <Route path="/who-we-are" element={
              <div className="landing-app">
                <Navbar 
                  onClientLogin={() => window.location.href = '/login'}
                  onNavigate={(key) => {
                    const routes = {
                      'who-we-are': '/who-we-are',
                      'risk-solutions': '/risk-solutions',
                      'research-insights': '/research-insights',
                      'careers': '/careers'
                    };
                    window.location.href = routes[key as keyof typeof routes] || '/';
                  }}
                  onBrandClick={() => window.location.href = '/'}
                />
                <WhoWeArePage />
              </div>
            } />
            
            <Route path="/risk-solutions" element={
              <div className="landing-app">
                <Navbar 
                  onClientLogin={() => window.location.href = '/login'}
                  onNavigate={(key) => {
                    const routes = {
                      'who-we-are': '/who-we-are',
                      'risk-solutions': '/risk-solutions',
                      'research-insights': '/research-insights',
                      'careers': '/careers'
                    };
                    window.location.href = routes[key as keyof typeof routes] || '/';
                  }}
                  onBrandClick={() => window.location.href = '/'}
                />
                <RiskSolutionsPage />
              </div>
            } />
            
            <Route path="/research-insights" element={
              <div className="landing-app">
                <Navbar 
                  onClientLogin={() => window.location.href = '/login'}
                  onNavigate={(key) => {
                    const routes = {
                      'who-we-are': '/who-we-are',
                      'risk-solutions': '/risk-solutions',
                      'research-insights': '/research-insights',
                      'careers': '/careers'
                    };
                    window.location.href = routes[key as keyof typeof routes] || '/';
                  }}
                  onBrandClick={() => window.location.href = '/'}
                />
                <ResearchInsightsPage />
              </div>
            } />
            
            <Route path="/careers" element={
              <div className="landing-app">
                <Navbar 
                  onClientLogin={() => window.location.href = '/login'}
                  onNavigate={(key) => {
                    const routes = {
                      'who-we-are': '/who-we-are',
                      'risk-solutions': '/risk-solutions',
                      'research-insights': '/research-insights',
                      'careers': '/careers'
                    };
                    window.location.href = routes[key as keyof typeof routes] || '/';
                  }}
                  onBrandClick={() => window.location.href = '/'}
                />
                <CareersPage />
              </div>
            } />
            
            <Route path="/privacy" element={
              <div className="landing-app">
                <Navbar 
                  onClientLogin={() => window.location.href = '/login'}
                  onNavigate={(key) => {
                    const routes = {
                      'who-we-are': '/who-we-are',
                      'risk-solutions': '/risk-solutions',
                      'research-insights': '/research-insights',
                      'careers': '/careers'
                    };
                    window.location.href = routes[key as keyof typeof routes] || '/';
                  }}
                  onBrandClick={() => window.location.href = '/'}
                />
                <PrivacyPage />
                <LandingFooter />
              </div>
            } />
            
            <Route path="/terms" element={
              <div className="landing-app">
                <Navbar 
                  onClientLogin={() => window.location.href = '/login'}
                  onNavigate={(key) => {
                    const routes = {
                      'who-we-are': '/who-we-are',
                      'risk-solutions': '/risk-solutions',
                      'research-insights': '/research-insights',
                      'careers': '/careers'
                    };
                    window.location.href = routes[key as keyof typeof routes] || '/';
                  }}
                  onBrandClick={() => window.location.href = '/'}
                />
                <TermsPage />
                <LandingFooter />
              </div>
            } />
            
            <Route path="/notices" element={
              <div className="landing-app">
                <Navbar 
                  onClientLogin={() => window.location.href = '/login'}
                  onNavigate={(key) => {
                    const routes = {
                      'who-we-are': '/who-we-are',
                      'risk-solutions': '/risk-solutions',
                      'research-insights': '/research-insights',
                      'careers': '/careers'
                    };
                    window.location.href = routes[key as keyof typeof routes] || '/';
                  }}
                  onBrandClick={() => window.location.href = '/'}
                />
                <NoticesPage />
                <LandingFooter />
              </div>
            } />
            
            <Route path="/disclosures" element={
              <div className="landing-app">
                <Navbar 
                  onClientLogin={() => window.location.href = '/login'}
                  onNavigate={(key) => {
                    const routes = {
                      'who-we-are': '/who-we-are',
                      'risk-solutions': '/risk-solutions',
                      'research-insights': '/research-insights',
                      'careers': '/careers'
                    };
                    window.location.href = routes[key as keyof typeof routes] || '/';
                  }}
                  onBrandClick={() => window.location.href = '/'}
                />
                <DisclosuresPage />
                <LandingFooter />
              </div>
            } />

            {/* Dashboard routes */}
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
