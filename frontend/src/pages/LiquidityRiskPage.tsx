import React, { useEffect, useMemo, useState } from 'react';
import { Doughnut } from 'react-chartjs-2';
import {
  Chart as ChartJS,
  CategoryScale,
  LinearScale,
  ArcElement,
  Title,
  Tooltip,
  Legend,
} from 'chart.js';
import apiService, { LiquidityOverviewResponse } from '../services/api';
import { useApiData } from '../hooks/useApiData';
import { useSession } from '../contexts/SessionContext';
import './LiquidityRiskPage.css';

ChartJS.register(CategoryScale, LinearScale, ArcElement, Title, Tooltip, Legend);

const RISK_LEVEL_COLORS: Record<string, string> = {
  LOW: '#4caf50',
  MEDIUM: '#ff9800',
  HIGH: '#f44336',
};

const DISTRIBUTION_COLORS = ['#2196F3', '#64B5F6', '#FF9800'];

const CHART_OPTIONS = {
  responsive: true,
  maintainAspectRatio: false,
  plugins: {
    legend: { position: 'right' as const, labels: { color: '#ffffff', font: { size: 12 } } },
    tooltip: {
      backgroundColor: '#2a2a2a',
      titleColor: '#ffffff',
      bodyColor: '#cccccc',
      borderColor: '#333',
      borderWidth: 1,
    },
  },
};

const buildDistributionData = (data: LiquidityOverviewResponse) => {
  const labels = Object.keys(data.distribution);
  const values = Object.values(data.distribution);
  return {
    labels,
    datasets: [
      {
        data: values,
        backgroundColor: DISTRIBUTION_COLORS,
        borderColor: DISTRIBUTION_COLORS,
        borderWidth: 2,
      },
    ],
  };
};

type LiquidityTab = 'overview' | 'spread' | 'volume' | 'alerts';

