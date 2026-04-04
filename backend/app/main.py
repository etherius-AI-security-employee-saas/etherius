from pathlib import Path

from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, RedirectResponse

from app.api import agent, auth, dashboard, licenses, response
from app.config import settings
from app.security.licenses import ensure_default_subscription_key

API_DOCS_ENABLED = settings.ENABLE_API_DOCS and settings.ENV == "development"
ALLOWED_ORIGINS = [origin.strip() for origin in settings.CORS_ORIGINS.split(",") if origin.strip()]

app = FastAPI(
    title="Etherius",
    description="Enterprise AI Cybersecurity Platform",
    version="1.0.0",
    docs_url="/docs" if API_DOCS_ENABLED else None,
    redoc_url="/redoc" if API_DOCS_ENABLED else None,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS,
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


def _resolve_dashboard_asset(path: str) -> Path | None:
    if not path:
        return None
    candidate = (dashboard_dist / path).resolve()
    if dashboard_dist.resolve() not in candidate.parents:
        return None
    if candidate.is_file():
        return candidate
    return None


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
    if API_DOCS_ENABLED:
        return RedirectResponse(url="/docs")
    return RedirectResponse(url="/health")


@app.get("/dashboard", include_in_schema=False)
@app.get("/dashboard/{path:path}", include_in_schema=False)
def serve_dashboard(path: str = ""):
    if not dashboard_dist.exists():
        if API_DOCS_ENABLED:
            return RedirectResponse(url="/docs")
        return RedirectResponse(url="/health")
    asset = _resolve_dashboard_asset(path)
    if asset:
        return FileResponse(asset)
    return FileResponse(dashboard_dist / "index.html")


@app.get("/assets/{path:path}", include_in_schema=False)
def serve_dashboard_assets_compat(path: str):
    if not dashboard_dist.exists():
        raise HTTPException(status_code=404, detail="Dashboard assets are not available")
    asset = _resolve_dashboard_asset(f"assets/{path}")
    if asset:
        return FileResponse(asset)
    raise HTTPException(status_code=404, detail="Asset not found")


@app.get("/etherius-logo.jpeg", include_in_schema=False)
def serve_dashboard_logo_compat():
    logo = dashboard_dist / "etherius-logo.jpeg"
    if logo.exists():
        return FileResponse(logo)
    raise HTTPException(status_code=404, detail="Logo not found")


@app.get("/login", include_in_schema=False)
@app.get("/alerts", include_in_schema=False)
@app.get("/endpoints", include_in_schema=False)
@app.get("/incidents", include_in_schema=False)
@app.get("/blocked", include_in_schema=False)
@app.get("/audit", include_in_schema=False)
@app.get("/settings", include_in_schema=False)
def serve_dashboard_legacy_routes():
    if not dashboard_dist.exists():
        if API_DOCS_ENABLED:
            return RedirectResponse(url="/docs")
        return RedirectResponse(url="/health")
    return FileResponse(dashboard_dist / "index.html")


@app.on_event("startup")
def startup():
    from app.database import SessionLocal, init_db
    from app.utils.demo_seed import bootstrap_demo_environment

    try:
        if settings.ENV != "development":
            if (
                "change_in_production" in settings.SECRET_KEY
                or "change_in_production" in settings.AGENT_SECRET_KEY
                or "CHANGE_THIS_CEO_MASTER_KEY" in settings.CEO_MASTER_KEY
            ):
                raise RuntimeError("Production secret keys are not configured securely.")
        init_db()
        print("[Etherius] Database ready")
    except Exception as e:
        print(f"[Etherius] DB init failed: {e}")
    if settings.ENV == "development" and settings.ENABLE_DEMO_SEED:
        db = SessionLocal()
        try:
            default_key = ensure_default_subscription_key(db)
            print(f"[Etherius] Demo subscription key ready: {default_key}")
            bootstrap_demo_environment(
                db,
                company_name=settings.DEMO_COMPANY_NAME,
                admin_email=settings.DEMO_ADMIN_EMAIL,
                admin_password=settings.DEMO_ADMIN_PASSWORD,
                subscription_key=default_key,
            )
            print(f"[Etherius] Demo admin ready: {settings.DEMO_ADMIN_EMAIL}")
        finally:
            db.close()
    print(f"[Etherius] Backend running | ENV={settings.ENV}")
    if API_DOCS_ENABLED:
        print("[Etherius] API docs at http://localhost:8000/docs")
