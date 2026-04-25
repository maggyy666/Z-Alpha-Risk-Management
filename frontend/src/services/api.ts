import axios, { AxiosRequestConfig } from 'axios';

const API_BASE_URL = import.meta.env.VITE_API_BASE || 'http://localhost:8000';

const api = axios.create({
  baseURL: API_BASE_URL,
  headers: { 'Content-Type': 'application/json' },
});

// ---------- Type definitions ----------

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

export interface MarketCapBucketEntry {
  ticker: string;
  market_cap: number;
  weight: number;
  market_value: number;
}

export interface MarketCapConcentration {
  categories: string[];
  weights: number[];
  details: { [category: string]: MarketCapBucketEntry[] };
  hhi: number;
  effective_categories: number;
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
  username?: string;
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
    'High Liquidity (8-10)': number;
    'Medium Liquidity (5-8)': number;
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

// User profile / portfolio CRUD

export interface UserPortfolioItem {
  ticker: string;
  shares: number;
  price: number;
  market_value: number;
  sector?: string;
  industry?: string;
}

export interface UserPortfolioResponse {
  username: string;
  portfolio_items: UserPortfolioItem[];
  total_market_value: number;
  total_positions: number;
}

export interface TickerSuggestion {
  symbol: string;
  name?: string;
  exchange?: string;
}

export interface TickerSearchResponse {
  suggestions: TickerSuggestion[];
}

export interface PortfolioMutationResponse {
  success: boolean;
  message?: string;
  data_source?: string;
  updated_items?: number;
  new_items?: number;
  total_items?: number;
  error?: string;
}

export interface InvalidateUserResponse {
  ok: boolean;
  message: string;
}

export interface HealthResponse {
  status: string;
}

// ---------- Request helper ----------

interface RequestOptions {
  params?: Record<string, unknown>;
  data?: unknown;
}

// All GETs get a `_t=<now>` cache buster to avoid stale browser caches.
// Mutations don't need it; backend cache invalidation handles those.
async function request<T>(
  method: 'get' | 'post' | 'delete' | 'put',
  url: string,
  { params, data }: RequestOptions = {},
): Promise<T> {
  const config: AxiosRequestConfig = {
    method,
    url,
    data,
    params: method === 'get' ? { ...(params || {}), _t: Date.now() } : params,
  };
  try {
    const res = await api.request<T>(config);
    return res.data;
  } catch (err) {
    console.error(`[api] ${method.toUpperCase()} ${url} failed:`, err);
    throw err;
  }
}

// ---------- ApiService ----------

class ApiService {
  // Analytics endpoints
  getVolatilityData(forecastModel = 'EWMA (5D)', username = 'admin') {
    return request<VolatilityData>('get', '/volatility-data', {
      params: { forecast_model: forecastModel, username },
    });
  }

  getFactorExposureData(username = 'admin') {
    return request<FactorExposureResponse>('get', '/factor-exposure-data', {
      params: { username },
    });
  }

  getLatestFactorExposures(username = 'admin') {
    return request<LatestFactorExposuresResponse>('get', '/latest-factor-exposures', {
      params: { username },
    });
  }

  getConcentrationRiskData(username = 'admin') {
    return request<ConcentrationRiskResponse>('get', '/concentration-risk-data', {
      params: { username },
    });
  }

  getRiskScoringData(username = 'admin') {
    return request<RiskScoringResponse>('get', '/risk-scoring', {
      params: { username },
    });
  }

  getStressTestingData(username = 'admin') {
    return request<StressTestingResponse>('get', '/stress-testing', {
      params: { username },
    });
  }

  getForecastRiskContributionData(
    volModel = 'EWMA (5D)',
    tickers: string[] = [],
    includePortfolioBar = true,
    username = 'admin',
  ) {
    return request<ForecastRiskContributionResponse>('get', '/forecast-risk-contribution', {
      params: {
        vol_model: volModel,
        tickers: tickers.length > 0 ? tickers.join(',') : '',
        include_portfolio_bar: includePortfolioBar,
        username,
      },
    });
  }

  getForecastMetrics(username = 'admin') {
    return request<ForecastMetricsResponse>('get', '/forecast-metrics', {
      params: { username },
    });
  }

