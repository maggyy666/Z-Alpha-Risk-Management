import React, { useEffect, useMemo, useState } from 'react';
import { Line } from 'react-chartjs-2';
import {
  Chart as ChartJS,
  CategoryScale,
  LinearScale,
  PointElement,
  LineElement,
  Title,
  Tooltip,
  Legend,
} from 'chart.js';
import apiService, { RealizedMetricsResponse, RollingMetricsResponse } from '../services/api';
import { useApiData } from '../hooks/useApiData';
import { useSession } from '../contexts/SessionContext';
import SelectableTags from '../components/SelectableTags';
import './RealizedRiskPage.css';

ChartJS.register(CategoryScale, LinearScale, PointElement, LineElement, Title, Tooltip, Legend);

const SERIES_COLORS = [
  '#4FC3F7', '#FF6B6B', '#4ECDC4', '#45B7D1', '#96CEB4', '#FFEAA7',
  '#DDA0DD', '#98D8C8', '#F7DC6F', '#BB8FCE', '#85C1E9', '#F8C471',
];

const MONTH_NAMES = [
  'Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun',
  'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec',
];

const METRIC_DISPLAY_NAMES: Record<string, string> = {
  vol: 'Rolling Volatility',
  sharpe: 'Rolling Sharpe',
  return: 'Rolling Return',
  maxdd: 'Rolling Max Drawdown',
  beta: 'Rolling Beta',
};

const TIMEFRAME_LABELS: Record<number, string> = {
  21: '21D (1M)',
  63: '63D (3M)',
  126: '126D (6M)',
  252: '252D (1Y)',
};

const formatRollingLabel = (date: string, index: number, allDates: string[]): string => {
  const d = new Date(date);
  const year = d.getFullYear();
  const month = d.getMonth();

  if (index === 0 || index === allDates.length - 1 || index % 90 === 0) {
    return `${MONTH_NAMES[month]} ${year}`;
  }
  if (index % 30 === 0) return MONTH_NAMES[month];
  if (index > 0 && new Date(allDates[index - 1]).getFullYear() !== year) {
    return year.toString();
  }
  return '';
};

const buildRollingChart = (rolling: RollingMetricsResponse) => {
  if (!rolling.datasets?.length) return null;
  const dates = rolling.datasets[0].dates;
  const labels = dates.map((d, i) => formatRollingLabel(d, i, dates));
  return {
    labels,
    datasets: rolling.datasets.map((ds, index) => ({
      label: ds.ticker,
      data: ds.values,
      borderColor: SERIES_COLORS[index % SERIES_COLORS.length],
      backgroundColor: 'transparent',
      borderWidth: 1.5,
      fill: false,
      tension: 0.1,
      borderDash: [],
      pointRadius: 0,
      pointHoverRadius: 4,
      pointHoverBackgroundColor: SERIES_COLORS[index % SERIES_COLORS.length],
      pointHoverBorderColor: '#ffffff',
      pointHoverBorderWidth: 2,
    })),
  };
};

const buildChartOptions = (selectedMetric: string, selectedTimeFrame: number) => ({
  responsive: true,
  maintainAspectRatio: false,
  plugins: {
    legend: {
      position: 'top' as const,
      labels: { color: '#ffffff', font: { size: 12 }, usePointStyle: true, padding: 10 },
    },
    title: {
      display: true,
      text: `${METRIC_DISPLAY_NAMES[selectedMetric] ?? selectedMetric} - ${TIMEFRAME_LABELS[selectedTimeFrame] ?? `${selectedTimeFrame}D`}`,
      color: '#ffffff',
      font: { size: 16, weight: 'bold' as const },
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
        title(context: Array<{ label: string }>) {
          const date = new Date(context[0].label);
          return date.toLocaleDateString('en-US', { year: 'numeric', month: 'short', day: 'numeric' });
        },
        label(context: { dataset: { label?: string }; parsed: { y: number } }) {
          const unit = selectedMetric === 'vol' ? '%' : '';
          return `${context.dataset.label || ''}: ${context.parsed.y.toFixed(2)}${unit}`;
        },
      },
    },
  },
  scales: {
    x: {
      grid: { color: '#333', drawBorder: false },
      ticks: {
        color: '#ffffff', font: { size: 11 },
        maxTicksLimit: 20, maxRotation: 0,
        autoSkip: true, autoSkipPadding: 10,
      },
    },
    y: {
      title: {
        display: true,
        text: selectedMetric === 'vol' ? 'Volatility (%)' : 'Value',
        color: '#cccccc',
        font: { size: 12, weight: 'bold' as const },
      },
      grid: { color: '#333', drawBorder: false },
      ticks: { color: '#ffffff', font: { size: 11 } },
    },
  },
  elements: { point: { hoverRadius: 4, hoverBorderWidth: 2 } },
});

