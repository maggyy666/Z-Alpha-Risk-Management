import React, { useEffect, useRef, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import './LandingPage.css';
import Navbar from '../components/Navbar';
import Footer from '../components/Footer';

import slide1 from '../images/image_1_nyc.jpg';
import slide2 from '../images/image_3_stock.avif';
import slide3 from '../images/image_2_nyc.jpg';
import slide4 from '../images/image_4_stock.jpg';
import { ChevronRight, ArrowRight, TrendingUp, Shield, Users, Award } from 'lucide-react';

const LandingPage: React.FC = () => {
  const navigate = useNavigate();
  const aboutRef = useRef<HTMLElement>(null);
  const servicesRef = useRef<HTMLElement>(null);
  const statsRef = useRef<HTMLElement>(null);
  const teamRef = useRef<HTMLElement>(null);
  // Internship slideshow state
  const [internshipSlide, setInternshipSlide] = useState<number>(0);

  // Internship items
  const internshipItems = [
    { title: 'Quantitative Research', desc: 'Work on cutting-edge risk models and market analysis' },
    { title: 'Software Engineering', desc: 'Develop high-performance trading systems and analytics tools' },
    { title: 'Data Science', desc: 'Apply machine learning to financial data and market prediction' },
    { title: 'Risk Management', desc: 'Learn portfolio risk assessment and regulatory compliance' },
    { title: 'Trading Operations', desc: 'Experience real-time market monitoring and execution' },
    { title: 'Technology Infrastructure', desc: 'Build and maintain critical trading infrastructure' },
    { title: 'Compliance & Legal', desc: 'Understand regulatory frameworks and compliance requirements' },
    { title: 'Business Development', desc: 'Support client relationships and business growth initiatives' },
    { title: 'Operations & Analytics', desc: 'Optimize trading operations and performance analytics' },
    { title: 'Research & Strategy', desc: 'Contribute to investment strategy and market research' }
  ];

  // Helper: load images by fuzzy hints (filenames are added later)
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

  // Roadmap events (images optional; will be added later)
  const roadmapItems: Array<{
    title: string;
    headline: string;
    cvar: string;
    outcome: string;
    positioning: string;
    image?: string | null;
  }> = [
    {
      title: '9/11 Attacks',
      headline: 'Sep 2001 — Coordinated terrorist attacks; aviation grounded; systemic credit & liquidity strain; volatility regime shift',
      cvar: 'CVAR Impact: –$280M projected at the open',
      outcome: 'Actual Outcome: –$8M after rapid rotations',
      positioning: 'Immediate tactical shorts in airlines, hotels and cruise operators; long‑dated defense contractor calls; rotation into energy infrastructure on Middle East escalation risk; residual beta hedged via long volatility.',
      image: findImage(['sept-11','9-11','911'])
    },
    {
      title: 'Global Financial Crisis',
      headline: 'Sep 2008 — Multi‑asset deleveraging; credit spread explosion; equity freefall',
      cvar: 'CVAR Impact: –$450M projected at the open',
      outcome: 'Actual Outcome: –$12M post‑hedge',
      positioning: 'Short mortgage lenders and regionals as Lehman collapsed; CDS on weakest IBs; rotated profits into distressed corporates pre‑TARP.',
      image: findImage(['gfc','2008','financial'])
    },
    {
      title: 'COVID Liquidity Spiral',
      headline: 'Feb–Mar 2020 — Pandemic shock; equity limit‑downs; dollar squeeze; crude collapse',
      cvar: 'CVAR Impact: –$390M in modeled peak stress',
      outcome: 'Actual Outcome: +$25M',
      positioning: 'Short airlines, hotels, live entertainment and cruise lines; long bleach, e‑commerce and video conferencing; scaled into oil shorts ahead of OPEC price war.',
      image: findImage(['covid','2020','pandemic'])
    },
    {
      title: 'Flash Crash',
      headline: 'May 2010 — Sudden intraday U.S. equity collapse; liquidity evaporation; algo feedback loop',
      cvar: 'CVAR Impact: –$165M instantaneous',
      outcome: 'Actual Outcome: +$3M',
      positioning: 'Pulled bids seconds before cascade; reloaded at −9% in high‑beta ETFs; flipped into rebound for +6% intraday.',
      image: findImage(['flash','2010'])
    },
    {
      title: 'Swiss Franc Shock',
      headline: 'Jan 2015 — SNB removes CHF/EUR floor; currency spikes 30%',
      cvar: 'CVAR Impact: –$95M from FX exposures',
      outcome: 'Actual Outcome: +$5M',
      positioning: 'Short Austrian/Polish mortgage lenders with CHF liabilities; long Swiss luxury exporters on strong‑currency brand premium.',
      image: findImage(['chf','swiss','2015'])
    },
    {
      title: 'UK Gilt Crisis',
      headline: 'Sep–Oct 2022 — LDI margin calls; gilt yields spike; GBP collapses',
      cvar: 'CVAR Impact: –$175M',
      outcome: 'Actual Outcome: –$2M',
      positioning: 'Short GBP and gilt futures on mini‑budget; puts on UK homebuilders; short UK banks on mortgage stress.',
      image: findImage(['gilt','ldi','2022','uk','british'])
    },
    {
      title: 'Jane Street India Ban (Special Situations Desk)',
      headline: 'Jul 2025 — SEBI freezes $567M on alleged Bank Nifty expiry manipulation',
      cvar: 'CVAR Impact: –$140M',
      outcome: 'Actual Outcome: +$9M',
      positioning: 'Shadow‑basket hedging of Bank Nifty; opportunistic long puts into expiry; volatility harvesting during regulatory uncertainty.',
      image: findImage(['india','bank','nifty','2025','jane'])
    },
  ];

  // Ensure chronological order by extracting the first 4-digit year from headline
  const extractYear = (s: string): number => {
    const m = s.match(/(19|20)\d{2}/);
    return m ? parseInt(m[0], 10) : 9999;
  };
  const roadmapChrono = [...roadmapItems].sort(
    (a, b) => extractYear(a.headline) - extractYear(b.headline)
  );

  useEffect(() => {
    const observerOptions = {
      threshold: 0.1,
      rootMargin: '0px 0px -50px 0px'
    };

    const observer = new IntersectionObserver((entries) => {
      entries.forEach((entry) => {
        if (entry.isIntersecting) {
          entry.target.classList.add('animate');
        }
      });
    }, observerOptions);

    // Observe sections
    if (aboutRef.current) observer.observe(aboutRef.current);
    if (servicesRef.current) observer.observe(servicesRef.current);
    if (statsRef.current) observer.observe(statsRef.current);
    if (teamRef.current) observer.observe(teamRef.current);

    return () => {
      observer.disconnect();
    };
  }, []);

  // Auto-advance Internship slideshow
  useEffect(() => {
    const timer = window.setInterval(() => {
      setInternshipSlide((prev) => (prev + 1) % internshipItems.length);
    }, 5000);
    return () => window.clearInterval(timer);
  }, [internshipItems.length]);

  // Slideshow images (1:1 as requested)
  const slides = [
    {
      image: slide1,
      title: 'Global Markets',
      subtitle: 'Operating at extraordinary pace and vast scale'
    },
    {
      image: slide2,
      title: 'Trading Excellence',
      subtitle: 'Real-time market surveillance and execution'
    },
    {
      image: slide3,
      title: 'Risk Analytics',
      subtitle: 'Advanced technology to protect institutional capital'
    },
    {
      image: slide4,
      title: 'Options & Derivatives',
      subtitle: 'Sophisticated risk management strategies'
    }
  ];

  const [currentSlide, setCurrentSlide] = useState(0);
  const [activeTab, setActiveTab] = useState<'solutions' | 'analytics' | 'team'>('solutions');
  const [isTransitioning, setIsTransitioning] = useState(false);
  const [animatedNumbers, setAnimatedNumbers] = useState({ assets: 0, accuracy: 0, monitoring: 0, experts: 0 });

  // Intersection Observer for animations (from App.tsx)
  useEffect(() => {
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
          
          // Trigger number animation when stats section comes into view
          if (target.classList.contains('stats-section')) {
            animateNumbers()
          }
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

  // Auto-advance slideshow (same animation behavior)
  useEffect(() => {
    const interval = setInterval(() => {
      setCurrentSlide((prev) => (prev + 1) % slides.length);
    }, 5000);
    return () => clearInterval(interval);
  }, [slides.length]);

  const handleGetStarted = () => {
    navigate('/login');
  };

  // Animate numbers function (1:1)
  const animateNumbers = () => {
    const targets = { assets: 45, accuracy: 99.7, monitoring: 24, experts: 260 };
    const duration = 800; // ms
    const steps = 40;
    const stepDuration = duration / steps;
    let currentStep = 0;
    const animate = () => {
      currentStep++;
      const progress = currentStep / steps;
      setAnimatedNumbers({
        assets: Math.floor(targets.assets * progress),
        accuracy: parseFloat((targets.accuracy * progress).toFixed(1)),
        monitoring: Math.floor(targets.monitoring * progress),
        experts: Math.floor(targets.experts * progress),
      });
      if (currentStep < steps) setTimeout(animate, stepDuration);
    };
    animate();
  };

  // Start number animation immediately
  useEffect(() => { 
    animateNumbers(); 
  }, []);

  const handleTabChange = (tabId: 'solutions' | 'analytics' | 'team') => {
    if (tabId === activeTab || isTransitioning) return;
    setIsTransitioning(true);
    setTimeout(() => {
      setActiveTab(tabId);
      setTimeout(() => setIsTransitioning(false), 50);
    }, 200);
  };

  // Navigation handler function  
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
    // Add other navigation handlers as needed
  };

  // Highlight +/- amounts within text with color and emphasis (bold + underline)
  const renderWithHighlights = (text: string): React.ReactNode[] => {
    const parts: React.ReactNode[] = [];
    const regex = /([–-]\$\d+(?:\.\d+)?[A-Za-z]*)|(\+\$\d+(?:\.\d+)?[A-Za-z]*)/g; // matches –$280M, -$12M, +$25M
    let lastIndex = 0;
    let match: RegExpExecArray | null;
    while ((match = regex.exec(text)) !== null) {
      const start = match.index;
      const end = regex.lastIndex;
      if (start > lastIndex) {
        parts.push(<span key={`${lastIndex}-${start}`}>{text.slice(lastIndex, start)}</span>);
      }
      const token = match[0];
      const isNegative = token.startsWith('–') || token.startsWith('-');
      parts.push(
        <span
          key={`${start}-${end}`}
          style={{
            color: isNegative ? '#d32f2f' : '#388e3c',
            fontWeight: 800,
            textDecoration: 'underline',
          }}
        >
          {token}
        </span>
      );
      lastIndex = end;
    }
    if (lastIndex < text.length) {
      parts.push(<span key={`${lastIndex}-end`}>{text.slice(lastIndex)}</span>);
    }
    return parts;
  };

  // Helpers for roadmap KPI-only rendering (no underline, improved colors)
  const extractMoneyToken = (text: string): string | null => {
    const regex = /([–-]?\$\d+(?:\.\d+)?[A-Za-z]*)|((?:\+)\$\d+(?:\.\d+)?[A-Za-z]*)/;
    const match = text.match(regex);
    return match ? match[0] : null;
  };

  const renderKpiToken = (token: string | null): React.ReactNode => {
    if (!token) return null;
    const isNegative = token.startsWith('–') || token.startsWith('-');
    const color = isNegative ? '#ff5252' : '#4caf50';
    return (
      <span style={{ color, fontWeight: 800 }}>{token}</span>
    );
  };

  return (
    <div className="landing-page">
      <Navbar
        onClientLogin={handleGetStarted}
        onBrandClick={() => navigate('/')}
        onNavigate={handleNavigate}
      />

      {/* Hero Section with Slideshow - Full Bleed (1:1 design + animations) */}
      <section style={{ 
        position: 'relative',
        height: '70vh', 
        backgroundColor: '#2c3e50', 
        overflow: 'hidden',
        marginTop: '70px',
        width: '100vw',
        marginLeft: 'calc(-50vw + 50%)',
        marginRight: 'calc(-50vw + 50%)'
      }}>
        {/* Background Slideshow */}
        {slides.map((slide, index) => (
          <div
            key={index}
            style={{
              position: 'absolute',
              top: 0,
              left: 0,
              width: '100%',
              height: '100%',
              backgroundImage: `linear-gradient(rgba(0, 0, 0, 0.4), rgba(0, 0, 0, 0.4)), url(${slide.image})`,
              backgroundSize: 'cover',
              backgroundPosition: 'center',
              backgroundRepeat: 'no-repeat',
              zIndex: currentSlide === index ? 1 : 0,
              opacity: currentSlide === index ? 1 : 0,
              transition: 'opacity 1s ease-in-out'
            }}
          />
        ))}

        {/* Content Overlay */}
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
              {slides[currentSlide].title}
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
              {slides[currentSlide].subtitle}
            </p>
            <button 
              className="hero-cta"
              style={{
                backgroundColor: '#1976d2',
                color: 'white',
                padding: '1rem 2rem',
                borderRadius: '4px',
                fontSize: '1rem',
                fontWeight: '500',
                border: 'none',
                cursor: 'pointer',
                display: 'flex',
                alignItems: 'center',
                gap: '0.5rem',
                boxShadow: '0 4px 8px rgba(0,0,0,0.2)',
                margin: '0 auto'
              }}
              onClick={handleGetStarted}
            >
              <span>Explore Our Solutions</span>
            </button>
          </div>
        </div>

        {/* Slide Indicators */}
        <div style={{
          position: 'absolute',
          bottom: '2rem',
          left: '50%',
          transform: 'translateX(-50%)',
          display: 'flex',
          gap: '0.5rem',
          zIndex: 3
        }}>
          {slides.map((_, index) => (
            <button
              key={index}
              onClick={() => setCurrentSlide(index)}
              style={{
                width: '12px',
                height: '12px',
                borderRadius: '50%',
                border: 'none',
                backgroundColor: currentSlide === index ? 'white' : 'rgba(255, 255, 255, 0.5)',
                cursor: 'pointer',
                transition: 'background-color 0.3s'
              }}
            />
          ))}
        </div>
      </section>

      {/* Main Content Wrapper with Padding (copied sections) */}
      <div style={{ color: '#202124', width: '100%', margin: '0 auto' }}>

        {/* Tabbed Solutions Section */}
        <section className="full-bleed animate-on-scroll" style={{ backgroundColor: '#ffffff', padding: '4rem 0' }}>
          <div className="container">
            <div style={{ textAlign: 'center', marginBottom: '2rem' }}>
              <h2 style={{ fontSize: '2.25rem', fontWeight: 'bold', color: '#202124', marginBottom: '0.75rem' }}>Our Risk Solutions</h2>
              <p style={{ fontSize: '1.125rem', color: '#5f6368', maxWidth: '600px', margin: '0 auto' }}>
                Comprehensive risk management across all asset classes and market conditions
              </p>
            </div>

            {/* Tabs */}
            <div style={{ display: 'flex', justifyContent: 'center', marginBottom: '2rem', gap: '0.5rem' }}>
              {[
                { id: 'solutions' as const, label: 'Risk Solutions', icon: Shield },
                { id: 'analytics' as const, label: 'Analytics', icon: TrendingUp },
                { id: 'team' as const, label: 'Our Team', icon: Users },
              ].map((tab) => (
                <button
                  key={tab.id}
                  onClick={() => handleTabChange(tab.id)}
                  style={{
                    backgroundColor: activeTab === tab.id ? '#1976d2' : 'transparent',
                    color: activeTab === tab.id ? 'white' : '#5f6368',
                    border: '1px solid #dadce0',
                    padding: '0.75rem 1.5rem',
                    borderRadius: '4px',
                    fontSize: '0.875rem',
                    fontWeight: '500',
                    cursor: 'pointer',
                    display: 'flex',
                    alignItems: 'center',
                    gap: '0.5rem',
                    transition: 'all 0.3s ease',
                    transform: activeTab === tab.id ? 'scale(1.05)' : 'scale(1)'
                  }}
                >
                  <tab.icon size={16} />
                  {tab.label}
                </button>
              ))}
            </div>

            {/* Tab Content with Animation */}
            <div style={{
              minHeight: '300px',
              position: 'relative',
              opacity: isTransitioning ? 0.3 : 1,
              transform: isTransitioning ? 'translateY(10px)' : 'translateY(0)',
              transition: 'opacity 0.2s ease, transform 0.2s ease'
            }}>
              {activeTab === 'solutions' && (
                <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(300px, 1fr))', gap: '1.5rem', animation: 'slideIn 0.3s ease-out' }}>
                  {[
                    { title: 'Portfolio Risk Management', desc: 'Advanced VaR models and stress testing across all asset classes', icon: Shield },
                    { title: 'Real-time Monitoring', desc: '24/7 surveillance systems with automated alerts and responses', icon: TrendingUp },
                    { title: 'Regulatory Compliance', desc: 'Comprehensive reporting and regulatory framework adherence', icon: Award },
                  ].map((card, index) => (
                    <div key={index} style={{ backgroundColor: '#f8f9fa', padding: '1.5rem', borderRadius: '8px', border: '1px solid #e9ecef', textAlign: 'center', transition: 'transform 0.2s', cursor: 'pointer', animation: `fadeInUp 0.4s ease-out ${index * 0.1}s both` }}
                      onMouseEnter={(e) => (e.currentTarget.style.transform = 'translateY(-4px)')}
                      onMouseLeave={(e) => (e.currentTarget.style.transform = 'translateY(0)')}>
                      <card.icon size={48} style={{ color: '#1976d2', marginBottom: '1rem' }} />
                      <h3 style={{ fontSize: '1.25rem', fontWeight: 'bold', color: '#202124', marginBottom: '0.5rem' }}>{card.title}</h3>
                      <p style={{ color: '#5f6368', fontSize: '0.875rem' }}>{card.desc}</p>
                    </div>
                  ))}
                </div>
              )}

              {activeTab === 'analytics' && (
                <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(300px, 1fr))', gap: '1.5rem', animation: 'slideIn 0.3s ease-out' }}>
                  {[
                    { title: 'Machine Learning Models', desc: 'AI-powered risk prediction and pattern recognition', icon: TrendingUp },
                    { title: 'Big Data Analytics', desc: 'Processing millions of data points in real-time', icon: Shield },
                    { title: 'Predictive Modeling', desc: 'Forward-looking risk assessment and scenario analysis', icon: Award },
                  ].map((card, index) => (
                    <div key={index} style={{ backgroundColor: '#f8f9fa', padding: '1.5rem', borderRadius: '8px', border: '1px solid #e9ecef', textAlign: 'center', transition: 'transform 0.2s', cursor: 'pointer', animation: `fadeInUp 0.4s ease-out ${index * 0.1}s both` }}
                      onMouseEnter={(e) => (e.currentTarget.style.transform = 'translateY(-4px)')}
                      onMouseLeave={(e) => (e.currentTarget.style.transform = 'translateY(0)')}>
                      <card.icon size={48} style={{ color: '#1976d2', marginBottom: '1rem' }} />
                      <h3 style={{ fontSize: '1.25rem', fontWeight: 'bold', color: '#202124', marginBottom: '0.5rem' }}>{card.title}</h3>
                      <p style={{ color: '#5f6368', fontSize: '0.875rem' }}>{card.desc}</p>
                    </div>
                  ))}
                </div>
              )}

              {activeTab === 'team' && (
                <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(300px, 1fr))', gap: '1.5rem', animation: 'slideIn 0.3s ease-out' }}>
                  {[
                    { title: 'Quantitative Experts', desc: 'PhD-level mathematicians and statisticians', icon: Users },
                    { title: 'Technology Leaders', desc: 'Software engineers and system architects', icon: Shield },
                    { title: 'Risk Specialists', desc: 'Industry veterans with decades of experience', icon: Award },
                  ].map((card, index) => (
                    <div key={index} style={{ backgroundColor: '#f8f9fa', padding: '1.5rem', borderRadius: '8px', border: '1px solid #e9ecef', textAlign: 'center', transition: 'transform 0.2s', cursor: 'pointer', animation: `fadeInUp 0.4s ease-out ${index * 0.1}s both` }}
                      onMouseEnter={(e) => (e.currentTarget.style.transform = 'translateY(-4px)')}
                      onMouseLeave={(e) => (e.currentTarget.style.transform = 'translateY(0)')}>
                      <card.icon size={48} style={{ color: '#1976d2', marginBottom: '1rem' }} />
                      <h3 style={{ fontSize: '1.25rem', fontWeight: 'bold', color: '#202124', marginBottom: '0.5rem' }}>{card.title}</h3>
                      <p style={{ color: '#5f6368', fontSize: '0.875rem' }}>{card.desc}</p>
                    </div>
                  ))}
                </div>
              )}
            </div>
          </div>
        </section>

        {/* Stats Section with Cards */}
        <section className="full-bleed animate-on-scroll stats-section" style={{ backgroundColor: '#f2f2f2', padding: '4rem 0' }}>
          <div className="container">
            <div style={{ textAlign: 'center', marginBottom: '2rem' }}>
              <h2 style={{ fontSize: '2.25rem', fontWeight: 'bold', color: '#202124', marginBottom: '1rem' }}>By The Numbers</h2>
            </div>
            <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(250px, 1fr))', gap: '1.5rem' }}>
              {[
                { number: animatedNumbers.assets, suffix: 'B', label: 'Assets Under Management', desc: 'Across global markets and asset classes' },
                { number: animatedNumbers.accuracy, suffix: '%', label: 'Model Accuracy', desc: 'Risk model accuracy rate across 15+ years' },
                { number: animatedNumbers.monitoring, suffix: '/7', label: 'Monitoring', desc: 'Real-time risk monitoring and automated responses' },
                { number: animatedNumbers.experts, suffix: '+', label: 'PhD Experts', desc: 'Quantitative specialists across 40+ fields' },
              ].map((stat, index) => (
                <div key={index} style={{ backgroundColor: 'white', padding: '1.5rem', borderRadius: '12px', textAlign: 'center', boxShadow: '0 4px 6px rgba(0, 0, 0, 0.1)', cursor: 'pointer' }}>
                  <div style={{ fontSize: '2.5rem', fontWeight: 'bold', color: '#1976d2', marginBottom: '0.5rem' }}>{stat.number}{stat.suffix}</div>
                  <div style={{ fontSize: '1.125rem', fontWeight: '600', color: '#202124', marginBottom: '0.5rem' }}>{stat.label}</div>
                  <div style={{ color: '#5f6368', fontSize: '0.875rem' }}>{stat.desc}</div>
                </div>
              ))}
            </div>
          </div>
        </section>

        {/* Careers Section with Gradient */}
        <section className="full-bleed animate-on-scroll" style={{ background: 'linear-gradient(135deg, #1976d2 0%, #1565c0 100%)', padding: '4rem 0', position: 'relative' }}>
          <div style={{ position: 'absolute', top: '0', right: '0', width: '300px', height: '300px', background: 'rgba(255, 255, 255, 0.1)', borderRadius: '50%', transform: 'translate(100px, -100px)' }} />
          <div style={{ position: 'absolute', bottom: '0', left: '0', width: '200px', height: '200px', background: 'rgba(255, 255, 255, 0.05)', borderRadius: '50%', transform: 'translate(-50px, 50px)' }} />
          <div className="container" style={{ position: 'relative', zIndex: 1 }}>
            {/* Header */}
            <div style={{ marginBottom: '1.5rem' }}>
              <h2 style={{ fontSize: '2.5rem', fontWeight: 900, color: 'white', marginBottom: '0.75rem', lineHeight: 1.2 }}>Institutional‑Grade Market Intelligence</h2>
              <p style={{ fontSize: '1.125rem', color: 'rgba(255, 255, 255, 0.92)', marginBottom: '0.75rem' }}>
                We convert market structure, cross‑asset volatility and flow‑driven signals into consistently actionable risk decisions.
              </p>
              <p style={{ fontSize: '1.1rem', color: 'rgba(255, 255, 255, 0.95)', marginBottom: '1.25rem', fontStyle: 'italic' }}>
                “Everything is already priced in — and we know how to turn that into our edge.”
              </p>
            </div>

            {/* Vertical Road‑map */}
            <div className="roadmap">
              <div className="roadmap-rail" aria-hidden="true" />
              {roadmapChrono.map((ev, idx) => {
                const isEven = idx % 2 === 0;
                const EventCard = (
                  <div className="roadmap-card event">
                    <h3 className="roadmap-title">{ev.title}</h3>
                    <div className="roadmap-media">
                      {ev.image ? (
                        <img src={ev.image} alt={ev.title} loading="lazy" />
                      ) : (
                        <div className="roadmap-media-pending">image pending</div>
                      )}
                    </div>
                  </div>
                );
                const DetailsCard = (
                  <div className="roadmap-card details">
                    <div className="roadmap-subheading">Event Context</div>
                    <p className="roadmap-context">{ev.headline}</p>
                    <div className="roadmap-kpis">
                      <span className="roadmap-chip">
                        CVAR: {renderKpiToken(extractMoneyToken(ev.cvar))} at the open
                      </span>
                      <span className="roadmap-chip">
                        Actual Outcome post-hedge: {renderKpiToken(extractMoneyToken(ev.outcome))}
                      </span>
                    </div>
                    <div className="roadmap-subheading" style={{ marginTop: '0.25rem' }}>Strategic Positioning</div>
                    <p className="roadmap-positioning">{ev.positioning}</p>
                  </div>
                );
                return (
                  <div key={idx} className="roadmap-row">
                    <span className="roadmap-dot" aria-hidden="true" />
                    {isEven ? (
                      <>
                        {EventCard}
                        {DetailsCard}
                      </>
                    ) : (
                      <>
                        {DetailsCard}
                        {EventCard}
                      </>
                    )}
                  </div>
                );
              })}
            </div>
          </div>
        </section>

        {/* Internship Program Section */}
        <section className="full-bleed animate-on-scroll" style={{ backgroundColor: '#f8f9fa', padding: '4rem 0' }}>
          <div className="container">
            <div style={{ textAlign: 'center', marginBottom: '3rem' }}>
              <h2 style={{ fontSize: '2.25rem', fontWeight: 'bold', color: '#202124', marginBottom: '1rem' }}>Internship Program</h2>
              <p style={{ fontSize: '1.125rem', color: '#5f6368', maxWidth: '600px', margin: '0 auto' }}>
                Join our dynamic internship program and gain hands-on experience in quantitative finance and risk management.
              </p>
            </div>

            {/* CTA */}
            <div style={{ display: 'flex', justifyContent: 'center', gap: '1rem', marginBottom: '3rem', flexWrap: 'wrap' }}>
              <button style={{ backgroundColor: 'white', color: '#1976d2', padding: '1rem 2rem', borderRadius: '4px', fontSize: '1rem', fontWeight: '500', cursor: 'pointer', border: '1px solid #1976d2', transition: 'all 0.2s', display: 'flex', alignItems: 'center', gap: '0.5rem' }}
                onMouseEnter={(e) => {
                  e.currentTarget.style.backgroundColor = '#1976d2';
                  e.currentTarget.style.color = 'white';
                }}
                onMouseLeave={(e) => {
                  e.currentTarget.style.backgroundColor = 'white';
                  e.currentTarget.style.color = '#1976d2';
                }}
                onClick={() => navigate('/careers')}
              >
                <span>Learn More</span>
                <ChevronRight size={20} />
              </button>
            </div>

            {/* Internship Items Slideshow */}
            <div style={{ maxWidth: '1000px', margin: '0 auto', display: 'flex', alignItems: 'center', gap: '1.5rem' }}>
              {/* Left Arrow */}
              <button
                onClick={() => setInternshipSlide((prev) => prev === 0 ? internshipItems.length - 1 : prev - 1)}
                style={{
                  backgroundColor: '#1976d2',
                  border: 'none',
                  width: '44px',
                  height: '44px',
                  borderRadius: '50%',
                  color: 'white',
                  fontSize: '22px',
                  cursor: 'pointer',
                  boxShadow: '0 4px 12px rgba(25,118,210,0.3)'
                }}
              >
                &#8249;
              </button>

              <div style={{ overflow: 'hidden', borderRadius: '12px', flex: 1, background: 'white', border: '1px solid #e9ecef' }}>
                <div style={{ display: 'flex', transform: `translateX(-${internshipSlide * 100}%)`, transition: 'transform 0.6s ease-in-out' }}>
                  {internshipItems.map((item, idx) => (
                    <div key={idx} style={{ minWidth: '100%', padding: '2rem', display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
                      <div style={{ textAlign: 'center', maxWidth: '720px' }}>
                        <div style={{ color: '#202124', fontSize: '1.25rem', fontWeight: 700, marginBottom: '0.25rem' }}>{item.title}</div>
                        <div style={{ color: '#5f6368', fontSize: '0.95rem' }}>{item.desc}</div>
                      </div>
                    </div>
                  ))}
                </div>
              </div>

              {/* Right Arrow */}
              <button
                onClick={() => setInternshipSlide((prev) => (prev + 1) % internshipItems.length)}
                style={{
                  backgroundColor: '#1976d2',
                  border: 'none',
                  width: '44px',
                  height: '44px',
                  borderRadius: '50%',
                  color: 'white',
                  fontSize: '22px',
                  cursor: 'pointer',
                  boxShadow: '0 4px 12px rgba(25,118,210,0.3)'
                }}
              >
                &#8250;
              </button>
            </div>

            {/* Dots */}
            <div style={{ display: 'flex', justifyContent: 'center', gap: '8px', marginTop: '12px' }}>
              {internshipItems.map((_, i) => (
                <div key={i} style={{ width: '10px', height: '10px', borderRadius: '50%', background: i === internshipSlide ? '#1976d2' : '#e0e0e0' }} />
              ))}
            </div>
          </div>
        </section>

        {/* News Section */}
        <section className="news-section full-bleed animate-on-scroll">
          <div className="container">
            <header className="news-header">
              <h2 className="news-title">Featured News &amp; Perspectives</h2>
              <p className="news-subtitle">
                Explore selected coverage and perspectives from across our firm.
              </p>
            </header>

            {(() => {
              const allNews = require('../data/newsItems').newsItems as any[];
              if (!allNews || allNews.length === 0) return null;
              const [featured, ...others] = allNews;
              return (
                <>
                  {/* Featured article */}
                  <article className="news-feature">
                    <a className="news-feature-media" href={featured.href} aria-label={featured.title}>
                      <picture>
                        <source srcSet={featured.imageWebp} type="image/webp" />
                        <img
                          src={featured.imageJpg}
                          alt={featured.alt}
                          loading="lazy"
                          width={1200}
                          height={675}
                        />
                      </picture>
                      <span className="news-category">{featured.category}</span>
                    </a>
                    <div className="news-feature-body">
                      <h3 className="news-feature-title">
                        <a href={featured.href}>{featured.title}</a>
                      </h3>
                      <p className="news-feature-desc">{featured.desc}</p>
                      <div className="news-meta">
                        <time dateTime={featured.date}>
                          {new Date(featured.date).toLocaleDateString(undefined, {
                            year: 'numeric',
                            month: 'short',
                            day: '2-digit'
                          })}
                        </time>
                        <span aria-hidden="true">•</span>
                        <span>{featured.readTime}</span>
                      </div>
                    </div>
                  </article>

                  {/* Grid of the rest */}
                  <div className="news-grid">
                    {others.map((item) => (
                      <article key={item.id} className="news-card">
                        <a className="news-media" href={item.href} aria-label={item.title}>
                          <picture>
                            <source srcSet={item.imageWebp} type="image/webp" />
                            <img
                              src={item.imageJpg}
                              alt={item.alt}
                              loading="lazy"
                              width={600}
                              height={400}
                            />
                          </picture>
                          <span className="news-category">{item.category}</span>
                        </a>
                        <div className="news-body">
                          <h3 className="news-card-title">
                            <a href={item.href}>{item.title}</a>
                          </h3>
                          <p className="news-desc">{item.desc}</p>
                          <div className="news-meta">
                            <time dateTime={item.date}>
                              {new Date(item.date).toLocaleDateString(undefined, {
                                year: 'numeric',
                                month: 'short',
                                day: '2-digit'
                              })}
                            </time>
                            <span aria-hidden="true">•</span>
                            <span>{item.readTime}</span>
                          </div>
                        </div>
                        <a className="news-cta" href={item.href}>
                          Read More
                          <ArrowRight size={16} />
                        </a>
                      </article>
                    ))}
                  </div>
                </>
              );
            })()}
          </div>
        </section>

        {/* Footer */}
        <Footer />
      </div>
    </div>
  );
};

export default LandingPage;