  getRollingForecast(model: string, window: number, tickers: string[], username = 'admin') {
    return request<RollingForecastResponse>('get', '/rolling-forecast', {
      params: { model, window, tickers: tickers.join(','), username },
    });
  }

  getPortfolioSummary(username = 'admin') {
    return request<PortfolioSummaryResponse>('get', '/portfolio-summary', {
      params: { username },
    });
  }

  getRealizedMetrics(username = 'admin') {
    return request<RealizedMetricsResponse>('get', '/realized-metrics', {
      params: { username },
    });
  }

  getRollingMetrics(
    metric = 'vol',
    window = 21,
    tickers: string[] = ['PORTFOLIO'],
    username = 'admin',
  ) {
    return request<RollingMetricsResponse>('get', '/rolling-metric', {
      params: { metric, window, tickers: tickers.join(','), username },
    });
  }

  getLiquidityOverview(username = 'admin') {
    return request<LiquidityOverviewResponse>('get', '/liquidity-overview', {
      params: { username },
    });
  }

  getLiquidityVolumeAnalysis(username = 'admin') {
    return request<LiquidityVolumeAnalysisResponse>('get', '/liquidity-volume-analysis', {
      params: { username },
    });
  }

  getLiquidityAlerts(username = 'admin') {
    return request<LiquidityAlertsResponse>('get', '/liquidity-alerts', {
      params: { username },
    });
  }

  // Auth + session
  getSession(username = 'admin') {
    return request<SessionResponse>('get', '/session', { params: { username } });
  }

  login(credentials: LoginRequest) {
    return request<LoginResponse>('post', '/login', { data: credentials });
  }

  // User profile / portfolio CRUD
  getUserPortfolio(username = 'admin') {
    return request<UserPortfolioResponse>('get', `/user-portfolio/${username}`);
  }

  savePortfolio(username: string, items: Array<{ ticker: string; shares: number }>) {
    return request<PortfolioMutationResponse>('post', `/user-portfolio/${username}`, {
      data: items,
    });
  }

  addTickerToPortfolio(username: string, ticker: string, shares: number) {
    return request<PortfolioMutationResponse>('post', `/add-ticker/${username}`, {
      params: { ticker, shares },
    });
  }

  removeTickerFromPortfolio(username: string, ticker: string) {
    return request<PortfolioMutationResponse>('delete', `/remove-ticker/${username}`, {
      params: { ticker },
    });
  }

  searchTickers(query: string) {
    return request<TickerSearchResponse>('get', '/ticker-search', { params: { query } });
  }

  invalidateUser(username: string) {
    return request<InvalidateUserResponse>('post', `/invalidate-user/${username}`);
  }

  // Misc
  initializePortfolio() {
    return request<{ success: boolean; message?: string }>('post', '/initialize-portfolio');
  }

  fetchHistoricalData(symbol: string) {
    return request<{ success: boolean; symbol: string }>('post', `/fetch-data/${symbol}`);
  }

  healthCheck() {
    return request<HealthResponse>('get', '/health');
  }

  /**
   * Pre-warm the backend's TTL cache for the heavy dashboard endpoints so the
   * user doesn't pay computation latency on first navigation. Fired in the
   * background by DashboardLayout after login -- failures are swallowed (the
   * pages will still trigger their own fetch on mount).
   *
   * Concentration is awaited first because almost every other endpoint reads
   * portfolio weights from it (via the facade shim); warming it sequentially
   * lets the parallel fan-out hit the cache instead of recomputing N times.
   */
  async warmDashboardCache(username = 'admin'): Promise<void> {
    try {
      await this.getConcentrationRiskData(username);
    } catch { /* downstream calls will retry */ }

    await Promise.allSettled([
      this.getRiskScoringData(username),
      this.getFactorExposureData(username),
      this.getLatestFactorExposures(username),
      this.getForecastRiskContributionData('EWMA (5D)', [], true, username),
      this.getForecastMetrics(username),
      this.getRealizedMetrics(username),
      this.getStressTestingData(username),
      this.getLiquidityOverview(username),
      this.getVolatilityData('EWMA (5D)', username),
      // Aggregator -- depends on the above; placed last so its sub-fetches
      // hit the freshly-populated cache.
      this.getPortfolioSummary(username),
    ]);
  }
}

const apiService = new ApiService();
export default apiService;
