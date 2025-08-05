import React, { useState, useEffect } from 'react';
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
import SelectableTags from '../components/SelectableTags';
import DateRangeSelector, { DateRange } from '../components/DateRangeSelector';
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

const FactorExposurePage: React.FC = () => {
  const [factorData, setFactorData] = useState<FactorExposureResponse | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  
  // Available options from portfolio
  const [availableTickers, setAvailableTickers] = useState<string[]>([]);
  const [availableFactors, setAvailableFactors] = useState<string[]>([]);
  
  // Selected filters - inicjalizuj puste, będą ustawione dynamicznie
  const [selectedFactors, setSelectedFactors] = useState<string[]>([]);
  const [selectedTickers, setSelectedTickers] = useState<string[]>([]);
  const [selectedTickersR2, setSelectedTickersR2] = useState<string[]>([]);

  // Date range state
  const [selectedDateRange, setSelectedDateRange] = useState<DateRange>('1Y');

  useEffect(() => {
    fetchFactorExposureData();
  }, []); // Added fetchFactorExposureData to dependency array to resolve warning

  const getDateRangeFilter = (range: DateRange) => {
    const now = new Date();
    const startDate = new Date();
    
    switch (range) {
      case 'YTD':
        startDate.setMonth(0, 1); // 1 stycznia tego roku
        break;
      case '1Y':
        startDate.setFullYear(now.getFullYear() - 1);
        break;
      case '3Y':
        startDate.setFullYear(now.getFullYear() - 3);
        break;
      case '5Y':
        startDate.setFullYear(now.getFullYear() - 5);
        break;
      case 'All':
        return () => true; // Wszystkie daty
      default:
        startDate.setFullYear(now.getFullYear() - 1);
    }
    
    return (date: string) => new Date(date) >= startDate;
  };

  const filterDataByDateRange = (data: FactorExposureData[], range: DateRange) => {
    const filterFn = getDateRangeFilter(range);
    return data.filter(item => filterFn(item.date));
  };

  const fetchFactorExposureData = async () => {
    try {
      setLoading(true);
      console.log('Fetching factor exposure data...');
      const data = await apiService.getFactorExposureData("admin"); // Można zmienić na dynamiczne
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
          // Weź pierwsze dwa tickery z portfolio użytkownika
          const defaultTickers = data.available_tickers.slice(0, 2);
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
  };

  // Generate sample data for charts (until backend is ready)
  const generateSampleData = () => {
    if (!factorData) return { factorExposures: [], r2Data: [] };

    const factorExposures: FactorExposureData[] = [];
    const r2Data: FactorExposureData[] = [];

    // Use real data from backend with date filtering
    if (factorData.factor_exposures) {
      const filteredFactorExposures = filterDataByDateRange(factorData.factor_exposures, selectedDateRange);
      filteredFactorExposures.forEach((item: any) => {
        if (selectedFactors.includes(item.factor) && selectedTickers.includes(item.ticker)) {
          factorExposures.push(item);
        }
      });
    }

    if (factorData.r2_data) {
      const filteredR2Data = filterDataByDateRange(factorData.r2_data, selectedDateRange);
      filteredR2Data.forEach((item: any) => {
        if (selectedTickersR2.includes(item.ticker)) {
          r2Data.push(item);
        }
      });
    }

    return { factorExposures, r2Data };
  };

  const sampleData = generateSampleData();

  const createFactorExposureChartData = () => {
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
        const data = sampleData.factorExposures
          .filter(d => d.factor === factor && d.ticker === ticker)
          .sort((a, b) => new Date(a.date).getTime() - new Date(b.date).getTime());

        if (data.length > 0) {
          // Agreguj dane - bierz co 14 dni (2 tygodnie) żeby zmniejszyć gęstość
          const aggregatedData = [];
          for (let i = 0; i < data.length; i += 14) {
            aggregatedData.push(data[i]);
          }
          
          // Użyj różnych kolorów dla każdej kombinacji factor-ticker
          const colorIndex = (factorIndex * selectedTickers.length + tickerIndex) % colors.length;
          
          datasets.push({
            label: `${factor}, ${ticker}`,
            data: aggregatedData.map(d => d.beta),
            borderColor: colors[colorIndex],
            backgroundColor: 'transparent',
            borderWidth: 2,
            fill: false,
            tension: 0.1,
            borderDash: tickerIndex % 2 === 0 ? [] : [5, 5]
          });
        }
      });
    });

    // Get unique dates for labels (agregowane)
    const allDates = sampleData.factorExposures
      .map(d => d.date)
      .filter((date, index, arr) => arr.indexOf(date) === index)
      .sort();

    // Agreguj daty - bierz co 14 dni (2 tygodnie)
    const aggregatedDates: string[] = [];
    for (let i = 0; i < allDates.length; i += 14) {
      aggregatedDates.push(allDates[i]);
    }

    // Format labels - lata tylko na początku i końcu
    const labels = aggregatedDates.map((date, index) => {
      const dateObj = new Date(date);
      const year = dateObj.getFullYear();
      const month = dateObj.getMonth();
      
      // Jeśli to pierwszy lub ostatni punkt, lub zmiana roku
      if (index === 0 || index === aggregatedDates.length - 1 || 
          (index > 0 && new Date(aggregatedDates[index - 1]).getFullYear() !== year)) {
        return year.toString();
      }
      
      // W środku pokazuj miesiące
      const monthNames = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 
                         'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec'];
      return monthNames[month];
    });

    return {
      labels,
      datasets
    };
  };

  const createR2ChartData = () => {
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
      const data = sampleData.r2Data
        .filter(d => d.ticker === ticker)
        .sort((a, b) => new Date(a.date).getTime() - new Date(b.date).getTime());

      if (data.length > 0) {
        // Agreguj dane - bierz co 14 dni (2 tygodnie) żeby zmniejszyć gęstość
        const aggregatedData = [];
        for (let i = 0; i < data.length; i += 14) {
          aggregatedData.push(data[i]);
        }
        
        datasets.push({
          label: ticker,
          data: aggregatedData.map(d => d.r2),
          borderColor: colors[index % colors.length],
          backgroundColor: 'transparent',
          borderWidth: 2,
          fill: false,
          tension: 0.1
        });
      }
    });

    // Get unique dates for labels (agregowane)
    const allDates = sampleData.r2Data
      .map(d => d.date)
      .filter((date, index, arr) => arr.indexOf(date) === index)
      .sort();

    // Agreguj daty - bierz co 14 dni (2 tygodnie)
    const aggregatedDates: string[] = [];
    for (let i = 0; i < allDates.length; i += 14) {
      aggregatedDates.push(allDates[i]);
    }

    // Format labels - lata tylko na początku i końcu
    const labels = aggregatedDates.map((date, index) => {
      const dateObj = new Date(date);
      const year = dateObj.getFullYear();
      const month = dateObj.getMonth();
      
      // Jeśli to pierwszy lub ostatni punkt, lub zmiana roku
      if (index === 0 || index === aggregatedDates.length - 1 || 
          (index > 0 && new Date(aggregatedDates[index - 1]).getFullYear() !== year)) {
        return year.toString();
      }
      
      // W środku pokazuj miesiące
      const monthNames = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 
                         'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec'];
      return monthNames[month];
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
      <div className="section">
        <div className="section-header">
          <h2>Rolling Factor Exposures</h2>
          <div className="controls">
            <SelectableTags title="Select Factors" selectedItems={selectedFactors} availableItems={availableFactors} onSelectionChange={setSelectedFactors} placeholder="Add factor" />
            <SelectableTags title="Select Tickers" selectedItems={selectedTickers} availableItems={availableTickers} onSelectionChange={setSelectedTickers} placeholder="Add ticker" />
          </div>
          <DateRangeSelector 
            selectedRange={selectedDateRange}
            onRangeChange={setSelectedDateRange}
          />
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
          </div>
          <DateRangeSelector 
            selectedRange={selectedDateRange}
            onRangeChange={setSelectedDateRange}
          />
        </div>
        <div className="chart-container">
          <Line data={createR2ChartData()} options={{ ...chartOptions, scales: { ...chartOptions.scales, y: { ...chartOptions.scales.y } } }} />
        </div>
      </div>
    </div>
  );
};

export default FactorExposurePage; 