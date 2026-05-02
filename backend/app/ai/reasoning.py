import httpx
from typing import Dict, Any
import logging
import json
from app.core.config import settings

logger = logging.getLogger(__name__)

class AIReasoningEngine:
    """AI-powered analysis layer - processes structured data for trader reasoning"""
    
    @staticmethod
    async def analyze_coin(market_data: Dict[str, Any]) -> str:
        """Generate professional analysis for a coin using real market data
        
        Args:
            market_data: Structured market analysis from backend
            
        Returns:
            Professional trader reasoning
        """
        
        if not settings.grok_api_key:
            return AIReasoningEngine._fallback_analysis(market_data)
        
        try:
            # Build fact-based context for AI
            facts = f"""
Based on real institutional market data:

Symbol: {market_data.get('symbol')}
Current Price: ${market_data.get('current_price', 'N/A')}
Bias Judgment: {market_data.get('judgment', 'N/A')}

Technical Analysis (Multi-Timeframe):
{market_data.get('mtf')}

Institutional Confluences:
- Liquidity Zones: {market_data.get('liquidity')}
- Volume Profile: {market_data.get('volume')}
- Order Flow (Imbalance/Walls): {market_data.get('order_flow')}
- Funding Rate: {market_data.get('funding_rate')}
"""
            
            prompt = f"""You are an elite institutional crypto trader with 15+ years experience.
            
Analyze this REAL market data and provide professional trader perspective:

{facts}

Provide:
1. Market situation assessment (1-2 sentences)
2. Risk/reward evaluation
3. Specific action (Long/Short/Wait/Avoid)
4. Why this specific decision?
5. Key levels to watch
6. When to take profit / stop loss triggers

Be concise, professional, and decisive. No beginner explanations."""
            
            response = await AIReasoningEngine._call_grok(
                model=settings.grok_model,
                system_prompt="You are an elite professional crypto trader.",
                user_prompt=prompt
            )
            
            return response
        
        except Exception as e:
            logger.error(f"Grok API error: {str(e)}")
            return AIReasoningEngine._fallback_analysis(market_data)
    
    @staticmethod
    async def validate_strategy_reasoning(strategy_result: Dict[str, Any]) -> str:
        """Generate reasoning for strategy validation result"""
        
        if not settings.grok_api_key:
            return AIReasoningEngine._fallback_strategy_reasoning(strategy_result)
        
        try:
            facts = f"""
Strategy Validation Results:
- Status: {strategy_result.get('status')}
- Confidence: {strategy_result.get('confidence')}%
- Technical Alignment: {', '.join(strategy_result.get('reasons', [])[:3])}
- Current Price: ${strategy_result.get('current_price')}
- Entry Zone: ${strategy_result.get('entry_low')} - ${strategy_result.get('entry_high')}
- Trend Direction: {strategy_result.get('trend')}
"""
            
            prompt = f"""As a professional trader, explain this strategy validation:

{facts}

Provide:
1. Why this status was assigned
2. Key factors supporting the decision
3. What would change the decision?
4. Risk factors to consider
5. Action plan for trader

Be direct and professional."""
            
            response = await AIReasoningEngine._call_grok(
                model=settings.grok_model,
                system_prompt="You are an elite professional crypto trader.",
                user_prompt=prompt
            )
            
            return response
        
        except Exception as e:
            logger.error(f"Grok API error: {str(e)}")
            return AIReasoningEngine._fallback_strategy_reasoning(strategy_result)
    
    @staticmethod
    async def evaluate_signal(signal_data: Dict[str, Any]) -> str:
        """Generate reasoning for signal evaluation"""
        
        if not settings.grok_api_key:
            return AIReasoningEngine._fallback_signal_eval(signal_data)
        
        try:
            facts = f"""
Signal Verification Results:
- Status: {signal_data.get('status')}
- Risk Score: {signal_data.get('risk_score')}%
- Symbol: {signal_data.get('symbol')}
- Direction: {signal_data.get('direction')}
- Entry Price: ${signal_data.get('entry_price')}
- Stop Loss: ${signal_data.get('stop_loss')}
- Risk/Reward: {signal_data.get('risk_reward', 'N/A')}
- Volume: {signal_data.get('volume_strength')}x average
- Issues: {', '.join(signal_data.get('warnings', [])[:3])}
"""
            
            prompt = f"""Professional trader perspective on this signal:

{facts}

Evaluate:
1. Overall assessment of this signal
2. Main risks identified
3. Recommended action
4. Risk management suggestions
5. If taking it, specific entry trigger

Be professional and direct."""
            
            response = await AIReasoningEngine._call_grok(
                model=settings.grok_model,
                system_prompt="You are an elite professional crypto trader.",
                user_prompt=prompt
            )
            
            return response
        
        except Exception as e:
            logger.error(f"Grok API error: {str(e)}")
            return AIReasoningEngine._fallback_signal_eval(signal_data)
    
    @staticmethod
    async def _call_grok(model: str, system_prompt: str, user_prompt: str) -> str:
        """Call Grok/Gemini API via xAI or Google"""
        if not settings.grok_api_key:
            raise ValueError("Grok/Gemini API key not configured")
        
        is_reasoning = "reasoning" in model.lower()
        is_groq = settings.grok_api_key.startswith("gsk_")
        is_gemini = "gemini" in model.lower() or not (is_groq or settings.grok_api_key.startswith("xai-"))
        
        # Override model name for Gemini if it's just 'gemini-1.5-flash' etc.
        if is_gemini and not model.startswith("models/"):
            # Ensure we use a valid model like models/gemini-1.5-flash-latest
            if "flash" in model.lower():
                model = "models/gemini-1.5-flash"
            elif "pro" in model.lower():
                model = "models/gemini-1.5-pro"
            else:
                model = "models/gemini-1.5-flash" # Default to flash
                
        if is_groq:
            endpoint = "https://api.groq.com/openai/v1/chat/completions"
        elif is_gemini:
            # Strip 'models/' from the model string for the URL path
            model_name = model.replace("models/", "")
            endpoint = f"https://generativelanguage.googleapis.com/v1beta/models/{model_name}:generateContent?key={settings.grok_api_key}"
        elif is_reasoning:
            endpoint = "https://api.x.ai/v1/responses"
        else:
            endpoint = "https://api.x.ai/v1/chat/completions"
        
        from app.utils.http import http_client
        import asyncio
        import httpx
        
        client = http_client.get_client()
        
        if is_gemini:
            payload = {
                "contents": [{
                    "parts": [{"text": f"{system_prompt}\n\n{user_prompt}"}]
                }]
            }
        elif is_reasoning and not is_groq:
            payload = {
                "model": model,
                "input": f"{system_prompt}\n\n{user_prompt}"
            }
        else:
            payload = {
                "model": model,
                "messages": [
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                "temperature": 0.7,
                "max_tokens": 500
            }

        headers = {"Content-Type": "application/json"}
        if not is_gemini:
            headers["Authorization"] = f"Bearer {settings.grok_api_key}"

        max_retries = 3
        base_delay = 2
        
        for attempt in range(max_retries):
            try:
                response = await client.post(
                    endpoint,
                    headers=headers,
                    json=payload,
                    timeout=45.0
                )
                
                if response.status_code != 200:
                    raise Exception(f"API error: {response.status_code} - {response.text}")
                
                data = response.json()
                if is_gemini:
                    try:
                        return data['candidates'][0]['content']['parts'][0]['text']
                    except Exception as e:
                        logger.error(f"Gemini parsing error: {e}. Data: {data}")
                        return "Analysis unavailable"
                elif is_reasoning:
                    return data.get('output', data.get('response', 'No output from model'))
                else:
                    return data['choices'][0]['message']['content']
                    
            except Exception as e:
                logger.warning(f"AI API attempt {attempt + 1}/{max_retries} failed: {str(e)}")
                if attempt < max_retries - 1:
                    await asyncio.sleep(base_delay * (2 ** attempt))
                else:
                    logger.error("AI API failed after max retries")
                    raise
    
    @staticmethod
    def _fallback_analysis(data: Dict) -> str:
        """Fallback analysis when Grok unavailable"""
        trend = data.get('trend', 'Unknown')
        status = "Looks bullish" if "BULLISH" in trend else "Looks bearish" if "BEARISH" in trend else "Sideways"
        return f"""
Institutional Analysis {data.get('symbol')}:

Current Status: {status}
Trend Strength: {data.get('confidence', 'Unknown')}%

The market shows {trend.lower()} momentum with support at ${data.get('support')} and resistance at ${data.get('resistance')}.

Volume is {data.get('volume_strength')}x average.

Decision: Wait for clearer signals before entering. Risk management priority.
        """
    
    @staticmethod
    def _fallback_strategy_reasoning(data: Dict) -> str:
        return f"""Strategy Analysis: {data.get('status')}
        
This setup shows {data.get('confidence', 0)}% alignment with the strategy rules.

Key Technical Factors:
{chr(10).join('- ' + r for r in data.get('reasons', [])[:3])}

Recommendation: {data.get('status')} with caution. Use tight stops.
        """
    
    @staticmethod
    def _fallback_signal_eval(data: Dict) -> str:
        return f"""Signal Evaluation: {data.get('status')}

Risk Score: {data.get('risk_score')}%
Volume Confirmation: {data.get('volume_strength')}x

This signal has moderate risk. {data.get('status')}.

Important: Use stop loss at ${data.get('stop_loss')} strictly.
        """
