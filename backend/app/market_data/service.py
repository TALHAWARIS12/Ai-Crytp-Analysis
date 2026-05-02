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

# Simple in-memory cache for CoinGecko data (TTL: 60 seconds)
class PriceCache:
    def __init__(self):
        self.cache = {}
        self.timestamps = {}
    
    def get(self, symbol: str) -> Optional[Dict]:
        """Get cached price if fresh (< 60s old)"""
        if symbol in self.cache:
            age = (datetime.utcnow() - self.timestamps[symbol]).total_seconds()
            if age < 60:  # Cache TTL: 60 seconds
                return self.cache[symbol]
            else:
                del self.cache[symbol]
                del self.timestamps[symbol]
        return None
    
    def set(self, symbol: str, data: Dict):
        """Cache price data"""
        self.cache[symbol] = data
        self.timestamps[symbol] = datetime.utcnow()
    
    def clear_old(self):
        """Remove stale entries older than 2 minutes"""
        now = datetime.utcnow()
        symbols_to_remove = [
            s for s, ts in self.timestamps.items() 
            if (now - ts).total_seconds() > 120
        ]
        for s in symbols_to_remove:
            del self.cache[s]
            del self.timestamps[s]

price_cache = PriceCache()

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
                'defaultType': 'future',
                'fetchOHLCV': 'v3',
                'fetchTicker': 'v3',
            }
        }
        # Use proxy if available (for geo-restricted locations like Render)
        proxy_url = settings.binance_api_proxy
        if proxy_url:
            exchange_config['httpProxy'] = proxy_url
            exchange_config['httpsProxy'] = proxy_url
            logger.info(f"Using Binance API proxy: {proxy_url}")
        
        if has_real_credentials:
            exchange_config['apiKey'] = raw_key
            exchange_config['secret'] = raw_secret
        self.exchange = ccxt.binance(exchange_config)
        self.kucoin_fallback = ccxt.kucoin({'enableRateLimit': True})
        self.is_restricted = False
        self.cache = price_cache
        self.coingecko_rate_limit_reset = 0  # Timestamp when rate limit resets

    async def _handle_api_error(self, e: Exception, symbol: str):
        """Handle specific API errors like location restrictions"""
        error_msg = str(e)
        if "451" in error_msg or "restricted location" in error_msg.lower():
            if not self.is_restricted:
                logger.error("🛑 LOCATION RESTRICTION: Binance is blocking your IP (HTTP 451). This is common on Render.")
                logger.error("SOLUTIONS: (1) Add BINANCE_API_PROXY env var, (2) Use VPN, (3) Switch providers")
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
        
        # Default to USDT for single words (e.g., BTC -> BTC/USDT)
        if len(s) >= 2 and len(s) <= 10:
            return f"{s}/USDT"
            
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
        """Fetch OHLCV candles from Binance Futures"""
        symbol = self._normalize_symbol(symbol)
        
        if self.is_restricted:
            return await self._get_ohlcv_kucoin(symbol, timeframe, limit)
            
        try:
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
            if await self._handle_api_error(e, symbol):
                return await self._get_ohlcv_kucoin(symbol, timeframe, limit)
                
            exc_type = type(e).__name__
            exc_msg = str(e) if str(e) else repr(e)
            logger.error(f"Error fetching OHLCV for {symbol}: [{exc_type}] {exc_msg}", exc_info=True)
            return []

    async def _get_ohlcv_kucoin(self, symbol: str, timeframe: str, limit: int) -> List[Dict]:
        """Fallback to KuCoin for OHLCV data if Binance is restricted"""
        try:
            # KuCoin uses the same symbol format for spot
            ohlcv = await self._with_retries(
                partial(self.kucoin_fallback.fetch_ohlcv, symbol, timeframe, limit=limit)
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
            logger.error(f"KuCoin fallback failed for OHLCV {symbol}: {str(e)}")
            return []
    
    async def get_ticker(self, symbol: str) -> Optional[Dict]:
        """Get current ticker information with CoinGecko fallback"""
        symbol = self._normalize_symbol(symbol)
        if self.is_restricted:
            return await self._get_ticker_coingecko(symbol)
            
        try:
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
            if self.is_restricted:
                logger.warning(f"Binance restricted, trying CoinGecko fallback for {symbol}")
                return await self._get_ticker_coingecko(symbol)
            
            if not await self._handle_api_error(e, symbol):
                exc_type = type(e).__name__
                exc_msg = str(e) if str(e) else repr(e)
                logger.error(f"Error fetching ticker for {symbol}: [{exc_type}] {exc_msg}")
            return None

    async def get_top_gainers(self, limit: int = 10) -> List[Dict]:
        """Fetch top gainers with fallback support"""
        exchange_to_use = self.exchange
        if self.is_restricted:
            exchange_to_use = self.kucoin_fallback
            
        try:
            await exchange_to_use.load_markets()
            tickers = await self._with_retries(exchange_to_use.fetch_tickers)
            
            # Filter for USDT pairs and sort by percentage change
            usdt_tickers = [t for s, t in tickers.items() if s.endswith('/USDT') or s.endswith('-USDT')]
            sorted_tickers = sorted(
                usdt_tickers, 
                key=lambda x: x.get('percentage', 0) or 0, 
                reverse=True
            )[:limit]
            
            return sorted_tickers
        except Exception as e:
            if not self.is_restricted and await self._handle_api_error(e, "MARKET"):
                return await self.get_top_gainers(limit)
            logger.error(f"Error fetching top gainers: {e}")
            return []
    
    async def _get_ticker_coingecko(self, symbol: str) -> Optional[Dict]:
        """Fallback: Get ticker from CoinGecko (no IP restrictions, with caching and rate limit handling)"""
        try:
            # Check cache first
            cached = self.cache.get(symbol)
            if cached:
                logger.info(f"Using cached price for {symbol}")
                return cached
            
            # Check if we're rate limited
            now = datetime.utcnow().timestamp()
            if now < self.coingecko_rate_limit_reset:
                wait_time = int(self.coingecko_rate_limit_reset - now)
                logger.warning(f"CoinGecko rate limit active, waiting {wait_time}s before retry")
                await asyncio.sleep(min(wait_time + 1, 5))  # Wait but cap at 5s
                self.coingecko_rate_limit_reset = 0
            
            # Map symbols to CoinGecko IDs
            coingecko_ids = {
                'BTC/USDT': 'bitcoin',
                'ETH/USDT': 'ethereum',
                'SOL/USDT': 'solana',
                'XRP/USDT': 'ripple',
                'ADA/USDT': 'cardano',
                'DOGE/USDT': 'dogecoin',
                'MATIC/USDT': 'matic-network',
                'BNB/USDT': 'binancecoin',
                'BTC': 'bitcoin',
                'ETH': 'ethereum'
            }
            
            coin_id = coingecko_ids.get(symbol)
            if not coin_id:
                logger.warning(f"CoinGecko mapping missing for {symbol}")
                return None
            
            # Retry logic with exponential backoff
            for attempt in range(1, 4):  # 3 attempts
                try:
                    async with aiohttp.ClientSession() as session:
                        url = f"https://api.coingecko.com/api/v3/simple/price?ids={coin_id}&vs_currencies=usd&include_market_cap=true&include_24hr_vol=true&include_24hr_change=true"
                        async with session.get(url, timeout=aiohttp.ClientTimeout(total=10)) as resp:
                            if resp.status == 429:  # Rate limited
                                retry_after = int(resp.headers.get('Retry-After', 60))
                                logger.warning(f"CoinGecko rate limit (attempt {attempt}/3): retry after {retry_after}s")
                                self.coingecko_rate_limit_reset = datetime.utcnow().timestamp() + retry_after
                                
                                if attempt < 3:
                                    await asyncio.sleep(min(retry_after, 5))
                                    continue
                                else:
                                    return None
                            
                            elif resp.status != 200:
                                logger.error(f"CoinGecko API error: {resp.status}")
                                if attempt < 3:
                                    await asyncio.sleep(2 ** attempt)  # Exponential backoff
                                    continue
                                return None
                            
                            data = await resp.json()
                            coin_data = data.get(coin_id, {})
                            
                            if not coin_data:
                                return None
                            
                            price = coin_data.get('usd', 0)
                            result = {
                                'symbol': symbol,
                                'last': price,
                                'bid': price * 0.999,  # Approximate bid
                                'ask': price * 1.001,  # Approximate ask
                                'high': price,  # CoinGecko doesn't provide 24h high
                                'low': price,
                                'volume': coin_data.get('usd_24h_vol', 0),
                                'timestamp': int(datetime.utcnow().timestamp() * 1000),
                                'change': coin_data.get('usd_24h_change', 0),
                                'percentage': coin_data.get('usd_24h_change', 0),
                                'source': 'coingecko'
                            }
                            
                            # Cache the result
                            self.cache.set(symbol, result)
                            return result
                
                except asyncio.TimeoutError:
                    logger.warning(f"CoinGecko timeout (attempt {attempt}/3)")
                    if attempt < 3:
                        await asyncio.sleep(2 ** attempt)
                        continue
                    return None
                except Exception as e:
                    logger.error(f"CoinGecko request error (attempt {attempt}/3): {str(e)}")
                    if attempt < 3:
                        await asyncio.sleep(2 ** attempt)
                        continue
                    return None
        
        except Exception as e:
            logger.error(f"CoinGecko fallback failed for {symbol}: {str(e)}")
            return None
    
    async def get_order_book(self, symbol: str, limit: int = 20) -> Optional[Dict]:
        """Get order book data"""
        symbol = self._normalize_symbol(symbol)
        
        if self.is_restricted:
            # Fallback to KuCoin
            try:
                orderbook = await self._with_retries(
                    partial(self.kucoin_fallback.fetch_order_book, symbol, limit=limit)
                )
                return {
                    'bids': orderbook['bids'][:limit],
                    'asks': orderbook['asks'][:limit],
                    'timestamp': orderbook['timestamp']
                }
            except Exception as e:
                logger.error(f"KuCoin order book fallback failed: {str(e)}")
                return None
                
        try:
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
        symbol = self._normalize_symbol(symbol)
        if self.is_restricted:
            return None  # Skip if restricted
            
        try:
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
        symbol = self._normalize_symbol(symbol)
        if self.is_restricted:
            return None  # Skip if restricted
            
        try:
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
        symbol = self._normalize_symbol(symbol)
        
        if self.is_restricted:
            try:
                await self._with_retries(self.kucoin_fallback.load_markets)
                return symbol in self.kucoin_fallback.symbols
            except:
                return True # Optimistic fallback
                
        try:
            await self._with_retries(self.exchange.load_markets)
            return symbol in self.exchange.symbols
        except:
            return False
    
    async def search_symbols(self, query: str) -> List[str]:
        """Search available trading pairs"""
        exchange_to_use = self.kucoin_fallback if self.is_restricted else self.exchange
        try:
            await self._with_retries(exchange_to_use.load_markets)
            query = query.upper()
            return [s for s in exchange_to_use.symbols if query in s][:10]
        except:
            return []

# Global instance
market_data_service = MarketDataService()
