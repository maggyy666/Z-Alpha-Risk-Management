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
  industry: string;
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

export interface MarketCapConcentration {
  categories: string[];
  weights: number[];
  hhi: number;
  effective_categories: number;
  details: {
    [category: string]: Array<{
      ticker: string;
      market_cap: number;
      weight: number;
      market_value: number;
    }>;
  };
}

export interface ConcentrationRiskResponse {
  portfolio_data: PortfolioItem[];
  concentration_metrics: ConcentrationMetrics;
  sector_concentration: SectorConcentration;
  market_cap_concentration: MarketCapConcentration;
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

export interface ForecastMetricsResponse {
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

export interface RollingForecastResponse {
  data: Array<{
    date: string;
    ticker: string;
    vol_pct: number;
  }>;
  model: string;
  window: number;
}

export interface LatestFactorExposuresResponse {
  as_of: string;
  factors: string[];
  data: Array<{
    ticker: string;
    [key: string]: string | number;
  }>;
}

export interface RealizedMetricsResponse {
  metrics: Array<{
    ticker: string;
    ann_return_pct: number;
    volatility_pct: number;
    sharpe_ratio: number;
    sortino_ratio: number;
    skewness: number;
    kurtosis: number;
    max_drawdown_pct: number;
    var_95_pct: number;
    cvar_95_pct: number;
    hit_ratio_pct: number;
    beta_ndx: number;
    beta_spy: number;
    up_capture_ndx_pct: number;
    down_capture_ndx_pct: number;
    tracking_error_pct: number;
    information_ratio: number;
  }>;
}

export interface RollingMetricsResponse {
  datasets: Array<{
    ticker: string;
    dates: string[];
    values: number[];
  }>;
  metric: string;
  window: number;
}

export interface LiquidityOverviewResponse {
  overview: {
    overall_score: number;
    risk_level: string;
    estimated_liquidation_time: string;
  };
  distribution: {
    "High Liquidity (8-10)": number;
    "Medium Liquidity (5-8)": number;
  };
  volume_analysis: {
    avg_volume_global: number;
    total_portfolio_volume: number;
    volume_weighted_avg: number;
  };
  position_details: Array<{
    ticker: string;
    shares: number;
    market_value: number;
    weight_pct: number;
    avg_volume: number;
    current_volume: number;
    spread_pct: number;
    volume_category: string;
    volume_score: number;
    liquidity_score: number;
    liq_days: number;
  }>;
  alerts: Array<{
    severity: string;
    text: string;
  }>;
}

export interface LiquidityVolumeAnalysisResponse {
  avg_volume_global: number;
  total_portfolio_volume: number;
  volume_weighted_avg: number;
}

export interface LiquidityAlertsResponse {
  alerts: Array<{
    severity: string;
    text: string;
  }>;
}

export interface SessionResponse {
  logged_in: boolean;
  username?: string;
  email?: string;
}

export interface LoginRequest {
  username: string;
  password: string;
}

export interface LoginResponse {
  success: boolean;
  message: string;
  username?: string;
}

export interface PortfolioSummaryResponse {
  risk_score: {
    overall_score: number;
    risk_level: string;
    highest_risk_component: string;
    highest_risk_percentage: number;
    high_risk_components_count: number;
  };
  portfolio_overview: {
    total_market_value: number;
    total_positions: number;
    largest_position: number;
    top_3_concentration: number;
    volatility_egarch: number;
    cvar_percentage: number;
    cvar_usd: number;
    top_risk_contributor: {
      ticker: string;
      weight_pct: number;
      vol_contribution_pct: number;
    };
  };
  portfolio_positions: Array<{
    ticker: string;
    weight: number;
    shares: number;
    market_value: number;
    sector: string;
  }>;
  flags?: {
    high_vol?: boolean;
    high_risk_score?: boolean;
    high_cvar?: boolean;
  };
}

class ApiService {
  async getVolatilityData(forecastModel: string = 'EWMA (5D)', username: string = "admin"): Promise<VolatilityData> {
    try {
      const response = await api.get('/volatility-data', {
        params: { 
          forecast_model: forecastModel, 
          username,
          _t: Date.now() // Add timestamp to prevent caching
        }
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
        params: { 
          username,
          _t: Date.now() // Add timestamp to prevent caching
        }
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
        params: { 
          username,
          _t: Date.now() // Add timestamp to prevent caching
        }
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
        params: { 
          username,
          _t: Date.now() // Add timestamp to prevent caching
        }
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
        params: { 
          username,
          _t: Date.now() // Add timestamp to prevent caching
        }
      });
      return response.data;
    } catch (error) {
      console.error('Error fetching stress testing data:', error);
      throw error;
    }
  }

