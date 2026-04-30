'use client'

import React, { useState, useEffect } from 'react'
import { marketAPI } from '@/lib/api'
import { CoinAnalysis } from '@/types/market'
import { Loader2, AlertCircle, TrendingUp, TrendingDown, Search, BarChart3, Shield, Activity, Sparkles } from 'lucide-react'

interface Props {
  symbol: string
}

export default function CoinAnalysisPanel({ symbol }: Props) {
  const [analysis, setAnalysis] = useState<CoinAnalysis | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [searchInput, setSearchInput] = useState(symbol)

  const fetchAnalysis = async (sym: string) => {
    setLoading(true)
    setError(null)
    try {
      const data = await marketAPI.analyzeCoin(sym)
      setAnalysis(data)
    } catch (err: any) {
      setError(err.message || 'Failed to analyze coin')
      setAnalysis(null)
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    fetchAnalysis(symbol)
  }, [symbol])

  const handleSearch = (e: React.FormEvent) => {
    e.preventDefault()
    if (searchInput.trim()) {
      fetchAnalysis(searchInput)
    }
  }

  return (
    <div className="space-y-8 fade-in">
      {/* Search Form */}
      <form onSubmit={handleSearch} className="relative group">
        <div className="absolute inset-y-0 left-4 flex items-center pointer-events-none text-white/30 group-focus-within:text-accent-purple transition-colors">
           <Search size={20} />
        </div>
        <input
          type="text"
          value={searchInput}
          onChange={(e) => setSearchInput(e.target.value)}
          placeholder="Enter coin symbol (e.g., BTC, ETH)"
          className="w-full bg-white/5 border border-white/10 rounded-2xl pl-12 pr-32 py-4 text-white placeholder-white/20 focus:outline-none focus:border-accent-purple/50 transition-all text-lg"
        />
        <button
          type="submit"
          className="absolute right-2 top-2 bottom-2 px-6 bg-gradient-to-r from-accent-purple to-accent-purple-pink text-white rounded-xl font-bold text-sm hover:shadow-[0_0_15px_rgba(123,47,255,0.4)] transition-all active:scale-95"
        >
          Analyze
        </button>
      </form>

      {/* Loading State */}
      {loading && (
        <div className="glass-card p-12 flex flex-col items-center justify-center gap-6">
          <div className="relative">
             <div className="absolute inset-0 bg-accent-cyan blur-2xl opacity-20 animate-pulse" />
             <Loader2 size={48} className="animate-spin text-accent-cyan relative z-10" />
          </div>
          <div className="text-center">
            <h3 className="text-xl font-bold mb-2 shimmer-text text-white">Fetching Real-time Intelligence</h3>
            <p className="text-white/40 text-sm">Aggregating order book data and technical indicators...</p>
          </div>
        </div>
      )}

      {/* Error State */}
      {error && (
        <div className="glass-card p-6 border-l-4 border-l-red-500 flex gap-5 bg-red-500/5">
          <div className="w-12 h-12 rounded-full bg-red-500/10 flex items-center justify-center text-red-500">
             <AlertCircle size={24} />
          </div>
          <div>
            <h3 className="font-bold text-red-400">Analysis Error</h3>
            <p className="text-white/50 text-sm mt-1">{error}</p>
          </div>
        </div>
      )}

      {/* Analysis Results */}
      {analysis && !loading && (
        <div className="space-y-8 animate-fadeIn">
          {/* Header Card */}
          <div className="glass-card p-8 relative overflow-hidden">
            <div className="absolute top-0 right-0 p-8 opacity-5">
               <Activity size={120} />
            </div>
            
            <div className="flex flex-col md:flex-row justify-between items-start md:items-center gap-8 mb-10">
              <div>
                <p className="text-xs uppercase tracking-[0.3em] font-bold text-white/30 mb-2">{analysis.symbol} / MARKET PRICE</p>
                <h2 className="text-5xl font-display font-black text-white">${analysis.current_price.toLocaleString()}</h2>
              </div>
              <div className={`flex items-center gap-6 p-4 rounded-2xl bg-white/5 border ${analysis.trend === 'BULLISH' ? 'border-green-500/20 text-green-400' : 'border-red-500/20 text-red-400'}`}>
                {analysis.trend === 'BULLISH' ? <TrendingUp size={40} /> : <TrendingDown size={40} />}
                <div>
                  <div className="text-[10px] uppercase font-bold opacity-50 mb-1">Market Sentiment</div>
                  <div className="font-display font-black text-2xl tracking-tight">{analysis.trend}</div>
                  <div className="text-sm font-bold opacity-80">{analysis.confidence.toFixed(0)}% Confidence</div>
                </div>
              </div>
            </div>

            {/* Key Metrics Grid */}
            <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
              <MetricBox label="EMA 8" value={analysis.ema8} />
              <MetricBox label="EMA 34" value={analysis.ema34} />
              <MetricBox label="MA 50" value={analysis.sma50} />
              <MetricBox label="MA 200" value={analysis.sma200} />
            </div>
          </div>

          {/* Levels & Conditions */}
          <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
            {/* Support */}
            <div className="glass-card p-8 border-b-4 border-b-green-500/30">
              <h3 className="text-xl font-display font-bold mb-6 text-green-400 flex items-center gap-3">
                 <Shield size={20} />
                 Support Zones
              </h3>
              <div className="space-y-3">
                {analysis.support.map((level, idx) => (
                  <div key={idx} className="flex justify-between items-center bg-white/5 rounded-xl p-4 group hover:bg-white/10 transition-colors">
                    <span className="text-white/30 text-xs font-bold">LVL {idx + 1}</span>
                    <span className="font-display font-bold text-white">${level.toLocaleString()}</span>
                  </div>
                ))}
              </div>
            </div>

            {/* Resistance */}
            <div className="glass-card p-8 border-b-4 border-b-red-500/30">
              <h3 className="text-xl font-display font-bold mb-6 text-red-400 flex items-center gap-3">
                 <BarChart3 size={20} />
                 Resistance
              </h3>
              <div className="space-y-3">
                {analysis.resistance.map((level, idx) => (
                  <div key={idx} className="flex justify-between items-center bg-white/5 rounded-xl p-4 group hover:bg-white/10 transition-colors">
                    <span className="text-white/30 text-xs font-bold">LVL {idx + 1}</span>
                    <span className="font-display font-bold text-white">${level.toLocaleString()}</span>
                  </div>
                ))}
              </div>
            </div>

            {/* Market Health */}
            <div className="glass-card p-8 border-b-4 border-b-accent-gold/30">
              <h3 className="text-xl font-display font-bold mb-6 text-accent-gold flex items-center gap-3">
                 <Activity size={20} />
                 Health Check
              </h3>
              <div className="space-y-6">
                {analysis.rsi && (
                  <div className="p-4 bg-white/5 rounded-xl">
                    <div className="flex justify-between items-center mb-2">
                       <span className="text-white/30 text-xs font-bold">RSI (14)</span>
                       <span className="font-display font-bold text-white">{analysis.rsi.toFixed(1)}</span>
                    </div>
                    <div className="w-full h-1 bg-white/10 rounded-full overflow-hidden">
                       <div className="h-full bg-accent-gold" style={{ width: `${analysis.rsi}%` }} />
                    </div>
                  </div>
                )}
                {analysis.funding_rate && (
                  <div className="p-4 bg-white/5 rounded-xl">
                    <p className="text-white/30 text-xs font-bold mb-2">FUNDING RATE</p>
                    <div className="flex justify-between items-end">
                       <span className="text-2xl font-display font-bold text-white">{analysis.funding_rate.funding_rate_percent.toFixed(4)}%</span>
                       <span className="px-2 py-1 bg-white/10 rounded text-[10px] font-black uppercase text-accent-cyan tracking-widest">{analysis.funding_rate.status}</span>
                    </div>
                  </div>
                )}
              </div>
            </div>
          </div>

          {/* AI Synthesis */}
          <div className="glass-card p-8 relative overflow-hidden group">
            <div className="absolute top-0 right-0 p-8 text-accent-cyan/5 group-hover:scale-110 transition-transform duration-700">
               <Sparkles size={160} />
            </div>
            <h3 className="text-xl font-display font-bold mb-6 text-accent-cyan flex items-center gap-3">
               <Sparkles size={20} />
               AI Market Synthesis
            </h3>
            <div className="relative z-10 text-white/80 whitespace-pre-wrap leading-relaxed text-lg font-medium max-w-4xl">
              {analysis.analysis}
            </div>
          </div>
        </div>
      )}
    </div>
  )
}

function MetricBox({ label, value }: { label: string; value: number | null | undefined }) {
  return (
    <div className="bg-white/5 border border-white/5 rounded-2xl p-5 hover:bg-white/10 transition-colors group">
      <p className="text-white/30 text-[10px] font-black uppercase tracking-widest mb-2 group-hover:text-accent-purple transition-colors">{label}</p>
      <p className="text-xl font-display font-bold text-white">
        {typeof value === 'number' && Number.isFinite(value) ? `$${value.toLocaleString()}` : 'n/a'}
      </p>
    </div>
  )
}
