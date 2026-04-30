'use client'

import React, { useEffect, useState } from 'react'
import { Search, TrendingUp, BarChart3, CheckCircle, Home as HomeIcon, Activity, RefreshCw, Sparkles, Zap, Shield, ArrowRight, ChevronRight, ChevronLeft } from 'lucide-react'
import CoinAnalysisPanel from '@/components/CoinAnalysisPanel'
import StrategyValidator from '@/components/StrategyValidator'
import SignalChecker from '@/components/SignalChecker'
import Watchlist from '@/components/Watchlist'
import Header from '@/components/Header'
import { marketAPI } from '@/lib/api'

type TabType = 'dashboard' | 'analyze' | 'strategy' | 'signal' | 'watchlist'

type SnapshotCard = {
  symbol: string
  last?: number
  percentage?: number
  funding?: string
  trend?: string
  loading: boolean
  error?: string
}

export default function Home() {
  const [activeTab, setActiveTab] = useState<TabType>('dashboard')
  const [selectedSymbol, setSelectedSymbol] = useState<string>('BTC/USDT')
  const [snapshots, setSnapshots] = useState<Record<string, SnapshotCard>>({
    'BTC/USDT': { symbol: 'BTC/USDT', loading: true },
    'ETH/USDT': { symbol: 'ETH/USDT', loading: true },
    'SOL/USDT': { symbol: 'SOL/USDT', loading: true },
  })

  const refreshSnapshots = async () => {
    const symbols = Object.keys(snapshots)
    setSnapshots((prev) =>
      Object.fromEntries(symbols.map((s) => [s, { ...prev[s], loading: true, error: undefined }]))
    )

    await Promise.all(
      symbols.map(async (symbol) => {
        try {
          const [ticker, analysis] = await Promise.all([
            marketAPI.getPrice(symbol),
            marketAPI.analyzeCoin(symbol),
          ])
          setSnapshots((prev) => ({
            ...prev,
            [symbol]: {
              ...prev[symbol],
              last: ticker.last,
              percentage: ticker.percentage,
              trend: analysis.trend,
              funding: analysis.funding_rate?.status ?? 'n/a',
              loading: false,
            },
          }))
        } catch (error: any) {
          setSnapshots((prev) => ({
            ...prev,
            [symbol]: {
              ...prev[symbol],
              loading: false,
              error: error?.response?.data?.detail || error?.message || 'unavailable',
            },
          }))
        }
      })
    )
  }

  useEffect(() => {
    refreshSnapshots()
    const interval = setInterval(refreshSnapshots, 15000)
    return () => clearInterval(interval)
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [])

  return (
    <div className="flex-1 flex flex-col">
      <Header />

      <main className="flex-1">
        {/* Hero Section */}
        <section className="relative pt-20 pb-32 overflow-hidden">
          <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 text-center relative z-10">
            <div className="inline-flex items-center gap-2 px-4 py-2 rounded-full bg-white/5 border border-white/10 text-accent-gold font-bold text-xs uppercase tracking-widest mb-8 fade-in stagger-1">
              <Sparkles size={14} className="animate-pulse" />
              <span>Next-Gen Market Intelligence</span>
            </div>
            
            <h1 className="heading-hero mb-8 fade-in stagger-2">
              Revolutionize Your <br />
              <span className="text-gradient-gold">Crypto Trading!</span>
            </h1>
            
            <p className="max-w-2xl mx-auto text-xl text-white/60 mb-12 fade-in stagger-3">
              Harness institutional-grade AI analysis to validate strategies and spot signals before they hit the mainstream.
            </p>
            
            <div className="flex flex-col sm:flex-row items-center justify-center gap-4 fade-in stagger-4">
              <button 
                onClick={() => setActiveTab('analyze')}
                className="btn-gold group flex items-center gap-3"
              >
                <span>Start Analyzing</span>
                <ArrowRight size={18} className="group-hover:translate-x-1 transition-transform" />
              </button>
              <button className="btn-outline">
                View Documentation
              </button>
            </div>

            {/* Dashboard Mockup Decoration */}
            <div className="mt-24 relative max-w-5xl mx-auto fade-in stagger-4">
              <div className="absolute -inset-1 bg-gradient-to-r from-accent-purple/20 via-accent-gold/20 to-accent-purple/20 rounded-[2.5rem] blur-2xl" />
              <div className="relative glass-card p-4 md:p-8 overflow-hidden">
                 <div className="flex items-center gap-4 mb-8">
                    <div className="flex gap-1.5">
                       <div className="w-3 h-3 rounded-full bg-red-500/50" />
                       <div className="w-3 h-3 rounded-full bg-yellow-500/50" />
                       <div className="w-3 h-3 rounded-full bg-green-500/50" />
                    </div>
                    <div className="h-6 w-32 bg-white/5 rounded-lg" />
                 </div>
                 <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
                    <div className="h-32 bg-white/5 rounded-2xl animate-pulse" />
                    <div className="h-32 bg-white/5 rounded-2xl animate-pulse stagger-1" />
                    <div className="h-32 bg-white/5 rounded-2xl animate-pulse stagger-2" />
                 </div>
                 <div className="mt-8 h-64 bg-white/5 rounded-2xl animate-pulse stagger-3" />
              </div>
            </div>
          </div>
        </section>

        {/* Dashboard Tools Section */}
        <section className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-20">
          {/* Navigation Tabs */}
          <div className="inline-flex flex-wrap p-1.5 bg-white/5 border border-white/10 rounded-2xl mb-12">
            {[
              { id: 'dashboard', icon: <HomeIcon size={18} />, label: 'Dashboard' },
              { id: 'analyze', icon: <BarChart3 size={18} />, label: 'Analyze' },
              { id: 'strategy', icon: <TrendingUp size={18} />, label: 'Strategy' },
              { id: 'signal', icon: <CheckCircle size={18} />, label: 'Signal' },
              { id: 'watchlist', icon: <Search size={18} />, label: 'Watchlist' },
            ].map((tab) => (
              <button
                key={tab.id}
                onClick={() => setActiveTab(tab.id as TabType)}
                className={`flex items-center gap-2 px-6 py-3 rounded-xl font-bold transition-all duration-300 ${
                  activeTab === tab.id
                    ? 'bg-gradient-to-r from-accent-purple to-accent-purple-pink text-white shadow-xl'
                    : 'text-white/40 hover:text-white/70 hover:bg-white/5'
                }`}
              >
                {tab.icon}
                <span>{tab.label}</span>
              </button>
            ))}
          </div>

          {/* Tab Content */}
          <div className="fade-in">
            {activeTab === 'dashboard' && (
              <div className="space-y-12">
                <div className="flex items-center justify-between">
                  <h2 className="text-3xl font-display font-bold">Live Market <span className="text-gradient-gold">Overview</span></h2>
                  <button
                    onClick={refreshSnapshots}
                    className="flex items-center gap-2 px-5 py-2.5 rounded-xl border border-white/10 bg-white/5 text-sm font-bold hover:bg-white/10 transition-colors"
                  >
                    <RefreshCw size={16} className={Object.values(snapshots).some(s => s.loading) ? 'animate-spin' : ''} />
                    Refresh Data
                  </button>
                </div>

                <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
                  {Object.values(snapshots).map((card) => (
                    <button
                      key={card.symbol}
                      onClick={() => {
                        setSelectedSymbol(card.symbol)
                        setActiveTab('analyze')
                      }}
                      className="glass-card group p-6 text-left"
                    >
                      <div className="mb-6 flex items-center justify-between">
                        <span className="px-3 py-1 rounded-lg bg-white/5 text-xs font-bold text-white/60 tracking-wider">{card.symbol}</span>
                        <div className="w-8 h-8 rounded-full bg-accent-cyan/10 flex items-center justify-center text-accent-cyan">
                           <Activity size={16} />
                        </div>
                      </div>
                      
                      {card.loading ? (
                        <div className="space-y-3">
                           <div className="h-8 w-3/4 bg-white/5 animate-pulse rounded-lg" />
                           <div className="h-4 w-1/2 bg-white/5 animate-pulse rounded-lg" />
                        </div>
                      ) : card.error ? (
                        <p className="text-sm text-red-400">Live data unavailable</p>
                      ) : (
                        <div className="space-y-1">
                          <p className="text-3xl font-display font-bold text-white">${card.last?.toLocaleString()}</p>
                          <div className="flex items-center justify-between">
                             <p className={`${(card.percentage ?? 0) >= 0 ? 'text-green-400' : 'text-red-400'} font-bold`}>
                               {(card.percentage ?? 0) >= 0 ? '+' : ''}{(card.percentage ?? 0).toFixed(2)}%
                             </p>
                             <div className="text-[10px] uppercase font-bold text-white/30">Trend: {card.trend}</div>
                          </div>
                        </div>
                      )}
                    </button>
                  ))}
                </div>

                <div className="grid grid-cols-1 md:grid-cols-2 gap-8">
                  <div className="glass-card p-8 border-l-4 border-l-accent-purple">
                    <h3 className="text-xl font-display font-bold mb-6 flex items-center gap-3">
                       <BarChart3 className="text-accent-purple" size={20} />
                       Quick Analysis: {selectedSymbol}
                    </h3>
                    <CoinAnalysisPanel symbol={selectedSymbol} />
                  </div>
                  
                  <div className="glass-card p-8 border-l-4 border-l-accent-gold">
                    <h3 className="text-xl font-display font-bold mb-6 flex items-center gap-3">
                       <Shield className="text-accent-gold" size={20} />
                       Operational Health
                    </h3>
                    <div className="space-y-4">
                      {[
                        { label: 'Data Source', value: 'Binance Futures (Real-time)', color: 'text-white' },
                        { label: 'Fallback Policy', value: 'Active Monitoring', color: 'text-accent-gold' },
                        { label: 'Manual Execution', value: 'Enabled (Safe)', color: 'text-green-400' },
                        { label: 'AI Model', value: 'Kalki Core v4.2', color: 'text-accent-purple' },
                      ].map((item, i) => (
                        <div key={i} className="flex justify-between items-center py-3 border-b border-white/5 last:border-0">
                          <span className="text-white/40 text-sm font-medium">{item.label}</span>
                          <span className={`text-sm font-bold ${item.color}`}>{item.value}</span>
                        </div>
                      ))}
                    </div>
                  </div>
                </div>
              </div>
            )}

            {activeTab === 'analyze' && <CoinAnalysisPanel symbol={selectedSymbol} />}

            {activeTab === 'strategy' && <StrategyValidator symbol={selectedSymbol} />}

            {activeTab === 'signal' && <SignalChecker />}

            {activeTab === 'watchlist' && <Watchlist />}
          </div>
        </section>

        {/* Strategy Selection Section */}
        <section className="py-24 relative">
          <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
            <div className="flex items-end justify-between mb-16">
              <div>
                <h2 className="text-4xl font-display font-bold mb-4">Select Your <span className="text-gradient-purple">Strategy</span></h2>
                <p className="text-white/40">Choose a risk profile that matches your trading style.</p>
              </div>
              <div className="flex gap-4">
                <button className="w-12 h-12 rounded-full border border-white/10 flex items-center justify-center hover:bg-white/5 transition-colors">
                  <ChevronLeft />
                </button>
                <button className="w-12 h-12 rounded-full border border-white/10 flex items-center justify-center hover:bg-white/5 transition-colors">
                  <ChevronRight />
                </button>
              </div>
            </div>

            <div className="grid grid-cols-1 md:grid-cols-3 gap-8">
              {/* Conservative Card */}
              <div className="glass-card group p-8 hover:shadow-[0_0_40px_rgba(0,212,255,0.1)] hover:border-accent-cyan/30">
                <div className="w-16 h-16 rounded-2xl bg-accent-cyan/10 flex items-center justify-center mb-8">
                   <Shield className="text-accent-cyan" size={32} />
                </div>
                <h3 className="text-2xl font-display font-bold mb-4">Conservative</h3>
                <p className="text-white/50 mb-8 leading-relaxed">
                  Focus on high-cap assets with low volatility. Perfect for long-term wealth preservation.
                </p>
                <div className="h-1 bg-white/5 rounded-full overflow-hidden mb-8">
                   <div className="h-full bg-accent-cyan w-1/3 animate-shimmer bg-[length:200%_100%]" />
                </div>
                <button className="w-full py-4 rounded-xl border border-white/10 font-bold group-hover:bg-gradient-to-r from-accent-cyan/20 to-accent-cyan/40 group-hover:border-accent-cyan/50 transition-all">
                  Get Started
                </button>
              </div>

              {/* Balanced Card */}
              <div className="glass-card group p-8 hover:shadow-[0_0_40px_rgba(245,197,24,0.1)] hover:border-accent-gold/30">
                <div className="w-16 h-16 rounded-2xl bg-accent-gold/10 flex items-center justify-center mb-8">
                   <Zap className="text-accent-gold" size={32} />
                </div>
                <h3 className="text-2xl font-display font-bold mb-4">Balanced</h3>
                <p className="text-white/50 mb-8 leading-relaxed">
                  A mix of mid and high-cap assets with moderate exposure to growth signals.
                </p>
                <div className="h-1 bg-white/5 rounded-full overflow-hidden mb-8">
                   <div className="h-full bg-accent-gold w-2/3 animate-shimmer bg-[length:200%_100%]" />
                </div>
                <button className="w-full py-4 rounded-xl border border-white/10 font-bold group-hover:bg-gradient-to-r from-accent-gold/20 to-accent-gold/40 group-hover:border-accent-gold/50 transition-all">
                  Get Started
                </button>
              </div>

              {/* Dynamic Card */}
              <div className="glass-card group p-8 hover:shadow-[0_0_40px_rgba(123,47,255,0.1)] hover:border-accent-purple/30">
                <div className="w-16 h-16 rounded-2xl bg-accent-purple/10 flex items-center justify-center mb-8">
                   <Activity className="text-accent-purple" size={32} />
                </div>
                <h3 className="text-2xl font-display font-bold mb-4">Dynamic</h3>
                <p className="text-white/50 mb-8 leading-relaxed">
                  High-risk, high-reward strategy targeting low-cap gems and momentum swings.
                </p>
                <div className="h-1 bg-white/5 rounded-full overflow-hidden mb-8">
                   <div className="h-full bg-accent-purple w-full animate-shimmer bg-[length:200%_100%]" />
                </div>
                <button className="w-full py-4 rounded-xl border border-white/10 font-bold group-hover:bg-gradient-to-r from-accent-purple/20 to-accent-purple/40 group-hover:border-accent-purple/50 transition-all">
                  Get Started
                </button>
              </div>
            </div>
          </div>
        </section>
      </main>

      <footer className="py-12 border-t border-white/5">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 flex flex-col md:row items-center justify-between gap-8">
           <div className="flex items-center gap-2">
              <div className="w-8 h-8 bg-white/5 rounded-lg flex items-center justify-center">
                 <TrendingUp size={16} className="text-accent-purple" />
              </div>
              <span className="font-display font-bold text-white/60">Kalki AI v1.0.4</span>
           </div>
           <div className="flex gap-8 text-sm font-medium text-white/30">
              <a href="#" className="hover:text-white transition-colors">Privacy</a>
              <a href="#" className="hover:text-white transition-colors">Terms</a>
              <a href="#" className="hover:text-white transition-colors">Security</a>
              <a href="#" className="hover:text-white transition-colors">Support</a>
           </div>
           <div className="text-white/20 text-xs">
              © 2026 Kalki Intelligence Systems. All rights reserved.
           </div>
        </div>
      </footer>
    </div>
  )
}
