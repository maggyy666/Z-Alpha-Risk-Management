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

export interface PortfolioItem {
  ticker: string;
  shares: number;
  price: number;
  market_value: number;
  weight: number;
  sector: string;
  market_cap: number;
}

export interface ConcentrationMetrics {
  largest_position: number;
  top_3_concentration: number;
  top_5_concentration: number;
  top_10_concentration: number;
  herfindahl_index: number;
  effective_positions: number;
}

export interface SectorConcentration {
  sectors: string[];
  weights: number[];
  hhi: number;
  effective_sectors: number;
}

export interface ConcentrationRiskResponse {
  portfolio_data: PortfolioItem[];
  concentration_metrics: ConcentrationMetrics;
  sector_concentration: SectorConcentration;
  total_market_value: number;
}

export interface RiskScoringResponse {
  score_weights: { [key: string]: number };
  component_scores: { [key: string]: number };
  risk_contribution_pct: { [key: string]: number };
  alerts: Array<{ severity: string; text: string }>;
  recommendations: string[];
  raw_metrics: {
    hhi: number;
    n_eff: number;
    vol_ann_pct: number;
    beta_market: number;
    avg_pair_corr: number;
    pairs_total: number;
    pairs_high_corr: number;
    max_drawdown_pct: number;
  };
}

export interface StressTestingResponse {
  market_regime: {
    label: string;
    volatility_pct: number;
    correlation: number;
    momentum_pct: number;
    radar: {
      volatility: number;
      correlation: number;
      momentum: number;
    };
  };
  scenarios: {
    scenarios_analyzed: number;
    scenarios_excluded: number;
    results: Array<{
      name: string;
      start: string;
      end: string;
      days: number;
      weight_coverage_pct: number;
      return_pct: number;
      max_drawdown_pct: number;
    }>;
    excluded: Array<{
      name: string;
      reason: string;
    }>;
  };
}

export interface ForecastRiskContributionResponse {
  tickers: string[];
  marginal_rc_pct: number[];
  total_rc_pct: number[];
  weights_pct: number[];
  portfolio_vol: number;
  vol_model: string;
}

class ApiService {
  async getVolatilityData(forecastModel: string = 'EWMA (5D)', username: string = "admin"): Promise<VolatilityData> {
    try {
      const response = await api.get('/volatility-data', {
        params: { forecast_model: forecastModel, username }
      });
      return response.data;
    } catch (error) {
      console.error('Error fetching volatility data:', error);
      throw error;
    }
  }

  async getFactorExposureData(username: string = "admin"): Promise<FactorExposureResponse> {
    try {
      const response = await api.get('/factor-exposure-data', {
        params: { username }
      });
      return response.data;
    } catch (error) {
      console.error('Error fetching factor exposure data:', error);
      throw error;
    }
  }

  async getConcentrationRiskData(username: string = "admin"): Promise<ConcentrationRiskResponse> {
    try {
      const response = await api.get('/concentration-risk-data', {
        params: { username }
      });
      return response.data;
    } catch (error) {
      console.error('Error fetching concentration risk data:', error);
      throw error;
    }
  }

  async getRiskScoringData(username: string = "admin"): Promise<RiskScoringResponse> {
    try {
      const response = await api.get('/risk-scoring', {
        params: { username }
      });
      return response.data;
    } catch (error) {
      console.error('Error fetching risk scoring data:', error);
      throw error;
    }
  }

  async getStressTestingData(username: string = "admin"): Promise<StressTestingResponse> {
    try {
      const response = await api.get('/stress-testing', {
        params: { username }
      });
      return response.data;
    } catch (error) {
      console.error('Error fetching stress testing data:', error);
      throw error;
    }
  }

  async getForecastRiskContributionData(volModel: string = 'EWMA (5D)', username: string = "admin"): Promise<ForecastRiskContributionResponse> {
    try {
      const response = await api.get('/forecast-risk-contribution', {
        params: { vol_model: volModel, username }
      });
      return response.data;
    } catch (error) {
      console.error('Error fetching forecast risk contribution data:', error);
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

const apiService = new ApiService();
export default apiService; 