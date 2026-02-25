import React from 'react';

/**
 * Key React Concept: Props pass data from parent to child, like arguments to a function.
 * We receive analytics data and display it as 4 cards.
 */
export default function StatCards({ analytics = {} }) {
  const stats = [
    {
      label: 'Total Logs',
      value: analytics.total_logs || 0,
      icon: '📊',
      color: 'text-blue-400',
    },
    {
      label: 'Errors',
      value: analytics.error_count || 0,
      icon: '❌',
      color: 'text-red-400',
    },
    {
      label: 'Anomalies',
      value: analytics.anomaly_count || 0,
      icon: '⚠️',
      color: 'text-yellow-400',
    },
    {
      label: 'Error Rate',
      value: `${(analytics.error_rate || 0).toFixed(1)}%`,
      icon: '📈',
      color: 'text-orange-400',
    },
  ];

  return (
    <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4 mb-6">
      {stats.map((stat, idx) => (
        <div
          key={idx}
          className="bg-surface border border-border rounded-lg p-6 hover:border-accent transition"
        >
          <div className="flex items-center justify-between mb-3">
            <span className="text-3xl">{stat.icon}</span>
            <span className={`text-xl font-bold ${stat.color}`}>
              {stat.value}
            </span>
          </div>
          <p className="text-muted text-sm">{stat.label}</p>
        </div>
      ))}
    </div>
  );
}
