from fastapi import FastAPI
from app.version import VERSION

app = FastAPI(title="Notifications Service", version=VERSION)

@app.get("/health")
def health():
    return {"status": "ok"}

@app.get("/v1/_info")
def info():
    return {"service": "notifications", "version": VERSION}
