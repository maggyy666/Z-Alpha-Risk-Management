import React, { useEffect, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import Navbar from '../components/Navbar';
import LandingFooter from '../components/LandingFooter';
import './WhoWeArePage.css';
// Staff images (provided in src/staff)
import billImg from '../staff/bill.jpg';
import madoffImg from '../staff/madoff.webp';
import rajImg from '../staff/American-investor-Raj-Rajaratnam-2011.webp';
import { Shield, Activity, Radar, Gauge, Zap, Brain, BarChart2, LineChart } from 'lucide-react';

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

// Leadership team (parody/fictional board inspired by WSB and real scandals)
const leadershipTeam = [
  // Move real scandal figures to the beginning
  {
    id: 1,
    name: "Bernie Madoff",
    position: "Chief Ponzi Architect",
    description: "Advises on Circular Revenue Recognition and client statement design. Chairs the Illusionary Alpha Committee, responsible for making Sharpe ratios visually appealing.",
    image: madoffImg
  },
  {
    id: 2,
    name: "Bill Hwang",
    position: "Chief Derivative Manipulator",
    description: "Oversees the Total Return Swaps & Hidden Exposure Division. Leads the firm's Prime Broker Distraction Strategy, ensuring concentration risk is 'out of sight, out of mind.'",
    image: billImg
  },
  {
    id: 3,
    name: "Raj Rajaratnam",
    position: "Head of Insider Intelligence",
    description: "Runs the Alternative Data & Lunch Networking Desk. Provides deep domain expertise in Pre‑Earnings Whisper Acquisition and Material Non‑Public Scenario Planning.",
    image: rajImg
  },
  // WSB legends
  {
    id: 4,
    name: "u/DeepFuckingValue (Roaring Kitty)",
    position: "Chief Meme Strategist",
    description: "Responsible for shaping market sentiment through coordinated meme deployment and tactical conviction trades. Oversees the Diamond Hands Research Desk and runs the firm's weekly YOLO Scenario Analysis calls.",
    image: null
  },
  {
    id: 5,
    name: "u/1R0NYMAN",
    position: "Director of 'Risk‑Free' Risk Management",
    description: "Leads the Box Spread Innovation Lab, developing exotic structures that 'statistically can't go tits up' (but still do). Maintains a proprietary Ruin Probability <100% framework.",
    image: null
  },
  {
    id: 6,
    name: "u/ControlTheNarrative",
    position: "Chief Leverage Exploits Officer",
    description: "Architect of the Infinite Buying Power Initiative, focusing on discovering, replicating and operationalizing broker loopholes. Heads the Internal Leverage Policy Committee — motto: 'Margin is just a suggestion.'",
    image: null
  },
  {
    id: 7,
    name: "u/fscomeau",
    position: "Head of Apple Drama Trades",
    description: "Runs the Earnings Event Emotional Simulation Unit. Specializes in all‑in single‑ticker positions, live‑streamed to the Investment Committee for morale purposes. Tracks 'Tears per Trade' as a core KPI.",
    image: null
  },
  {
    id: 8,
    name: "XIV Massacre Trader",
    position: "VP, Reverse Volatility Catastrophes",
    description: "Designs stress tests for trades that implode before the market close. Founder of the Inverse Inverse Volatility Fund and keeper of the firm's Liquidity Vaporization Protocol.",
    image: null
  }
];

const WhoWeArePage: React.FC = () => {
  const navigate = useNavigate();
  const heroImage = findImage(['image_5_nyc', '5_nyc', 'nyc']);

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

  // Ensure all leadership cards become visible even if observer misses some
  useEffect(() => {
    const timer = window.setTimeout(() => {
      document.querySelectorAll('.leadership-card').forEach((el) => {
        el.classList.add('animate-in');
      });
    }, 200);
    return () => window.clearTimeout(timer);
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

  return (
    <div className="who-we-are-page">
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
          ? `linear-gradient(rgba(0,0,0,0.35), rgba(0,0,0,0.35)), url(${heroImage})`
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
            Who We Are
          </h1>
          <p className="animate-on-scroll" style={{
            fontSize: '1.5rem',
            opacity: 0.9,
            lineHeight: '1.6',
            fontWeight: '300'
          }}>
            We're a team of quantitative analysts, risk engineers and technologists, delivering cutting-edge portfolio risk management solutions.
          </p>
        </div>
      </section>

      {/* Pioneering Risk Intelligence (modern layout) */}
      <section className="animate-on-scroll pri-section">
        <div className="pri-wrap">
          <header className="pri-header">
            <h2>Pioneering Risk Intelligence</h2>
            <p>
              Institutional-grade models, regime-aware analytics and real-time risk pipelines — built to convert uncertainty into disciplined decisions.
            </p>
          </header>

          <div className="pri-grid" style={{ contain: 'layout', gridTemplateColumns: '1fr' }}>
            {/* Left: Feature cards */}
            <div className="pri-col pri-features">
              <div className="pri-feature">
                <div className="pri-icon" aria-hidden="true"><Shield size={22} /></div>
                <div>
                  <div className="pri-title">Multi-Model Volatility</div>
                  <div className="pri-desc">EWMA, GARCH, E-GARCH and realized measures blended for robust regime coverage.</div>
                  <div className="pri-tags">
                    <span className="pri-chip">EWMA</span>
                    <span className="pri-chip">GARCH</span>
                    <span className="pri-chip">Realized</span>
                  </div>
                </div>
              </div>
              <div className="pri-feature">
                <div className="pri-icon" aria-hidden="true"><Radar size={22} /></div>
                <div>
                  <div className="pri-title">Market Regime Detection</div>
                  <div className="pri-desc">Crisis, Bull, Cautious and Neutral states inferred from cross-asset structure.</div>
                  <div className="pri-tags">
                    <span className="pri-chip">Regime</span>
                    <span className="pri-chip">Correlation</span>
                    <span className="pri-chip">Beta</span>
                  </div>
                </div>
              </div>
              <div className="pri-feature">
                <div className="pri-icon" aria-hidden="true"><Activity size={22} /></div>
                <div>
                  <div className="pri-title">Historical Stress Engine</div>
                  <div className="pri-desc">Scenario replay across crises with CVaR-aware hedging guidance.</div>
                  <div className="pri-tags">
                    <span className="pri-chip">Scenarios</span>
                    <span className="pri-chip">CVaR</span>
                    <span className="pri-chip">Hedges</span>
                  </div>
                </div>
              </div>
              {/* (condensed) removed one feature to reduce density */}
            </div>

            {/* Right column removed to keep max 3 elements total */}
          </div>
        </div>
      </section>

      {/* Culture Section */}
      <section className="animate-on-scroll" style={{
        padding: '6rem 2rem',
        backgroundColor: '#f8f9fa'
      }}>
        <div style={{ maxWidth: '1200px', margin: '0 auto', textAlign: 'center' }}>
          <h2 style={{
            fontSize: '3rem',
            fontWeight: 'bold',
            color: '#202124',
            marginBottom: '2rem'
          }}>
            Data-Driven Excellence
          </h2>
          <p style={{
            fontSize: '1.5rem',
            color: '#5f6368',
            lineHeight: '1.7',
            maxWidth: '800px',
            margin: '0 auto'
          }}>
            Our culture emphasizes rigorous analysis, continuous innovation, and collaborative problem-solving in the pursuit of superior risk management solutions.
          </p>
        </div>
      </section>

      {/* Two Firms Section */}
      <section className="animate-on-scroll" style={{
        padding: '6rem 2rem',
        backgroundColor: '#ffffff'
      }}>
        <div style={{ maxWidth: '1200px', margin: '0 auto' }}>
          <h2 style={{
            fontSize: '3rem',
            fontWeight: 'bold',
            color: '#202124',
            marginBottom: '2rem',
            textAlign: 'center'
          }}>
            Two Divisions: Z-Alpha and Z-Alpha Securities
          </h2>
          <div style={{
            display: 'grid',
            gridTemplateColumns: 'repeat(auto-fit, minmax(400px, 1fr))',
            gap: '4rem',
            marginTop: '4rem'
          }}>
            <div style={{
              padding: '3rem',
              borderRadius: '16px',
              backgroundColor: '#f8f9fa',
              border: '1px solid #e8eaed'
            }}>
              <h3 style={{
                fontSize: '2rem',
                fontWeight: 'bold',
                color: '#1976d2',
                marginBottom: '1.5rem'
              }}>
                Z-Alpha Risk Management
              </h3>
              <p style={{
                fontSize: '1.25rem',
                color: '#5f6368',
                lineHeight: '1.7',
                marginBottom: '2rem'
              }}>
                Our flagship platform providing comprehensive portfolio risk analytics, volatility forecasting, and concentration analysis for institutional investors and hedge funds.
              </p>
              <button style={{
                backgroundColor: '#1976d2',
                color: 'white',
                border: 'none',
                padding: '0.75rem 2rem',
                borderRadius: '8px',
                fontSize: '1rem',
                fontWeight: '600',
                cursor: 'pointer',
                transition: 'all 0.3s ease'
              }}>
                Explore Platform
              </button>
            </div>
            <div style={{
              padding: '3rem',
              borderRadius: '16px',
              backgroundColor: '#f8f9fa',
              border: '1px solid #e8eaed'
            }}>
              <h3 style={{
                fontSize: '2rem',
                fontWeight: 'bold',
                color: '#1976d2',
                marginBottom: '1.5rem'
              }}>
                Z-Alpha Securities
              </h3>
              <p style={{
                fontSize: '1.25rem',
                color: '#5f6368',
                lineHeight: '1.7',
                marginBottom: '2rem'
              }}>
                Advanced market intelligence and execution services, leveraging our risk models to provide optimized trading strategies and liquidity solutions for professional traders.
              </p>
              <button style={{
                backgroundColor: '#1976d2',
                color: 'white',
                border: 'none',
                padding: '0.75rem 2rem',
                borderRadius: '8px',
                fontSize: '1rem',
                fontWeight: '600',
                cursor: 'pointer',
                transition: 'all 0.3s ease'
              }}>
                Explore Securities
              </button>
            </div>
          </div>
        </div>
      </section>

      {/* Leadership Intro */}
      <section className="animate-on-scroll" style={{
        padding: '6rem 2rem 3rem',
        backgroundColor: '#f8f9fa'
      }}>
        <div style={{ maxWidth: '1200px', margin: '0 auto', textAlign: 'center' }}>
          <h2 style={{
            fontSize: '3rem',
            fontWeight: 'bold',
            color: '#202124',
            marginBottom: '2rem'
          }}>
            Led by Risk Management Experts
          </h2>
          <p style={{
            fontSize: '1.5rem',
            color: '#5f6368',
            lineHeight: '1.7',
            maxWidth: '800px',
            margin: '0 auto'
          }}>
            Our leadership team combines decades of experience in quantitative finance, risk analytics, and financial technology to deliver cutting-edge solutions.
          </p>
        </div>
      </section>

      {/* Leadership Team Section */}
      <section className="animate-on-scroll leadership-section" style={{
        padding: '3rem 2rem 6rem',
        backgroundColor: '#f8f9fa'
      }}>
        <div style={{ maxWidth: '1400px', margin: '0 auto' }}>
          <div className="leadership-grid" style={{
            display: 'grid',
            gridTemplateColumns: 'repeat(auto-fit, minmax(350px, 1fr))',
            gap: '3rem',
            position: 'relative'
          }}>
            {/* Winding path SVG overlay */}
            <div className="leadership-path" style={{
              position: 'absolute',
              top: 0,
              left: 0,
              right: 0,
              bottom: 0,
              pointerEvents: 'none',
              zIndex: 1
            }}>
              <svg 
                width="100%" 
                height="100%" 
                style={{ position: 'absolute' }}
                viewBox="0 0 1200 800"
                preserveAspectRatio="xMidYMid slice"
              >
                <defs>
                  <linearGradient id="pathGradient" x1="0%" y1="0%" x2="100%" y2="100%">
                    <stop offset="0%" stopColor="#1976d2" stopOpacity="0.3" />
                    <stop offset="50%" stopColor="#2196f3" stopOpacity="0.2" />
                    <stop offset="100%" stopColor="#1976d2" stopOpacity="0.3" />
                  </linearGradient>
                </defs>
                <path
                  d="M 100 100 Q 400 50 600 200 T 1100 300 Q 800 450 500 500 T 200 700"
                  stroke="url(#pathGradient)"
                  strokeWidth="4"
                  fill="none"
                  strokeDasharray="10,5"
                  className="winding-path"
                />
              </svg>
            </div>

            {leadershipTeam.map((leader, index) => (
              <div
                key={leader.id}
                className="leadership-card animate-on-scroll"
                style={{
                  backgroundColor: '#ffffff',
                  borderRadius: '20px',
                  padding: '2.5rem',
                  boxShadow: '0 8px 32px rgba(0, 0, 0, 0.08)',
                  border: '1px solid #e8eaed',
                  textAlign: 'center',
                  position: 'relative',
                  zIndex: 2,
                  transition: 'all 0.3s ease',
                  cursor: 'pointer'
                }}
                onMouseEnter={(e) => {
                  e.currentTarget.style.transform = 'translateY(-8px)';
                  e.currentTarget.style.boxShadow = '0 16px 48px rgba(0, 0, 0, 0.12)';
                }}
                onMouseLeave={(e) => {
                  e.currentTarget.style.transform = 'translateY(0)';
                  e.currentTarget.style.boxShadow = '0 8px 32px rgba(0, 0, 0, 0.08)';
                }}
              >
                {/* Placeholder for photo */}
                <div style={{
                  width: '120px',
                  height: '120px',
                  borderRadius: '50%',
                  backgroundColor: '#e8eaed',
                  margin: '0 auto 1.5rem',
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'center',
                  fontSize: '2rem',
                  color: '#5f6368',
                  border: '4px solid #1976d2'
                }}>
                  {leader.image ? (
                    <img 
                      src={leader.image} 
                      alt={leader.name}
                      style={{
                        width: '100%',
                        height: '100%',
                        borderRadius: '50%',
                        objectFit: 'cover'
                      }}
                    />
                  ) : (
                    ''
                  )}
                </div>

                <h3 style={{
                  fontSize: '1.5rem',
                  fontWeight: 'bold',
                  color: '#202124',
                  marginBottom: '0.5rem'
                }}>
                  {leader.name}
                </h3>

                <p style={{
                  fontSize: '1rem',
                  fontWeight: '600',
                  color: '#1976d2',
                  marginBottom: '1rem'
                }}>
                  {leader.position}
                </p>

                <p style={{
                  fontSize: '1rem',
                  color: '#5f6368',
                  lineHeight: '1.6',
                  margin: 0
                }}>
                  {leader.description}
                </p>
              </div>
            ))}
          </div>
        </div>
      </section>

      <LandingFooter />
    </div>
  );
};

export default WhoWeArePage;