  async getForecastRiskContributionData(volModel: string = 'EWMA (5D)', tickers: string[] = [], includePortfolioBar: boolean = true, username: string = "admin"): Promise<ForecastRiskContributionResponse> {
    try {
      console.log('[API] getForecastRiskContributionData called with:', { volModel, tickers, includePortfolioBar, username });
      
      const params = { 
        vol_model: volModel, 
        tickers: tickers.length > 0 ? tickers.join(',') : '',
        include_portfolio_bar: includePortfolioBar,
        username,
        _t: Date.now() // Add timestamp to prevent caching
      };
      
      console.log('[API] Request params:', params);
      
      const response = await api.get('/forecast-risk-contribution', { params });
      
      console.log('[API] Response data:', response.data);
      
      return response.data;
    } catch (error) {
      console.error('Error fetching forecast risk contribution data:', error);
      throw error;
    }
  }

  async getForecastMetrics(username: string = "admin"): Promise<ForecastMetricsResponse> {
    try {
      const response = await api.get('/forecast-metrics', {
        params: { 
          username,
          _t: Date.now() // Add timestamp to prevent caching
        }
      });
      return response.data;
    } catch (error) {
      console.error('Error fetching forecast metrics data:', error);
      throw error;
    }
  }

  async getRollingForecast(model: string, window: number, tickers: string[], username: string = "admin"): Promise<RollingForecastResponse> {
    try {
      const response = await api.get('/rolling-forecast', {
        params: { 
          model, 
          window, 
          tickers: tickers.join(','), 
          username,
          _t: Date.now() // Add timestamp to prevent caching
        }
      });
      return response.data;
    } catch (error) {
      console.error('Error fetching rolling forecast data:', error);
      throw error;
    }
  }

  async getLatestFactorExposures(username: string = "admin"): Promise<LatestFactorExposuresResponse> {
    try {
      const response = await api.get('/latest-factor-exposures', {
        params: { 
          username,
          _t: Date.now() // Add timestamp to prevent caching
        }
      });
      return response.data;
    } catch (error) {
      console.error('Error fetching latest factor exposures data:', error);
      throw error;
    }
  }

  async getPortfolioSummary(username: string = "admin"): Promise<PortfolioSummaryResponse> {
    try {
      const response = await api.get('/portfolio-summary', {
        params: { 
          username,
          _t: Date.now() // Add timestamp to prevent caching
        }
      });
      return response.data;
    } catch (error) {
      console.error('Error fetching portfolio summary data:', error);
      throw error;
    }
  }

  async getRealizedMetrics(username: string = "admin"): Promise<RealizedMetricsResponse> {
    try {
      const response = await api.get('/realized-metrics', {
        params: { 
          username,
          _t: Date.now() // Add timestamp to prevent caching
        }
      });
      return response.data;
    } catch (error) {
      console.error('Error fetching realized metrics data:', error);
      throw error;
    }
  }

  async getRollingMetrics(
    metric: string = "vol",
    window: number = 21,
    tickers: string[] = ["PORTFOLIO"],
    username: string = "admin"
  ): Promise<RollingMetricsResponse> {
    try {
      const response = await api.get('/rolling-metric', {
        params: { 
          metric, 
          window, 
          tickers: tickers.join(','), 
          username,
          _t: Date.now() // Add timestamp to prevent caching
        }
      });
      return response.data;
    } catch (error) {
      console.error('Error fetching rolling metrics data:', error);
      throw error;
    }
  }

  async getLiquidityOverview(username: string = "admin"): Promise<LiquidityOverviewResponse> {
    try {
      const response = await api.get('/liquidity-overview', {
        params: { 
          username,
          _t: Date.now() // Add timestamp to prevent caching
        }
      });
      return response.data;
    } catch (error) {
      console.error('Error fetching liquidity overview data:', error);
      throw error;
    }
  }

  async getLiquidityVolumeAnalysis(username: string = "admin"): Promise<LiquidityVolumeAnalysisResponse> {
    try {
      const response = await api.get('/liquidity-volume-analysis', {
        params: { 
          username,
          _t: Date.now() // Add timestamp to prevent caching
        }
      });
      return response.data;
    } catch (error) {
      console.error('Error fetching liquidity volume analysis data:', error);
      throw error;
    }
  }

  async getLiquidityAlerts(username: string = "admin"): Promise<LiquidityAlertsResponse> {
    try {
      const response = await api.get('/liquidity-alerts', {
        params: { 
          username,
          _t: Date.now() // Add timestamp to prevent caching
        }
      });
      return response.data;
    } catch (error) {
      console.error('Error fetching liquidity alerts data:', error);
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

  async getSession(username: string = 'admin'): Promise<SessionResponse> {
    try {
      const response = await api.get(`/session?username=${username}`);
      return response.data;
    } catch (error) {
      console.error('Session error:', error);
      throw error;
    }
  }

  async login(credentials: LoginRequest): Promise<LoginResponse> {
    try {
      const response = await api.post('/login', credentials);
      return response.data;
    } catch (error) {
      console.error('Login error:', error);
      throw error;
    }
  }

  async getUserPortfolio(username: string = "admin"): Promise<any> {
    try {
      const response = await api.get(`/user-portfolio/${username}`);
      return response.data;
    } catch (error) {
      console.error('Error fetching user portfolio:', error);
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