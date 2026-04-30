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
        """Detect Market Structure (BOS, HHL)"""
        if len(close) < 20:
            return {"structure": "NEUTRAL", "bos": False}
        
        recent_high = max(high[-10:])
        prev_high = max(high[-20:-10])
        recent_low = min(low[-10:])
        prev_low = min(low[-20:-10])
        
        bos_bullish = close[-1] > prev_high
        bos_bearish = close[-1] < prev_low
        
        structure = "BULLISH" if (recent_high > prev_high and recent_low > prev_low) else \
                    "BEARISH" if (recent_high < prev_high and recent_low < prev_low) else "SIDEWAYS"
        
        return {
            "structure": structure,
            "bos": bos_bullish or bos_bearish,
            "bos_direction": "UP" if bos_bullish else "DOWN" if bos_bearish else None
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
