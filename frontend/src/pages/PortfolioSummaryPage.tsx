import React, { useEffect, useMemo } from 'react';
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
import { useApiData } from '../hooks/useApiData';
import { useSession } from '../contexts/SessionContext';
import './PortfolioSummaryPage.css';

ChartJS.register(CategoryScale, LinearScale, BarElement, Title, Tooltip, Legend);

const RISK_LEVEL_COLORS: Record<string, string> = {
  LOW: '#4caf50',
  MEDIUM: '#ff9800',
  HIGH: '#f44336',
};

const RISK_LEVEL_DESCRIPTIONS: Record<string, string> = {
  LOW: 'Portfolio has low risk levels',
  MEDIUM: 'Portfolio has moderate risk levels that should be monitored',
  HIGH: 'Portfolio has high risk levels requiring immediate attention',
};

const POSITION_COLOR = (weight: number) => {
  if (weight > 0.12) return '#f44336';
  if (weight > 0.08) return '#ff9800';
  return '#4caf50';
};

// Static -- safe to compute once at module scope, no per-render allocation.
const CHART_OPTIONS = {
  responsive: true,
  maintainAspectRatio: false,
  plugins: {
    legend: { display: false },
    tooltip: {
      backgroundColor: 'rgba(0, 0, 0, 0.9)',
      titleColor: '#ffffff',
      bodyColor: '#ffffff',
      borderColor: '#333',
      borderWidth: 1,
      cornerRadius: 6,
      callbacks: {
        label(context: { label: string; parsed: { y: number } }) {
          return `${context.label}: ${context.parsed.y.toFixed(1)}%`;
        },
      },
    },
  },
  scales: {
    x: {
      grid: { color: '#333', drawBorder: false },
      ticks: { color: '#ffffff', font: { size: 11 } },
    },
    y: {
      grid: { color: '#333', drawBorder: false },
      ticks: {
        color: '#ffffff',
        font: { size: 11 },
        callback(value: number | string) {
          return `${value}%`;
        },
      },
      title: { display: true, text: 'Weight (%)', color: '#ffffff', font: { size: 12 } },
    },
  },
};

const buildPositionsChartData = (data: PortfolioSummaryResponse) => {
  const positions = data.portfolio_positions.slice(0, 15);
  const colors = positions.map((item) => POSITION_COLOR(item.weight));
  return {
    labels: positions.map((item) => item.ticker),
    datasets: [
      {
        label: 'Position Weight (%)',
        data: positions.map((item) => item.weight),
        backgroundColor: colors,
        borderColor: colors,
        borderWidth: 1,
      },
    ],
  };
};

const PortfolioSummaryPage: React.FC = () => {
  const { getCurrentUsername } = useSession();
  const username = getCurrentUsername();

  const { data, loading, error, refetch } = useApiData<PortfolioSummaryResponse>(
    () => apiService.getPortfolioSummary(username),
    [username],
    'Failed to load portfolio summary data',
  );

  // Refetch when the user saves portfolio edits in another tab/component.
  useEffect(() => {
    const handler = () => { refetch(); };
    window.addEventListener('portfolio-updated', handler);
    return () => window.removeEventListener('portfolio-updated', handler);
  }, [refetch]);

  const chartData = useMemo(() => (data ? buildPositionsChartData(data) : null), [data]);

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
          <button onClick={refetch} className="retry-button">Retry</button>
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

  const { risk_score: rs, portfolio_overview: po, flags } = data;
  const levelColor = RISK_LEVEL_COLORS[rs.risk_level] ?? '#666';
  const levelDescription = RISK_LEVEL_DESCRIPTIONS[rs.risk_level] ?? 'Risk level assessment unavailable';

  return (
    <div className="portfolio-summary">
      <div className="portfolio-summary-header">
        <h2>Portfolio Summary</h2>
      </div>

      {/* Risk Score Section */}
      <div className="risk-score-section">
        <div className="risk-gauge-container">
          <div className="risk-score-display">
            <div className="gauge-value">{rs.overall_score}</div>
            <div className="gauge-label">Risk Score (%)</div>
            <div className="gauge-change">▼-7</div>
          </div>
          <div className="risk-scale">
            <div className="scale-gradient"></div>
            <div className="scale-marks">
              <span>0</span><span>20</span><span>40</span>
              <span>60</span><span>80</span><span>100</span>
            </div>
          </div>
        </div>

        <div className="risk-info">
          <div className="risk-level" style={{ color: levelColor }}>
            Risk Level: {rs.risk_level}
          </div>
          <div className="risk-description">{levelDescription}</div>
          <div className="overall-score">Overall Score: {rs.overall_score}%</div>
        </div>

        <div className="highest-risk">
          <div className="highest-risk-label">Highest Risk</div>
          <div className="highest-risk-component">
            {rs.highest_risk_component}
            <span className="risk-percentage">↑{rs.highest_risk_percentage}%</span>
          </div>
          <div className="high-risk-components">
            High Risk Components: {rs.high_risk_components_count}
          </div>
        </div>
      </div>

      {/* Portfolio Overview Section */}
      <div className="portfolio-overview-section">
        <div className="overview-grid">
          <div className="overview-item">
            <div className="overview-label">PORTFOLIO VALUE</div>
            <div className="overview-value">${po.total_market_value.toLocaleString()}</div>
          </div>

          <div className="overview-item">
            <div className="overview-label">TOTAL POSITIONS</div>
            <div className="overview-value">{po.total_positions}</div>
          </div>

          <div className="overview-item">
            <div className="overview-label">LARGEST POSITION</div>
            <div className="overview-value">{po.largest_position}%</div>
          </div>

          <div className="overview-item">
            <div className="overview-label">TOP 3 CONCENTRATION</div>
            <div className="overview-value">{po.top_3_concentration}%</div>
          </div>

          <div className="overview-item">
            <div className="overview-label">E-GARCH VOLATILITY</div>
            <div className={`overview-value ${flags?.high_vol ? 'metric--warning' : ''}`}>
              {po.volatility_egarch}%
              {flags?.high_vol && <span className="warning-icon">⚠️</span>}
            </div>
          </div>

          <div className="overview-item">
            <div className="overview-label">CVAR (95%)</div>
            <div className={`overview-value ${flags?.high_cvar ? 'metric--danger' : ''}`}>
              {po.cvar_percentage}%
              {flags?.high_cvar && <span className="warning-icon">⚠️</span>}
            </div>
          </div>

          <div className="overview-item">
            <div className="overview-label">CVAR ($)</div>
            <div className="overview-value">${po.cvar_usd.toLocaleString()}</div>
          </div>

          <div className="overview-item">
            <div className="overview-label">TOP RISK CONTRIBUTOR</div>
            <div className="overview-value">
              {po.top_risk_contributor.ticker} ({(po.top_risk_contributor.vol_contribution_pct || 0).toFixed(1)}%)
            </div>
          </div>
        </div>

        <div className="portfolio-positions-chart">
          <h3>Portfolio Positions</h3>
          <div className="chart-container">
            {chartData && <Bar data={chartData} options={CHART_OPTIONS} />}
          </div>
        </div>
      </div>
    </div>
  );
};

export default PortfolioSummaryPage;
