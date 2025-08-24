
from fastapi import FastAPI
from app.version import VERSION
from app.api import routes

app = FastAPI(title="Order Service", version=VERSION)

@app.get("/health")
def health(): return {"status":"ok"}

@app.get('/order/health')
def auth_health(): return {'status':'ok'}

@app.get("/v1/_info")
def info(): return {"service":"order", "version": VERSION}

app.include_router(routes.router, tags=["orders"])


from fastapi import Request
from app.kafka import consumer as payment_consumer

@app.on_event("startup")
def _startup():
    payment_consumer.start()

@app.on_event("shutdown")
def _shutdown():
    payment_consumer.stop()
