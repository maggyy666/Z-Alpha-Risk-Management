import React from 'react';
import { Doughnut } from 'react-chartjs-2';
import {
  Chart as ChartJS,
  CategoryScale,
  LinearScale,
  PointElement,
  LineElement,
  Title,
  Tooltip,
  Legend,
  ArcElement,
} from 'chart.js';
import './VolatilityDonutChart.css';

ChartJS.register(
  CategoryScale,
  LinearScale,
  PointElement,
  LineElement,
  Title,
  Tooltip,
  Legend,
  ArcElement
);

interface PortfolioData {
  symbol: string;
  adj_volatility_weight_pct: number;
}

interface VolatilityDonutChartProps {
  data: PortfolioData[];
}

const VolatilityDonutChart: React.FC<VolatilityDonutChartProps> = ({ data }) => {
  // Sort data by weight descending and take top 12
  const sortedData = data
    .sort((a, b) => b.adj_volatility_weight_pct - a.adj_volatility_weight_pct)
    .slice(0, 12);

  // Generate professional colors for the chart
  const colors = [
    '#00BCD4', '#2196F3', '#3F51B5', '#9C27B0', '#E91E63',
    '#F44336', '#FF5722', '#FF9800', '#FFC107', '#4CAF50',
    '#8BC34A', '#607D8B'
  ];

  const chartData = {
    labels: sortedData.map(item => item.symbol),
    datasets: [
      {
        data: sortedData.map(item => item.adj_volatility_weight_pct),
        backgroundColor: colors.slice(0, sortedData.length),
        borderColor: '#1a1a1a',
        borderWidth: 2,
        hoverBorderColor: '#333',
        hoverBorderWidth: 3,
      },
    ],
  };

  const options = {
    responsive: true,
    maintainAspectRatio: false,
    plugins: {
      legend: {
        position: 'right' as const,
        labels: {
          color: '#ffffff',
          font: {
            size: 13,
          },
          padding: 20,
          usePointStyle: true,
          pointStyle: 'circle',
        },
      },
      tooltip: {
        backgroundColor: '#2a2a2a',
        titleColor: '#ffffff',
        bodyColor: '#ffffff',
        borderColor: '#333',
        borderWidth: 1,
        cornerRadius: 8,
        displayColors: true,
        callbacks: {
          title: function(context: any) {
            return context[0].label;
          },
          label: function(context: any) {
            const value = context.parsed;
            const total = context.dataset.data.reduce((a: number, b: number) => a + b, 0);
            const percentage = ((value / total) * 100).toFixed(1);
            return [
              `Weight: ${value.toFixed(2)}%`,
              `Portfolio Share: ${percentage}%`
            ];
          },
        },
      },
    },
    cutout: '65%',
    radius: '85%',
  };

  // Calculate some statistics
  const totalWeight = sortedData.reduce((sum, item) => sum + item.adj_volatility_weight_pct, 0);
  const topWeight = sortedData[0]?.adj_volatility_weight_pct || 0;
  const avgWeight = totalWeight / sortedData.length;

  return (
    <div className="donut-chart-container">
      <div className="chart-title">Volatility-Adjusted Weights</div>
      <div className="chart-wrapper">
        <Doughnut data={chartData} options={options} />
      </div>
      <div className="chart-stats">
        <div className="stat-item">
          <span className="stat-value">{sortedData.length}</span>
          <span className="stat-label">Tickers</span>
        </div>
        <div className="stat-item">
          <span className="stat-value">{topWeight.toFixed(1)}%</span>
          <span className="stat-label">Top Weight</span>
        </div>
        <div className="stat-item">
          <span className="stat-value">{avgWeight.toFixed(1)}%</span>
          <span className="stat-label">Avg Weight</span>
        </div>
      </div>
    </div>
  );
};

export default VolatilityDonutChart; 