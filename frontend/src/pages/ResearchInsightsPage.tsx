import React, { useEffect, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import Navbar from '../components/Navbar';
import LandingFooter from '../components/LandingFooter';
import './ResearchInsightsPage.css';
import { TrendingUp, TrendingDown, BarChart, PieChart, Shield, Award, Activity, DollarSign } from 'lucide-react';

const ResearchInsightsPage: React.FC = () => {
  const navigate = useNavigate();
  const [activeTab, setActiveTab] = useState('market-regime');

  // Intersection Observer for animations
  useEffect(() => {
    const observerOptions = {
      threshold: 0.1,
      rootMargin: '0px 0px -50px 0px'
    };

    const observer = new IntersectionObserver((entries) => {
      entries.forEach((entry) => {
        if (entry.isIntersecting) {
          entry.target.classList.add('animate-in');
        }
      });
    }, observerOptions);

    const animateElements = document.querySelectorAll('.animate-on-scroll');
    animateElements.forEach((el) => observer.observe(el));

    return () => observer.disconnect();
  }, []);

  const handleNavigate = (page: string) => {
    if (page === 'risk-solutions') {
      navigate('/risk-solutions');
    } else if (page === 'who-we-are') {
      navigate('/who-we-are');
    } else if (page === 'research-insights') {
      navigate('/research-insights');
    } else if (page === 'careers') {
      navigate('/careers');
    }
    // Add other navigation logic as needed
  };

  // Market Regime Detection Data
  const marketRegimeData = [
    {
      regime: 'Crisis',
      probability: 15,
      description: 'High volatility, negative momentum, elevated correlations',
      indicators: {
        volatility: 'High (>25%)',
        correlation: 'Elevated (>0.7)',
        momentum: 'Negative',
        signal: 'Risk-Off'
      },
      color: '#d32f2f'
    },
    {
      regime: 'Cautious',
      probability: 35,
      description: 'Moderate volatility, mixed signals, selective correlation',
      indicators: {
        volatility: 'Moderate (15-25%)',
        correlation: 'Mixed (0.4-0.7)',
        momentum: 'Neutral',
        signal: 'Selective'
      },
      color: '#ff9800'
    },
    {
      regime: 'Bull',
      probability: 40,
      description: 'Low volatility, positive momentum, diversified correlations',
      indicators: {
        volatility: 'Low (<15%)',
        correlation: 'Diversified (<0.4)',
        momentum: 'Positive',
        signal: 'Risk-On'
      },
      color: '#388e3c'
    },
    {
      regime: 'Neutral',
      probability: 10,
      description: 'Stable conditions, balanced risk-reward environment',
      indicators: {
        volatility: 'Stable (10-20%)',
        correlation: 'Balanced (0.3-0.6)',
        momentum: 'Sideways',
        signal: 'Balanced'
      },
      color: '#1976d2'
    }
  ];

  // Risk Scoring Components Data
  const riskScoringData = [
    {
      component: 'Concentration Risk (HHI)',
      score: 75,
      weight: 25,
      description: 'Portfolio concentration measured by Herfindahl-Hirschman Index',
      status: 'Moderate',
      trend: 'stable'
    },
    {
      component: 'Volatility (GARCH)',
      score: 65,
      weight: 20,
      description: 'EWMA and E-GARCH volatility forecasting models',
      status: 'Acceptable',
      trend: 'decreasing'
    },
    {
      component: 'Beta Exposure',
      score: 80,
      weight: 15,
      description: 'Market beta and systematic risk exposure',
      status: 'High',
      trend: 'increasing'
    },
    {
      component: 'Factor L1 Norm',
      score: 55,
      weight: 15,
      description: 'Factor exposure concentration and style drift',
      status: 'Low',
      trend: 'stable'
    },
    {
      component: 'Stress Testing',
      score: 70,
      weight: 15,
      description: 'Historical scenario stress test performance',
      status: 'Moderate',
      trend: 'improving'
    },
    {
      component: 'Liquidity Risk',
      score: 60,
      weight: 10,
      description: 'ADV ratio and bid-ask spread analysis',
      status: 'Acceptable',
      trend: 'stable'
    }
  ];

  // Stress Testing Scenarios
  const stressTestingData = [
    {
      scenario: 'COVID-19 Crash (2020)',
      dateRange: 'Feb 2020 - Mar 2020',
      marketDecline: -34.0,
      portfolioImpact: -28.5,
      maxDrawdown: -31.2,
      recoveryDays: 156,
      status: 'Passed'
    },
    {
      scenario: 'Tech Bubble Burst (2000)',
      dateRange: 'Mar 2000 - Oct 2002',
      marketDecline: -49.0,
      portfolioImpact: -42.3,
      maxDrawdown: -45.8,
      recoveryDays: 892,
      status: 'Caution'
    },
    {
      scenario: 'Financial Crisis (2008)',
      dateRange: 'Oct 2007 - Mar 2009',
      marketDecline: -57.0,
      portfolioImpact: -48.7,
      maxDrawdown: -52.1,
      recoveryDays: 1,
      status: 'Passed'
    },
    {
      scenario: 'Flash Crash (2010)',
      dateRange: 'May 6, 2010',
      marketDecline: -9.2,
      portfolioImpact: -7.8,
      maxDrawdown: -8.5,
      recoveryDays: 1,
      status: 'Passed'
    },
    {
      scenario: 'European Debt Crisis (2011)',
      dateRange: 'Apr 2011 - Oct 2011',
      marketDecline: -19.4,
      portfolioImpact: -16.2,
      maxDrawdown: -17.8,
      recoveryDays: 89,
      status: 'Passed'
    }
  ];

  // Volatility Forecasting Data
  const volatilityData = [
    {
      model: 'EWMA (λ=0.94)',
      currentForecast: 18.5,
      oneWeek: 19.2,
      oneMonth: 20.8,
      threeMonth: 22.1,
      accuracy: 87.3,
      description: 'Exponentially Weighted Moving Average'
    },
    {
      model: 'GARCH(1,1)',
      currentForecast: 17.8,
      oneWeek: 18.9,
      oneMonth: 21.2,
      threeMonth: 23.5,
      accuracy: 89.1,
      description: 'Generalized Autoregressive Conditional Heteroskedasticity'
    },
    {
      model: 'E-GARCH',
      currentForecast: 18.1,
      oneWeek: 19.0,
      oneMonth: 21.5,
      threeMonth: 24.2,
      accuracy: 91.2,
      description: 'Exponential GARCH with asymmetric effects'
    },
    {
      model: 'Historical (30d)',
      currentForecast: 16.9,
      oneWeek: 17.1,
      oneMonth: 17.8,
      threeMonth: 18.5,
      accuracy: 78.5,
      description: 'Rolling historical volatility'
    }
  ];

  const researchCategories = [
    {
      id: 'market-regime',
      title: 'Market Regime Detection',
      description: 'AI-powered regime classification and transition analysis',
      icon: TrendingUp,
      color: '#1976d2'
    },
    {
      id: 'risk-scoring',
      title: 'Risk Scoring Framework',
      description: 'Composite risk scores and component analysis',
      icon: Shield,
      color: '#d32f2f'
    },
    {
      id: 'stress-testing',
      title: 'Historical Stress Testing',
      description: 'Portfolio performance under historical market stress',
      icon: BarChart,
      color: '#ff9800'
    },
    {
      id: 'volatility-forecast',
      title: 'Volatility Forecasting',
      description: 'GARCH, E-GARCH, and EWMA volatility models',
      icon: Activity,
      color: '#9c27b0'
    },
    {
      id: 'factor-analysis',
      title: 'Factor Exposure Analysis',
      description: 'Style factor decomposition and attribution',
      icon: PieChart,
      color: '#388e3c'
    },
    {
      id: 'portfolio-analytics',
      title: 'Portfolio Analytics',
      description: 'Performance attribution and risk-adjusted metrics',
      icon: Award,
      color: '#f57c00'
    }
  ];

  // Helper to locate images by fuzzy name in /images
  const imagesCtx = (require as any).context('../images', false, /\.(png|jpe?g|webp|avif)$/);
  const findImage = (hints: string[]): string | null => {
    const keys: string[] = imagesCtx.keys();
    const lower = keys.map((k) => k.toLowerCase());
    for (const hint of hints.map((h) => h.toLowerCase())) {
      const idx = lower.findIndex((k) => k.includes(hint));
      if (idx !== -1) {
        const mod = imagesCtx(keys[idx]);
        return (mod && mod.default) ? mod.default : mod;
      }
    }
    return null;
  };

  const heroImage = findImage(['quant']);

  return (
    <div className="research-insights-page">
      <Navbar 
        onNavigate={handleNavigate}
        onBrandClick={() => navigate('/')}
        onClientLogin={() => navigate('/login')}
      />
      
      {/* Hero Section */}
      <section style={{
        position: 'relative',
        height: '60vh',
        backgroundImage: heroImage 
          ? `linear-gradient(rgba(0,0,0,0.4), rgba(0,0,0,0.4)), url(${heroImage})`
          : 'linear-gradient(135deg, #1e3c72 0%, #2a5298 100%)',
        backgroundSize: 'cover',
        backgroundPosition: 'center',
        backgroundRepeat: 'no-repeat',
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'center',
        marginTop: '70px',
        width: '100vw',
        marginLeft: 'calc(-50vw + 50%)',
        marginRight: 'calc(-50vw + 50%)'
      }}>
        <div style={{
          textAlign: 'center',
          color: 'white',
          maxWidth: '800px',
          padding: '0 2rem'
        }}>
          <h1 className="animate-on-scroll" style={{
            fontSize: '4rem',
            fontWeight: 'bold',
            marginBottom: '1.5rem',
            letterSpacing: '-0.02em'
          }}>
            Research & Insights
          </h1>
          <p className="animate-on-scroll" style={{
            fontSize: '1.5rem',
            opacity: 0.9,
            lineHeight: '1.6',
            fontWeight: '300'
          }}>
            Advanced quantitative research, market regime analysis, and institutional-grade risk insights powered by cutting-edge models.
          </p>
        </div>
      </section>

      {/* Research Categories */}
      <section className="animate-on-scroll" style={{ padding: '6rem 2rem' }}>
        <div style={{ maxWidth: '1200px', margin: '0 auto' }}>
          <div style={{ textAlign: 'center', marginBottom: '4rem' }}>
            <h2 style={{
              fontSize: '3rem',
              fontWeight: 'bold',
              color: '#202124',
              marginBottom: '1rem'
            }}>
              Research Categories
            </h2>
            <p style={{
              fontSize: '1.25rem',
              color: '#5f6368',
              maxWidth: '600px',
              margin: '0 auto'
            }}>
              Explore our comprehensive quantitative research and analytical frameworks
            </p>
          </div>

          <div style={{
            display: 'grid',
            gridTemplateColumns: 'repeat(auto-fit, minmax(350px, 1fr))',
            gap: '2rem'
          }}>
            {researchCategories.map((category, index) => (
              <div
                key={category.id}
                className="animate-on-scroll research-card"
                style={{
                  backgroundColor: 'white',
                  padding: '2.5rem',
                  borderRadius: '16px',
                  border: '1px solid #e8eaed',
                  cursor: 'pointer',
                  transition: 'all 0.3s ease',
                  boxShadow: '0 4px 12px rgba(0,0,0,0.08)',
                  animationDelay: `${index * 0.1}s`
                }}
                onClick={() => setActiveTab(category.id)}
                onMouseEnter={(e) => {
                  e.currentTarget.style.transform = 'translateY(-8px)';
                  e.currentTarget.style.boxShadow = '0 12px 24px rgba(0,0,0,0.15)';
                }}
                onMouseLeave={(e) => {
                  e.currentTarget.style.transform = 'translateY(0)';
                  e.currentTarget.style.boxShadow = '0 4px 12px rgba(0,0,0,0.08)';
                }}
              >
                <div style={{
                  width: '80px',
                  height: '80px',
                  backgroundColor: category.color,
                  borderRadius: '16px',
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'center',
                  marginBottom: '1.5rem'
                }}>
                  <category.icon size={40} color="white" />
                </div>
                <h3 style={{
                  fontSize: '1.5rem',
                  fontWeight: 'bold',
                  color: '#202124',
                  marginBottom: '1rem'
                }}>
                  {category.title}
                </h3>
                <p style={{
                  color: '#5f6368',
                  fontSize: '1rem',
                  lineHeight: '1.6'
                }}>
                  {category.description}
                </p>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* Market Regime Detection Section */}
      {activeTab === 'market-regime' && (
        <section className="animate-on-scroll" style={{ padding: '6rem 2rem', backgroundColor: '#f8f9fa' }}>
          <div style={{ maxWidth: '1200px', margin: '0 auto' }}>
            <div style={{ textAlign: 'center', marginBottom: '4rem' }}>
              <h2 style={{
                fontSize: '2.5rem',
                fontWeight: 'bold',
                color: '#202124',
                marginBottom: '1rem'
              }}>
                Market Regime Detection
              </h2>
              <p style={{
                fontSize: '1.25rem',
                color: '#5f6368',
                maxWidth: '600px',
                margin: '0 auto'
              }}>
                AI-powered classification of market regimes based on volatility, correlation, and momentum indicators
              </p>
            </div>

            {/* Current Regime Summary */}
            <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(200px, 1fr))', gap: '1.5rem', marginBottom: '4rem' }}>
              <div style={{
                backgroundColor: 'white',
                padding: '2rem',
                borderRadius: '12px',
                textAlign: 'center',
                boxShadow: '0 4px 12px rgba(0,0,0,0.1)'
              }}>
                <TrendingUp size={48} style={{ color: '#388e3c', marginBottom: '1rem' }} />
                <div style={{ fontSize: '2rem', fontWeight: 'bold', color: '#388e3c', marginBottom: '0.5rem' }}>
                  Bull
                </div>
                <div style={{ fontSize: '1rem', fontWeight: '600', color: '#202124', marginBottom: '0.5rem' }}>
                  Current Regime
                </div>
                <div style={{ color: '#5f6368', fontSize: '0.875rem' }}>
                  40% Probability
                </div>
              </div>

              <div style={{
                backgroundColor: 'white',
                padding: '2rem',
                borderRadius: '12px',
                textAlign: 'center',
                boxShadow: '0 4px 12px rgba(0,0,0,0.1)'
              }}>
                <Activity size={48} style={{ color: '#1976d2', marginBottom: '1rem' }} />
                <div style={{ fontSize: '2rem', fontWeight: 'bold', color: '#1976d2', marginBottom: '0.5rem' }}>
                  12.8%
                </div>
                <div style={{ fontSize: '1rem', fontWeight: '600', color: '#202124', marginBottom: '0.5rem' }}>
                  Current Volatility
                </div>
                <div style={{ color: '#5f6368', fontSize: '0.875rem' }}>
                  21-day realized
                </div>
              </div>

              <div style={{
                backgroundColor: 'white',
                padding: '2rem',
                borderRadius: '12px',
                textAlign: 'center',
                boxShadow: '0 4px 12px rgba(0,0,0,0.1)'
              }}>
                <BarChart size={48} style={{ color: '#9c27b0', marginBottom: '1rem' }} />
                <div style={{ fontSize: '2rem', fontWeight: 'bold', color: '#9c27b0', marginBottom: '0.5rem' }}>
                  0.32
                </div>
                <div style={{ fontSize: '1rem', fontWeight: '600', color: '#202124', marginBottom: '0.5rem' }}>
                  Average Correlation
                </div>
                <div style={{ color: '#5f6368', fontSize: '0.875rem' }}>
                  Diversified
                </div>
              </div>
            </div>

            {/* Regime Analysis Cards */}
            <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(300px, 1fr))', gap: '2rem' }}>
              {marketRegimeData.map((regime, index) => (
                <div
                  key={index}
                  style={{
                    backgroundColor: 'white',
                    borderRadius: '16px',
                    overflow: 'hidden',
                    boxShadow: '0 8px 24px rgba(0,0,0,0.1)',
                    border: regime.regime === 'Bull' ? `3px solid ${regime.color}` : '1px solid #e8eaed'
                  }}
                >
                  <div style={{
                    padding: '2rem 2rem 1rem',
                    backgroundColor: regime.color,
                    color: 'white'
                  }}>
                    <h3 style={{ fontSize: '1.5rem', fontWeight: 'bold', marginBottom: '0.5rem' }}>
                      {regime.regime} Market
                    </h3>
                    <div style={{ fontSize: '2rem', fontWeight: 'bold', marginBottom: '0.5rem' }}>
                      {regime.probability}%
                    </div>
                    <p style={{ fontSize: '0.9rem', opacity: 0.9 }}>
                      {regime.description}
                    </p>
                  </div>

                  <div style={{ padding: '2rem' }}>
                    <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '1rem' }}>
                      <div>
                        <div style={{ fontSize: '0.75rem', color: '#5f6368', marginBottom: '0.25rem' }}>
                          Volatility
                        </div>
                        <div style={{ fontSize: '0.875rem', fontWeight: '600', color: '#202124' }}>
                          {regime.indicators.volatility}
                        </div>
                      </div>
                      <div>
                        <div style={{ fontSize: '0.75rem', color: '#5f6368', marginBottom: '0.25rem' }}>
                          Correlation
                        </div>
                        <div style={{ fontSize: '0.875rem', fontWeight: '600', color: '#202124' }}>
                          {regime.indicators.correlation}
                        </div>
                      </div>
                      <div>
                        <div style={{ fontSize: '0.75rem', color: '#5f6368', marginBottom: '0.25rem' }}>
                          Momentum
                        </div>
                        <div style={{ fontSize: '0.875rem', fontWeight: '600', color: '#202124' }}>
                          {regime.indicators.momentum}
                        </div>
                      </div>
                      <div>
                        <div style={{ fontSize: '0.75rem', color: '#5f6368', marginBottom: '0.25rem' }}>
                          Signal
                        </div>
                        <div style={{ fontSize: '0.875rem', fontWeight: '600', color: regime.color }}>
                          {regime.indicators.signal}
                        </div>
                      </div>
                    </div>
                  </div>
                </div>
              ))}
            </div>
          </div>
        </section>
      )}

      {/* Risk Scoring Section */}
      {activeTab === 'risk-scoring' && (
        <section className="animate-on-scroll" style={{ padding: '6rem 2rem', backgroundColor: '#f8f9fa' }}>
          <div style={{ maxWidth: '1200px', margin: '0 auto' }}>
            <div style={{ textAlign: 'center', marginBottom: '4rem' }}>
              <h2 style={{
                fontSize: '2.5rem',
                fontWeight: 'bold',
                color: '#202124',
                marginBottom: '1rem'
              }}>
                Risk Scoring Framework
              </h2>
              <p style={{
                fontSize: '1.25rem',
                color: '#5f6368',
                maxWidth: '600px',
                margin: '0 auto'
              }}>
                Composite risk score decomposition and component analysis
              </p>
            </div>

            {/* Overall Risk Score */}
            <div style={{
              backgroundColor: 'white',
              padding: '3rem',
              borderRadius: '16px',
              marginBottom: '3rem',
              textAlign: 'center',
              boxShadow: '0 8px 24px rgba(0,0,0,0.1)'
            }}>
              <h3 style={{ fontSize: '1.5rem', fontWeight: 'bold', color: '#202124', marginBottom: '2rem' }}>
                Overall Portfolio Risk Score
              </h3>
              <div style={{
                width: '200px',
                height: '200px',
                borderRadius: '50%',
                background: `conic-gradient(#388e3c 0deg ${69 * 3.6}deg, #e8eaed ${69 * 3.6}deg 360deg)`,
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center',
                margin: '0 auto',
                position: 'relative'
              }}>
                <div style={{
                  width: '150px',
                  height: '150px',
                  borderRadius: '50%',
                  backgroundColor: 'white',
                  display: 'flex',
                  flexDirection: 'column',
                  alignItems: 'center',
                  justifyContent: 'center'
                }}>
                  <div style={{ fontSize: '3rem', fontWeight: 'bold', color: '#388e3c' }}>69</div>
                  <div style={{ fontSize: '1rem', color: '#5f6368' }}>Risk Score</div>
                </div>
              </div>
              <p style={{ fontSize: '1.125rem', color: '#5f6368', marginTop: '1rem' }}>
                Moderate Risk - Weighted composite of 6 risk components
              </p>
            </div>

            {/* Risk Components */}
            <div style={{ display: 'grid', gridTemplateColumns: '1fr', gap: '1.5rem' }}>
              {riskScoringData.map((component, index) => (
                <div
                  key={index}
                  style={{
                    backgroundColor: 'white',
                    padding: '2rem',
                    borderRadius: '12px',
                    boxShadow: '0 4px 12px rgba(0,0,0,0.08)'
                  }}
                >
                  <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '1rem' }}>
                    <div>
                      <h4 style={{ fontSize: '1.25rem', fontWeight: 'bold', color: '#202124', marginBottom: '0.25rem' }}>
                        {component.component}
                      </h4>
                      <p style={{ fontSize: '0.875rem', color: '#5f6368', margin: 0 }}>
                        {component.description}
                      </p>
                    </div>
                    <div style={{ textAlign: 'right' }}>
                      <div style={{ fontSize: '1.5rem', fontWeight: 'bold', color: component.score >= 70 ? '#d32f2f' : component.score >= 50 ? '#ff9800' : '#388e3c' }}>
                        {component.score}
                      </div>
                      <div style={{ fontSize: '0.75rem', color: '#5f6368' }}>
                        Weight: {component.weight}%
                      </div>
                    </div>
                  </div>
                  
                  <div style={{
                    width: '100%',
                    height: '8px',
                    backgroundColor: '#e8eaed',
                    borderRadius: '4px',
                    overflow: 'hidden',
                    marginBottom: '1rem'
                  }}>
                    <div style={{
                      width: `${component.score}%`,
                      height: '100%',
                      backgroundColor: component.score >= 70 ? '#d32f2f' : component.score >= 50 ? '#ff9800' : '#388e3c',
                      transition: 'width 1s ease-in-out'
                    }} />
                  </div>

                  <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                    <span style={{
                      padding: '0.25rem 0.75rem',
                      borderRadius: '12px',
                      fontSize: '0.75rem',
                      fontWeight: '600',
                      backgroundColor: component.score >= 70 ? '#ffebee' : component.score >= 50 ? '#fff3e0' : '#e8f5e8',
                      color: component.score >= 70 ? '#d32f2f' : component.score >= 50 ? '#ff9800' : '#388e3c'
                    }}>
                      {component.status}
                    </span>
                    
                    <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
                      {component.trend === 'increasing' && <TrendingUp size={16} style={{ color: '#d32f2f' }} />}
                      {component.trend === 'decreasing' && <TrendingDown size={16} style={{ color: '#388e3c' }} />}
                      {component.trend === 'stable' && <Activity size={16} style={{ color: '#5f6368' }} />}
                      <span style={{ fontSize: '0.75rem', color: '#5f6368', textTransform: 'capitalize' }}>
                        {component.trend}
                      </span>
                    </div>
                  </div>
                </div>
              ))}
            </div>
          </div>
        </section>
      )}

      {/* Stress Testing Section */}
      {activeTab === 'stress-testing' && (
        <section className="animate-on-scroll" style={{ padding: '6rem 2rem', backgroundColor: '#f8f9fa' }}>
          <div style={{ maxWidth: '1400px', margin: '0 auto' }}>
            <div style={{ textAlign: 'center', marginBottom: '4rem' }}>
              <h2 style={{
                fontSize: '2.5rem',
                fontWeight: 'bold',
                color: '#202124',
                marginBottom: '1rem'
              }}>
                Historical Stress Testing
              </h2>
              <p style={{
                fontSize: '1.25rem',
                color: '#5f6368',
                maxWidth: '600px',
                margin: '0 auto'
              }}>
                Portfolio performance analysis under historical market stress scenarios
              </p>
            </div>

            {/* Stress Test Results Table */}
            <div style={{
              backgroundColor: 'white',
              borderRadius: '16px',
              overflow: 'hidden',
              boxShadow: '0 8px 24px rgba(0,0,0,0.1)'
            }}>
              <div style={{ padding: '2rem', borderBottom: '1px solid #e8eaed' }}>
                <h3 style={{ fontSize: '1.5rem', fontWeight: 'bold', color: '#202124' }}>
                  Historical Scenario Analysis
                </h3>
              </div>
              
              <div style={{ overflowX: 'auto' }}>
                <table style={{ width: '100%', borderCollapse: 'collapse' }}>
                  <thead>
                    <tr style={{ backgroundColor: '#f8f9fa' }}>
                      <th style={{ padding: '1rem', textAlign: 'left', borderBottom: '1px solid #e8eaed', fontSize: '0.875rem', fontWeight: '600', color: '#5f6368' }}>
                        Scenario
                      </th>
                      <th style={{ padding: '1rem', textAlign: 'center', borderBottom: '1px solid #e8eaed', fontSize: '0.875rem', fontWeight: '600', color: '#5f6368' }}>
                        Period
                      </th>
                      <th style={{ padding: '1rem', textAlign: 'right', borderBottom: '1px solid #e8eaed', fontSize: '0.875rem', fontWeight: '600', color: '#5f6368' }}>
                        Market Decline
                      </th>
                      <th style={{ padding: '1rem', textAlign: 'right', borderBottom: '1px solid #e8eaed', fontSize: '0.875rem', fontWeight: '600', color: '#5f6368' }}>
                        Portfolio Impact
                      </th>
                      <th style={{ padding: '1rem', textAlign: 'right', borderBottom: '1px solid #e8eaed', fontSize: '0.875rem', fontWeight: '600', color: '#5f6368' }}>
                        Max Drawdown
                      </th>
                      <th style={{ padding: '1rem', textAlign: 'right', borderBottom: '1px solid #e8eaed', fontSize: '0.875rem', fontWeight: '600', color: '#5f6368' }}>
                        Recovery Days
                      </th>
                      <th style={{ padding: '1rem', textAlign: 'center', borderBottom: '1px solid #e8eaed', fontSize: '0.875rem', fontWeight: '600', color: '#5f6368' }}>
                        Status
                      </th>
                    </tr>
                  </thead>
                  <tbody>
                    {stressTestingData.map((test, index) => (
                      <tr
                        key={index}
                        style={{ 
                          borderBottom: '1px solid #f0f0f0',
                          transition: 'background-color 0.2s'
                        }}
                        onMouseEnter={(e) => e.currentTarget.style.backgroundColor = '#f8f9fa'}
                        onMouseLeave={(e) => e.currentTarget.style.backgroundColor = 'transparent'}
                      >
                        <td style={{ padding: '1rem', fontSize: '0.875rem', fontWeight: '600', color: '#202124' }}>
                          {test.scenario}
                        </td>
                        <td style={{ padding: '1rem', textAlign: 'center', fontSize: '0.875rem', color: '#5f6368' }}>
                          {test.dateRange}
                        </td>
                        <td style={{ padding: '1rem', textAlign: 'right', fontSize: '0.875rem', fontWeight: '600', color: '#d32f2f' }}>
                          {test.marketDecline}%
                        </td>
                        <td style={{ padding: '1rem', textAlign: 'right', fontSize: '0.875rem', fontWeight: '600', color: '#ff9800' }}>
                          {test.portfolioImpact}%
                        </td>
                        <td style={{ padding: '1rem', textAlign: 'right', fontSize: '0.875rem', fontWeight: '600', color: '#d32f2f' }}>
                          {test.maxDrawdown}%
                        </td>
                        <td style={{ padding: '1rem', textAlign: 'right', fontSize: '0.875rem', color: '#5f6368' }}>
                          {test.recoveryDays}
                        </td>
                        <td style={{ padding: '1rem', textAlign: 'center' }}>
                          <span style={{
                            padding: '0.25rem 0.75rem',
                            borderRadius: '12px',
                            fontSize: '0.75rem',
                            fontWeight: '600',
                            backgroundColor: test.status === 'Passed' ? '#e8f5e8' : '#fff3e0',
                            color: test.status === 'Passed' ? '#388e3c' : '#ff9800'
                          }}>
                            {test.status}
                          </span>
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </div>
          </div>
        </section>
      )}

      {/* Volatility Forecasting Section */}
      {activeTab === 'volatility-forecast' && (
        <section className="animate-on-scroll" style={{ padding: '6rem 2rem', backgroundColor: '#f8f9fa' }}>
          <div style={{ maxWidth: '1200px', margin: '0 auto' }}>
            <div style={{ textAlign: 'center', marginBottom: '4rem' }}>
              <h2 style={{
                fontSize: '2.5rem',
                fontWeight: 'bold',
                color: '#202124',
                marginBottom: '1rem'
              }}>
                Volatility Forecasting Models
              </h2>
              <p style={{
                fontSize: '1.25rem',
                color: '#5f6368',
                maxWidth: '600px',
                margin: '0 auto'
              }}>
                Advanced GARCH, E-GARCH, and EWMA volatility forecasting models with accuracy metrics
              </p>
            </div>

            {/* Model Comparison Grid */}
            <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(300px, 1fr))', gap: '2rem' }}>
              {volatilityData.map((model, index) => (
                <div
                  key={index}
                  style={{
                    backgroundColor: 'white',
                    borderRadius: '16px',
                    padding: '2.5rem',
                    boxShadow: '0 8px 24px rgba(0,0,0,0.1)',
                    border: model.model === 'E-GARCH' ? '3px solid #9c27b0' : '1px solid #e8eaed'
                  }}
                >
                  <div style={{ marginBottom: '2rem' }}>
                    <h3 style={{ fontSize: '1.5rem', fontWeight: 'bold', color: '#202124', marginBottom: '0.5rem' }}>
                      {model.model}
                    </h3>
                    <p style={{ fontSize: '0.875rem', color: '#5f6368' }}>
                      {model.description}
                    </p>
                  </div>

                  <div style={{ marginBottom: '2rem' }}>
                    <div style={{ fontSize: '0.75rem', color: '#5f6368', marginBottom: '0.5rem' }}>
                      CURRENT FORECAST
                    </div>
                    <div style={{ fontSize: '2.5rem', fontWeight: 'bold', color: '#9c27b0', marginBottom: '0.25rem' }}>
                      {model.currentForecast}%
                    </div>
                    <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
                      <div style={{
                        padding: '0.25rem 0.5rem',
                        borderRadius: '8px',
                        fontSize: '0.75rem',
                        fontWeight: '600',
                        backgroundColor: model.accuracy >= 90 ? '#e8f5e8' : model.accuracy >= 85 ? '#fff3e0' : '#ffeaea',
                        color: model.accuracy >= 90 ? '#388e3c' : model.accuracy >= 85 ? '#ff9800' : '#d32f2f'
                      }}>
                        {model.accuracy}% Accuracy
                      </div>
                    </div>
                  </div>

                  <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '1rem' }}>
                    <div>
                      <div style={{ fontSize: '0.75rem', color: '#5f6368', marginBottom: '0.25rem' }}>
                        1 Week
                      </div>
                      <div style={{ fontSize: '1rem', fontWeight: '600', color: '#202124' }}>
                        {model.oneWeek}%
                      </div>
                    </div>
                    <div>
                      <div style={{ fontSize: '0.75rem', color: '#5f6368', marginBottom: '0.25rem' }}>
                        1 Month
                      </div>
                      <div style={{ fontSize: '1rem', fontWeight: '600', color: '#202124' }}>
                        {model.oneMonth}%
                      </div>
                    </div>
                    <div>
                      <div style={{ fontSize: '0.75rem', color: '#5f6368', marginBottom: '0.25rem' }}>
                        3 Months
                      </div>
                      <div style={{ fontSize: '1rem', fontWeight: '600', color: '#202124' }}>
                        {model.threeMonth}%
                      </div>
                    </div>
                    <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
                      {model.model === 'E-GARCH' && (
                        <span style={{
                          padding: '0.25rem 0.5rem',
                          borderRadius: '8px',
                          fontSize: '0.75rem',
                          fontWeight: '600',
                          backgroundColor: '#9c27b0',
                          color: 'white'
                        }}>
                          BEST
                        </span>
                      )}
                    </div>
                  </div>
                </div>
              ))}
            </div>
          </div>
        </section>
      )}

      {/* Placeholder sections for other tabs */}
      {activeTab === 'factor-analysis' && (
        <section className="animate-on-scroll" style={{ padding: '6rem 2rem', backgroundColor: '#f8f9fa' }}>
          <div style={{ maxWidth: '1200px', margin: '0 auto', textAlign: 'center' }}>
            <h2 style={{ fontSize: '2.5rem', fontWeight: 'bold', color: '#202124', marginBottom: '2rem' }}>
              Factor Exposure Analysis
            </h2>
            <p style={{ fontSize: '1.25rem', color: '#5f6368', marginBottom: '3rem' }}>
              Style factor decomposition and attribution analysis coming soon...
            </p>
            <div style={{ backgroundColor: 'white', padding: '4rem', borderRadius: '16px', boxShadow: '0 8px 24px rgba(0,0,0,0.1)' }}>
              <PieChart size={80} style={{ color: '#388e3c', marginBottom: '1rem' }} />
              <h3 style={{ fontSize: '1.5rem', fontWeight: 'bold', color: '#202124' }}>
                Advanced Factor Models
              </h3>
              <p style={{ color: '#5f6368' }}>
                Multi-factor risk models and style drift analysis
              </p>
            </div>
          </div>
        </section>
      )}

      {activeTab === 'portfolio-analytics' && (
        <section className="animate-on-scroll" style={{ padding: '6rem 2rem', backgroundColor: '#f8f9fa' }}>
          <div style={{ maxWidth: '1200px', margin: '0 auto', textAlign: 'center' }}>
            <h2 style={{ fontSize: '2.5rem', fontWeight: 'bold', color: '#202124', marginBottom: '2rem' }}>
              Portfolio Analytics
            </h2>
            <p style={{ fontSize: '1.25rem', color: '#5f6368', marginBottom: '3rem' }}>
              Comprehensive performance attribution and risk-adjusted metrics coming soon...
            </p>
            <div style={{ backgroundColor: 'white', padding: '4rem', borderRadius: '16px', boxShadow: '0 8px 24px rgba(0,0,0,0.1)' }}>
              <Award size={80} style={{ color: '#f57c00', marginBottom: '1rem' }} />
              <h3 style={{ fontSize: '1.5rem', fontWeight: 'bold', color: '#202124' }}>
                Performance Analytics
              </h3>
              <p style={{ color: '#5f6368' }}>
                Sharpe ratio, Sortino ratio, and risk-adjusted performance metrics
              </p>
            </div>
          </div>
        </section>
      )}

              <LandingFooter />
    </div>
  );
};

export default ResearchInsightsPage;
