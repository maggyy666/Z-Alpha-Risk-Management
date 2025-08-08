import React, { useState, useEffect, useCallback } from 'react';
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
import './LiquidityRiskPage.css';

ChartJS.register(
  CategoryScale,
  LinearScale,
  ArcElement,
  Title,
  Tooltip,
  Legend
);

const LiquidityRiskPage: React.FC = () => {
  const [data, setData] = useState<LiquidityOverviewResponse | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [activeTab, setActiveTab] = useState('overview');

  const fetchLiquidityData = useCallback(async () => {
    try {
      setLoading(true);
      const response = await apiService.getLiquidityOverview("admin");
      setData(response);
      setError(null);
    } catch (err) {
      setError('Failed to load liquidity data');
      console.error('Error fetching liquidity data:', err);
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    fetchLiquidityData();
  }, [fetchLiquidityData]);

  const getRiskLevelColor = (level: string) => {
    switch (level) {
      case 'LOW': return '#4caf50';
      case 'MEDIUM': return '#ff9800';
      case 'HIGH': return '#f44336';
      default: return '#666';
    }
  };

  const getRiskLevelDescription = (level: string) => {
    switch (level) {
      case 'LOW': return 'Portfolio has good liquidity';
      case 'MEDIUM': return 'Portfolio has moderate liquidity';
      case 'HIGH': return 'Portfolio has poor liquidity requiring attention';
      default: return 'Liquidity assessment unavailable';
    }
  };

  const createLiquidityDistributionChartData = () => {
    if (!data) return null;

    const distribution = data.distribution;
    const labels = Object.keys(distribution);
    const values = Object.values(distribution);

    // Color scale for liquidity distribution - updated for 3 buckets
    const colors = ['#2196F3', '#64B5F6', '#FF9800']; // Dark blue, light blue, orange

    return {
      labels,
      datasets: [
        {
          data: values,
          backgroundColor: colors,
          borderColor: colors.map(color => color.replace('0.8', '1')),
          borderWidth: 2,
        },
      ],
    };
  };

  const chartOptions = {
    responsive: true,
    maintainAspectRatio: false,
    plugins: {
      legend: {
        position: 'right' as const,
        labels: {
          color: '#ffffff',
          font: {
            size: 12,
          },
        },
      },
      tooltip: {
        backgroundColor: '#2a2a2a',
        titleColor: '#ffffff',
        bodyColor: '#cccccc',
        borderColor: '#333',
        borderWidth: 1,
      },
    },
  };

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
          <button onClick={fetchLiquidityData} className="retry-button">
            Retry
          </button>
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

  return (
    <div className="liquidity-risk-page">
      {/* Sub-navigation */}
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

      {/* Main Content */}
      <div className="liquidity-content">
        {activeTab === 'overview' && (
          <>
            {/* Portfolio Liquidity Overview */}
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
                  <div 
                    className="metric-value risk-level"
                    style={{ color: getRiskLevelColor(data.overview.risk_level) }}
                  >
                    {data.overview.risk_level} Liquidity
                  </div>
                </div>
              </div>
            </div>

            {/* Liquidity Score Distribution */}
            <div className="liquidity-section">
              <h2 className="section-title">Liquidity Score Distribution</h2>
              <div className="distribution-container">
                <div className="chart-container">
                  <Doughnut data={createLiquidityDistributionChartData()!} options={chartOptions} />
                </div>
              </div>
            </div>

            {/* Position Liquidity Details */}
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
