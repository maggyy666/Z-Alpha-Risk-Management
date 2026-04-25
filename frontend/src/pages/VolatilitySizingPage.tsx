import React, { useState } from 'react';
import apiService, { VolatilityData } from '../services/api';
import VolatilityDonutChart from '../components/VolatilityDonutChart';
import { useApiData } from '../hooks/useApiData';
import { useSession } from '../contexts/SessionContext';
import './VolatilitySizingPage.css';

const formatCurrency = (value: number) =>
  new Intl.NumberFormat('en-US', { style: 'currency', currency: 'USD' }).format(value);

const formatPercentage = (value: number) => `${value.toFixed(2)}%`;

const formatNumber = (value: number) => new Intl.NumberFormat('en-US').format(value);

const VolatilitySizingPage: React.FC = () => {
  const { getCurrentUsername } = useSession();
  const [selectedModel, setSelectedModel] = useState<string>('EWMA (5D)');
  const username = getCurrentUsername();

  const { data, loading, error, refetch } = useApiData<VolatilityData>(
    () => apiService.getVolatilityData(selectedModel, username),
    [selectedModel, username],
    'Failed to fetch volatility data',
  );

  const initializePortfolio = async () => {
    try {
      await apiService.initializePortfolio();
      await refetch();
    } catch {
      // refetch already surfaces the error state
    }
  };

  if (loading) {
    return (
      <div className="volatility-sizing-page">
        <div className="loading">Loading volatility data...</div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="volatility-sizing-page">
        <div className="error">
          <p>{error}</p>
          <button onClick={initializePortfolio} className="init-button">
            Initialize Portfolio
          </button>
        </div>
      </div>
    );
  }

  const portfolioData = data?.portfolio_data ?? [];

  return (
    <div className="volatility-sizing-page">
      <div className="section">
        <div className="section-header">
          <h2>Volatility-Based Sizing</h2>
          <div className="dropdown-container">
            <label>Select Volatility Forecast Model:</label>
            <select
              className="model-dropdown"
              value={selectedModel}
              onChange={(e) => setSelectedModel(e.target.value)}
            >
              <option value="EWMA (5D)">EWMA (5D)</option>
              <option value="EWMA (30D)">EWMA (30D)</option>
              <option value="EWMA (200D)">EWMA (200D)</option>
              <option value="Garch Volatility">Garch Volatility</option>
              <option value="E-Garch Volatility">E-Garch Volatility</option>
            </select>
          </div>
        </div>

        <div className="table-container">
          <table className="volatility-table">
            <thead>
              <tr>
                <th>Ticker</th>
                <th>Forecast Volatility</th>
                <th>Current Weight</th>
                <th>Adj. Volatility Weight</th>
                <th>Current MV</th>
                <th>Target MV</th>
                <th>(+/-)</th>
                <th>Last Price</th>
                <th>Shares Delta</th>
              </tr>
            </thead>
            <tbody>
              {portfolioData.map((item) => (
                <tr key={item.symbol}>
                  <td>{item.symbol}</td>
                  <td className="percentage-column">{formatPercentage(item.forecast_volatility_pct)}</td>
                  <td className="percentage-column">{formatPercentage(item.current_weight_pct)}</td>
                  <td className="percentage-column">{formatPercentage(item.adj_volatility_weight_pct)}</td>
                  <td className="currency-column">{formatCurrency(item.current_mv || 0)}</td>
                  <td className="currency-column">{formatCurrency(item.target_mv || 0)}</td>
                  <td className={`currency-column ${item.delta_mv && item.delta_mv > 0 ? 'positive' : 'negative'}`}>
                    {formatCurrency(item.delta_mv || 0)}
                  </td>
                  <td className="currency-column">{formatCurrency(item.last_price)}</td>
                  <td className={`number-column ${item.delta_shares && item.delta_shares > 0 ? 'positive' : 'negative'}`}>
                    {formatNumber(item.delta_shares || 0)}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>

        <div className="volatility-chart-container">
          <VolatilityDonutChart data={portfolioData} />
        </div>
      </div>
    </div>
  );
};

export default VolatilitySizingPage;
