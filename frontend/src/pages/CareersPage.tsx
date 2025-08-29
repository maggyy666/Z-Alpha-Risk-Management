import React, { useEffect, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import Navbar from '../components/Navbar';
import LandingFooter from '../components/LandingFooter';
import './CareersPage.css';
import { TrendingUp, Users, Award, BookOpen, Star, Target, Brain, MapPin, DollarSign, Briefcase, Clock, SlidersHorizontal } from 'lucide-react';

const CareersPage: React.FC = () => {
  const navigate = useNavigate();
  const [activeSection, setActiveSection] = useState<'internship' | 'careers'>('internship');
  const [currentUniversity, setCurrentUniversity] = useState<number>(0);

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
  const heroImage = findImage(['harvard']);

  // Full-time careers: jobs data and filters
  const allJobs: Array<{
    title: string;
    category: 'Quant' | 'Investment Banking' | 'Risk Management' | 'Trading' | 'Engineering';
    location: string;
    workType: 'Onsite' | 'Hybrid' | 'Remote';
    salaryUSD: number;
    level: 'Analyst' | 'Associate' | 'VP' | 'Director' | 'Principal';
  }> = [
    { title: 'Quant Researcher – Macro Vol', category: 'Quant', location: 'New York, NY', workType: 'Onsite', salaryUSD: 275000, level: 'Associate' },
    { title: 'Quantitative Developer – Python/C++', category: 'Engineering', location: 'New York, NY', workType: 'Onsite', salaryUSD: 240000, level: 'Associate' },
    { title: 'Risk Manager – Equities', category: 'Risk Management', location: 'New York, NY', workType: 'Onsite', salaryUSD: 230000, level: 'VP' },
    { title: 'Execution Trader – Systematic', category: 'Trading', location: 'New York, NY', workType: 'Onsite', salaryUSD: 260000, level: 'VP' },
    { title: 'Data Engineer – Market Data', category: 'Engineering', location: 'New York, NY', workType: 'Hybrid', salaryUSD: 210000, level: 'Associate' },
    { title: 'Junior Quant Analyst – Multi-Asset', category: 'Quant', location: 'New York, NY', workType: 'Onsite', salaryUSD: 180000, level: 'Analyst' },
    { title: 'Junior Risk Analyst – Stress Testing', category: 'Risk Management', location: 'New York, NY', workType: 'Onsite', salaryUSD: 175000, level: 'Analyst' },
    { title: 'Junior Data Engineer – ETL', category: 'Engineering', location: 'New York, NY', workType: 'Hybrid', salaryUSD: 170000, level: 'Analyst' },
    { title: 'Trading Assistant – Systematic', category: 'Trading', location: 'New York, NY', workType: 'Onsite', salaryUSD: 165000, level: 'Analyst' },
    { title: 'Portfolio Risk – Stress & VaR', category: 'Risk Management', location: 'New York, NY', workType: 'Onsite', salaryUSD: 245000, level: 'VP' },
    { title: 'IB Associate – Capital Markets Liaison', category: 'Investment Banking', location: 'New York, NY', workType: 'Onsite', salaryUSD: 200000, level: 'Associate' },
    { title: 'Quant Platform Engineer', category: 'Engineering', location: 'New York, NY', workType: 'Onsite', salaryUSD: 235000, level: 'VP' },
    { title: 'Trader – Index Options', category: 'Trading', location: 'New York, NY', workType: 'Onsite', salaryUSD: 290000, level: 'Director' },
  ];

  const [query, setQuery] = useState('');
  const [selectedCategory, setSelectedCategory] = useState<'All' | 'Quant' | 'Investment Banking' | 'Risk Management' | 'Trading' | 'Engineering'>('All');
  const [locationFilter, setLocationFilter] = useState<'Any' | 'New York, NY' | 'London, UK'>('Any');
  const [workTypeFilter, setWorkTypeFilter] = useState<'Any' | 'Onsite' | 'Hybrid' | 'Remote'>('Any');
  const [minSalary, setMinSalary] = useState<number>(180000);


  const filtered = allJobs
    .filter((j) => (query ? j.title.toLowerCase().includes(query.toLowerCase()) : true))
    .filter((j) => (selectedCategory === 'All' ? true : j.category === selectedCategory))
    .filter((j) => (locationFilter === 'Any' ? true : j.location === locationFilter))
    .filter((j) => (workTypeFilter === 'Any' ? true : j.workType === workTypeFilter))
    .filter((j) => j.salaryUSD >= minSalary)
    .sort((a, b) => b.salaryUSD - a.salaryUSD);

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

  // Ensure newly rendered sections become visible after toggle
  useEffect(() => {
    const elements = document.querySelectorAll('.careers-page .animate-on-scroll');
    elements.forEach((el) => el.classList.add('animate-in'));
  }, [activeSection]);

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
  };

  // Universities slideshow data (name, location, acceptance rate)
  const universities: Array<{ name: string; location: string; acceptanceRate: string }> = [
    { name: 'Harvard University', location: 'Cambridge, MA', acceptanceRate: '0.67%' },
    { name: 'Yale University', location: 'New Haven, CT', acceptanceRate: '0.72%' },
    { name: 'Massachusetts Institute of Technology (MIT)', location: 'Cambridge, MA', acceptanceRate: '0.54%' },
    { name: 'ETH Zurich', location: 'Zurich, Switzerland', acceptanceRate: '0.32%' },
    { name: 'Imperial College London', location: 'London, UK', acceptanceRate: '0.81%' },
    { name: 'Stanford University', location: 'Stanford, CA', acceptanceRate: '0.45%' }
  ];

  // Auto-advance universities slideshow
  useEffect(() => {
    const timer = window.setInterval(() => {
      setCurrentUniversity((prev) => (prev + 1) % universities.length);
    }, 5000);
    return () => window.clearInterval(timer);
  }, [universities.length]);

  return (
    <div className="careers-page">
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
            Join Z-Alpha
          </h1>
          <p className="animate-on-scroll" style={{
            fontSize: '1.5rem',
            opacity: 0.9,
            lineHeight: '1.6',
            fontWeight: '300'
          }}>
            Shape the future of quantitative finance with the world's most selective trading and technology programs.
          </p>
        </div>
      </section>

      {/* Section Toggle */}
      <section className="animate-on-scroll" style={{ padding: '4rem 2rem 2rem', backgroundColor: '#ffffff' }}>
        <div style={{ maxWidth: '1200px', margin: '0 auto', textAlign: 'center' }}>
          <div style={{
            display: 'inline-flex',
            backgroundColor: '#f8f9fa',
            borderRadius: '50px',
            padding: '8px',
            border: '1px solid #e8eaed'
          }}>
            <button
              onClick={() => setActiveSection('internship')}
              style={{
                padding: '12px 32px',
                borderRadius: '42px',
                border: 'none',
                backgroundColor: activeSection === 'internship' ? '#1976d2' : 'transparent',
                color: activeSection === 'internship' ? 'white' : '#5f6368',
                fontSize: '1rem',
                fontWeight: '600',
                cursor: 'pointer',
                transition: 'all 0.3s ease',
                marginRight: '8px'
              }}
            >
              Internship Program
            </button>
            <button
              onClick={() => setActiveSection('careers')}
              style={{
                padding: '12px 32px',
                borderRadius: '42px',
                border: 'none',
                backgroundColor: activeSection === 'careers' ? '#1976d2' : 'transparent',
                color: activeSection === 'careers' ? 'white' : '#5f6368',
                fontSize: '1rem',
                fontWeight: '600',
                cursor: 'pointer',
                transition: 'all 0.3s ease'
              }}
            >
              Full-Time Careers
            </button>
          </div>
        </div>
      </section>

      {/* Internship Section */}
      {activeSection === 'internship' && (
        <>
          {/* Elite Program Section */}
          <section className="animate-on-scroll" style={{ padding: '4rem 2rem', backgroundColor: '#ffffff' }}>
            <div style={{ maxWidth: '1200px', margin: '0 auto', textAlign: 'center' }}>
              <h2 style={{
                fontSize: '3rem',
                fontWeight: 'bold',
                color: '#202124',
                marginBottom: '2rem'
              }}>
                The Most Competitive Program on The Street
              </h2>
              <p style={{
                fontSize: '1.5rem',
                color: '#5f6368',
                marginBottom: '4rem',
                maxWidth: '800px',
                margin: '0 auto 4rem',
                lineHeight: '1.6'
              }}>
                At Z-Alpha, we maintain the highest standards in quantitative finance. Our internship program represents the pinnacle of selective excellence in the industry.
              </p>

              {/* Statistics Grid */}
              <div style={{
                display: 'grid',
                gridTemplateColumns: 'repeat(auto-fit, minmax(200px, 1fr))',
                gap: '2rem',
                marginBottom: '4rem'
              }}>
                <div style={{
                  backgroundColor: '#f8f9fa',
                  padding: '3rem 2rem',
                  borderRadius: '16px',
                  border: '1px solid #e8eaed'
                }}>
                  <TrendingUp size={48} style={{ color: '#d32f2f', marginBottom: '1rem' }} />
                  <div style={{ fontSize: '3rem', fontWeight: 'bold', color: '#d32f2f', marginBottom: '0.5rem' }}>
                    450,000
                  </div>
                  <div style={{ fontSize: '1.25rem', fontWeight: '600', color: '#202124', marginBottom: '0.5rem' }}>
                    Applications Received
                  </div>
                  <div style={{ color: '#5f6368', fontSize: '0.875rem' }}>
                    Annual cycle 2024
                  </div>
                </div>

                <div style={{
                  backgroundColor: '#f8f9fa',
                  padding: '3rem 2rem',
                  borderRadius: '16px',
                  border: '1px solid #e8eaed'
                }}>
                  <Users size={48} style={{ color: '#388e3c', marginBottom: '1rem' }} />
                  <div style={{ fontSize: '3rem', fontWeight: 'bold', color: '#388e3c', marginBottom: '0.5rem' }}>
                    3,500
                  </div>
                  <div style={{ fontSize: '1.25rem', fontWeight: '600', color: '#202124', marginBottom: '0.5rem' }}>
                    Positions Available
                  </div>
                  <div style={{ color: '#5f6368', fontSize: '0.875rem' }}>
                    Global program
                  </div>
                </div>

                <div style={{
                  backgroundColor: '#f8f9fa',
                  padding: '3rem 2rem',
                  borderRadius: '16px',
                  border: '1px solid #e8eaed'
                }}>
                  <Target size={48} style={{ color: '#1976d2', marginBottom: '1rem' }} />
                  <div style={{ fontSize: '3rem', fontWeight: 'bold', color: '#1976d2', marginBottom: '0.5rem' }}>
                    0.014%
                  </div>
                  <div style={{ fontSize: '1.25rem', fontWeight: '600', color: '#202124', marginBottom: '0.5rem' }}>
                    Acceptance Rate
                  </div>
                  <div style={{ color: '#5f6368', fontSize: '0.875rem' }}>
                    Most selective in finance
                  </div>
                </div>

                {/* Removed ranked program card per request */}
              </div>

              {/* Best of the Best Section */}
              <div style={{
                backgroundColor: '#1976d2',
                color: 'white',
                padding: '4rem',
                borderRadius: '16px',
                marginBottom: '4rem'
              }}>
                <h3 style={{ fontSize: '2.5rem', fontWeight: 'bold', marginBottom: '2rem' }}>
                  We Recruit Only The Best of The Best
                </h3>
                <p style={{ fontSize: '1.25rem', lineHeight: '1.6', marginBottom: '2rem', opacity: 0.9 }}>
                  Our selection process is designed to identify exceptional talent with the intellectual rigor, 
                  analytical precision, and innovative thinking required to excel in quantitative finance. 
                  We seek individuals who demonstrate not just academic excellence, but the ability to thrive 
                  in high-pressure, fast-paced environments where split-second decisions impact global markets.
                </p>
                <div style={{
                  display: 'grid',
                  gridTemplateColumns: 'repeat(auto-fit, minmax(250px, 1fr))',
                  gap: '2rem',
                  marginTop: '3rem'
                }}>
                  <div style={{ textAlign: 'center' }}>
                    <Brain size={40} style={{ marginBottom: '1rem' }} />
                    <h4 style={{ fontSize: '1.25rem', fontWeight: 'bold', marginBottom: '0.5rem' }}>
                      Intellectual Excellence
                    </h4>
                    <p style={{ fontSize: '1rem', opacity: 0.9 }}>
                      Top 1% academic performers with exceptional analytical capabilities
                    </p>
                  </div>
                  <div style={{ textAlign: 'center' }}>
                    <TrendingUp size={40} style={{ marginBottom: '1rem' }} />
                    <h4 style={{ fontSize: '1.25rem', fontWeight: 'bold', marginBottom: '0.5rem' }}>
                      Market Intuition
                    </h4>
                    <p style={{ fontSize: '1rem', opacity: 0.9 }}>
                      Natural understanding of market dynamics and risk assessment
                    </p>
                  </div>
                  <div style={{ textAlign: 'center' }}>
                    <Star size={40} style={{ marginBottom: '1rem' }} />
                    <h4 style={{ fontSize: '1.25rem', fontWeight: 'bold', marginBottom: '0.5rem' }}>
                      Leadership Potential
                    </h4>
                    <p style={{ fontSize: '1rem', opacity: 0.9 }}>
                      Demonstrated ability to lead and innovate under pressure
                    </p>
                  </div>
                </div>
              </div>
            </div>
          </section>

          {/* Universities Slideshow */}
          <section className="animate-on-scroll" style={{ padding: '4rem 2rem', backgroundColor: '#f8f9fa' }}>
            <div style={{ maxWidth: '1200px', margin: '0 auto' }}>
              <div style={{ textAlign: 'center', marginBottom: '2rem' }}>
                <h2 style={{ fontSize: '3rem', fontWeight: 'bold', color: '#202124', marginBottom: '1rem' }}>
                  University Network
                </h2>
                <p style={{ fontSize: '1.25rem', color: '#5f6368' }}>
                  Selected candidates often come from our global academic network
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
                  onClick={() => setCurrentUniversity((prev) => prev === 0 ? universities.length - 1 : prev - 1)}
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
                  flex: 1,
                  backgroundColor: 'white'
                }}>
                  <div style={{
                    display: 'flex',
                    transform: `translateX(-${currentUniversity * 100}%)`,
                    transition: 'transform 0.6s ease-in-out'
                  }}>
                    {universities.map((u, idx) => (
                      <div key={idx} style={{ minWidth: '100%', padding: '3rem', display: 'flex', alignItems: 'center', justifyContent: 'space-between', gap: '2rem' }}>
                        <div style={{ flex: 1 }}>
                          <h3 style={{ fontSize: '2rem', fontWeight: 'bold', color: '#202124', marginBottom: '0.5rem' }}>
                            {u.name}
                          </h3>
                          <p style={{ fontSize: '1rem', color: '#5f6368', marginBottom: '1rem' }}>
                            {u.location}
                          </p>
                        </div>
                        <div style={{
                          padding: '0.75rem 1.25rem',
                          backgroundColor: '#e8f5e8',
                          color: '#388e3c',
                          borderRadius: '24px',
                          fontSize: '1rem',
                          fontWeight: 700
                        }}>
                          Acceptance: {u.acceptanceRate}
                        </div>
                      </div>
                    ))}
                  </div>
                </div>

                {/* Right Arrow */}
                <button
                  onClick={() => setCurrentUniversity((prev) => (prev + 1) % universities.length)}
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
              <div style={{ display: 'flex', justifyContent: 'center', gap: '8px', marginTop: '16px' }}>
                {universities.map((_, idx) => (
                  <div key={idx} style={{
                    width: '10px',
                    height: '10px',
                    borderRadius: '50%',
                    backgroundColor: idx === currentUniversity ? '#1976d2' : '#e0e0e0',
                    transition: 'all 0.3s ease'
                  }} />
                ))}
              </div>
            </div>
          </section>

          {/* What Sets Us Apart */}
          <section className="animate-on-scroll" style={{ padding: '6rem 2rem', backgroundColor: '#ffffff' }}>
            <div style={{ maxWidth: '1200px', margin: '0 auto', textAlign: 'center' }}>
              <h2 style={{
                fontSize: '3rem',
                fontWeight: 'bold',
                color: '#202124',
                marginBottom: '2rem'
              }}>
                Why Z-Alpha Internships Are Different
              </h2>
              <p style={{
                fontSize: '1.25rem',
                color: '#5f6368',
                marginBottom: '4rem',
                maxWidth: '800px',
                margin: '0 auto 4rem',
                lineHeight: '1.6'
              }}>
                Our interns don't just observe – they contribute to real trading strategies, develop cutting-edge risk models, 
                and work alongside portfolio managers on live positions worth billions of dollars.
              </p>

              <div style={{
                display: 'grid',
                gridTemplateColumns: 'repeat(auto-fit, minmax(300px, 1fr))',
                gap: '3rem'
              }}>
                <div style={{ textAlign: 'center' }}>
                  <div style={{
                    width: '80px',
                    height: '80px',
                    backgroundColor: '#1976d2',
                    borderRadius: '50%',
                    display: 'flex',
                    alignItems: 'center',
                    justifyContent: 'center',
                    margin: '0 auto 1.5rem'
                  }}>
                    <TrendingUp size={40} color="white" />
                  </div>
                  <h3 style={{ fontSize: '1.5rem', fontWeight: 'bold', color: '#202124', marginBottom: '1rem' }}>
                    Real P&L Impact
                  </h3>
                  <p style={{ color: '#5f6368', lineHeight: '1.6' }}>
                    Your models and analysis directly influence trading decisions on positions worth $100M+. 
                    Every intern project has measurable market impact.
                  </p>
                </div>

                <div style={{ textAlign: 'center' }}>
                  <div style={{
                    width: '80px',
                    height: '80px',
                    backgroundColor: '#388e3c',
                    borderRadius: '50%',
                    display: 'flex',
                    alignItems: 'center',
                    justifyContent: 'center',
                    margin: '0 auto 1.5rem'
                  }}>
                    <Brain size={40} color="white" />
                  </div>
                  <h3 style={{ fontSize: '1.5rem', fontWeight: 'bold', color: '#202124', marginBottom: '1rem' }}>
                    Cutting-Edge Technology
                  </h3>
                  <p style={{ color: '#5f6368', lineHeight: '1.6' }}>
                    Work with proprietary trading systems, advanced GARCH models, and real-time risk engines 
                    that process millions of market data points per second.
                  </p>
                </div>

                <div style={{ textAlign: 'center' }}>
                  <div style={{
                    width: '80px',
                    height: '80px',
                    backgroundColor: '#ff9800',
                    borderRadius: '50%',
                    display: 'flex',
                    alignItems: 'center',
                    justifyContent: 'center',
                    margin: '0 auto 1.5rem'
                  }}>
                    <Award size={40} color="white" />
                  </div>
                  <h3 style={{ fontSize: '1.5rem', fontWeight: 'bold', color: '#202124', marginBottom: '1rem' }}>
                    Unmatched Mentorship
                  </h3>
                  <p style={{ color: '#5f6368', lineHeight: '1.6' }}>
                    One-on-one mentorship from senior portfolio managers, quants, and technologists 
                    with decades of experience at the world's top funds.
                  </p>
                </div>
              </div>
            </div>
          </section>
        </>
      )}

      {/* Careers Section */}
      {activeSection === 'careers' && (
        <section className="animate-on-scroll" style={{ padding: '6rem 2rem', backgroundColor: '#f8f9fa' }}>
          <div style={{ maxWidth: '1200px', margin: '0 auto' }}>
            {/* Intro */}
            <div style={{ textAlign: 'center', marginBottom: '2.5rem' }}>
              <h2 style={{ fontSize: '2.75rem', fontWeight: 'bold', color: '#202124', marginBottom: '0.75rem' }}>
                Full-Time Careers at Z-Alpha
              </h2>
              <p style={{ fontSize: '1.125rem', color: '#5f6368', maxWidth: '780px', margin: '0 auto' }}>
                We hire exceptional talent across Quant, Trading, Risk Management and Engineering. Most roles are New York-based and on-site to maximize collaboration and speed of execution.
              </p>
            </div>

            {/* Filters */}
                  {/* Filters Bar */}
                  <div style={{
                    backgroundColor: 'white',
                    border: '1px solid #e8eaed',
                    borderRadius: '12px',
                    padding: '1rem',
                    boxShadow: '0 4px 12px rgba(0,0,0,0.06)',
                    marginBottom: '1.5rem'
                  }}>
                    <div style={{ display: 'flex', alignItems: 'center', gap: '1rem', flexWrap: 'wrap' }}>
                      <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
                        <SlidersHorizontal size={18} style={{ color: '#1976d2' }} />
                        <strong style={{ color: '#202124' }}>Filters</strong>
                      </div>

                      {/* Search */}
                      <input
                        value={query}
                        onChange={(e) => setQuery(e.target.value)}
                        placeholder="Search roles (e.g., Quant, Trader)"
                        style={{
                          flex: '1 1 240px',
                          border: '1px solid #e0e0e0',
                          borderRadius: '8px',
                          padding: '0.5rem 0.75rem'
                        }}
                      />

                      {/* Location */}
                      <select
                        value={locationFilter}
                        onChange={(e) => setLocationFilter(e.target.value as any)}
                        style={{ border: '1px solid #e0e0e0', borderRadius: '8px', padding: '0.5rem 0.75rem' }}
                      >
                        <option value="Any">Any Location</option>
                        <option value="New York, NY">New York, NY</option>
                        <option value="London, UK">London, UK</option>
                      </select>

                      {/* Work Type */}
                      <select
                        value={workTypeFilter}
                        onChange={(e) => setWorkTypeFilter(e.target.value as any)}
                        style={{ border: '1px solid #e0e0e0', borderRadius: '8px', padding: '0.5rem 0.75rem' }}
                      >
                        <option value="Any">Any Work Type</option>
                        <option value="Onsite">Onsite</option>
                        <option value="Hybrid">Hybrid</option>
                        <option value="Remote">Remote</option>
                      </select>

                      {/* Min Salary */}
                      <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
                        <DollarSign size={16} style={{ color: '#1976d2' }} />
                        <input
                          type="range"
                          min={150000}
                          max={350000}
                          step={5000}
                          value={minSalary}
                          onChange={(e) => setMinSalary(parseInt(e.target.value))}
                        />
                        <span style={{ fontSize: '0.9rem', color: '#5f6368', minWidth: 72 }}>
                          ${minSalary.toLocaleString()}
                        </span>
                      </div>

                      {/* Category selector */}
                      <select
                        value={selectedCategory}
                        onChange={(e) => setSelectedCategory(e.target.value as any)}
                        style={{ border: '1px solid #e0e0e0', borderRadius: '8px', padding: '0.5rem 0.75rem' }}
                      >
                        <option value="All">All Categories</option>
                        <option value="Quant">Quant</option>
                        <option value="Trading">Trading</option>
                        <option value="Risk Management">Risk Management</option>
                        <option value="Engineering">Engineering</option>
                        <option value="Investment Banking">Investment Banking</option>
                      </select>

                      {/* Reset */}
                      <button
                        onClick={() => {
                          setQuery('');
                          setSelectedCategory('All');
                          setLocationFilter('Any');
                          setWorkTypeFilter('Any');
                          setMinSalary(180000);
                        }}
                        style={{ marginLeft: 'auto', border: '1px solid #e0e0e0', borderRadius: '8px', padding: '0.5rem 0.75rem', background: 'white' }}
                      >
                        Reset
                      </button>
                    </div>
                  </div>

                  {/* Results count */}
                  <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', margin: '0.5rem 0 1rem' }}>
                    <div style={{ color: '#5f6368', fontSize: '0.95rem' }}>
                      {filtered.length} open roles
                    </div>
                  </div>

                  {/* Jobs List */}
                  <div style={{ display: 'grid', gridTemplateColumns: '1fr', gap: '1rem' }}>
                    {filtered.map((job, idx) => (
                      <div key={idx} style={{
                        backgroundColor: 'white',
                        border: '1px solid #e8eaed',
                        borderRadius: '12px',
                        padding: '1.25rem 1.5rem',
                        display: 'grid',
                        gridTemplateColumns: '1fr auto',
                        gap: '1rem',
                        alignItems: 'center',
                        boxShadow: '0 4px 12px rgba(0,0,0,0.06)'
                      }}>
                        <div>
                          <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', marginBottom: '0.25rem' }}>
                            <span style={{ fontSize: '1.25rem', fontWeight: 800, color: '#202124' }}>{job.title}</span>
                            <span style={{ padding: '0.2rem 0.6rem', borderRadius: '12px', backgroundColor: '#f1f3f4', color: '#5f6368', fontSize: '0.75rem', fontWeight: 600 }}>
                              {job.category}
                            </span>
                            <span style={{ padding: '0.2rem 0.6rem', borderRadius: '12px', backgroundColor: '#e8f5e8', color: '#388e3c', fontSize: '0.75rem', fontWeight: 700 }}>
                              {job.level}
                            </span>
                          </div>
                          <div style={{ display: 'flex', alignItems: 'center', gap: '1rem', flexWrap: 'wrap', color: '#5f6368' }}>
                            <span style={{ display: 'inline-flex', alignItems: 'center', gap: '0.35rem' }}>
                              <MapPin size={16} /> {job.location}
                            </span>
                            <span style={{ display: 'inline-flex', alignItems: 'center', gap: '0.35rem' }}>
                              <Briefcase size={16} /> {job.workType}
                            </span>
                            <span style={{ display: 'inline-flex', alignItems: 'center', gap: '0.35rem' }}>
                              <DollarSign size={16} /> ${job.salaryUSD.toLocaleString()} base
                            </span>
                          </div>
                        </div>
                        <div>
                          <button style={{
                            backgroundColor: '#1976d2',
                            color: 'white',
                            border: 'none',
                            padding: '0.6rem 1rem',
                            borderRadius: '8px',
                            fontWeight: 600,
                            cursor: 'pointer'
                          }}>
                            Apply
                          </button>
                        </div>
                      </div>
                    ))}
                  </div>
            
          </div>
        </section>
      )}

              <LandingFooter />
    </div>
  );
};

export default CareersPage;
