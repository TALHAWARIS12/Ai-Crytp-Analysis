'use client'

import React from 'react'
import { TrendingUp, Settings, User } from 'lucide-react'

export default function Header() {
  return (
    <header className="bg-dark-900 border-b border-dark-700 sticky top-0 z-50">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-4 flex justify-between items-center">
        {/* Logo */}
        <div className="flex items-center gap-3">
          <div className="w-10 h-10 bg-gradient-to-br from-crypto-blue to-crypto-cyan rounded-lg flex items-center justify-center">
            <TrendingUp size={20} className="text-white" />
          </div>
          <div>
            <h1 className="text-lg font-bold text-white">AI Crypto Trading</h1>
            <p className="text-xs text-gray-500">Institutional Analysis</p>
          </div>
        </div>

        {/* Right Actions */}
        <div className="flex items-center gap-4">
          <button className="p-2 hover:bg-dark-800 rounded-lg transition text-gray-400 hover:text-white">
            <Settings size={20} />
          </button>
          <button className="p-2 hover:bg-dark-800 rounded-lg transition text-gray-400 hover:text-white">
            <User size={20} />
          </button>
        </div>
      </div>
    </header>
  )
}
