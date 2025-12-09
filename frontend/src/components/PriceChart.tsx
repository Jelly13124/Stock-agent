import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, Area, AreaChart } from 'recharts'
import './PriceChart.css'

interface PriceDataPoint {
  date: string
  price: number
  volume?: number
}

interface PriceChartProps {
  data: PriceDataPoint[]
  title?: string
}

export function PriceChart({ data, title = '价格走势' }: PriceChartProps) {
  if (!data || data.length === 0) {
    return (
      <div className="chart-empty">
        <p>暂无价格数据</p>
      </div>
    )
  }

  // Calculate dynamic Y-axis range based on actual prices
  const prices = data.map(d => d.price)
  const minPrice = Math.min(...prices)
  const maxPrice = Math.max(...prices)
  const priceRange = maxPrice - minPrice
  
  // Add padding (10% on each side, minimum 5% of the price)
  const padding = Math.max(priceRange * 0.1, minPrice * 0.05)
  const yMin = Math.max(0, minPrice - padding)
  const yMax = maxPrice + padding

  return (
    <div className="price-chart-container">
      <h4 className="chart-title">{title}</h4>
      <ResponsiveContainer width="100%" height={300}>
        <AreaChart data={data} margin={{ top: 10, right: 30, left: 0, bottom: 0 }}>
          <defs>
            <linearGradient id="priceGradient" x1="0" y1="0" x2="0" y2="1">
              <stop offset="5%" stopColor="#1b5dad" stopOpacity={0.3} />
              <stop offset="95%" stopColor="#1b5dad" stopOpacity={0} />
            </linearGradient>
          </defs>
          <CartesianGrid strokeDasharray="3 3" stroke="rgba(27, 93, 173, 0.1)" />
          <XAxis
            dataKey="date"
            tick={{ fill: '#5a7a96', fontSize: 12 }}
            tickFormatter={(value) => {
              const date = new Date(value)
              return `${date.getMonth() + 1}/${date.getDate()}`
            }}
          />
          <YAxis
            domain={[yMin, yMax]}
            tick={{ fill: '#5a7a96', fontSize: 12 }}
            tickFormatter={(value) => `$${value.toFixed(0)}`}
          />
          <Tooltip
            contentStyle={{
              backgroundColor: 'rgba(255, 255, 255, 0.95)',
              border: '1px solid rgba(27, 93, 173, 0.2)',
              borderRadius: '8px',
              padding: '8px 12px',
            }}
            labelFormatter={(label) => `日期: ${label}`}
            formatter={(value: number) => [`$${value.toFixed(2)}`, '价格']}
          />
          <Area
            type="monotone"
            dataKey="price"
            stroke="#1b5dad"
            strokeWidth={2}
            fill="url(#priceGradient)"
          />
        </AreaChart>
      </ResponsiveContainer>
    </div>
  )
}

