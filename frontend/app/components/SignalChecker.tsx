'use client'

import React, { useState } from 'react'
import { marketAPI } from '@/lib/api'
import { SignalVerification } from '@/types/market'
import { Loader2, AlertCircle, CheckCircle, AlertTriangle } from 'lucide-react'

export default function SignalChecker() {
  const [formData, setFormData] = useState({
    symbol: 'BTC/USDT',
    direction: 'LONG' as 'LONG' | 'SHORT',
    entryPrice: '',
    entryZoneLow: '',
    entryZoneHigh: '',
    target1: '',
    target2: '',
    target3: '',
    stopLoss: '',
  })

  const [result, setResult] = useState<SignalVerification | null>(null)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)

  const handleChange = (e: React.ChangeEvent<HTMLInputElement | HTMLSelectElement>) => {
    const { name, value } = e.target
    setFormData((prev) => ({
      ...prev,
      [name]: value,
    }))
  }

  const handleCheck = async (e: React.FormEvent) => {
    e.preventDefault()
    setLoading(true)
    setError(null)

    try {
      const targets = [formData.target1, formData.target2, formData.target3]
        .filter((t) => t)
        .map(Number)

      if (!targets.length) {
        setError('Please provide at least one target')
        setLoading(false)
        return
      }

      const data = await marketAPI.checkSignal(
        formData.symbol,
        formData.direction,
        Number(formData.entryPrice),
        Number(formData.entryZoneLow),
        Number(formData.entryZoneHigh),
        targets,
        Number(formData.stopLoss)
      )

      setResult(data)
    } catch (err: any) {
      setError(err.message || 'Signal check failed')
      setResult(null)
    } finally {
      setLoading(false)
    }
  }

  const getStatusColor = (status: string) => {
    if (status === 'VALID') return 'text-crypto-emerald border-crypto-emerald/30 bg-crypto-emerald/10'
    if (status === 'WAIT') return 'text-crypto-gold border-crypto-gold/30 bg-crypto-gold/10'
    if (status === 'RISKY') return 'text-orange-500 border-orange-500/30 bg-orange-500/10'
    return 'text-crypto-red border-crypto-red/30 bg-crypto-red/10'
  }

  const getStatusIcon = (status: string) => {
    if (status === 'VALID') return <CheckCircle size={24} />
    if (status === 'WAIT' || status === 'RISKY') return <AlertTriangle size={24} />
    return <AlertCircle size={24} />
  }

  return (
    <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
      {/* Form */}
      <div className="lg:col-span-1">
        <form onSubmit={handleCheck} className="bg-dark-800 rounded-lg p-6 border border-dark-700 space-y-4">
          <h2 className="text-xl font-semibold mb-4">Check Signal</h2>

          <div>
            <label className="block text-sm font-medium text-gray-300 mb-2">Symbol</label>
            <input
              type="text"
              name="symbol"
              value={formData.symbol}
              onChange={handleChange}
              placeholder="BTC/USDT"
              className="w-full bg-dark-700 border border-dark-600 rounded px-3 py-2 text-white placeholder-gray-500 focus:outline-none focus:border-crypto-blue"
            />
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-300 mb-2">Direction</label>
            <select
              name="direction"
              value={formData.direction}
              onChange={handleChange}
              className="w-full bg-dark-700 border border-dark-600 rounded px-3 py-2 text-white focus:outline-none focus:border-crypto-blue"
            >
              <option value="LONG">LONG</option>
              <option value="SHORT">SHORT</option>
            </select>
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-300 mb-2">Entry Price</label>
            <input
              type="number"
              name="entryPrice"
              value={formData.entryPrice}
              onChange={handleChange}
              placeholder="0.00"
              step="0.01"
              className="w-full bg-dark-700 border border-dark-600 rounded px-3 py-2 text-white placeholder-gray-500 focus:outline-none focus:border-crypto-blue"
            />
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-300 mb-2">Entry Zone Low</label>
            <input
              type="number"
              name="entryZoneLow"
              value={formData.entryZoneLow}
              onChange={handleChange}
              placeholder="0.00"
              step="0.01"
              className="w-full bg-dark-700 border border-dark-600 rounded px-3 py-2 text-white placeholder-gray-500 focus:outline-none focus:border-crypto-blue"
            />
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-300 mb-2">Entry Zone High</label>
            <input
              type="number"
              name="entryZoneHigh"
              value={formData.entryZoneHigh}
              onChange={handleChange}
              placeholder="0.00"
              step="0.01"
              className="w-full bg-dark-700 border border-dark-600 rounded px-3 py-2 text-white placeholder-gray-500 focus:outline-none focus:border-crypto-blue"
            />
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-300 mb-2">Targets</label>
            <input
              type="number"
              name="target1"
              value={formData.target1}
              onChange={handleChange}
              placeholder="Target 1"
              step="0.01"
              className="w-full bg-dark-700 border border-dark-600 rounded px-3 py-2 text-white placeholder-gray-500 focus:outline-none focus:border-crypto-blue mb-2"
            />
            <input
              type="number"
              name="target2"
              value={formData.target2}
              onChange={handleChange}
              placeholder="Target 2"
              step="0.01"
              className="w-full bg-dark-700 border border-dark-600 rounded px-3 py-2 text-white placeholder-gray-500 focus:outline-none focus:border-crypto-blue mb-2"
            />
            <input
              type="number"
              name="target3"
              value={formData.target3}
              onChange={handleChange}
              placeholder="Target 3"
              step="0.01"
              className="w-full bg-dark-700 border border-dark-600 rounded px-3 py-2 text-white placeholder-gray-500 focus:outline-none focus:border-crypto-blue"
            />
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-300 mb-2">Stop Loss</label>
            <input
              type="number"
              name="stopLoss"
              value={formData.stopLoss}
              onChange={handleChange}
              placeholder="0.00"
              step="0.01"
              className="w-full bg-dark-700 border border-dark-600 rounded px-3 py-2 text-white placeholder-gray-500 focus:outline-none focus:border-crypto-blue"
            />
          </div>

          <button
            type="submit"
            disabled={loading}
            className="w-full bg-crypto-blue text-white py-2 rounded-lg hover:bg-blue-600 disabled:opacity-50 transition font-medium"
          >
            {loading ? 'Checking...' : 'Check Signal'}
          </button>
        </form>
      </div>

      {/* Results */}
      <div className="lg:col-span-2 space-y-4">
        {loading && (
          <div className="bg-dark-800 rounded-lg p-8 border border-dark-700 flex flex-col items-center justify-center gap-4">
            <Loader2 size={32} className="animate-spin text-crypto-blue" />
            <p className="text-gray-400">Checking signal...</p>
          </div>
        )}

        {error && (
          <div className="bg-dark-800 rounded-lg p-6 border border-crypto-red/30 flex gap-4">
            <AlertCircle size={24} className="text-crypto-red flex-shrink-0" />
            <div>
              <h3 className="font-semibold text-crypto-red">Error</h3>
              <p className="text-gray-400 text-sm mt-1">{error}</p>
            </div>
          </div>
        )}

        {result && !loading && (
          <div className="space-y-4">
            {/* Status */}
            <div className={`bg-dark-800 rounded-lg p-6 border-2 ${getStatusColor(result.status)} flex items-start gap-4`}>
              {getStatusIcon(result.status)}
              <div className="flex-1">
                <h3 className="text-2xl font-bold mb-1">{result.status}</h3>
                <p className="text-sm opacity-90">Risk Score: {result.risk_score.toFixed(0)}%</p>
                <p className="text-sm opacity-90">Confidence: {result.confidence.toFixed(0)}%</p>
              </div>
            </div>

            {/* Reasons */}
            {result.reasons.length > 0 && (
              <div className="bg-dark-800 rounded-lg p-6 border border-dark-700">
                <h3 className="text-lg font-semibold mb-4 text-crypto-emerald">✓ Positive Factors</h3>
                <div className="space-y-2">
                  {result.reasons.map((reason, idx) => (
                    <p key={idx} className="text-gray-300 text-sm">
                      {reason}
                    </p>
                  ))}
                </div>
              </div>
            )}

            {/* Warnings */}
            {result.warnings.length > 0 && (
              <div className="bg-dark-800 rounded-lg p-6 border border-crypto-gold/30">
                <h3 className="text-lg font-semibold mb-4 text-crypto-gold">⚠ Warnings</h3>
                <div className="space-y-2">
                  {result.warnings.map((warning, idx) => (
                    <p key={idx} className="text-crypto-gold text-sm">
                      {warning}
                    </p>
                  ))}
                </div>
              </div>
            )}

            {/* AI Analysis */}
            <div className="bg-dark-800 rounded-lg p-6 border border-crypto-blue/30">
              <h3 className="text-lg font-semibold mb-4 text-crypto-blue">Professional Assessment</h3>
              <div className="text-gray-300 whitespace-pre-wrap leading-relaxed text-sm">
                {result.ai_reasoning}
              </div>
            </div>
          </div>
        )}
      </div>
    </div>
  )
}
