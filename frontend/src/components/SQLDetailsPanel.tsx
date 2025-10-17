'use client';

import React, { useMemo, useState } from 'react';
import {
  ChevronDown,
  ChevronRight,
  Copy,
  Download,
  BarChart3,
  PieChart,
  LineChart,
  ScatterChart as ScatterPlot,
} from 'lucide-react';

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
import { Bar, Line, Pie, Scatter, Bubble, Radar } from 'react-chartjs-2';

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

interface SQLDetails {
  query: string;
  result_count: number;
  columns: string[];
  rows: any[];
  total_rows: number;
  execution_time?: string;
  truncated?: boolean;
}

interface SQLDetailsPanelProps {
  sqlDetails: SQLDetails;
  className?: string;
  defaultCollapsed?: boolean;
}

type ChartType =
  | 'line'
  | 'bar'
  | 'pie'
  | 'scatter'
  | 'area'
  | 'stacked-bar'
  | 'bubble'
  | 'radar';

export default function SQLDetailsPanel({
  sqlDetails,
  className = '',
  defaultCollapsed = true
}: SQLDetailsPanelProps) {
  const [isCollapsed, setIsCollapsed] = useState(defaultCollapsed);
  const [activeTab, setActiveTab] = useState<'query' | 'results' | 'charts'>('query');
  const [chartType, setChartType] = useState<ChartType>('line');

  // axis + series state
  const [xAxis, setXAxis] = useState<string>(sqlDetails.columns[0] || '');
  const [yAxis, setYAxis] = useState<string>('');
  const [sizeAxis, setSizeAxis] = useState<string>('');     // for bubble size
  const [seriesCols, setSeriesCols] = useState<string[]>([]); // for stacked/radar

  // --- helpers ---
  const isDark = () =>
    typeof document !== 'undefined' &&
    document.documentElement.classList.contains('dark');

  const parseNum = (v: any): number | null => {
    if (typeof v === 'number' && Number.isFinite(v)) return v;
    const n = parseFloat(v);
    return Number.isFinite(n) ? n : null;
  };

  const numericColumns = useMemo(() => {
    return sqlDetails.columns.filter(col =>
      sqlDetails.rows.some(r => parseNum(r[col]) !== null)
    );
  }, [sqlDetails.columns, sqlDetails.rows]);

  const categoricalColumns = useMemo(() => {
    return sqlDetails.columns.filter(col => {
      // strings / ids / typical label fields
      const sample = sqlDetails.rows?.[0]?.[col];
      return (
        typeof sample === 'string' ||
        /date|time|created|updated|id/i.test(col)
      );
    });
  }, [sqlDetails.columns, sqlDetails.rows]);

  // auto-pick sensible defaults
  useMemo(() => {
    if (!yAxis) {
      const firstNumeric = numericColumns.find(c => c !== xAxis);
      setYAxis(firstNumeric || sqlDetails.columns[1] || '');
    }
    if (!sizeAxis) {
      setSizeAxis(numericColumns.find(c => c !== xAxis && c !== yAxis) || yAxis);
    }
    if (seriesCols.length === 0) {
      // Pick up to 3 numeric series (skip yAxis to avoid duplication if desired)
      const picks = numericColumns.filter(c => c !== yAxis).slice(0, 3);
      setSeriesCols(picks);
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [numericColumns.length, xAxis, yAxis]);

  // --- copy & download ---
  const copyToClipboard = async (text: string) => {
    try {
      await navigator.clipboard.writeText(text);
    } catch (err) {
      console.error('Failed to copy text: ', err);
    }
  };

  const downloadResults = () => {
    const csvContent = [
      sqlDetails.columns.join(','),
      ...sqlDetails.rows.map(row =>
        sqlDetails.columns
          .map(col => {
            const v = row[col];
            const str = String(v ?? '');
            return str.includes(',') ? `"${str.replace(/"/g, '""')}"` : str;
          })
          .join(',')
      )
    ].join('\n');

    const blob = new Blob([csvContent], { type: 'text/csv;charset=utf-8;' });
    const url = URL.createObjectURL(blob);
    const link = document.createElement('a');
    link.setAttribute('href', url);
    link.setAttribute('download', 'query_results.csv');
    link.style.visibility = 'hidden';
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
  };

  const formatQuery = (query: string) => {
    return query
      .replace(
        /\b(SELECT|FROM|WHERE|JOIN|LEFT JOIN|RIGHT JOIN|INNER JOIN|ORDER BY|GROUP BY|HAVING|LIMIT)\b/gi,
        '\n$1'
      )
      .replace(/,\s*/g, ',\n  ')
      .trim();
  };

  // ------- CHART DATA & OPTIONS (Chart.js) -------
  // Labels: use xAxis values as strings
  const labels = useMemo(
    () => sqlDetails.rows.map(r => String(r[xAxis] ?? '')),
    [sqlDetails.rows, xAxis]
  );

  // For pie, avoid clutter: cap to 8 slices
  const pieRows = useMemo(
    () => (chartType === 'pie' ? sqlDetails.rows.slice(0, 8) : sqlDetails.rows),
    [chartType, sqlDetails.rows]
  );

  // Build datasets by type
  const chartData: ChartData<any> = useMemo(() => {
    if (chartType === 'scatter' || chartType === 'bubble') {
      const ds = sqlDetails.rows
        .map(r => {
          const x = parseNum(r[xAxis]);
          const y = parseNum(r[yAxis]);
          const s = parseNum(r[sizeAxis || yAxis]);
          if (x === null || y === null) return null;
          return {
            x,
            y,
            r: chartType === 'bubble' ? Math.max(4, Math.min(20, (s ?? y) * 0.5)) : undefined
          };
        })
        .filter(Boolean) as { x: number; y: number; r?: number }[];

      return {
        datasets: [
          {
            label: `${xAxis} vs ${yAxis}`,
            data: ds,
            backgroundColor: 'rgba(59,130,246,0.5)',
            borderColor: 'rgba(59,130,246,1)'
          }
        ]
      };
    }

    if (chartType === 'pie') {
      const dataVals = pieRows.map(r => parseNum(r[yAxis]) ?? 0);
      return {
        labels: pieRows.map(r => String(r[xAxis] ?? '')),
        datasets: [
          {
            data: dataVals,
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

    if (chartType === 'radar') {
      // Treat each selected series as its own polygon across first N x-categories
      const sliceN = Math.max(3, Math.min(8, sqlDetails.rows.length));
      const radarLabels = sqlDetails.rows.slice(0, sliceN).map(r => String(r[xAxis] ?? ''));
      const metrics = (seriesCols.length ? seriesCols : numericColumns.slice(0, 3));

      const baseR = 75, baseG = 192, baseB = 192;
      const ds = metrics.map((metric, i) => ({
        label: metric,
        data: sqlDetails.rows.slice(0, sliceN).map(r => parseNum(r[metric]) ?? 0),
        backgroundColor: `rgba(${baseR + i * 30}, ${Math.max(0, baseG - i * 20)}, ${Math.max(0, baseB - i * 30)}, 0.2)`,
        borderColor: `rgba(${baseR + i * 30}, ${Math.max(0, baseG - i * 20)}, ${Math.max(0, baseB - i * 30)}, 1)`,
        borderWidth: 1
      }));

      return { labels: radarLabels, datasets: ds };
    }

    if (chartType === 'stacked-bar') {
      const metrics = (seriesCols.length ? seriesCols : numericColumns.slice(0, 3));
      const palette = [
        ['rgba(59,130,246,0.7)', 'rgba(59,130,246,1)'],
        ['rgba(16,185,129,0.7)', 'rgba(16,185,129,1)'],
        ['rgba(245,158,11,0.7)', 'rgba(245,158,11,1)'],
        ['rgba(139,92,246,0.7)', 'rgba(139,92,246,1)'],
        ['rgba(239,68,68,0.7)', 'rgba(239,68,68,1)']
      ];

      const ds = metrics.map((metric, i) => ({
        label: metric,
        data: sqlDetails.rows.map(r => parseNum(r[metric]) ?? 0),
        backgroundColor: palette[i % palette.length][0],
        borderColor: palette[i % palette.length][1],
        borderWidth: 1
      }));

      return { labels, datasets: ds };
    }

    // line, area, bar
    const vals = sqlDetails.rows.map(r => parseNum(r[yAxis]) ?? 0);
    return {
      labels,
      datasets: [
        {
          label: yAxis,
          data: vals,
          backgroundColor:
            chartType === 'bar' ? 'rgba(59,130,246,0.7)' : 'rgba(59,130,246,0.3)',
          borderColor: 'rgba(59,130,246,1)',
          borderWidth: 2,
          tension: 0.25,
          fill: chartType === 'area'
        }
      ]
    };
  }, [chartType, sqlDetails.rows, xAxis, yAxis, labels, seriesCols, numericColumns, sizeAxis, pieRows]);

  const chartOptions: ChartOptions<any> = useMemo(() => {
    const text = isDark() ? '#e5e7eb' : '#374151';
    const grid = isDark() ? 'rgba(255,255,255,0.08)' : 'rgba(0,0,0,0.08)';

    const base: ChartOptions<any> = {
      responsive: true,
      maintainAspectRatio: false,
      plugins: {
        legend: {
          position: 'top',
          labels: { color: text }
        },
        title: {
          display: true,
          text:
            chartType === 'scatter' || chartType === 'bubble'
              ? `${yAxis} vs ${xAxis}`
              : `${yAxis} by ${xAxis}`,
          color: text
        },
        tooltip: { enabled: true }
      }
    };

    // pie/radar have no Cartesian scales
    if (chartType === 'pie' || chartType === 'radar') return base;

    // stacked bar needs stacked axes
    if (chartType === 'stacked-bar') {
      return {
        ...base,
        scales: {
          x: {
            stacked: true,
            ticks: { color: text },
            title: { display: true, text: xAxis, color: text },
            grid: { color: grid }
          },
          y: {
            stacked: true,
            ticks: { color: text },
            title: { display: true, text: 'Value', color: text },
            grid: { color: grid }
          }
        }
      };
    }

    // others (bar/line/area/scatter/bubble)
    return {
      ...base,
      scales: {
        x: {
          ticks: { color: text },
          title: { display: true, text: xAxis, color: text },
          grid: { color: grid }
        },
        y: {
          ticks: { color: text },
          title: { display: true, text: yAxis, color: text },
          grid: { color: grid }
        }
      }
    };
  }, [chartType, xAxis, yAxis]);

  // Small reusable UI
  const SeriesMultiSelect = ({
    value,
    onChange,
    options
  }: {
    value: string[];
    onChange: (v: string[]) => void;
    options: string[];
  }) => (
    <div className="w-full border border-gray-300 rounded-md p-2 flex flex-wrap gap-2">
      {options.map((col) => {
        const checked = value.includes(col);
        return (
          <label
            key={col}
            className={`text-xs px-2 py-1 border rounded cursor-pointer ${
              checked
                ? 'bg-blue-50 border-blue-500 text-blue-700'
                : 'bg-white border-gray-300 text-gray-700'
            }`}
          >
            <input
              type="checkbox"
              className="mr-1"
              checked={checked}
              onChange={(e) => {
                if (e.target.checked) onChange([...value, col]);
                else onChange(value.filter((v) => v !== col));
              }}
            />
            {col}
          </label>
        );
      })}
    </div>
  );

  const chartTypes = [
    { id: 'line', label: 'Line Chart', icon: LineChart },
    { id: 'bar', label: 'Bar Chart', icon: BarChart3 },
    { id: 'pie', label: 'Pie Chart', icon: PieChart },
    { id: 'scatter', label: 'Scatter Plot', icon: ScatterPlot },
    { id: 'area', label: 'Area Chart', icon: LineChart },
    { id: 'stacked-bar', label: 'Stacked Bar', icon: BarChart3 },
    { id: 'bubble', label: 'Bubble Chart', icon: ScatterPlot },
    { id: 'radar', label: 'Radar Chart', icon: PieChart }
  ] as const;

  // Render chart component by type
  const renderChart = () => {
    if (sqlDetails.rows.length === 0) {
      return (
        <div className="text-center py-8 text-gray-500">
          <p className="text-sm">No data available for charting</p>
        </div>
      );
    }

    switch (chartType) {
      case 'bar':
      case 'stacked-bar':
        return <Bar data={chartData} options={chartOptions} />;
      case 'line':
      case 'area':
        return <Line data={chartData} options={chartOptions} />;
      case 'pie':
        return <Pie data={chartData} options={chartOptions} />;
      case 'scatter':
        return <Scatter data={chartData} options={chartOptions} />;
      case 'bubble':
        return <Bubble data={chartData} options={chartOptions} />;
      case 'radar':
        return <Radar data={chartData} options={chartOptions} />;
      default:
        return <Bar data={chartData} options={chartOptions} />;
    }
  };

  return (
    <div className={`border border-gray-200 bg-white overflow-hidden ${className}`}>
      {/* Header */}
      <div
        className="flex items-center justify-between p-4 cursor-pointer hover:bg-gray-50 border-b border-gray-100"
        onClick={() => setIsCollapsed(!isCollapsed)}
      >
        <div className="flex items-center space-x-2">
          {isCollapsed ? (
            <ChevronRight className="h-4 w-4 text-gray-500" />
          ) : (
            <ChevronDown className="h-4 w-4 text-gray-500" />
          )}
          <h3 className="text-sm font-semibold text-gray-900">SQL Query & Results</h3>
          <span className="text-xs text-gray-500">
            {sqlDetails.result_count} rows
            {sqlDetails.truncated && <span className="text-orange-600 ml-1">(truncated)</span>}
            {sqlDetails.execution_time && <span className="ml-2">{sqlDetails.execution_time}</span>}
          </span>
        </div>

        <div className="text-xs text-gray-400">
          {isCollapsed ? 'Click to expand' : 'Click to collapse'}
        </div>
      </div>

      {/* Content */}
      {!isCollapsed && (
        <div className="p-4 overflow-hidden">
          {/* Tabs */}
          <div className="flex space-x-1 mb-4 border-b border-gray-200">
            <button
              onClick={() => setActiveTab('query')}
              className={`px-3 py-2 text-sm font-medium border-b-2 transition-colors ${
                activeTab === 'query'
                  ? 'border-blue-500 text-blue-600'
                  : 'border-transparent text-gray-500 hover:text-gray-700'
              }`}
            >
              SQL Query
            </button>
            <button
              onClick={() => setActiveTab('results')}
              className={`px-3 py-2 text-sm font-medium border-b-2 transition-colors ${
                activeTab === 'results'
                  ? 'border-blue-500 text-blue-600'
                  : 'border-transparent text-gray-500 hover:text-gray-700'
              }`}
            >
              Results ({sqlDetails.result_count})
            </button>
            <button
              onClick={() => setActiveTab('charts')}
              className={`px-3 py-2 text-sm font-medium border-b-2 transition-colors ${
                activeTab === 'charts'
                  ? 'border-blue-500 text-blue-600'
                  : 'border-transparent text-gray-500 hover:text-gray-700'
              }`}
            >
              Charts
            </button>
          </div>

          {/* Query Tab */}
          {activeTab === 'query' && (
            <div className="space-y-3">
              <div className="flex items-center justify-between">
                <h4 className="text-sm font-medium text-gray-700">Generated SQL Query</h4>
                <button
                  onClick={() => copyToClipboard(sqlDetails.query)}
                  className="flex items-center space-x-1 px-2 py-1 text-xs text-gray-600 hover:text-gray-800 hover:bg-gray-100"
                >
                  <Copy className="h-3 w-3" />
                  <span>Copy</span>
                </button>
              </div>

              <div className="relative overflow-hidden">
                <pre className="bg-gray-900 text-gray-100 p-4 text-sm overflow-x-auto whitespace-pre">
                  <code>{formatQuery(sqlDetails.query)}</code>
                </pre>
              </div>
            </div>
          )}

          {/* Results Tab */}
          {activeTab === 'results' && (
            <div className="space-y-3">
              <div className="flex items-center justify-between">
                <h4 className="text-sm font-medium text-gray-700">
                  Query Results
                  {sqlDetails.truncated && (
                    <span className="ml-2 text-xs text-orange-600 bg-orange-50 px-2 py-1">
                      Showing first {sqlDetails.result_count} of {sqlDetails.total_rows} rows
                    </span>
                  )}
                </h4>
                {sqlDetails.rows.length > 0 && (
                  <button
                    onClick={downloadResults}
                    className="flex items-center space-x-1 px-2 py-1 text-xs text-gray-600 hover:text-gray-800 hover:bg-gray-100"
                  >
                    <Download className="h-3 w-3" />
                    <span>Download CSV</span>
                  </button>
                )}
              </div>

              {sqlDetails.rows.length === 0 ? (
                <div className="text-center py-8 text-gray-500">
                  <p className="text-sm">No results returned</p>
                </div>
              ) : (
                <div className="border border-gray-200">
                  <div className="overflow-auto max-h-96 max-w-full">
                    <table className="w-full divide-y divide-gray-200" style={{ minWidth: 'max-content' }}>
                      <thead className="bg-gray-50">
                        <tr>
                          {sqlDetails.columns.map((column, index) => (
                            <th
                              key={index}
                              className="px-4 py-2 text-left text-xs font-medium text-gray-500 uppercase tracking-wider sticky top-0 bg-gray-50 whitespace-nowrap"
                            >
                              {column}
                            </th>
                          ))}
                        </tr>
                      </thead>
                      <tbody className="bg-white divide-y divide-gray-200">
                        {sqlDetails.rows.map((row, rowIndex) => (
                          <tr key={rowIndex} className="hover:bg-gray-50">
                            {sqlDetails.columns.map((column, colIndex) => (
                              <td
                                key={colIndex}
                                className="px-4 py-2 text-sm text-gray-900"
                                style={{
                                  maxWidth: '200px',
                                  overflow: 'hidden',
                                  textOverflow: 'ellipsis',
                                  whiteSpace: 'nowrap'
                                }}
                                title={
                                  row[column] !== null && row[column] !== undefined
                                    ? String(row[column])
                                    : 'null'
                                }
                              >
                                {row[column] !== null && row[column] !== undefined ? (
                                  String(row[column])
                                ) : (
                                  <span className="text-gray-400 italic">null</span>
                                )}
                              </td>
                            ))}
                          </tr>
                        ))}
                      </tbody>
                    </table>
                  </div>
                </div>
              )}
            </div>
          )}

          {/* Charts Tab */}
          {activeTab === 'charts' && (
            <div className="space-y-4">
              {/* Chart Type Selection */}
              <div className="space-y-3">
                <h4 className="text-sm font-medium text-gray-700">Chart Type</h4>
                <div className="flex flex-wrap gap-2">
                  {chartTypes.map((type) => {
                    const Icon = type.icon;
                    return (
                      <button
                        key={type.id}
                        onClick={() => setChartType(type.id)}
                        className={`flex items-center space-x-2 px-3 py-2 text-sm border rounded-md transition-colors ${
                          chartType === type.id
                            ? 'bg-blue-50 border-blue-500 text-blue-700'
                            : 'bg-white border-gray-300 text-gray-700 hover:bg-gray-50'
                        }`}
                      >
                        <Icon className="h-4 w-4" />
                        <span>{type.label}</span>
                      </button>
                    );
                  })}
                </div>
              </div>

              {/* Axis / Series Config */}
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                {/* X */}
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">
                    {chartType === 'scatter' || chartType === 'bubble' ? 'X-Axis (Numeric)' : 'X-Axis (Labels)'}
                  </label>
                  <select
                    value={xAxis}
                    onChange={(e) => setXAxis(e.target.value)}
                    className="w-full px-3 py-2 border border-gray-300 rounded-md text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
                  >
                    <option value="">Select column</option>
                    {(chartType === 'scatter' || chartType === 'bubble'
                      ? numericColumns
                      : (categoricalColumns.length ? categoricalColumns : sqlDetails.columns)
                    ).map((col) => (
                      <option key={col} value={col}>{col}</option>
                    ))}
                  </select>
                </div>

                {/* Y */}
                {chartType !== 'stacked-bar' && chartType !== 'radar' && (
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-2">Y-Axis (Numeric)</label>
                    <select
                      value={yAxis}
                      onChange={(e) => setYAxis(e.target.value)}
                      className="w-full px-3 py-2 border border-gray-300 rounded-md text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
                    >
                      <option value="">Select column</option>
                      {numericColumns.map((col) => (
                        <option key={col} value={col}>{col}</option>
                      ))}
                    </select>
                  </div>
                )}

                {/* Bubble size */}
                {chartType === 'bubble' && (
                  <div className="md:col-span-2">
                    <label className="block text-sm font-medium text-gray-700 mb-2">Bubble Size (Numeric)</label>
                    <select
                      value={sizeAxis}
                      onChange={(e) => setSizeAxis(e.target.value)}
                      className="w-full px-3 py-2 border border-gray-300 rounded-md text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
                    >
                      {numericColumns.map((col) => (
                        <option key={col} value={col}>{col}</option>
                      ))}
                    </select>
                  </div>
                )}

                {/* Series multi-select for stacked / radar */}
                {(chartType === 'stacked-bar' || chartType === 'radar') && (
                  <div className="md:col-span-2">
                    <label className="block text-sm font-medium text-gray-700 mb-2">
                      Series Columns (pick 1+ numeric)
                    </label>
                    <SeriesMultiSelect
                      value={seriesCols}
                      onChange={setSeriesCols}
                      options={numericColumns}
                    />
                  </div>
                )}
              </div>

              {/* Chart */}
              <div className="border border-gray-200 rounded-md p-4 bg-gray-50 h-[380px]">
                {renderChart()}
              </div>
            </div>
          )}
        </div>
      )}
    </div>
  );
}
