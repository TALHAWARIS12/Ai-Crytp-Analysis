import numpy as np
import pandas as pd
from typing import List, Tuple, Dict

class TechnicalIndicators:
    """Production-grade technical indicator calculations"""

    @staticmethod
    def _clean(values: List[float]) -> List[float]:
        cleaned = []
        for value in values:
            if pd.isna(value):
                cleaned.append(None)
            else:
                cleaned.append(float(value))
        return cleaned
    
    @staticmethod
    def ema(data: List[float], period: int) -> List[float]:
        """Calculate Exponential Moving Average"""
        s = pd.Series(data)
        return TechnicalIndicators._clean(s.ewm(span=period, adjust=False).mean().tolist())
    
    @staticmethod
    def sma(data: List[float], period: int) -> List[float]:
        """Calculate Simple Moving Average"""
        s = pd.Series(data)
        return TechnicalIndicators._clean(s.rolling(window=period).mean().tolist())
    
    @staticmethod
    def rsi(data: List[float], period: int = 14) -> List[float]:
        """Calculate Relative Strength Index"""
        s = pd.Series(data)
        delta = s.diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=period).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()
        rs = gain / loss
        rsi = 100 - (100 / (1 + rs))
        return TechnicalIndicators._clean(rsi.tolist())
    
    @staticmethod
    def macd(data: List[float], fast: int = 12, slow: int = 26, signal: int = 9) -> Dict:
        """Calculate MACD (Moving Average Convergence Divergence)"""
        s = pd.Series(data)
        ema_fast = s.ewm(span=fast, adjust=False).mean()
        ema_slow = s.ewm(span=slow, adjust=False).mean()
        macd_line = ema_fast - ema_slow
        signal_line = macd_line.ewm(span=signal, adjust=False).mean()
        histogram = macd_line - signal_line
        
        return {
            'macd': macd_line.tolist(),
            'signal': signal_line.tolist(),
            'histogram': histogram.tolist()
        }
    
    @staticmethod
    def atr(high: List[float], low: List[float], close: List[float], period: int = 14) -> List[float]:
        """Calculate Average True Range"""
        high_s = pd.Series(high)
        low_s = pd.Series(low)
        close_s = pd.Series(close)
        
        tr1 = high_s - low_s
        tr2 = (high_s - close_s.shift()).abs()
        tr3 = (low_s - close_s.shift()).abs()
        tr = pd.concat([tr1, tr2, tr3], axis=1).max(axis=1)
        atr = tr.rolling(window=period).mean()
        return TechnicalIndicators._clean(atr.tolist())
    
    @staticmethod
    def bollinger_bands(data: List[float], period: int = 20, std_dev: float = 2) -> Dict:
        """Calculate Bollinger Bands"""
        s = pd.Series(data)
        sma_val = s.rolling(window=period).mean()
        std_val = s.rolling(window=period).std()
        upper = sma_val + (std_dev * std_val)
        lower = sma_val - (std_dev * std_val)
        
        return {
            'upper': upper.tolist(),
            'middle': sma_val.tolist(),
            'lower': lower.tolist()
        }
    
    @staticmethod
    def vwap(high: List[float], low: List[float], close: List[float], volume: List[float]) -> List[float]:
        """Calculate Volume Weighted Average Price"""
        high_s = pd.Series(high)
        low_s = pd.Series(low)
        close_s = pd.Series(close)
        volume_s = pd.Series(volume)
        
        tp = (high_s + low_s + close_s) / 3
        cumul_tp_vol = (tp * volume_s).cumsum()
        cumul_vol = volume_s.cumsum()
        vwap = cumul_tp_vol / cumul_vol
        return vwap.tolist()
    
    @staticmethod
    def obv(close: List[float], volume: List[float]) -> List[float]:
        """Calculate On Balance Volume"""
        close_s = pd.Series(close)
        volume_s = pd.Series(volume)
        
        obv_val = (np.sign(close_s.diff()) * volume_s).fillna(0).cumsum()
        return obv_val.tolist()
    
    @staticmethod
    def higher_highs_lows(data: List[float], lookback: int = 5) -> Tuple[bool, bool]:
        """Detect higher highs and lower lows pattern"""
        if len(data) < lookback * 2:
            return False, False
        
        recent = data[-lookback:]
        previous = data[-lookback*2:-lookback]
        
        higher_high = max(recent) > max(previous)
        lower_low = min(recent) < min(previous)
        
        return higher_high, lower_low
    
    @staticmethod
    def trend_score(ema8: List[float], ema34: List[float], sma50: List[float], 
                    sma200: List[float], close: List[float]) -> Dict:
        """Calculate comprehensive trend score"""
        current_price = close[-1]

        ema_alignment = 1.0 if ema8[-1] > ema34[-1] else -1.0

        sma50_val = sma50[-1] if sma50 else None
        sma200_val = sma200[-1] if sma200 else None
        price_vs_50 = 0.0 if sma50_val is None else (1.0 if current_price > sma50_val else -1.0)
        price_vs_200 = 0.0 if sma200_val is None else (1.0 if current_price > sma200_val else -1.0)
        ema_vs_50 = 0.0 if sma50_val is None else (1.0 if ema8[-1] > sma50_val else -1.0)
        
        bullish_score = (ema_alignment + price_vs_50 + price_vs_200 + ema_vs_50) / 4
        
        return {
            'bullish_score': bullish_score,
            'ema_alignment': ema_alignment,
            'price_vs_50': price_vs_50,
            'price_vs_200': price_vs_200,
            'ema_vs_50': ema_vs_50,
            'direction': 'BULLISH' if bullish_score > 0.5 else ('BEARISH' if bullish_score < -0.5 else 'NEUTRAL')
        }
    
    @staticmethod
    def detect_structure(high: List[float], low: List[float], close: List[float]) -> Dict:
        """Detect Market Structure (BOS, CHoCH)"""
        if len(close) < 30:
            return {"structure": "NEUTRAL", "bos": False, "choch": False}
        
        # Recent Swing Highs/Lows
        recent_high = max(high[-10:])
        prev_high = max(high[-25:-10])
        recent_low = min(low[-10:])
        prev_low = min(low[-25:-10])
        
        # BOS: Break in trend direction
        bos_bullish = close[-1] > prev_high
        bos_bearish = close[-1] < prev_low
        
        # CHoCH: Change of Character (First counter-trend break)
        choch_bullish = close[-1] > prev_high and close[-2] <= prev_high # Simplified
        choch_bearish = close[-1] < prev_low and close[-2] >= prev_low # Simplified
        
        structure = "BULLISH" if (recent_high > prev_high and recent_low > prev_low) else \
                    "BEARISH" if (recent_high < prev_high and recent_low < prev_low) else "SIDEWAYS"
        
        return {
            "structure": structure,
            "bos": bos_bullish or bos_bearish,
            "bos_direction": "UP" if bos_bullish else "DOWN" if bos_bearish else None,
            "choch": choch_bullish or choch_bearish,
            "choch_type": "BULLISH" if choch_bullish else "BEARISH" if choch_bearish else None
        }

    @staticmethod
    def calculate_tp_levels(entry: float, sl: float, direction: str) -> List[float]:
        """Calculate 3-tier TP levels based on Risk/Reward"""
        risk = abs(entry - sl)
        if direction.upper() == "LONG":
            return [round(entry + (risk * 1.5), 6), round(entry + (risk * 2.5), 6), round(entry + (risk * 4.0), 6)]
        else:
            return [round(entry - (risk * 1.5), 6), round(entry - (risk * 2.5), 6), round(entry - (risk * 4.0), 6)]

    @staticmethod
    def support_resistance(high: List[float], low: List[float], lookback: int = 20) -> Dict:
        """Identify support and resistance levels"""
        recent_high = max(high[-lookback:])
        recent_low = min(low[-lookback:])
        
        resistance_levels = sorted(
            [h for h in high[-lookback:] if h > (recent_high - (recent_high * 0.02))],
            reverse=True
        )[:3]
        
        support_levels = sorted(
            [l for l in low[-lookback:] if l < (recent_low + (recent_low * 0.02))]
        )[:3]
        
        return {
            'resistance': list(set(resistance_levels)),
            'support': list(set(support_levels)),
            'primary_resistance': recent_high,
            'primary_support': recent_low
        }

    @staticmethod
    def support_resistance_advanced(high: List[float], low: List[float], close: List[float], lookback: int = 50) -> Dict:
        """Advanced cluster-based support/resistance"""
        recent_high = max(high[-lookback:])
        recent_low = min(low[-lookback:])
        
        # Simple clustering
        def get_clusters(data, threshold=0.01):
            sorted_data = sorted(data)
            clusters = []
            if not sorted_data: return clusters
            curr_cluster = [sorted_data[0]]
            for val in sorted_data[1:]:
                if (val - curr_cluster[-1]) / curr_cluster[-1] <= threshold:
                    curr_cluster.append(val)
                else:
                    clusters.append({'level': sum(curr_cluster)/len(curr_cluster), 'strength': len(curr_cluster)})
                    curr_cluster = [val]
            clusters.append({'level': sum(curr_cluster)/len(curr_cluster), 'strength': len(curr_cluster)})
            return clusters

        res_clusters = get_clusters([h for h in high[-lookback:] if h >= close[-1]])
        sup_clusters = get_clusters([l for l in low[-lookback:] if l <= close[-1]])
        
        res_clusters = sorted(res_clusters, key=lambda x: x['strength'], reverse=True)
        sup_clusters = sorted(sup_clusters, key=lambda x: x['strength'], reverse=True)
        
        return {
            'strong_resistance': [c['level'] for c in res_clusters[:2]],
            'weak_resistance': [c['level'] for c in res_clusters[2:4]],
            'strong_support': [c['level'] for c in sup_clusters[:2]],
            'weak_support': [c['level'] for c in sup_clusters[2:4]],
            'primary_resistance': recent_high,
            'primary_support': recent_low
        }

    @staticmethod
    def detect_liquidity_zones(high: List[float], low: List[float], lookback: int = 50) -> Dict:
        """Detect liquidity pools, equal highs/lows"""
        if len(high) < lookback:
            return {"buy_side": [], "sell_side": []}
            
        recent_highs = high[-lookback:]
        recent_lows = low[-lookback:]
        
        # Equal highs (Buy-side liquidity)
        max_high = max(recent_highs)
        eqh = [h for h in recent_highs if max_high * 0.998 <= h <= max_high * 1.002]
        
        # Equal lows (Sell-side liquidity)
        min_low = min(recent_lows)
        eql = [l for l in recent_lows if min_low * 0.998 <= l <= min_low * 1.002]
        
        buy_side = []
        if len(eqh) >= 2:
            buy_side.append(f"Above {max_high:.2f} (Equal Highs)")
        else:
            buy_side.append(f"Above {max_high:.2f} (Swing High)")
            
        sell_side = []
        if len(eql) >= 2:
            sell_side.append(f"Below {min_low:.2f} (Equal Lows)")
        else:
            sell_side.append(f"Below {min_low:.2f} (Swing Low)")
            
        return {
            "buy_side": buy_side,
            "sell_side": sell_side
        }

    @staticmethod
    def volume_analysis(volume: List[float], close: List[float]) -> Dict:
        """Analyze volume profile"""
        if len(volume) < 20:
            return {"status": "Normal", "multiplier": 1.0, "buyers_active": False}
            
        recent_vol = volume[-1]
        avg_vol = sum(volume[-20:-1]) / 19 if sum(volume[-20:-1]) > 0 else 1
        multiplier = recent_vol / avg_vol
        
        close_change = close[-1] - close[-2]
        buyers_active = close_change > 0 and multiplier > 1.2
        sellers_active = close_change < 0 and multiplier > 1.2
        
        if multiplier > 2.0:
            status = "Volume Spike"
        elif multiplier > 1.2:
            status = "Above Average"
        elif multiplier < 0.8:
            status = "Below Average"
        else:
            status = "Average"
            
        return {
            "status": status,
            "multiplier": multiplier,
            "buyers_active": buyers_active,
            "sellers_active": sellers_active,
            "message": f"{status} ({'buyers active' if buyers_active else 'sellers active' if sellers_active else 'neutral'})"
        }

    @staticmethod
    def analyze_order_book(orderbook: Dict) -> Dict:
        """Analyze Binance order book for order flow"""
        if not orderbook or not orderbook.get('bids') or not orderbook.get('asks'):
            return {"strong_bids": [], "heavy_asks": []}
            
        bids = orderbook['bids']
        asks = orderbook['asks']
        
        # Calculate total depth volume
        total_bid_vol = sum(bid[1] for bid in bids)
        total_ask_vol = sum(ask[1] for ask in asks)
        
        strong_bids = []
        for price, vol in bids[:15]:
            if vol > (total_bid_vol / len(bids)) * 2: # 2x average size
                strong_bids.append(price)
                
        heavy_asks = []
        for price, vol in asks[:15]:
            if vol > (total_ask_vol / len(asks)) * 2: # 2x average size
                heavy_asks.append(price)
                
        return {
            "strong_bids": strong_bids,
            "heavy_asks": heavy_asks,
            "imbalance": "BUY" if total_bid_vol > total_ask_vol * 1.2 else "SELL" if total_ask_vol > total_bid_vol * 1.2 else "NEUTRAL"
        }
