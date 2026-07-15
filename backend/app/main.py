import os

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.router import api_router
from app.core.exceptions import register_exception_handlers
from app.core.logging import configure_logging

ALLOWED_ORIGINS = [
    "http://localhost:5173",
    "http://127.0.0.1:5173",
]

# 生产环境额外允许的来源（通过环境变量配置）
_extra_origins = os.getenv("CORS_EXTRA_ORIGINS", "").strip()
if _extra_origins:
    ALLOWED_ORIGINS.extend(origin.strip() for origin in _extra_origins.split(",") if origin.strip())


def create_app() -> FastAPI:
    configure_logging()

    app = FastAPI(
        title="AI Interview API",
        version="0.1.0",
    )
    app.add_middleware(
        CORSMiddleware,
        allow_origins=ALLOWED_ORIGINS,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    register_exception_handlers(app)
    app.include_router(api_router)

    return app


app = create_app()
