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
  Filler
} from 'chart.js';
import apiService from '../services/api';
import { useSession } from '../contexts/SessionContext';
import SelectableTags from '../components/SelectableTags';

import './FactorExposurePage.css';

ChartJS.register(
  CategoryScale,
  LinearScale,
  PointElement,
  LineElement,
  Title,
  Tooltip,
  Legend,
  Filler
);

interface FactorExposureData {
  date: string;
  ticker: string;
  factor: string;
  beta: number;
  r2?: number;
}

interface FactorExposureResponse {
  factor_exposures: FactorExposureData[];
  r2_data: FactorExposureData[];
  available_factors: string[];
  available_tickers: string[];
}

interface LatestFactorExposuresSectionProps {
  data: any;
  loading: boolean;
  error: string | null;
  onRetry: () => void;
}

const LatestFactorExposuresSection: React.FC<LatestFactorExposuresSectionProps> = ({ 
  data, 
  loading, 
  error, 
  onRetry 
}) => {
  if (loading) {
    return (
      <div className="section">
        <div className="loading">Loading latest factor exposures...</div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="section">
        <div className="error">
          <p>{error}</p>
          <button onClick={onRetry} className="retry-button">
            Retry
          </button>
        </div>
      </div>
    );
  }

  if (!data || !data.data) {
    return (
      <div className="section">
        <div className="error">No latest factor exposures data available</div>
      </div>
    );
  }

  return (
    <>
      {/* Latest Factor Exposures Table */}
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
                {data.factors?.map((factor: string) => (
                  <th key={factor}>{factor}</th>
                ))}
              </tr>
            </thead>
            <tbody>
              {data.data?.map((row: any, index: number) => (
                <tr key={index}>
                  <td className="ticker-cell">{row.ticker}</td>
                  {data.factors?.map((factor: string) => {
                    const value = row[factor];
                    const isPositive = value > 0;
                    const isNegative = value < 0;
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
            {/* Heatmap header */}
            <div className="heatmap-header">
              <div className="heatmap-corner"></div>
              {data.factors?.map((factor: string) => (
                <div key={factor} className="heatmap-factor-header">
                  {factor}
                </div>
              ))}
            </div>
            
            {/* Heatmap rows */}
            {data.data?.map((row: any, rowIndex: number) => (
              <div key={rowIndex} className="heatmap-row">
                <div className="heatmap-ticker-label">{row.ticker}</div>
                                 {data.factors?.map((factor: string, colIndex: number) => {
                   const value = row[factor];
                   const normalizedValue = Math.max(-1, Math.min(1, value)); // Clamp to [-1, 1]
                   const intensity = Math.abs(normalizedValue);
                   const isPositive = normalizedValue > 0;
                   const isNegative = normalizedValue < 0;
                   
                   // Color calculation using our palette - gradient approach
                   let backgroundColor = '#1a1a1a'; // neutral dark
                   let textColor = '#ffffff';
                   
                   if (isPositive) {
                     // Green gradient for positive values using our palette
                     const greenIntensity = Math.round(76 + (179 * intensity)); // #4caf50 to #00ff00
                     backgroundColor = `rgb(0, ${greenIntensity}, 0)`;
                     textColor = '#ffffff';
                   } else if (isNegative) {
                     // Red gradient for negative values using our palette
                     const redIntensity = Math.round(244 + (11 * intensity)); // #f44336 to #ff0000
                     backgroundColor = `rgb(${redIntensity}, 0, 0)`;
                     textColor = '#ffffff';
                   } else {
                     // Neutral for zero values
                     backgroundColor = '#2a2a2a';
                     textColor = '#cccccc';
                   }
                   
                   return (
                     <div 
                       key={colIndex} 
                       className="heatmap-cell"
                       style={{ 
                         backgroundColor,
                         color: textColor,
                         fontWeight: intensity > 0.3 ? '700' : '600'
                       }}
                       title={`${row.ticker} - ${factor}: ${typeof value === 'number' ? value.toFixed(2) : value}`}
                     >
                       {typeof value === 'number' ? value.toFixed(2) : value}
                     </div>
                   );
                 })}
              </div>
            ))}
          </div>
          
          {/* Color legend */}
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
  const [factorData, setFactorData] = useState<FactorExposureResponse | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const { getCurrentUsername } = useSession();
  
  // Available options from portfolio
  const [availableTickers, setAvailableTickers] = useState<string[]>([]);
  const [availableFactors, setAvailableFactors] = useState<string[]>([]);
  
  // Selected filters - inicjalizuj puste, będą ustawione dynamicznie
  const [selectedFactors, setSelectedFactors] = useState<string[]>([]);
  const [selectedTickers, setSelectedTickers] = useState<string[]>([]);
  const [selectedTickersR2, setSelectedTickersR2] = useState<string[]>([]);

  // Date range state - removed, using common date range from backend
  
  // Chart density control
  const [chartDensity, setChartDensity] = useState<'high' | 'medium' | 'low'>('medium');
  
  // R² smoothing control
  const [r2Smoothing, setR2Smoothing] = useState<boolean>(true);

  // Sub-navigation state
  const [activeTab, setActiveTab] = useState<'charts' | 'latest'>('charts');

  // Latest factor exposures state
  const [latestExposuresData, setLatestExposuresData] = useState<any>(null);
  const [latestExposuresLoading, setLatestExposuresLoading] = useState(false);
  const [latestExposuresError, setLatestExposuresError] = useState<string | null>(null);



  // Date range filtering removed - using common date range from backend

  const getAggregationStep = () => {
    switch (chartDensity) {
      case 'high':
        return 1; // Wszystkie punkty
      case 'medium':
        return 7; // Co tydzień
      case 'low':
        return 14; // Co 2 tygodnie
      default:
        return 7;
    }
  };

  const smoothR2Data = (data: FactorExposureData[], windowSize: number = 5) => {
    if (!r2Smoothing || data.length < windowSize) {
      return data;
    }
    
    const smoothed = [];
    for (let i = 0; i < data.length; i++) {
      const start = Math.max(0, i - Math.floor(windowSize / 2));
      const end = Math.min(data.length, i + Math.floor(windowSize / 2) + 1);
      const window = data.slice(start, end);
      
      // Filtruj tylko elementy z r2 i oblicz średnią
      const validR2Items = window.filter(item => item.r2 !== undefined);
      const avgR2 = validR2Items.length > 0 
        ? validR2Items.reduce((sum, item) => sum + (item.r2 || 0), 0) / validR2Items.length
        : (data[i].r2 || 0);
      
      smoothed.push({
        ...data[i],
        r2: avgR2
      });
    }
    
    return smoothed;
  };

  const fetchFactorExposureData = useCallback(async () => {
    try {
      setLoading(true);
      console.log('Fetching factor exposure data...');
      const username = getCurrentUsername();
      const data = await apiService.getFactorExposureData(username);
      console.log('Received data:', data);
      console.log('Available tickers:', data.available_tickers);
      console.log('Available factors:', data.available_factors);
      console.log('Factor exposures count:', data.factor_exposures?.length);
      console.log('R2 data count:', data.r2_data?.length);
      console.log('Sample dates:', data.factor_exposures?.slice(0, 5).map(d => d.date));
      
      setFactorData(data);
      
      // Update available options from backend
      if (data.available_tickers) {
        setAvailableTickers(data.available_tickers);
        // Set default selections based on available data
        if (selectedTickers.length === 0 && data.available_tickers.length > 0) {
          // Prefer GOOGL and META as default tickers
          const preferredTickers = ['GOOGL', 'META'];
          const defaultTickers = preferredTickers.filter(ticker => 
            data.available_tickers.includes(ticker)
          );
          
          // If preferred tickers not available, fall back to first two
          if (defaultTickers.length === 0) {
            defaultTickers.push(...data.available_tickers.slice(0, 2));
          }
          
          setSelectedTickers(defaultTickers);
          setSelectedTickersR2(defaultTickers);
        }
      }
      
      if (data.available_factors) {
        setAvailableFactors(data.available_factors);
        if (selectedFactors.length === 0 && data.available_factors.length > 0) {
          // Weź pierwszy factor jako domyślny
          setSelectedFactors([data.available_factors[0]]);
        }
      }
      
      setError(null);
    } catch (err) {
      console.error('Error fetching data:', err);
      setError('Failed to fetch factor exposure data');
    } finally {
      setLoading(false);
    }
  }, []); // Usunięte zależności - dane ładują się tylko raz

  const fetchLatestFactorExposures = useCallback(async () => {
    try {
      setLatestExposuresLoading(true);
      const data = await apiService.getLatestFactorExposures("admin");
      setLatestExposuresData(data);
      setLatestExposuresError(null);
    } catch (err) {
      console.error('Error fetching latest factor exposures:', err);
      setLatestExposuresError('Failed to fetch latest factor exposures data');
    } finally {
      setLatestExposuresLoading(false);
    }
  }, []);

  useEffect(() => {
    fetchFactorExposureData();
    fetchLatestFactorExposures();
  }, [fetchFactorExposureData, fetchLatestFactorExposures]);

  // Generate sample data for charts (until backend is ready)
  const generateSampleData = () => {
    if (!factorData) return { factorExposures: [], r2Data: [] };

    const factorExposures: FactorExposureData[] = [];
    const r2Data: FactorExposureData[] = [];

    // Use real data from backend - no date filtering needed
    if (factorData.factor_exposures) {
      factorData.factor_exposures.forEach((item: any) => {
        if (selectedFactors.includes(item.factor) && selectedTickers.includes(item.ticker)) {
          factorExposures.push(item);
        }
      });
    }

    if (factorData.r2_data) {
      factorData.r2_data.forEach((item: any) => {
        if (selectedTickersR2.includes(item.ticker)) {
          r2Data.push(item);
        }
      });
    }

    return { factorExposures, r2Data };
  };

  const sampleData = generateSampleData();

  const createFactorExposureChartData = () => {
    if (!factorData || !factorData.factor_exposures) return { labels: [], datasets: [] };
    
    // Get all unique dates for selected tickers and factors
    const allTickers = selectedTickers;
    const allFactors = selectedFactors;
    let allDates: string[] = [];
    
    if (allTickers.length > 0 && allFactors.length > 0) {
      // Collect all dates from all selected tickers and factors
      for (const ticker of allTickers) {
        for (const factor of allFactors) {
          const tickerFactorDates = factorData.factor_exposures
            .filter(d => d.ticker === ticker && d.factor === factor)
            .map(d => d.date);
          allDates = allDates.concat(tickerFactorDates);
        }
      }
      
      // Remove duplicates and sort
      allDates = Array.from(new Set(allDates)).sort();
    }
    
    const datasets: any[] = [];
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

    selectedFactors.forEach((factor, factorIndex) => {
      selectedTickers.forEach((ticker, tickerIndex) => {
        const data = factorData.factor_exposures
          .filter(d => d.factor === factor && d.ticker === ticker)
          .sort((a, b) => new Date(a.date).getTime() - new Date(b.date).getTime());

        if (data.length > 0) {
          // Użyj tylko wspólnych dat
          const colorIndex = (factorIndex * selectedTickers.length + tickerIndex) % colors.length;
          
          // Map data to common dates
          const dataMap = new Map(data.map(d => [d.date, d.beta]));
          const mappedData = allDates.map(date => dataMap.get(date) || null);
          
          datasets.push({
            label: `${factor}, ${ticker}`,
            data: mappedData,
            borderColor: colors[colorIndex],
            backgroundColor: 'transparent',
            borderWidth: 1.5, // Cieńsze linie dla lepszej czytelności
            fill: false,
            tension: 0.1, // Delikatne wygładzenie
            borderDash: tickerIndex % 2 === 0 ? [] : [5, 5],
            pointRadius: 0, // Ukryj punkty dla lepszej czytelności
            pointHoverRadius: 4, // Pokaż punkty tylko przy hover
            pointHoverBackgroundColor: colors[colorIndex],
            pointHoverBorderColor: '#ffffff',
            pointHoverBorderWidth: 2
          });
        }
      });
    });

    // Format labels - lepsze etykiety osi X
    const labels = allDates.map((date, index) => {
      const dateObj = new Date(date);
      const year = dateObj.getFullYear();
      const month = dateObj.getMonth();
      const day = dateObj.getDate();
      
      // Pokaż pełną datę co 3 miesiące
      if (index === 0 || index === allDates.length - 1 || index % 90 === 0) {
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
      if (index > 0 && new Date(allDates[index - 1]).getFullYear() !== year) {
        return year.toString();
      }
      
      return ''; // Puste etykiety dla większości punktów
    });

    return {
      labels,
      datasets
    };
  };

  const createR2ChartData = () => {
    if (!factorData || !factorData.r2_data) return { labels: [], datasets: [] };
    
    // Get all unique dates for selected tickers
    const allTickers = selectedTickersR2;
    let allDates: string[] = [];
    
    if (allTickers.length > 0) {
      // Collect all dates from all selected tickers
      for (const ticker of allTickers) {
        const tickerDates = factorData.r2_data
          .filter(d => d.ticker === ticker)
          .map(d => d.date);
        allDates = allDates.concat(tickerDates);
      }
      
      // Remove duplicates and sort
      allDates = Array.from(new Set(allDates)).sort();
    }
    
    const datasets: any[] = [];
    // Większa paleta kolorów dla R² chart
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

    selectedTickersR2.forEach((ticker, index) => {
      const data = factorData.r2_data
        .filter(d => d.ticker === ticker)
        .sort((a, b) => new Date(a.date).getTime() - new Date(b.date).getTime());

      if (data.length > 0) {
        // Użyj tylko wspólnych dat
        // Zastosuj wygładzanie tylko dla R²
        const smoothedData = smoothR2Data(data, 7); // 7-dniowe wygładzanie
        
        // Map data to common dates
        const dataMap = new Map(smoothedData.map(d => [d.date, d.r2]));
        const mappedData = allDates.map(date => dataMap.get(date) || null);
        
        datasets.push({
          label: ticker,
          data: mappedData,
          borderColor: colors[index % colors.length],
          backgroundColor: 'transparent',
          borderWidth: 2, // Grubsze linie dla R² (łatwiejsze do śledzenia)
          fill: false,
          tension: 0.2, // Większe wygładzenie dla R²
          pointRadius: 0, // Ukryj punkty dla lepszej czytelności
          pointHoverRadius: 4, // Pokaż punkty tylko przy hover
          pointHoverBackgroundColor: colors[index % colors.length],
          pointHoverBorderColor: '#ffffff',
          pointHoverBorderWidth: 2
        });
      }
    });

    // Format labels - lepsze etykiety osi X
    const labels = allDates.map((date, index) => {
      const dateObj = new Date(date);
      const year = dateObj.getFullYear();
      const month = dateObj.getMonth();
      const day = dateObj.getDate();
      
      // Pokaż pełną datę co 3 miesiące
      if (index === 0 || index === allDates.length - 1 || index % 90 === 0) {
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
      if (index > 0 && new Date(allDates[index - 1]).getFullYear() !== year) {
        return year.toString();
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
            const label = context[0].label;
            if (!label || label === '') {
              return 'No date';
            }
            try {
              const date = new Date(label);
              if (isNaN(date.getTime())) {
                return label; // Return original label if it's not a valid date
              }
              return date.toLocaleDateString('en-US', { 
                year: 'numeric', 
                month: 'short', 
                day: 'numeric' 
              });
            } catch (e) {
              return label; // Return original label if parsing fails
            }
          },
          label: function(context: any) {
            const label = context.dataset.label || '';
            const value = context.parsed.y;
            if (value === null || value === undefined) {
              return `${label}: No data`;
            }
            return `${label}: ${value.toFixed(3)}`;
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
        radius: 0, // Usuwam punkty żeby wykres był czystszy
        hoverRadius: 6, // Zwiększam hover radius żeby łatwiej było trafić
        hoverBackgroundColor: '#ffffff',
        hoverBorderColor: '#333',
        hoverBorderWidth: 2
      },
      line: {
        borderWidth: 2,
        tension: 0.1
      }
    },
    interaction: {
      mode: 'index' as const,
      intersect: false
    }
  };

  if (loading) {
    return (
      <div className="factor-exposure-page">
        <div className="loading">
          Loading factor exposure data...
        </div>
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
      {/* Sub-navigation */}
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
                <SelectableTags title="Select Factors" selectedItems={selectedFactors} availableItems={availableFactors} onSelectionChange={setSelectedFactors} placeholder="Add factor" />
                <SelectableTags title="Select Tickers" selectedItems={selectedTickers} availableItems={availableTickers} onSelectionChange={setSelectedTickers} placeholder="Add ticker" />
              </div>
            </div>
            <div className="chart-container">
              <Line data={createFactorExposureChartData()} options={{ ...chartOptions, scales: { ...chartOptions.scales, y: { ...chartOptions.scales.y } } }} />
            </div>
          </div>
          <div className="section">
            <div className="section-header">
              <h2>Rolling R²</h2>
              <div className="controls">
                <SelectableTags title="Select Tickers for R²" selectedItems={selectedTickersR2} availableItems={availableTickers} onSelectionChange={setSelectedTickersR2} placeholder="Add ticker" />
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
              <Line data={createR2ChartData()} options={{ ...chartOptions, scales: { ...chartOptions.scales, y: { ...chartOptions.scales.y } } }} />
            </div>
          </div>
        </>
      )}

      {activeTab === 'latest' && (
        <LatestFactorExposuresSection 
          data={latestExposuresData}
          loading={latestExposuresLoading}
          error={latestExposuresError}
          onRetry={fetchLatestFactorExposures}
        />
      )}
    </div>
  );
};

export default FactorExposurePage; 