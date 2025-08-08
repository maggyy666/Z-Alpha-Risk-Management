import { useSession } from '../contexts/SessionContext';

export interface PortfolioItem {
  ticker: string;
  shares: number;
  price: number;
  market_value: number;
  weight: number;
  sector?: string;
  industry?: string;
  market_cap?: number;
}

export interface PortfolioData {
  items: PortfolioItem[];
  total_market_value: number;
  total_shares: number;
}

class PortfolioService {
  private static instance: PortfolioService;
  private portfolioData: Map<string, PortfolioData> = new Map();

  static getInstance(): PortfolioService {
    if (!PortfolioService.instance) {
      PortfolioService.instance = new PortfolioService();
    }
    return PortfolioService.instance;
  }

  // Get portfolio for specific user
  getPortfolio(username: string): PortfolioData {
    return this.portfolioData.get(username) || {
      items: [],
      total_market_value: 0,
      total_shares: 0
    };
  }

  // Set portfolio for specific user
  setPortfolio(username: string, portfolio: PortfolioData) {
    this.portfolioData.set(username, portfolio);
  }

  // Add ticker to user's portfolio
  addTicker(username: string, ticker: string, shares: number, price: number) {
    const portfolio = this.getPortfolio(username);
    const market_value = shares * price;
    
    const newItem: PortfolioItem = {
      ticker,
      shares,
      price,
      market_value,
      weight: 0 // Will be calculated below
    };

    // Add to portfolio
    portfolio.items.push(newItem);
    
    // Recalculate weights and totals
    this.recalculatePortfolio(username);
  }

  // Remove ticker from user's portfolio
  removeTicker(username: string, ticker: string) {
    const portfolio = this.getPortfolio(username);
    portfolio.items = portfolio.items.filter(item => item.ticker !== ticker);
    this.recalculatePortfolio(username);
  }

  // Update shares for a ticker
  updateShares(username: string, ticker: string, shares: number) {
    const portfolio = this.getPortfolio(username);
    const item = portfolio.items.find(item => item.ticker === ticker);
    if (item) {
      item.shares = shares;
      item.market_value = shares * item.price;
      this.recalculatePortfolio(username);
    }
  }

  // Recalculate portfolio weights and totals
  private recalculatePortfolio(username: string) {
    const portfolio = this.getPortfolio(username);
    
    // Calculate total market value
    portfolio.total_market_value = portfolio.items.reduce((sum, item) => sum + item.market_value, 0);
    portfolio.total_shares = portfolio.items.reduce((sum, item) => sum + item.shares, 0);
    
    // Calculate weights
    portfolio.items.forEach(item => {
      item.weight = portfolio.total_market_value > 0 ? (item.market_value / portfolio.total_market_value) * 100 : 0;
    });
    
    // Update the portfolio
    this.setPortfolio(username, portfolio);
  }

  // Get tickers for API calls
  getTickers(username: string): string[] {
    const portfolio = this.getPortfolio(username);
    return portfolio.items.map(item => item.ticker);
  }

  // Get portfolio items for display
  getPortfolioItems(username: string): PortfolioItem[] {
    const portfolio = this.getPortfolio(username);
    return portfolio.items;
  }

  // Get total market value
  getTotalMarketValue(username: string): number {
    const portfolio = this.getPortfolio(username);
    return portfolio.total_market_value;
  }

  // Initialize default portfolios
  initializeDefaultPortfolios() {
    // Admin portfolio (existing data)
    const adminPortfolio: PortfolioData = {
      items: [
        { ticker: 'AMD', shares: 1000, price: 190.30, market_value: 190300, weight: 12.1 },
        { ticker: 'APP', shares: 1000, price: 16.71, market_value: 16710, weight: 1.1 },
        { ticker: 'BULL', shares: 1000, price: 108.22, market_value: 108220, weight: 6.9 },
        { ticker: 'DOMO', shares: 1000, price: 182.01, market_value: 182010, weight: 11.5 },
        { ticker: 'GOOGL', shares: 1000, price: 257.09, market_value: 257090, weight: 16.3 },
        { ticker: 'META', shares: 1000, price: 22.77, market_value: 22770, weight: 1.4 },
        { ticker: 'QQQM', shares: 1000, price: 89.50, market_value: 89500, weight: 5.7 },
        { ticker: 'RDDT', shares: 1000, price: 54.14, market_value: 54140, weight: 3.4 },
        { ticker: 'SGOV', shares: 1000, price: 281.96, market_value: 281960, weight: 17.9 },
        { ticker: 'SMCI', shares: 1000, price: 13.56, market_value: 13560, weight: 0.9 },
        { ticker: 'SNOW', shares: 1000, price: 63.36, market_value: 63360, weight: 4.0 },
        { ticker: 'TSLA', shares: 1000, price: 8.98, market_value: 8980, weight: 0.6 },
        { ticker: 'ULTY', shares: 1000, price: 241.20, market_value: 241200, weight: 15.3 }
      ],
      total_market_value: 1530800,
      total_shares: 13000
    };

    // User portfolio (new data from image)
    const userPortfolio: PortfolioData = {
      items: [
        { ticker: 'NFLX', shares: 1000, price: 1195.80, market_value: 1195800, weight: 26.6 },
        { ticker: 'META', shares: 1000, price: 765.17, market_value: 765170, weight: 17.0 },
        { ticker: 'MSFT', shares: 1000, price: 450.00, market_value: 450000, weight: 10.0 },
        { ticker: 'ADBE', shares: 1000, price: 350.00, market_value: 350000, weight: 7.8 },
        { ticker: 'TSLA', shares: 1000, price: 250.00, market_value: 250000, weight: 5.6 },
        { ticker: 'ORCL', shares: 1000, price: 150.00, market_value: 150000, weight: 3.3 },
        { ticker: 'CRM', shares: 1000, price: 200.00, market_value: 200000, weight: 4.4 },
        { ticker: 'AAPL', shares: 1000, price: 180.00, market_value: 180000, weight: 4.0 },
        { ticker: 'AMZN', shares: 1000, price: 160.00, market_value: 160000, weight: 3.6 },
        { ticker: 'GOOGL', shares: 1000, price: 140.00, market_value: 140000, weight: 3.1 },
        { ticker: 'NVDA', shares: 1000, price: 183.02, market_value: 183020, weight: 4.1 },
        { ticker: 'INTC', shares: 1000, price: 19.69, market_value: 19690, weight: 0.4 }
      ],
      total_market_value: 4494180,
      total_shares: 12000
    };

    this.setPortfolio('admin', adminPortfolio);
    this.setPortfolio('user', userPortfolio);
  }
}

export default PortfolioService.getInstance();
