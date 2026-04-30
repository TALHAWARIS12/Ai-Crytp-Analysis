from fastapi.testclient import TestClient

from app.main import app
from app.market_data.service import market_data_service
from app.ai.reasoning import AIReasoningEngine


client = TestClient(app)


def test_health_ok():
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json()["status"] == "healthy"


def test_price_returns_503_when_exchange_unavailable(monkeypatch):
    async def _ticker(_symbol: str):
        return None

    monkeypatch.setattr(market_data_service, "get_ticker", _ticker)
    response = client.get("/api/v1/price/BTCUSDT")
    assert response.status_code == 503


def test_analyze_success(monkeypatch):
    async def _validate_symbol(_symbol: str):
        return True

    async def _snapshot(_symbol: str):
        candles = [
            {"close": 70000 + i, "high": 70100 + i, "low": 69900 + i, "volume": 1000 + i}
            for i in range(260)
        ]
        return {
            "candles": {"4h": candles},
            "funding_rate": None,
            "open_interest": None,
        }

    async def _ai(_data):
        return "Test reasoning"

    monkeypatch.setattr(market_data_service, "validate_symbol", _validate_symbol)
    monkeypatch.setattr(market_data_service, "get_full_market_snapshot", _snapshot)
    monkeypatch.setattr(AIReasoningEngine, "analyze_coin", _ai)

    response = client.post("/api/v1/analyze", json={"symbol": "BTCUSDT"})
    assert response.status_code == 200
    body = response.json()
    assert body["symbol"] == "BTCUSDT"
    assert "trend" in body
    assert "analysis" in body
