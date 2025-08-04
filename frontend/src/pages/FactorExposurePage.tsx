import React, { useState, useEffect } from 'react';
import apiService from '../services/api';
import './FactorExposurePage.css';

interface FactorExposureData {
  date: string;
  ticker: string;
  factor: string;
  beta: number;
  r2?: number;
}

interface FactorExposureResponse {
  factor_exposures: FactorExposureData[];
  r2_data: FactorExposureData[];
  available_factors: string[];
  available_tickers: string[];
}

const FactorExposurePage: React.FC = () => {
  const [factorData, setFactorData] = useState<FactorExposureResponse | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  
  // Selected filters
  const [selectedFactors, setSelectedFactors] = useState<string[]>(['MARKET', 'MOMENTUM']);
  const [selectedTickers, setSelectedTickers] = useState<string[]>(['PORTFOLIO', 'BULL']);
  const [selectedTickersR2, setSelectedTickersR2] = useState<string[]>(['PORTFOLIO', 'BULL']);

  useEffect(() => {
    fetchFactorExposureData();
  }, []);

  const fetchFactorExposureData = async () => {
    try {
      setLoading(true);
      console.log('Fetching factor exposure data...');
      const data = await apiService.getFactorExposureData();
      console.log('Received data:', data);
      setFactorData(data);
      setError(null);
    } catch (err) {
      console.error('Error fetching data:', err);
      setError('Failed to fetch factor exposure data');
    } finally {
      setLoading(false);
    }
  };

  const handleFactorToggle = (factor: string) => {
    setSelectedFactors(prev => 
      prev.includes(factor) 
        ? prev.filter(f => f !== factor)
        : [...prev, factor]
    );
  };

  const handleTickerToggle = (ticker: string) => {
    setSelectedTickers(prev => 
      prev.includes(ticker) 
        ? prev.filter(t => t !== ticker)
        : [...prev, ticker]
    );
  };

  const handleTickerR2Toggle = (ticker: string) => {
    setSelectedTickersR2(prev => 
      prev.includes(ticker) 
        ? prev.filter(t => t !== ticker)
        : [...prev, ticker]
    );
  };

  if (loading) {
    return (
      <div className="factor-exposure-page">
        <div className="loading" style={{color: 'white', fontSize: '20px'}}>
          Loading factor exposure data...
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="factor-exposure-page">
        <div className="error" style={{color: 'red', fontSize: '20px'}}>{error}</div>
      </div>
    );
  }

  return (
    <div className="factor-exposure-page" style={{backgroundColor: '#0a0a0a', minHeight: '100vh', color: 'white'}}>
      <div style={{padding: '20px', color: 'white'}}>
        <h1 style={{color: 'white'}}>Factor Exposure Page Loaded!</h1>
        <p style={{color: 'white'}}>Data: {factorData ? 'Loaded' : 'Not loaded'}</p>
      </div>
      <div className="section">
        <div className="section-header">
          <h2>Rolling Factor Exposures</h2>
          <div className="controls">
            <div className="control-group">
              <label>Select Factors:</label>
              <div className="filter-tags">
                {factorData?.available_factors.map(factor => (
                  <span
                    key={factor}
                    className={`filter-tag ${selectedFactors.includes(factor) ? 'active' : ''}`}
                    onClick={() => handleFactorToggle(factor)}
                  >
                    {factor}
                    {selectedFactors.includes(factor) && <span className="remove">×</span>}
                  </span>
                ))}
              </div>
            </div>
            <div className="control-group">
              <label>Select Tickers:</label>
              <div className="filter-tags">
                {factorData?.available_tickers.map(ticker => (
                  <span
                    key={ticker}
                    className={`filter-tag ${selectedTickers.includes(ticker) ? 'active' : ''}`}
                    onClick={() => handleTickerToggle(ticker)}
                  >
                    {ticker}
                    {selectedTickers.includes(ticker) && <span className="remove">×</span>}
                  </span>
                ))}
              </div>
            </div>
          </div>
        </div>
        
        <div className="chart-container">
          <div className="chart-placeholder">
            Factor Exposure Chart will be implemented here
          </div>
        </div>
      </div>

      <div className="section">
        <div className="section-header">
          <h2>Rolling R²</h2>
          <div className="controls">
            <div className="control-group">
              <label>Select Tickers for R²:</label>
              <div className="filter-tags">
                {factorData?.available_tickers.map(ticker => (
                  <span
                    key={ticker}
                    className={`filter-tag ${selectedTickersR2.includes(ticker) ? 'active' : ''}`}
                    onClick={() => handleTickerR2Toggle(ticker)}
                  >
                    {ticker}
                    {selectedTickersR2.includes(ticker) && <span className="remove">×</span>}
                  </span>
                ))}
              </div>
            </div>
          </div>
        </div>
        
        <div className="chart-container">
          <div className="chart-placeholder">
            R² Chart will be implemented here
          </div>
        </div>
      </div>
    </div>
  );
};

export default FactorExposurePage; 