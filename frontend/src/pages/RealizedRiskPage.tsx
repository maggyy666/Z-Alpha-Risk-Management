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
  
  // Rolling metrics controls
  const [selectedMetric, setSelectedMetric] = useState<string>("vol");
  const [selectedTimeFrame, setSelectedTimeFrame] = useState<number>(21);
  const [selectedTickers, setSelectedTickers] = useState<string[]>(["PORTFOLIO"]);

  const fetchRealizedData = useCallback(async () => {
    try {
      setLoading(true);
      const response = await apiService.getRealizedMetrics("admin");
      setRealizedData(response);
      setError(null);
    } catch (err) {
      setError('Failed to load realized metrics data');
      console.error('Error fetching realized metrics:', err);
    } finally {
      setLoading(false);
    }
  }, []);

  const fetchRollingData = useCallback(async () => {
    try {
      const response = await apiService.getRollingMetrics(
        selectedMetric,
        selectedTimeFrame,
        selectedTickers[0] || "PORTFOLIO",
        "admin"
      );
      setRollingData(response);
    } catch (err) {
      console.error('Error fetching rolling metrics:', err);
    }
  }, [selectedMetric, selectedTimeFrame, selectedTickers]);

  useEffect(() => {
    fetchRealizedData();
  }, [fetchRealizedData]);

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
    if (!rollingData) return null;

    // Większa paleta kolorów dla lepszego rozróżnienia (jak w Forecast Metrics)
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

    // Format labels - lepsze etykiety osi X
    const labels = rollingData.dates.map((date, index) => {
      const dateObj = new Date(date);
      const year = dateObj.getFullYear();
      const month = dateObj.getMonth();
      const day = dateObj.getDate();
      
      // Pokaż pełną datę co 3 miesiące
      if (index === 0 || index === rollingData.dates.length - 1 || index % 90 === 0) {
        const monthNames = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 
                           'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec'];
        return `${monthNames[month]} ${year}`;
      }
      
      // Pokaż miesiąc co miesiąc
      if (index % 30 === 0) {
        const monthNames = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 
                           'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec'];
        return monthNames[month];
      }
      
      // Pokaż rok na początku każdego roku
      if (index > 0 && new Date(rollingData.dates[index - 1]).getFullYear() !== year) {
        return year.toString();
      }
      
      return ''; // Puste etykiety dla większości punktów
    });

    return {
      labels,
      datasets: [
        {
          label: `Ticker - ${rollingData.ticker}`,
          data: rollingData.values,
          borderColor: colors[0], // Użyj pierwszego koloru dla pojedynczej linii
          backgroundColor: 'transparent',
          borderWidth: 1.5, // Cieńsze linie dla lepszej czytelności
          fill: false,
          tension: 0.1, // Delikatne wygładzenie
          borderDash: [], // Linia ciągła
          pointRadius: 0, // Ukryj punkty dla lepszej czytelności
          pointHoverRadius: 4, // Pokaż punkty tylko przy hover
          pointHoverBackgroundColor: colors[0],
          pointHoverBorderColor: '#ffffff',
          pointHoverBorderWidth: 2
        },
      ],
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
                <th>Beta (SPX)</th>
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
                    {metric.ann_return_pct.toFixed(1)}
                  </td>
                  <td>{metric.ann_volatility_pct.toFixed(1)}</td>
                  <td className={metric.sharpe >= 1 ? 'positive' : 'neutral'}>
                    {metric.sharpe.toFixed(2)}
                  </td>
                  <td className={metric.sortino >= 1 ? 'positive' : 'neutral'}>
                    {metric.sortino.toFixed(2)}
                  </td>
                  <td>{metric.skew.toFixed(1)}</td>
                  <td>{metric.kurtosis.toFixed(0)}</td>
                  <td className="negative">{metric.max_drawdown_pct.toFixed(1)}</td>
                  <td className="negative">{metric.var_95_pct.toFixed(1)}</td>
                  <td className="negative">{metric.cvar_95_pct.toFixed(1)}</td>
                  <td>{metric.hit_ratio_pct.toFixed(0)}</td>
                  <td>{metric.beta_ndx.toFixed(2)}</td>
                  <td>{metric.beta_spy.toFixed(2)}</td>
                  <td className={metric.up_capture_ndx_pct >= 100 ? 'positive' : 'neutral'}>
                    {metric.up_capture_ndx_pct.toFixed(0)}
                  </td>
                  <td className={metric.down_capture_ndx_pct <= 100 ? 'positive' : 'negative'}>
                    {metric.down_capture_ndx_pct.toFixed(0)}
                  </td>
                  <td>{metric.tracking_error_pct.toFixed(1)}</td>
                  <td className={metric.information_ratio >= 0.5 ? 'positive' : 'neutral'}>
                    {metric.information_ratio.toFixed(2)}
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
              availableItems={["PORTFOLIO", "AMD", "GOOGL", "META", "TSLA", "APP", "DOMO", "SGOV", "RDDT", "ULTY", "BULL", "BRK-B", "QQQM", "SNOW", "SMCI"]}
              onSelectionChange={setSelectedTickers}
              placeholder="Add ticker"
            />
          </div>
        </div>

        {/* Chart */}
        <div className="rolling-chart-container">
          {rollingData ? (
            <Line data={createRollingChartData()!} options={chartOptions} />
          ) : (
            <div className="chart-loading">Loading chart data...</div>
          )}
        </div>
      </div>
    </div>
  );
};

export default RealizedRiskPage;
