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
    <nav className="zalpha-navbar">
      <div className="container">
        <div className="navbar-row">
          {/* Brand */}
          <button className="brand" onClick={onBrandClick} aria-label="Home">
            <div className="logo">
              <span className="logo-symbol">ρ</span>
              <div className="logo-text">
                <span className="logo-main">Z-ALPHA</span>
                <span className="logo-separator">|</span>
                <span className="logo-sub">Securities</span>
              </div>
            </div>
          </button>

          {/* Desktop nav */}
          <div className="desktop-nav">
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
                className={`nav-link ${hoveredNav === item.key ? 'hover' : ''}`}
              >
                {item.title}
              </a>
            ))}
          </div>

          {/* Desktop right */}
          <div className="desktop-right">
            <div className="lang">
              <Globe size={16} />
              <span>EN</span>
              <ChevronRight size={12} />
            </div>
            <button className="login-btn" onClick={onClientLogin}>Client Portal</button>
          </div>

          {/* Mobile menu button */}
          <div className="mobile-menu-btn">
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
          <div className="mobile-nav">
            {navItems.map((item) => (
              <a
                key={item.key}
                href="#"
                onClick={(e) => {
                  e.preventDefault();
                  setIsMenuOpen(false);
                  handleItemClick(item.key);
                }}
                className="nav-link"
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


