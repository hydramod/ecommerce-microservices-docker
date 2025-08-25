from fastapi import FastAPI
from app.version import VERSION

app = FastAPI(title="Notifications Service", version=VERSION)

@app.get("/health")
def health():
    return {"status": "ok"}

@app.get("/v1/_info")
def info():
    return {"service": "notifications", "version": VERSION}

@app.on_event("startup")
async def startup_event():
    # Print all routes for debugging
    for route in app.routes:
        if hasattr(route, "methods") and hasattr(route, "path"):
            print(f"{route.methods} {route.path}")