import React, { useState, useEffect, useMemo } from 'react';
import axios from 'axios';
import 'bootstrap/dist/css/bootstrap.min.css';
import './App.css';
import { BrowserRouter as Router, Routes, Route, useNavigate } from 'react-router-dom';
import ReportPage from './ReportPage';
import Navbar from './Navbar';
import PeRatioBar from './PeRatioBar'; // Import the new component

interface EtfRoi {
  '1D': number | null;
  '5D': number | null;
  '1M': number | null;
  '3M': number | null;
  '6M': number | null;
  '1Y': number | null;
  'pe_today': number | null;
}

interface IndustryData {
  industry_name: string;
  preview_summary: string;
  etf_roi: EtfRoi | null;
  pe_high_1y: number | null;
  pe_low_1y: number | null;
  market_breadth_200d: number | null; // Add market breadth
}

interface ReportData {
  title: string;
  report_part_1: string;
  report_part_2: string;
  preview_summary: string;
}

type SortKey = 'industry_name' | '1D' | '5D' | '1M' | '3M' | '6M' | '1Y' | 'pe_today' | 'market_breadth_200d';

interface SortConfig {
  key: SortKey;
  direction: 'ascending' | 'descending';
}

// Helper component for colored ROI values
const RoiCell: React.FC<{ value: number | null | undefined, isPercentage?: boolean, hasColor?: boolean }> = ({ value, isPercentage = true, hasColor = true }) => {
  if (value === null || value === undefined) {
    return <span className="text-muted">N/A</span>;
  }
  const className = hasColor && isPercentage ? (value >= 0 ? 'text-success' : 'text-danger') : '';
  const displayValue = isPercentage ? `${value.toFixed(2)}%` : value.toFixed(2);
  return <span className={className}>{displayValue}</span>;
};

