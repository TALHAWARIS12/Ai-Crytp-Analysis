import ccxt
import asyncio
import aiohttp
from typing import Dict, List, Optional, Tuple
from datetime import datetime, timedelta
import logging
import traceback
from functools import partial
from app.core.config import settings

logger = logging.getLogger(__name__)

class MarketDataService:
    """Production market data service using CCXT and Binance Futures API"""
    
    def __init__(self):
        # Public market-data mode must not send fake credentials.
        # If keys are missing, ccxt should run unauthenticated for public endpoints.
        raw_key = (settings.binance_api_key or "").strip()
        raw_secret = (settings.binance_api_secret or "").strip()
        has_real_credentials = (
            raw_key.lower() not in {"", "public", "your_api_key_here"} and
            raw_secret.lower() not in {"", "public", "your_api_secret_here"}
        )

        exchange_config = {
            'enableRateLimit': True,
            'options': {
                'defaultType': 'future'
            }
        }
        if has_real_credentials:
            exchange_config['apiKey'] = raw_key
            exchange_config['secret'] = raw_secret
        self.exchange = ccxt.binance(exchange_config)
        self.is_restricted = False

    async def _handle_api_error(self, e: Exception, symbol: str):
        """Handle specific API errors like location restrictions"""
        error_msg = str(e)
        if "451" in error_msg or "restricted location" in error_msg.lower():
            if not self.is_restricted:
                logger.error("🛑 LOCATION RESTRICTION: Binance is blocking your IP. Please use a VPN (UK/EU/Asia) to resolve this.")
                self.is_restricted = True
            return True
        return False

    @staticmethod
    def _normalize_symbol(symbol: str) -> str:
        """Normalize user input into CCXT symbol format (e.g., BTCUSDT -> BTC/USDT)."""
        if not symbol:
            return symbol

        s = symbol.strip().upper().replace('-', '/').replace('_', '/')
        if '/' in s:
            return s

        for quote in ("USDT", "USDC", "BUSD", "BTC", "ETH"):
            if s.endswith(quote) and len(s) > len(quote):
                base = s[:-len(quote)]
                return f"{base}/{quote}"
        return s

    async def _with_retries(self, func, attempts: int = 3, base_delay: float = 0.4):
        """Run IO-bound exchange operations with retry/backoff."""
        last_exc = None
        for attempt in range(1, attempts + 1):
            try:
                return await asyncio.to_thread(func)
            except Exception as exc:
                last_exc = exc
                if attempt < attempts:
                    await asyncio.sleep(base_delay * attempt)
                else:
                    # Log full traceback on final failure
                    logger.warning(f"All {attempts} attempts failed, raising exception: {type(exc).__name__}: {exc}")
        raise last_exc
    
    async def get_ohlcv(self, symbol: str, timeframe: str = '1h', limit: int = 200) -> List[Dict]:
        """Fetch OHLCV candles from Binance Futures
        
        Args:
            symbol: Trading pair (e.g., 'BTC/USDT')
            timeframe: Candle timeframe ('1m', '5m', '15m', '1h', '4h', '1d')
            limit: Number of candles to fetch
            
        Returns:
            List of candles with OHLCV data
        """
        try:
            symbol = self._normalize_symbol(symbol)
            if not self.exchange.has['fetchOHLCV']:
                raise Exception("Exchange doesn't support OHLCV")
            ohlcv = await self._with_retries(
                partial(self.exchange.fetch_ohlcv, symbol, timeframe, limit=limit)
            )
            
            result = []
            for candle in ohlcv:
                result.append({
                    'timestamp': candle[0],
                    'datetime': datetime.fromtimestamp(candle[0] / 1000),
                    'open': candle[1],
                    'high': candle[2],
                    'low': candle[3],
                    'close': candle[4],
                    'volume': candle[5]
                })
            
            return result
        
        except Exception as e:
            if not await self._handle_api_error(e, symbol):
                exc_type = type(e).__name__
                exc_msg = str(e) if str(e) else repr(e)
                logger.error(f"Error fetching OHLCV for {symbol}: [{exc_type}] {exc_msg}", exc_info=True)
            return []
    
    async def get_ticker(self, symbol: str) -> Optional[Dict]:
        """Get current ticker information"""
        try:
            symbol = self._normalize_symbol(symbol)
            ticker = await self._with_retries(partial(self.exchange.fetch_ticker, symbol))
            
            return {
                'symbol': ticker['symbol'],
                'last': ticker['last'],
                'bid': ticker['bid'],
                'ask': ticker['ask'],
                'high': ticker['high'],
                'low': ticker['low'],
                'volume': ticker['quoteVolume'],
                'timestamp': ticker['timestamp'],
                'change': ticker['change'],
                'percentage': ticker['percentage']
            }
        
        except Exception as e:
            if not await self._handle_api_error(e, symbol):
                exc_type = type(e).__name__
                exc_msg = str(e) if str(e) else repr(e)
                logger.error(f"Error fetching ticker for {symbol}: [{exc_type}] {exc_msg}", exc_info=True)
            return None
    
    async def get_order_book(self, symbol: str, limit: int = 20) -> Optional[Dict]:
        """Get order book data"""
        try:
            symbol = self._normalize_symbol(symbol)
            orderbook = await self._with_retries(
                partial(self.exchange.fetch_order_book, symbol, limit=limit)
            )
            
            return {
                'bids': orderbook['bids'][:limit],
                'asks': orderbook['asks'][:limit],
                'timestamp': orderbook['timestamp']
            }
        
        except Exception as e:
            logger.error(f"Error fetching order book for {symbol}: {str(e)}")
            return None
    
    async def get_funding_rate(self, symbol: str) -> Optional[Dict]:
        """Get current funding rate (using CCXT for stability)"""
        try:
            symbol = self._normalize_symbol(symbol)
            # CCXT fetch_funding_rate returns a standardized object
            data = await self._with_retries(partial(self.exchange.fetch_funding_rate, symbol))
            
            rate = data.get('fundingRate', 0)
            return {
                'funding_rate': rate,
                'funding_rate_percent': rate * 100,
                'timestamp': data.get('timestamp'),
                'status': 'overheated' if abs(rate) > 0.001 else 'normal'
            }
        
        except Exception as e:
            if not await self._handle_api_error(e, symbol):
                logger.error(f"Error fetching funding rate for {symbol}: {str(e)}")
        
        return None
    
    async def get_open_interest(self, symbol: str) -> Optional[Dict]:
        """Get open interest data (using CCXT)"""
        try:
            symbol = self._normalize_symbol(symbol)
            data = await self._with_retries(partial(self.exchange.fetch_open_interest, symbol))
            
            return {
                'open_interest': float(data['openInterestAmount']),
                'timestamp': data.get('timestamp')
            }
        
        except Exception as e:
            if not await self._handle_api_error(e, symbol):
                logger.error(f"Error fetching open interest for {symbol}: {str(e)}")
        
        return None
    
    async def get_multi_timeframe_data(self, symbol: str, timeframes: List[str] = None) -> Dict:
        """Fetch data for multiple timeframes simultaneously"""
        symbol = self._normalize_symbol(symbol)
        if timeframes is None:
            timeframes = ['15m', '1h', '4h', '1d']
        
        tasks = [self.get_ohlcv(symbol, tf, 100) for tf in timeframes]
        results = await asyncio.gather(*tasks)
        
        return {
            tf: data for tf, data in zip(timeframes, results)
        }
    
    async def get_full_market_snapshot(self, symbol: str) -> Dict:
        """Get complete market snapshot for analysis"""
        symbol = self._normalize_symbol(symbol)
        ticker = await self.get_ticker(symbol)
        funding = await self.get_funding_rate(symbol)
        oi = await self.get_open_interest(symbol)
        orderbook = await self.get_order_book(symbol)
        multi_tf = await self.get_multi_timeframe_data(symbol)
        
        return {
            'symbol': symbol,
            'ticker': ticker,
            'funding_rate': funding,
            'open_interest': oi,
            'order_book': orderbook,
            'candles': multi_tf,
            'timestamp': datetime.utcnow().isoformat()
        }
    
    async def validate_symbol(self, symbol: str) -> bool:
        """Validate if symbol exists and is tradeable"""
        try:
            symbol = self._normalize_symbol(symbol)
            await self._with_retries(self.exchange.load_markets)
            return symbol in self.exchange.symbols
        except:
            return False
    
    async def search_symbols(self, query: str) -> List[str]:
        """Search available trading pairs"""
        try:
            await self._with_retries(self.exchange.load_markets)
            query = query.upper()
            return [s for s in self.exchange.symbols if query in s][:10]
        except:
            return []

# Global instance
market_data_service = MarketDataService()
