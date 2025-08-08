import React, { useEffect, useRef } from 'react';
import { useNavigate } from 'react-router-dom';
import './LandingPage.css';

const LandingPage: React.FC = () => {
  const navigate = useNavigate();
  const aboutRef = useRef<HTMLElement>(null);
  const servicesRef = useRef<HTMLElement>(null);
  const statsRef = useRef<HTMLElement>(null);
  const teamRef = useRef<HTMLElement>(null);

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

  const handleGetStarted = () => {
    navigate('/login');
  };

  return (
    <div className="landing-page">
      {/* Navigation Bar */}
      <nav className="navbar">
        <div className="nav-container">
          <div className="nav-left">
            <div className="logo">
              <span className="logo-symbol">ρ</span>
              <div className="logo-text">
                <span className="logo-main">Z-ALPHA</span>
                <span className="logo-separator">|</span>
                <span className="logo-sub">Securities</span>
              </div>
            </div>
          </div>
          
          <div className="nav-center">
            <a href="#about" className="nav-link">Who We Are</a>
            <a href="#services" className="nav-link">What We Do</a>
            <a href="#insights" className="nav-link">News & Insights</a>
            <a href="#careers" className="nav-link">Careers</a>
          </div>
          
          <div className="nav-right">
            <button className="client-login-btn" onClick={handleGetStarted}>
              Client Login
            </button>
          </div>
        </div>
      </nav>

      {/* Hero Section */}
      <section className="hero-section">
        <div className="hero-background">
          <div className="hero-content-left">
            <h1 className="hero-title">Where Global<br />Markets Evolve</h1>
            <p className="hero-subtitle">
              Resilient and efficient markets drive economic opportunity. Through our trading, research and technology, we move markets forward.
            </p>
            <button className="hero-cta" onClick={handleGetStarted}>
              Explore Who We Are
            </button>
          </div>
        </div>
      </section>

      {/* About Section */}
      <section className="about-section" id="about" ref={aboutRef}>
        <div className="container">
          <div className="about-content">
            <div className="about-left">
              <h2 className="section-title">The Next-Generation Capital Markets Firm</h2>
            </div>
            <div className="about-right">
              <p className="about-text">
                Our work is powered by the deepest integration of financial, mathematical and engineering expertise.
              </p>
              <p className="about-text">
                Combining deep trading acumen with cutting-edge analytics and technology, we deliver critical liquidity to the world's most important financial institutions—while helping shape the global markets of tomorrow.
              </p>
            </div>
          </div>
        </div>
      </section>

      {/* Services Section */}
      <section className="services-section" id="services" ref={servicesRef}>
        <div className="container">
          <div className="services-content">
            <div className="services-left">
              <h2 className="section-title">Proven Innovators. Trusted Partners.</h2>
            </div>
            <div className="services-right">
              <p className="services-text">
                Incredible people. Powerful predictive models. Systems that scale. We leverage our strengths to provide liquidity you depend on.
              </p>
              <button className="services-cta" onClick={handleGetStarted}>
                Explore What We Do
              </button>
            </div>
          </div>
        </div>
      </section>

      {/* Stats Section */}
      <section className="stats-section" ref={statsRef}>
        <div className="container">
          <div className="stats-grid">
            <div className="stat-item">
              <div className="stat-number">#1</div>
              <div className="stat-description">Risk Management Platform</div>
            </div>
            <div className="stat-item">
              <div className="stat-number">$652B</div>
              <div className="stat-description">Assets Under Analysis</div>
            </div>
            <div className="stat-item">
              <div className="stat-number">7x</div>
              <div className="stat-description">Faster Risk Assessment</div>
            </div>
          </div>
        </div>
      </section>

      {/* Team Section */}
      <section className="team-section" id="careers" ref={teamRef}>
        <div className="container">
          <div className="team-content">
            <div className="team-left">
              <h2 className="section-title">Extraordinary Talent.<br />Exceptional Teamwork.</h2>
            </div>
            <div className="team-right">
              <p className="team-text">
                Our people succeed as a team. The brightest minds across a range of disciplines collaborate to realize our ambitions. We always seek a better way, and we're just getting started.
              </p>
            </div>
          </div>
          
          <div className="team-stats">
            <div className="team-stat-item">
              <div className="team-stat-number">45%</div>
              <div className="team-stat-description">Team members who hold an advanced degree³</div>
            </div>
            <div className="team-stat-item">
              <div className="team-stat-number">260⁺</div>
              <div className="team-stat-description">PhDs across ~40 fields of study, from applied mathematics and computer engineering to bioinformatics and geophysics³</div>
            </div>
            <div className="team-stat-item">
              <div className="team-stat-number">80⁺</div>
              <div className="team-stat-description">Nationalities represented³</div>
            </div>
          </div>
        </div>
      </section>

      {/* Footer */}
      <footer className="landing-footer">
        <div className="container">
          <p>&copy; 2024 Z-Alpha Securities. All rights reserved.</p>
        </div>
      </footer>
    </div>
  );
};

export default LandingPage;
