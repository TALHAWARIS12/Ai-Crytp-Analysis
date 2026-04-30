'use client'

import React, { useState } from 'react'
import { marketAPI } from '@/lib/api'
import { SignalVerification } from '@/types/market'
import { Loader2, AlertCircle, CheckCircle, AlertTriangle, ShieldCheck, Target, Zap, Activity, Info, BarChart } from 'lucide-react'

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

  const getStatusClasses = (status: string) => {
    if (status === 'VALID') return 'border-green-500/50 bg-green-500/10 text-green-400'
    if (status === 'WAIT') return 'border-accent-gold/50 bg-accent-gold/10 text-accent-gold'
    if (status === 'RISKY') return 'border-orange-500/50 bg-orange-500/10 text-orange-400'
    return 'border-red-500/50 bg-red-500/10 text-red-400'
  }

  const getStatusIcon = (status: string) => {
    if (status === 'VALID') return <ShieldCheck size={32} />
    if (status === 'WAIT' || status === 'RISKY') return <AlertTriangle size={32} />
    return <AlertCircle size={32} />
  }

  return (
    <div className="grid grid-cols-1 lg:grid-cols-12 gap-8 fade-in">
      {/* Form Section */}
      <div className="lg:col-span-5">
        <form onSubmit={handleCheck} className="glass-card p-8 space-y-6 sticky top-24">
          <div className="mb-8">
            <h2 className="text-2xl font-display font-bold mb-2 flex items-center gap-3">
               <Zap size={24} className="text-accent-gold" />
               Signal Verifier
            </h2>
            <p className="text-white/40 text-sm">Input your trade signal for AI-powered verification.</p>
          </div>

          <div className="grid grid-cols-2 gap-4">
            <div className="space-y-2">
              <label className="text-[10px] uppercase font-bold text-white/30 ml-1">Symbol</label>
              <input
                type="text"
                name="symbol"
                value={formData.symbol}
                onChange={handleChange}
                className="w-full bg-white/5 border border-white/10 rounded-xl px-4 py-3 text-white focus:outline-none focus:border-accent-purple/50 transition-all"
              />
            </div>
            <div className="space-y-2">
              <label className="text-[10px] uppercase font-bold text-white/30 ml-1">Direction</label>
              <select
                name="direction"
                value={formData.direction}
                onChange={handleChange}
                className="w-full bg-white/5 border border-white/10 rounded-xl px-4 py-3 text-white focus:outline-none focus:border-accent-purple/50 appearance-none cursor-pointer"
              >
                <option value="LONG">LONG</option>
                <option value="SHORT">SHORT</option>
              </select>
            </div>
          </div>

          <div className="space-y-2">
            <label className="text-[10px] uppercase font-bold text-white/30 ml-1">Current Entry Price</label>
            <input
              type="number"
              name="entryPrice"
              value={formData.entryPrice}
              onChange={handleChange}
              placeholder="0.00"
              step="0.0001"
              className="w-full bg-white/5 border border-white/10 rounded-xl px-4 py-3 text-white focus:outline-none focus:border-accent-purple/50"
            />
          </div>

          <div className="grid grid-cols-2 gap-4">
            <div className="space-y-2">
              <label className="text-[10px] uppercase font-bold text-white/30 ml-1">Entry Zone Low</label>
              <input
                type="number"
                name="entryZoneLow"
                value={formData.entryZoneLow}
                onChange={handleChange}
                placeholder="Min"
                step="0.0001"
                className="w-full bg-white/5 border border-white/10 rounded-xl px-4 py-3 text-white focus:outline-none focus:border-accent-purple/50"
              />
            </div>
            <div className="space-y-2">
              <label className="text-[10px] uppercase font-bold text-white/30 ml-1">Entry Zone High</label>
              <input
                type="number"
                name="entryZoneHigh"
                value={formData.entryZoneHigh}
                onChange={handleChange}
                placeholder="Max"
                step="0.0001"
                className="w-full bg-white/5 border border-white/10 rounded-xl px-4 py-3 text-white focus:outline-none focus:border-accent-purple/50"
              />
            </div>
          </div>

          <div className="space-y-2">
            <label className="text-[10px] uppercase font-bold text-white/30 ml-1">Take Profit Targets</label>
            <div className="space-y-2">
               <input
                 type="number"
                 name="target1"
                 value={formData.target1}
                 onChange={handleChange}
                 placeholder="Target 1"
                 step="0.0001"
                 className="w-full bg-white/5 border border-white/10 rounded-xl px-4 py-2.5 text-white focus:outline-none focus:border-accent-cyan/50"
               />
               <input
                 type="number"
                 name="target2"
                 value={formData.target2}
                 onChange={handleChange}
                 placeholder="Target 2"
                 step="0.0001"
                 className="w-full bg-white/5 border border-white/10 rounded-xl px-4 py-2.5 text-white focus:outline-none focus:border-accent-cyan/50"
               />
               <input
                 type="number"
                 name="target3"
                 value={formData.target3}
                 onChange={handleChange}
                 placeholder="Target 3"
                 step="0.0001"
                 className="w-full bg-white/5 border border-white/10 rounded-xl px-4 py-2.5 text-white focus:outline-none focus:border-accent-cyan/50"
               />
            </div>
          </div>

          <div className="space-y-2">
            <label className="text-[10px] uppercase font-bold text-white/30 ml-1">Stop Loss</label>
            <input
              type="number"
              name="stopLoss"
              value={formData.stopLoss}
              onChange={handleChange}
              placeholder="0.00"
              step="0.0001"
              className="w-full bg-white/5 border border-red-500/20 rounded-xl px-4 py-3 text-white focus:outline-none focus:border-red-500/50"
            />
          </div>

          <button
            type="submit"
            disabled={loading}
            className="w-full btn-gold py-4 mt-4"
          >
            {loading ? (
              <div className="flex items-center justify-center gap-3">
                 <Loader2 size={18} className="animate-spin" />
                 <span>Verifying...</span>
              </div>
            ) : 'Verify Signal Intelligence'}
          </button>
        </form>
      </div>

      {/* Results Section */}
      <div className="lg:col-span-7 space-y-6">
        {loading && (
          <div className="glass-card p-20 flex flex-col items-center justify-center gap-6">
            <div className="relative">
               <div className="absolute inset-0 bg-accent-gold blur-2xl opacity-20 animate-pulse" />
               <Loader2 size={64} className="animate-spin text-accent-gold relative z-10" />
            </div>
            <div className="text-center">
              <h3 className="text-2xl font-display font-bold mb-2 shimmer-text text-white">Quantum Signal Analysis</h3>
              <p className="text-white/40 max-w-sm mx-auto">Evaluating risk-to-reward ratios and multi-exchange order flow consistency...</p>
            </div>
          </div>
        )}

        {error && (
          <div className="glass-card p-6 border-l-4 border-l-red-500 flex gap-5 bg-red-500/5">
            <div className="w-12 h-12 rounded-full bg-red-500/10 flex items-center justify-center text-red-500">
               <AlertCircle size={24} />
            </div>
            <div>
              <h3 className="font-bold text-red-400">Processing Error</h3>
              <p className="text-white/50 text-sm mt-1">{error}</p>
            </div>
          </div>
        )}

        {result && !loading && (
          <div className="space-y-8 animate-fadeIn">
            {/* Verdict Header */}
            <div className={`glass-card p-8 border-l-8 ${getStatusClasses(result.status)} flex flex-col md:flex-row items-center justify-between gap-8`}>
              <div className="flex items-center gap-6">
                <div className="p-4 rounded-2xl bg-white/5">
                  {getStatusIcon(result.status)}
                </div>
                <div>
                  <div className="text-xs uppercase tracking-widest font-bold opacity-50 mb-1">Signal Verdict</div>
                  <h3 className="text-4xl font-display font-black tracking-tight">{result.status}</h3>
                </div>
              </div>
              <div className="flex gap-8">
                 <div className="text-right">
                    <div className="text-[10px] uppercase font-bold opacity-50 mb-1">Risk Score</div>
                    <div className={`text-2xl font-display font-black ${result.risk_score < 30 ? 'text-green-400' : result.risk_score < 60 ? 'text-accent-gold' : 'text-red-400'}`}>
                      {result.risk_score.toFixed(0)}%
                    </div>
                 </div>
                 <div className="text-right">
                    <div className="text-[10px] uppercase font-bold opacity-50 mb-1">Confidence</div>
                    <div className="text-2xl font-display font-black text-white">
                      {result.confidence.toFixed(0)}%
                    </div>
                 </div>
              </div>
            </div>

            {/* Analysis Grid */}
            <div className="grid grid-cols-1 md:grid-cols-2 gap-8">
               {/* Positive Factors */}
              <div className="glass-card p-8">
                <h3 className="text-xl font-display font-bold mb-6 text-green-400 flex items-center gap-3">
                   <ShieldCheck size={20} />
                   Verified Assets
                </h3>
                <div className="space-y-4">
                  {result.reasons.length > 0 ? result.reasons.map((reason, idx) => (
                    <div key={idx} className="flex gap-4 p-4 rounded-xl bg-green-500/5 border border-green-500/10">
                      <div className="w-1.5 h-1.5 rounded-full bg-green-500 mt-2 flex-shrink-0" />
                      <span className="text-green-100/70 text-sm leading-relaxed">{reason}</span>
                    </div>
                  )) : (
                    <p className="text-white/20 italic">No positive factors identified.</p>
                  )}
                </div>
              </div>

              {/* Warnings */}
              <div className="glass-card p-8 border-accent-gold/20">
                <h3 className="text-xl font-display font-bold mb-6 text-accent-gold flex items-center gap-3">
                   <AlertTriangle size={20} />
                   Risk Factors
                </h3>
                <div className="space-y-4">
                  {result.warnings.length > 0 ? result.warnings.map((warning, idx) => (
                    <div key={idx} className="p-4 rounded-xl bg-accent-gold/5 border border-accent-gold/10 text-accent-gold text-sm flex gap-3">
                       <Info size={18} className="flex-shrink-0" />
                       {warning}
                    </div>
                  )) : (
                    <div className="flex flex-col items-center justify-center py-8 text-white/20">
                       <ShieldCheck size={40} className="mb-2 opacity-10" />
                       <p>Low-risk configuration</p>
                    </div>
                  )}
                </div>
              </div>
            </div>

            {/* Final Assessment */}
            <div className="glass-card p-8 relative overflow-hidden group">
               <div className="absolute -right-4 -top-4 w-32 h-32 bg-accent-purple/10 blur-3xl rounded-full" />
               <h3 className="text-xl font-display font-bold mb-6 text-accent-purple flex items-center gap-3">
                  <Activity size={20} />
                  Professional Risk/Reward Assessment
               </h3>
               <div className="relative z-10 text-white/80 whitespace-pre-wrap leading-relaxed text-lg font-medium">
                  {result.ai_reasoning}
               </div>
               
               <div className="mt-10 grid grid-cols-1 md:grid-cols-3 gap-4">
                  <div className="p-4 bg-white/5 rounded-2xl border border-white/5 text-center">
                     <p className="text-[10px] font-black text-white/30 uppercase tracking-widest mb-1">Potential Alpha</p>
                     <p className="text-xl font-display font-bold text-green-400">High</p>
                  </div>
                  <div className="p-4 bg-white/5 rounded-2xl border border-white/5 text-center">
                     <p className="text-[10px] font-black text-white/30 uppercase tracking-widest mb-1">Market Liquidity</p>
                     <p className="text-xl font-display font-bold text-accent-cyan">Optimal</p>
                  </div>
                  <div className="p-4 bg-white/5 rounded-2xl border border-white/5 text-center">
                     <p className="text-[10px] font-black text-white/30 uppercase tracking-widest mb-1">Execution Priority</p>
                     <p className="text-xl font-display font-bold text-accent-gold">High</p>
                  </div>
               </div>
            </div>
          </div>
        )}

        {!result && !loading && !error && (
          <div className="glass-card p-20 flex flex-col items-center justify-center text-center">
             <div className="w-20 h-20 rounded-full bg-white/5 flex items-center justify-center mb-6 text-white/20">
                <Target size={40} />
             </div>
             <h3 className="text-2xl font-display font-bold text-white mb-2">Ready for Verification</h3>
             <p className="text-white/40 max-w-sm">Enter your signal details on the left to begin the institutional-grade verification process.</p>
          </div>
        )}
      </div>
    </div>
  )
}
