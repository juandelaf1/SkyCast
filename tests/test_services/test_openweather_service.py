import asyncio
from unittest.mock import AsyncMock, MagicMock, patch

from app.services.openweather_service import OpenWeatherService


class TestOpenWeatherService:
    def setup_method(self):
        self.service = OpenWeatherService()

    def test_get_weather_with_key_returns_data(self):
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "name": "Madrid",
            "main": {"temp": 22.5, "humidity": 60, "pressure": 1013},
            "wind": {"speed": 5.0},
        }

        with patch("httpx.AsyncClient") as mock_client:
            mock_client.return_value.__aenter__ = AsyncMock(
                return_value=MagicMock(get=AsyncMock(return_value=mock_response))
            )
            mock_client.return_value.__aexit__ = AsyncMock(return_value=False)
            result = asyncio.run(self.service.get_weather(lat=40.4168, lon=-3.7038))

        assert result is not None
        assert "data" in result
        assert result["data"]["temperatura"] == 22.5

    def test_ms_to_kmh_none(self):
        assert self.service._ms_to_kmh(None) is None

    def test_ms_to_kmh_valid(self):
        result = self.service._ms_to_kmh(10.0)
        assert result == 36.0

    def test_ms_to_kmh_zero(self):
        result = self.service._ms_to_kmh(0)
        assert result == 0.0

    def test_ms_to_kmh_string(self):
        result = self.service._ms_to_kmh("5.0")
        assert result == 18.0

    def test_ms_to_kmh_invalid(self):
        assert self.service._ms_to_kmh("abc") is None
