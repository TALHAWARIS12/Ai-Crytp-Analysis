'use client'

import React, { useState, useEffect } from 'react'
import { marketAPI } from '@/lib/api'
import { CoinAnalysis } from '@/types/market'
import { Loader2, AlertCircle, TrendingUp, TrendingDown } from 'lucide-react'

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
    <div className="space-y-6">
      {/* Search Form */}
      <form onSubmit={handleSearch} className="flex gap-2">
        <input
          type="text"
          value={searchInput}
          onChange={(e) => setSearchInput(e.target.value)}
          placeholder="Enter coin symbol (e.g., BTC, ETH, RARE)"
          className="flex-1 bg-dark-800 border border-dark-700 rounded-lg px-4 py-2 text-white placeholder-gray-500 focus:outline-none focus:border-crypto-blue"
        />
        <button
          type="submit"
          className="bg-crypto-blue text-white px-6 py-2 rounded-lg hover:bg-blue-600 transition font-medium"
        >
          Analyze
        </button>
      </form>

      {/* Loading State */}
      {loading && (
        <div className="bg-dark-800 rounded-lg p-8 border border-dark-700 flex flex-col items-center justify-center gap-4">
          <Loader2 size={32} className="animate-spin text-crypto-blue" />
          <p className="text-gray-400">Analyzing {searchInput}...</p>
        </div>
      )}

      {/* Error State */}
      {error && (
        <div className="bg-dark-800 rounded-lg p-6 border border-crypto-red/30 flex gap-4">
          <AlertCircle size={24} className="text-crypto-red flex-shrink-0 mt-1" />
          <div>
            <h3 className="font-semibold text-crypto-red mb-1">Analysis Failed</h3>
            <p className="text-gray-400 text-sm">{error}</p>
          </div>
        </div>
      )}

      {/* Analysis Results */}
      {analysis && !loading && (
        <div className="space-y-4">
          {/* Header Card */}
          <div className="bg-dark-800 rounded-lg p-6 border border-dark-700">
            <div className="flex justify-between items-start mb-4">
              <div>
                <h2 className="text-3xl font-bold text-white">{analysis.current_price.toLocaleString()}</h2>
                <p className="text-gray-500 mt-1">{analysis.symbol}</p>
              </div>
              <div className={`flex items-center gap-2 ${analysis.trend === 'BULLISH' ? 'text-crypto-emerald' : 'text-crypto-red'}`}>
                {analysis.trend === 'BULLISH' ? <TrendingUp size={24} /> : <TrendingDown size={24} />}
                <div>
                  <div className="font-bold text-lg">{analysis.trend}</div>
                  <div className="text-sm">{analysis.confidence.toFixed(0)}%</div>
                </div>
              </div>
            </div>

            {/* Key Metrics */}
            <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
              <MetricBox label="EMA 8" value={analysis.ema8} />
              <MetricBox label="EMA 34" value={analysis.ema34} />
              <MetricBox label="MA 50" value={analysis.sma50} />
              <MetricBox label="MA 200" value={analysis.sma200} />
            </div>
          </div>

          {/* Levels Card */}
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div className="bg-dark-800 rounded-lg p-6 border border-dark-700">
              <h3 className="text-lg font-semibold mb-4 text-crypto-emerald">Support Levels</h3>
              <div className="space-y-2">
                {analysis.support.map((level, idx) => (
                  <div key={idx} className="flex justify-between items-center bg-dark-700 rounded p-3">
                    <span className="text-gray-400">Level {idx + 1}</span>
                    <span className="font-semibold">${level.toFixed(2)}</span>
                  </div>
                ))}
              </div>
            </div>

            <div className="bg-dark-800 rounded-lg p-6 border border-dark-700">
              <h3 className="text-lg font-semibold mb-4 text-crypto-red">Resistance Levels</h3>
              <div className="space-y-2">
                {analysis.resistance.map((level, idx) => (
                  <div key={idx} className="flex justify-between items-center bg-dark-700 rounded p-3">
                    <span className="text-gray-400">Level {idx + 1}</span>
                    <span className="font-semibold">${level.toFixed(2)}</span>
                  </div>
                ))}
              </div>
            </div>
          </div>

          {/* Market Conditions */}
          <div className="bg-dark-800 rounded-lg p-6 border border-dark-700">
            <h3 className="text-lg font-semibold mb-4">Market Conditions</h3>
            <div className="space-y-3">
              {analysis.rsi && (
                <div className="flex justify-between items-center">
                  <span className="text-gray-400">RSI (14)</span>
                  <span className="font-semibold">{analysis.rsi.toFixed(1)}</span>
                </div>
              )}
              {analysis.funding_rate && (
                <div className="flex justify-between items-center">
                  <span className="text-gray-400">Funding Rate</span>
                  <div>
                    <span className="font-semibold">{analysis.funding_rate.funding_rate_percent.toFixed(3)}%</span>
                    <span className="text-xs text-gray-500 ml-2">({analysis.funding_rate.status})</span>
                  </div>
                </div>
              )}
            </div>
          </div>

          {/* AI Analysis */}
          <div className="bg-dark-800 rounded-lg p-6 border border-crypto-blue/30">
            <h3 className="text-lg font-semibold mb-4 text-crypto-blue">AI Analysis</h3>
            <div className="text-gray-300 whitespace-pre-wrap leading-relaxed text-sm">
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
    <div className="bg-dark-700 rounded p-4">
      <p className="text-gray-500 text-sm mb-1">{label}</p>
      <p className="text-lg font-semibold text-white">
        {typeof value === 'number' && Number.isFinite(value) ? `$${value.toFixed(2)}` : 'n/a'}
      </p>
    </div>
  )
}
