from fastapi import FastAPI
from app.version import VERSION

app = FastAPI(title="Shipping Service", version=VERSION)

@app.get("/health")
def health():
    return {"status": "ok"}

@app.get('/shipping/health')
def auth_health(): return {'status':'ok'}

@app.get("/v1/_info")
def info():
    return {"service": "shipping", "version": VERSION}
