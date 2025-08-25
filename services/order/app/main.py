from fastapi import FastAPI
from app.version import VERSION
from app.api import routes
from app.kafka import consumer as payment_consumer

app = FastAPI(title="Order Service", version=VERSION)

# Health endpoints
@app.get("/health")
def health():
    return {"status": "ok"}

@app.get("/order/health")
def order_health():
    return {"status": "ok"}

@app.get("/v1/_info")
def info():
    return {"service": "order", "version": VERSION}

# Kafka event handlers
@app.on_event("startup")
async def startup_event():
    # Print all routes for debugging
    for route in app.routes:
        if hasattr(route, "methods") and hasattr(route, "path"):
            print(f"{route.methods} {route.path}")
    
    # Start Kafka consumer
    payment_consumer.start()

@app.on_event("shutdown")
async def shutdown_event():
    payment_consumer.stop()

# Include routers
app.include_router(routes.router, prefix='/order', tags=["orders"])