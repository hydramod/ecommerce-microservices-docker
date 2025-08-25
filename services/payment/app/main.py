from fastapi import FastAPI
from app.version import VERSION
from app.api import routes
from prometheus_fastapi_instrumentator import Instrumentator

app = FastAPI(title="Payment Service", version=VERSION)

@app.get("/health")
def health(): return {"status":"ok"}

@app.get('/payment/health')
def auth_health(): return {'status':'ok'}

@app.get("/v1/_info")
def info(): return {"service":"payment","version":VERSION}

@app.on_event("startup")
async def _startup():
    Instrumentator().instrument(app).expose(
        app,
        include_in_schema=False,
        endpoint=f"{SERVICE_PREFIX}/metrics",
        should_gzip=True,
    )

@app.on_event("startup")
async def startup_event():
    # Print all routes for debugging
    for route in app.routes:
        if hasattr(route, "methods") and hasattr(route, "path"):
            print(f"{route.methods} {route.path}")

app.include_router(routes.router, prefix='/payment', tags=["payments"])
