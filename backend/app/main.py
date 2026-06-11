from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.core.config import get_settings
from app.core.database import init_db
from app.api import (
    auth_router, services_router, customers_router,
    staff_router, orders_router, ai_router, stats_router,
)

settings = get_settings()


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    await init_db()
    yield
    # Shutdown


app = FastAPI(
    title="智家管家AI API",
    version=settings.APP_VERSION,
    lifespan=lifespan,
)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Routers
app.include_router(auth_router, prefix="/api/v1")
app.include_router(services_router, prefix="/api/v1")
app.include_router(customers_router, prefix="/api/v1")
app.include_router(staff_router, prefix="/api/v1")
app.include_router(orders_router, prefix="/api/v1")
app.include_router(ai_router, prefix="/api/v1")
app.include_router(stats_router, prefix="/api/v1")


@app.get("/api/v1/health")
async def health_check():
    return {"status": "ok", "version": settings.APP_VERSION, "name": "智家管家AI"}


@app.get("/")
async def root():
    return {"name": "智家管家AI", "docs": "/docs"}
