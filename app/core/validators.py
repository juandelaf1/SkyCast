def validar_registro(registro: dict) -> list[str]:
    errores = []
    temperatura = registro.get("temperatura")
    humedad = registro.get("humedad")
    viento = registro.get("viento")
    lluvia = registro.get("lluvia")
    fecha_str = registro.get("fecha")
    municipio = registro.get("municipio")

    if temperatura is not None:
        if temperatura < -20 or temperatura > 60:
            errores.append(f"Temperatura fuera de rango físico: {temperatura}°C (permitido: -20 a 60)")

    if humedad is not None:
        if humedad < 0 or humedad > 100:
            errores.append(f"Humedad fuera de rango: {humedad}% (permitido: 0-100)")

    if viento is not None:
        if viento < 0:
            errores.append(f"Viento no puede ser negativo: {viento} km/h")
        if viento > 150:
            errores.append(f"Viento fuera de rango físico: {viento} km/h (máximo: 150)")

    if lluvia is not None:
        if lluvia < 0:
            errores.append(f"Lluvia no puede ser negativa: {lluvia} mm")

    if fecha_str:
        from datetime import datetime
        try:
            fecha_dt = datetime.strptime(fecha_str, "%Y-%m-%d")
            from datetime import date
            if fecha_dt.date() > date.today():
                errores.append("No se permiten fechas futuras")
        except ValueError:
            errores.append(f"Formato de fecha inválido: {fecha_str}. Usar YYYY-MM-DD")

    if municipio:
        import re
        if re.search(r"\d", municipio):
            errores.append(f"Nombre de municipio no puede contener dígitos: {municipio}")

    return errores
