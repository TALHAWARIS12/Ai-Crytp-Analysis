'use client'

import React, { useState } from 'react'
import { useUIStore } from '@/lib/store'
import { Trash2, Plus } from 'lucide-react'

export default function Watchlist() {
  const { watchlist, addToWatchlist, removeFromWatchlist } = useUIStore()
  const [newSymbol, setNewSymbol] = useState('')

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
    <div className="space-y-6">
      {/* Add to Watchlist */}
      <form onSubmit={handleAddToWatchlist} className="bg-dark-800 rounded-lg p-6 border border-dark-700 flex gap-2">
        <input
          type="text"
          value={newSymbol}
          onChange={(e) => setNewSymbol(e.target.value)}
          placeholder="Add symbol to watchlist (e.g., BTC, ETH)"
          className="flex-1 bg-dark-700 border border-dark-600 rounded px-4 py-2 text-white placeholder-gray-500 focus:outline-none focus:border-crypto-blue"
        />
        <button
          type="submit"
          className="bg-crypto-blue text-white px-6 py-2 rounded-lg hover:bg-blue-600 transition font-medium flex items-center gap-2"
        >
          <Plus size={18} />
          Add
        </button>
      </form>

      {/* Watchlist Items */}
      {watchlist.length === 0 ? (
        <div className="bg-dark-800 rounded-lg p-12 border border-dark-700 text-center">
          <p className="text-gray-500">Your watchlist is empty</p>
          <p className="text-gray-600 text-sm mt-2">Add symbols above to start tracking</p>
        </div>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
          {watchlist.map((item) => (
            <div key={item.symbol} className="bg-dark-800 rounded-lg p-6 border border-dark-700 flex justify-between items-start">
              <div className="flex-1">
                <h3 className="text-lg font-semibold text-white">{item.symbol}</h3>
                <p className="text-sm text-gray-500 mt-1">Trend: {item.trend}</p>
                <div className="mt-4">
                  <p className="text-xs text-gray-500 mb-1">Price</p>
                  <p className="text-lg font-semibold text-crypto-emerald">
                    ${item.current_price.toFixed(2)}
                  </p>
                </div>
              </div>
              <button
                onClick={() => removeFromWatchlist(item.symbol)}
                className="p-2 hover:bg-dark-700 rounded transition text-gray-400 hover:text-crypto-red"
              >
                <Trash2 size={18} />
              </button>
            </div>
          ))}
        </div>
      )}
    </div>
  )
}