export const IndustryTable: React.FC = () => {
  const [industryData, setIndustryData] = useState<IndustryData[]>([]);
  const [sp500Data, setSp500Data] = useState<IndustryData | null>(null);
  const [isCollapsed, setIsCollapsed] = useState(false);
  const [sortConfig, setSortConfig] = useState<SortConfig>({ key: 'industry_name', direction: 'ascending' });
  const [hoveredIndustrySummary, setHoveredIndustrySummary] = useState<string | null>(null);
  const [tooltipPosition, setTooltipPosition] = useState<{ x: number; y: number; direction: 'up' | 'down' } | null>(null);
  const navigate = useNavigate();

  useEffect(() => {
    axios.get('http://localhost:8000/api/industry-data')
      .then(response => {
        const allData = response.data.data;
        const spData = allData.find((d: IndustryData) => d.industry_name === 'S&P 500');
        const otherIndustries = allData.filter((d: IndustryData) => d.industry_name !== 'S&P 500');
        
        setSp500Data(spData || null);
        setIndustryData(otherIndustries);
      })
      .catch(error => {
        console.error('Error fetching industry data:', error);
      });
  }, []);

  const sortedIndustryData = useMemo(() => {
    let sortableData = [...industryData];
    if (sortConfig !== null) {
      sortableData.sort((a, b) => {
        let valA: number | string | null = null;
        let valB: number | string | null = null;

        if (sortConfig.key === 'industry_name') {
          valA = a.industry_name;
          valB = b.industry_name;
        } else if (sortConfig.key === 'pe_today') {
          valA = a.etf_roi?.pe_today ?? null;
          valB = b.etf_roi?.pe_today ?? null;
        } else if (sortConfig.key === 'market_breadth_200d') {
          valA = a.market_breadth_200d ?? null;
          valB = b.market_breadth_200d ?? null;
        } else { // For other ROI keys
          valA = a.etf_roi ? a.etf_roi[sortConfig.key as keyof EtfRoi] : null;
          valB = b.etf_roi ? b.etf_roi[sortConfig.key as keyof EtfRoi] : null;
        }

        if (valA === null) return 1;
        if (valB === null) return -1;
        
        if (valA < valB) {
          return sortConfig.direction === 'ascending' ? -1 : 1;
        }
        if (valA > valB) {
          return sortConfig.direction === 'ascending' ? 1 : -1;
        }
        return 0;
      });
    }
    return sortableData;
  }, [industryData, sortConfig]);

  const requestSort = (key: SortKey) => {
    let direction: 'ascending' | 'descending' = 'ascending';
    if (sortConfig.key === key && sortConfig.direction === 'ascending') {
      direction = 'descending';
    }
    setSortConfig({ key, direction });
  };

  const getSortIndicator = (key: SortKey) => {
    if (sortConfig.key !== key) {
      return null;
    }
    return sortConfig.direction === 'ascending' ? ' ▲' : ' ▼';
  };

  const toggleCollapse = () => {
    setIsCollapsed(!isCollapsed);
  };

  const handleRowClick = (industry: IndustryData) => {
    navigate(`/report/${industry.industry_name}/latest`);
  };

  const handleMouseEnter = (industry: IndustryData, event: React.MouseEvent) => {
    const { clientX, clientY } = event;
    const direction = clientY > window.innerHeight / 2 ? 'up' : 'down';
    setHoveredIndustrySummary(industry.preview_summary);
    setTooltipPosition({ x: clientX, y: clientY, direction });
  };

  const handleMouseLeave = () => {
    setHoveredIndustrySummary(null);
    setTooltipPosition(null);
  };

  const tooltipStyle: React.CSSProperties = useMemo(() => {
    if (!tooltipPosition) return {};
    
    const { x, y, direction } = tooltipPosition;
    const top = direction === 'up' ? y - 15 : y + 15;
    const transform = direction === 'up' ? 'translateY(-100%)' : 'translateY(0)';

    return {
      left: x + 15,
      top: top,
      transform: transform,
      position: 'fixed', // Use fixed position to avoid being affected by scroll
    };
  }, [tooltipPosition]);

  return (
    <div>
      <div className='hero-section'>
        <h1>產業週報</h1>
        <p>您每週的產業動態與市場洞察</p>
      </div>
      <div className="container mt-5">
        {sp500Data && sp500Data.etf_roi && (
          <div className="sp500-container">
            <h4>S&P 500 (SPY)</h4>
            <div className="roi-grid">
              <div className="roi-item">
                <span className="roi-label">1D</span>
                <span className={`roi-value ${sp500Data.etf_roi['1D']! >= 0 ? 'text-success' : 'text-danger'}`}>{sp500Data.etf_roi['1D']?.toFixed(2)}%</span>
              </div>
              <div className="roi-item">
                <span className="roi-label">5D</span>
                <span className={`roi-value ${sp500Data.etf_roi['5D']! >= 0 ? 'text-success' : 'text-danger'}`}>{sp500Data.etf_roi['5D']?.toFixed(2)}%</span>
              </div>
              <div className="roi-item">
                <span className="roi-label">1M</span>
                <span className={`roi-value ${sp500Data.etf_roi['1M']! >= 0 ? 'text-success' : 'text-danger'}`}>{sp500Data.etf_roi['1M']?.toFixed(2)}%</span>
              </div>
              <div className="roi-item">
                <span className="roi-label">3M</span>
                <span className={`roi-value ${sp500Data.etf_roi['3M']! >= 0 ? 'text-success' : 'text-danger'}`}>{sp500Data.etf_roi['3M']?.toFixed(2)}%</span>
              </div>
              <div className="roi-item">
                <span className="roi-label">6M</span>
                <span className={`roi-value ${sp500Data.etf_roi['6M']! >= 0 ? 'text-success' : 'text-danger'}`}>{sp500Data.etf_roi['6M']?.toFixed(2)}%</span>
              </div>
              <div className="roi-item">
                <span className="roi-label">1Y</span>
                <span className={`roi-value ${sp500Data.etf_roi['1Y']! >= 0 ? 'text-success' : 'text-danger'}`}>{sp500Data.etf_roi['1Y']?.toFixed(2)}%</span>
              </div>
            </div>
          </div>
        )}
        <div className="table-container">
          <div className="table-header" onClick={toggleCollapse} style={{ cursor: 'pointer' }}>
            <h2>產業列表 {isCollapsed ? '▶' : '▼'}</h2>
          </div>
          {!isCollapsed && (
            <table className="table b-table fds-all-sectors-overview table-responsive">
              <thead>
                <tr>
                  <th className="text-left b-table-sortable-column" onClick={(e) => { e.stopPropagation(); requestSort('industry_name'); }}>
                    Industry{getSortIndicator('industry_name')}
                  </th>
                  <th className="text-left b-table-sortable-column" onClick={(e) => { e.stopPropagation(); requestSort('1D'); }}>
                    1D{getSortIndicator('1D')}
                  </th>
                  <th className="text-left b-table-sortable-column" onClick={(e) => { e.stopPropagation(); requestSort('5D'); }}>
                    5D{getSortIndicator('5D')}
                  </th>
                  <th className="text-left b-table-sortable-column" onClick={(e) => { e.stopPropagation(); requestSort('1M'); }}>
                    1M{getSortIndicator('1M')}
                  </th>
                  <th className="text-left b-table-sortable-column" onClick={(e) => { e.stopPropagation(); requestSort('3M'); }}>
                    3M{getSortIndicator('3M')}
                  </th>
                  <th className="text-left b-table-sortable-column" onClick={(e) => { e.stopPropagation(); requestSort('6M'); }}>
                    6M{getSortIndicator('6M')}
                  </th>
                  <th className="text-left b-table-sortable-column" onClick={(e) => { e.stopPropagation(); requestSort('1Y'); }}>
                    1Y{getSortIndicator('1Y')}
                  </th>
                  <th className="text-left b-table-sortable-column" onClick={(e) => { e.stopPropagation(); requestSort('pe_today'); }}>
                    PE Range (1Y){getSortIndicator('pe_today')}
                  </th>
                  <th className="text-left b-table-sortable-column" onClick={(e) => { e.stopPropagation(); requestSort('market_breadth_200d'); }}>
                    Market Breadth (200d){getSortIndicator('market_breadth_200d')}
                  </th>
                </tr>
              </thead>
              <tbody>
                {sortedIndustryData.map(industry => (
                  <tr key={industry.industry_name} onClick={() => handleRowClick(industry)}>
                    <td onMouseEnter={(e) => handleMouseEnter(industry, e)} onMouseLeave={handleMouseLeave}>{industry.industry_name}</td>
                    <td onMouseEnter={(e) => handleMouseEnter(industry, e)} onMouseLeave={handleMouseLeave}><RoiCell value={industry.etf_roi ? industry.etf_roi['1D'] : null} /></td>
                    <td onMouseEnter={(e) => handleMouseEnter(industry, e)} onMouseLeave={handleMouseLeave}><RoiCell value={industry.etf_roi ? industry.etf_roi['5D'] : null} /></td>
                    <td onMouseEnter={(e) => handleMouseEnter(industry, e)} onMouseLeave={handleMouseLeave}><RoiCell value={industry.etf_roi ? industry.etf_roi['1M'] : null} /></td>
                    <td onMouseEnter={(e) => handleMouseEnter(industry, e)} onMouseLeave={handleMouseLeave}><RoiCell value={industry.etf_roi ? industry.etf_roi['3M'] : null} /></td>
                    <td onMouseEnter={(e) => handleMouseEnter(industry, e)} onMouseLeave={handleMouseLeave}><RoiCell value={industry.etf_roi ? industry.etf_roi['6M'] : null} /></td>
                    <td onMouseEnter={(e) => handleMouseEnter(industry, e)} onMouseLeave={handleMouseLeave}><RoiCell value={industry.etf_roi ? industry.etf_roi['1Y'] : null} /></td>
                    <td className="pe-range-cell">
                      <PeRatioBar 
                        pe_today={industry.etf_roi?.pe_today}
                        pe_low_1y={industry.pe_low_1y}
                        pe_high_1y={industry.pe_high_1y}
                      />
                    </td>
                    <td onMouseEnter={(e) => handleMouseEnter(industry, e)} onMouseLeave={handleMouseLeave}>
                      <RoiCell value={industry.market_breadth_200d} hasColor={false} />
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          )}
        </div>
      </div>

      {hoveredIndustrySummary && (
        <div className="tooltip-custom" style={tooltipStyle}>
          {hoveredIndustrySummary}
        </div>
      )}
    </div>
  );
}

function App() {
  return (
    <Router>
      <Navbar />
      <Routes>
        <Route path="/" element={<IndustryTable />} />
        <Route path="/report/:industryName/:reportDate" element={<ReportPage />} />
      </Routes>
    </Router>
  );
}

export default App;
