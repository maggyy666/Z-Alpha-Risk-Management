import React, { useMemo, useState } from 'react';
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
import apiService, {
  ConcentrationRiskResponse,
  PortfolioItem,
  MarketCapBucketEntry,
} from '../services/api';
import { useApiData } from '../hooks/useApiData';
import { useSession } from '../contexts/SessionContext';
import RiskScoring from '../components/RiskScoring';
import './ConcentrationRiskPage.css';

ChartJS.register(CategoryScale, LinearScale, BarElement, Title, Tooltip, Legend, ArcElement);

type TabType = 'position' | 'sector' | 'market-cap' | 'risk-scoring';

const PIE_PALETTE = [
  'rgba(255, 107, 107, 0.8)',
  'rgba(255, 99, 132, 0.8)',
  'rgba(255, 159, 64, 0.8)',
  'rgba(255, 99, 71, 0.8)',
  'rgba(220, 20, 60, 0.8)',
  'rgba(255, 140, 0, 0.8)',
];

const BAR_OPTIONS = {
  responsive: true,
  maintainAspectRatio: false,
  plugins: {
    legend: { display: false },
    tooltip: {
      enabled: true,
      backgroundColor: 'rgba(0, 0, 0, 0.9)',
      titleColor: '#ffffff',
      bodyColor: '#ffffff',
      borderColor: '#333',
      borderWidth: 1,
      cornerRadius: 6,
      callbacks: {
        label(context: { label: string; parsed: { y: number } }) {
          return `${context.label}: ${context.parsed.y.toFixed(1)}%`;
        },
      },
    },
  },
  scales: {
    x: {
      grid: { color: '#333', drawBorder: false },
      ticks: { color: '#ffffff', font: { size: 11 } },
    },
    y: {
      grid: { color: '#333', drawBorder: false },
      ticks: {
        color: '#ffffff',
        font: { size: 11 },
        callback(value: number | string) { return `${value}%`; },
      },
    },
  },
};

const PIE_OPTIONS = {
  responsive: true,
  maintainAspectRatio: false,
  plugins: {
    legend: {
      display: true,
      position: 'right' as const,
      labels: { color: '#ffffff', padding: 20, usePointStyle: true, pointStyle: 'circle' },
    },
    tooltip: {
      enabled: true,
      backgroundColor: 'rgba(0, 0, 0, 0.9)',
      titleColor: '#ffffff',
      bodyColor: '#ffffff',
      borderColor: '#333',
      borderWidth: 1,
      callbacks: {
        label(context: { label: string; parsed: number }) {
          return `${context.label}: ${context.parsed.toFixed(1)}%`;
        },
      },
    },
  },
};

const buildBarChart = (labels: string[], values: number[], label: string) => ({
  labels,
  datasets: [
    {
      label,
      data: values,
      backgroundColor: 'rgba(255, 107, 107, 0.8)',
      borderColor: 'rgba(255, 107, 107, 1)',
      borderWidth: 2,
    },
  ],
});

const buildPieChart = (labels: string[], values: number[]) => {
  const colors = PIE_PALETTE.slice(0, labels.length);
  return {
    labels,
    datasets: [
      {
        data: values,
        backgroundColor: colors,
        borderColor: colors,
        borderWidth: 2,
      },
    ],
  };
};

interface SectorBreakdown {
  name: string;
  weight: number;
  positions: number;
  positionList: string;
}

interface MarketCapBreakdown extends SectorBreakdown {
  avgMarketCap: number;
}

const buildSectorBreakdown = (items: PortfolioItem[]): SectorBreakdown[] => {
  const groups: Record<string, PortfolioItem[]> = {};
  items.forEach((item) => {
    if (!groups[item.sector]) groups[item.sector] = [];
    groups[item.sector].push(item);
  });
  return Object.entries(groups)
    .map(([name, group]) => ({
      name,
      weight: group.reduce((sum, it) => sum + it.weight, 0),
      positions: group.length,
      positionList: group.map((it) => it.ticker).join(', '),
    }))
    .sort((a, b) => b.weight - a.weight);
};

const buildMarketCapBreakdown = (
  details: { [category: string]: MarketCapBucketEntry[] },
): MarketCapBreakdown[] =>
  Object.entries(details)
    .map(([name, items]) => ({
      name,
      weight: items.reduce((sum, it) => sum + it.weight, 0),
      positions: items.length,
      positionList: items.map((it) => it.ticker).join(', '),
      avgMarketCap: items.reduce((sum, it) => sum + it.market_cap, 0) / items.length,
    }))
    .sort((a, b) => b.weight - a.weight);

const argMax = (arr: number[]) => arr.indexOf(Math.max(...arr));

