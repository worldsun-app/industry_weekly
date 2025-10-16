import React, { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';
import './Navbar.css';

const Navbar: React.FC = () => {
  const [isScrolled, setIsScrolled] = useState(false);

  useEffect(() => {
    const handleScroll = () => {
      if (window.scrollY > 10) {
        setIsScrolled(true);
      } else {
        setIsScrolled(false);
      }
    };

    window.addEventListener('scroll', handleScroll);

    // Cleanup function to remove the event listener
    return () => {
      window.removeEventListener('scroll', handleScroll);
    };
  }, []);

  return (
    <nav className={isScrolled ? 'navbar scrolled' : 'navbar'}>
      <div className="navbar-container">
        <Link to="/" className="navbar-logo">
          WSGFO
        </Link>
        <ul className="nav-menu">
          <li className="nav-item">
            <a href="#" className="nav-links">Dashboard</a>
          </li>
          <li className="nav-item">
            <a href="#" className="nav-links">Reports</a>
          </li>
          <li className="nav-item">
            <a href="#" className="nav-links">Sectors</a>
          </li>
          <li className="nav-item">
            <a href="#" className="nav-links">Screener</a>
          </li>
          <li className="nav-item">
            <a href="#" className="nav-links">Pricing</a>
          </li>
          <li className="nav-item">
            <a href="#" className="nav-links">Blog</a>
          </li>
        </ul>
        <div className="nav-buttons">
          <button className="nav-btn login">Login</button>
          <button className="nav-btn signup">Sign Up</button>
        </div>
      </div>
    </nav>
  );
};

export default Navbar;
