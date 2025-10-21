import React, { useState, useEffect, useMemo } from 'react';
import { Link, useParams } from 'react-router-dom';
import axios from 'axios';
import './ReportPage.css';

interface Stock {
  symbol: string;
  price: number;
  marketCap: number;
  changePercentage: number;
}

interface FullIndustryData {
  industry_name: string;
  preview_summary: string;
  etf_roi: any; // Simplified for now
  top_stocks?: Stock[];
}

interface ReportData {
  title: string;
  generated_at: string;
  report_part_1: string;
  report_part_2: string;
  preview_summary: string;
}

// Helper function to format market cap
const formatMarketCap = (cap: number) => {
  if (cap >= 1_000_000_000_000) {
    return `${(cap / 1_000_000_000_000).toFixed(2)}T`;
  }
  if (cap >= 1_000_000_000) {
    return `${(cap / 1_000_000_000).toFixed(2)}B`;
  }
  if (cap >= 1_000_000) {
    return `${(cap / 1_000_000).toFixed(2)}M`;
  }
  return cap.toString();
};

const ReportPage: React.FC = () => {
  const { industryName, reportDate } = useParams<{ industryName: string; reportDate: string }>();
  
  // State
  const [report, setReport] = useState<ReportData | null>(null);
  const [allIndustries, setAllIndustries] = useState<FullIndustryData[]>([]);
  const [currentIndustry, setCurrentIndustry] = useState<FullIndustryData | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [readingTime, setReadingTime] = useState(0);
  const [scrollProgress, setScrollProgress] = useState(0);

  // Helper to format date directly in render
  const getFormattedDate = (dateString: string | undefined) => {
    if (!dateString) return '';
    try {
      const date = new Date(dateString);
      const year = date.getFullYear();
      const month = String(date.getMonth() + 1).padStart(2, '0');
      const day = String(date.getDate()).padStart(2, '0');
      return `${year}-${month}-${day}`;
    } catch (e) {
      return ''; // Return empty string if date is invalid
    }
  };

  // Scroll handler
  const handleScroll = () => {
    const scrollTop = window.scrollY;
    const docHeight = document.documentElement.scrollHeight - window.innerHeight;
    const scrolled = (scrollTop / docHeight) * 100;
    setScrollProgress(scrolled);
  };

  useEffect(() => {
    window.addEventListener('scroll', handleScroll);
    return () => window.removeEventListener('scroll', handleScroll);
  }, []);

  // Data fetching effect
  useEffect(() => {
    setLoading(true);

    const reportApiUrl = reportDate === 'latest'
      ? `http://localhost:8000/api/industry-reports/${industryName}/latest`
      : `http://localhost:8000/api/industry-reports/${industryName}/${reportDate}`;

    const fetchReport = axios.get(reportApiUrl);
    const fetchAllIndustries = axios.get('http://localhost:8000/api/industry-data');

    Promise.all([fetchReport, fetchAllIndustries])
      .then(([reportResponse, industriesResponse]) => {
        const reportData = reportResponse.data;
        console.log("Received report data from backend:", reportData); // Log the received data
        const allIndustriesData = industriesResponse.data.data;
        const filteredIndustries = allIndustriesData.filter((ind: FullIndustryData) => ind.industry_name !== 'S&P 500');

        setReport(reportData);
        setAllIndustries(filteredIndustries);

        // Find and set the current industry's full data
        const foundIndustry = allIndustriesData.find((ind: FullIndustryData) => ind.industry_name === industryName);
        setCurrentIndustry(foundIndustry || null);

        // Calculate reading time
        const wordsPerMinute = 225;
        const text = reportData.report_part_1 + " " + reportData.report_part_2;
        const wordCount = text.split(/\s+/).length;
        const time = Math.ceil(wordCount / wordsPerMinute);
        setReadingTime(time);
        
        setLoading(false);
      })
      .catch(err => {
        console.error('Error fetching data:', err);
        setError('Failed to load the report. Please try again later.');
        setLoading(false);
      });

  }, [industryName, reportDate]);

  if (loading && !report) {
    return <div className="report-page-container">Loading...</div>;
  }

  if (error) {
    return <div className="report-page-container">{error}</div>;
  }

  return (
    <>
      <div className="progress-bar" style={{ width: `${scrollProgress}%` }} />
      <div className="report-page-container">
        {/* Left Sidebar */}
        <aside className="sidebar left-sidebar">
          <h4>所有產業</h4>
          <ul className="industry-list">
            {allIndustries.map(industry => (
              <li key={industry.industry_name} className={industry.industry_name === industryName ? 'active' : ''}>
                <Link to={`/report/${industry.industry_name}/latest`}>
                  {industry.industry_name}
                </Link>
              </li>
            ))}
          </ul>
        </aside>

        {/* Main Content */}
        <main className="report-main-content">
          <Link to="/" className="back-link">← 返回產業總覽</Link>
          {report ? (
            <article className="report-content">
              <header>
                <h1>{industryName} 產業週報</h1>
                <div className="report-meta">
                  <span className="meta-item">By WSGFO Analyst</span>
                  <span className="meta-item">{getFormattedDate(report?.generated_at)}</span>
                  <span className="meta-item">{readingTime} min read</span>
                </div>
                <p className="report-summary">{report.preview_summary}</p>
              </header>
              <section>
                <p>{report.report_part_1}</p>
                <p>{report.report_part_2}</p>
              </section>
            </article>
          ) : (
            <div>Loading report...</div>
          )}
        </main>

        {/* Right Sidebar */}
        <aside className="sidebar right-sidebar">
          <h4>產業重點個股</h4>
          {currentIndustry && currentIndustry.top_stocks && currentIndustry.top_stocks.length > 0 ? (
            <table className="top-stocks-table">
              <thead>
                <tr>
                  <th>公司</th>
                  <th>市值</th>
                  <th>股價</th>
                </tr>
              </thead>
              <tbody>
                {currentIndustry.top_stocks.map(stock => (
                  <tr key={stock.symbol}>
                    <td>{stock.symbol}</td>
                    <td>{formatMarketCap(stock.marketCap)}</td>
                    <td className={stock.changePercentage >= 0 ? 'text-success' : 'text-danger'}>
                      ${stock.price?.toFixed(2) ?? 'N/A'}
                      <span style={{ marginLeft: '5px' }}>
                        ({stock.changePercentage >= 0 ? '▲' : '▼'}{stock.changePercentage?.toFixed(2) ?? 'N/A'}%)
                      </span>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          ) : (
            <p className="no-stocks-message">暫無個股資料</p>
          )}
        </aside>
      </div>
    </>
  );
};
export default ReportPage; 