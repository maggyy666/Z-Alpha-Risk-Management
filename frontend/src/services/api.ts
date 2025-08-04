import axios from 'axios';

const API_BASE_URL = 'http://localhost:8000';

const api = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
});

export interface PortfolioData {
  symbol: string;
  forecast_volatility_pct: number;
  current_weight_pct: number;
  adj_volatility_weight_pct: number;
  last_price: number;
  current_mv?: number;
  target_mv?: number;
  delta_mv?: number;
  delta_shares?: number;
  sharpe_ratio?: number;
}

export interface VolatilityData {
  portfolio_data: PortfolioData[];
  source?: string;
}

export interface FactorExposureData {
  date: string;
  ticker: string;
  factor: string;
  beta: number;
  r2?: number;
}

export interface FactorExposureResponse {
  factor_exposures: FactorExposureData[];
  r2_data: FactorExposureData[];
  available_factors: string[];
  available_tickers: string[];
}

class ApiService {
  async getVolatilityData(forecastModel: string = 'EWMA (5D)'): Promise<VolatilityData> {
    try {
      const response = await api.get('/volatility-data', {
        params: { forecast_model: forecastModel }
      });
      return response.data;
    } catch (error) {
      console.error('Error fetching volatility data:', error);
      throw error;
    }
  }

  async getFactorExposureData(): Promise<FactorExposureResponse> {
    try {
      const response = await api.get('/factor-exposure-data');
      return response.data;
    } catch (error) {
      console.error('Error fetching factor exposure data:', error);
      throw error;
    }
  }

  async initializePortfolio(): Promise<any> {
    try {
      const response = await api.post('/initialize-portfolio');
      return response.data;
    } catch (error) {
      console.error('Error initializing portfolio:', error);
      throw error;
    }
  }

  async fetchHistoricalData(symbol: string): Promise<any> {
    try {
      const response = await api.post(`/fetch-data/${symbol}`);
      return response.data;
    } catch (error) {
      console.error(`Error fetching data for ${symbol}:`, error);
      throw error;
    }
  }

  async healthCheck(): Promise<any> {
    try {
      const response = await api.get('/health');
      return response.data;
    } catch (error) {
      console.error('Health check failed:', error);
      throw error;
    }
  }
}

export default new ApiService(); 