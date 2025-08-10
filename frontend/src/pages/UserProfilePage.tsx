import React, { useState, useEffect } from 'react';
import './UserProfilePage.css';
import martinPhoto from '../assets/martin-shkreli.webp';
import sbfPhoto from '../assets/Sam-Bankman-Fried-Silicon-Valley-Culture-Plaintext-Business-1237105664.webp';
import apiService from '../services/api';
import axios from 'axios';
import { useSession } from '../contexts/SessionContext';
import portfolioService, { PortfolioItem } from '../services/portfolioService';

const UserProfilePage: React.FC = () => {
  const [loading, setLoading] = useState(true);
  const { session, setDefaultSession, setCurrentUser, refreshPortfolioData } = useSession();

  const [newTicker, setNewTicker] = useState('');
  const [newShares, setNewShares] = useState('');
  const [portfolio, setPortfolio] = useState<PortfolioItem[]>([]);
  const [totalMarketValue, setTotalMarketValue] = useState(0);
  const [saving, setSaving] = useState(false);
  const [saveMessage, setSaveMessage] = useState('');
  
  // Ticker search states
  const [tickerQuery, setTickerQuery] = useState('');
  const [tickerSuggestions, setTickerSuggestions] = useState<any[]>([]);
  const [showSuggestions, setShowSuggestions] = useState(false);
  const [addingTicker, setAddingTicker] = useState(false);
  const [addMessage, setAddMessage] = useState('');

  const fetchPortfolioData = async () => {
    try {
      const currentUsername = session?.username || 'admin';
      const response = await axios.get(`http://localhost:8000/user-portfolio/${currentUsername}`);
      
      if (response.data && response.data.portfolio_items) {
        const portfolioItems = response.data.portfolio_items.map((item: any) => ({
          ticker: item.ticker,
          shares: item.shares,
          price: item.price,
          market_value: item.market_value,
          weight: (item.market_value / response.data.total_market_value) * 100,
          sector: item.sector,
          industry: item.industry
        }));
        
        setPortfolio(portfolioItems);
        setTotalMarketValue(response.data.total_market_value);
      }
    } catch (error) {
      console.error('Error fetching portfolio data:', error);
      // Fallback to default portfolios if API fails
      portfolioService.initializeDefaultPortfolios();
      const currentUsername = session?.username || 'admin';
      setPortfolio(portfolioService.getPortfolioItems(currentUsername));
      setTotalMarketValue(portfolioService.getTotalMarketValue(currentUsername));
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchPortfolioData();
  }, [session?.username]);

  // Get current user's portfolio
  const currentUsername = session?.username || 'admin';
  
  // Different profiles for different users
  const isAdmin = currentUsername === 'admin';
  const isUser = currentUsername === 'user';

  const handleSharesChange = (index: number, newShares: number) => {
    const updatedPortfolio = [...portfolio];
    updatedPortfolio[index].shares = newShares;
    updatedPortfolio[index].market_value = newShares * updatedPortfolio[index].price;
    
    // Recalculate weights
    const newTotal = updatedPortfolio.reduce((sum, item) => sum + item.market_value, 0);
    updatedPortfolio.forEach(item => {
      item.weight = (item.market_value / newTotal) * 100;
    });
    
    setPortfolio(updatedPortfolio);
    setTotalMarketValue(newTotal);
  };

  const handleRemoveTicker = async (index: number) => {
    const tickerToRemove = portfolio[index].ticker;
    
    try {
      const currentUsername = session?.username || 'admin';
      const response = await axios.delete(
        `http://localhost:8000/remove-ticker/${currentUsername}?ticker=${encodeURIComponent(tickerToRemove)}`
      );

      if (response.data.success) {
        // Remove from local state
        const updatedPortfolio = portfolio.filter((_, i) => i !== index);
        
        // Recalculate weights
        const newTotal = updatedPortfolio.reduce((sum, item) => sum + item.market_value, 0);
        updatedPortfolio.forEach(item => {
          item.weight = (item.market_value / newTotal) * 100;
        });
        
        setPortfolio(updatedPortfolio);
        setTotalMarketValue(newTotal);
        
        // Show success message
        setSaveMessage(`Successfully removed ${tickerToRemove} from portfolio`);
        setTimeout(() => setSaveMessage(''), 3000);
      } else {
        setSaveMessage(response.data.error || 'Failed to remove ticker');
        setTimeout(() => setSaveMessage(''), 5000);
      }
    } catch (error: any) {
      console.error('Error removing ticker:', error);
      setSaveMessage(error.response?.data?.detail || 'Error removing ticker. Please try again.');
      setTimeout(() => setSaveMessage(''), 5000);
    }
  };

  const handleAddTicker = () => {
    if (newTicker.trim() && newShares.trim()) {
      const ticker = newTicker.trim().toUpperCase();
      const shares = parseInt(newShares);
      
      if (shares > 0 && !portfolio.find(item => item.ticker === ticker)) {
        // For now, use a placeholder price - in real app this would come from API
        const placeholderPrice = 100; // Placeholder price
        
        const newItem: PortfolioItem = {
          ticker,
          shares,
          price: placeholderPrice,
          market_value: shares * placeholderPrice,
          weight: 0
        };
        
        const updatedPortfolio = [...portfolio, newItem];
        
        // Recalculate weights
        const newTotal = updatedPortfolio.reduce((sum, item) => sum + item.market_value, 0);
        updatedPortfolio.forEach(item => {
          item.weight = (item.market_value / newTotal) * 100;
        });
        
        setPortfolio(updatedPortfolio);
        setTotalMarketValue(newTotal);
        setNewTicker('');
        setNewShares('');
      }
    }
  };

  const handleKeyPress = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter') {
      handleAddTicker();
    }
  };

    const handleSavePortfolio = async () => {
    setSaving(true);
    setSaveMessage('');

    try {
      const currentUsername = session?.username || 'admin';

      // Prepare data for API
      const portfolioData = portfolio.map(item => ({
        ticker: item.ticker,
        shares: item.shares
      }));

      const response = await axios.post(
        `http://localhost:8000/user-portfolio/${currentUsername}`,
        portfolioData
      );

      if (response.data.success) {
        setSaveMessage('Portfolio saved successfully!');
        setTimeout(() => setSaveMessage(''), 3000);
        
        // Clear backend cache for this user using new endpoint
        try {
          await axios.post(`http://localhost:8000/invalidate-user/${currentUsername}`);
          console.log('Backend cache invalidated for user:', currentUsername);
        } catch (cacheError) {
          console.error('Error invalidating cache:', cacheError);
        }
        
        // Refresh portfolio data in this component
        await fetchPortfolioData();
        
        // Notify other components about portfolio update
        console.log('🔄 Dispatching portfolio-updated event...');
        window.dispatchEvent(new CustomEvent('portfolio-updated', {
          detail: { timestamp: Date.now() }
        }));
        console.log('✅ Portfolio update event dispatched');
      }
    } catch (error) {
      console.error('Error saving portfolio:', error);
      setSaveMessage('Error saving portfolio. Please try again.');
      setTimeout(() => setSaveMessage(''), 5000);
    } finally {
      setSaving(false);
    }
  };

  // Ticker search functions
  const searchTickers = async (query: string) => {
    if (query.length < 2) {
      setTickerSuggestions([]);
      setShowSuggestions(false);
      return;
    }

    try {
      const response = await axios.get(`http://localhost:8000/ticker-search?query=${encodeURIComponent(query)}`);
      setTickerSuggestions(response.data.suggestions || []);
      setShowSuggestions(true);
    } catch (error) {
      console.error('Error searching tickers:', error);
      setTickerSuggestions([]);
      setShowSuggestions(false);
    }
  };

  const handleTickerQueryChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const query = e.target.value;
    setTickerQuery(query);
    searchTickers(query);
  };

  const handleTickerSelect = (suggestion: any) => {
    setTickerQuery(suggestion.symbol);
    setShowSuggestions(false);
  };

  const handleAddTickerToPortfolio = async () => {
    if (!tickerQuery.trim() || !newShares.trim()) {
      setAddMessage('Please enter both ticker and shares');
      setTimeout(() => setAddMessage(''), 3000);
      return;
    }

    const shares = parseInt(newShares);
    if (shares <= 0) {
      setAddMessage('Shares must be greater than 0');
      setTimeout(() => setAddMessage(''), 3000);
      return;
    }

    // Check if ticker already exists
    if (portfolio.find(item => item.ticker === tickerQuery.toUpperCase())) {
      setAddMessage('Ticker already exists in portfolio');
      setTimeout(() => setAddMessage(''), 3000);
      return;
    }

    setAddingTicker(true);
    setAddMessage('');

    try {
      const currentUsername = session?.username || 'admin';
      const response = await axios.post(
        `http://localhost:8000/add-ticker/${currentUsername}?ticker=${encodeURIComponent(tickerQuery)}&shares=${shares}`
      );

      if (response.data.success) {
        setAddMessage(`Successfully added ${tickerQuery} with ${shares} shares (${response.data.data_source})`);
        setTickerQuery('');
        setNewShares('');
        setShowSuggestions(false);
        
        // Refresh portfolio data
        const portfolioResponse = await axios.get(`http://localhost:8000/user-portfolio/${currentUsername}`);
        if (portfolioResponse.data && portfolioResponse.data.portfolio_items) {
          const portfolioItems = portfolioResponse.data.portfolio_items.map((item: any) => ({
            ticker: item.ticker,
            shares: item.shares,
            price: item.price,
            market_value: item.market_value,
            weight: (item.market_value / portfolioResponse.data.total_market_value) * 100,
            sector: item.sector,
            industry: item.industry
          }));
          
          setPortfolio(portfolioItems);
          setTotalMarketValue(portfolioResponse.data.total_market_value);
        }
        
        setTimeout(() => setAddMessage(''), 5000);
      } else {
        setAddMessage(response.data.error || 'Failed to add ticker');
        setTimeout(() => setAddMessage(''), 5000);
      }
    } catch (error: any) {
      console.error('Error adding ticker:', error);
      setAddMessage(error.response?.data?.detail || 'Error adding ticker. Please try again.');
      setTimeout(() => setAddMessage(''), 5000);
    } finally {
      setAddingTicker(false);
    }
  };

  const formatCurrency = (value: number) => {
    if (value >= 1000000) {
      return `$${(value / 1000000).toFixed(2)}M`;
    } else if (value >= 1000) {
      return `$${(value / 1000).toFixed(0)}K`;
    }
    return `$${value.toFixed(0)}`;
  };

  if (loading) {
    return (
      <div className="user-profile-page">
        <div className="profile-container">
          <div className="loading">Loading portfolio data...</div>
        </div>
      </div>
    );
  }

  return (
    <div className="user-profile-page">
      <div className="profile-container">
        <div className="profile-header">
          <h1>Client Investment Profile</h1>
          <p className="profile-subtitle">Portfolio Management Dashboard</p>

        </div>
        
        <div className="profile-content">
          <div className="profile-main">
            <div className="profile-photo-section">
              <div className="profile-photo">
                <div className="photo-container">
                  <img 
                    src={isUser ? sbfPhoto : martinPhoto} 
                    alt={isUser ? "Sam Bankman-Fried" : "Martin Shkreli"} 
                    className="profile-image"
                    onError={(e) => {
                      const target = e.target as HTMLImageElement;
                      target.style.display = 'none';
                      target.nextElementSibling?.classList.remove('hidden');
                    }}
                  />
                  <div className="photo-placeholder hidden">
                    <span className="photo-icon"></span>
                  </div>
                </div>
              </div>
              <div className="profile-basic-info">
                <h2 className="user-name">{isUser ? 'Sam Bankman-Fried' : 'Martin Shkreli'}</h2>
                <p className="user-title">{isUser ? 'Crypto Entrepreneur' : 'Portfolio Manager'}</p>
                <p className="user-company">{isUser ? 'FTX, Alameda Research' : 'JP Morgan Asset Management'}</p>
                <p className="user-join-date">Fund Client since: {isUser ? 'March 2022' : 'January 2018'}</p>
                <div className="compliance-badges">
                  <span className="compliance-badge accredited">{isUser ? 'Crypto Bro' : 'Accredited Investor'}</span>
                  <span className="compliance-badge qualified">{isUser ? 'DeFi Degenerate' : 'Qualified Purchaser'}</span>
                  <span className="compliance-badge verified">{isUser ? 'Pyramid Scheme CEO' : 'KYC Verified'}</span>
                </div>
              </div>
            </div>
            
            <div className="profile-stats-grid">
              <div className="stat-card">
                <div className="stat-label">Investment in Fund</div>
                <div className="stat-value">{formatCurrency(totalMarketValue)}</div>
                <div className="stat-change positive">{isUser ? '-99.9% MTD' : '+2.3% MTD'}</div>
              </div>
              
              <div className="stat-card">
                <div className="stat-label">Target Returns</div>
                <div className="stat-value">{isUser ? '∞%' : '15.0%'}</div>
                <div className="stat-change neutral">{isUser ? 'Crypto Dreams' : 'Annual Target'}</div>
              </div>
              
              <div className="stat-card">
                <div className="stat-label">Margin with Us</div>
                <div className="stat-value">{isUser ? '$0' : '$395K'}</div>
                <div className="stat-change neutral">{isUser ? 'All Liquidated' : '2.5:1 Leverage'}</div>
              </div>
              
              <div className="stat-card">
                <div className="stat-label">Total Profit</div>
                <div className="stat-value">{isUser ? '-$8.7B' : '$237K'}</div>
                <div className="stat-change positive">{isUser ? '-100% YTD' : '+18.7% YTD'}</div>
              </div>
            </div>

            <div className="detail-section">
              <h3>Contract Information</h3>
              <div className="detail-grid">
                <div className="detail-item">
                  <span className="detail-label">Contract Type:</span>
                  <span className="detail-value">{isUser ? 'Crypto Exchange Terms' : 'Institutional Fund Agreement'}</span>
                </div>
                <div className="detail-item">
                  <span className="detail-label">Management Fee:</span>
                  <span className="detail-value">{isUser ? '0.1% + Customer Funds' : '2.0% + 20% Performance'}</span>
                </div>
                <div className="detail-item">
                  <span className="detail-label">Redemption Terms:</span>
                  <span className="detail-value">{isUser ? 'Never (Funds Stuck)' : 'Quarterly (30-day notice)'}</span>
                </div>
                <div className="detail-item">
                  <span className="detail-label">Minimum Investment:</span>
                  <span className="detail-value">{isUser ? '$1 (Crypto)' : '$5.0M'}</span>
                </div>
                <div className="detail-item">
                  <span className="detail-label">Contract Start:</span>
                  <span className="detail-value">{isUser ? 'March 15, 2022' : 'January 15, 2018'}</span>
                </div>
                <div className="detail-item">
                  <span className="detail-label">Contract End:</span>
                  <span className="detail-value">{isUser ? 'November 11, 2022' : 'January 15, 2028'}</span>
                </div>
              </div>
            </div>
          </div>
          
          <div className="profile-details">
            <div className="detail-section">
              <h3>Client Information</h3>
              <div className="detail-grid">
                <div className="detail-item">
                  <span className="detail-label">Current Position:</span>
                  <span className="detail-value">{isUser ? 'Former CEO, Crypto Exchange' : 'Portfolio Manager, Institutional Investments'}</span>
                </div>
                <div className="detail-item">
                  <span className="detail-label">Institution:</span>
                  <span className="detail-value">{isUser ? 'FTX Trading Ltd (Bankrupt)' : 'JP Morgan Asset Management'}</span>
                </div>
                <div className="detail-item">
                  <span className="detail-label">Experience:</span>
                  <span className="detail-value">{isUser ? '2 years Crypto Trading' : '15+ years Institutional Investing'}</span>
                </div>
                <div className="detail-item">
                  <span className="detail-label">Specialization:</span>
                  <span className="detail-value">{isUser ? 'Customer Fund Misappropriation' : 'Alternative Investments & Hedge Funds'}</span>
                </div>
                <div className="detail-item">
                  <span className="detail-label">Professional Licenses:</span>
                  <span className="detail-value">{isUser ? 'None (Crypto)' : 'Series 7, 63, 65'}</span>
                </div>
                <div className="detail-item">
                  <span className="detail-label">Professional Memberships:</span>
                  <span className="detail-value">{isUser ? 'Crypto Bros Anonymous' : 'CFA Institute, CAIA'}</span>
                </div>
              </div>
            </div>
            
            <div className="detail-section">
              <h3>Portfolio - Total Value: {formatCurrency(totalMarketValue)}</h3>
              
              {/* Add New Ticker Section */}
              <div className="add-ticker-section">
                <h4>Add New Ticker</h4>
                <div className="add-ticker-container">
                  <div className="ticker-search-container">
                    <input
                      type="text"
                      placeholder="Search ticker (e.g., AAPL)"
                      value={tickerQuery}
                      onChange={handleTickerQueryChange}
                      className="ticker-input"
                    />
                    {showSuggestions && tickerSuggestions.length > 0 && (
                      <div className="ticker-suggestions">
                        {tickerSuggestions.map((suggestion, index) => (
                          <div
                            key={index}
                            className="suggestion-item"
                            onClick={() => handleTickerSelect(suggestion)}
                          >
                            <span className="suggestion-symbol">{suggestion.symbol}</span>
                            <span className="suggestion-name">{suggestion.name}</span>
                            <span className="suggestion-exchange">{suggestion.exchange}</span>
                          </div>
                        ))}
                      </div>
                    )}
                  </div>
                  <input
                    type="number"
                    placeholder="Shares"
                    value={newShares}
                    onChange={(e) => setNewShares(e.target.value)}
                    className="shares-input"
                  />
                  <button 
                    onClick={handleAddTickerToPortfolio} 
                    disabled={addingTicker}
                    className="add-ticker-btn"
                  >
                    {addingTicker ? 'Adding...' : 'Add Ticker'}
                  </button>
                </div>
                {addMessage && (
                  <div className={`add-message ${addMessage.includes('Error') || addMessage.includes('Failed') ? 'error' : 'success'}`}>
                    {addMessage}
                  </div>
                )}
              </div>

              {/* Save Portfolio Section */}
              <div className="save-portfolio-section">
                <button 
                  onClick={handleSavePortfolio} 
                  disabled={saving}
                  className="save-portfolio-btn"
                >
                  {saving ? 'Saving...' : 'SAVE PORTFOLIO'}
                </button>
                {saveMessage && (
                  <div className={`save-message ${saveMessage.includes('Error') ? 'error' : 'success'}`}>
                    {saveMessage}
                  </div>
                )}
              </div>

              <div className="portfolio-table-container">
                <table className="portfolio-table">
                  <thead>
                    <tr>
                      <th>Ticker</th>
                      <th>Shares</th>
                      <th>Price</th>
                      <th>Market Value</th>
                      <th>Weight</th>
                      <th>Action</th>
                    </tr>
                  </thead>
                  <tbody>
                    {portfolio.map((item, index) => (
                      <tr key={item.ticker}>
                        <td className="ticker-cell">{item.ticker}</td>
                        <td>
                          <input
                            type="number"
                            value={item.shares}
                            onChange={(e) => handleSharesChange(index, parseInt(e.target.value) || 0)}
                            className="portfolio-input shares-input"
                            style={{ WebkitAppearance: 'none', MozAppearance: 'textfield' }}
                          />
                        </td>
                        <td className="price-cell">
                          ${item.price.toFixed(2)}
                        </td>
                        <td className="market-value-cell">
                          ${item.market_value.toLocaleString()}
                        </td>
                        <td className="weight-cell">
                          {totalMarketValue > 0 ? ((item.market_value / totalMarketValue) * 100).toFixed(1) : '0.0'}%
                        </td>
                        <td>
                          <button 
                            onClick={() => handleRemoveTicker(index)}
                            className="remove-ticker-btn"
                          >
                            ✕
                          </button>
                        </td>
                      </tr>
                    ))}
                  </tbody>
                  <tfoot>
                    <tr className="total-row">
                      <td><strong>Total</strong></td>
                      <td><strong>{portfolio.reduce((sum, item) => sum + item.shares, 0).toLocaleString()}</strong></td>
                      <td></td>
                      <td><strong>${totalMarketValue.toLocaleString()}</strong></td>
                      <td><strong>100.0%</strong></td>
                      <td></td>
                    </tr>
                  </tfoot>
                </table>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default UserProfilePage;
