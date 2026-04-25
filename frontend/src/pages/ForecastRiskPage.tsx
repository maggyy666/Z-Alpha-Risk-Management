import React, { useMemo, useState } from 'react';
import { Bar, Doughnut } from 'react-chartjs-2';
import {
  Chart as ChartJS,
  CategoryScale,
  LinearScale,
  BarElement,
  Title,
  Tooltip,
  Legend,
  ArcElement,
} from 'chart.js';
import apiService, { ForecastRiskContributionResponse } from '../services/api';
import { useApiData } from '../hooks/useApiData';
import { useSession } from '../contexts/SessionContext';
import ForecastMetricsPage from './ForecastMetricsPage';
import './ForecastRiskPage.css';

ChartJS.register(CategoryScale, LinearScale, BarElement, Title, Tooltip, Legend, ArcElement);

type TabType = 'metrics' | 'contribution';

const DOUGHNUT_PALETTE = [
  '#36A2EB', '#FF6384', '#4BC0C0', '#FF9F40', '#9966FF',
  '#FFCD56', '#C9CBCF', '#4BC0C0', '#FF6384', '#36A2EB',
  '#FF9F40', '#9966FF', '#FFCD56', '#C9CBCF',
];

const POSITIVE_FILL = 'rgba(54, 162, 235, 0.8)';
const NEGATIVE_FILL = 'rgba(255, 99, 132, 0.8)';
const POSITIVE_BORDER = 'rgba(54, 162, 235, 1)';
const NEGATIVE_BORDER = 'rgba(255, 99, 132, 1)';

const buildMarginalChart = (data: ForecastRiskContributionResponse) => {
  const colors = data.marginal_rc_pct.map((v) => (v >= 0 ? POSITIVE_FILL : NEGATIVE_FILL));
  const borders = data.marginal_rc_pct.map((v) => (v >= 0 ? POSITIVE_BORDER : NEGATIVE_BORDER));
  return {
    labels: data.tickers,
    datasets: [
      {
        label: 'Marginal Risk Contribution (%)',
        data: data.marginal_rc_pct,
        backgroundColor: colors,
        borderColor: borders,
        borderWidth: 1,
      },
    ],
  };
};

const buildTotalChart = (data: ForecastRiskContributionResponse) => ({
  labels: data.tickers,
  datasets: [
    {
      data: data.total_rc_pct,
      backgroundColor: DOUGHNUT_PALETTE.slice(0, data.tickers.length),
      borderWidth: 2,
      borderColor: '#1a1a1a',
    },
  ],
});

const BAR_OPTIONS = {
  indexAxis: 'y' as const,
  responsive: true,
  maintainAspectRatio: false,
  plugins: {
    legend: {
      display: true,
      position: 'top' as const,
      labels: {
        color: '#ffffff',
        font: { size: 11, weight: 'bold' as const },
        usePointStyle: true,
        pointStyle: 'rect',
        generateLabels() {
          return [
            {
              text: 'Risk Contribution', fillStyle: POSITIVE_FILL, strokeStyle: POSITIVE_BORDER,
              lineWidth: 1, hidden: false, index: 0, fontColor: '#ffffff',
            },
            {
              text: 'Risk Reduction (Hedging)', fillStyle: NEGATIVE_FILL, strokeStyle: NEGATIVE_BORDER,
              lineWidth: 1, hidden: false, index: 1, fontColor: '#ffffff',
            },
          ];
        },
      },
    },
    tooltip: {
      enabled: true,
      mode: 'index' as const,
      intersect: false,
      backgroundColor: 'rgba(0, 0, 0, 0.9)',
      titleColor: '#ffffff',
      bodyColor: '#ffffff',
      borderColor: '#333',
      borderWidth: 1,
      cornerRadius: 6,
      displayColors: true,
      titleFont: { size: 14, weight: 'bold' as const },
      bodyFont: { size: 12 },
      padding: 10,
      callbacks: {
        title(context: Array<{ label: string }>) { return context[0].label; },
        label(context: { parsed: { x: number } }) {
          const v = context.parsed.x;
          return `${v < 0 ? 'Risk Reduction' : 'Risk Contribution'}: ${v.toFixed(2)}%`;
        },
      },
    },
  },
  scales: {
    x: {
      beginAtZero: true,
      title: {
        display: true, text: 'Marginal Risk Contribution (%)',
        color: '#cccccc', font: { size: 12, weight: 'bold' as const },
      },
      ticks: { color: '#cccccc', font: { size: 11 } },
      grid: { color: '#333', drawBorder: false },
    },
    y: {
      ticks: { color: '#cccccc', font: { size: 11, weight: 'bold' as const } },
      grid: { display: false },
      barThickness: 'flex',
      maxBarThickness: 50,
    },
  },
  elements: {
    point: { hoverRadius: 6, hoverBackgroundColor: POSITIVE_FILL, hoverBorderColor: '#ffffff', hoverBorderWidth: 2 },
    bar: { borderWidth: 2, borderRadius: 4, borderSkipped: false },
  },
};

