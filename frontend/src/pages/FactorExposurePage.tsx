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
  Filler,
} from 'chart.js';
import apiService, {
  FactorExposureData,
  FactorExposureResponse,
  LatestFactorExposuresResponse,
} from '../services/api';
import { useApiData } from '../hooks/useApiData';
import { useSession } from '../contexts/SessionContext';
import SelectableTags from '../components/SelectableTags';
import './FactorExposurePage.css';

ChartJS.register(CategoryScale, LinearScale, PointElement, LineElement, Title, Tooltip, Legend, Filler);

const SERIES_COLORS = [
  '#4FC3F7', '#FF6B6B', '#4ECDC4', '#45B7D1', '#96CEB4', '#FFEAA7',
  '#DDA0DD', '#98D8C8', '#F7DC6F', '#BB8FCE', '#85C1E9', '#F8C471',
];

const MONTH_NAMES = [
  'Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun',
  'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec',
];

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
          const label = context[0].label;
          if (!label) return 'No date';
          try {
            const date = new Date(label);
            if (isNaN(date.getTime())) return label;
            return date.toLocaleDateString('en-US', { year: 'numeric', month: 'short', day: 'numeric' });
          } catch {
            return label;
          }
        },
        label(context: { dataset: { label?: string }; parsed: { y: number | null } }) {
          const label = context.dataset.label || '';
          const value = context.parsed.y;
          if (value === null || value === undefined) return `${label}: No data`;
          return `${label}: ${value.toFixed(3)}`;
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
      grid: { color: '#333', drawBorder: false },
      ticks: { color: '#ffffff', font: { size: 11 } },
    },
  },
  elements: {
    point: {
      radius: 0, hoverRadius: 6,
      hoverBackgroundColor: '#ffffff', hoverBorderColor: '#333', hoverBorderWidth: 2,
    },
    line: { borderWidth: 2, tension: 0.1 },
  },
  interaction: { mode: 'index' as const, intersect: false },
};

const PREFERRED_DEFAULT_TICKERS = ['GOOGL', 'META'];

// Centered moving average over `r2` field. Used to dampen the rolling-OLS
// noise on the R² panel; toggleable from the UI.
const smoothR2 = (data: FactorExposureData[], windowSize = 5): FactorExposureData[] => {
  if (data.length < windowSize) return data;
  const half = Math.floor(windowSize / 2);
  return data.map((point, i) => {
    const window = data.slice(Math.max(0, i - half), Math.min(data.length, i + half + 1));
    const valid = window.filter((it) => it.r2 !== undefined);
    const avg = valid.length > 0
      ? valid.reduce((sum, it) => sum + (it.r2 || 0), 0) / valid.length
      : (point.r2 || 0);
    return { ...point, r2: avg };
  });
};

interface BetaChartArgs {
  data: FactorExposureData[];
  selectedFactors: string[];
  selectedTickers: string[];
}

const buildBetaChart = ({ data, selectedFactors, selectedTickers }: BetaChartArgs) => {
  if (selectedFactors.length === 0 || selectedTickers.length === 0) {
    return { labels: [], datasets: [] };
  }

  // Union of all dates across selected (ticker, factor) combos so every
  // dataset is plotted on the same x-axis.
  const allDatesSet = new Set<string>();
  for (const ticker of selectedTickers) {
    for (const factor of selectedFactors) {
      data
        .filter((d) => d.ticker === ticker && d.factor === factor)
        .forEach((d) => allDatesSet.add(d.date));
    }
  }
  const allDates = Array.from(allDatesSet).sort();

  const datasets = selectedFactors.flatMap((factor, fIdx) =>
    selectedTickers.map((ticker, tIdx) => {
      const series = data
        .filter((d) => d.factor === factor && d.ticker === ticker)
        .sort((a, b) => new Date(a.date).getTime() - new Date(b.date).getTime());
      if (series.length === 0) return null;
      const colorIndex = (fIdx * selectedTickers.length + tIdx) % SERIES_COLORS.length;
      const dataMap = new Map(series.map((d) => [d.date, d.beta] as const));
      return {
        label: `${factor}, ${ticker}`,
        data: allDates.map((date) => dataMap.get(date) ?? null),
        borderColor: SERIES_COLORS[colorIndex],
        backgroundColor: 'transparent',
        borderWidth: 1.5,
        fill: false,
        tension: 0.1,
        borderDash: tIdx % 2 === 0 ? [] : [5, 5],
        pointRadius: 0,
        pointHoverRadius: 4,
        pointHoverBackgroundColor: SERIES_COLORS[colorIndex],
        pointHoverBorderColor: '#ffffff',
        pointHoverBorderWidth: 2,
      };
    }).filter((d): d is NonNullable<typeof d> => d !== null),
  );

  return {
    labels: allDates.map((date, i) => formatRollingLabel(date, i, allDates)),
    datasets,
  };
};

