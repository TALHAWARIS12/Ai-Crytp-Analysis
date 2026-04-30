'use client'

import React, { useEffect, useState } from 'react'
import { useUIStore } from '@/lib/store'
import { Trash2, Plus, Search, Star, TrendingUp, TrendingDown, Activity, AlertCircle } from 'lucide-react'
import { marketAPI } from '@/lib/api'

export default function Watchlist() {
  const { watchlist, addToWatchlist, removeFromWatchlist } = useUIStore()
  const [newSymbol, setNewSymbol] = useState('')
  const [loading, setLoading] = useState<Record<string, boolean>>({})
  const [errors, setErrors] = useState<Record<string, string>>({})

  useEffect(() => {
    const refresh = async () => {
      await Promise.all(
        watchlist.map(async (item) => {
          try {
            setLoading((prev) => ({ ...prev, [item.symbol]: true }))
            const ticker = await marketAPI.getPrice(item.symbol)
            addToWatchlist({
              symbol: item.symbol,
              current_price: ticker.last,
              change_percent: ticker.percentage ?? 0,
              trend: (ticker.percentage ?? 0) >= 0 ? 'BULLISH' : 'BEARISH',
            })
            setErrors((prev) => ({ ...prev, [item.symbol]: '' }))
          } catch (error: any) {
            setErrors((prev) => ({
              ...prev,
              [item.symbol]: error?.response?.data?.detail || 'live data unavailable',
            }))
          } finally {
            setLoading((prev) => ({ ...prev, [item.symbol]: false }))
          }
        })
      )
    }

    if (watchlist.length) {
      refresh()
      const interval = setInterval(refresh, 15000)
      return () => clearInterval(interval)
    }
    return
  }, [watchlist.length])

  const handleAddToWatchlist = (e: React.FormEvent) => {
    e.preventDefault()
    if (newSymbol.trim()) {
      addToWatchlist({
        symbol: newSymbol.toUpperCase(),
        current_price: 0,
        change_percent: 0,
        trend: 'NEUTRAL',
      })
      setNewSymbol('')
    }
  }

  return (
    <div className="space-y-10 fade-in">
      {/* Add to Watchlist Header */}
      <div className="flex flex-col md:flex-row items-center justify-between gap-8">
         <div>
            <h2 className="text-3xl font-display font-bold mb-2 flex items-center gap-3">
               <Star className="text-accent-gold" size={28} />
               Institutional <span className="text-gradient-gold">Watchlist</span>
            </h2>
            <p className="text-white/40">Track high-conviction assets in real-time.</p>
         </div>

         <form onSubmit={handleAddToWatchlist} className="relative w-full md:w-96 group">
            <div className="absolute inset-y-0 left-4 flex items-center pointer-events-none text-white/30 group-focus-within:text-accent-purple transition-colors">
               <Search size={18} />
            </div>
            <input
               type="text"
               value={newSymbol}
               onChange={(e) => setNewSymbol(e.target.value)}
               placeholder="Add symbol (e.g., BTC, ETH)"
               className="w-full bg-white/5 border border-white/10 rounded-2xl pl-12 pr-24 py-4 text-white placeholder-white/20 focus:outline-none focus:border-accent-purple/50 transition-all"
            />
            <button
               type="submit"
               className="absolute right-2 top-2 bottom-2 px-4 bg-white/5 hover:bg-white/10 text-white rounded-xl font-bold text-xs uppercase tracking-widest transition-all border border-white/5 active:scale-95 flex items-center gap-2"
            >
               <Plus size={14} />
               <span>Add</span>
            </button>
         </form>
      </div>

      {/* Watchlist Grid */}
      {watchlist.length === 0 ? (
        <div className="glass-card p-24 text-center border-dashed border-2">
          <div className="w-20 h-20 rounded-full bg-white/5 flex items-center justify-center mx-auto mb-6 text-white/10">
             <Star size={40} />
          </div>
          <h3 className="text-xl font-bold mb-2">No active assets</h3>
          <p className="text-white/40 max-w-xs mx-auto">Start building your portfolio watchlist to monitor real-time AI sentiment.</p>
        </div>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-6">
          {watchlist.map((item) => (
            <div key={item.symbol} className="glass-card p-6 group hover:border-accent-purple/30 transition-all">
              <div className="flex justify-between items-start mb-8">
                <div className="flex items-center gap-3">
                   <div className={`w-10 h-10 rounded-xl flex items-center justify-center ${item.trend === 'BULLISH' ? 'bg-green-500/10 text-green-400' : 'bg-red-500/10 text-red-400'}`}>
                      {item.trend === 'BULLISH' ? <TrendingUp size={20} /> : <TrendingDown size={20} />}
                   </div>
                   <div>
                      <h3 className="text-xl font-display font-black text-white">{item.symbol}</h3>
                      <p className="text-[10px] uppercase font-bold text-white/30 tracking-widest">{item.trend}</p>
                   </div>
                </div>
                <button
                  onClick={() => removeFromWatchlist(item.symbol)}
                  className="p-2 opacity-0 group-hover:opacity-100 bg-red-500/10 hover:bg-red-500/20 text-red-400 rounded-lg transition-all"
                >
                  <Trash2 size={16} />
                </button>
              </div>

              <div className="p-4 bg-white/5 rounded-2xl border border-white/5">
                <p className="text-[10px] uppercase font-bold text-white/30 tracking-widest mb-1">Live Valuation</p>
                {loading[item.symbol] ? (
                  <div className="flex items-center gap-2">
                     <div className="h-6 w-24 bg-white/5 animate-pulse rounded" />
                  </div>
                ) : errors[item.symbol] ? (
                  <div className="flex items-center gap-2 text-red-400 text-xs">
                     <AlertCircle size={14} />
                     <span>Data Unavailable</span>
                  </div>
                ) : (
                  <div className="flex items-end justify-between">
                    <p className="text-2xl font-display font-black text-white">
                      ${item.current_price.toLocaleString()}
                    </p>
                    <p className={`font-bold text-sm ${item.change_percent >= 0 ? 'text-green-400' : 'text-red-400'}`}>
                      {item.change_percent >= 0 ? '+' : ''}
                      {item.change_percent.toFixed(2)}%
                    </p>
                  </div>
                )}
              </div>
              
              <div className="mt-6 flex items-center justify-between px-2">
                 <div className="flex gap-1">
                    {[1,2,3,4,5].map(i => (
                       <div key={i} className={`w-1 h-3 rounded-full ${i <= 3 ? 'bg-accent-purple/40' : 'bg-white/5'}`} />
                    ))}
                 </div>
                 <div className="text-[10px] font-black text-accent-cyan flex items-center gap-1">
                    <Activity size={10} />
                    <span>HIGH ALPHA</span>
                 </div>
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  )
}
