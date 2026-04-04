from pathlib import Path

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import RedirectResponse
from fastapi.staticfiles import StaticFiles

from app.api import agent, auth, dashboard, licenses, response
from app.config import settings
from app.security.licenses import ensure_default_subscription_key

app = FastAPI(
    title="Etherius",
    description="Enterprise AI Cybersecurity Platform",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://localhost:3000", "http://localhost:4173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.middleware("http")
async def apply_security_headers(request: Request, call_next):
    response = await call_next(request)
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-Frame-Options"] = "DENY"
    response.headers["Referrer-Policy"] = "no-referrer"
    response.headers["Permissions-Policy"] = "camera=(), microphone=(), geolocation=()"
    response.headers["Content-Security-Policy"] = "default-src 'self'; frame-ancestors 'none'; object-src 'none'"
    if request.url.scheme == "https":
        response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"
    return response

app.include_router(auth.router)
app.include_router(agent.router)
app.include_router(dashboard.router)
app.include_router(licenses.router)
app.include_router(response.router)

workspace_root = Path(__file__).resolve().parents[2]
dashboard_dist = workspace_root / "dashboard" / "dist"
if dashboard_dist.exists():
    app.mount("/dashboard", StaticFiles(directory=str(dashboard_dist), html=True), name="dashboard")


@app.get("/health", tags=["Health"])
def health():
    from app.database import check_db

    db_ok = check_db()
    return {
        "status": "ok",
        "service": settings.APP_NAME,
        "env": settings.ENV,
        "database": "connected" if db_ok else "disconnected",
    }


@app.get("/", include_in_schema=False)
def root():
    if dashboard_dist.exists():
        return RedirectResponse(url="/dashboard")
    return RedirectResponse(url="/docs")


@app.on_event("startup")
def startup():
    from app.database import SessionLocal, init_db
    from app.utils.demo_seed import bootstrap_demo_environment

    try:
        if settings.ENV != "development":
            if "change_in_production" in settings.SECRET_KEY or "change_in_production" in settings.AGENT_SECRET_KEY:
                raise RuntimeError("Production secret keys are not configured securely.")
        init_db()
        print("[Etherius] Database ready")
    except Exception as e:
        print(f"[Etherius] DB init failed: {e}")
    if settings.ENV == "development":
        db = SessionLocal()
        try:
            default_key = ensure_default_subscription_key(db)
            print(f"[Etherius] Demo subscription key ready: {default_key}")
            bootstrap_demo_environment(
                db,
                company_name=settings.DEMO_COMPANY_NAME,
                admin_email=settings.DEMO_ADMIN_EMAIL,
                admin_password=settings.DEMO_ADMIN_PASSWORD,
            )
            print(f"[Etherius] Demo admin ready: {settings.DEMO_ADMIN_EMAIL}")
        finally:
            db.close()
    print(f"[Etherius] Backend running | ENV={settings.ENV}")
    print("[Etherius] API docs at http://localhost:8000/docs")
