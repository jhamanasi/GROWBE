'use client';

import React, { useMemo } from 'react';
import {
  Chart as ChartJS,
  CategoryScale,
  LinearScale,
  PointElement,
  LineElement,
  BarElement,
  ArcElement,
  Title as ChartTitle,
  Tooltip,
  Legend,
  RadialLinearScale,
  Filler,
  ScatterController,
  BubbleController,
  ChartOptions,
  ChartData
} from 'chart.js';
import { Bar, Line, Pie, Scatter } from 'react-chartjs-2';

ChartJS.register(
  CategoryScale,
  LinearScale,
  PointElement,
  LineElement,
  BarElement,
  ArcElement,
  RadialLinearScale,
  ChartTitle,
  Tooltip,
  Legend,
  Filler,
  ScatterController,
  BubbleController
);

interface ChartConfig {
  type: string;
  title: string;
  x_axis: string;
  y_axis: string;
  eligible: boolean;
  series_columns?: string[];
}

interface InlineSQLChartProps {
  chartConfig: ChartConfig;
  sqlData: {
    rows: any[];
    columns: string[];
  };
}

export default function InlineSQLChart({ chartConfig, sqlData }: InlineSQLChartProps) {
  // Helper function to parse numeric values
  const parseNum = (val: any): number | null => {
    if (val === null || val === undefined || val === '') return null;
    const num = typeof val === 'string' ? parseFloat(val) : Number(val);
    return isNaN(num) ? null : num;
  };

  // Generate chart data based on configuration
  const chartData: ChartData<any> = useMemo(() => {
    const { type, x_axis, y_axis, series_columns } = chartConfig;
    const { rows } = sqlData;

    if (type === 'scatter') {
      const scatterData = rows
        .map(row => {
          const x = parseNum(row[x_axis]);
          const y = parseNum(row[y_axis]);
          if (x === null || y === null) return null;
          return { x, y };
        })
        .filter(Boolean) as { x: number; y: number }[];

      return {
        datasets: [
          {
            label: `${x_axis} vs ${y_axis}`,
            data: scatterData,
            backgroundColor: 'rgba(59,130,246,0.6)',
            borderColor: 'rgba(59,130,246,1)',
            borderWidth: 1,
          }
        ]
      };
    }

    if (type === 'pie') {
      const pieData = rows.slice(0, 8); // Limit for readability
      return {
        labels: pieData.map(row => String(row[x_axis] ?? '')),
        datasets: [
          {
            data: pieData.map(row => parseNum(row[y_axis]) ?? 0),
            backgroundColor: [
              'rgba(59,130,246,0.7)',
              'rgba(16,185,129,0.7)',
              'rgba(245,158,11,0.7)',
              'rgba(239,68,68,0.7)',
              'rgba(139,92,246,0.7)',
              'rgba(6,182,212,0.7)',
              'rgba(132,204,22,0.7)',
              'rgba(249,115,22,0.7)'
            ],
            borderColor: [
              'rgba(59,130,246,1)',
              'rgba(16,185,129,1)',
              'rgba(245,158,11,1)',
              'rgba(239,68,68,1)',
              'rgba(139,92,246,1)',
              'rgba(6,182,212,1)',
              'rgba(132,204,22,1)',
              'rgba(249,115,22,1)'
            ],
            borderWidth: 1
          }
        ]
      };
    }

    if (type === 'stacked-bar' && series_columns) {
      const palette = [
        ['rgba(59,130,246,0.7)', 'rgba(59,130,246,1)'],
        ['rgba(16,185,129,0.7)', 'rgba(16,185,129,1)'],
        ['rgba(245,158,11,0.7)', 'rgba(245,158,11,1)'],
        ['rgba(139,92,246,0.7)', 'rgba(139,92,246,1)'],
        ['rgba(239,68,68,0.7)', 'rgba(239,68,68,1)']
      ];

      const datasets = [y_axis, ...series_columns].map((col, i) => ({
        label: col,
        data: rows.map(row => parseNum(row[col]) ?? 0),
        backgroundColor: palette[i % palette.length][0],
        borderColor: palette[i % palette.length][1],
        borderWidth: 1
      }));

      return {
        labels: rows.map(row => String(row[x_axis] ?? '')),
        datasets
      };
    }

    // Default: bar or line chart
    const isLine = type === 'line';
    return {
      labels: rows.map(row => String(row[x_axis] ?? '')),
      datasets: [
        {
          label: y_axis,
          data: rows.map(row => parseNum(row[y_axis]) ?? 0),
          backgroundColor: isLine ? 'rgba(59,130,246,0.1)' : 'rgba(59,130,246,0.7)',
          borderColor: 'rgba(59,130,246,1)',
          borderWidth: 2,
          fill: isLine,
          tension: isLine ? 0.4 : undefined
        }
      ]
    };
  }, [chartConfig, sqlData]);

  // Chart options
  const chartOptions: ChartOptions<any> = useMemo(() => {
    const baseOptions: ChartOptions<any> = {
      responsive: true,
      maintainAspectRatio: false,
      plugins: {
        title: {
          display: true,
          text: chartConfig.title,
          font: {
            size: 14,
            weight: 'bold'
          }
        },
        legend: {
          display: chartConfig.type !== 'scatter',
          position: 'top' as const,
        },
        tooltip: {
          mode: 'index' as const,
          intersect: false,
        },
      },
    };

    if (chartConfig.type !== 'pie') {
      baseOptions.scales = {
        x: {
          display: true,
          title: {
            display: true,
            text: chartConfig.x_axis
          }
        },
        y: {
          display: true,
          title: {
            display: true,
            text: chartConfig.y_axis
          }
        }
      };
    }

    if (chartConfig.type === 'stacked-bar') {
      baseOptions.scales!.x!.stacked = true;
      baseOptions.scales!.y!.stacked = true;
    }

    return baseOptions;
  }, [chartConfig]);

  // Render appropriate chart component
  const renderChart = () => {
    const commonProps = {
      data: chartData,
      options: chartOptions,
      height: 300
    };

    switch (chartConfig.type) {
      case 'line':
        return <Line {...commonProps} />;
      case 'pie':
        return <Pie {...commonProps} />;
      case 'scatter':
        return <Scatter {...commonProps} />;
      case 'bar':
      case 'stacked-bar':
      default:
        return <Bar {...commonProps} />;
    }
  };

  return (
    <div className="my-4 p-4 bg-gray-50 border border-gray-200">
      <div style={{ height: '300px' }}>
        {renderChart()}
      </div>
    </div>
  );
}