const RealizedRiskPage: React.FC = () => {
  const { getCurrentUsername } = useSession();
  const username = getCurrentUsername();

  const [selectedMetric, setSelectedMetric] = useState<string>('vol');
  const [selectedTimeFrame, setSelectedTimeFrame] = useState<number>(21);
  const [selectedTickers, setSelectedTickers] = useState<string[]>(['PORTFOLIO']);
  const [availableTickers, setAvailableTickers] = useState<string[]>([]);

  // Side-effect fetch for ticker selector population. Sets initial selection
  // to PORTFOLIO + first holding so the chart has something useful by default.
  useEffect(() => {
    let cancelled = false;
    apiService
      .getUserPortfolio(username)
      .then((response) => {
        if (cancelled || !response?.portfolio_items) return;
        const tickers = response.portfolio_items.map((item) => item.ticker);
        setAvailableTickers(tickers);
        if (tickers.length > 0) {
          setSelectedTickers(['PORTFOLIO', tickers[0]]);
        }
      })
      .catch(() => { /* selector falls back to PORTFOLIO only */ });
    return () => { cancelled = true; };
  }, [username]);

  const {
    data: realizedData,
    loading: realizedLoading,
    error: realizedError,
    refetch: refetchRealized,
  } = useApiData<RealizedMetricsResponse>(
    () => apiService.getRealizedMetrics(username),
    [username],
    'Failed to load realized metrics data',
  );

  const { data: rollingData } = useApiData<RollingMetricsResponse>(
    () => apiService.getRollingMetrics(selectedMetric, selectedTimeFrame, selectedTickers, username),
    [selectedMetric, selectedTimeFrame, selectedTickers, username],
  );

  const chartOptions = useMemo(
    () => buildChartOptions(selectedMetric, selectedTimeFrame),
    [selectedMetric, selectedTimeFrame],
  );

  const rollingChart = useMemo(
    () => (rollingData ? buildRollingChart(rollingData) : null),
    [rollingData],
  );

  if (realizedLoading) {
    return (
      <div className="realized-risk-page">
        <div className="loading">Loading realized risk data...</div>
      </div>
    );
  }

  if (realizedError) {
    return (
      <div className="realized-risk-page">
        <div className="error">
          <p>{realizedError}</p>
          <button onClick={refetchRealized} className="retry-button">Retry</button>
        </div>
      </div>
    );
  }

  return (
    <div className="realized-risk-page">
      <div className="realized-risk-header">
        <h1>Realized Risk</h1>
      </div>

      {/* Realized Metrics Table */}
      <div className="realized-metrics-section">
        <div className="section-header">
          <h2>Realized Metrics</h2>
        </div>
        <div className="metrics-table-container">
          <table className="metrics-table">
            <thead>
              <tr>
                <th>Ticker</th>
                <th>Ann. Return %</th>
                <th>Ann. Vol %</th>
                <th>Sharpe</th>
                <th>Sortino</th>
                <th>Skew</th>
                <th>Kurt</th>
                <th>Max DD %</th>
                <th>VaR 95%</th>
                <th>CVaR 95%</th>
                <th>Hit Ratio</th>
                <th>Beta (SPY)</th>
                <th>Up Cap %</th>
                <th>Down Cap %</th>
                <th>Track Error</th>
                <th>Info Ratio</th>
              </tr>
            </thead>
            <tbody>
              {realizedData?.metrics.map((metric, index) => (
                <tr key={index}>
                  <td className="ticker-cell">{metric.ticker}</td>
                  <td className={metric.ann_return_pct >= 0 ? 'positive' : 'negative'}>
                    {metric.ann_return_pct?.toFixed(1) || '0.0'}
                  </td>
                  <td>{metric.volatility_pct?.toFixed(1) || '0.0'}</td>
                  <td className={metric.sharpe_ratio >= 1 ? 'positive' : 'neutral'}>
                    {metric.sharpe_ratio?.toFixed(2) || '0.00'}
                  </td>
                  <td className={metric.sortino_ratio >= 1 ? 'positive' : 'neutral'}>
                    {metric.sortino_ratio?.toFixed(2) || '0.00'}
                  </td>
                  <td>{metric.skewness?.toFixed(1) || '0.0'}</td>
                  <td>{metric.kurtosis?.toFixed(0) || '0'}</td>
                  <td className="negative">{metric.max_drawdown_pct?.toFixed(1) || '0.0'}</td>
                  <td className="negative">{metric.var_95_pct?.toFixed(1) || '0.0'}</td>
                  <td className="negative">{metric.cvar_95_pct?.toFixed(1) || '0.0'}</td>
                  <td>{metric.hit_ratio_pct?.toFixed(0) || '0'}</td>
                  <td>{metric.beta_ndx?.toFixed(2) || '0.00'}</td>
                  <td className={metric.up_capture_ndx_pct >= 100 ? 'positive' : 'neutral'}>
                    {metric.up_capture_ndx_pct?.toFixed(0) || '0'}
                  </td>
                  <td className={metric.down_capture_ndx_pct <= 100 ? 'positive' : 'negative'}>
                    {metric.down_capture_ndx_pct?.toFixed(0) || '0'}
                  </td>
                  <td>{metric.tracking_error_pct?.toFixed(1) || '0.0'}</td>
                  <td className={metric.information_ratio >= 0.5 ? 'positive' : 'neutral'}>
                    {metric.information_ratio?.toFixed(2) || '0.00'}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>

      {/* Rolling Metrics Section */}
      <div className="rolling-metrics-section">
        <div className="section-header">
          <h2>Rolling Metrics</h2>
        </div>

        <div className="rolling-controls">
          <div className="control-group">
            <label>Select Rolling Metric:</label>
            <select
              value={selectedMetric}
              onChange={(e) => setSelectedMetric(e.target.value)}
              className="metric-select"
            >
              <option value="vol">Rolling Volatility</option>
              <option value="sharpe">Rolling Sharpe</option>
              <option value="return">Rolling Return</option>
              <option value="maxdd">Rolling Max Drawdown</option>
              <option value="beta">Rolling Beta</option>
            </select>
          </div>

          <div className="control-group">
            <label>Select Time Frame:</label>
            <select
              value={selectedTimeFrame}
              onChange={(e) => setSelectedTimeFrame(Number(e.target.value))}
              className="timeframe-select"
            >
              <option value={21}>21D (1M)</option>
              <option value={63}>63D (3M)</option>
              <option value={126}>126D (6M)</option>
              <option value={252}>252D (1Y)</option>
            </select>
          </div>

          <div className="control-group">
            <SelectableTags
              title="Select Tickers"
              selectedItems={selectedTickers}
              availableItems={['PORTFOLIO', ...availableTickers]}
              onSelectionChange={setSelectedTickers}
              placeholder="Add ticker"
            />
          </div>
        </div>

        <div className="rolling-chart-container">
          {rollingData ? (
            rollingChart ? (
              <Line data={rollingChart} options={chartOptions} />
            ) : (
              <div className="chart-loading">No data available for selected metric</div>
            )
          ) : (
            <div className="chart-loading">Loading chart data...</div>
          )}
        </div>
      </div>
    </div>
  );
};

export default RealizedRiskPage;
