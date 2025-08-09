import React from "react"
import { useNavigate } from 'react-router-dom';
import { Linkedin, Facebook, Instagram, Youtube, Activity, AlertTriangle, Target, PieChart, Gauge, BarChart, TrendingDown, BarChart3 } from "lucide-react"
import Navbar from '../components/Navbar';
import Footer from '../components/Footer';
import './RiskSolutionsPage.css';

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

const RiskSolutionsPage: React.FC = () => {
  const navigate = useNavigate();
  const [currentSlide, setCurrentSlide] = React.useState(0);
  const heroImage = findImage(['image_6_nyc', '6_nyc', 'nyc']);

  const riskComponents = [
    {
      id: 'portfolio-summary',
      title: 'Portfolio Risk Dashboard',
      subtitle: 'Comprehensive Risk Overview',
      description: 'Central dashboard displaying overall risk score (0-100), largest positions analysis, portfolio volatility metrics, and real-time risk alerts for immediate portfolio health monitoring.',
      icon: Gauge,
      color: '#1976d2'
    },
    {
      id: 'realized-risk',
      title: 'Realized Risk Analysis',
      subtitle: 'Historical Performance Metrics',
      description: 'Historical risk analysis including rolling volatility measures, maximum drawdown analysis, position correlation matrices, and risk-adjusted performance (Sharpe, Sortino ratios).',
      icon: TrendingDown,
      color: '#d32f2f'
    },
    {
      id: 'forecast-risk',
      title: 'Forecast Risk Models',
      subtitle: 'EWMA, GARCH & E-GARCH Models',
      description: 'Multiple volatility forecasting models (5D, 30D, 200D EWMA, GARCH, E-GARCH) with model comparison, forecast vs realized tracking, and risk contribution analysis.',
      icon: BarChart,
      color: '#388e3c'
    },
    {
      id: 'concentration-risk',
      title: 'Concentration Analysis',
      subtitle: 'HHI & Diversification Metrics',
      description: 'Herfindahl-Hirschman Index concentration scoring, top-N position weights analysis, effective number of positions, and sector/market-cap diversification assessment.',
      icon: PieChart,
      color: '#f57c00'
    },
    {
      id: 'stress-testing',
      title: 'Historical Stress Testing',
      subtitle: 'Crisis Scenario Analysis',
      description: 'Portfolio stress testing against historical crises: 2018 Q4 Volatility, 2020 COVID Crash, 2020 Recovery, 2022 Inflation Shock, and 2015 China Devaluation scenarios.',
      icon: AlertTriangle,
      color: '#7b1fa2'
    },
    {
      id: 'liquidity-risk',
      title: 'Liquidity Risk Assessment',
      subtitle: 'ADV & Bid-Ask Analysis',
      description: 'Average Daily Volume analysis, bid-ask spread assessment, liquidity score calculation, volume-based portfolio categorization, and estimated liquidation timeframes.',
      icon: Activity,
      color: '#1976d2'
    },
    {
      id: 'factor-exposure',
      title: 'Factor Exposure Analysis',
      subtitle: 'Market Beta & Style Factors',
      description: 'Market beta calculation, factor exposures to momentum (MTUM), size (IWM), value (VLUE), and quality (QUAL) factors with rolling R² explanatory power tracking.',
      icon: Target,
      color: '#388e3c'
    },
    {
      id: 'regime-detection',
      title: 'Market Regime Detection',
      subtitle: 'Crisis, Bull, Cautious, Neutral',
      description: 'Real-time market regime classification based on volatility thresholds, correlation levels, and momentum indicators with adaptive risk parameters.',
      icon: BarChart3,
      color: '#f57c00'
    }
  ];

  // Auto-advance slideshow
  React.useEffect(() => {
    const interval = setInterval(() => {
      setCurrentSlide((prev) => (prev + 1) % riskComponents.length);
    }, 8000); // Change slide every 8 seconds
    return () => clearInterval(interval);
  }, [riskComponents.length]);

  // Intersection Observer for animations
  React.useEffect(() => {
    const observerOptions = {
      threshold: 0.1,
      rootMargin: '0px 0px -50px 0px'
    }

    const observer = new IntersectionObserver((entries) => {
      entries.forEach(entry => {
        if (entry.isIntersecting) {
          const target = entry.target as HTMLElement
          target.style.opacity = '1'
          target.style.transform = 'translateY(0)'
        }
      })
    }, observerOptions)

    // Observe all animated elements
    const animatedElements = document.querySelectorAll('.animate-on-scroll')
    animatedElements.forEach(el => {
      const element = el as HTMLElement
      element.style.opacity = '0'
      element.style.transform = 'translateY(30px)'
      element.style.transition = 'opacity 0.6s ease-out, transform 0.6s ease-out'
      observer.observe(el)
    })

    return () => observer.disconnect()
  }, [])

  return (
    <div className="risk-solutions-page">
      <Navbar
        onClientLogin={() => {
          navigate('/login');
        }}
        onBrandClick={() => {
          navigate('/');
        }}
        onNavigate={(page: string) => {
          if (page === 'who-we-are') {
            navigate('/who-we-are');
          } else if (page === 'research-insights') {
            navigate('/research-insights');
          } else if (page === 'risk-solutions') {
            navigate('/risk-solutions');
          } else if (page === 'careers') {
            navigate('/careers');
          }
        }}
      />

      {/* Hero Section */}
      <section style={{ 
        position: 'relative',
        height: '70vh',
        backgroundImage: heroImage 
          ? `linear-gradient(rgba(0, 0, 0, 0.5), rgba(0, 0, 0, 0.5)), url(${heroImage})`
          : 'linear-gradient(rgba(0, 0, 0, 0.5), rgba(0, 0, 0, 0.5)), url(https://images.unsplash.com/photo-1551288049-bebda4e38f71?ixlib=rb-4.0.3&ixid=M3wxMjA3fDB8MHxwaG90by1wYWdlfHx8fGVufDB8fHx8fA%3D%3D&auto=format&fit=crop&w=1920&q=80)',
        backgroundSize: 'cover',
        backgroundPosition: 'center',
        width: '100vw',
        marginLeft: 'calc(-50vw + 50%)',
        marginRight: 'calc(-50vw + 50%)',
        marginTop: '70px'
      }}>
        <div className="container" style={{ 
          position: 'relative', 
          zIndex: 2, 
          height: '100%', 
          display: 'flex', 
          alignItems: 'center',
          justifyContent: 'center'
        }}>
          <div style={{ 
            maxWidth: '1024px',
            textAlign: 'center',
            width: '100%'
          }}>
            <h1 
              style={{ 
                fontSize: '3.5rem', 
                fontWeight: 'bold', 
                color: 'white', 
                lineHeight: '1.2', 
                marginBottom: '1.5rem',
                textShadow: '0 2px 4px rgba(0,0,0,0.3)',
                textAlign: 'center'
              }}
            >
              Quantitative Risk Management
            </h1>
            <p 
              style={{ 
                fontSize: '1.5rem', 
                color: 'rgba(255, 255, 255, 0.9)', 
                marginBottom: '2rem', 
                maxWidth: '768px',
                margin: '0 auto 2rem auto',
                textShadow: '0 1px 2px rgba(0,0,0,0.3)',
                textAlign: 'center'
              }}
            >
              Advanced portfolio risk analytics with real-time monitoring, volatility forecasting, and comprehensive stress testing
            </p>
          </div>
        </div>
      </section>

      {/* Risk Solutions Slideshow */}
      <section style={{ 
        backgroundColor: '#ffffff', 
        padding: '5rem 0',
        width: '100%'
      }}>
        <div className="container">
          {/* Section Header */}
          <div style={{ textAlign: 'center', marginBottom: '3rem' }}>
            <h2 style={{ 
              fontSize: '2.5rem', 
              fontWeight: 'bold', 
              color: '#202124', 
              marginBottom: '1rem' 
            }}>
              Our Risk Solutions
            </h2>
            <p style={{ 
              fontSize: '1.125rem', 
              color: '#5f6368', 
              maxWidth: '600px', 
              margin: '0 auto' 
            }}>
              Comprehensive portfolio risk analysis tools for institutional investors
            </p>
          </div>

          {/* Slideshow Container with External Arrows */}
          <div style={{ 
            position: 'relative',
            maxWidth: '900px',
            margin: '0 auto',
            display: 'flex',
            alignItems: 'center',
            gap: '2rem'
          }}>
            {/* Left Arrow */}
            <button
              onClick={() => setCurrentSlide((prev) => prev === 0 ? riskComponents.length - 1 : prev - 1)}
              style={{
                backgroundColor: '#1976d2',
                border: 'none',
                width: '56px',
                height: '56px',
                borderRadius: '50%',
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center',
                cursor: 'pointer',
                boxShadow: '0 4px 12px rgba(25, 118, 210, 0.3)',
                fontSize: '24px',
                color: 'white',
                transition: 'all 0.3s ease',
                flexShrink: 0
              }}
              onMouseEnter={(e) => {
                e.currentTarget.style.backgroundColor = '#1565c0';
                e.currentTarget.style.transform = 'scale(1.1)';
              }}
              onMouseLeave={(e) => {
                e.currentTarget.style.backgroundColor = '#1976d2';
                e.currentTarget.style.transform = 'scale(1)';
              }}
            >
              &#8249;
            </button>

            {/* Slideshow Content */}
            <div style={{ 
              overflow: 'hidden',
              borderRadius: '16px',
              boxShadow: '0 8px 32px rgba(0, 0, 0, 0.1)',
              flex: 1
            }}>
              {/* Slides */}
              <div style={{
                display: 'flex',
                transform: `translateX(-${currentSlide * 100}%)`,
                transition: 'transform 0.6s ease-in-out'
              }}>
                {riskComponents.map((component, index) => (
                  <div
                    key={component.id}
                    style={{
                      minWidth: '100%',
                      backgroundColor: '#ffffff',
                      padding: '3rem',
                      display: 'flex',
                      alignItems: 'center',
                      gap: '2rem'
                    }}
                  >
                    {/* Icon */}
                    <div style={{
                      width: '80px',
                      height: '80px',
                      backgroundColor: component.color,
                      borderRadius: '16px',
                      display: 'flex',
                      alignItems: 'center',
                      justifyContent: 'center',
                      flexShrink: 0
                    }}>
                      <component.icon size={36} color="white" />
                    </div>

                    {/* Content */}
                    <div style={{ flex: 1 }}>
                      <h3 style={{ 
                        fontSize: '2rem', 
                        fontWeight: 'bold', 
                        color: '#202124',
                        marginBottom: '0.5rem'
                      }}>
                        {component.title}
                      </h3>
                      <p style={{ 
                        fontSize: '1rem', 
                        color: component.color,
                        fontWeight: '600',
                        marginBottom: '1rem'
                      }}>
                        {component.subtitle}
                      </p>
                      <p style={{ 
                        fontSize: '1.125rem', 
                        color: '#5f6368', 
                        lineHeight: '1.6',
                        margin: 0
                      }}>
                        {component.description}
                      </p>
                    </div>
                  </div>
                ))}
              </div>
            </div>
            
            {/* Right Arrow */}
            <button
              onClick={() => setCurrentSlide((prev) => (prev + 1) % riskComponents.length)}
              style={{
                backgroundColor: '#1976d2',
                border: 'none',
                width: '56px',
                height: '56px',
                borderRadius: '50%',
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center',
                cursor: 'pointer',
                boxShadow: '0 4px 12px rgba(25, 118, 210, 0.3)',
                fontSize: '24px',
                color: 'white',
                transition: 'all 0.3s ease',
                flexShrink: 0
              }}
              onMouseEnter={(e) => {
                e.currentTarget.style.backgroundColor = '#1565c0';
                e.currentTarget.style.transform = 'scale(1.1)';
              }}
              onMouseLeave={(e) => {
                e.currentTarget.style.backgroundColor = '#1976d2';
                e.currentTarget.style.transform = 'scale(1)';
              }}
            >
              &#8250;
            </button>
          </div>

          {/* Slide Indicators */}
          <div style={{
            display: 'flex',
            justifyContent: 'center',
            gap: '0.75rem',
            marginTop: '2rem'
          }}>
            {riskComponents.map((_, index) => (
              <button
                key={index}
                onClick={() => setCurrentSlide(index)}
                style={{
                  width: '12px',
                  height: '12px',
                  borderRadius: '50%',
                  border: 'none',
                  backgroundColor: currentSlide === index ? '#1976d2' : '#e0e0e0',
                  cursor: 'pointer',
                  transition: 'background-color 0.3s'
                }}
              />
            ))}
          </div>

          {/* Progress Bar */}
          <div style={{
            width: '100%',
            height: '4px',
            backgroundColor: '#e0e0e0',
            borderRadius: '2px',
            marginTop: '2rem',
            overflow: 'hidden'
          }}>
            <div style={{
              width: `${((currentSlide + 1) / riskComponents.length) * 100}%`,
              height: '100%',
              backgroundColor: '#1976d2',
              borderRadius: '2px',
              transition: 'width 0.6s ease-in-out'
            }} />
          </div>
        </div>
      </section>

      {/* Advanced Analytics Section */}
      <section style={{ 
        backgroundColor: '#f8f9fa', 
        padding: '5rem 0',
        width: '100%'
      }}>
        <div className="container">
          <div style={{ 
            display: 'grid', 
            gridTemplateColumns: '1fr 1fr', 
            gap: '4rem',
            alignItems: 'center'
          }}>
            <div className="animate-on-scroll">
              <h2 style={{ 
                fontSize: '3rem', 
                fontWeight: 'bold', 
                color: '#202124',
                lineHeight: '1.1',
                marginBottom: '2rem'
              }}>
                Quantitative Risk<br />Framework
              </h2>
              <div style={{ fontSize: '1.125rem', lineHeight: '1.7', color: '#202124' }}>
                <p style={{ marginBottom: '1.5rem' }}>
                  Z-Alpha's risk management platform integrates multiple quantitative models including EWMA, GARCH, and E-GARCH volatility forecasting, providing comprehensive portfolio risk assessment and monitoring.
                </p>
                <p style={{ marginBottom: '1.5rem' }}>
                  Our system processes real-time market data to deliver risk scoring (0-100 scale), concentration analysis using Herfindahl-Hirschman Index, and stress testing against historical market crises.
                </p>
                <p>
                  Factor exposure analysis covers market beta, momentum (MTUM), size (IWM), value (VLUE), and quality (QUAL) factors with automated regime detection classifying market conditions as Crisis, Bull, Cautious, or Neutral.
                </p>
              </div>
            </div>

            <div
              className="animate-on-scroll"
              style={{
                backgroundImage: 'url(https://images.unsplash.com/photo-1551288049-bebda4e38f71?ixlib=rb-4.0.3&ixid=M3wxMjA3fDB8MHxwaG90by1wYWdlfHx8fGVufDB8fHx8fA%3D%3D&auto=format&fit=crop&w=1920&q=80)',
                backgroundSize: 'cover',
                backgroundPosition: 'center',
                height: '400px',
                borderRadius: '12px'
              }}
            />
          </div>
        </div>
      </section>

      {/* Implementation Section */}
      <section style={{ 
        backgroundColor: '#171717', 
        color: 'white', 
        padding: '5rem 0',
        width: '100%'
      }}>
        <div className="container">
          <div style={{ 
            display: 'grid', 
            gridTemplateColumns: '1fr 1fr', 
            gap: '4rem',
            alignItems: 'center'
          }}>
            <div className="animate-on-scroll">
              <h2 style={{ 
                fontSize: '3rem', 
                fontWeight: 'bold', 
                color: 'white',
                marginBottom: '2rem'
              }}>
                Real-Time Risk<br />Monitoring
              </h2>
              <p style={{ 
                fontSize: '1.125rem', 
                color: 'rgba(255, 255, 255, 0.9)', 
                lineHeight: '1.6',
                marginBottom: '1.5rem'
              }}>
                Our platform provides continuous portfolio monitoring with integrated IBKR data connectivity, real-time risk score calculations, and automated alerting for concentration, liquidity, and volatility thresholds.
              </p>
              <p style={{ 
                fontSize: '1.125rem', 
                color: 'rgba(255, 255, 255, 0.9)', 
                lineHeight: '1.6'
              }}>
                The dashboard delivers instant access to risk metrics, historical stress test results, and forecast model performance with intuitive visualizations for immediate decision-making support.
              </p>
            </div>

            <div
              className="animate-on-scroll"
              style={{
                backgroundImage: 'url(https://images.unsplash.com/photo-1551288049-bebda4e38f71?ixlib=rb-4.0.3&ixid=M3wxMjA3fDB8MHxwaG90by1wYWdlfHx8fGVufDB8fHx8fA%3D%3D&auto=format&fit=crop&w=1920&q=80)',
                backgroundSize: 'cover',
                backgroundPosition: 'center',
                height: '400px',
                borderRadius: '8px'
              }}
            />
          </div>
        </div>
      </section>

      <Footer />
    </div>
  )
}

export default RiskSolutionsPage
