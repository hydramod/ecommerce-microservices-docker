
from fastapi import APIRouter, Depends, HTTPException
from typing import List
from pydantic import BaseModel
from redis import Redis
import httpx

from sqlalchemy.orm import Session
from app.db.session import SessionLocal
from app.db import models
from app.core.config import settings
from app.kafka.producer import send
import jwt, json

router = APIRouter()

def get_db():
    db = SessionLocal()
    try: yield db
    finally: db.close()

def get_identity(auth: str | None = None) -> dict:
    # FastAPI simpler approach: expect 'Authorization' header automatically?
    # We'll accept it as dependency parameter (set in route signature).
    if not auth or not auth.lower().startswith("bearer "):
        raise HTTPException(status_code=401, detail="Not authenticated")
    token = auth.split(" ", 1)[1]
    try:
        payload = jwt.decode(token, settings.JWT_SECRET, algorithms=[settings.JWT_ALGORITHM])
    except Exception:
        raise HTTPException(status_code=401, detail="Invalid token")
    if payload.get("type") != "access":
        raise HTTPException(status_code=401, detail="Invalid access token")
    return payload

def redis_client() -> Redis:
    return Redis.from_url(settings.REDIS_URL, decode_responses=True)

class CheckoutResponse(BaseModel):
    order_id: int
    status: str
    total_cents: int
    currency: str

@router.post("/v1/orders/checkout", response_model=CheckoutResponse)
def checkout(authorization: str | None = None, db: Session = Depends(get_db)):
    identity = get_identity(authorization)
    email = identity.get("sub")
    # Read cart from Redis
    r = redis_client()
    key = f"cart:{email}"
    raw = r.hgetall(key)  # {product_id: item_json}
    if not raw:
        raise HTTPException(status_code=400, detail="Cart is empty")

    items = []
    total = 0
    for _, v in raw.items():
        it = json.loads(v)
        items.append(it)
        total += int(it["qty"]) * int(it["unit_price_cents"])

    # Reserve inventory via Catalog internal API
    reserve_req = {"items": [{"product_id": it["product_id"], "qty": it["qty"]} for it in items]}
    try:
        with httpx.Client(timeout=5.0) as client:
            resp = client.post(f"{settings.CATALOG_BASE}/v1/inventory/reserve", json=reserve_req, headers={"X-Internal-Key": settings.INTERNAL_KEY})
            if resp.status_code != 200:
                raise HTTPException(status_code=resp.status_code, detail=resp.text)
    except httpx.RequestError:
        raise HTTPException(status_code=503, detail="Catalog unavailable")

    # Create order in DB
    order = models.Order(user_email=email, status="CREATED", total_cents=total, currency="USD")
    db.add(order); db.commit(); db.refresh(order)
    for it in items:
        oi = models.OrderItem(order_id=order.id, product_id=it["product_id"], qty=it["qty"], unit_price_cents=it["unit_price_cents"], title_snapshot=it["title"])
        db.add(oi)
    db.commit()

    # Emit event
    send(
        topic="order.events",
        key=str(order.id),
        value={
            "type": "order.created",
            "order_id": order.id,
            "user_email": email,
            "amount_cents": total,
            "items": [{"product_id": it["product_id"], "qty": it["qty"], "unit_price_cents": it["unit_price_cents"]} for it in items],
        },
    )

    return CheckoutResponse(order_id=order.id, status=order.status, total_cents=order.total_cents, currency=order.currency)


from sqlalchemy import select

@router.get("/v1/orders/{order_id}")
def get_order(order_id: int, db: Session = Depends(get_db)):
    obj = db.get(models.Order, order_id)
    if not obj:
        raise HTTPException(status_code=404, detail="Order not found")
    return {
        "id": obj.id,
        "status": obj.status,
        "total_cents": obj.total_cents,
        "currency": obj.currency,
        "items": [{"product_id": it.product_id, "qty": it.qty, "unit_price_cents": it.unit_price_cents} for it in obj.items],
    }
