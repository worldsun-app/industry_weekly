import React, { useState, useEffect, useMemo } from 'react';
import axios from 'axios';
import 'bootstrap/dist/css/bootstrap.min.css';
import './App.css';
import { BrowserRouter as Router, Routes, Route, useNavigate } from 'react-router-dom';
import ReportPage from './ReportPage';
import Navbar from './Navbar';

interface IndustryData {
  industry_name: string;
  pe_today: number | null;
  pe_weekly_change_percent: number | null;
  preview_summary: string;
}

interface ReportData {
  title: string;
  report_part_1: string;
  report_part_2: string;
  preview_summary: string;
}

type SortKey = 'industry_name' | 'pe_today' | 'pe_weekly_change_percent';

interface SortConfig {
  key: SortKey;
  direction: 'ascending' | 'descending';
}

export const IndustryTable: React.FC = () => {
  const [industryData, setIndustryData] = useState<IndustryData[]>([]);
  const [isCollapsed, setIsCollapsed] = useState(false);
  const [sortConfig, setSortConfig] = useState<SortConfig>({ key: 'industry_name', direction: 'ascending' });
  const [hoveredIndustrySummary, setHoveredIndustrySummary] = useState<string | null>(null);
  const [tooltipPosition, setTooltipPosition] = useState<{ x: number; y: number; direction: 'up' | 'down' } | null>(null);
  const navigate = useNavigate();

  useEffect(() => {
    axios.get('http://localhost:8000/api/industry-data')
      .then(response => {
        setIndustryData(response.data.data);
      })
      .catch(error => {
        console.error('Error fetching industry data:', error);
      });
  }, []);

  const sortedIndustryData = useMemo(() => {
    let sortableData = [...industryData];
    if (sortConfig !== null) {
      sortableData.sort((a, b) => {
        const valA = a[sortConfig.key];
        const valB = b[sortConfig.key];

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
    const today = new Date();
    const year = today.getFullYear();
    const month = String(today.getMonth() + 1).padStart(2, '0');
    const day = String(today.getDate()).padStart(2, '0');
    const formattedDate = `${year}-${month}-${day}`;
    navigate(`/report/${industry.industry_name}/${formattedDate}`);
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
        <div className="table-container">
          <div className="table-header">
            <h2>產業列表</h2>
          </div>
          <table className="table b-table fds-all-sectors-overview table-responsive">
            <thead>
              <tr>
                <th className="text-left b-table-sortable-column" onClick={() => requestSort('industry_name')}>
                  Industry{getSortIndicator('industry_name')}
                </th>
                <th className="text-left b-table-sortable-column" onClick={() => requestSort('pe_today')}>
                  Today's PE{getSortIndicator('pe_today')}
                </th>
                <th className="text-left b-table-sortable-column" onClick={() => requestSort('pe_weekly_change_percent')}>
                  Weekly Change{getSortIndicator('pe_weekly_change_percent')}
                </th>
              </tr>
            </thead>
            <tbody>
              {sortedIndustryData.map(industry => (
                <tr 
                  key={industry.industry_name} 
                  onClick={() => handleRowClick(industry)}
                  onMouseEnter={(e) => handleMouseEnter(industry, e)}
                  onMouseLeave={handleMouseLeave}
                >
                  <td>{industry.industry_name}</td>
                  <td>{industry.pe_today ?? 'N/A'}</td>
                  <td className={`${industry.pe_weekly_change_percent === null ? 'text-muted' : industry.pe_weekly_change_percent >= 0 ? 'text-success' : 'text-danger'}`}>
                    {industry.pe_weekly_change_percent !== null ? `${industry.pe_weekly_change_percent.toFixed(2)}%` : 'N/A'}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
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
