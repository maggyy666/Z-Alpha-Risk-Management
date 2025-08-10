import React, { useState, useEffect, useCallback } from 'react';
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
import { useSession } from '../contexts/SessionContext';
import SelectableTags from '../components/SelectableTags';
import './RealizedRiskPage.css';

ChartJS.register(
  CategoryScale,
  LinearScale,
  PointElement,
  LineElement,
  Title,
  Tooltip,
  Legend
);

const RealizedRiskPage: React.FC = () => {
  const [realizedData, setRealizedData] = useState<RealizedMetricsResponse | null>(null);
  const [rollingData, setRollingData] = useState<RollingMetricsResponse | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [availableTickers, setAvailableTickers] = useState<string[]>([]);
  const { getCurrentUsername } = useSession();
  
  // Rolling metrics controls
  const [selectedMetric, setSelectedMetric] = useState<string>("vol");
  const [selectedTimeFrame, setSelectedTimeFrame] = useState<number>(21);
  const [selectedTickers, setSelectedTickers] = useState<string[]>(["PORTFOLIO"]);

  const fetchAvailableTickers = useCallback(async () => {
    try {
      const username = getCurrentUsername();
      const response = await apiService.getUserPortfolio(username);
      if (response && response.portfolio_items) {
        const tickers = response.portfolio_items.map((item: any) => item.ticker);
        setAvailableTickers(tickers);
        
        // Automatycznie wybierz PORTFOLIO + pierwszy ticker z portfolio
        if (tickers.length > 0) {
          setSelectedTickers(["PORTFOLIO", tickers[0]]);
        }
      }
    } catch (err) {
      console.error('Error fetching available tickers:', err);
    }
  }, [getCurrentUsername]);

  const fetchRealizedData = useCallback(async () => {
    try {
      setLoading(true);
      const username = getCurrentUsername();
      const response = await apiService.getRealizedMetrics(username);
      setRealizedData(response);
      setError(null);
    } catch (err) {
      setError('Failed to load realized metrics data');
      console.error('Error fetching realized metrics:', err);
    } finally {
      setLoading(false);
    }
  }, [getCurrentUsername]);

  const fetchRollingData = useCallback(async () => {
    try {
      const username = getCurrentUsername();
      const response = await apiService.getRollingMetrics(
        selectedMetric,
        selectedTimeFrame,
        selectedTickers.length > 0 ? selectedTickers : ["PORTFOLIO"],
        username
      );
      setRollingData(response);
    } catch (err) {
      console.error('Error fetching rolling metrics:', err);
    }
  }, [selectedMetric, selectedTimeFrame, selectedTickers, getCurrentUsername]);

  useEffect(() => {
    fetchAvailableTickers();
    fetchRealizedData();
  }, [fetchAvailableTickers, fetchRealizedData]);

  useEffect(() => {
    fetchRollingData();
  }, [fetchRollingData]);

  const getMetricDisplayName = (metric: string) => {
    switch (metric) {
      case "vol": return "Rolling Volatility";
      case "sharpe": return "Rolling Sharpe";
      case "return": return "Rolling Return";
      case "maxdd": return "Rolling Max Drawdown";
      case "beta": return "Rolling Beta";
      default: return metric;
    }
  };

  const getTimeFrameDisplayName = (window: number) => {
    switch (window) {
      case 21: return "21D (1M)";
      case 63: return "63D (3M)";
      case 126: return "126D (6M)";
      case 252: return "252D (1Y)";
      default: return `${window}D`;
    }
  };

  const createRollingChartData = () => {
    if (!rollingData || !rollingData.datasets || rollingData.datasets.length === 0) return null;

    // Większa paleta kolorów dla lepszego rozróżnienia
    const colors = [
      '#4FC3F7', // Jasny niebieski
      '#FF6B6B', // Czerwony
      '#4ECDC4', // Turkusowy
      '#45B7D1', // Ciemny niebieski
      '#96CEB4', // Zielony
      '#FFEAA7', // Żółty
      '#DDA0DD', // Fioletowy
      '#98D8C8', // Mint
      '#F7DC6F', // Złoty
      '#BB8FCE', // Lawenda
      '#85C1E9', // Błękitny
      '#F8C471'  // Pomarańczowy
    ];

    // Użyj dat z pierwszego datasetu (wszystkie powinny mieć te same daty)
    const firstDataset = rollingData.datasets[0];
    const labels = firstDataset.dates.map((date, index) => {
      const dateObj = new Date(date);
      const year = dateObj.getFullYear();
      const month = dateObj.getMonth();
      const day = dateObj.getDate();
      
      // Pokaż pełną datę co 3 miesiące (jak w Factor Exposure)
      if (index === 0 || index === firstDataset.dates.length - 1 || index % 90 === 0) {
        const monthNames = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 
                           'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec'];
        return `${monthNames[month]} ${year}`;
      }
      
      // Pokaż miesiąc co miesiąc (jak w Factor Exposure)
      if (index % 30 === 0) {
        const monthNames = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 
                           'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec'];
        return monthNames[month];
      }
      
      // Pokaż rok na początku każdego roku (jak w Factor Exposure)
      if (index > 0 && new Date(firstDataset.dates[index - 1]).getFullYear() !== year) {
        return year.toString();
      }
      
      return ''; // Puste etykiety dla większości punktów
    });

    return {
      labels,
      datasets: rollingData.datasets.map((dataset, index) => ({
        label: dataset.ticker,
        data: dataset.values,
        borderColor: colors[index % colors.length],
        backgroundColor: 'transparent',
        borderWidth: 1.5,
        fill: false,
        tension: 0.1,
        borderDash: [],
        pointRadius: 0,
        pointHoverRadius: 4,
        pointHoverBackgroundColor: colors[index % colors.length],
        pointHoverBorderColor: '#ffffff',
        pointHoverBorderWidth: 2
      })),
    };
  };

  const chartOptions = {
    responsive: true,
    maintainAspectRatio: false,
    plugins: {
      legend: {
        position: 'top' as const,
        labels: {
          color: '#ffffff',
          font: {
            size: 12
          },
          usePointStyle: true,
          padding: 10
        }
      },
      title: {
        display: true,
        text: `${getMetricDisplayName(selectedMetric)} - ${getTimeFrameDisplayName(selectedTimeFrame)}`,
        color: '#ffffff',
        font: {
          size: 16,
          weight: 'bold' as const,
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
        titleFont: {
          size: 14,
          weight: 'bold' as const
        },
        bodyFont: {
          size: 12
        },
        padding: 10,
        callbacks: {
          title: function(context: any) {
            const date = new Date(context[0].label);
            return date.toLocaleDateString('en-US', { 
              year: 'numeric', 
              month: 'short', 
              day: 'numeric' 
            });
          },
          label: function(context: any) {
            const label = context.dataset.label || '';
            const value = context.parsed.y;
            const unit = selectedMetric === "vol" ? "%" : "";
            return `${label}: ${value.toFixed(2)}${unit}`;
          }
        }
      }
    },
    scales: {
      x: {
        grid: {
          color: '#333',
          drawBorder: false
        },
        ticks: {
          color: '#ffffff',
          font: {
            size: 11
          },
          maxTicksLimit: 20, // Ogranicz liczbę etykiet na osi X
          maxRotation: 0, // Brak rotacji etykiet
          autoSkip: true,
          autoSkipPadding: 10
        }
      },
      y: {
        title: {
          display: true,
          text: selectedMetric === "vol" ? "Volatility (%)" : "Value",
          color: '#cccccc',
          font: {
            size: 12,
            weight: 'bold' as const
          }
        },
        grid: {
          color: '#333',
          drawBorder: false
        },
        ticks: {
          color: '#ffffff',
          font: {
            size: 11
          }
        }
      },
    },
    elements: {
      point: {
        hoverRadius: 4,
        hoverBorderWidth: 2
      }
    }
  };

  if (loading) {
    return (
      <div className="realized-risk-page">
        <div className="loading">Loading realized risk data...</div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="realized-risk-page">
        <div className="error">
          <p>{error}</p>
          <button onClick={fetchRealizedData} className="retry-button">
            Retry
          </button>
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
        
        {/* Controls */}
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
              availableItems={[
                "PORTFOLIO",
                ...availableTickers
              ]}
              onSelectionChange={setSelectedTickers}
              placeholder="Add ticker"
            />
          </div>
        </div>

        {/* Chart */}
        <div className="rolling-chart-container">
          {rollingData ? (
            (() => {
              const chartData = createRollingChartData();
              if (!chartData) {
                return <div className="chart-loading">No data available for selected metric</div>;
              }
              return <Line data={chartData} options={chartOptions} />;
            })()
          ) : (
            <div className="chart-loading">Loading chart data...</div>
          )}
        </div>
      </div>
    </div>
  );
};

export default RealizedRiskPage;
