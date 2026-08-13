from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from slowapi import _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded

from app.core.config import settings
from app.core.limiter import limiter
from app.routers import admin, auth, chat, contacts, faq, procedures, reports

app = FastAPI(title="Hòa Tiến AI Assistant API", version="1.0.0")
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth.router)
app.include_router(procedures.router)
app.include_router(faq.router)
app.include_router(contacts.router)
app.include_router(chat.router)
app.include_router(reports.router)
app.include_router(admin.router)


@app.get("/health")
def health():
    return {"status": "ok", "env": settings.env}


@app.exception_handler(Exception)
async def generic_exception_handler(request: Request, exc: Exception):
    # Không lộ stack trace ở production
    if settings.env == "production":
        return JSONResponse(status_code=500, content={"detail": "Đã có lỗi xảy ra, vui lòng thử lại."})
    raise exc
