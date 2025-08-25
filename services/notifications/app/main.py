from fastapi import FastAPI
from app.api.routes import router
from app.kafka import consumer

app = FastAPI(title="Notifications Service")

@app.on_event("startup")
async def startup():
    consumer.start()

@app.on_event("shutdown")
async def shutdown():
    consumer.stop()

@app.get("/health")
def health():
    return {"status": "ok"}

@app.get('/notifications/health')
def auth_health(): return {'status':'ok'}


# Debug: Print all routes on startup
@app.on_event("startup")
async def startup_event():
    for route in app.routes:
        if hasattr(route, "methods") and hasattr(route, "path"):
            print(f"{route.methods} {route.path}")

app.include_router(router)