const ConcentrationRiskPage: React.FC = () => {
  const { getCurrentUsername } = useSession();
  const username = getCurrentUsername();
  const [activeTab, setActiveTab] = useState<TabType>('position');

  const { data, loading, error } = useApiData<ConcentrationRiskResponse>(
    () => apiService.getConcentrationRiskData(username),
    [username],
    'Failed to load concentration risk data',
  );

  const positionWeightChart = useMemo(() => {
    if (!data) return null;
    const top10 = data.portfolio_data.slice(0, 10);
    return buildBarChart(top10.map((i) => i.ticker), top10.map((i) => i.weight), 'Position Weight (%)');
  }, [data]);

  const sectorPieChart = useMemo(() => {
    if (!data) return null;
    return buildPieChart(data.sector_concentration.sectors, data.sector_concentration.weights);
  }, [data]);

  const marketCapPieChart = useMemo(() => {
    if (!data) return null;
    return buildPieChart(data.market_cap_concentration.categories, data.market_cap_concentration.weights);
  }, [data]);

  const sectorBreakdown = useMemo(
    () => (data ? buildSectorBreakdown(data.portfolio_data) : []),
    [data],
  );

  const marketCapBreakdown = useMemo(
    () => (data ? buildMarketCapBreakdown(data.market_cap_concentration.details) : []),
    [data],
  );

  const largestSector = useMemo(() => {
    if (!data) return '';
    return data.sector_concentration.sectors[argMax(data.sector_concentration.weights)];
  }, [data]);

  const largestMarketCapCategory = useMemo(() => {
    if (!data) return '';
    return data.market_cap_concentration.categories[argMax(data.market_cap_concentration.weights)];
  }, [data]);

  if (loading) {
    return (
      <div className="concentration-risk-page">
        <div className="loading">Loading concentration risk data...</div>
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
        <>
          <div className="position-metrics-grid">
            <div className="position-metric-card">
              <div className="position-metric-label">Largest Position</div>
              <div className="position-metric-value">{data.concentration_metrics.largest_position}%</div>
            </div>
            <div className="position-metric-card">
              <div className="position-metric-label">Herfindahl Index</div>
              <div className="position-metric-value">{data.concentration_metrics.herfindahl_index}</div>
            </div>
            <div className="position-metric-card">
              <div className="position-metric-label">Effective Positions</div>
              <div className="position-metric-value">{data.concentration_metrics.effective_positions}</div>
            </div>
            <div className="position-metric-card">
              <div className="position-metric-label">Top 3 Concentration</div>
              <div className="position-metric-value">{data.concentration_metrics.top_3_concentration}%</div>
            </div>
            <div className="position-metric-card">
              <div className="position-metric-label">Top 5 Concentration</div>
              <div className="position-metric-value">{data.concentration_metrics.top_5_concentration}%</div>
            </div>
            <div className="position-metric-card">
              <div className="position-metric-label">Top 10 Concentration</div>
              <div className="position-metric-value">{data.concentration_metrics.top_10_concentration}%</div>
            </div>
          </div>

          <div className="position-concentration">
            <div className="chart-section">
              <h3>Top 10 Position Weights</h3>
              <div className="chart-container">
                {positionWeightChart && <Bar data={positionWeightChart} options={BAR_OPTIONS} />}
              </div>
            </div>

            <div className="table-section">
              <h3>Position Concentration Details</h3>
              <div className="table-container">
                <table className="concentration-table">
                  <thead>
                    <tr>
                      <th>Position</th>
                      <th>Weight (%)</th>
                      <th>Market Value</th>
                      <th>Sector</th>
                      <th>Industry</th>
                      <th>Market Cap</th>
                    </tr>
                  </thead>
                  <tbody>
                    {data.portfolio_data.map((item, index) => (
                      <tr key={index}>
                        <td>{item.ticker}</td>
                        <td>{item.weight.toFixed(1)}%</td>
                        <td>${item.market_value.toLocaleString()}</td>
                        <td>{item.sector}</td>
                        <td>{item.industry}</td>
                        <td>{item.market_cap.toLocaleString()}</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </div>
          </div>
        </>
      )}

      {activeTab === 'sector' && (
        <div className="sector-concentration">
          <div className="sector-analysis-section">
            <h3>Sector Concentration Analysis</h3>
            <div className="metrics-grid">
              <div className="metric-card">
                <div className="metric-label">Largest Sector</div>
                <div className="metric-value">{largestSector}</div>
              </div>
              <div className="metric-card">
                <div className="metric-label">Number of Sectors</div>
                <div className="metric-value">{data.sector_concentration.sectors.length}</div>
              </div>
            </div>
          </div>

          <div className="chart-section">
            <h3>Portfolio Sector Allocation</h3>
            <div className="chart-container">
              {sectorPieChart && <Doughnut data={sectorPieChart} options={PIE_OPTIONS} />}
            </div>
          </div>

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
                  {sectorBreakdown.map((sector, index) => (
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
          <div className="market-cap-analysis-section">
            <h3>Market Cap Concentration Analysis</h3>
            <div className="metrics-grid">
              <div className="metric-card">
                <div className="metric-label">Largest Market Cap Category</div>
                <div className="metric-value">{largestMarketCapCategory}</div>
              </div>
              <div className="metric-card">
                <div className="metric-label">Number of Market Cap Categories</div>
                <div className="metric-value">{data.market_cap_concentration.categories.length}</div>
              </div>
            </div>
          </div>

          <div className="chart-section">
            <h3>Portfolio Market Cap Allocation</h3>
            <div className="chart-container">
              {marketCapPieChart && <Doughnut data={marketCapPieChart} options={PIE_OPTIONS} />}
            </div>
          </div>

          <div className="table-section">
            <h3>Market Cap Breakdown</h3>
            <div className="table-container">
              <table className="concentration-table">
                <thead>
                  <tr>
                    <th>Category</th>
                    <th>Weight</th>
                    <th>Positions</th>
                    <th>Position List</th>
                    <th>Average Market Cap</th>
                  </tr>
                </thead>
                <tbody>
                  {marketCapBreakdown.map((category, index) => (
                    <tr key={index}>
                      <td>{category.name}</td>
                      <td>{category.weight.toFixed(1)}%</td>
                      <td>{category.positions}</td>
                      <td>{category.positionList}</td>
                      <td>${category.avgMarketCap.toLocaleString()}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>
        </div>
      )}

      {activeTab === 'risk-scoring' && <RiskScoring />}
    </div>
  );
};

export default ConcentrationRiskPage;
