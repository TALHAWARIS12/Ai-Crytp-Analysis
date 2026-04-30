export interface Ticker {
  symbol: string
  last: number
  bid: number
  ask: number
  high: number
  low: number
  volume: number
  change: number
  percentage: number
}

export interface CoinAnalysis {
  symbol: string
  current_price: number
  trend: 'BULLISH' | 'BEARISH' | 'NEUTRAL'
  confidence: number
  support: number[]
  resistance: number[]
  ema8: number
  ema34: number
  sma50: number | null
  sma200: number | null
  rsi: number | null
  funding_rate: {
    funding_rate: number
    funding_rate_percent: number
    status: string
  }
  analysis: string
  timestamp: string
}

export interface StrategyValidation {
  status: 'VALID LONG' | 'VALID SHORT' | 'WAIT FOR RETEST' | 'AVOID ENTRY'
  confidence: number
  reasons: string[]
  warnings: string[]
  entry_zones: {
    primary_zone: { low: number; high: number }
    secondary_zone: { low: number; high: number }
  }
  exit_zones: {
    take_profit: number
    stop_loss: number
  }
  ai_reasoning: string
  timestamp: string
}

export interface SignalVerification {
  status: 'VALID' | 'WAIT' | 'AVOID' | 'RISKY'
  confidence: number
  risk_score: number
  reasons: string[]
  warnings: string[]
  symbol: string
  direction: 'LONG' | 'SHORT'
  entry_price: number
  stop_loss: number
  targets: number[]
  ai_reasoning: string
  timestamp: string
}

export interface WatchlistItem {
  symbol: string
  current_price: number
  change_percent: number
  trend: string
}

export interface MarketData {
  symbol: string
  price: number
  high24h: number
  low24h: number
  volume24h: number
}
