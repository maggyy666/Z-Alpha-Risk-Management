import React from 'react';
import './IntroductionPage.css';

const IntroductionPage: React.FC = () => {
  return (
    <div className="introduction-page">
      <div className="introduction-container">
        <h1 className="introduction-title">Z-Alpha Securities Hedge Fund</h1>
        
        <div className="introduction-content">
          <p className="introduction-description">
            Z-Alpha Securities is a quantitative hedge fund that leverages advanced risk management 
            technology to deliver superior returns while maintaining strict risk controls. Our proprietary 
            platform combines sophisticated quantitative models with real-time market analysis to identify 
            opportunities and manage portfolio risk across diverse market conditions.
          </p>

          <div className="sections-grid">
            <div className="section-card">
              <h3 className="section-title">Portfolio Summary</h3>
              <p className="section-description">
                Central dashboard displaying overall risk score, largest positions, portfolio volatility, 
                and primary risk contributors for immediate portfolio health monitoring.
              </p>
              <div className="section-metrics">
                <span className="metric">• Overall risk score and classification</span>
                <span className="metric">• Largest positions analysis</span>
                <span className="metric">• Portfolio volatility metrics</span>
                <span className="metric">• Real-time risk alerts</span>
              </div>
            </div>

            <div className="section-card">
              <h3 className="section-title">Realized Risk</h3>
              <p className="section-description">
                Historical risk analysis based on actual portfolio performance data including 
                volatility, drawdown periods, and position correlations.
              </p>
              <div className="section-metrics">
                <span className="metric">• Historical volatility measures</span>
                <span className="metric">• Maximum drawdown analysis</span>
                <span className="metric">• Position correlation matrices</span>
                <span className="metric">• Risk-adjusted performance</span>
              </div>
            </div>

            <div className="section-card">
              <h3 className="section-title">Forecast Risk</h3>
              <p className="section-description">
                Forward-looking risk prediction using advanced econometric models (EWMA, GARCH, EGARCH) 
                to analyze marginal and total risk contributions for each position.
              </p>
              <div className="section-metrics">
                <span className="metric">• Marginal Risk Contribution analysis</span>
                <span className="metric">• Total Risk Contribution calculations</span>
                <span className="metric">• Advanced volatility forecasting</span>
                <span className="metric">• Risk decomposition analysis</span>
              </div>
            </div>

            <div className="section-card">
              <h3 className="section-title">Factor Exposure</h3>
              <p className="section-description">
                Analysis of portfolio exposure to various risk factors including macroeconomic, 
                sector-specific, and style factors to identify vulnerabilities.
              </p>
              <div className="section-metrics">
                <span className="metric">• Factor beta analysis</span>
                <span className="metric">• Sector concentration analysis</span>
                <span className="metric">• Factor sensitivity testing</span>
                <span className="metric">• R-squared analysis</span>
              </div>
            </div>

            <div className="section-card">
              <h3 className="section-title">Stress Testing</h3>
              <p className="section-description">
                Comprehensive stress testing framework simulating extreme market scenarios 
                and crisis conditions to evaluate portfolio resilience.
              </p>
              <div className="section-metrics">
                <span className="metric">• Historical crisis scenarios</span>
                <span className="metric">• Market regime testing</span>
                <span className="metric">• Potential loss estimation</span>
                <span className="metric">• Sensitivity analysis</span>
              </div>
            </div>

            <div className="section-card">
              <h3 className="section-title">Concentration Risk</h3>
              <p className="section-description">
                Analysis of portfolio concentration risk using sophisticated metrics like 
                the Herfindahl Index to ensure proper diversification.
              </p>
              <div className="section-metrics">
                <span className="metric">• Herfindahl Index metrics</span>
                <span className="metric">• Sector concentration analysis</span>
                <span className="metric">• Largest position monitoring</span>
                <span className="metric">• Concentration alerts</span>
              </div>
            </div>

            <div className="section-card">
              <h3 className="section-title">Liquidity Risk</h3>
              <p className="section-description">
                Assessment of portfolio liquidity risk and position exit capabilities 
                to ensure efficient liquidation when needed.
              </p>
              <div className="section-metrics">
                <span className="metric">• Liquidity scoring</span>
                <span className="metric">• Exit time calculations</span>
                <span className="metric">• Market impact analysis</span>
                <span className="metric">• Spread monitoring</span>
              </div>
            </div>

            <div className="section-card">
              <h3 className="section-title">Volatility-Based Sizing</h3>
              <p className="section-description">
                Position sizing optimization based on volatility and correlation analysis 
                to balance portfolio risk with optimal weights.
              </p>
              <div className="section-metrics">
                <span className="metric">• Risk-parity weights</span>
                <span className="metric">• Volatility analysis</span>
                <span className="metric">• Correlation modeling</span>
                <span className="metric">• Rebalancing suggestions</span>
              </div>
            </div>

            <div className="section-card">
              <h3 className="section-title">Reconstructed Prices</h3>
              <p className="section-description">
                Advanced price reconstruction and modeling based on risk factor exposures 
                to understand factor influence on asset prices.
              </p>
              <div className="section-metrics">
                <span className="metric">• Factor-based modeling</span>
                <span className="metric">• Factor impact analysis</span>
                <span className="metric">• Scenario projections</span>
                <span className="metric">• Price decomposition</span>
              </div>
            </div>
          </div>

          <div className="methodology-section">
            <h2 className="methodology-title">Methodology & Technical Framework</h2>
            <p className="methodology-description">
              Z-Alpha Securities employs advanced econometric models and risk analysis techniques, 
              combining quantitative rigor with practical portfolio management insights:
            </p>
            <ul className="methodology-list">
              <li><strong>Volatility Models:</strong> EWMA, GARCH, EGARCH for volatility forecasting and risk prediction</li>
              <li><strong>Factor Analysis:</strong> Multiple regression and principal component analysis for exposure identification</li>
              <li><strong>Stress Testing:</strong> Monte Carlo simulations and historical scenario analysis</li>
              <li><strong>Optimization:</strong> Constrained optimization algorithms for portfolio construction</li>
              <li><strong>Correlation Analysis:</strong> Dynamic correlation matrices and regime-dependent modeling</li>
              <li><strong>Risk Attribution:</strong> Marginal and total risk contribution decomposition</li>
              <li><strong>Liquidity Modeling:</strong> Market impact analysis and exit time estimation</li>
            </ul>
          </div>

          <div className="interpretation-section">
            <h2 className="interpretation-title">Risk Metrics Interpretation Guide</h2>
            <div className="interpretation-grid">
              <div className="interpretation-item">
                <h4>Risk Score Classification</h4>
                <p><strong>Low (0-30):</strong> Portfolio exhibits low risk levels with good diversification<br/>
                <strong>Medium (31-70):</strong> Moderate risk requiring regular monitoring and potential adjustments<br/>
                <strong>High (71-100):</strong> Elevated risk requiring immediate attention and risk mitigation</p>
              </div>
              <div className="interpretation-item">
                <h4>Risk Contribution Analysis</h4>
                <p>Shows the percentage contribution of each position to total portfolio risk. 
                Positions with high risk contribution require special attention and may need 
                position size adjustments or hedging strategies.</p>
              </div>
              <div className="interpretation-item">
                <h4>Maximum Drawdown</h4>
                <p>Historical maximum decline in portfolio value from peak to trough. 
                High drawdown indicates significant volatility and potential for large losses. 
                Recovery periods and drawdown frequency are key monitoring metrics.</p>
              </div>
              <div className="interpretation-item">
                <h4>Correlation Analysis</h4>
                <p>High correlations between positions increase portfolio risk and reduce 
                diversification benefits. Low correlations provide better diversification 
                and risk reduction through position combination effects.</p>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default IntroductionPage;
