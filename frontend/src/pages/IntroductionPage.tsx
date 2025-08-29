import React, { useState } from 'react';
import './IntroductionPage.css';

const IntroductionPage: React.FC = () => {
  const [expandedCard, setExpandedCard] = useState<string | null>(null);
  const [expandedMetric, setExpandedMetric] = useState<string | null>(null);

  const handleMetricClick = (cardId: string, metricId: string) => {
    if (expandedCard === cardId && expandedMetric === metricId) {
      setExpandedCard(null);
      setExpandedMetric(null);
    } else {
      setExpandedCard(cardId);
      setExpandedMetric(metricId);
    }
  };

  const getExpandedContent = (cardId: string, metricId: string) => {
    const contentMap: { [key: string]: { [key: string]: any } } = {
      'portfolio-summary': {
        'risk-score': {
          title: 'Risk Score Calculation',
          description: 'Our proprietary algorithm combines multiple risk factors into a single actionable score.',
          details: [
            'Volatility contribution (40% weight)',
            'Concentration risk (25% weight)', 
            'Correlation impact (20% weight)',
            'Liquidity factor (15% weight)'
          ],
          example: 'A score of 75+ indicates your portfolio has similar risk to pre-crisis 2008 levels.'
        },
        'risk-contributors': {
          title: 'Top Risk Contributors Analysis',
          description: 'Identify which positions are driving your portfolio risk and why.',
          details: [
            'Marginal Risk Contribution calculation',
            'Position size vs. risk contribution mismatch',
            'Sector concentration impact',
            'Factor exposure contribution'
          ],
          example: 'If AAPL represents 10% of portfolio value but 25% of risk, consider reducing position size.'
        },
        'volatility-tracking': {
          title: 'Volatility vs. Benchmark',
          description: 'Compare your portfolio volatility against relevant benchmarks and market conditions.',
          details: [
            'Rolling 30-day volatility calculation',
            'Benchmark comparison (S&P 500, Russell 2000)',
            'Volatility regime classification',
            'Risk-adjusted performance metrics'
          ],
          example: 'Portfolio volatility of 18% vs. S&P 500 at 15% indicates higher risk exposure.'
        },
        'real-time-alerts': {
          title: 'Real-Time Risk Alerts',
          description: 'Proactive notifications when risk exceeds predefined thresholds.',
          details: [
            'Configurable risk thresholds',
            'Email and dashboard notifications',
            'Escalation protocols',
            'Historical alert accuracy tracking'
          ],
          example: 'Alert triggered when portfolio risk score exceeds 70 or any position contributes >20% of total risk.'
        }
      },
      'realized-risk': {
        'drawdown-analysis': {
          title: 'Maximum Drawdown Analysis',
          description: 'Comprehensive analysis of historical losses and recovery patterns.',
          details: [
            'Peak-to-trough loss calculation',
            'Recovery time analysis',
            'Drawdown frequency and severity',
            'Stress period identification'
          ],
          example: 'Portfolio experienced 15% drawdown in March 2020, recovered in 45 days vs. market 90 days.'
        },
        'correlation-breakdown': {
          title: 'Correlation Breakdown During Stress',
          description: 'Analysis of how correlations change during market stress periods.',
          details: [
            'Pre-stress vs. during-stress correlations',
            'Correlation regime detection',
            'Diversification effectiveness',
            'Hedging strategy evaluation'
          ],
          example: 'Correlations spiked from 0.3 to 0.8 during COVID crash, reducing diversification benefits.'
        },
        'risk-adjusted-returns': {
          title: 'Risk-Adjusted Performance Metrics',
          description: 'Comprehensive performance analysis accounting for risk taken.',
          details: [
            'Sharpe ratio calculation',
            'Sortino ratio (downside deviation)',
            'Calmar ratio (drawdown adjusted)',
            'Information ratio vs. benchmark'
          ],
          example: 'Sharpe ratio of 1.2 indicates strong risk-adjusted returns vs. market average of 0.8.'
        },
        'stress-performance': {
          title: 'Historical Stress Period Performance',
          description: 'How your portfolio performed during past market crises.',
          details: [
            'Crisis period identification',
            'Relative performance analysis',
            'Recovery pattern analysis',
            'Stress period lessons learned'
          ],
          example: 'Portfolio outperformed market by 5% during 2008 crisis due to defensive positioning.'
        }
      },
      'forecast-risk': {
        'marginal-contribution': {
          title: 'Marginal Risk Contribution',
          description: 'Advanced risk decomposition showing each position\'s impact on total portfolio risk.',
          details: [
            'Mathematical risk decomposition',
            'Position-specific risk drivers',
            'Hedging opportunity identification',
            'Risk budget allocation'
          ],
          example: 'TSLA contributes 18% of portfolio risk despite being only 8% of portfolio value.'
        },
        'volatility-forecasting': {
          title: 'Dynamic Volatility Forecasting',
          description: 'Predictive volatility models that adapt to changing market conditions.',
          details: [
            'EWMA, GARCH, EGARCH models',
            '1-30 day volatility forecasts',
            'Model accuracy tracking',
            'Regime-dependent adjustments'
          ],
          example: '30-day volatility forecast of 22% vs. current 18% suggests increasing risk ahead.'
        },
        'correlation-regime': {
          title: 'Correlation Regime Detection',
          description: 'Identify when correlations are about to break down and spike.',
          details: [
            'Regime classification algorithms',
            'Early warning signals',
            'Correlation breakdown prediction',
            'Hedging strategy optimization'
          ],
          example: 'Correlation regime indicator shows 85% probability of correlation spike in next 2 weeks.'
        },
        'risk-decomposition': {
          title: 'Risk Decomposition by Factor',
          description: 'Break down portfolio risk by underlying risk factors.',
          details: [
            'Factor risk attribution',
            'Systematic vs. idiosyncratic risk',
            'Factor timing analysis',
            'Risk factor hedging'
          ],
          example: '60% of portfolio risk comes from market factor, 25% from size factor, 15% from idiosyncratic risk.'
        }
      },
      'factor-exposure': {
        'factor-beta': {
          title: 'Factor Beta Analysis',
          description: 'Measure exposure to key risk factors: market, size, value, and momentum.',
          details: [
            'Multi-factor regression analysis',
            'Factor beta calculation',
            'Factor timing signals',
            'Factor rotation strategies'
          ],
          example: 'Portfolio has 1.2 market beta, 0.3 size beta, -0.1 value beta, 0.4 momentum beta.'
        },
        'sector-concentration': {
          title: 'Sector Concentration Analysis',
          description: 'Compare sector weights against benchmarks and identify concentration risks.',
          details: [
            'Sector weight calculation',
            'Benchmark comparison',
            'Concentration risk scoring',
            'Sector rotation opportunities'
          ],
          example: 'Technology sector represents 35% of portfolio vs. 28% in S&P 500, indicating overweight.'
        },
        'factor-timing': {
          title: 'Factor Timing Signals',
          description: 'Identify optimal times to increase or decrease factor exposures.',
          details: [
            'Factor performance cycles',
            'Regime shift detection',
            'Factor momentum analysis',
            'Timing signal generation'
          ],
          example: 'Value factor showing strong momentum, consider increasing value exposure.'
        },
        'r-squared-analysis': {
          title: 'R-Squared Factor Fit',
          description: 'Measure how well factor models explain portfolio returns.',
          details: [
            'Model fit statistics',
            'Residual analysis',
            'Factor model selection',
            'Model improvement suggestions'
          ],
          example: 'R-squared of 0.85 indicates factors explain 85% of portfolio return variation.'
        }
      },
      'stress-testing': {
        'crisis-scenarios': {
          title: 'Historical Crisis Scenarios',
          description: 'Test portfolio against real historical disasters with exact dates and conditions.',
          details: [
            '9/11 Attacks (Sep 2001)',
            'Global Financial Crisis (Sep 2008)',
            'COVID Crash (Mar 2020)',
            'Flash Crash (May 2010)',
            'Swiss Franc Shock (Jan 2015)'
          ],
          example: 'Portfolio would have lost 12% during COVID crash vs. market loss of 34%.'
        },
        'market-regime': {
          title: 'Market Regime Testing',
          description: 'Analyze performance across different market environments.',
          details: [
            'Crisis regime (high vol, high corr)',
            'Cautious regime (moderate vol, moderate corr)',
            'Bull regime (low vol, low corr)',
            'Regime transition probabilities'
          ],
          example: 'Portfolio performs best in cautious regimes, underperforms in crisis regimes.'
        },
        'loss-estimation': {
          title: 'Potential Loss Estimation',
          description: 'Calculate Value at Risk (VaR) and Conditional VaR for different confidence levels.',
          details: [
            '1-day, 5-day, 30-day VaR',
            '95%, 99% confidence levels',
            'Historical vs. parametric VaR',
            'Stress-adjusted VaR'
          ],
          example: '95% 1-day VaR of $2.5M means 5% chance of losing more than $2.5M in one day.'
        },
        'position-impact': {
          title: 'Position-Specific Stress Impact',
          description: 'Identify which positions would be most affected during stress scenarios.',
          details: [
            'Position stress sensitivity',
            'Liquidity impact during stress',
            'Correlation breakdown effects',
            'Hedging effectiveness'
          ],
          example: 'Small-cap positions show 40% higher stress impact than large-cap positions.'
        }
      },
      'concentration-risk': {
        'herfindahl-index': {
          title: 'Herfindahl Index Measurement',
          description: 'Sophisticated concentration metric that penalizes large positions exponentially.',
          details: [
            'HHI calculation methodology',
            'Industry benchmark comparison',
            'Concentration trend analysis',
            'Regulatory compliance tracking'
          ],
          example: 'HHI of 0.25 indicates moderate concentration (0.1 = diversified, 0.5 = concentrated).'
        },
        'sector-standards': {
          title: 'Sector Concentration vs. Standards',
          description: 'Compare sector weights against industry best practices and regulatory limits.',
          details: [
            'Industry benchmark data',
            'Regulatory concentration limits',
            'Peer comparison analysis',
            'Concentration optimization'
          ],
          example: 'Technology sector at 35% exceeds industry average of 28% and regulatory limit of 30%.'
        },
        'position-monitoring': {
          title: 'Largest Position Monitoring',
          description: 'Real-time monitoring of largest positions with configurable alerts.',
          details: [
            'Position size tracking',
            'Alert threshold configuration',
            'Position limit enforcement',
            'Concentration trend analysis'
          ],
          example: 'AAPL at 8% of portfolio triggers alert when approaching 10% limit.'
        },
        'asset-class-limits': {
          title: 'Concentration Limits by Asset Class',
          description: 'Different concentration limits for different asset classes and risk profiles.',
          details: [
            'Equity concentration limits',
            'Fixed income limits',
            'Alternative asset limits',
            'Geographic concentration limits'
          ],
          example: 'Single equity position limit: 5%, single bond position limit: 10%, single alternative: 3%.'
        }
      },
      'liquidity-risk': {
        'bid-ask-analysis': {
          title: 'Bid-Ask Spread Analysis',
          description: 'Monitor bid-ask spreads to assess market liquidity and trading costs.',
          details: [
            'Real-time spread monitoring',
            'Historical spread analysis',
            'Spread trend identification',
            'Liquidity deterioration alerts'
          ],
          example: 'Average bid-ask spread of 0.05% indicates high liquidity, 0.5% indicates low liquidity.'
        },
        'exit-time': {
          title: 'Exit Time Calculations',
          description: 'Calculate how long it would take to liquidate positions without moving the market.',
          details: [
            'Market impact modeling',
            'Volume analysis',
            'Exit strategy optimization',
            'Liquidation cost estimation'
          ],
          example: 'It would take 3.5 days to liquidate AAPL position without moving price more than 1%.'
        },
        'market-impact': {
          title: 'Market Impact Analysis',
          description: 'Estimate the price impact of large orders and optimize execution strategies.',
          details: [
            'Impact model calibration',
            'Order size optimization',
            'Execution strategy selection',
            'Cost-benefit analysis'
          ],
          example: 'Selling 100,000 shares would move price down 2.5%, suggesting smaller order sizes.'
        },
        'liquidity-alerts': {
          title: 'Liquidity Deterioration Alerts',
          description: 'Proactive alerts when liquidity conditions deteriorate.',
          details: [
            'Liquidity metric tracking',
            'Alert threshold configuration',
            'Deterioration pattern recognition',
            'Action recommendation generation'
          ],
          example: 'Liquidity alert triggered when average spread increases 50% from normal levels.'
        }
      },
      'volatility-sizing': {
        'risk-parity': {
          title: 'Risk-Parity Weight Calculations',
          description: 'Optimize position weights to equalize risk contribution across all positions.',
          details: [
            'Risk contribution equalization',
            'Volatility targeting',
            'Rebalancing frequency optimization',
            'Transaction cost consideration'
          ],
          example: 'Risk-parity weights: AAPL 6%, MSFT 5%, GOOGL 4% (vs. equal weights: 8.3% each).'
        },
        'volatility-adjusted': {
          title: 'Volatility-Adjusted Position Sizing',
          description: 'Adjust position sizes based on individual asset volatility.',
          details: [
            'Volatility-based sizing',
            'Risk budget allocation',
            'Position limit optimization',
            'Volatility regime adjustment'
          ],
          example: 'High volatility stocks (30% vol) get smaller position sizes than low volatility (15% vol).'
        },
        'correlation-adjusted': {
          title: 'Correlation-Adjusted Risk Allocation',
          description: 'Account for correlations when allocating risk across positions.',
          details: [
            'Correlation matrix analysis',
            'Diversification benefit calculation',
            'Correlation regime adjustment',
            'Hedging strategy optimization'
          ],
          example: 'Positions with 0.8 correlation get 40% less risk allocation than uncorrelated positions.'
        },
        'rebalancing-suggestions': {
          title: 'Rebalancing Suggestions and Triggers',
          description: 'Automated suggestions for when and how to rebalance the portfolio.',
          details: [
            'Rebalancing threshold monitoring',
            'Optimal rebalancing frequency',
            'Transaction cost optimization',
            'Tax-efficient rebalancing'
          ],
          example: 'Rebalancing suggested when position weights deviate more than 2% from targets.'
        }
      }
    };

    return contentMap[cardId]?.[metricId] || null;
  };

  return (
    <div id="introduction-root" className="introduction-page">
      <div className="introduction-container">
        {/* Hero Section */}
        <div className="introduction-hero-section">
          <div className="introduction-hero-content">
            <div className="introduction-hero-titles">
              <h1 className="introduction-main-title">
                <span className="introduction-title-line">INSTITUTIONAL</span>
                <span className="introduction-title-line">RISK MANAGEMENT</span>
                <span className="introduction-title-line">PLATFORM</span>
              </h1>
              
              <div className="introduction-tagline">
                <span className="introduction-tagline-text">Where Quantitative Excellence Meets Risk Intelligence</span>
                <div className="introduction-tagline-divider"></div>
              </div>
            </div>

            <div className="introduction-hero-stats">
              <div className="stat-item">
                <div className="stat-number">$2.8B</div>
                <div className="stat-label">AUM</div>
              </div>
              <div className="stat-item">
                <div className="stat-number">1.47</div>
                <div className="stat-label">Sharpe Ratio</div>
              </div>
              <div className="stat-item">
                <div className="stat-number">12.3%</div>
                <div className="stat-label">Annual Return</div>
              </div>
              <div className="stat-item">
                <div className="stat-number">8.2%</div>
                <div className="stat-label">Max Drawdown</div>
              </div>
              <div className="stat-item">
                <div className="stat-number">1.85</div>
                <div className="stat-label">Sortino Ratio</div>
              </div>
              <div className="stat-item">
                <div className="stat-number">15.2%</div>
                <div className="stat-label">Volatility</div>
              </div>
            </div>
          </div>
        </div>

        <div className="introduction-content">
          <p className="introduction-description">
            Z-Alpha Securities delivers institutional-grade risk management technology that transforms 
            how portfolio managers identify, measure, and mitigate risk. Our platform solves real-world 
            problems: from preventing catastrophic losses during market crashes to optimizing position 
            sizing for maximum risk-adjusted returns.
          </p>

          <div className="section-divider"></div>

          <div className="sections-grid">
            <div className={`section-card ${expandedCard === 'portfolio-summary' ? 'expanded' : ''}`}>
              <h3 className="section-title">Portfolio Summary</h3>
              <p className="section-description">
                Real-time portfolio health monitoring that prevents the next LTCM or Archegos disaster. 
                Instantly identify which positions are driving 80% of your risk and take action before 
                it's too late.
              </p>
              <div className="section-metrics">
                <span 
                  className={`metric ${expandedMetric === 'risk-score' ? 'active' : ''}`}
                  onClick={() => handleMetricClick('portfolio-summary', 'risk-score')}
                >
                  • Single risk score (0-100) for instant decision making
                </span>
                <span 
                  className={`metric ${expandedMetric === 'risk-contributors' ? 'active' : ''}`}
                  onClick={() => handleMetricClick('portfolio-summary', 'risk-contributors')}
                >
                  • Top 5 risk contributors with exact percentages
                </span>
                <span 
                  className={`metric ${expandedMetric === 'volatility-tracking' ? 'active' : ''}`}
                  onClick={() => handleMetricClick('portfolio-summary', 'volatility-tracking')}
                >
                  • Portfolio volatility vs. benchmark tracking
                </span>
                <span 
                  className={`metric ${expandedMetric === 'real-time-alerts' ? 'active' : ''}`}
                  onClick={() => handleMetricClick('portfolio-summary', 'real-time-alerts')}
                >
                  • Real-time alerts when risk exceeds thresholds
                </span>
              </div>
              {expandedCard === 'portfolio-summary' && expandedMetric && (
                <div className="expanded-content">
                  {(() => {
                    const content = getExpandedContent('portfolio-summary', expandedMetric);
                    return content ? (
                      <div className="expanded-details">
                        <h4>{content.title}</h4>
                        <p>{content.description}</p>
                        <ul>
                          {content.details.map((detail: string, index: number) => (
                            <li key={index}>{detail}</li>
                          ))}
                        </ul>
                        <div className="example-box">
                          <strong>Example:</strong> {content.example}
                        </div>
                      </div>
                    ) : null;
                  })()}
                </div>
              )}
            </div>

            <div className={`section-card ${expandedCard === 'realized-risk' ? 'expanded' : ''}`}>
              <h3 className="section-title">Realized Risk</h3>
              <p className="section-description">
                Learn from actual losses. Analyze what went wrong in past drawdowns and build 
                defensive strategies. See correlations that break down when you need them most.
              </p>
              <div className="section-metrics">
                <span 
                  className={`metric ${expandedMetric === 'drawdown-analysis' ? 'active' : ''}`}
                  onClick={() => handleMetricClick('realized-risk', 'drawdown-analysis')}
                >
                  • Maximum drawdown analysis with recovery periods
                </span>
                <span 
                  className={`metric ${expandedMetric === 'correlation-breakdown' ? 'active' : ''}`}
                  onClick={() => handleMetricClick('realized-risk', 'correlation-breakdown')}
                >
                  • Correlation breakdown during stress periods
                </span>
                <span 
                  className={`metric ${expandedMetric === 'risk-adjusted-returns' ? 'active' : ''}`}
                  onClick={() => handleMetricClick('realized-risk', 'risk-adjusted-returns')}
                >
                  • Risk-adjusted returns (Sharpe, Sortino ratios)
                </span>
                <span 
                  className={`metric ${expandedMetric === 'stress-performance' ? 'active' : ''}`}
                  onClick={() => handleMetricClick('realized-risk', 'stress-performance')}
                >
                  • Historical stress period performance
                </span>
              </div>
              {expandedCard === 'realized-risk' && expandedMetric && (
                <div className="expanded-content">
                  {(() => {
                    const content = getExpandedContent('realized-risk', expandedMetric);
                    return content ? (
                      <div className="expanded-details">
                        <h4>{content.title}</h4>
                        <p>{content.description}</p>
                        <ul>
                          {content.details.map((detail: string, index: number) => (
                            <li key={index}>{detail}</li>
                          ))}
                        </ul>
                        <div className="example-box">
                          <strong>Example:</strong> {content.example}
                        </div>
                      </div>
                    ) : null;
                  })()}
                </div>
              )}
            </div>

            <div className={`section-card ${expandedCard === 'forecast-risk' ? 'expanded' : ''}`}>
              <h3 className="section-title">Forecast Risk</h3>
              <p className="section-description">
                Predict tomorrow's risk today. Advanced volatility models (EWMA, GARCH, EGARCH) 
                that adapt to changing market conditions and warn you before correlations spike.
              </p>
              <div className="section-metrics">
                <span 
                  className={`metric ${expandedMetric === 'marginal-contribution' ? 'active' : ''}`}
                  onClick={() => handleMetricClick('forecast-risk', 'marginal-contribution')}
                >
                  • Marginal Risk Contribution for each position
                </span>
                <span 
                  className={`metric ${expandedMetric === 'volatility-forecasting' ? 'active' : ''}`}
                  onClick={() => handleMetricClick('forecast-risk', 'volatility-forecasting')}
                >
                  • Dynamic volatility forecasting (1-30 days)
                </span>
                <span 
                  className={`metric ${expandedMetric === 'correlation-regime' ? 'active' : ''}`}
                  onClick={() => handleMetricClick('forecast-risk', 'correlation-regime')}
                >
                  • Correlation regime detection
                </span>
                <span 
                  className={`metric ${expandedMetric === 'risk-decomposition' ? 'active' : ''}`}
                  onClick={() => handleMetricClick('forecast-risk', 'risk-decomposition')}
                >
                  • Risk decomposition by factor
                </span>
              </div>
              {expandedCard === 'forecast-risk' && expandedMetric && (
                <div className="expanded-content">
                  {(() => {
                    const content = getExpandedContent('forecast-risk', expandedMetric);
                    return content ? (
                      <div className="expanded-details">
                        <h4>{content.title}</h4>
                        <p>{content.description}</p>
                        <ul>
                          {content.details.map((detail: string, index: number) => (
                            <li key={index}>{detail}</li>
                          ))}
                        </ul>
                        <div className="example-box">
                          <strong>Example:</strong> {content.example}
                        </div>
                      </div>
                    ) : null;
                  })()}
                </div>
              )}
            </div>

            <div className={`section-card ${expandedCard === 'factor-exposure' ? 'expanded' : ''}`}>
              <h3 className="section-title">Factor Exposure</h3>
              <p className="section-description">
                Don't get blindsided by hidden factor bets. Identify when your "diversified" portfolio 
                is actually a concentrated bet on tech, value, or momentum factors.
              </p>
              <div className="section-metrics">
                <span 
                  className={`metric ${expandedMetric === 'factor-beta' ? 'active' : ''}`}
                  onClick={() => handleMetricClick('factor-exposure', 'factor-beta')}
                >
                  • Factor beta analysis (market, size, value, momentum)
                </span>
                <span 
                  className={`metric ${expandedMetric === 'sector-concentration' ? 'active' : ''}`}
                  onClick={() => handleMetricClick('factor-exposure', 'sector-concentration')}
                >
                  • Sector concentration vs. benchmark
                </span>
                <span 
                  className={`metric ${expandedMetric === 'factor-timing' ? 'active' : ''}`}
                  onClick={() => handleMetricClick('factor-exposure', 'factor-timing')}
                >
                  • Factor timing signals and regime shifts
                </span>
                <span 
                  className={`metric ${expandedMetric === 'r-squared-analysis' ? 'active' : ''}`}
                  onClick={() => handleMetricClick('factor-exposure', 'r-squared-analysis')}
                >
                  • R-squared analysis for factor fit
                </span>
              </div>
              {expandedCard === 'factor-exposure' && expandedMetric && (
                <div className="expanded-content">
                  {(() => {
                    const content = getExpandedContent('factor-exposure', expandedMetric);
                    return content ? (
                      <div className="expanded-details">
                        <h4>{content.title}</h4>
                        <p>{content.description}</p>
                        <ul>
                          {content.details.map((detail: string, index: number) => (
                            <li key={index}>{detail}</li>
                          ))}
                        </ul>
                        <div className="example-box">
                          <strong>Example:</strong> {content.example}
                        </div>
                      </div>
                    ) : null;
                  })()}
                </div>
              )}
            </div>

            <div className={`section-card ${expandedCard === 'stress-testing' ? 'expanded' : ''}`}>
              <h3 className="section-title">Stress Testing</h3>
              <p className="section-description">
                Survive the next crisis. Test your portfolio against real historical disasters: 
                9/11, GFC 2008, COVID crash, Flash Crash 2010. Know your worst-case scenario.
              </p>
              <div className="section-metrics">
                <span 
                  className={`metric ${expandedMetric === 'crisis-scenarios' ? 'active' : ''}`}
                  onClick={() => handleMetricClick('stress-testing', 'crisis-scenarios')}
                >
                  • Historical crisis scenarios with exact dates
                </span>
                <span 
                  className={`metric ${expandedMetric === 'market-regime' ? 'active' : ''}`}
                  onClick={() => handleMetricClick('stress-testing', 'market-regime')}
                >
                  • Market regime testing (crisis, cautious, bull)
                </span>
                <span 
                  className={`metric ${expandedMetric === 'loss-estimation' ? 'active' : ''}`}
                  onClick={() => handleMetricClick('stress-testing', 'loss-estimation')}
                >
                  • Potential loss estimation (VaR, CVaR)
                </span>
                <span 
                  className={`metric ${expandedMetric === 'position-impact' ? 'active' : ''}`}
                  onClick={() => handleMetricClick('stress-testing', 'position-impact')}
                >
                  • Position-specific stress impact
                </span>
              </div>
              {expandedCard === 'stress-testing' && expandedMetric && (
                <div className="expanded-content">
                  {(() => {
                    const content = getExpandedContent('stress-testing', expandedMetric);
                    return content ? (
                      <div className="expanded-details">
                        <h4>{content.title}</h4>
                        <p>{content.description}</p>
                        <ul>
                          {content.details.map((detail: string, index: number) => (
                            <li key={index}>{detail}</li>
                          ))}
                        </ul>
                        <div className="example-box">
                          <strong>Example:</strong> {content.example}
                        </div>
                      </div>
                    ) : null;
                  })()}
                </div>
              )}
            </div>

            <div className={`section-card ${expandedCard === 'concentration-risk' ? 'expanded' : ''}`}>
              <h3 className="section-title">Concentration Risk</h3>
              <p className="section-description">
                Avoid the next Enron or Lehman Brothers. Monitor concentration using Herfindahl Index 
                and get alerts when any position exceeds safe limits.
              </p>
              <div className="section-metrics">
                <span 
                  className={`metric ${expandedMetric === 'herfindahl-index' ? 'active' : ''}`}
                  onClick={() => handleMetricClick('concentration-risk', 'herfindahl-index')}
                >
                  • Herfindahl Index for concentration measurement
                </span>
                <span 
                  className={`metric ${expandedMetric === 'sector-standards' ? 'active' : ''}`}
                  onClick={() => handleMetricClick('concentration-risk', 'sector-standards')}
                >
                  • Sector concentration vs. industry standards
                </span>
                <span 
                  className={`metric ${expandedMetric === 'position-monitoring' ? 'active' : ''}`}
                  onClick={() => handleMetricClick('concentration-risk', 'position-monitoring')}
                >
                  • Largest position monitoring with alerts
                </span>
                <span 
                  className={`metric ${expandedMetric === 'asset-class-limits' ? 'active' : ''}`}
                  onClick={() => handleMetricClick('concentration-risk', 'asset-class-limits')}
                >
                  • Concentration limits by asset class
                </span>
              </div>
              {expandedCard === 'concentration-risk' && expandedMetric && (
                <div className="expanded-content">
                  {(() => {
                    const content = getExpandedContent('concentration-risk', expandedMetric);
                    return content ? (
                      <div className="expanded-details">
                        <h4>{content.title}</h4>
                        <p>{content.description}</p>
                        <ul>
                          {content.details.map((detail: string, index: number) => (
                            <li key={index}>{detail}</li>
                          ))}
                        </ul>
                        <div className="example-box">
                          <strong>Example:</strong> {content.example}
                        </div>
                      </div>
                    ) : null;
                  })()}
                </div>
              )}
            </div>

            <div className={`section-card ${expandedCard === 'liquidity-risk' ? 'expanded' : ''}`}>
              <h3 className="section-title">Liquidity Risk</h3>
              <p className="section-description">
                Exit when you want to, not when you have to. Calculate how long it takes to liquidate 
                positions without moving the market, and identify illiquid traps.
              </p>
              <div className="section-metrics">
                <span 
                  className={`metric ${expandedMetric === 'bid-ask-analysis' ? 'active' : ''}`}
                  onClick={() => handleMetricClick('liquidity-risk', 'bid-ask-analysis')}
                >
                  • Bid-ask spread analysis and monitoring
                </span>
                <span 
                  className={`metric ${expandedMetric === 'exit-time' ? 'active' : ''}`}
                  onClick={() => handleMetricClick('liquidity-risk', 'exit-time')}
                >
                  • Exit time calculations (days to liquidate)
                </span>
                <span 
                  className={`metric ${expandedMetric === 'market-impact' ? 'active' : ''}`}
                  onClick={() => handleMetricClick('liquidity-risk', 'market-impact')}
                >
                  • Market impact analysis for large orders
                </span>
                <span 
                  className={`metric ${expandedMetric === 'liquidity-alerts' ? 'active' : ''}`}
                  onClick={() => handleMetricClick('liquidity-risk', 'liquidity-alerts')}
                >
                  • Liquidity alerts for deteriorating conditions
                </span>
              </div>
              {expandedCard === 'liquidity-risk' && expandedMetric && (
                <div className="expanded-content">
                  {(() => {
                    const content = getExpandedContent('liquidity-risk', expandedMetric);
                    return content ? (
                      <div className="expanded-details">
                        <h4>{content.title}</h4>
                        <p>{content.description}</p>
                        <ul>
                          {content.details.map((detail: string, index: number) => (
                            <li key={index}>{detail}</li>
                          ))}
                        </ul>
                        <div className="example-box">
                          <strong>Example:</strong> {content.example}
                        </div>
                      </div>
                    ) : null;
                  })()}
                </div>
              )}
            </div>

            <div className={`section-card ${expandedCard === 'volatility-sizing' ? 'expanded' : ''}`}>
              <h3 className="section-title">Volatility-Based Sizing</h3>
              <p className="section-description">
                Optimize position sizes for maximum risk-adjusted returns. Use risk-parity principles 
                to balance portfolio risk across all positions, not just equal weights.
              </p>
              <div className="section-metrics">
                <span 
                  className={`metric ${expandedMetric === 'risk-parity' ? 'active' : ''}`}
                  onClick={() => handleMetricClick('volatility-sizing', 'risk-parity')}
                >
                  • Risk-parity weight calculations
                </span>
                <span 
                  className={`metric ${expandedMetric === 'volatility-adjusted' ? 'active' : ''}`}
                  onClick={() => handleMetricClick('volatility-sizing', 'volatility-adjusted')}
                >
                  • Volatility-adjusted position sizing
                </span>
                <span 
                  className={`metric ${expandedMetric === 'correlation-adjusted' ? 'active' : ''}`}
                  onClick={() => handleMetricClick('volatility-sizing', 'correlation-adjusted')}
                >
                  • Correlation-adjusted risk allocation
                </span>
                <span 
                  className={`metric ${expandedMetric === 'rebalancing-suggestions' ? 'active' : ''}`}
                  onClick={() => handleMetricClick('volatility-sizing', 'rebalancing-suggestions')}
                >
                  • Rebalancing suggestions and triggers
                </span>
              </div>
              {expandedCard === 'volatility-sizing' && expandedMetric && (
                <div className="expanded-content">
                  {(() => {
                    const content = getExpandedContent('volatility-sizing', expandedMetric);
                    return content ? (
                      <div className="expanded-details">
                        <h4>{content.title}</h4>
                        <p>{content.description}</p>
                        <ul>
                          {content.details.map((detail: string, index: number) => (
                            <li key={index}>{detail}</li>
                          ))}
                        </ul>
                        <div className="example-box">
                          <strong>Example:</strong> {content.example}
                        </div>
                      </div>
                    ) : null;
                  })()}
                </div>
              )}
            </div>
          </div>

          <div className="section-divider thick"></div>

          <div className="methodology-section">
            <h2 className="methodology-title">Real-World Problems We Solve</h2>
            <p className="methodology-description">
              Every feature addresses specific pain points that have cost investors billions:
            </p>
            <ul className="methodology-list">
              <li><strong>Problem:</strong> "We didn't see the risk coming" → <strong>Solution:</strong> Real-time risk monitoring with predictive models</li>
              <li><strong>Problem:</strong> "All correlations went to 1 during the crash" → <strong>Solution:</strong> Dynamic correlation modeling and regime detection</li>
              <li><strong>Problem:</strong> "We couldn't exit our positions" → <strong>Solution:</strong> Liquidity analysis and exit time calculations</li>
              <li><strong>Problem:</strong> "One position blew up our entire portfolio" → <strong>Solution:</strong> Concentration monitoring and position limits</li>
              <li><strong>Problem:</strong> "Our risk models failed during stress" → <strong>Solution:</strong> Historical stress testing with real crisis data</li>
              <li><strong>Problem:</strong> "We were overexposed to hidden factors" → <strong>Solution:</strong> Factor exposure analysis and regime detection</li>
              <li><strong>Problem:</strong> "We didn't know our true risk-adjusted returns" → <strong>Solution:</strong> Comprehensive risk-adjusted performance metrics</li>
            </ul>
          </div>

          <div className="section-divider"></div>

          <div className="interpretation-section">
            <h2 className="interpretation-title">Actionable Risk Intelligence</h2>
            <div className="interpretation-grid">
              <div className="interpretation-item">
                <h4>Risk Score (0-100)</h4>
                <p><strong>0-30 (Green):</strong> Portfolio is well-diversified with low risk. Continue current strategy.<br/>
                <strong>31-70 (Yellow):</strong> Moderate risk requiring position adjustments or hedging.<br/>
                <strong>71-100 (Red):</strong> High risk requiring immediate action - reduce positions or add hedges.</p>
              </div>
              <div className="interpretation-item">
                <h4>Marginal Risk Contribution</h4>
                <p>Shows which positions contribute most to portfolio risk. If AAPL contributes 25% of risk 
                but only 10% of portfolio value, consider reducing the position or hedging it. 
                High MRC positions are your biggest vulnerabilities.</p>
              </div>
              <div className="interpretation-item">
                <h4>Maximum Drawdown</h4>
                <p>Your worst historical loss from peak to trough. If your max drawdown is 15% and 
                you're currently down 12%, you're approaching dangerous territory. Use this to set 
                stop-loss levels and position sizing limits.</p>
              </div>
              <div className="interpretation-item">
                <h4>Correlation Breakdown</h4>
                <p>During normal markets, correlations may be low, but during crashes they spike to 0.8-0.9. 
                Our models detect when correlations are about to break down, giving you time to 
                adjust positions before the crash.</p>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default IntroductionPage;
