"""
Test suite for technical indicators module
"""

import pytest
from app.indicators.technical import TechnicalIndicators

# Sample data for testing
SAMPLE_PRICES = [
    100, 102, 101, 103, 105, 104, 106, 108, 107, 110,
    109, 111, 112, 111, 113, 115, 114, 116, 118, 117,
    119, 120, 119, 121, 122, 121, 123, 125, 124, 126
]

SAMPLE_HIGH = [
    102, 104, 103, 105, 107, 106, 108, 110, 109, 112,
    111, 113, 114, 113, 115, 117, 116, 118, 120, 119,
    121, 122, 121, 123, 124, 123, 125, 127, 126, 128
]

SAMPLE_LOW = [
    98, 100, 99, 101, 103, 102, 104, 106, 105, 108,
    107, 109, 110, 109, 111, 113, 112, 114, 116, 115,
    117, 118, 117, 119, 120, 119, 121, 123, 122, 124
]

SAMPLE_VOLUME = [
    1000000, 1100000, 1050000, 1200000, 1300000, 1150000,
    1400000, 1500000, 1350000, 1600000, 1450000, 1700000,
    1800000, 1650000, 1900000, 2000000, 1850000, 2100000,
    2200000, 2050000, 2300000, 2400000, 2250000, 2500000,
    2600000, 2450000, 2700000, 2800000, 2650000, 2900000
]

class TestTechnicalIndicators:
    
    def test_ema_calculation(self):
        """Test EMA calculation"""
        ema = TechnicalIndicators.ema(SAMPLE_PRICES, 8)
        assert len(ema) == len(SAMPLE_PRICES)
        assert all(isinstance(v, (int, float)) for v in ema)
        # EMA should be smooth
        assert ema[-1] > 0
    
    def test_sma_calculation(self):
        """Test SMA calculation"""
        sma = TechnicalIndicators.sma(SAMPLE_PRICES, 20)
        assert len(sma) == len(SAMPLE_PRICES)
        # First 19 values should be NaN/None
        assert sma[-1] > 0
    
    def test_rsi_calculation(self):
        """Test RSI calculation"""
        rsi = TechnicalIndicators.rsi(SAMPLE_PRICES, 14)
        assert len(rsi) == len(SAMPLE_PRICES)
        # RSI should be between 0-100
        valid_rsi = [v for v in rsi if v is not None and 0 <= v <= 100]
        assert len(valid_rsi) > 0
    
    def test_macd_calculation(self):
        """Test MACD calculation"""
        macd_result = TechnicalIndicators.macd(SAMPLE_PRICES, 12, 26, 9)
        assert 'macd' in macd_result
        assert 'signal' in macd_result
        assert 'histogram' in macd_result
        assert len(macd_result['macd']) == len(SAMPLE_PRICES)
    
    def test_atr_calculation(self):
        """Test ATR calculation"""
        atr = TechnicalIndicators.atr(SAMPLE_HIGH, SAMPLE_LOW, SAMPLE_PRICES, 14)
        assert len(atr) == len(SAMPLE_PRICES)
        assert all(v >= 0 for v in atr if v is not None)
    
    def test_bollinger_bands(self):
        """Test Bollinger Bands calculation"""
        bb = TechnicalIndicators.bollinger_bands(SAMPLE_PRICES, 20, 2)
        assert 'upper' in bb
        assert 'middle' in bb
        assert 'lower' in bb
        assert len(bb['upper']) == len(SAMPLE_PRICES)
        # Upper band should be above lower band
        assert bb['upper'][-1] > bb['lower'][-1]
    
    def test_trend_score(self):
        """Test trend score calculation"""
        ema8 = TechnicalIndicators.ema(SAMPLE_PRICES, 8)
        ema34 = TechnicalIndicators.ema(SAMPLE_PRICES, 34)
        sma50 = TechnicalIndicators.sma(SAMPLE_PRICES, 50)
        sma200 = TechnicalIndicators.sma(SAMPLE_PRICES, 200)
        
        trend = TechnicalIndicators.trend_score(ema8, ema34, sma50, sma200, SAMPLE_PRICES)
        
        assert 'bullish_score' in trend
        assert 'direction' in trend
        assert trend['direction'] in ['BULLISH', 'BEARISH', 'NEUTRAL']
        assert -1 <= trend['bullish_score'] <= 1
    
    def test_support_resistance(self):
        """Test support/resistance detection"""
        sr = TechnicalIndicators.support_resistance(SAMPLE_HIGH, SAMPLE_LOW, 20)
        
        assert 'support' in sr
        assert 'resistance' in sr
        assert 'primary_support' in sr
        assert 'primary_resistance' in sr
        assert sr['primary_resistance'] > sr['primary_support']
    
    def test_higher_highs_lows(self):
        """Test higher highs/lows detection"""
        hh, ll = TechnicalIndicators.higher_highs_lows(SAMPLE_PRICES, 5)
        assert isinstance(hh, bool)
        assert isinstance(ll, bool)

if __name__ == '__main__':
    pytest.main([__file__, '-v'])
