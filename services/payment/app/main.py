
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

app.include_router(routes.router, tags=["payments"])
