import React, { useMemo, useState } from 'react';
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
import apiService, {
  ForecastMetricsResponse,
  RollingForecastResponse,
} from '../services/api';
import { useApiData } from '../hooks/useApiData';
import { useDebouncedValue } from '../hooks/useDebouncedValue';
import { useSession } from '../contexts/SessionContext';
import SelectableTags from '../components/SelectableTags';
import './ForecastMetricsPage.css';

ChartJS.register(CategoryScale, LinearScale, PointElement, LineElement, Title, Tooltip, Legend);

const SERIES_COLORS = [
  '#4FC3F7', '#FF6B6B', '#4ECDC4', '#45B7D1', '#96CEB4', '#FFEAA7',
  '#DDA0DD', '#98D8C8', '#F7DC6F', '#BB8FCE', '#85C1E9', '#F8C471',
];

const MONTH_NAMES = [
  'Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun',
  'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec',
];

// Compress dense daily x-axis labels: full date every 90 days, month name
// every 30, year on year-boundary, blank otherwise.
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

const buildRollingChart = (rolling: RollingForecastResponse) => {
  const tickerData: Record<string, { dates: string[]; vols: number[] }> = {};
  rolling.data.forEach((item) => {
    if (!tickerData[item.ticker]) tickerData[item.ticker] = { dates: [], vols: [] };
    tickerData[item.ticker].dates.push(item.date);
    tickerData[item.ticker].vols.push(item.vol_pct);
  });

  const datasets = Object.keys(tickerData).map((ticker, index) => ({
    label: ticker,
    data: tickerData[ticker].vols,
    borderColor: SERIES_COLORS[index % SERIES_COLORS.length],
    backgroundColor: 'transparent',
    borderWidth: 1.5,
    fill: false,
    tension: 0.1,
    borderDash: index % 2 === 0 ? [] : [5, 5],
    pointRadius: 0,
    pointHoverRadius: 4,
    pointHoverBackgroundColor: SERIES_COLORS[index % SERIES_COLORS.length],
    pointHoverBorderColor: '#ffffff',
    pointHoverBorderWidth: 2,
  }));

  // Common dates = intersection across all tickers (so all series render aligned).
  const allTickers = Object.keys(tickerData);
  let commonDates: string[] = [];
  if (allTickers.length > 0) {
    commonDates = tickerData[allTickers[0]].dates;
    for (let i = 1; i < allTickers.length; i++) {
      const dates = tickerData[allTickers[i]].dates;
      commonDates = commonDates.filter((d) => dates.includes(d));
    }
  }

  return {
    labels: commonDates.map((date, i) => formatRollingLabel(date, i, commonDates)),
    datasets,
  };
};

const CHART_OPTIONS = {
  responsive: true,
  maintainAspectRatio: false,
  plugins: {
    legend: {
      position: 'top' as const,
      labels: { color: '#ffffff', font: { size: 12 }, usePointStyle: true, padding: 10 },
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
          return `${context.dataset.label || ''}: ${context.parsed.y.toFixed(2)}%`;
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
        maxTicksLimit: 20,
        maxRotation: 0,
        autoSkip: true,
        autoSkipPadding: 10,
      },
    },
    y: {
      title: { display: true, text: 'Volatility (%)', color: '#cccccc' },
      grid: { color: '#333', drawBorder: false },
      ticks: { color: '#ffffff', font: { size: 11 } },
    },
  },
  elements: {
    point: { hoverRadius: 4, hoverBorderWidth: 2 },
  },
};

const AVAILABLE_TICKERS = ['PORTFOLIO', 'DOMO', 'AMD', 'GOOGL', 'META', 'TSLA'];

