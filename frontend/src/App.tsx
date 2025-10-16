import React, { useState, useEffect, useMemo } from 'react';
import axios from 'axios';
import 'bootstrap/dist/css/bootstrap.min.css';
import './App.css';

interface IndustryData {
  industry_name: string;
  pe_today: number | null;
  pe_weekly_change_percent: number | null;
  preview_summary: string; // Add preview_summary to IndustryData
}

interface ReportData {
  title: string;
  report_part_1: string;
  report_part_2: string;
  preview_summary: string;
}

type SortKey = 'industry_name' | 'pe_today' | 'pe_weekly_change_percent';

function App() {
  const [industryData, setIndustryData] = useState<IndustryData[]>([]);
  const [isCollapsed, setIsCollapsed] = useState(false);
  const [sortKey, setSortKey] = useState<SortKey>('industry_name');
  const [selectedIndustry, setSelectedIndustry] = useState<IndustryData | null>(null);
  const [report, setReport] = useState<ReportData | null>(null);
  const [showModal, setShowModal] = useState(false);
  const [hoveredIndustrySummary, setHoveredIndustrySummary] = useState<string | null>(null);
  const [tooltipPosition, setTooltipPosition] = useState<{ x: number; y: number } | null>(null);

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
    sortableData.sort((a, b) => {
      if (sortKey === 'industry_name') {
        return a.industry_name.localeCompare(b.industry_name);
      } else {
        const valA = a[sortKey];
        const valB = b[sortKey];
        if (valA === null) return 1;
        if (valB === null) return -1;
        return (valB as number) - (valA as number);
      }
    });
    return sortableData;
  }, [industryData, sortKey]);

  const toggleCollapse = () => {
    setIsCollapsed(!isCollapsed);
  };

  const handleCardClick = (industry: IndustryData) => {
    setSelectedIndustry(industry);
    const today = new Date();
    const year = today.getFullYear();
    const month = String(today.getMonth() + 1).padStart(2, '0');
    const day = String(today.getDate()).padStart(2, '0');
    const formattedDate = `${year}-${month}-${day}`;

    axios.get(`http://localhost:8000/api/industry-reports/${industry.industry_name}/${formattedDate}`)
      .then(response => {
        setReport(response.data);
        setShowModal(true);
      })
      .catch(error => {
        console.error('Error fetching industry report:', error);
      });
  };

  const handleMouseEnter = (industry: IndustryData, event: React.MouseEvent) => {
    setHoveredIndustrySummary(industry.preview_summary);
    setTooltipPosition({ x: event.clientX, y: event.clientY });
  };

  const handleMouseLeave = () => {
    setHoveredIndustrySummary(null);
    setTooltipPosition(null);
  };

  const handleCloseModal = () => {
    setShowModal(false);
    setSelectedIndustry(null);
    setReport(null);
  };

  return (
    <div>
      <div className='hero-section'>
        <h1>產業週報</h1>
        <p>您每週的產業動態與市場洞察</p>
      </div>
      <div className="container mt-5">
        <div className="card">
          <div className="card-header">
            <div className="d-flex justify-content-between align-items-center">
              <h2 onClick={toggleCollapse} style={{ cursor: 'pointer' }}>產業</h2>
              <div className="col-md-3">
                <select className="form-select" value={sortKey} onChange={(e) => setSortKey(e.target.value as SortKey)}>
                  <option value="industry_name">字母排序</option>
                  <option value="pe_weekly_change_percent">週漲跌幅</option>
                  <option value="pe_today">今日PE</option>
                </select>
              </div>
            </div>
          </div>
          {!isCollapsed && (
            <div className="card-body">
              <div className="row">
                {sortedIndustryData.map(industry => (
                  <div className="col-md-4 mb-4" key={industry.industry_name}>
                    <div 
                      className="card h-100 industry-card" 
                      onClick={() => handleCardClick(industry)}
                      onMouseEnter={(e) => handleMouseEnter(industry, e)}
                      onMouseLeave={handleMouseLeave}
                    >
                      <div className="card-body">
                        <h5 className="card-title">{industry.industry_name}</h5>
                        <div className="d-flex justify-content-between">
                          <span>今日PE:</span>
                          <span>{industry.pe_today ?? 'N/A'}</span>
                        </div>
                        <div className="d-flex justify-content-between">
                          <span>週漲跌幅:</span>
                          <span className={`${industry.pe_weekly_change_percent === null ? 'text-muted' : industry.pe_weekly_change_percent >= 0 ? 'text-success' : 'text-danger'}`}>
                            {industry.pe_weekly_change_percent !== null ? `${industry.pe_weekly_change_percent.toFixed(2)}%` : 'N/A'}
                          </span>
                        </div>
                      </div>
                    </div>
                  </div>
                ))}
              </div>
            </div>
          )}
        </div>
      </div>

      {hoveredIndustrySummary && tooltipPosition && (
        <div className="tooltip-custom" style={{ top: tooltipPosition.y + 10, left: tooltipPosition.x + 10 }}>
          {hoveredIndustrySummary}
        </div>
      )}

      {showModal && report && (
        <div className="modal show d-block" tabIndex={-1}>
          <div className="modal-dialog modal-lg">
            <div className="modal-content">
              <div className="modal-header">
                <h5 className="modal-title">{report.title}</h5>
                <button type="button" className="btn-close" onClick={handleCloseModal}></button>
              </div>
              <div className="modal-body">
                <h6>預覽摘要</h6>
                <p>{report.preview_summary}</p>
                <hr />
                <h6>報告第一部分</h6>
                <p>{report.report_part_1}</p>
                <hr />
                <h6>報告第二部分</h6>
                <p>{report.report_part_2}</p>
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}

export default App;
