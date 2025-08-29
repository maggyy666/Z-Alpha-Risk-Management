import React, { useState } from 'react';
import { ChevronRight, Globe, Menu, X } from 'lucide-react';
import './Navbar.css';

type NavKey = 'who-we-are' | 'risk-solutions' | 'research-insights' | 'careers';

export interface NavbarProps {
  onClientLogin?: () => void;
  onNavigate?: (key: string) => void;
  onBrandClick?: () => void;
}

const navItems: Array<{ key: NavKey; title: string }> = [
  { key: 'who-we-are', title: 'Who We Are' },
  { key: 'risk-solutions', title: 'Risk Solutions' },
  { key: 'research-insights', title: 'Research & Insights' },
  { key: 'careers', title: 'Careers' },
];

export const Navbar: React.FC<NavbarProps> = ({ onClientLogin, onNavigate, onBrandClick }) => {
  const [isMenuOpen, setIsMenuOpen] = useState(false);
  const [hoveredNav, setHoveredNav] = useState<NavKey | null>(null);

  const handleItemClick = (key: NavKey) => {
    if (onNavigate) onNavigate(key);
  };

  return (
    <nav className="landing-page-navbar">
      <div className="landing-page-container">
        <div className="landing-page-navbar-row">
          {/* Brand */}
          <button className="landing-page-brand" onClick={onBrandClick} aria-label="Home">
            <div className="landing-page-logo">
              <span className="landing-page-logo-symbol">α</span>
              <div className="landing-page-logo-text">
                <span className="landing-page-logo-main">Z-ALPHA</span>
                <span className="landing-page-logo-separator">|</span>
                <span className="landing-page-logo-sub">Securities</span>
              </div>
            </div>
          </button>

          {/* Desktop nav */}
          <div className="landing-page-desktop-nav">
            {navItems.map((item) => (
              <a
                key={item.key}
                href="#"
                onClick={(e) => {
                  e.preventDefault();
                  handleItemClick(item.key);
                }}
                onMouseEnter={() => setHoveredNav(item.key)}
                onMouseLeave={() => setHoveredNav(null)}
                className={`landing-page-nav-link ${hoveredNav === item.key ? 'hover' : ''}`}
              >
                {item.title}
              </a>
            ))}
          </div>

          {/* Desktop right */}
          <div className="landing-page-desktop-right">
            <div className="landing-page-lang">
              <Globe size={16} />
              <span>EN</span>
              <ChevronRight size={12} />
            </div>
            <button className="landing-page-login-btn" onClick={onClientLogin}>Client Portal</button>
          </div>

          {/* Mobile menu button */}
          <div className="landing-page-mobile-menu-btn">
            <button
              onClick={() => setIsMenuOpen(!isMenuOpen)}
              aria-label="Toggle menu"
            >
              {isMenuOpen ? <X size={24} /> : <Menu size={24} />}
            </button>
          </div>
        </div>

        {/* Mobile nav */}
        {isMenuOpen && (
          <div className="landing-page-mobile-nav">
            {navItems.map((item) => (
              <a
                key={item.key}
                href="#"
                onClick={(e) => {
                  e.preventDefault();
                  setIsMenuOpen(false);
                  handleItemClick(item.key);
                }}
                className="landing-page-nav-link"
              >
                {item.title}
              </a>
            ))}
            <div className="mobile-actions">
              <div className="lang">
                <Globe size={16} />
                <span>EN</span>
                <ChevronRight size={12} />
              </div>
              <button className="login-btn" onClick={onClientLogin}>Client Portal</button>
            </div>
          </div>
        )}
      </div>
    </nav>
  );
};

export default Navbar;


