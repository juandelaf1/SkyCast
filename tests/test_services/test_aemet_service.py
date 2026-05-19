from app.services.aemet_service import AemetService


class TestAemetService:
    def setup_method(self):
        self.service = AemetService()

    def test_parse_float_none(self):
        assert self.service._parse_float(None) is None

    def test_parse_float_empty_string(self):
        assert self.service._parse_float("") is None

    def test_parse_float_valid(self):
        assert self.service._parse_float("22.5") == 22.5

    def test_parse_float_comma(self):
        assert self.service._parse_float("22,5") == 22.5

    def test_parse_float_invalid(self):
        assert self.service._parse_float("abc") is None

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

    def test_normalize_aemet_data(self):
        raw = {"ta": "25.0", "hr": "60", "vv": "5.0", "prec": "0.0", "p": "1015", "ubi": "Madrid"}
        result = self.service._normalize_aemet_data(raw)
        assert result["temperatura"] == 25.0
        assert result["humedad"] == 60.0
        assert result["viento"] == 18.0
        assert result["lluvia"] == 0.0
        assert result["presion"] == 1015.0
        assert result["municipio"] == "Madrid"

    def test_normalize_aemet_data_empty(self):
        result = self.service._normalize_aemet_data({})
        assert result["temperatura"] is None
        assert result["humedad"] is None
        assert result["municipio"] == "Madrid"

    def test_get_fallback_data(self):
        result = self.service._get_fallback_data(40.4168, -3.7038, "Madrid")
        assert result["estacion_nombre"] == "Madrid-Retiro"
        assert result["data"]["temperatura"] == 22.5
        assert result["data"]["municipio"] == "Madrid"
        assert result["data"]["provincia"] == "Madrid"

    def test_get_fallback_data_no_city(self):
        result = self.service._get_fallback_data(40.4168, -3.7038, None)
        assert result["data"]["municipio"] == "Madrid"

    def test_get_weather_no_api_key_sync(self):
        import asyncio
        result = asyncio.run(self.service.get_weather(lat=40.4168, lon=-3.7038))
        assert result["estacion_nombre"] == "Madrid-Retiro"
        assert result["data"]["temperatura"] == 22.5
