'use client'

import React, { useState } from 'react'
import { marketAPI } from '@/lib/api'
import { StrategyValidation } from '@/types/market'
import { Loader2, AlertCircle, CheckCircle, AlertTriangle } from 'lucide-react'

interface Props {
  symbol: string
}

export default function StrategyValidator({ symbol }: Props) {
  const [searchInput, setSearchInput] = useState(symbol)
  const [direction, setDirection] = useState<'LONG' | 'SHORT'>('LONG')
  const [timeframe, setTimeframe] = useState('4h')
  const [result, setResult] = useState<StrategyValidation | null>(null)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)

  const handleValidate = async (e: React.FormEvent) => {
    e.preventDefault()
    setLoading(true)
    setError(null)

    try {
      const data = await marketAPI.validateStrategy(searchInput, direction, timeframe)
      setResult(data)
    } catch (err: any) {
      setError(err.message || 'Validation failed')
      setResult(null)
    } finally {
      setLoading(false)
    }
  }

  const getStatusColor = (status: string) => {
    if (status.includes('VALID LONG')) return 'text-crypto-emerald border-crypto-emerald/30 bg-crypto-emerald/10'
    if (status.includes('VALID SHORT')) return 'text-crypto-red border-crypto-red/30 bg-crypto-red/10'
    if (status.includes('WAIT')) return 'text-crypto-gold border-crypto-gold/30 bg-crypto-gold/10'
    return 'text-crypto-red border-crypto-red/30 bg-crypto-red/10'
  }

  const getStatusIcon = (status: string) => {
    if (status.includes('VALID')) return <CheckCircle size={24} />
    if (status.includes('WAIT')) return <AlertTriangle size={24} />
    return <AlertCircle size={24} />
  }

  return (
    <div className="space-y-6">
      {/* Input Form */}
      <form onSubmit={handleValidate} className="bg-dark-800 rounded-lg p-6 border border-dark-700 space-y-4">
        <h2 className="text-xl font-semibold mb-4">Strategy Validator</h2>

        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          <div>
            <label className="block text-sm font-medium text-gray-300 mb-2">Symbol</label>
            <input
              type="text"
              value={searchInput}
              onChange={(e) => setSearchInput(e.target.value)}
              placeholder="BTC, ETH, RARE..."
              className="w-full bg-dark-700 border border-dark-600 rounded px-3 py-2 text-white placeholder-gray-500 focus:outline-none focus:border-crypto-blue"
            />
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-300 mb-2">Direction</label>
            <select
              value={direction}
              onChange={(e) => setDirection(e.target.value as 'LONG' | 'SHORT')}
              className="w-full bg-dark-700 border border-dark-600 rounded px-3 py-2 text-white focus:outline-none focus:border-crypto-blue"
            >
              <option value="LONG">LONG</option>
              <option value="SHORT">SHORT</option>
            </select>
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-300 mb-2">Timeframe</label>
            <select
              value={timeframe}
              onChange={(e) => setTimeframe(e.target.value)}
              className="w-full bg-dark-700 border border-dark-600 rounded px-3 py-2 text-white focus:outline-none focus:border-crypto-blue"
            >
              <option value="1h">1H</option>
              <option value="4h">4H</option>
              <option value="1d">1D</option>
            </select>
          </div>
        </div>

        <button
          type="submit"
          disabled={loading}
          className="w-full bg-crypto-blue text-white py-2 rounded-lg hover:bg-blue-600 disabled:opacity-50 transition font-medium"
        >
          {loading ? 'Validating...' : 'Validate Strategy'}
        </button>
      </form>

      {/* Loading State */}
      {loading && (
        <div className="bg-dark-800 rounded-lg p-8 border border-dark-700 flex flex-col items-center justify-center gap-4">
          <Loader2 size={32} className="animate-spin text-crypto-blue" />
          <p className="text-gray-400">Validating strategy...</p>
        </div>
      )}

      {/* Error State */}
      {error && (
        <div className="bg-dark-800 rounded-lg p-6 border border-crypto-red/30 flex gap-4">
          <AlertCircle size={24} className="text-crypto-red flex-shrink-0" />
          <div>
            <h3 className="font-semibold text-crypto-red">Validation Error</h3>
            <p className="text-gray-400 text-sm mt-1">{error}</p>
          </div>
        </div>
      )}

      {/* Results */}
      {result && !loading && (
        <div className="space-y-4">
          {/* Status Card */}
          <div className={`bg-dark-800 rounded-lg p-6 border-2 ${getStatusColor(result.status)} flex items-start gap-4`}>
            {getStatusIcon(result.status)}
            <div className="flex-1">
              <h3 className="text-2xl font-bold mb-2">{result.status}</h3>
              <p className="text-sm opacity-90">Confidence: {result.confidence.toFixed(0)}%</p>
            </div>
          </div>

          {/* Reasons */}
          <div className="bg-dark-800 rounded-lg p-6 border border-dark-700">
            <h3 className="text-lg font-semibold mb-4">Technical Analysis</h3>
            <div className="space-y-2">
              {result.reasons.map((reason, idx) => (
                <div key={idx} className="text-gray-300 text-sm">
                  {reason}
                </div>
              ))}
            </div>
          </div>

          {/* Warnings */}
          {result.warnings && result.warnings.length > 0 && (
            <div className="bg-dark-800 rounded-lg p-6 border border-crypto-gold/30">
              <h3 className="text-lg font-semibold mb-4 text-crypto-gold">⚠ Warnings</h3>
              <div className="space-y-2">
                {result.warnings.map((warning, idx) => (
                  <div key={idx} className="text-crypto-gold text-sm">
                    {warning}
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* Entry/Exit Zones */}
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div className="bg-dark-800 rounded-lg p-6 border border-dark-700">
              <h3 className="text-lg font-semibold mb-4 text-crypto-emerald">Entry Zones</h3>
              <div className="space-y-3">
                {Object.entries(result.entry_zones).map(([zone, prices]: any) => (
                  <div key={zone} className="bg-dark-700 rounded p-3">
                    <p className="text-gray-400 text-sm capitalize mb-1">{zone.replace('_', ' ')}</p>
                    <p className="font-semibold">
                      ${prices.low.toFixed(2)} - ${prices.high.toFixed(2)}
                    </p>
                  </div>
                ))}
              </div>
            </div>

            <div className="bg-dark-800 rounded-lg p-6 border border-dark-700">
              <h3 className="text-lg font-semibold mb-4 text-crypto-red">Exit Zones</h3>
              <div className="space-y-3">
                <div className="bg-dark-700 rounded p-3">
                  <p className="text-gray-400 text-sm mb-1">Take Profit</p>
                  <p className="font-semibold">${result.exit_zones.take_profit.toFixed(2)}</p>
                </div>
                <div className="bg-dark-700 rounded p-3">
                  <p className="text-gray-400 text-sm mb-1">Stop Loss</p>
                  <p className="font-semibold">${result.exit_zones.stop_loss.toFixed(2)}</p>
                </div>
              </div>
            </div>
          </div>

          {/* AI Reasoning */}
          <div className="bg-dark-800 rounded-lg p-6 border border-crypto-blue/30">
            <h3 className="text-lg font-semibold mb-4 text-crypto-blue">Professional Analysis</h3>
            <div className="text-gray-300 whitespace-pre-wrap leading-relaxed text-sm">
              {result.ai_reasoning}
            </div>
          </div>
        </div>
      )}
    </div>
  )
}
