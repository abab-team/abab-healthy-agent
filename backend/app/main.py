from fastapi import FastAPI

from app.api.router import api_router


def create_app() -> FastAPI:
    app = FastAPI(title="Family Health Agent")
    app.include_router(api_router)
    return app


app = create_app()
