'use client';

import React from 'react';
import {
  BarChart,
  Bar,
  PieChart,
  Pie,
  LineChart,
  Line,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
  ResponsiveContainer,
  Cell,
  Label,
} from 'recharts';

interface ChartData {
  status: string;
  chart_type: string;
  title: string;
  chart_config: {
    type: string;
    data: any[];
    dataKey?: string;
    nameKey?: string;
    colors?: string[];
    bars?: Array<{ dataKey: string; name: string; color: string }>;
    lines?: Array<{ dataKey: string; name: string; color: string }>;
    xAxisKey?: string;
    yAxisLabel?: string;
    yAxisDomain?: [number, number];
    legend?: boolean;
    tooltip?: boolean;
    grid?: boolean;
    labelFormat?: 'percentage' | 'value';
  };
  summary?: any;
}

interface ChartDisplayProps {
  chartData: ChartData;
}

/**
 * ChartDisplay component renders financial charts using Recharts library.
 * Supports pie, bar, and line charts with smart formatting and tooltips.
 */
export default function ChartDisplay({ chartData }: ChartDisplayProps) {
  if (!chartData || chartData.status !== 'success') {
    return null;
  }

  const { title, chart_config } = chartData;
  const { type, data, colors, legend: showLegend, tooltip: showTooltip, grid } = chart_config;

  // Custom tooltip formatter
  const CustomTooltip = ({ active, payload, label }: any) => {
    if (active && payload && payload.length) {
      return (
        <div className="bg-white p-3 border border-gray-200 rounded shadow-md">
          <p className="font-semibold text-gray-900">{label}</p>
          {payload.map((entry: any, index: number) => (
            <p key={`item-${index}`} className="text-sm" style={{ color: entry.color }}>
              {entry.name}: {typeof entry.value === 'number' ? `$${entry.value.toLocaleString()}` : entry.value}
            </p>
          ))}
        </div>
      );
    }
    return null;
  };

  // Pie chart label formatter
  const renderPieLabel = (entry: any) => {
    if (chart_config.labelFormat === 'percentage') {
      return `${entry.percentage}%`;
    }
    return `$${entry.value.toLocaleString()}`;
  };

  // Render pie chart
  if (type === 'pie') {
    return (
      <div className="my-4 bg-white p-4 rounded-lg border border-gray-200">
        <h3 className="text-lg font-semibold text-gray-900 mb-4">{title}</h3>
        <ResponsiveContainer width="100%" height={400}>
          <PieChart>
            <Pie
              data={data}
              dataKey={chart_config.dataKey || 'value'}
              nameKey={chart_config.nameKey || 'name'}
              cx="50%"
              cy="50%"
              outerRadius={120}
              label={renderPieLabel}
              labelLine={false}
            >
              {data.map((entry, index) => (
                <Cell key={`cell-${index}`} fill={colors?.[index] || '#3B82F6'} />
              ))}
            </Pie>
            {showTooltip && <Tooltip content={<CustomTooltip />} />}
            {showLegend && <Legend />}
          </PieChart>
        </ResponsiveContainer>
      </div>
    );
  }

  // Render bar chart
  if (type === 'bar') {
    return (
      <div className="my-4 bg-white p-4 rounded-lg border border-gray-200">
        <h3 className="text-lg font-semibold text-gray-900 mb-4">{title}</h3>
        <ResponsiveContainer width="100%" height={400}>
          <BarChart data={data}>
            {grid && <CartesianGrid strokeDasharray="3 3" stroke="#E5E7EB" />}
            <XAxis dataKey={chart_config.xAxisKey || 'name'} stroke="#6B7280" />
            <YAxis stroke="#6B7280">
              {chart_config.yAxisLabel && <Label value={chart_config.yAxisLabel} angle={-90} position="insideLeft" />}
            </YAxis>
            {showTooltip && <Tooltip content={<CustomTooltip />} />}
            {showLegend && <Legend />}
            {chart_config.bars?.map((bar, index) => (
              <Bar key={`bar-${index}`} dataKey={bar.dataKey} name={bar.name} fill={bar.color} radius={[4, 4, 0, 0]} />
            ))}
          </BarChart>
        </ResponsiveContainer>
      </div>
    );
  }

  // Render line chart
  if (type === 'line') {
    return (
      <div className="my-4 bg-white p-4 rounded-lg border border-gray-200">
        <h3 className="text-lg font-semibold text-gray-900 mb-4">{title}</h3>
        <ResponsiveContainer width="100%" height={400}>
          <LineChart data={data}>
            {grid && <CartesianGrid strokeDasharray="3 3" stroke="#E5E7EB" />}
            <XAxis dataKey={chart_config.xAxisKey || 'name'} stroke="#6B7280" />
            <YAxis
              stroke="#6B7280"
              domain={chart_config.yAxisDomain || ['auto', 'auto']}
            >
              {chart_config.yAxisLabel && <Label value={chart_config.yAxisLabel} angle={-90} position="insideLeft" />}
            </YAxis>
            {showTooltip && <Tooltip content={<CustomTooltip />} />}
            {showLegend && <Legend />}
            {chart_config.lines?.map((line, index) => (
              <Line
                key={`line-${index}`}
                type="monotone"
                dataKey={line.dataKey}
                name={line.name}
                stroke={line.color}
                strokeWidth={2}
                dot={{ fill: line.color, r: 4 }}
                activeDot={{ r: 6 }}
              />
            ))}
          </LineChart>
        </ResponsiveContainer>
      </div>
    );
  }

  return null;
}

