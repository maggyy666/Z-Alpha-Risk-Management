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
import apiService from '../services/api';
import SelectableTags from '../components/SelectableTags';
import './ForecastMetricsPage.css';

ChartJS.register(
  CategoryScale,
  LinearScale,
  PointElement,
  LineElement,
  Title,
  Tooltip,
  Legend
);

interface ForecastMetricsData {
  metrics: Array<{
    ticker: string;
    ewma5_pct: number;
    ewma20_pct: number;
    garch_vol_pct: number;
    egarch_vol_pct: number;
    var_pct: number;
    cvar_pct: number;
    var_usd: number;
    cvar_usd: number;
  }>;
  conf_level: number;
}

interface RollingForecastData {
  data: Array<{
    date: string;
    ticker: string;
    vol_pct: number;
  }>;
  model: string;
  window: number;
}

const ForecastMetricsPage: React.FC = () => {
  const [metricsData, setMetricsData] = useState<ForecastMetricsData | null>(null);
  const [rollingData, setRollingData] = useState<RollingForecastData | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  
  // Rolling forecast controls
  const [selectedModel, setSelectedModel] = useState<string>('EGARCH');
  const [selectedWindow, setSelectedWindow] = useState<number>(21);
  const [selectedTickers, setSelectedTickers] = useState<string[]>(['PORTFOLIO', 'DOMO']);
  const [availableTickers, setAvailableTickers] = useState<string[]>(['PORTFOLIO', 'DOMO', 'AMD', 'GOOGL', 'META', 'TSLA']);

  const fetchForecastMetrics = useCallback(async () => {
    try {
      setLoading(true);
      const response = await apiService.getForecastMetrics("admin");
      setMetricsData(response);
      setError(null);
    } catch (err) {
      setError('Failed to load forecast metrics data');
      console.error('Error fetching forecast metrics:', err);
    } finally {
      setLoading(false);
    }
  }, []);

  const fetchRollingForecast = useCallback(async () => {
    try {
      const response = await apiService.getRollingForecast(selectedModel, selectedWindow, selectedTickers, "admin");
      setRollingData(response);
    } catch (err) {
      console.error('Error fetching rolling forecast:', err);
    }
  }, [selectedModel, selectedWindow, selectedTickers]);

  useEffect(() => {
    fetchForecastMetrics();
  }, [fetchForecastMetrics]);

  useEffect(() => {
    fetchRollingForecast();
  }, [fetchRollingForecast]);

  const createRollingForecastChartData = () => {
    if (!rollingData) return null;

    // Group data by ticker
    const tickerData: { [key: string]: { dates: string[], vols: number[] } } = {};
    
    rollingData.data.forEach(item => {
      if (!tickerData[item.ticker]) {
        tickerData[item.ticker] = { dates: [], vols: [] };
      }
      tickerData[item.ticker].dates.push(item.date);
      tickerData[item.ticker].vols.push(item.vol_pct);
    });

    // Większa paleta kolorów dla lepszego rozróżnienia (jak w Factor Exposure)
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

    const datasets = Object.keys(tickerData).map((ticker, index) => ({
      label: ticker,
      data: tickerData[ticker].vols,
      borderColor: colors[index % colors.length],
      backgroundColor: 'transparent',
      borderWidth: 1.5, // Cieńsze linie dla lepszej czytelności
      fill: false,
      tension: 0.1, // Delikatne wygładzenie
      borderDash: index % 2 === 0 ? [] : [5, 5], // Przemienne linie ciągłe/przerywane
      pointRadius: 0, // Ukryj punkty dla lepszej czytelności
      pointHoverRadius: 4, // Pokaż punkty tylko przy hover
      pointHoverBackgroundColor: colors[index % colors.length],
      pointHoverBorderColor: '#ffffff',
      pointHoverBorderWidth: 2
    }));

    // Get unique dates for labels
    const allDates = tickerData[Object.keys(tickerData)[0]]?.dates || [];
    
    // Format labels - inteligentne etykiety osi X (jak w Factor Exposure)
    const labels = allDates.map((date, index) => {
      const dateObj = new Date(date);
      const year = dateObj.getFullYear();
      const month = dateObj.getMonth();
      
      // Pokaż rok tylko na początku każdego roku lub co 2-3 lata
      if (index === 0 || 
          (index > 0 && new Date(allDates[index - 1]).getFullYear() !== year) ||
          year % 2 === 0) {
        return year.toString();
      }
      
      // W pozostałych przypadkach pokazuj tylko miesiące co kilka miesięcy
      if (index % 30 === 0) { // Co ~miesiąc
        const monthNames = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 
                           'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec'];
        return monthNames[month];
      }
      
      return ''; // Puste etykiety dla większości punktów
    });

    return {
      labels,
      datasets
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
            return `${label}: ${value.toFixed(2)}%`;
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
          text: 'Volatility (%)',
          color: '#cccccc'
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
      }
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
      <div className="forecast-metrics-page">
        <div className="loading">Loading forecast metrics data...</div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="forecast-metrics-page">
        <div className="error">
          <p>{error}</p>
          <button onClick={fetchForecastMetrics} className="retry-button">
            Retry
          </button>
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
      {/* Forecast Metrics Section */}
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

      {/* Rolling Forecast Metrics Section */}
      <div className="rolling-forecast-section">
        <h2>Rolling Forecast Metrics</h2>
        
        <div className="controls">
          <div className="control-group">
            <label>Select Model:</label>
            <select 
              value={selectedModel}
              onChange={(e) => setSelectedModel(e.target.value)}
              className="model-select"
            >
              <option value="EWMA (5D)">EWMA (5D)</option>
              <option value="EWMA (30D)">EWMA (30D)</option>
              <option value="EWMA (200D)">EWMA (200D)</option>
              <option value="GARCH">GARCH</option>
              <option value="EGARCH">EGARCH</option>
            </select>
          </div>
          
          <div className="control-group">
            <label>Select Time Frame:</label>
            <input 
              type="number" 
              value={selectedWindow}
              onChange={(e) => setSelectedWindow(Number(e.target.value))}
              min="5"
              max="252"
              className="timeframe-input"
            />
          </div>
          
          <div className="control-group">
            <SelectableTags
              title="Select Tickers"
              selectedItems={selectedTickers}
              availableItems={availableTickers}
              onSelectionChange={setSelectedTickers}
              placeholder="Add ticker"
            />
          </div>
        </div>

        <div className="chart-container">
          {rollingData && createRollingForecastChartData() && (
            <Line data={createRollingForecastChartData()!} options={chartOptions} />
          )}
        </div>
      </div>
    </div>
  );
};

export default ForecastMetricsPage;
