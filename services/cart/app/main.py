from fastapi import FastAPI
from app.version import VERSION
from app.api import routes as cart_routes

app = FastAPI(title="Cart Service", version=VERSION)

@app.get("/health")
def health():
    return {"status": "ok"}

@app.get('/cart/health')
def auth_health(): return {'status':'ok'}

@app.get("/v1/_info")
def info():
    return {"service": "cart", "version": VERSION}

# Add to main.py
@app.on_event("startup")
async def startup_event():
    for route in app.routes:
        if hasattr(route, "methods") and hasattr(route, "path"):
            print(f"{route.methods} {route.path}")

app.include_router(cart_routes.router, prefix='/cart', tags=['cart'])
