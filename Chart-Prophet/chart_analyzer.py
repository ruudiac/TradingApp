import os
from google import genai
from google.genai import types
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception
from typing import Dict, Any, List
from pydantic import BaseModel
import json

AI_INTEGRATIONS_GEMINI_API_KEY = os.environ.get("AI_INTEGRATIONS_GEMINI_API_KEY")
AI_INTEGRATIONS_GEMINI_BASE_URL = os.environ.get("AI_INTEGRATIONS_GEMINI_BASE_URL")

client = genai.Client(
    api_key=AI_INTEGRATIONS_GEMINI_API_KEY,
    http_options={
        'api_version': '',
        'base_url': AI_INTEGRATIONS_GEMINI_BASE_URL
    }
)

class TechnicalIndicator(BaseModel):
    name: str
    value: str
    signal: str
    description: str

class FibonacciLevel(BaseModel):
    level: str
    price: str
    significance: str

class TradingAnalysis(BaseModel):
    overall_recommendation: str
    confidence_level: str
    trend_direction: str
    support_levels: List[str]
    resistance_levels: List[str]
    rsi_analysis: TechnicalIndicator
    macd_analysis: TechnicalIndicator
    fibonacci_levels: List[FibonacciLevel]
    key_observations: List[str]
    risk_factors: List[str]
    entry_points: List[str]
    exit_points: List[str]
    summary: str

def is_rate_limit_error(exception: BaseException) -> bool:
    error_msg = str(exception)
    return (
        "429" in error_msg
        or "RATELIMIT_EXCEEDED" in error_msg
        or "quota" in error_msg.lower()
        or "rate limit" in error_msg.lower()
        or (hasattr(exception, 'status') and getattr(exception, 'status', None) == 429)
    )

