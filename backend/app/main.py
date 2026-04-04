from urllib.parse import quote_plus

from fastapi import FastAPI, Header, HTTPException, Query, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.openapi.docs import get_swagger_ui_html
from fastapi.openapi.utils import get_openapi
from fastapi.responses import JSONResponse

from app.api import agent, auth, dashboard, licenses, response
from app.config import settings
from app.security.licenses import ensure_default_subscription_key

API_DOCS_ENABLED = settings.ENABLE_API_DOCS
ALLOWED_ORIGINS = [origin.strip() for origin in settings.CORS_ORIGINS.split(",") if origin.strip()]

app = FastAPI(
    title="Etherius",
    description="Enterprise AI Cybersecurity Platform",
    version="1.0.0",
    docs_url=None,
    redoc_url=None,
    openapi_url=None,
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


def _authorize_ceo(x_ceo_key: str = "", token: str = ""):
    expected = str(settings.CEO_MASTER_KEY or "").strip()
    provided = str(x_ceo_key or token or "").strip()
    if not expected or provided != expected:
        raise HTTPException(status_code=401, detail="CEO authorization required")


def _health_payload():
    from app.database import check_db

    db_ok = check_db()
    return {
        "status": "ok",
        "service": settings.APP_NAME,
        "env": settings.ENV,
        "database": "connected" if db_ok else "disconnected",
    }


def _schema():
    return get_openapi(
        title=app.title,
        version=app.version,
        description=app.description,
        routes=app.routes,
    )


app.include_router(auth.router)
app.include_router(agent.router)
app.include_router(dashboard.router)
app.include_router(licenses.router)
app.include_router(response.router)


@app.get("/", include_in_schema=False)
def root():
    return {
        "service": settings.APP_NAME,
        "message": "Private API surface. CEO authorization is required for health and API docs.",
    }


@app.get("/health", include_in_schema=False)
def health_private(
    x_ceo_key: str = Header(default=""),
    token: str = Query(default=""),
):
    _authorize_ceo(x_ceo_key=x_ceo_key, token=token)
    return _health_payload()


@app.get("/api/ceo/health", tags=["CEO"])
def ceo_health(
    x_ceo_key: str = Header(default=""),
    token: str = Query(default=""),
):
    _authorize_ceo(x_ceo_key=x_ceo_key, token=token)
    return _health_payload()


@app.get("/api/ceo/openapi.json", include_in_schema=False)
def ceo_openapi(
    x_ceo_key: str = Header(default=""),
    token: str = Query(default=""),
):
    if not API_DOCS_ENABLED:
        raise HTTPException(status_code=404, detail="CEO Swagger is disabled")
    _authorize_ceo(x_ceo_key=x_ceo_key, token=token)
    return JSONResponse(_schema())


@app.get("/api/ceo/swagger", include_in_schema=False)
def ceo_swagger(
    x_ceo_key: str = Header(default=""),
    token: str = Query(default=""),
):
    if not API_DOCS_ENABLED:
        raise HTTPException(status_code=404, detail="CEO Swagger is disabled")
    _authorize_ceo(x_ceo_key=x_ceo_key, token=token)
    effective_token = token or x_ceo_key
    encoded = quote_plus(effective_token)
    return get_swagger_ui_html(
        openapi_url=f"/api/ceo/openapi.json?token={encoded}",
        title="Etherius CEO Swagger",
    )


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
        print("[Etherius] CEO Swagger route: /api/ceo/swagger (CEO authorization required)")
