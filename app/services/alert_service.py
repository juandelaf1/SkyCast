from typing import Optional


class AlertService:
    ALERT_CONFIG = {
        "temperatura": [
            {"nivel": "rojo", "umbral": 40.0, "mensaje": "ALERTA ROJA: Calor extremo (>= 40C)", "icono": "🔥"},
            {"nivel": "naranja", "umbral": 35.0, "mensaje": "ALERTA NARANJA: Calor alto (>= 35C)", "icono": "🟠"},
            {"nivel": "amarillo", "umbral": 30.0, "mensaje": "AVISO AMARILLO: Calor moderado (>= 30C)", "icono": "🌡️"},
            {"nivel": "azul", "umbral": 0.0, "mensaje": "AVISO AZUL: Helada (<= 0C)", "icono": "❄️"},
        ],
        "viento": [
            {"nivel": "rojo", "umbral": 70.0, "mensaje": "ALERTA ROJA: Viento muy fuerte (>= 70 km/h)", "icono": "💨"},
            {"nivel": "naranja", "umbral": 50.0, "mensaje": "ALERTA NARANJA: Viento fuerte (>= 50 km/h)", "icono": "💨"},
        ],
        "lluvia": [
            {"nivel": "rojo", "umbral": 30.0, "mensaje": "ALERTA ROJA: Lluvia intensa (>= 30 mm)", "icono": "🌧️"},
            {"nivel": "naranja", "umbral": 15.0, "mensaje": "ALERTA NARANJA: Lluvia moderada (>= 15 mm)", "icono": "🌧️"},
        ],
        "humedad": [
            {"nivel": "rojo", "umbral": 90.0, "mensaje": "ALERTA ROJA: Humedad extrema (>= 90%)", "icono": "💧"},
            {"nivel": "naranja", "umbral": 80.0, "mensaje": "ALERTA NARANJA: Humedad alta (>= 80%)", "icono": "💧"},
        ],
    }

    def get_alertas_activas(self, data: dict) -> list[dict]:
        alertas = []
        temp = data.get("temperatura")
        viento = data.get("viento")
        lluvia = data.get("lluvia")
        humedad = data.get("humedad")

        if temp is not None:
            if temp >= 40:
                alertas.append({"variable": "temperatura", **self.ALERT_CONFIG["temperatura"][0]})
            elif temp >= 35:
                alertas.append({"variable": "temperatura", **self.ALERT_CONFIG["temperatura"][1]})
            elif temp >= 30:
                alertas.append({"variable": "temperatura", **self.ALERT_CONFIG["temperatura"][2]})
            elif temp <= 0:
                alertas.append({"variable": "temperatura", **self.ALERT_CONFIG["temperatura"][3]})

        if viento is not None and viento >= 70:
            alertas.append({"variable": "viento", **self.ALERT_CONFIG["viento"][0]})
        elif viento is not None and viento >= 50:
            alertas.append({"variable": "viento", **self.ALERT_CONFIG["viento"][1]})

        if lluvia is not None and lluvia >= 30:
            alertas.append({"variable": "lluvia", **self.ALERT_CONFIG["lluvia"][0]})
        elif lluvia is not None and lluvia >= 15:
            alertas.append({"variable": "lluvia", **self.ALERT_CONFIG["lluvia"][1]})

        if humedad is not None and humedad >= 90:
            alertas.append({"variable": "humedad", **self.ALERT_CONFIG["humedad"][0]})
        elif humedad is not None and humedad >= 80:
            alertas.append({"variable": "humedad", **self.ALERT_CONFIG["humedad"][1]})

        return alertas

    def get_nivel_maximo(self, data: dict) -> Optional[str]:
        alertas = self.get_alertas_activas(data)
        if not alertas:
            return "verde"

        nivel_orden = {"rojo": 4, "naranja": 3, "amarillo": 2, "azul": 1}
        niveles = [a["nivel"] for a in alertas]
        return max(niveles, key=lambda n: nivel_orden.get(n, 0))