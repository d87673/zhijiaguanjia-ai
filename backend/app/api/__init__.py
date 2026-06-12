from app.api.auth import router as auth_router
from app.api.services import router as services_router
from app.api.customers import router as customers_router
from app.api.staff import router as staff_router
from app.api.orders import router as orders_router
from app.api.ai import router as ai_router
from app.api.stats import router as stats_router
from app.api.company import router as company_router
from app.api.payments import router as payments_router
from app.api.export import router as export_router
from app.api.h5 import router as h5_router
from app.api.staff_app import router as staff_app_router

__all__ = [
    "auth_router", "services_router", "customers_router",
    "staff_router", "orders_router", "ai_router", "stats_router",
    "company_router", "payments_router", "export_router", "h5_router",
    "staff_app_router",
]
