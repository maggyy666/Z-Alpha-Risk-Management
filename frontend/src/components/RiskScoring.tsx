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
import apiService, { RiskScoringResponse } from '../services/api';
import './RiskScoring.css';

ChartJS.register(
  CategoryScale,
  LinearScale,
  BarElement,
  Title,
  Tooltip,
  Legend,
  ArcElement
);

const RiskScoring: React.FC = () => {
  const [data, setData] = useState<RiskScoringResponse | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    fetchRiskScoringData();
  }, []);

  const fetchRiskScoringData = async () => {
    try {
      setLoading(true);
      const response = await apiService.getRiskScoringData("admin");
      setData(response);
      setError(null);
    } catch (err) {
      setError('Failed to load risk scoring data');
      console.error('Error fetching risk scoring data:', err);
    } finally {
      setLoading(false);
    }
  };

  const createScoreWeightsChartData = () => {
    if (!data) return null;

    const labels = [
      'Stress Test',
      'Correlation', 
      'Factor Risk',
      'Market Risk',
      'Volatility',
      'Concentration'
    ];

    const weights = [
      data.score_weights.stress || 0,
      data.score_weights.correlation,
      data.score_weights.factor,
      data.score_weights.market,
      data.score_weights.volatility,
      data.score_weights.concentration
    ];

    // Create gradient colors based on weight values
    const colors = weights.map(w => {
      const intensity = Math.min(255, Math.max(50, 255 - (w * 100 * 5)));
      return `rgba(54, 162, 235, ${0.3 + (w * 0.7)})`;
    });

    return {
      labels,
      datasets: [
        {
          label: 'Weight',
          data: weights.map(w => w * 100), // Convert to percentage
          backgroundColor: colors,
          borderColor: 'rgba(54, 162, 235, 1)',
          borderWidth: 1,
        },
      ],
    };
  };

  const createContributionChartData = () => {
    if (!data) return null;

    const labels = Object.keys(data.risk_contribution_pct).map(key => 
      key.charAt(0).toUpperCase() + key.slice(1)
    );
    const values = Object.values(data.risk_contribution_pct);

    // Colors matching the image: light blue, green, red, pink, blue
    const colors = [
      '#36A2EB', // Factor Risk - light blue
      '#4BC0C0', // Stress Test - light green  
      '#4BC0C0', // Market Risk - green
      '#FF6384', // Correlation - red
      '#FF6384', // Volatility - pink
      '#36A2EB'  // Concentration - blue
    ];

    return {
      labels,
      datasets: [
        {
          data: values,
          backgroundColor: colors,
          borderWidth: 2,
          borderColor: '#1a1a1a',
        },
      ],
    };
  };

  const chartOptions = {
    responsive: true,
    maintainAspectRatio: false,
    indexAxis: 'y' as const, // Horizontal bar chart
    plugins: {
      legend: { 
        display: false,
        position: 'top' as const,
        labels: { color: '#ffffff' }
      },
      tooltip: {
        backgroundColor: 'rgba(0, 0, 0, 0.9)',
        titleColor: '#ffffff',
        bodyColor: '#ffffff',
        borderColor: '#333',
        borderWidth: 1,
        cornerRadius: 6,
        callbacks: {
          label: function(context: any) {
            return `${context.label}: ${context.parsed.x.toFixed(1)}%`;
          }
        }
      }
    },
    scales: {
      x: { 
        grid: { color: '#333', drawBorder: false }, 
        ticks: { 
          color: '#ffffff', 
          font: { size: 11 },
          callback: function(value: any) { 
            return value + '%'; 
          }
        },
        title: {
          display: true,
          text: 'Weight',
          color: '#ffffff',
          font: { size: 12 }
        }
      },
      y: {
        grid: { color: '#333', drawBorder: false },
        ticks: { 
          color: '#ffffff', 
          font: { size: 11 }
        },
        title: {
          display: true,
          text: 'Risk Type',
          color: '#ffffff',
          font: { size: 12 }
        }
      }
    }
  };

  const doughnutOptions = {
    responsive: true,
    maintainAspectRatio: false,
    plugins: {
      legend: { 
        position: 'bottom' as const,
        labels: { 
          color: '#ffffff',
          padding: 15,
          font: { size: 11 }
        }
      },
      tooltip: {
        backgroundColor: 'rgba(0, 0, 0, 0.9)',
        titleColor: '#ffffff',
        bodyColor: '#ffffff',
        borderColor: '#333',
        borderWidth: 1,
        cornerRadius: 6,
        callbacks: {
          label: function(context: any) {
            return `${context.label}: ${context.parsed.toFixed(1)}%`;
          }
        }
      }
    }
  };

  if (loading) {
    return (
      <div className="risk-scoring">
        <div className="loading">Loading risk scoring data...</div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="risk-scoring">
        <div className="error">
          <p>{error}</p>
          <button onClick={fetchRiskScoringData} className="retry-button">
            Retry
          </button>
        </div>
      </div>
    );
  }

  if (!data) {
    return (
      <div className="risk-scoring">
        <div className="error">No risk scoring data available</div>
      </div>
    );
  }

  return (
    <div className="risk-scoring">
      <div className="risk-scoring-header">
        <h2>Risk Scoring</h2>
      </div>

      <div className="charts-container">
        <div className="chart-section">
          <h3>Risk Score Weights</h3>
          <div className="chart-container">
            {createScoreWeightsChartData() && (
              <Bar data={createScoreWeightsChartData()!} options={chartOptions} />
            )}
          </div>
        </div>

        <div className="chart-section">
          <h3>Risk Contribution by Component</h3>
          <div className="chart-container">
            {createContributionChartData() && (
              <Doughnut data={createContributionChartData()!} options={doughnutOptions} />
            )}
          </div>
        </div>
      </div>

      <div className="alerts-section">
        <h3>Risk Alerts</h3>
        {data.alerts.length > 0 ? (
          <>
            <div className="alerts-banner">
              <span className="banner-text">MEDIUM RISK ALERTS</span>
            </div>
            <div className="alerts-container">
              {data.alerts.map((alert, index) => (
                <div key={index} className={`alert-item ${alert.severity.toLowerCase()}`}>
                  <div className="alert-text">{alert.text}</div>
                  <div className="alert-chevron">▼</div>
                </div>
              ))}
            </div>
          </>
        ) : (
          <div className="no-alerts">No risk alerts at this time.</div>
        )}
      </div>

      <div className="recommendations-section">
        <h3>Recommendations</h3>
        {data.recommendations.length > 0 ? (
          <div className="recommendations-container">
            {data.recommendations.map((rec, index) => (
              <div key={index} className="recommendation-item">
                {rec}
              </div>
            ))}
          </div>
        ) : (
          <div className="recommendation-item">
            MEDIUM Factor Risk: Review factor exposures and consider diversification
          </div>
        )}
      </div>


    </div>
  );
};

export default RiskScoring; 