const ForecastMetricsPage: React.FC = () => {
  const { getCurrentUsername } = useSession();
  const username = getCurrentUsername();

  const [selectedModel, setSelectedModel] = useState<string>('EGARCH');
  const [selectedWindow, setSelectedWindow] = useState<number>(21);
  const [selectedTickers, setSelectedTickers] = useState<string[]>(['PORTFOLIO', 'DOMO']);

  // Debounce + clamp the window value before it drives the network fetch.
  // The input is type=number so users typing "21" briefly emit "2", which
  // would 422 against the backend's `ge=5` validator on every keystroke.
  const debouncedWindow = useDebouncedValue(selectedWindow, 400);
  const safeWindow = Math.max(5, Math.min(252, debouncedWindow || 5));

  const {
    data: metricsData,
    loading: metricsLoading,
    error: metricsError,
    refetch: refetchMetrics,
  } = useApiData<ForecastMetricsResponse>(
    () => apiService.getForecastMetrics(username),
    [username],
    'Failed to load forecast metrics data',
  );

  const { data: rollingData } = useApiData<RollingForecastResponse>(
    () => apiService.getRollingForecast(selectedModel, safeWindow, selectedTickers, username),
    [selectedModel, safeWindow, selectedTickers, username],
  );

  const rollingChart = useMemo(
    () => (rollingData ? buildRollingChart(rollingData) : null),
    [rollingData],
  );

  if (metricsLoading) {
    return (
      <div className="forecast-metrics-page">
        <div className="loading">Loading forecast metrics data...</div>
      </div>
    );
  }

  if (metricsError) {
    return (
      <div className="forecast-metrics-page">
        <div className="error">
          <p>{metricsError}</p>
          <button onClick={refetchMetrics} className="retry-button">Retry</button>
        </div>
      </div>
    );
  }

  if (!metricsData) {
    return (
      <div className="forecast-metrics-page">
        <div className="error">No forecast metrics data available</div>
      </div>
    );
  }

  return (
    <div className="forecast-metrics-page">
      <div className="forecast-metrics-section">
        <h2>Forecast Metrics</h2>
        <div className="table-container">
          <table className="forecast-table">
            <thead>
              <tr>
                <th>Ticker</th>
                <th>EWMA (5D)</th>
                <th>EWMA (200)</th>
                <th>Garch Volatility</th>
                <th>E-Garch Volatility</th>
                <th>VaR (95%)</th>
                <th>CVaR (95%)</th>
                <th>VaR ($)</th>
                <th>CVaR ($)</th>
              </tr>
            </thead>
            <tbody>
              {metricsData.metrics.map((metric, index) => (
                <tr key={index}>
                  <td>{metric.ticker}</td>
                  <td>{metric.ewma5_pct.toFixed(2)}%</td>
                  <td>{metric.ewma20_pct.toFixed(2)}%</td>
                  <td>{metric.garch_vol_pct.toFixed(2)}%</td>
                  <td>{metric.egarch_vol_pct.toFixed(2)}%</td>
                  <td>{metric.var_pct.toFixed(2)}%</td>
                  <td>{metric.cvar_pct.toFixed(2)}%</td>
                  <td>${Math.abs(metric.var_usd).toFixed(0)}</td>
                  <td>${Math.abs(metric.cvar_usd).toFixed(0)}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>

      <div className="rolling-forecast-section">
        <h2>Rolling Forecast Metrics</h2>

        <div className="controls">
          <div className="control-group">
            <label>SELECT MODEL:</label>
            <select
              value={selectedModel}
              onChange={(e) => setSelectedModel(e.target.value)}
              className="model-select"
              style={{ height: 'clamp(32px, 5vw, 36px)', minHeight: 'clamp(32px, 5vw, 36px)' }}
            >
              <option value="EWMA (5D)">EWMA (5D)</option>
              <option value="EWMA (30D)">EWMA (30D)</option>
              <option value="EWMA (200D)">EWMA (200D)</option>
              <option value="GARCH">GARCH</option>
              <option value="EGARCH">EGARCH</option>
            </select>
          </div>

          <div className="control-group">
            <label>SELECT TIME FRAME:</label>
            <input
              type="number"
              value={selectedWindow}
              onChange={(e) => setSelectedWindow(Number(e.target.value))}
              min="5"
              max="252"
              className="timeframe-input"
              style={{ height: 'clamp(32px, 5vw, 36px)', minHeight: 'clamp(32px, 5vw, 36px)' }}
            />
          </div>

          <div className="control-group">
            <SelectableTags
              title="SELECT TICKERS"
              selectedItems={selectedTickers}
              availableItems={AVAILABLE_TICKERS}
              onSelectionChange={setSelectedTickers}
              placeholder="Add ticker"
            />
          </div>
        </div>

        <div className="chart-container" style={{ width: '100%', height: '400px', minWidth: '100%' }}>
          {rollingChart && (
            <Line
              key={`${selectedModel}-${safeWindow}-${selectedTickers.join(',')}`}
              data={rollingChart}
              options={CHART_OPTIONS}
            />
          )}
        </div>
      </div>
    </div>
  );
};

export default ForecastMetricsPage;
