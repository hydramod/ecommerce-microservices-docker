from fastapi import FastAPI
from app.version import VERSION
from app.api import products, categories
from app.api import inventory

app = FastAPI(title='Catalog Service', version=VERSION)

@app.get('/health')
def health(): return {'status':'ok'}

@app.get('/catalog/health')
def auth_health(): return {'status':'ok'}

@app.get('/v1/_info')
def info(): return {'service':'catalog','version':VERSION}

# Add to main.py
@app.on_event("startup")
async def startup_event():
    for route in app.routes:
        if hasattr(route, "methods") and hasattr(route, "path"):
            print(f"{route.methods} {route.path}")

app.include_router(categories.router, prefix='/catalog/v1/categories', tags=['categories'])
app.include_router(products.router,   prefix='/catalog/v1/products',   tags=['products'])
app.include_router(inventory.router,  prefix='/catalog', tags=['inventory'])
