import React, { useMemo, useState } from 'react';
import { Bar, Radar } from 'react-chartjs-2';
import {
  Chart as ChartJS,
  CategoryScale,
  LinearScale,
  BarElement,
  Title,
  Tooltip,
  Legend,
  RadialLinearScale,
  PointElement,
  LineElement,
  Filler,
} from 'chart.js';
import apiService, { StressTestingResponse } from '../services/api';
import { useApiData } from '../hooks/useApiData';
import { useSession } from '../contexts/SessionContext';
import './StressTestingPage.css';

ChartJS.register(
  CategoryScale,
  LinearScale,
  BarElement,
  Title,
  Tooltip,
  Legend,
  RadialLinearScale,
  PointElement,
  LineElement,
  Filler,
);

const drawdownColor = (dd: number) => {
  if (dd > -10) return '#FFA500';
  if (dd > -20) return '#FF6347';
  if (dd > -30) return '#DC143C';
  return '#8B0000';
};

const RADAR_OPTIONS = {
  responsive: true,
  maintainAspectRatio: false,
  plugins: {
    legend: { display: false, position: 'top' as const, labels: { color: '#ffffff' } },
    tooltip: {
      backgroundColor: 'rgba(0, 0, 0, 0.9)',
      titleColor: '#ffffff',
      bodyColor: '#ffffff',
      borderColor: '#333',
      borderWidth: 1,
      cornerRadius: 6,
    },
  },
  scales: {
    r: {
      beginAtZero: true,
      max: 1,
      grid: { color: '#333' },
      angleLines: { color: '#333' },
      pointLabels: { color: '#ffffff', font: { size: 12 } },
      ticks: { color: '#ffffff', font: { size: 10 }, stepSize: 0.2 },
    },
  },
};

const BAR_OPTIONS = {
  responsive: true,
  maintainAspectRatio: false,
  indexAxis: 'y' as const,
  plugins: {
    legend: { display: false, position: 'top' as const, labels: { color: '#ffffff' } },
    tooltip: {
      backgroundColor: 'rgba(0, 0, 0, 0.9)',
      titleColor: '#ffffff',
      bodyColor: '#ffffff',
      borderColor: '#333',
      borderWidth: 1,
      cornerRadius: 6,
      callbacks: {
        label(context: { parsed: { x: number } }) {
          return `Max Drawdown: ${context.parsed.x.toFixed(1)}%`;
        },
      },
    },
  },
  scales: {
    x: {
      grid: { color: '#333', drawBorder: false },
      ticks: {
        color: '#ffffff',
        font: { size: 11 },
        callback(value: number | string) { return `${value}%`; },
      },
      title: { display: true, text: 'Max Drawdown (%)', color: '#ffffff', font: { size: 12 } },
    },
    y: {
      grid: { color: '#333', drawBorder: false },
      ticks: { color: '#ffffff', font: { size: 11 } },
    },
  },
};

const buildRadarData = (data: StressTestingResponse) => ({
  labels: ['Correlation', 'Volatility', 'Momentum'],
  datasets: [
    {
      label: 'Market Regime Indicators',
      data: [
        data.market_regime.radar?.correlation || 0,
        data.market_regime.radar?.volatility || 0,
        data.market_regime.radar?.momentum || 0,
      ],
      backgroundColor: 'rgba(54, 162, 235, 0.2)',
      borderColor: 'rgba(54, 162, 235, 1)',
      borderWidth: 2,
      pointBackgroundColor: 'rgba(54, 162, 235, 1)',
      pointBorderColor: '#fff',
      pointHoverBackgroundColor: '#fff',
      pointHoverBorderColor: 'rgba(54, 162, 235, 1)',
    },
  ],
});

const buildScenariosData = (data: StressTestingResponse) => {
  const labels = data.scenarios.results?.map((r) => r.name) || [];
  const drawdowns = data.scenarios.results?.map((r) => r.max_drawdown_pct) || [];
  const colors = drawdowns.map(drawdownColor);
  return {
    labels,
    datasets: [
      {
        label: 'Max Drawdown (%)',
        data: drawdowns,
        backgroundColor: colors,
        borderColor: colors,
        borderWidth: 1,
      },
    ],
  };
};

