'use client'

import { useMemo } from 'react'
import {
  BarChart, Bar, LineChart, Line, PieChart, Pie, Cell,
  XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer,
} from 'recharts'
import type { ChartData } from '@/lib/services/writing'

// ─────────────────────────────────────────────
//  Color palette for chart series
// ─────────────────────────────────────────────

const COLORS = [
  'hsl(221, 83%, 53%)',  // blue
  'hsl(142, 71%, 45%)',  // green
  'hsl(25, 95%, 53%)',   // orange
  'hsl(262, 83%, 58%)',  // purple
  'hsl(346, 77%, 50%)',  // pink
  'hsl(47, 96%, 53%)',   // yellow
  'hsl(189, 94%, 43%)',  // cyan
  'hsl(0, 72%, 51%)',    // red
]

// ─────────────────────────────────────────────
//  Props
// ─────────────────────────────────────────────

interface Task1ChartProps {
  chartData: ChartData
  className?: string
}

// ─────────────────────────────────────────────
//  Component
// ─────────────────────────────────────────────

export function Task1Chart({ chartData, className }: Task1ChartProps) {
  const { chart_type, title, x_axis_label, y_axis_label, labels, datasets } = chartData

  // Transform data into recharts format: [{label, series1, series2, ...}]
  const formattedData = useMemo(() => {
    return labels.map((label, index) => {
      const point: Record<string, string | number> = { name: label }
      datasets.forEach((ds) => {
        point[ds.label] = ds.data[index] ?? 0
      })
      return point
    })
  }, [labels, datasets])

  // Pie data format: [{name, value}]
  const pieData = useMemo(() => {
    if (chart_type !== 'pie' || !datasets[0]) return []
    return labels.map((label, index) => ({
      name: label,
      value: datasets[0].data[index] ?? 0,
    }))
  }, [chart_type, labels, datasets])

  return (
    <div className={className}>
      {/* Chart title */}
      <h4 className="text-sm font-semibold text-center mb-3">{title}</h4>

      {/* Chart rendering */}
      <div className="w-full h-[300px]">
        <ResponsiveContainer width="100%" height="100%">
          {chart_type === 'bar' ? (
            <BarChart data={formattedData} margin={{ top: 5, right: 20, left: 10, bottom: 5 }}>
              <CartesianGrid strokeDasharray="3 3" className="opacity-30" />
              <XAxis
                dataKey="name"
                tick={{ fontSize: 12 }}
                label={x_axis_label ? { value: x_axis_label, position: 'insideBottom', offset: -5, fontSize: 11 } : undefined}
              />
              <YAxis
                tick={{ fontSize: 12 }}
                label={y_axis_label ? { value: y_axis_label, angle: -90, position: 'insideLeft', fontSize: 11 } : undefined}
              />
              <Tooltip contentStyle={{ borderRadius: 8, fontSize: 12 }} />
              <Legend wrapperStyle={{ fontSize: 12 }} />
              {datasets.map((ds, i) => (
                <Bar key={ds.label} dataKey={ds.label} fill={COLORS[i % COLORS.length]} radius={[4, 4, 0, 0]} />
              ))}
            </BarChart>
          ) : chart_type === 'line' ? (
            <LineChart data={formattedData} margin={{ top: 5, right: 20, left: 10, bottom: 5 }}>
              <CartesianGrid strokeDasharray="3 3" className="opacity-30" />
              <XAxis
                dataKey="name"
                tick={{ fontSize: 12 }}
                label={x_axis_label ? { value: x_axis_label, position: 'insideBottom', offset: -5, fontSize: 11 } : undefined}
              />
              <YAxis
                tick={{ fontSize: 12 }}
                label={y_axis_label ? { value: y_axis_label, angle: -90, position: 'insideLeft', fontSize: 11 } : undefined}
              />
              <Tooltip contentStyle={{ borderRadius: 8, fontSize: 12 }} />
              <Legend wrapperStyle={{ fontSize: 12 }} />
              {datasets.map((ds, i) => (
                <Line
                  key={ds.label}
                  type="monotone"
                  dataKey={ds.label}
                  stroke={COLORS[i % COLORS.length]}
                  strokeWidth={2}
                  dot={{ r: 4 }}
                  activeDot={{ r: 6 }}
                />
              ))}
            </LineChart>
          ) : (
            <PieChart>
              <Pie
                data={pieData}
                cx="50%"
                cy="50%"
                labelLine
                label={({ name, percent }) => `${name} (${((percent ?? 0) * 100).toFixed(0)}%)`}
                outerRadius={100}
                dataKey="value"
              >
                {pieData.map((_, index) => (
                  <Cell key={`cell-${index}`} fill={COLORS[index % COLORS.length]} />
                ))}
              </Pie>
              <Tooltip contentStyle={{ borderRadius: 8, fontSize: 12 }} />
              <Legend wrapperStyle={{ fontSize: 12 }} />
            </PieChart>
          )}
        </ResponsiveContainer>
      </div>
    </div>
  )
}
