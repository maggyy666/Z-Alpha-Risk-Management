import React, { useState, useEffect } from 'react';
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
import apiService, { ConcentrationRiskResponse } from '../services/api';
import RiskScoring from '../components/RiskScoring';
import './ConcentrationRiskPage.css';

ChartJS.register(
  CategoryScale,
  LinearScale,
  BarElement,
  Title,
  Tooltip,
  Legend,
  ArcElement
);

type TabType = 'position' | 'sector' | 'market-cap' | 'risk-scoring';

const ConcentrationRiskPage: React.FC = () => {
  const [data, setData] = useState<ConcentrationRiskResponse | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [activeTab, setActiveTab] = useState<TabType>('position');

  const fetchConcentrationData = async () => {
    try {
      setLoading(true);
      const response = await apiService.getConcentrationRiskData("admin");
      setData(response);
      setError(null);
    } catch (err) {
      setError('Failed to load concentration risk data');
      console.error('Error fetching concentration data:', err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchConcentrationData();
  }, []);

  const createPositionWeightChartData = () => {
    if (!data) return null;

    const top10Data = data.portfolio_data.slice(0, 10);
    
    return {
      labels: top10Data.map(item => item.ticker),
      datasets: [
        {
          label: 'Position Weight (%)',
          data: top10Data.map(item => item.weight),
          backgroundColor: 'rgba(54, 162, 235, 0.8)',
          borderColor: 'rgba(54, 162, 235, 1)',
          borderWidth: 1,
        },
      ],
    };
  };

  const createSectorChartData = () => {
    if (!data) return null;

    return {
      labels: data.sector_concentration.sectors,
      datasets: [
        {
          label: 'Sector Weight (%)',
          data: data.sector_concentration.weights,
          backgroundColor: 'rgba(255, 99, 132, 0.8)',
          borderColor: 'rgba(255, 99, 132, 1)',
          borderWidth: 1,
        },
      ],
    };
  };

  const getLargestSector = () => {
    if (!data) return '';
    const maxIndex = data.sector_concentration.weights.indexOf(Math.max(...data.sector_concentration.weights));
    return data.sector_concentration.sectors[maxIndex];
  };

  const createSectorPieChartData = () => {
    if (!data) return null;

    const colors = [
      'rgba(54, 162, 235, 0.8)',   // Light Blue
      'rgba(75, 192, 192, 0.8)',   // Dark Blue  
      'rgba(255, 99, 132, 0.8)',   // Light Red/Pink
      'rgba(255, 159, 64, 0.8)',   // Red
      'rgba(75, 192, 192, 0.8)',   // Green
    ];

    return {
      labels: data.sector_concentration.sectors,
      datasets: [
        {
          data: data.sector_concentration.weights,
          backgroundColor: colors.slice(0, data.sector_concentration.sectors.length),
          borderColor: colors.slice(0, data.sector_concentration.sectors.length).map(color => color.replace('0.8', '1')),
          borderWidth: 2,
        },
      ],
    };
  };

  const createSectorBreakdownData = () => {
    if (!data) return [];

    // Group portfolio data by sector
    const sectorGroups: { [key: string]: any[] } = {};
    data.portfolio_data.forEach(item => {
      const sector = item.sector;
      if (!sectorGroups[sector]) {
        sectorGroups[sector] = [];
      }
      sectorGroups[sector].push(item);
    });

    // Create breakdown data
    return Object.keys(sectorGroups).map(sector => {
      const items = sectorGroups[sector];
      const totalWeight = items.reduce((sum, item) => sum + item.weight, 0);
      const tickers = items.map(item => item.ticker).join(', ');
      
      return {
        name: sector,
        weight: totalWeight,
        positions: items.length,
        positionList: tickers
      };
    }).sort((a, b) => b.weight - a.weight); // Sort by weight descending
  };

  const chartOptions = {
    responsive: true,
    maintainAspectRatio: false,
    plugins: {
      legend: {
        display: false,
      },
      tooltip: {
        enabled: true,
        backgroundColor: 'rgba(0, 0, 0, 0.9)',
        titleColor: '#ffffff',
        bodyColor: '#ffffff',
        borderColor: '#333',
        borderWidth: 1,
        cornerRadius: 6,
        callbacks: {
          label: function(context: any) {
            return `${context.label}: ${context.parsed.y.toFixed(1)}%`;
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
          }
        }
      },
      y: {
        grid: {
          color: '#333',
          drawBorder: false
        },
        ticks: {
          color: '#ffffff',
          font: {
            size: 11
          },
          callback: function(value: any) {
            return value + '%';
          }
        }
      }
    }
  };

  const sectorPieChartOptions = {
    responsive: true,
    maintainAspectRatio: false,
    plugins: {
      legend: {
        display: true,
        position: 'right' as const,
        labels: {
          color: '#ffffff',
          padding: 20,
          usePointStyle: true,
          pointStyle: 'circle',
        },
      },
      tooltip: {
        enabled: true,
        backgroundColor: 'rgba(0, 0, 0, 0.9)',
        titleColor: '#ffffff',
        bodyColor: '#ffffff',
        borderColor: '#333',
        borderWidth: 1,
        callbacks: {
          label: function(context: any) {
            return `${context.label}: ${context.parsed.toFixed(1)}%`;
          }
        }
      },
    },
  };

  if (loading) {
    return (
      <div className="concentration-risk-page">
        <div className="loading">
          Loading concentration risk data...
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="concentration-risk-page">
        <div className="error">{error}</div>
      </div>
    );
  }

  if (!data) {
    return (
      <div className="concentration-risk-page">
        <div className="error">No data available</div>
      </div>
    );
  }

  return (
    <div className="concentration-risk-page">
      {/* Sub-navigation */}
      <div className="sub-nav">
        <button 
          className={`sub-nav-item ${activeTab === 'position' ? 'active' : ''}`}
          onClick={() => setActiveTab('position')}
        >
          Position Concentration
        </button>
        <button 
          className={`sub-nav-item ${activeTab === 'sector' ? 'active' : ''}`}
          onClick={() => setActiveTab('sector')}
        >
          Sector Concentration
        </button>
        <button 
          className={`sub-nav-item ${activeTab === 'market-cap' ? 'active' : ''}`}
          onClick={() => setActiveTab('market-cap')}
        >
          Market Cap Concentration
        </button>
        <button 
          className={`sub-nav-item ${activeTab === 'risk-scoring' ? 'active' : ''}`}
          onClick={() => setActiveTab('risk-scoring')}
        >
          Risk Scoring
        </button>
      </div>

      {activeTab === 'position' && (
        <div className="position-concentration">
          {/* Concentration Metrics */}
          <div className="metrics-grid">
            <div className="metric-card">
              <div className="metric-label">Largest Position</div>
              <div className="metric-value">{data.concentration_metrics.largest_position}%</div>
            </div>
            <div className="metric-card">
              <div className="metric-label">Herfindahl Index</div>
              <div className="metric-value">{data.concentration_metrics.herfindahl_index}</div>
            </div>
            <div className="metric-card">
              <div className="metric-label">Effective Positions</div>
              <div className="metric-value">{data.concentration_metrics.effective_positions}</div>
            </div>
            <div className="metric-card">
              <div className="metric-label">Top 3 Concentration</div>
              <div className="metric-value">{data.concentration_metrics.top_3_concentration}%</div>
            </div>
            <div className="metric-card">
              <div className="metric-label">Top 5 Concentration</div>
              <div className="metric-value">{data.concentration_metrics.top_5_concentration}%</div>
            </div>
            <div className="metric-card">
              <div className="metric-label">Top 10 Concentration</div>
              <div className="metric-value">{data.concentration_metrics.top_10_concentration}%</div>
            </div>
          </div>

          {/* Position Weight Distribution Chart */}
          <div className="chart-section">
            <h3>Top 10 Position Weights</h3>
            <div className="chart-container">
              {createPositionWeightChartData() && (
                <Bar data={createPositionWeightChartData()!} options={chartOptions} />
              )}
            </div>
          </div>

          {/* Position Concentration Details Table */}
          <div className="table-section">
            <h3>Position Concentration Details</h3>
            <div className="table-container">
              <table className="concentration-table">
                <thead>
                  <tr>
                    <th>Ticker</th>
                    <th>Weight</th>
                    <th>Market Value</th>
                    <th>Sector</th>
                    <th>Market Cap ($bn)</th>
                  </tr>
                </thead>
                <tbody>
                  {data.portfolio_data.map((item, index) => (
                    <tr key={index}>
                      <td>{item.ticker}</td>
                      <td>{item.weight.toFixed(1)}%</td>
                      <td>${item.market_value.toLocaleString()}</td>
                      <td>{item.sector}</td>
                      <td>{item.market_cap.toLocaleString()}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>
        </div>
      )}

      {activeTab === 'sector' && (
        <div className="sector-concentration">
          {/* Sector Concentration Analysis */}
          <div className="sector-analysis-section">
            <h3>Sector Concentration Analysis</h3>
            
            {/* KPI Cards */}
            <div className="metrics-grid">
              <div className="metric-card">
                <div className="metric-label">Largest Sector</div>
                <div className="metric-value">{getLargestSector()}</div>
              </div>
              <div className="metric-card">
                <div className="metric-label">Number of Sectors</div>
                <div className="metric-value">{data.sector_concentration.sectors.length}</div>
              </div>
            </div>
          </div>

          {/* Portfolio Sector Allocation */}
          <div className="chart-section">
            <h3>Portfolio Sector Allocation</h3>
            <div className="chart-container">
              {createSectorPieChartData() && (
                <Doughnut data={createSectorPieChartData()!} options={sectorPieChartOptions} />
              )}
            </div>
          </div>

          {/* Sector Breakdown Table */}
          <div className="table-section">
            <h3>Sector Breakdown</h3>
            <div className="table-container">
              <table className="concentration-table">
                <thead>
                  <tr>
                    <th>Sector</th>
                    <th>Weight</th>
                    <th>Positions</th>
                    <th>Position List</th>
                  </tr>
                </thead>
                <tbody>
                  {createSectorBreakdownData().map((sector, index) => (
                    <tr key={index}>
                      <td>{sector.name}</td>
                      <td>{sector.weight.toFixed(1)}%</td>
                      <td>{sector.positions}</td>
                      <td>{sector.positionList}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>
        </div>
      )}

      {activeTab === 'market-cap' && (
        <div className="market-cap-concentration">
          <div className="coming-soon">
            <h3>Market Cap Concentration</h3>
            <p>This feature will be implemented soon.</p>
          </div>
        </div>
      )}

      {activeTab === 'risk-scoring' && <RiskScoring />}
    </div>
  );
};

export default ConcentrationRiskPage; 