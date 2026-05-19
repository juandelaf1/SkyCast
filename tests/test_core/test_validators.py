from datetime import date
from app.core.validators import validar_registro


class TestValidators:

    def test_temperatura_valida(self):
        errors = validar_registro({"temperatura": 25.0, "humedad": 50.0, "viento": 10.0, "lluvia": 0.0})
        assert len(errors) == 0

    def test_temperatura_extrema(self):
        errors = validar_registro({"temperatura": 65.0})
        assert any("Temperatura fuera de rango" in e for e in errors)

    def test_temperatura_heladas(self):
        errors = validar_registro({"temperatura": -30.0})
        assert any("Temperatura fuera de rango" in e for e in errors)

    def test_humedad_fuera_rango(self):
        errors = validar_registro({"humedad": 150.0})
        assert any("Humedad fuera de rango" in e for e in errors)

    def test_humedad_negativa(self):
        errors = validar_registro({"humedad": -5.0})
        assert any("Humedad fuera de rango" in e for e in errors)

    def test_viento_negativo(self):
        errors = validar_registro({"viento": -10.0})
        assert any("negativo" in e for e in errors)

    def test_viento_extremo(self):
        errors = validar_registro({"viento": 200.0})
        assert any("Viento fuera de rango" in e for e in errors)

    def test_lluvia_negativa(self):
        errors = validar_registro({"lluvia": -5.0})
        assert any("negativa" in e for e in errors)

    def test_fecha_futura(self):
        from datetime import timedelta
        future = (date.today() + timedelta(days=1)).isoformat()
        errors = validar_registro({"fecha": future})
        assert any("futuras" in e.lower() for e in errors)

    def test_municipio_con_digitos(self):
        errors = validar_registro({"municipio": "Madrid123"})
        assert any("dígitos" in e for e in errors)

    def test_municipio_limpio(self):
        errors = validar_registro({"municipio": "Madrid"})
        assert len(errors) == 0