const LiquidityRiskPage: React.FC = () => {
  const { getCurrentUsername } = useSession();
  const username = getCurrentUsername();
  const [activeTab, setActiveTab] = useState<LiquidityTab>('overview');

  const { data, loading, error, refetch } = useApiData<LiquidityOverviewResponse>(
    () => apiService.getLiquidityOverview(username),
    [username],
    'Failed to load liquidity data',
  );

  // Refetch when the user saves portfolio edits.
  useEffect(() => {
    const handler = () => { refetch(); };
    window.addEventListener('portfolio-updated', handler);
    return () => window.removeEventListener('portfolio-updated', handler);
  }, [refetch]);

  const distributionData = useMemo(
    () => (data ? buildDistributionData(data) : null),
    [data],
  );

  if (loading) {
    return (
      <div className="liquidity-risk-page">
        <div className="loading-container">
          <div className="loading-spinner"></div>
          <p>Loading liquidity data...</p>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="liquidity-risk-page">
        <div className="error-container">
          <h2>Error</h2>
          <p>{error}</p>
          <button onClick={refetch} className="retry-button">Retry</button>
        </div>
      </div>
    );
  }

  if (!data) {
    return (
      <div className="liquidity-risk-page">
        <div className="no-data-container">
          <h2>No Data Available</h2>
          <p>Liquidity data could not be loaded.</p>
        </div>
      </div>
    );
  }

  const riskColor = RISK_LEVEL_COLORS[data.overview.risk_level] ?? '#666';

  return (
    <div className="liquidity-risk-page">
      <div className="sub-nav-tabs">
        <button
          className={`sub-nav-tab ${activeTab === 'overview' ? 'active' : ''}`}
          onClick={() => setActiveTab('overview')}
        >
          Portfolio Liquidity Overview
        </button>
        <button
          className={`sub-nav-tab ${activeTab === 'spread' ? 'active' : ''}`}
          onClick={() => setActiveTab('spread')}
        >
          Bid-Ask Spread Analysis
        </button>
        <button
          className={`sub-nav-tab ${activeTab === 'volume' ? 'active' : ''}`}
          onClick={() => setActiveTab('volume')}
        >
          Volume Analysis
        </button>
        <button
          className={`sub-nav-tab ${activeTab === 'alerts' ? 'active' : ''}`}
          onClick={() => setActiveTab('alerts')}
        >
          Liquidity Alerts
        </button>
      </div>

      <div className="liquidity-content">
        {activeTab === 'overview' && (
          <>
            <div className="liquidity-section">
              <h2 className="section-title">Portfolio Liquidity Overview</h2>
              <div className="overview-metrics">
                <div className="metric-card">
                  <h3>Overall Liquidity Score</h3>
                  <div className="metric-value">{data.overview.overall_score}/10</div>
                </div>
                <div className="metric-card">
                  <h3>Estimated Liquidation Time</h3>
                  <div className="metric-value">{data.overview.estimated_liquidation_time}</div>
                </div>
                <div className="metric-card">
                  <h3>Risk Assessment</h3>
                  <div className="metric-value risk-level" style={{ color: riskColor }}>
                    {data.overview.risk_level} Liquidity
                  </div>
                </div>
              </div>
            </div>

            <div className="liquidity-section">
              <h2 className="section-title">Liquidity Score Distribution</h2>
              <div className="distribution-container">
                <div className="chart-container">
                  {distributionData && <Doughnut data={distributionData} options={CHART_OPTIONS} />}
                </div>
              </div>
            </div>

            <div className="liquidity-section">
              <h2 className="section-title">Position Liquidity Details</h2>
              <div className="table-container">
                <table className="liquidity-table">
                  <thead>
                    <tr>
                      <th>Ticker</th>
                      <th>Weight</th>
                      <th>Market Value</th>
                      <th>Liquidity Score</th>
                      <th>Spread</th>
                      <th>Avg Volume</th>
                      <th>Volume Category</th>
                    </tr>
                  </thead>
                  <tbody>
                    {data.position_details.map((position, index) => (
                      <tr key={index}>
                        <td className="ticker-cell">{position.ticker}</td>
                        <td>{position.weight_pct}%</td>
                        <td>${position.market_value.toLocaleString()}</td>
                        <td>{position.liquidity_score}</td>
                        <td>{position.spread_pct}%</td>
                        <td>{position.avg_volume.toLocaleString()}</td>
                        <td className={`volume-category ${position.volume_category.toLowerCase()}`}>
                          {position.volume_category}
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </div>
          </>
        )}

        {activeTab === 'spread' && (
          <div className="liquidity-section">
            <h2 className="section-title">Bid-Ask Spread Analysis</h2>
            <div className="coming-soon">
              <p>Bid-Ask spread analysis charts coming soon...</p>
            </div>
          </div>
        )}

        {activeTab === 'volume' && (
          <div className="liquidity-section">
            <h2 className="section-title">Volume Analysis</h2>
            <div className="volume-metrics">
              <div className="metric-card">
                <h3>Average Volume (Global)</h3>
                <div className="metric-value">{data.volume_analysis.avg_volume_global.toLocaleString()}</div>
              </div>
              <div className="metric-card">
                <h3>Total Portfolio Volume</h3>
                <div className="metric-value">{data.volume_analysis.total_portfolio_volume.toLocaleString()}</div>
              </div>
              <div className="metric-card">
                <h3>Volume Weighted Average</h3>
                <div className="metric-value">{data.volume_analysis.volume_weighted_avg.toLocaleString()}</div>
              </div>
            </div>
          </div>
        )}

        {activeTab === 'alerts' && (
          <div className="liquidity-section">
            <h2 className="section-title">Liquidity Alerts</h2>
            <div className="alerts-container">
              {data.alerts.length === 0 ? (
                <div className="no-alerts">
                  <p>No liquidity alerts at this time.</p>
                </div>
              ) : (
                data.alerts.map((alert, index) => (
                  <div key={index} className={`alert-item ${alert.severity.toLowerCase()}`}>
                    <span className="alert-severity">{alert.severity}</span>
                    <span className="alert-text">{alert.text}</span>
                  </div>
                ))
              )}
            </div>
          </div>
        )}
      </div>
    </div>
  );
};

export default LiquidityRiskPage;
