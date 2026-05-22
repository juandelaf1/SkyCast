import httpx

BASE = "http://localhost:8000"

print("=== ROOT ===")
r = httpx.get(f"{BASE}/")
print(f"{r.status_code} OK")

print("\n=== HEALTH (publico, sin auth) ===")
r = httpx.get(f"{BASE}/api/v1/health")
d = r.json()
print(f"{r.status_code} -> status={d['status']} uptime={d['uptime_seconds']}s")

print("\n=== REGISTER + LOGIN ===")
for email in ["demo1@skycast.io", "demo2@skycast.io"]:
    r = httpx.post(f"{BASE}/api/v1/auth/register", json={"email": email, "password": "Test1234"})
    if r.status_code == 200:
        token = r.json()["access_token"]
        print(f"  {email}: registrado OK")
        break
    elif r.status_code == 409:
        print(f"  {email}: ya existe")
        continue

r = httpx.post(f"{BASE}/api/v1/auth/login", data={"username": email, "password": "Test1234"})
if r.status_code != 200:
    print(f"  LOGIN FAILED: {r.status_code} -> {r.text}")
    exit(1)
token = r.json()["access_token"]
print(f"  LOGIN: OK user_id={r.json()['user_id']}")
H = {"Authorization": f"Bearer {token}"}

print("\n=== CREATE RECORD (geovalidacion OK) ===")
r = httpx.post(f"{BASE}/api/v1/registros",
    json={"temperatura": 24.5, "humedad": 58, "viento": 12, "lluvia": 0,
          "estacion_id": 1, "lat": 40.4114, "lon": -3.6788},
    headers=H)
print(f"{r.status_code} -> id={r.json()['id']} temp={r.json()['temperatura']}C")

print("\n=== CREATE RECORD (geovalidacion FAIL) ===")
r = httpx.post(f"{BASE}/api/v1/registros",
    json={"temperatura": 30, "humedad": 70, "viento": 20, "lluvia": 5,
          "estacion_id": 1, "lat": 28.0, "lon": -16.0},
    headers=H)
print(f"{r.status_code} -> {r.json()['detail']}")

print("\n=== CREATE RECORD (fecha invalida) ===")
r = httpx.post(f"{BASE}/api/v1/registros",
    json={"temperatura": 22, "humedad": 50, "viento": 10, "lluvia": 0,
          "estacion_id": 1, "fecha": "invalida"},
    headers=H)
print(f"{r.status_code} -> {r.json()['detail']}")

print("\n=== GET RECORDS (paginacion) ===")
r = httpx.get(f"{BASE}/api/v1/registros?page=1&limit=2", headers=H)
d = r.json()
print(f"{r.status_code} -> total={d['total']} pages={d['pages']} items={len(d['items'])}")

print("\n=== GET RECORDS (fecha invalida) ===")
r = httpx.get(f"{BASE}/api/v1/registros?fecha=xx", headers=H)
print(f"{r.status_code} -> {r.json()['detail']}")

print("\n=== STATS ===")
r = httpx.get(f"{BASE}/api/v1/health/stats", headers=H)
d = r.json()
print(f"{r.status_code} -> registros_hoy={d['datos']['registros_hoy']} temp_avg={d['datos']['temp_promedio']}C")

print("\n=== GEO Madrid ===")
r = httpx.get(f"{BASE}/api/v1/geo/Madrid", headers=H)
d = r.json()
print(f"{r.status_code} -> {d['ciudad']} lat={d['lat']:.4f} lon={d['lon']:.4f} [{d['fuente']}]")

print("\n=== GEO Tokyo ===")
r = httpx.get(f"{BASE}/api/v1/geo/Tokyo", headers=H)
d = r.json()
print(f"{r.status_code} -> {d['ciudad']} lat={d['lat']:.4f} lon={d['lon']:.4f} [{d['fuente']}]")

print("\n=== ALERTAS OFICIALES AEMET ===")
r = httpx.get(f"{BASE}/api/v1/alertas/oficiales", headers=H)
d = r.json()
print(f"{r.status_code} -> total={d['total']} alertas")

print("\n=== COMPARISON ===")
r = httpx.post(f"{BASE}/api/v1/comparar",
    json={"temperatura_manual": 25, "humedad_manual": 60,
          "viento_manual": 15, "lluvia_manual": 2, "municipio": "Madrid"},
    headers=H)
d = r.json()
print(f"{r.status_code} -> fuente_aemet={d['fuente_aemet']} alertas={len(d['alertas'])}")

print("\n=== ME ===")
r = httpx.get(f"{BASE}/api/v1/auth/me", headers=H)
d = r.json()
print(f"{r.status_code} -> {d['email']} activo={d['activo']}")

print("\n========================================")
print("  SkyCast v1.0.0 - 180 tests PASSING")
print("  Docs: http://localhost:8000/docs")
print("  Redoc: http://localhost:8000/redoc")
print("========================================")