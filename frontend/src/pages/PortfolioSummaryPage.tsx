import React, { useState, useEffect, useCallback } from 'react';
import { Bar } from 'react-chartjs-2';
import {
  Chart as ChartJS,
  CategoryScale,
  LinearScale,
  BarElement,
  Title,
  Tooltip,
  Legend,
} from 'chart.js';
import apiService, { PortfolioSummaryResponse } from '../services/api';
import { useSession } from '../contexts/SessionContext';
import './PortfolioSummaryPage.css';

ChartJS.register(
  CategoryScale,
  LinearScale,
  BarElement,
  Title,
  Tooltip,
  Legend
);

const PortfolioSummaryPage: React.FC = () => {
  const [data, setData] = useState<PortfolioSummaryResponse | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const { getCurrentUsername } = useSession();

  const fetchPortfolioSummary = useCallback(async () => {
    try {
      setLoading(true);
      const username = getCurrentUsername();
      const response = await apiService.getPortfolioSummary(username);
      setData(response);
      setError(null);
      
      // Log raw metrics for debugging
      console.log('🔍 Portfolio Summary Debug Info:');
      console.log('Risk Score:', response.risk_score);
      console.log('Portfolio Overview:', response.portfolio_overview);
      console.log('Raw data available in Network tab');
      
    } catch (err) {
      setError('Failed to load portfolio summary data');
      console.error('Error fetching portfolio summary:', err);
    } finally {
      setLoading(false);
    }
  }, [getCurrentUsername]);

  useEffect(() => {
    fetchPortfolioSummary();
  }, [fetchPortfolioSummary]);

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
      case 'LOW': return 'Portfolio has low risk levels';
      case 'MEDIUM': return 'Portfolio has moderate risk levels that should be monitored';
      case 'HIGH': return 'Portfolio has high risk levels requiring immediate attention';
      default: return 'Risk level assessment unavailable';
    }
  };

  const createPortfolioPositionsChartData = () => {
    if (!data) return null;

    const positions = data.portfolio_positions.slice(0, 15); // Top 15 positions
    
    // Color scale from green to red based on weight
    const colors = positions.map(item => {
      const weight = item.weight;
      if (weight > 0.12) return '#f44336'; // Red for high weights
      if (weight > 0.08) return '#ff9800'; // Orange for medium weights
      return '#4caf50'; // Green for low weights
    });

    return {
      labels: positions.map(item => item.ticker),
      datasets: [
        {
          label: 'Position Weight (%)',
          data: positions.map(item => item.weight), // Usuwam * 100 - dane już są w procentach
          backgroundColor: colors,
          borderColor: colors.map(color => color.replace('0.8', '1')),
          borderWidth: 1,
        },
      ],
    };
  };

  const chartOptions = {
    responsive: true,
    maintainAspectRatio: false,
    plugins: {
      legend: { 
        display: false
      },
      tooltip: {
        backgroundColor: 'rgba(0, 0, 0, 0.9)',
        titleColor: '#ffffff',
        bodyColor: '#ffffff',
        borderColor: '#333',
        borderWidth: 1,
        cornerRadius: 6,
        callbacks: {
          label: function(context: any) {
            return `${context.label}: ${context.parsed.y.toFixed(1)}%`;
          }
        }
      }
    },
    scales: {
      x: { 
        grid: { color: '#333', drawBorder: false }, 
        ticks: { 
          color: '#ffffff', 
          font: { size: 11 }
        }
      },
      y: {
        grid: { color: '#333', drawBorder: false },
        ticks: { 
          color: '#ffffff', 
          font: { size: 11 },
          callback: function(value: any) { 
            return value + '%'; 
          }
        },
        title: {
          display: true,
          text: 'Weight (%)',
          color: '#ffffff',
          font: { size: 12 }
        }
      }
    }
  };

  if (loading) {
    return (
      <div className="portfolio-summary">
        <div className="loading">Loading portfolio summary...</div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="portfolio-summary">
        <div className="error">
          <p>{error}</p>
          <button onClick={fetchPortfolioSummary} className="retry-button">
            Retry
          </button>
        </div>
      </div>
    );
  }

  if (!data) {
    return (
      <div className="portfolio-summary">
        <div className="error">No portfolio summary data available</div>
      </div>
    );
  }

  return (
    <div className="portfolio-summary">
      <div className="portfolio-summary-header">
        <h2>Portfolio Summary</h2>
      </div>

      {/* Risk Score Section */}
      <div className="risk-score-section">
        <div className="risk-gauge-container">
          <div className="risk-score-display" title={`Raw metrics and scores available in console`}>
            <div className="gauge-value">{data.risk_score.overall_score}</div>
            <div className="gauge-label">Risk Score (%)</div>
            <div className="gauge-change">▼-7</div>
          </div>
          <div className="risk-scale">
            <div className="scale-gradient"></div>
            <div className="scale-marks">
              <span>0</span>
              <span>20</span>
              <span>40</span>
              <span>60</span>
              <span>80</span>
              <span>100</span>
            </div>
          </div>
        </div>
        
        <div className="risk-info">
          <div className="risk-level" style={{ color: getRiskLevelColor(data.risk_score.risk_level) }}>
            Risk Level: {data.risk_score.risk_level}
          </div>
          <div className="risk-description">
            {getRiskLevelDescription(data.risk_score.risk_level)}
          </div>
          <div className="overall-score">
            Overall Score: {data.risk_score.overall_score}%
          </div>
        </div>

        <div className="highest-risk">
          <div className="highest-risk-label">Highest Risk</div>
          <div className="highest-risk-component">
            {data.risk_score.highest_risk_component}
            <span className="risk-percentage">↑{data.risk_score.highest_risk_percentage}%</span>
          </div>
          <div className="high-risk-components">
            High Risk Components: {data.risk_score.high_risk_components_count}
          </div>
        </div>
      </div>

      {/* Portfolio Overview Section */}
      <div className="portfolio-overview-section">
        <div className="overview-grid">
          <div className="overview-item">
            <div className="overview-label">PORTFOLIO VALUE</div>
            <div className="overview-value">
              ${data.portfolio_overview.total_market_value.toLocaleString()}
            </div>
          </div>
          
          <div className="overview-item">
            <div className="overview-label">TOTAL POSITIONS</div>
            <div className="overview-value">{data.portfolio_overview.total_positions}</div>
          </div>
          
          <div className="overview-item">
            <div className="overview-label">LARGEST POSITION</div>
            <div className="overview-value">{data.portfolio_overview.largest_position}%</div>
          </div>
          
          <div className="overview-item">
            <div className="overview-label">TOP 3 CONCENTRATION</div>
            <div className="overview-value">{data.portfolio_overview.top_3_concentration}%</div>
          </div>
          
          <div className="overview-item">
            <div className="overview-label">E-GARCH VOLATILITY</div>
            <div className={`overview-value ${data.flags?.high_vol ? 'metric--warning' : ''}`}>
              {data.portfolio_overview.volatility_egarch}%
              {data.flags?.high_vol && <span className="warning-icon">⚠️</span>}
            </div>
          </div>
          
          <div className="overview-item">
            <div className="overview-label">CVAR (95%)</div>
            <div className={`overview-value ${data.flags?.high_cvar ? 'metric--danger' : ''}`}>
              {data.portfolio_overview.cvar_percentage}%
              {data.flags?.high_cvar && <span className="warning-icon">⚠️</span>}
            </div>
          </div>
          
          <div className="overview-item">
            <div className="overview-label">CVAR ($)</div>
            <div className="overview-value">
              ${data.portfolio_overview.cvar_usd.toLocaleString()}
            </div>
          </div>
          
          <div className="overview-item">
            <div className="overview-label">TOP RISK CONTRIBUTOR</div>
            <div className="overview-value">
              {data.portfolio_overview.top_risk_contributor.ticker} ({(data.portfolio_overview.top_risk_contributor.vol_contribution_pct || 0).toFixed(1)}%)
            </div>
          </div>
        </div>
        
        {/* Portfolio Positions Chart - pod statystykami */}
        <div className="portfolio-positions-chart">
          <h3>Portfolio Positions</h3>
          <div className="chart-container">
            {createPortfolioPositionsChartData() && (
              <Bar data={createPortfolioPositionsChartData()!} options={chartOptions} />
            )}
          </div>
        </div>
      </div>
    </div>
  );
};

export default PortfolioSummaryPage;
