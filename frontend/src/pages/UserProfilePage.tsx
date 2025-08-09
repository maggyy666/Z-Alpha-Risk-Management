import React, { useState, useEffect } from 'react';
import './UserProfilePage.css';
import martinPhoto from '../assets/martin-shkreli.webp';
import sbfPhoto from '../assets/Sam-Bankman-Fried-Silicon-Valley-Culture-Plaintext-Business-1237105664.webp';
import apiService from '../services/api';
import { useSession } from '../contexts/SessionContext';
import portfolioService, { PortfolioItem } from '../services/portfolioService';

const UserProfilePage: React.FC = () => {
  const [loading, setLoading] = useState(true);
  const { session, setDefaultSession, setCurrentUser } = useSession();

  const [newTicker, setNewTicker] = useState('');
  const [newShares, setNewShares] = useState('');

  useEffect(() => {
    // Initialize portfolio service with default portfolios
    portfolioService.initializeDefaultPortfolios();
    setLoading(false);
  }, []);

  // Get current user's portfolio
  const currentUsername = session?.username || 'admin';
  const portfolio = portfolioService.getPortfolioItems(currentUsername);
  const totalMarketValue = portfolioService.getTotalMarketValue(currentUsername);
  
  // Different profiles for different users
  const isAdmin = currentUsername === 'admin';
  const isUser = currentUsername === 'user';

  const handleSharesChange = (index: number, newShares: number) => {
    const ticker = portfolio[index].ticker;
    portfolioService.updateShares(currentUsername, ticker, newShares);
    // Force re-render
    window.location.reload();
  };

  const handleRemoveTicker = (index: number) => {
    const ticker = portfolio[index].ticker;
    portfolioService.removeTicker(currentUsername, ticker);
    // Force re-render
    window.location.reload();
  };

  const handleAddTicker = () => {
    if (newTicker.trim() && newShares.trim()) {
      const ticker = newTicker.trim().toUpperCase();
      const shares = parseInt(newShares);
      
      if (shares > 0 && !portfolio.find(item => item.ticker === ticker)) {
        // Simulate price fetch - in real app this would come from API
        const simulatedPrice = Math.random() * 200 + 10; // Random price between $10-$210
        
        portfolioService.addTicker(currentUsername, ticker, shares, simulatedPrice);
        setNewTicker('');
        setNewShares('');
        // Force re-render
        window.location.reload();
      }
    }
  };

  const handleKeyPress = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter') {
      handleAddTicker();
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
              <h3>Portfolio [Editable] - Total Value: {formatCurrency(totalMarketValue)}</h3>
              
              {/* Add New Ticker Section */}
              <div className="add-ticker-section">
                <h4>Add New Ticker</h4>
                <div className="add-ticker-container">
                  <input
                    type="text"
                    placeholder="Ticker (e.g., AAPL)"
                    value={newTicker}
                    onChange={(e) => setNewTicker(e.target.value)}
                    onKeyPress={handleKeyPress}
                    className="ticker-input"
                  />
                  <input
                    type="number"
                    placeholder="Shares"
                    value={newShares}
                    onChange={(e) => setNewShares(e.target.value)}
                    onKeyPress={handleKeyPress}
                    className="shares-input"
                  />
                  <button onClick={handleAddTicker} className="add-ticker-btn">
                    Add
                  </button>
                </div>
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