const StressTestingPage: React.FC = () => {
  const { getCurrentUsername } = useSession();
  const username = getCurrentUsername();
  const [showExcluded, setShowExcluded] = useState(false);

  const { data, loading, error, refetch } = useApiData<StressTestingResponse>(
    () => apiService.getStressTestingData(username),
    [username],
    'Failed to load stress testing data',
  );

  const radarData = useMemo(() => (data ? buildRadarData(data) : null), [data]);
  const scenariosData = useMemo(() => (data ? buildScenariosData(data) : null), [data]);

  if (loading) {
    return (
      <div className="stress-testing-page">
        <div className="loading">Loading stress testing data...</div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="stress-testing-page">
        <div className="error">
          <p>{error}</p>
          <button onClick={refetch} className="retry-button">Retry</button>
        </div>
      </div>
    );
  }

  if (!data) {
    return (
      <div className="stress-testing-page">
        <div className="error">No stress testing data available</div>
      </div>
    );
  }

  return (
    <div className="stress-testing-page">
      <div className="stress-testing-header">
        <h2>Stress Testing</h2>
      </div>

      {/* Market Regime Analysis */}
      <div className="market-regime-section">
        <h3>Market Regime Analysis</h3>
        <div className="regime-content">
          <div className="regime-metrics">
            <div className="regime-label">
              <span className="label-text">Current Market Regime:</span>
              <span className={`regime-status ${data.market_regime.label?.toLowerCase() || 'normal'}`}>
                {data.market_regime.label || 'Normal'}
              </span>
            </div>
            <div className="metrics-grid">
              <div className="metric-item">
                <span className="metric-label">Volatility:</span>
                <span className="metric-value">{data.market_regime.volatility_pct?.toFixed(2) || '0.00'}%</span>
              </div>
              <div className="metric-item">
                <span className="metric-label">Correlation:</span>
                <span className="metric-value">{data.market_regime.correlation?.toFixed(3) || '0.000'}</span>
              </div>
              <div className="metric-item">
                <span className="metric-label">Momentum:</span>
                <span className="metric-value">{data.market_regime.momentum_pct?.toFixed(2) || '0.00'}%</span>
              </div>
            </div>
          </div>
          <div className="radar-chart-container">
            <h4>Market Regime Indicators</h4>
            <div className="chart-container">
              {radarData && <Radar data={radarData} options={RADAR_OPTIONS} />}
            </div>
          </div>
        </div>
      </div>

      {/* Stress Scenario Tests */}
      <div className="stress-scenarios-section">
        <h3>Stress Scenario Tests</h3>
        <div className="scenarios-summary">
          <div className="summary-item">
            <span className="summary-label">Scenarios Analyzed:</span>
            <span className="summary-value">{data.scenarios.scenarios_analyzed || 0}</span>
          </div>
          <div className="summary-item">
            <span className="summary-label">Scenarios Excluded:</span>
            <span className="summary-value">{data.scenarios.scenarios_excluded || 0}</span>
          </div>
        </div>

        {data.scenarios.excluded?.length > 0 && (
          <div className="excluded-scenarios">
            <button
              className="excluded-toggle"
              onClick={() => setShowExcluded(!showExcluded)}
            >
              Excluded Scenarios {showExcluded ? '▼' : '▶'}
            </button>
            {showExcluded && (
              <div className="excluded-list">
                {data.scenarios.excluded?.map((item, index) => (
                  <div key={index} className="excluded-item">
                    <span className="excluded-name">{item.name}</span>
                    <span className="excluded-reason">{item.reason}</span>
                  </div>
                ))}
              </div>
            )}
          </div>
        )}
      </div>

      {/* Historical Scenarios */}
      <div className="historical-scenarios-section">
        <h3>Historical Scenarios</h3>
        <div className="chart-container">
          {scenariosData && <Bar data={scenariosData} options={BAR_OPTIONS} />}
        </div>
      </div>
    </div>
  );
};

export default StressTestingPage;
