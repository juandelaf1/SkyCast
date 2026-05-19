from app.services.openweather_service import OpenWeatherService


class TestOpenWeatherService:
    def setup_method(self):
        self.service = OpenWeatherService()

    def test_no_api_key_returns_none(self):
        result = self.service.get_weather(lat=40.4168, lon=-3.7038)
        import asyncio
        result = asyncio.run(result)
        assert result is None

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
