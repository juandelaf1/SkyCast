from app.services.alert_service import AlertService


class TestAlertService:
    def setup_method(self):
        self.service = AlertService()

    def test_sin_alertas(self):
        data = {"temperatura": 20.0, "humedad": 50.0, "viento": 10.0, "lluvia": 0.0}
        alertas = self.service.get_alertas_activas(data)
        assert len(alertas) == 0
        assert self.service.get_nivel_maximo(data) == "verde"

    def test_alerta_roja_calor(self):
        data = {"temperatura": 42.0, "humedad": 50.0, "viento": 10.0, "lluvia": 0.0}
        alertas = self.service.get_alertas_activas(data)
        assert len(alertas) == 1
        assert alertas[0]["nivel"] == "rojo"
        assert alertas[0]["variable"] == "temperatura"

    def test_alerta_naranja_calor(self):
        data = {"temperatura": 36.0}
        alertas = self.service.get_alertas_activas(data)
        assert len(alertas) == 1
        assert alertas[0]["nivel"] == "naranja"

    def test_alerta_azul_heladas(self):
        data = {"temperatura": -5.0}
        alertas = self.service.get_alertas_activas(data)
        assert any(a["nivel"] == "azul" for a in alertas)

    def test_alerta_viento_rojo(self):
        data = {"temperatura": 20.0, "viento": 75.0}
        alertas = self.service.get_alertas_activas(data)
        assert any(a["nivel"] == "rojo" and a["variable"] == "viento" for a in alertas)

    def test_alerta_lluvia_naranja(self):
        data = {"lluvia": 20.0}
        alertas = self.service.get_alertas_activas(data)
        assert any(a["nivel"] == "naranja" and a["variable"] == "lluvia" for a in alertas)

    def test_alerta_humedad_extrema(self):
        data = {"humedad": 95.0}
        alertas = self.service.get_alertas_activas(data)
        assert any(a["nivel"] == "rojo" and a["variable"] == "humedad" for a in alertas)

    def test_multiple_alertas(self):
        data = {"temperatura": 42.0, "viento": 80.0, "lluvia": 35.0}
        alertas = self.service.get_alertas_activas(data)
        assert len(alertas) == 3
        assert self.service.get_nivel_maximo(data) == "rojo"

    def test_nivel_maximo_naranja(self):
        data = {"temperatura": 36.0, "viento": 55.0}
        _alertas = self.service.get_alertas_activas(data)
        assert self.service.get_nivel_maximo(data) == "naranja"

    def test_datos_none_no_crash(self):
        data = {"temperatura": None, "humedad": None, "viento": None, "lluvia": None}
        alertas = self.service.get_alertas_activas(data)
        assert alertas == []
        assert self.service.get_nivel_maximo(data) == "verde"