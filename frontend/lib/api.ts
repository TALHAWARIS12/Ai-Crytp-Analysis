import axios from 'axios'
import { CoinAnalysis, StrategyValidation, SignalVerification } from '@/types/market'

const rawUrl = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'
const API_URL = rawUrl.replace(/\/api\/v1\/?$/, '')

const api = axios.create({
  baseURL: API_URL,
  headers: {
    'Content-Type': 'application/json',
  },
})

const normalizeSymbol = (symbol: string): string => {
  const cleaned = symbol.trim().toUpperCase().replace('-', '/').replace('_', '/')
  if (cleaned.includes('/')) return cleaned

  const quotes = ['USDT', 'USDC', 'BUSD', 'BTC', 'ETH']
  for (const quote of quotes) {
    if (cleaned.endsWith(quote) && cleaned.length > quote.length) {
      const base = cleaned.slice(0, cleaned.length - quote.length)
      return `${base}/${quote}`
    }
  }
  return `${cleaned}/USDT`
}

const pathSymbol = (symbol: string): string => normalizeSymbol(symbol).replace('/', '')

export const marketAPI = {
  // Coin Analysis
  analyzeCoin: async (symbol: string): Promise<CoinAnalysis> => {
    const response = await api.post('/api/v1/analyze', {
      symbol: normalizeSymbol(symbol),
    })
    return response.data
  },

  // Strategy Validation
  validateStrategy: async (
    symbol: string,
    direction: 'LONG' | 'SHORT',
    timeframe: string = '4h'
  ): Promise<StrategyValidation> => {
    const response = await api.post('/api/v1/strategy', {
      symbol: normalizeSymbol(symbol),
      direction,
      timeframe,
    })
    return response.data
  },

  // Signal Verification
  checkSignal: async (
    symbol: string,
    direction: 'LONG' | 'SHORT',
    entryPrice: number,
    entryZoneLow: number,
    entryZoneHigh: number,
    targets: number[],
    stopLoss: number
  ): Promise<SignalVerification> => {
    const response = await api.post('/api/v1/checksignal', {
      symbol: normalizeSymbol(symbol),
      direction,
      entry_price: entryPrice,
      entry_zone_low: entryZoneLow,
      entry_zone_high: entryZoneHigh,
      targets,
      stop_loss: stopLoss,
    })
    return response.data
  },

  // Search Symbols
  searchSymbols: async (query: string): Promise<string[]> => {
    const response = await api.get('/api/v1/search', {
      params: { q: query },
    })
    return response.data.symbols
  },

  // Get Current Price
  getPrice: async (symbol: string) => {
    const response = await api.get(`/api/v1/price/${pathSymbol(symbol)}`)
    return response.data
  },

  // Health Check
  health: async () => {
    const response = await api.get('/health')
    return response.data
  },
}

export default api