const DOUGHNUT_OPTIONS = {
  responsive: true,
  maintainAspectRatio: false,
  plugins: {
    legend: {
      position: 'right' as const,
      labels: {
        color: '#cccccc', font: { size: 11 },
        padding: 15, usePointStyle: true, pointStyle: 'circle',
      },
    },
    tooltip: {
      enabled: true,
      backgroundColor: 'rgba(0, 0, 0, 0.9)',
      titleColor: '#ffffff', bodyColor: '#ffffff',
      borderColor: '#333', borderWidth: 1, cornerRadius: 6,
      displayColors: true,
      titleFont: { size: 14, weight: 'bold' as const },
      bodyFont: { size: 12 },
      padding: 10,
      callbacks: {
        title(context: Array<{ label: string }>) { return context[0].label; },
        label(context: { parsed: number }) {
          return `Risk Contribution: ${context.parsed.toFixed(2)}%`;
        },
      },
    },
  },
};

const ForecastRiskPage: React.FC = () => {
  const { getCurrentUsername } = useSession();
  const username = getCurrentUsername();
  const [activeTab, setActiveTab] = useState<TabType>('metrics');

  const { data, loading, error, refetch } = useApiData<ForecastRiskContributionResponse>(
    () => apiService.getForecastRiskContributionData('EWMA (5D)', [], true, username),
    [username],
    'Failed to load forecast risk contribution data',
  );

  const marginalChart = useMemo(() => (data ? buildMarginalChart(data) : null), [data]);
  const totalChart = useMemo(() => (data ? buildTotalChart(data) : null), [data]);

  // Dynamic height for the marginal chart -- scale with ticker count, clamped.
  const chartHeight = useMemo(() => {
    if (!data?.tickers) return 300;
    return Math.max(250, Math.min(600, 200 + data.tickers.length * 25));
  }, [data]);

  if (loading) {
    return (
      <div className="forecast-risk-page">
        <div className="loading">Loading forecast risk contribution data...</div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="forecast-risk-page">
        <div className="error">
          <p>{error}</p>
          <button onClick={refetch} className="retry-button">Retry</button>
        </div>
      </div>
    );
  }

  if (!data) {
    return (
      <div className="forecast-risk-page">
        <div className="error">No forecast risk contribution data available</div>
      </div>
    );
  }

  return (
    <div className="forecast-risk-page">
      <div className="sub-nav">
        <button
          className={`sub-nav-item ${activeTab === 'metrics' ? 'active' : ''}`}
          onClick={() => setActiveTab('metrics')}
        >
          Forecast Metrics
        </button>
        <button
          className={`sub-nav-item ${activeTab === 'contribution' ? 'active' : ''}`}
          onClick={() => setActiveTab('contribution')}
        >
          Contribution
        </button>
      </div>

      {activeTab === 'metrics' && <ForecastMetricsPage />}

      {activeTab === 'contribution' && (
        <>
          <div className="section-header">
            <h2>Forecast Risk Contribution</h2>
          </div>

          <div className="forecast-summary">
            <div className="summary-item">
              <span className="label">Portfolio Volatility:</span>
              <span className="value">{(data.portfolio_vol * 100).toFixed(2)}%</span>
            </div>
            <div className="summary-item">
              <span className="label">Model:</span>
              <span className="value">{data.vol_model}</span>
            </div>
            <div className="summary-item">
              <span className="label">Hedging Positions:</span>
              <span className="value">{data.marginal_rc_pct.filter((v) => v < 0).length}</span>
            </div>
          </div>

          <div className="charts-container">
            <div className="chart-section">
              <h3>Marginal Risk Contribution</h3>
              <div className="chart-container" style={{ height: `${chartHeight}px` }}>
                {marginalChart && <Bar data={marginalChart} options={BAR_OPTIONS} />}
              </div>
            </div>

            <div className="chart-section">
              <h3>Forecast Risk Contribution</h3>
              <div className="chart-container" style={{ height: `${Math.min(400, chartHeight)}px` }}>
                {totalChart && <Doughnut data={totalChart} options={DOUGHNUT_OPTIONS} />}
              </div>
            </div>
          </div>
        </>
      )}
    </div>
  );
};

export default ForecastRiskPage;
