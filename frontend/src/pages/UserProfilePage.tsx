import React, { useState, useEffect } from 'react';
import './UserProfilePage.css';
import martinPhoto from '../assets/martin-shkreli.webp';
import apiService from '../services/api';

interface PortfolioItem {
  ticker: string;
  shares: number;
  price: number;
  market_value: number;
}

const UserProfilePage: React.FC = () => {
  const [portfolio, setPortfolio] = useState<PortfolioItem[]>([]);
  const [loading, setLoading] = useState(true);
  const [totalMarketValue, setTotalMarketValue] = useState(0);

  const [newTicker, setNewTicker] = useState('');
  const [newShares, setNewShares] = useState('');

  useEffect(() => {
    const fetchPortfolioData = async () => {
      try {
        const data = await apiService.getPortfolioSummary('admin');
        if (data.portfolio_positions) {
          const portfolioItems = data.portfolio_positions.map((item: any) => ({
            ticker: item.ticker,
            shares: item.shares,
            price: item.price,
            market_value: item.market_value
          }));
          setPortfolio(portfolioItems);
          setTotalMarketValue(data.portfolio_overview?.total_market_value || 0);
        }
      } catch (error) {
        console.error('Error fetching portfolio data:', error);
        // Fallback to hardcoded data if API fails
        setPortfolio([
          { ticker: 'AMD', shares: 1000, price: 190.30, market_value: 190300 },
          { ticker: 'APP', shares: 1000, price: 16.71, market_value: 16710 },
          { ticker: 'BRK-B', shares: 1000, price: 46.49, market_value: 46490 },
          { ticker: 'BULL', shares: 1000, price: 108.22, market_value: 108220 },
          { ticker: 'DOMO', shares: 1000, price: 182.01, market_value: 182010 },
          { ticker: 'GOOGL', shares: 1000, price: 257.09, market_value: 257090 },
          { ticker: 'META', shares: 1000, price: 22.77, market_value: 22770 },
          { ticker: 'QQQM', shares: 1000, price: 89.50, market_value: 89500 },
          { ticker: 'RDDT', shares: 1000, price: 54.14, market_value: 54140 },
          { ticker: 'SGOV', shares: 1000, price: 281.96, market_value: 281960 },
          { ticker: 'SMCI', shares: 1000, price: 13.56, market_value: 13560 },
          { ticker: 'SNOW', shares: 1000, price: 63.36, market_value: 63360 },
          { ticker: 'TSLA', shares: 1000, price: 8.98, market_value: 8980 },
          { ticker: 'ULTY', shares: 1000, price: 241.20, market_value: 241200 }
        ]);
        setTotalMarketValue(1576290);
      } finally {
        setLoading(false);
      }
    };

    fetchPortfolioData();
  }, []);

  const handleSharesChange = (index: number, newShares: number) => {
    const updatedPortfolio = [...portfolio];
    updatedPortfolio[index].shares = newShares;
    updatedPortfolio[index].market_value = newShares * updatedPortfolio[index].price;
    setPortfolio(updatedPortfolio);
    setTotalMarketValue(updatedPortfolio.reduce((sum, item) => sum + item.market_value, 0));
  };

  const handleRemoveTicker = (index: number) => {
    const updatedPortfolio = portfolio.filter((_, i) => i !== index);
    setPortfolio(updatedPortfolio);
    setTotalMarketValue(updatedPortfolio.reduce((sum, item) => sum + item.market_value, 0));
  };

  const handleAddTicker = () => {
    if (newTicker.trim() && newShares.trim()) {
      const ticker = newTicker.trim().toUpperCase();
      const shares = parseInt(newShares);
      
      if (shares > 0 && !portfolio.find(item => item.ticker === ticker)) {
        // Simulate price fetch - in real app this would come from API
        const simulatedPrice = Math.random() * 200 + 10; // Random price between $10-$210
        
        const newItem = {
          ticker,
          shares,
          price: simulatedPrice,
          market_value: shares * simulatedPrice
        };
        
        const updatedPortfolio = [...portfolio, newItem];
        setPortfolio(updatedPortfolio);
        setTotalMarketValue(updatedPortfolio.reduce((sum, item) => sum + item.market_value, 0));
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
                    src={martinPhoto} 
                    alt="Martin Shkreli" 
                    className="profile-image"
                    onError={(e) => {
                      const target = e.target as HTMLImageElement;
                      target.style.display = 'none';
                      target.nextElementSibling?.classList.remove('hidden');
                    }}
                  />
                  <div className="photo-placeholder hidden">
                    <span className="photo-icon">👤</span>
                  </div>
                </div>
              </div>
              <div className="profile-basic-info">
                <h2 className="user-name">Martin Shkreli</h2>
                <p className="user-title">Portfolio Manager</p>
                <p className="user-company">JP Morgan Asset Management</p>
                <p className="user-join-date">Fund Client since: January 2018</p>
                <div className="compliance-badges">
                  <span className="compliance-badge accredited">Accredited Investor</span>
                  <span className="compliance-badge qualified">Qualified Purchaser</span>
                  <span className="compliance-badge verified">KYC Verified</span>
                </div>
              </div>
            </div>
            
            <div className="profile-stats-grid">
              <div className="stat-card">
                <div className="stat-label">Investment in Fund</div>
                <div className="stat-value">{formatCurrency(totalMarketValue)}</div>
                <div className="stat-change positive">+2.3% MTD</div>
              </div>
              
              <div className="stat-card">
                <div className="stat-label">Target Returns</div>
                <div className="stat-value">15.0%</div>
                <div className="stat-change neutral">Annual Target</div>
              </div>
              
              <div className="stat-card">
                <div className="stat-label">Margin with Us</div>
                <div className="stat-value">$395K</div>
                <div className="stat-change neutral">2.5:1 Leverage</div>
              </div>
              
              <div className="stat-card">
                <div className="stat-label">Total Profit</div>
                <div className="stat-value">$237K</div>
                <div className="stat-change positive">+18.7% YTD</div>
              </div>
            </div>

            <div className="detail-section">
              <h3>Contract Information</h3>
              <div className="detail-grid">
                <div className="detail-item">
                  <span className="detail-label">Contract Type:</span>
                  <span className="detail-value">Institutional Fund Agreement</span>
                </div>
                <div className="detail-item">
                  <span className="detail-label">Management Fee:</span>
                  <span className="detail-value">2.0% + 20% Performance</span>
                </div>
                <div className="detail-item">
                  <span className="detail-label">Redemption Terms:</span>
                  <span className="detail-value">Quarterly (30-day notice)</span>
                </div>
                <div className="detail-item">
                  <span className="detail-label">Minimum Investment:</span>
                  <span className="detail-value">$5.0M</span>
                </div>
                <div className="detail-item">
                  <span className="detail-label">Contract Start:</span>
                  <span className="detail-value">January 15, 2018</span>
                </div>
                <div className="detail-item">
                  <span className="detail-label">Contract End:</span>
                  <span className="detail-value">January 15, 2028</span>
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
                  <span className="detail-value">Portfolio Manager, Institutional Investments</span>
                </div>
                <div className="detail-item">
                  <span className="detail-label">Institution:</span>
                  <span className="detail-value">JP Morgan Asset Management</span>
                </div>
                <div className="detail-item">
                  <span className="detail-label">Experience:</span>
                  <span className="detail-value">15+ years Institutional Investing</span>
                </div>
                <div className="detail-item">
                  <span className="detail-label">Specialization:</span>
                  <span className="detail-value">Alternative Investments & Hedge Funds</span>
                </div>
                <div className="detail-item">
                  <span className="detail-label">Professional Licenses:</span>
                  <span className="detail-value">Series 7, 63, 65</span>
                </div>
                <div className="detail-item">
                  <span className="detail-label">Professional Memberships:</span>
                  <span className="detail-value">CFA Institute, CAIA</span>
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
