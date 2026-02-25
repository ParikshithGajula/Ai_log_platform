import React from 'react';
import {
  LineChart,
  Line,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
  ReferenceLine,
  ResponsiveContainer,
} from 'recharts';

/**
 * Key React Concept: Recharts takes your array of objects and handles all the 
 * drawing — you just describe what you want with JSX components.
 * ResponsiveContainer makes the chart fill its parent width automatically.
 */
export default function AnomalyChart({ data = [] }) {
  // If no data, show a placeholder
  if (!data || data.length === 0) {
    return (
      <div className="bg-surface border border-border rounded-lg p-6 h-80 flex items-center justify-center">
        <p className="text-muted">No data available for chart</p>
      </div>
    );
  }

  return (
    <div className="bg-surface border border-border rounded-lg p-6">
      <h3 className="text-lg font-semibold mb-4">Log Volume & Errors</h3>
      <ResponsiveContainer width="100%" height={300}>
        <LineChart data={data}>
          <CartesianGrid strokeDasharray="3 3" stroke="#21262d" />
          <XAxis dataKey="hour" stroke="#8b949e" />
          <YAxis stroke="#8b949e" />
          <Tooltip
            contentStyle={{
              backgroundColor: '#161b22',
              border: '1px solid #21262d',
              borderRadius: '4px',
              color: '#e6edf3',
            }}
          />
          <Legend />
          <ReferenceLine
            y={0.7}
            stroke="#fbbf24"
            strokeDasharray="5 5"
            label="Anomaly Threshold"
          />
          <Line
            type="monotone"
            dataKey="total_logs"
            stroke="#0ea5e9"
            name="Total Logs"
            dot={false}
            strokeWidth={2}
          />
          <Line
            type="monotone"
            dataKey="error_count"
            stroke="#ef4444"
            name="Error Count"
            dot={false}
            strokeWidth={2}
          />
        </LineChart>
      </ResponsiveContainer>
    </div>
  );
}
