'use client'

import React, { useState } from 'react'
import { marketAPI } from '@/lib/api'
import { StrategyValidation } from '@/types/market'
import { Loader2, AlertCircle, CheckCircle, AlertTriangle, Zap, Target, ShieldAlert, BarChart, Info, Sparkles } from 'lucide-react'

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

  const getStatusClasses = (status: string) => {
    if (status.includes('VALID LONG')) return 'border-green-500/50 bg-green-500/10 text-green-400'
    if (status.includes('VALID SHORT')) return 'border-red-500/50 bg-red-500/10 text-red-400'
    if (status.includes('WAIT')) return 'border-accent-gold/50 bg-accent-gold/10 text-accent-gold'
    return 'border-red-500/50 bg-red-500/10 text-red-400'
  }

  const getStatusIcon = (status: string) => {
    if (status.includes('VALID')) return <CheckCircle size={32} />
    if (status.includes('WAIT')) return <AlertTriangle size={32} />
    return <AlertCircle size={32} />
  }

  return (
    <div className="space-y-8 fade-in">
      {/* Input Form */}
      <form onSubmit={handleValidate} className="glass-card p-8 space-y-8 relative overflow-hidden">
        <div className="absolute top-0 right-0 p-8 opacity-5">
           <Zap size={120} />
        </div>
        
        <div>
          <h2 className="text-2xl font-display font-bold mb-2 flex items-center gap-3">
             <Target className="text-accent-gold" size={24} />
             Strategy Validator
          </h2>
          <p className="text-white/40 text-sm">Configure parameters to run AI multi-factor validation.</p>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
          <div className="space-y-2">
            <label className="block text-xs uppercase tracking-widest font-bold text-white/30 ml-1">Symbol</label>
            <input
              type="text"
              value={searchInput}
              onChange={(e) => setSearchInput(e.target.value)}
              placeholder="e.g. BTC, ETH"
              className="w-full bg-white/5 border border-white/10 rounded-xl px-4 py-3 text-white placeholder-white/20 focus:outline-none focus:border-accent-purple/50 transition-all"
            />
          </div>

          <div className="space-y-2">
            <label className="block text-xs uppercase tracking-widest font-bold text-white/30 ml-1">Direction</label>
            <div className="flex p-1 bg-white/5 border border-white/10 rounded-xl">
               <button 
                 type="button"
                 onClick={() => setDirection('LONG')}
                 className={`flex-1 py-2 rounded-lg font-bold text-sm transition-all ${direction === 'LONG' ? 'bg-green-500/20 text-green-400' : 'text-white/30 hover:text-white/50'}`}
               >
                 LONG
               </button>
               <button 
                 type="button"
                 onClick={() => setDirection('SHORT')}
                 className={`flex-1 py-2 rounded-lg font-bold text-sm transition-all ${direction === 'SHORT' ? 'bg-red-500/20 text-red-400' : 'text-white/30 hover:text-white/50'}`}
               >
                 SHORT
               </button>
            </div>
          </div>

          <div className="space-y-2">
            <label className="block text-xs uppercase tracking-widest font-bold text-white/30 ml-1">Timeframe</label>
            <select
              value={timeframe}
              onChange={(e) => setTimeframe(e.target.value)}
              className="w-full bg-white/5 border border-white/10 rounded-xl px-4 py-3 text-white focus:outline-none focus:border-accent-purple/50 appearance-none transition-all cursor-pointer"
            >
              <option value="1h">1H - Scalping</option>
              <option value="4h">4H - Swing</option>
              <option value="1d">1D - Position</option>
            </select>
          </div>
        </div>

        <button
          type="submit"
          disabled={loading}
          className="w-full btn-gold py-4"
        >
          {loading ? (
            <div className="flex items-center justify-center gap-3">
               <Loader2 className="animate-spin" size={20} />
               <span>Processing Strategy...</span>
            </div>
          ) : 'Run AI Validation'}
        </button>
      </form>

      {/* Loading State Skeleton */}
      {loading && (
        <div className="glass-card p-12 flex flex-col items-center justify-center gap-6">
          <div className="relative">
            <div className="absolute inset-0 bg-accent-purple blur-2xl opacity-20 animate-pulse" />
            <Loader2 size={48} className="animate-spin text-accent-purple relative z-10" />
          </div>
          <div className="text-center">
            <h3 className="text-xl font-bold mb-2 shimmer-text text-white">Analyzing Market Structure</h3>
            <p className="text-white/40 text-sm">Cross-referencing technical indicators and order flow...</p>
          </div>
        </div>
      )}

      {/* Error State */}
      {error && (
        <div className="glass-card p-6 border-l-4 border-l-red-500 flex gap-5 bg-red-500/5">
          <div className="w-12 h-12 rounded-full bg-red-500/10 flex items-center justify-center text-red-500">
             <ShieldAlert size={24} />
          </div>
          <div>
            <h3 className="font-bold text-red-400">System Notification</h3>
            <p className="text-white/50 text-sm mt-1">{error}</p>
          </div>
        </div>
      )}

      {/* Results Rendering */}
      {result && !loading && (
        <div className="space-y-8 animate-fadeIn">
          {/* Status Header Card */}
          <div className={`glass-card p-8 border-l-8 ${getStatusClasses(result.status)} flex flex-col md:flex-row items-center justify-between gap-8`}>
            <div className="flex items-center gap-6">
              <div className="p-4 rounded-2xl bg-white/5">
                {getStatusIcon(result.status)}
              </div>
              <div>
                <div className="text-xs uppercase tracking-widest font-bold opacity-50 mb-1">Validation Result</div>
                <h3 className="text-4xl font-display font-black tracking-tight">{result.status}</h3>
              </div>
            </div>
            <div className="text-right flex flex-col items-center md:items-end">
               <div className="text-xs uppercase tracking-widest font-bold opacity-50 mb-1">AI Confidence</div>
               <div className="text-4xl font-display font-black text-white">{result.confidence.toFixed(0)}%</div>
               <div className="w-32 h-1.5 bg-white/5 rounded-full mt-2 overflow-hidden">
                  <div className="h-full bg-accent-purple" style={{ width: `${result.confidence}%` }} />
               </div>
            </div>
          </div>

          <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
            {/* Technical Factors */}
            <div className="glass-card p-8">
              <h3 className="text-xl font-display font-bold mb-6 flex items-center gap-3">
                 <BarChart className="text-accent-purple" size={20} />
                 Technical Analysis
              </h3>
              <div className="space-y-4">
                {result.reasons.map((reason, idx) => (
                  <div key={idx} className="flex gap-4 p-4 rounded-xl bg-white/5 border border-white/5">
                    <div className="w-1.5 h-1.5 rounded-full bg-accent-purple mt-2 flex-shrink-0" />
                    <span className="text-white/70 text-sm leading-relaxed">{reason}</span>
                  </div>
                ))}
              </div>
            </div>

            {/* Risk Warnings */}
            <div className="glass-card p-8 border-accent-gold/20">
              <h3 className="text-xl font-display font-bold mb-6 flex items-center gap-3 text-accent-gold">
                 <ShieldAlert size={20} />
                 Risk Assessment
              </h3>
              {result.warnings && result.warnings.length > 0 ? (
                <div className="space-y-4">
                  {result.warnings.map((warning, idx) => (
                    <div key={idx} className="p-4 rounded-xl bg-accent-gold/5 border border-accent-gold/10 text-accent-gold text-sm flex gap-3">
                       <Info size={18} className="flex-shrink-0" />
                       {warning}
                    </div>
                  ))}
                </div>
              ) : (
                <div className="flex flex-col items-center justify-center py-12 text-white/20">
                   <CheckCircle size={48} className="mb-4 opacity-10" />
                   <p>No critical risks identified</p>
                </div>
              )}
            </div>
          </div>

          {/* Zones Section */}
          <div className="grid grid-cols-1 md:grid-cols-2 gap-8">
            <div className="glass-card p-8 border-b-4 border-b-green-500/30">
              <h3 className="text-xl font-display font-bold mb-8 text-green-400">Optimal Entry Zones</h3>
              <div className="space-y-6">
                {Object.entries(result.entry_zones).map(([zone, prices]: any) => (
                  <div key={zone} className="relative group">
                    <div className="absolute -inset-2 bg-green-500/5 rounded-2xl opacity-0 group-hover:opacity-100 transition-opacity" />
                    <div className="relative flex justify-between items-end border-b border-white/5 pb-4">
                       <div>
                          <p className="text-[10px] uppercase font-bold text-white/30 tracking-widest mb-1">{zone.replace('_', ' ')}</p>
                          <p className="text-2xl font-display font-bold text-white">
                            ${prices.low.toLocaleString()}
                          </p>
                       </div>
                       <div className="text-right">
                          <p className="text-[10px] uppercase font-bold text-white/30 tracking-widest mb-1">Target Max</p>
                          <p className="text-xl font-display font-bold text-white/60">
                            ${prices.high.toLocaleString()}
                          </p>
                       </div>
                    </div>
                  </div>
                ))}
              </div>
            </div>

            <div className="glass-card p-8 border-b-4 border-b-red-500/30">
              <h3 className="text-xl font-display font-bold mb-8 text-red-400">Risk Management</h3>
              <div className="space-y-8">
                <div className="flex justify-between items-center p-6 rounded-2xl bg-white/5 border border-white/10">
                  <div>
                    <p className="text-[10px] uppercase font-bold text-white/30 tracking-widest mb-1">Take Profit Target</p>
                    <p className="text-3xl font-display font-bold text-green-400">${result.exit_zones.take_profit.toLocaleString()}</p>
                  </div>
                  <div className="w-12 h-12 rounded-xl bg-green-500/10 flex items-center justify-center text-green-400">
                     <Target size={24} />
                  </div>
                </div>
                
                <div className="flex justify-between items-center p-6 rounded-2xl bg-white/5 border border-white/10">
                  <div>
                    <p className="text-[10px] uppercase font-bold text-white/30 tracking-widest mb-1">Hard Stop Loss</p>
                    <p className="text-3xl font-display font-bold text-red-400">${result.exit_zones.stop_loss.toLocaleString()}</p>
                  </div>
                  <div className="w-12 h-12 rounded-xl bg-red-500/10 flex items-center justify-center text-red-400">
                     <ShieldAlert size={24} />
                  </div>
                </div>
              </div>
            </div>
          </div>

          {/* AI Narrative */}
          <div className="glass-card p-8 relative overflow-hidden group">
            <div className="absolute top-0 right-0 p-8 text-accent-purple/5 group-hover:scale-110 transition-transform duration-700">
               <Sparkles size={160} />
            </div>
            <h3 className="text-xl font-display font-bold mb-6 text-accent-purple flex items-center gap-3">
               <Sparkles size={20} />
               Executive Intelligence Summary
            </h3>
            <div className="relative z-10 text-white/80 whitespace-pre-wrap leading-relaxed text-lg font-medium max-w-4xl">
              {result.ai_reasoning}
            </div>
          </div>
        </div>
      )}
    </div>
  )
}
