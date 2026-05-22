from app.main import app

for route in app.routes:
    methods = getattr(route, "methods", "")
    print(f"{methods} {route.path}")