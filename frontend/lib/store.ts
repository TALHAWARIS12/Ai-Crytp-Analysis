import { create } from 'zustand'
import { WatchlistItem } from '@/types/market'

interface UIStore {
  // Watchlist
  watchlist: WatchlistItem[]
  addToWatchlist: (item: WatchlistItem) => void
  removeFromWatchlist: (symbol: string) => void
  
  // Analysis History
  recentAnalyses: Array<{ symbol: string; timestamp: string }>
  addAnalysis: (symbol: string) => void
  
  // UI State
  isLoading: boolean
  setLoading: (loading: boolean) => void
  
  error: string | null
  setError: (error: string | null) => void
  
  // Theme
  isDark: boolean
  setDark: (dark: boolean) => void
}

export const useUIStore = create<UIStore>((set) => ({
  watchlist: [],
  addToWatchlist: (item) =>
    set((state) => ({
      watchlist: [item, ...state.watchlist.filter((w) => w.symbol !== item.symbol)],
    })),
  removeFromWatchlist: (symbol) =>
    set((state) => ({
      watchlist: state.watchlist.filter((w) => w.symbol !== symbol),
    })),
  
  recentAnalyses: [],
  addAnalysis: (symbol) =>
    set((state) => ({
      recentAnalyses: [
        { symbol, timestamp: new Date().toISOString() },
        ...state.recentAnalyses.slice(0, 9),
      ],
    })),
  
  isLoading: false,
  setLoading: (loading) => set({ isLoading: loading }),
  
  error: null,
  setError: (error) => set({ error }),
  
  isDark: true,
  setDark: (dark) => set({ isDark: dark }),
}))
