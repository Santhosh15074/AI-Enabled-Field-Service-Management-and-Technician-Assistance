import logging
import threading
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI, Request
from fastapi.responses import FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from starlette.middleware.sessions import SessionMiddleware

from app.config import get_settings
from app.database import SessionLocal
from app.deps import Forbidden, NotAuthenticated
from app.voice.processing import resume_unfinished
from app.routes import analytics, auth, equipment, knowledge_base, notifications, overview, platform, service_reports, service_requests, shops, users, voice_notes

logger = logging.getLogger(__name__)

ROOT = Path(__file__).resolve().parent.parent
# The built React apps (npm run build in each folder). In development Vite serves them instead.
FRONTEND_DIST = ROOT / "frontend" / "dist"
# The config portal for Sollu operators, served under /config (its Vite base) — see app.routes.platform.
CONFIG_PORTAL_DIST = ROOT / "config-portal" / "dist"


@asynccontextmanager
async def _lifespan(_app: FastAPI):
    if get_settings().resume_voice_notes_on_startup:
        # On its own thread: transcribing can take minutes and mustn't hold up startup.
        threading.Thread(target=resume_unfinished, args=(SessionLocal,), daemon=True, name="voice-notes-resume").start()
    yield


def create_app() -> FastAPI:
    settings = get_settings()
    if settings.secret_key == "change-me":
        logger.warning("SECRET_KEY is the default value. Set a random one in .env.")

    app = FastAPI(title="AI-Enabled Field Service Management", docs_url="/api/docs", redoc_url=None, lifespan=_lifespan)

    @app.middleware("http")
    async def no_cache_api(request: Request, call_next):
        # Account data must never be served from the browser cache, e.g. after logout.
        response = await call_next(request)
        if request.url.path.startswith("/api/"):
            response.headers["Cache-Control"] = "no-store"
        return response

    # Added after the no-cache middleware so it runs first and the session is ready for every route.
    app.add_middleware(
        SessionMiddleware,
        secret_key=settings.secret_key,
        session_cookie="fsm_session",
        max_age=settings.session_max_age_seconds,
        same_site="lax",
        https_only=settings.session_https_only,
    )

    @app.exception_handler(NotAuthenticated)
    async def not_authenticated(_request: Request, _exc: NotAuthenticated):
        return JSONResponse({"detail": "Not logged in."}, status_code=401)

    @app.exception_handler(Forbidden)
    async def forbidden(_request: Request, _exc: Forbidden):
        return JSONResponse({"detail": "Your account doesn't have access to this."}, status_code=403)

    app.include_router(auth.router)
    app.include_router(shops.router)
    app.include_router(overview.router)
    app.include_router(analytics.router)
    app.include_router(equipment.router)
    app.include_router(service_requests.router)
    app.include_router(service_reports.router)
    app.include_router(users.router)
    app.include_router(knowledge_base.router)
    app.include_router(notifications.router)
    app.include_router(platform.router)
    app.include_router(voice_notes.router)

    # The config portal first: the shop app's catch-all below would otherwise claim /config too.
    if CONFIG_PORTAL_DIST.is_dir():
        _serve_config_portal(app)
    if FRONTEND_DIST.is_dir():
        _serve_frontend(app)
    return app


def _spa_response(dist: Path, path: str):
    file = (dist / path).resolve()
    if path and file.is_file() and file.is_relative_to(dist):
        return FileResponse(file)
    if "." in path.rsplit("/", 1)[-1]:
        # A missing file such as /favicon.ico, not a page.
        return JSONResponse({"detail": "Not found."}, status_code=404)
    # Every other path is a React route, e.g. /admin; the React router decides what to show.
    return FileResponse(dist / "index.html", headers={"Cache-Control": "no-cache"})


def _serve_config_portal(app: FastAPI) -> None:
    @app.get("/config", include_in_schema=False)
    @app.get("/config/{path:path}", include_in_schema=False)
    async def config_portal(path: str = ""):
        return _spa_response(CONFIG_PORTAL_DIST, path)


def _serve_frontend(app: FastAPI) -> None:
    app.mount("/assets", StaticFiles(directory=FRONTEND_DIST / "assets"), name="assets")

    @app.get("/{path:path}", include_in_schema=False)
    async def spa(path: str):
        if path.startswith("api/"):
            return JSONResponse({"detail": "Not found."}, status_code=404)
        return _spa_response(FRONTEND_DIST, path)


app = create_app()
