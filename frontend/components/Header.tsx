'use client'

import React from 'react'
import { TrendingUp, Settings, User, Sparkles } from 'lucide-react'

export default function Header() {
  return (
    <header className="glass-nav sticky top-0 z-50">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-4 flex justify-between items-center">
        {/* Logo */}
        <div className="flex items-center gap-3 group">
          <div className="relative w-12 h-12 bg-gradient-to-br from-accent-purple to-accent-purple-pink rounded-2xl flex items-center justify-center transition-all duration-500 group-hover:rotate-12 group-hover:scale-110">
            {/* Glow effect */}
            <div className="absolute inset-0 bg-accent-purple blur-xl opacity-40 group-hover:opacity-80 transition-opacity" />
            <TrendingUp size={24} className="text-white relative z-10" />
          </div>
          <div>
            <h1 className="text-xl font-display font-bold text-white tracking-tight leading-none mb-1 flex items-center gap-2">
              Kalki <span className="text-gradient-gold">AI</span>
            </h1>
            <p className="text-[10px] uppercase tracking-[0.2em] text-white/40 font-bold">
              Institutional Intelligence
            </p>
          </div>
        </div>

        {/* Right Actions */}
        <div className="flex items-center gap-6">
          <div className="hidden md:flex items-center gap-6 mr-4">
            <a href="#" className="text-sm font-medium text-white/60 hover:text-white transition-colors">Market</a>
            <a href="#" className="text-sm font-medium text-white/60 hover:text-white transition-colors">History</a>
            <a href="#" className="text-sm font-medium text-white/60 hover:text-white transition-colors">API</a>
          </div>
          
          <button className="relative group p-2.5 bg-white/5 hover:bg-white/10 border border-white/10 rounded-xl transition-all">
            <Settings size={20} className="text-white/70 group-hover:text-white group-hover:rotate-45 transition-all" />
          </button>
          
          <button className="flex items-center gap-2 pl-2 pr-4 py-2 bg-gradient-to-r from-accent-gold to-accent-orange text-space rounded-xl font-bold text-sm hover:shadow-[0_0_20px_rgba(245,197,24,0.3)] transition-all active:scale-95">
             <div className="w-6 h-6 bg-space/20 rounded-lg flex items-center justify-center">
               <User size={14} />
             </div>
             <span>0x...4F2d</span>
          </button>
        </div>
      </div>
    </header>
  )
}
