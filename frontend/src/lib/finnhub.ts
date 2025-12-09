/**
 * Finnhub API Service for fetching real-time stock data
 * API Documentation: https://finnhub.io/docs/api
 */

interface FinnhubCandle {
  c: number[]  // Close prices
  h: number[]  // High prices
  l: number[]  // Low prices
  o: number[]  // Open prices
  t: number[]  // Timestamps
  v: number[]  // Volume
  s: string    // Status
}

interface ChartDataPoint {
  date: string
  price: number
  volume?: number
}

// Get API key from environment variable or use provided key
const FINNHUB_API_KEY = import.meta.env.VITE_FINNHUB_API_KEY || 'd3g1aq9r01qqbh54p1p0d3g1aq9r01qqbh54p1pg'

/**
 * Fetch historical stock data from Finnhub
 * @param symbol Stock symbol (e.g., AAPL, TSLA)
 * @param days Number of days to fetch (default: 30)
 * @returns Array of price data points
 */
export async function fetchStockData(
  symbol: string,
  days: number = 30
): Promise<ChartDataPoint[]> {
  try {
    // Calculate date range
    const endDate = Math.floor(Date.now() / 1000) // Current timestamp
    const startDate = endDate - (days * 24 * 60 * 60) // N days ago

    const url = `https://finnhub.io/api/v1/stock/candle?symbol=${symbol}&resolution=D&from=${startDate}&to=${endDate}&token=${FINNHUB_API_KEY}`

    const response = await fetch(url)
    
    if (!response.ok) {
      throw new Error(`Finnhub API error: ${response.status}`)
    }

    const data: FinnhubCandle = await response.json()

    // Check if data is valid
    if (data.s !== 'ok' || !data.c || data.c.length === 0) {
      console.warn(`No data available for ${symbol}`)
      return []
    }

    // Convert to chart format
    const chartData: ChartDataPoint[] = []
    for (let i = 0; i < data.c.length; i++) {
      const date = new Date(data.t[i] * 1000) // Convert Unix timestamp to Date
      chartData.push({
        date: date.toISOString().split('T')[0], // Format: YYYY-MM-DD
        price: data.c[i], // Use closing price
        volume: data.v[i],
      })
    }

    return chartData
  } catch (error) {
    console.error('Error fetching stock data from Finnhub:', error)
    return []
  }
}

/**
 * Get current stock quote from Finnhub
 * @param symbol Stock symbol
 */
export async function fetchStockQuote(symbol: string) {
  try {
    const url = `https://finnhub.io/api/v1/quote?symbol=${symbol}&token=${FINNHUB_API_KEY}`
    const response = await fetch(url)
    
    if (!response.ok) {
      throw new Error(`Finnhub API error: ${response.status}`)
    }

    return await response.json()
  } catch (error) {
    console.error('Error fetching stock quote from Finnhub:', error)
    return null
  }
}