class ChartAnalyzer:
    def __init__(self):
        self.analysis_prompt = """You are an expert technical analyst and professional trader. Analyze this trading chart image and provide a comprehensive technical analysis.

Please analyze the chart and provide:

1. **Overall Recommendation**: Should the trader BUY, SELL, or HOLD? Be decisive.

2. **Confidence Level**: Rate your confidence as HIGH, MEDIUM, or LOW.

3. **Trend Direction**: Is the current trend BULLISH, BEARISH, or SIDEWAYS?

4. **Support Levels**: Identify key support price levels visible on the chart.

5. **Resistance Levels**: Identify key resistance price levels visible on the chart.

6. **RSI Analysis**: If RSI is visible or can be inferred:
   - Current approximate value
   - Signal (OVERBOUGHT, OVERSOLD, or NEUTRAL)
   - Interpretation

7. **MACD Analysis**: If MACD is visible or can be inferred:
   - Current signal (BULLISH, BEARISH, or NEUTRAL)
   - Whether there's a crossover
   - Interpretation

8. **Fibonacci Retracement Levels**: Identify key Fibonacci levels:
   - 0%, 23.6%, 38.2%, 50%, 61.8%, 78.6%, 100%
   - Which levels are acting as support/resistance

9. **Key Observations**: List important patterns, candlestick formations, or notable features.

10. **Risk Factors**: What could go wrong with this trade?

11. **Entry Points**: Suggested price levels to enter a position.

12. **Exit Points**: Suggested price levels for take-profit or stop-loss.

13. **Summary**: A concise 2-3 sentence summary of your analysis.

Be specific with price levels where visible. If certain indicators are not visible on the chart, make reasonable inferences based on price action and patterns."""

    @retry(
        stop=stop_after_attempt(5),
        wait=wait_exponential(multiplier=2, min=4, max=60),
        retry=retry_if_exception(is_rate_limit_error),
        reraise=True
    )
    def _call_gemini(self, image_data: bytes, mime_type: str) -> str:
        response = client.models.generate_content(
            model="gemini-2.5-flash",
            contents=[
                types.Part(text=self.analysis_prompt),
                types.Part(
                    inline_data=types.Blob(
                        mime_type=mime_type,
                        data=image_data
                    )
                )
            ]
        )
        return response.text or ""

    def analyze_chart(self, image_data: bytes, mime_type: str = "image/png") -> Dict[str, Any]:
        try:
            raw_analysis = self._call_gemini(image_data, mime_type)
            
            structured_result = self._parse_analysis(raw_analysis)
            
            return structured_result
            
        except Exception as e:
            return {
                "error": True,
                "message": str(e),
                "overall_recommendation": "UNABLE TO ANALYZE",
                "confidence_level": "N/A",
                "trend_direction": "UNKNOWN",
                "raw_analysis": str(e)
            }

    def _parse_analysis(self, raw_text: str) -> Dict[str, Any]:
        result = {
            "overall_recommendation": self._extract_recommendation(raw_text),
            "confidence_level": self._extract_field(raw_text, ["confidence", "confidence level"]),
            "trend_direction": self._extract_field(raw_text, ["trend direction", "trend"]),
            "support_levels": self._extract_list(raw_text, "support"),
            "resistance_levels": self._extract_list(raw_text, "resistance"),
            "rsi_analysis": self._extract_indicator(raw_text, "rsi"),
            "macd_analysis": self._extract_indicator(raw_text, "macd"),
            "fibonacci_levels": self._extract_fibonacci(raw_text),
            "key_observations": self._extract_list(raw_text, "observation"),
            "risk_factors": self._extract_list(raw_text, "risk"),
            "entry_points": self._extract_list(raw_text, "entry"),
            "exit_points": self._extract_list(raw_text, "exit"),
            "summary": self._extract_summary(raw_text),
            "raw_analysis": raw_text
        }
        return result

    def _extract_recommendation(self, text: str) -> str:
        text_upper = text.upper()
        if "STRONG BUY" in text_upper:
            return "STRONG BUY"
        elif "STRONG SELL" in text_upper:
            return "STRONG SELL"
        elif "BUY" in text_upper and "SELL" not in text_upper[:text_upper.find("BUY")+50]:
            return "BUY"
        elif "SELL" in text_upper:
            return "SELL"
        elif "HOLD" in text_upper:
            return "HOLD"
        return "HOLD"

    def _extract_field(self, text: str, keywords: list) -> str:
        text_lower = text.lower()
        for keyword in keywords:
            if keyword in text_lower:
                idx = text_lower.find(keyword)
                snippet = text[idx:idx+100]
                if "HIGH" in snippet.upper():
                    return "HIGH"
                elif "MEDIUM" in snippet.upper() or "MODERATE" in snippet.upper():
                    return "MEDIUM"
                elif "LOW" in snippet.upper():
                    return "LOW"
                elif "BULLISH" in snippet.upper():
                    return "BULLISH"
                elif "BEARISH" in snippet.upper():
                    return "BEARISH"
                elif "SIDEWAYS" in snippet.upper() or "NEUTRAL" in snippet.upper():
                    return "SIDEWAYS"
        return "N/A"

    def _extract_list(self, text: str, keyword: str) -> List[str]:
        lines = text.split('\n')
        items = []
        in_section = False
        
        for line in lines:
            if keyword.lower() in line.lower() and ':' in line:
                in_section = True
                after_colon = line.split(':', 1)[-1].strip()
                if after_colon:
                    items.append(after_colon)
                continue
            
            if in_section:
                if line.strip().startswith('-') or line.strip().startswith('*') or line.strip().startswith('•'):
                    items.append(line.strip().lstrip('-*• '))
                elif line.strip() and line.strip()[0].isdigit():
                    items.append(line.strip().lstrip('0123456789. '))
                elif line.strip() == '' or (line.strip() and line.strip()[0] == '#'):
                    in_section = False
        
        return items[:5] if items else ["Not identified in chart"]

    def _extract_indicator(self, text: str, indicator: str) -> Dict[str, str]:
        text_lower = text.lower()
        result = {
            "name": indicator.upper(),
            "value": "N/A",
            "signal": "NEUTRAL",
            "description": "Not visible or cannot be determined"
        }
        
        if indicator in text_lower:
            idx = text_lower.find(indicator)
            snippet = text[idx:idx+300]
            
            if "OVERBOUGHT" in snippet.upper():
                result["signal"] = "OVERBOUGHT"
            elif "OVERSOLD" in snippet.upper():
                result["signal"] = "OVERSOLD"
            elif "BULLISH" in snippet.upper():
                result["signal"] = "BULLISH"
            elif "BEARISH" in snippet.upper():
                result["signal"] = "BEARISH"
            
            lines = snippet.split('\n')
            for line in lines[:3]:
                if line.strip():
                    result["description"] = line.strip()[:200]
                    break
        
        return result

    def _extract_fibonacci(self, text: str) -> List[Dict[str, str]]:
        fib_levels = []
        standard_levels = ["0%", "23.6%", "38.2%", "50%", "61.8%", "78.6%", "100%"]
        
        for level in standard_levels:
            if level in text:
                idx = text.find(level)
                snippet = text[idx:idx+150]
                significance = "Key level"
                if "support" in snippet.lower():
                    significance = "Acting as support"
                elif "resistance" in snippet.lower():
                    significance = "Acting as resistance"
                
                fib_levels.append({
                    "level": level,
                    "price": "See chart",
                    "significance": significance
                })
        
        if not fib_levels:
            fib_levels.append({
                "level": "N/A",
                "price": "N/A",
                "significance": "Fibonacci levels not visible on chart"
            })
        
        return fib_levels

    def _extract_summary(self, text: str) -> str:
        text_lower = text.lower()
        if "summary" in text_lower:
            idx = text_lower.find("summary")
            snippet = text[idx:]
            lines = snippet.split('\n')
            summary_parts = []
            for line in lines[1:4]:
                if line.strip() and not line.strip().startswith('#'):
                    summary_parts.append(line.strip())
            if summary_parts:
                return ' '.join(summary_parts)[:500]
        
        sentences = text.replace('\n', ' ').split('.')
        return '. '.join(sentences[:3]) + '.' if sentences else "Analysis complete."
