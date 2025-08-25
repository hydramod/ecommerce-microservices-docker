
from fastapi import FastAPI
from app.version import VERSION
from app.api import routes

app = FastAPI(title="Payment Service", version=VERSION)

@app.get("/health")
def health(): return {"status":"ok"}

@app.get('/payment/health')
def auth_health(): return {'status':'ok'}

@app.get("/v1/_info")
def info(): return {"service":"payment","version":VERSION}

@app.on_event("startup")
async def startup_event():
    # Print all routes for debugging
    for route in app.routes:
        if hasattr(route, "methods") and hasattr(route, "path"):
            print(f"{route.methods} {route.path}")

app.include_router(routes.router, prefix='/payment', tags=["payments"])
