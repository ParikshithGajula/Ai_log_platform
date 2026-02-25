import React, { useState, useEffect, useRef } from 'react';
import { getAnalytics, getLogs } from './api/client';
import StatCards from './components/StatCards';
import AnomalyChart from './components/AnomalyChart';
import LogUploader from './components/LogUploader';
import LogTable from './components/LogTable';
import AskAI from './components/AskAI';

const API_URL = import.meta.env.VITE_API_URL || 'http://localhost:8001';

export default function App() {
  const [activeTab, setActiveTab] = useState('dashboard');
  const [analytics, setAnalytics] = useState({});
  const [logs, setLogs] = useState([]);
  const [total, setTotal] = useState(0);
  const [page, setPage] = useState(1);
  const [pages, setPages] = useState(1);
  const [filters, setFilters] = useState({});
  const [health, setHealth] = useState(false);
  const analyticsIntervalRef = useRef(null);

  // Fetch analytics data
  const fetchAnalytics = async () => {
    try {
      const data = await getAnalytics();
      setAnalytics(data);
    } catch (error) {
      console.error('Error fetching analytics:', error);
    }
  };

  // Fetch logs with filters
  const fetchLogs = async (pageNum = 1, filtersObj = filters) => {
    try {
      const response = await getLogs({
        page: pageNum,
        ...filtersObj,
      });
      setLogs(response.logs || []);
      setTotal(response.total || 0);
      setPage(pageNum);
      setPages(response.pages || 1);
    } catch (error) {
      console.error('Error fetching logs:', error);
    }
  };

  // Check backend health
  const checkHealth = async () => {
    try {
      const response = await fetch(`${API_URL}/health`);
      setHealth(response.ok);
    } catch {
      setHealth(false);
    }
  };

  // On mount: fetch initial data and set up auto-refresh
  useEffect(() => {
    fetchAnalytics();
    fetchLogs(1);
    checkHealth();

    // Auto-refresh analytics every 30 seconds
    analyticsIntervalRef.current = setInterval(() => {
      fetchAnalytics();
      checkHealth();
    }, 30000);

    return () => {
      if (analyticsIntervalRef.current) {
        clearInterval(analyticsIntervalRef.current);
      }
    };
  }, []);

  // Handle uploader completion
  const handleUploadComplete = () => {
    fetchAnalytics();
    fetchLogs(1);
  };

  // Handle filter changes
  const handleFilterChange = (newFilters) => {
    setFilters(newFilters);
    fetchLogs(1, newFilters);
  };

  // Handle page changes
  const handlePageChange = (newPage) => {
    fetchLogs(newPage, filters);
  };

  return (
    <div className="min-h-screen bg-bg text-text">
      {/* Navbar */}
      <nav className="bg-surface border-b border-border sticky top-0 z-50">
        <div className="max-w-7xl mx-auto px-4 py-4 flex items-center justify-between">
          <div className="flex items-center gap-3">
            <span className="text-2xl">⚡</span>
            <h1 className="text-xl font-bold">AI Log Platform</h1>
          </div>

          {/* Health indicator */}
          <div className="flex items-center gap-2">
            <span
              className={`inline-block w-3 h-3 rounded-full ${health ? 'bg-success animate-pulse' : 'bg-error'
                }`}
            />
            <span className="text-xs text-muted">Backend {health ? 'Online' : 'Offline'}</span>
          </div>
        </div>

        {/* Tabs */}
        <div className="border-t border-border">
          <div className="max-w-7xl mx-auto px-4 flex gap-0">
            {[
              { id: 'dashboard', label: 'Dashboard' },
              { id: 'logs', label: 'Logs' },
              { id: 'askai', label: 'Ask AI' },
            ].map((tab) => (
              <button
                key={tab.id}
                onClick={() => setActiveTab(tab.id)}
                className={`px-6 py-3 border-b-2 transition ${activeTab === tab.id
                    ? 'border-accent text-accent font-semibold'
                    : 'border-transparent text-muted hover:text-text'
                  }`}
              >
                {tab.label}
              </button>
            ))}
          </div>
        </div>
      </nav>

      {/* Main content */}
      <main className="max-w-7xl mx-auto px-4 py-8">
        {/* Dashboard Tab */}
        {activeTab === 'dashboard' && (
          <div>
            <StatCards analytics={analytics} />
            <AnomalyChart data={analytics.hourly_data || []} />
          </div>
        )}

        {/* Logs Tab */}
        {activeTab === 'logs' && (
          <div className="space-y-6">
            <LogUploader onComplete={handleUploadComplete} />
            <LogTable
              logs={logs}
              total={total}
              page={page}
              pages={pages}
              onFilterChange={handleFilterChange}
              onPageChange={handlePageChange}
            />
          </div>
        )}

        {/* Ask AI Tab */}
        {activeTab === 'askai' && <AskAI />}
      </main>
    </div>
  );
}
