import React, { useState, useEffect, useCallback } from 'react';
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
import ForecastMetricsPage from './ForecastMetricsPage';
import './ForecastRiskPage.css';

ChartJS.register(
  CategoryScale,
  LinearScale,
  BarElement,
  Title,
  Tooltip,
  Legend,
  ArcElement
);

type TabType = 'metrics' | 'contribution';

const ForecastRiskPage: React.FC = () => {
  const [data, setData] = useState<ForecastRiskContributionResponse | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [selectedModel, setSelectedModel] = useState<string>('EWMA (5D)');
  const [activeTab, setActiveTab] = useState<TabType>('metrics');

  const fetchForecastRiskData = useCallback(async () => {
    try {
      setLoading(true);
      const response = await apiService.getForecastRiskContributionData(selectedModel, "admin");
      setData(response);
      setError(null);
    } catch (err) {
      setError('Failed to load forecast risk contribution data');
      console.error('Error fetching forecast risk data:', err);
    } finally {
      setLoading(false);
    }
  }, [selectedModel]);

  useEffect(() => {
    fetchForecastRiskData();
  }, [fetchForecastRiskData]);

  const createMarginalRiskChartData = () => {
    if (!data) return null;

    // Color coding: positive = blue, negative = red (hedging)
    const colors = data.marginal_rc_pct.map(value => 
      value >= 0 ? 'rgba(54, 162, 235, 0.8)' : 'rgba(255, 99, 132, 0.8)'
    );

    return {
      labels: data.tickers,
      datasets: [
        {
          label: 'Marginal Risk Contribution (%)',
          data: data.marginal_rc_pct,
          backgroundColor: colors,
          borderColor: data.marginal_rc_pct.map(value => 
            value >= 0 ? 'rgba(54, 162, 235, 1)' : 'rgba(255, 99, 132, 1)'
          ),
          borderWidth: 1,
        },
      ],
    };
  };

  const createTotalRiskChartData = () => {
    if (!data) return null;

    // Colors for doughnut chart
    const colors = [
      '#36A2EB', '#FF6384', '#4BC0C0', '#FF9F40', '#9966FF',
      '#FFCD56', '#C9CBCF', '#4BC0C0', '#FF6384', '#36A2EB',
      '#FF9F40', '#9966FF', '#FFCD56', '#C9CBCF'
    ];

    return {
      labels: data.tickers,
      datasets: [
        {
          data: data.total_rc_pct,
          backgroundColor: colors.slice(0, data.tickers.length),
          borderWidth: 2,
          borderColor: '#1a1a1a',
        },
      ],
    };
  };

  // Calculate dynamic height based on number of tickers
  const getChartHeight = () => {
    if (!data || !data.tickers) return 300;
    const tickerCount = data.tickers.length;
    // Base height + additional height per ticker, but with reasonable limits
    return Math.max(250, Math.min(600, 200 + tickerCount * 25));
  };

  const chartOptions = {
    indexAxis: 'y' as const,
    responsive: true,
    maintainAspectRatio: false,
    plugins: {
      legend: {
        display: true,
        position: 'top' as const,
        labels: {
          color: '#ffffff',
          font: {
            size: 11,
            weight: 'bold' as const
          },
          usePointStyle: true,
          pointStyle: 'rect',
          generateLabels: function(chart: any) {
            return [
              {
                text: 'Risk Contribution',
                fillStyle: 'rgba(54, 162, 235, 0.8)',
                strokeStyle: 'rgba(54, 162, 235, 1)',
                lineWidth: 1,
                hidden: false,
                index: 0,
                fontColor: '#ffffff'
              },
              {
                text: 'Risk Reduction (Hedging)',
                fillStyle: 'rgba(255, 99, 132, 0.8)',
                strokeStyle: 'rgba(255, 99, 132, 1)',
                lineWidth: 1,
                hidden: false,
                index: 1,
                fontColor: '#ffffff'
              }
            ];
          }
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
            return context[0].label;
          },
          label: function(context: any) {
            const value = context.parsed.x;
            const isHedging = value < 0;
            const effect = isHedging ? 'Risk Reduction' : 'Risk Contribution';
            return `${effect}: ${value.toFixed(2)}%`;
          }
        }
      }
    },
    scales: {
      x: {
        beginAtZero: true,
        title: {
          display: true,
          text: 'Marginal Risk Contribution (%)',
          color: '#cccccc',
          font: {
            size: 12,
            weight: 'bold' as const
          }
        },
        ticks: {
          color: '#cccccc',
          font: {
            size: 11
          }
        },
        grid: {
          color: '#333',
          drawBorder: false
        }
      },
      y: {
        ticks: {
          color: '#cccccc',
          font: {
            size: 11,
            weight: 'bold' as const
          }
        },
        grid: {
          display: false
        },
        barThickness: 'flex',
        maxBarThickness: 50
      }
    },
    elements: {
      point: {
        hoverRadius: 6,
        hoverBackgroundColor: 'rgba(54, 162, 235, 0.8)',
        hoverBorderColor: '#ffffff',
        hoverBorderWidth: 2
      },
      bar: {
        borderWidth: 2,
        borderRadius: 4,
        borderSkipped: false
      }
    }
  };

  const doughnutOptions = {
    responsive: true,
    maintainAspectRatio: false,
    plugins: {
      legend: {
        position: 'right' as const,
        labels: {
          color: '#cccccc',
          font: {
            size: 11
          },
          padding: 15,
          usePointStyle: true,
          pointStyle: 'circle'
        }
      },
      tooltip: {
        enabled: true,
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
            return context[0].label;
          },
          label: function(context: any) {
            const value = context.parsed;
            return `Risk Contribution: ${value.toFixed(2)}%`;
          }
        }
      }
    }
  };

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
          <button onClick={fetchForecastRiskData} className="retry-button">
            Retry
          </button>
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
      {/* Sub-navigation */}
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
            <div className="dropdown-container">
              <label>Select Model for Risk Contribution:</label>
              <select 
                className="model-dropdown"
                value={selectedModel}
                onChange={(e) => setSelectedModel(e.target.value)}
              >
                <option value="EWMA (5D)">EWMA (5D)</option>
                <option value="EWMA (30D)">EWMA (30D)</option>
                <option value="EWMA (200D)">EWMA (200D)</option>
                <option value="Garch Volatility">Garch Volatility</option>
                <option value="E-Garch Volatility">E-Garch Volatility</option>
              </select>
            </div>
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
          <span className="value">{data.marginal_rc_pct.filter(v => v < 0).length}</span>
        </div>
      </div>

      <div className="charts-container">
        <div className="chart-section">
          <h3>Marginal Risk Contribution</h3>
          <div className="chart-container" style={{ height: `${getChartHeight()}px` }}>
            {createMarginalRiskChartData() && (
              <Bar data={createMarginalRiskChartData()!} options={chartOptions} />
            )}
          </div>
        </div>

        <div className="chart-section">
          <h3>Forecast Risk Contribution</h3>
          <div className="chart-container" style={{ height: `${Math.min(400, getChartHeight())}px` }}>
            {createTotalRiskChartData() && (
              <Doughnut data={createTotalRiskChartData()!} options={doughnutOptions} />
            )}
          </div>
        </div>
      </div>
        </>
      )}
    </div>
  );
};

export default ForecastRiskPage;