interface R2ChartArgs {
  data: FactorExposureData[];
  selectedTickers: string[];
  smoothing: boolean;
}

const buildR2Chart = ({ data, selectedTickers, smoothing }: R2ChartArgs) => {
  if (selectedTickers.length === 0) return { labels: [], datasets: [] };

  const allDatesSet = new Set<string>();
  for (const ticker of selectedTickers) {
    data.filter((d) => d.ticker === ticker).forEach((d) => allDatesSet.add(d.date));
  }
  const allDates = Array.from(allDatesSet).sort();

  const datasets = selectedTickers
    .map((ticker, idx) => {
      const series = data
        .filter((d) => d.ticker === ticker)
        .sort((a, b) => new Date(a.date).getTime() - new Date(b.date).getTime());
      if (series.length === 0) return null;
      const smoothed = smoothing ? smoothR2(series, 7) : series;
      const dataMap = new Map(smoothed.map((d) => [d.date, d.r2] as const));
      return {
        label: ticker,
        data: allDates.map((date) => dataMap.get(date) ?? null),
        borderColor: SERIES_COLORS[idx % SERIES_COLORS.length],
        backgroundColor: 'transparent',
        borderWidth: 2,
        fill: false,
        tension: 0.2,
        pointRadius: 0,
        pointHoverRadius: 4,
        pointHoverBackgroundColor: SERIES_COLORS[idx % SERIES_COLORS.length],
        pointHoverBorderColor: '#ffffff',
        pointHoverBorderWidth: 2,
      };
    })
    .filter((d): d is NonNullable<typeof d> => d !== null);

  return {
    labels: allDates.map((date, i) => formatRollingLabel(date, i, allDates)),
    datasets,
  };
};

interface LatestSectionProps {
  data: LatestFactorExposuresResponse | null;
  loading: boolean;
  error: string | null;
  onRetry: () => void;
}

