import React, { useState } from 'react';

/**
 * Key React Concept: Controlled components — all filter values live in 
 * React state, and every change triggers a new API call.
 */
export default function LogTable({
  logs = [],
  page = 1,
  pages = 1,
  onFilterChange = () => { },
  onPageChange = () => { },
}) {
  const [filters, setFilters] = useState({
    service: '',
    level: '',
    anomaly_threshold: 0.5,
    search: '',
  });
  const [expandedRow, setExpandedRow] = useState(null);

  const handleFilterChange = (name, value) => {
    const newFilters = { ...filters, [name]: value };
    setFilters(newFilters);
    onFilterChange(newFilters);
  };

  const getLevelBadgeColor = (level) => {
    switch (level?.toUpperCase()) {
      case 'ERROR':
        return 'bg-red-900 text-red-200';
      case 'WARN':
        return 'bg-yellow-900 text-yellow-200';
      case 'INFO':
        return 'bg-green-900 text-green-200';
      case 'DEBUG':
        return 'bg-gray-900 text-gray-200';
      default:
        return 'bg-gray-800 text-gray-300';
    }
  };

  const getAnomalyColor = (score) => {
    if (score > 0.7) return 'bg-red-600';
    if (score > 0.4) return 'bg-yellow-600';
    return 'bg-green-600';
  };

  return (
    <div className="bg-surface border border-border rounded-lg">
      {/* Filters */}
      <div className="border-b border-border p-4 grid grid-cols-1 md:grid-cols-4 gap-3">
        <input
          type="text"
          placeholder="Search message..."
          value={filters.search}
          onChange={(e) => handleFilterChange('search', e.target.value)}
          className="px-3 py-2 bg-[#161b22] text-text border border-border rounded text-sm"
        />
        <input
          type="text"
          placeholder="Filter by service..."
          value={filters.service}
          onChange={(e) => handleFilterChange('service', e.target.value)}
          className="px-3 py-2 bg-[#161b22] text-text border border-border rounded text-sm"
        />
        <select
          value={filters.level}
          onChange={(e) => handleFilterChange('level', e.target.value)}
          className="px-3 py-2 bg-[#161b22] text-text border border-border rounded text-sm"
        >
          <option value="">All Levels</option>
          <option value="ERROR">ERROR</option>
          <option value="WARN">WARN</option>
          <option value="INFO">INFO</option>
          <option value="DEBUG">DEBUG</option>
        </select>
        <input
          type="range"
          min="0"
          max="1"
          step="0.1"
          value={filters.anomaly_threshold}
          onChange={(e) => handleFilterChange('anomaly_threshold', parseFloat(e.target.value))}
          className="px-3 py-2 accent-accent"
          title={`Anomaly threshold: ${filters.anomaly_threshold.toFixed(2)}`}
        />
      </div>

      {/* Table */}
      <div className="overflow-x-auto">
        <table className="w-full text-sm">
          <thead className="bg-[#161b22] border-b border-border">
            <tr className="text-muted text-xs uppercase">
              <th className="px-4 py-3 text-left">Timestamp</th>
              <th className="px-4 py-3 text-left">Level</th>
              <th className="px-4 py-3 text-left">Service</th>
              <th className="px-4 py-3 text-left">Message</th>
              <th className="px-4 py-3 text-left">Anomaly Score</th>
            </tr>
          </thead>
          <tbody>
            {logs.length === 0 ? (
              <tr>
                <td colSpan="5" className="px-4 py-6 text-center text-muted">
                  No logs found
                </td>
              </tr>
            ) : (
              logs.map((log, idx) => (
                <React.Fragment key={idx}>
                  <tr
                    onClick={() =>
                      setExpandedRow(expandedRow === idx ? null : idx)
                    }
                    className="border-b border-border hover:bg-[#161b22] cursor-pointer transition"
                  >
                    <td className="px-4 py-3 text-muted text-xs">
                      {new Date(log.timestamp).toLocaleString()}
                    </td>
                    <td className="px-4 py-3">
                      <span
                        className={`px-2 py-1 rounded text-xs font-semibold ${getLevelBadgeColor(
                          log.level
                        )}`}
                      >
                        {log.level}
                      </span>
                    </td>
                    <td className="px-4 py-3 text-text text-sm">
                      {log.service || '—'}
                    </td>
                    <td className="px-4 py-3 text-text max-w-sm truncate">
                      {log.message || log.raw_line || '—'}
                    </td>
                    <td className="px-4 py-3">
                      <div className="w-16 h-6 bg-[#161b22] rounded overflow-hidden">
                        <div
                          className={`h-full transition-all ${getAnomalyColor(
                            log.anomaly_score || 0
                          )}`}
                          style={{
                            width: `${((log.anomaly_score || 0) * 100).toFixed(
                              0
                            )}%`,
                          }}
                        />
                      </div>
                    </td>
                  </tr>
                  {expandedRow === idx && (
                    <tr className="bg-[#161b22] border-b border-border">
                      <td colSpan="5" className="px-4 py-4">
                        <div className="text-xs text-muted font-mono bg-[#0d1117] p-3 rounded border border-border overflow-auto max-h-40">
                          {log.raw_line || JSON.stringify(log, null, 2)}
                        </div>
                      </td>
                    </tr>
                  )}
                </React.Fragment>
              ))
            )}
          </tbody>
        </table>
      </div>

      {/* Pagination */}
      <div className="border-t border-border p-4 flex items-center justify-between">
        <button
          onClick={() => onPageChange(page - 1)}
          disabled={page === 1}
          className="px-4 py-2 bg-[#161b22] text-text rounded border border-border hover:border-accent disabled:opacity-50 transition"
        >
          ← Previous
        </button>
        <span className="text-sm text-muted">
          Page {page} of {pages}
        </span>
        <button
          onClick={() => onPageChange(page + 1)}
          disabled={page === pages}
          className="px-4 py-2 bg-[#161b22] text-text rounded border border-border hover:border-accent disabled:opacity-50 transition"
        >
          Next →
        </button>
      </div>
    </div>
  );
}
