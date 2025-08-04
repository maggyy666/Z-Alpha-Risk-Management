import React from 'react';
import { BrowserRouter as Router, Routes, Route, Navigate } from 'react-router-dom';
import './App.css';
import DashboardLayout from './components/DashboardLayout';
import VolatilitySizingPage from './pages/VolatilitySizingPage';
import FactorExposurePage from './pages/FactorExposurePage';

function App() {
  return (
    <Router>
      <div className="App">
              <Routes>
        <Route path="/" element={<Navigate to="/volatility-sizing" replace />} />
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
      </Routes>
      </div>
    </Router>
  );
}

export default App;