const LatestFactorExposuresSection: React.FC<LatestSectionProps> = ({ data, loading, error, onRetry }) => {
  if (loading) {
    return <div className="section"><div className="loading">Loading latest factor exposures...</div></div>;
  }
  if (error) {
    return (
      <div className="section">
        <div className="error">
          <p>{error}</p>
          <button onClick={onRetry} className="retry-button">Retry</button>
        </div>
      </div>
    );
  }
  if (!data?.data) {
    return <div className="section"><div className="error">No latest factor exposures data available</div></div>;
  }

  return (
    <>
      <div className="section">
        <div className="section-header">
          <h2>Latest Factor Exposures</h2>
          {data.as_of && (
            <p className="as-of-date">Exposures as of {new Date(data.as_of).toLocaleDateString()}</p>
          )}
        </div>
        <div className="table-container">
          <table className="factor-exposure-table">
            <thead>
              <tr>
                <th>Ticker</th>
                {data.factors?.map((factor) => <th key={factor}>{factor}</th>)}
              </tr>
            </thead>
            <tbody>
              {data.data?.map((row, index) => (
                <tr key={index}>
                  <td className="ticker-cell">{row.ticker as string}</td>
                  {data.factors?.map((factor) => {
                    const value = row[factor];
                    const isPositive = typeof value === 'number' && value > 0;
                    const isNegative = typeof value === 'number' && value < 0;
                    return (
                      <td
                        key={factor}
                        className={`beta-cell ${isPositive ? 'positive' : ''} ${isNegative ? 'negative' : ''}`}
                      >
                        {typeof value === 'number' ? value.toFixed(2) : value}
                      </td>
                    );
                  })}
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>

      {/* Heatmap of Latest Exposures */}
      <div className="section">
        <div className="section-header">
          <h2>Heatmap of Latest Exposures</h2>
        </div>
        <div className="heatmap-container">
          <div className="heatmap">
            <div className="heatmap-header">
              <div className="heatmap-corner"></div>
              {data.factors?.map((factor) => (
                <div key={factor} className="heatmap-factor-header">{factor}</div>
              ))}
            </div>

            {data.data?.map((row, rowIndex) => (
              <div key={rowIndex} className="heatmap-row">
                <div className="heatmap-ticker-label">{row.ticker as string}</div>
                {data.factors?.map((factor, colIndex) => {
                  const value = row[factor];
                  if (typeof value !== 'number') {
                    return (
                      <div key={colIndex} className="heatmap-cell"
                        style={{ backgroundColor: '#2a2a2a', color: '#cccccc' }}>{String(value)}</div>
                    );
                  }
                  const normalized = Math.max(-1, Math.min(1, value));
                  const intensity = Math.abs(normalized);
                  let backgroundColor = '#1a1a1a';
                  let textColor = '#ffffff';
                  if (normalized > 0) {
                    backgroundColor = `rgb(0, ${Math.round(76 + 179 * intensity)}, 0)`;
                  } else if (normalized < 0) {
                    backgroundColor = `rgb(${Math.round(244 + 11 * intensity)}, 0, 0)`;
                  } else {
                    backgroundColor = '#2a2a2a';
                    textColor = '#cccccc';
                  }
                  return (
                    <div
                      key={colIndex}
                      className="heatmap-cell"
                      style={{ backgroundColor, color: textColor, fontWeight: intensity > 0.3 ? 700 : 600 }}
                      title={`${row.ticker} - ${factor}: ${value.toFixed(2)}`}
                    >
                      {value.toFixed(2)}
                    </div>
                  );
                })}
              </div>
            ))}
          </div>

          <div className="heatmap-legend">
            <div className="legend-title">Beta</div>
            <div className="legend-gradient">
              <div className="legend-color" style={{ backgroundColor: '#f44336', color: '#ffffff' }}>-1</div>
              <div className="legend-color" style={{ backgroundColor: '#2a2a2a', color: '#cccccc' }}>0</div>
              <div className="legend-color" style={{ backgroundColor: '#4caf50', color: '#ffffff' }}>+1</div>
            </div>
          </div>
        </div>
      </div>
    </>
  );
};

const FactorExposurePage: React.FC = () => {
  const { getCurrentUsername } = useSession();
  const username = getCurrentUsername();

  const [activeTab, setActiveTab] = useState<'charts' | 'latest'>('charts');
  const [selectedFactors, setSelectedFactors] = useState<string[]>([]);
  const [selectedTickers, setSelectedTickers] = useState<string[]>([]);
  const [selectedTickersR2, setSelectedTickersR2] = useState<string[]>([]);
  const [r2Smoothing, setR2Smoothing] = useState<boolean>(true);

  const { data: factorData, loading, error } = useApiData<FactorExposureResponse>(
    () => apiService.getFactorExposureData(username),
    [username],
    'Failed to fetch factor exposure data',
  );

  const {
    data: latestExposuresData,
    loading: latestExposuresLoading,
    error: latestExposuresError,
    refetch: refetchLatest,
  } = useApiData<LatestFactorExposuresResponse>(
    () => apiService.getLatestFactorExposures(username),
    [username],
    'Failed to fetch latest factor exposures data',
  );

  // Initialize default selections once factor data first arrives.
  useEffect(() => {
    if (!factorData) return;
    if (selectedTickers.length === 0 && factorData.available_tickers?.length > 0) {
      const preferred = PREFERRED_DEFAULT_TICKERS.filter((t) => factorData.available_tickers.includes(t));
      const defaults = preferred.length > 0 ? preferred : factorData.available_tickers.slice(0, 2);
      setSelectedTickers(defaults);
      setSelectedTickersR2(defaults);
    }
    if (selectedFactors.length === 0 && factorData.available_factors?.length > 0) {
      setSelectedFactors([factorData.available_factors[0]]);
    }
    // Run only when factorData identity changes -- subsequent UI selections
    // shouldn't reset themselves.
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [factorData]);

  const betaChart = useMemo(
    () => (factorData
      ? buildBetaChart({
        data: factorData.factor_exposures || [],
        selectedFactors,
        selectedTickers,
      })
      : { labels: [], datasets: [] }),
    [factorData, selectedFactors, selectedTickers],
  );

  const r2Chart = useMemo(
    () => (factorData
      ? buildR2Chart({
        data: factorData.r2_data || [],
        selectedTickers: selectedTickersR2,
        smoothing: r2Smoothing,
      })
      : { labels: [], datasets: [] }),
    [factorData, selectedTickersR2, r2Smoothing],
  );

  if (loading) {
    return (
      <div className="factor-exposure-page">
        <div className="loading">Loading factor exposure data...</div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="factor-exposure-page">
        <div className="error">{error}</div>
      </div>
    );
  }

  return (
    <div className="factor-exposure-page">
      <div className="sub-nav">
        <button
          className={`sub-nav-item ${activeTab === 'charts' ? 'active' : ''}`}
          onClick={() => setActiveTab('charts')}
        >
          Rolling Charts
        </button>
        <button
          className={`sub-nav-item ${activeTab === 'latest' ? 'active' : ''}`}
          onClick={() => setActiveTab('latest')}
        >
          Latest Exposures
        </button>
      </div>

      {activeTab === 'charts' && (
        <>
          <div className="section">
            <div className="section-header">
              <h2>Rolling Factor Exposures</h2>
              <div className="controls">
                <SelectableTags
                  title="Select Factors"
                  selectedItems={selectedFactors}
                  availableItems={factorData?.available_factors || []}
                  onSelectionChange={setSelectedFactors}
                  placeholder="Add factor"
                />
                <SelectableTags
                  title="Select Tickers"
                  selectedItems={selectedTickers}
                  availableItems={factorData?.available_tickers || []}
                  onSelectionChange={setSelectedTickers}
                  placeholder="Add ticker"
                />
              </div>
            </div>
            <div className="chart-container">
              <Line data={betaChart} options={CHART_OPTIONS} />
            </div>
          </div>

          <div className="section">
            <div className="section-header">
              <h2>Rolling R²</h2>
              <div className="controls">
                <SelectableTags
                  title="Select Tickers for R²"
                  selectedItems={selectedTickersR2}
                  availableItems={factorData?.available_tickers || []}
                  onSelectionChange={setSelectedTickersR2}
                  placeholder="Add ticker"
                />
                <div className="control-group">
                  <label>R² Smoothing</label>
                  <div className="smoothing-toggle">
                    <input
                      type="checkbox"
                      id="r2-smoothing"
                      checked={r2Smoothing}
                      onChange={(e) => setR2Smoothing(e.target.checked)}
                    />
                    <label htmlFor="r2-smoothing">Enable Smoothing</label>
                  </div>
                </div>
              </div>
            </div>
            <div className="chart-container">
              <Line data={r2Chart} options={CHART_OPTIONS} />
            </div>
          </div>
        </>
      )}

      {activeTab === 'latest' && (
        <LatestFactorExposuresSection
          data={latestExposuresData}
          loading={latestExposuresLoading}
          error={latestExposuresError}
          onRetry={refetchLatest}
        />
      )}
    </div>
  );
};

export default FactorExposurePage;
