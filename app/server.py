from fastapi import FastAPI
from app.routes.predict_routes import router as predict_router
from app.docs.swagger_config import custom_openapi
def create_app() -> FastAPI:
    app = FastAPI(
        title="Plant Identifier API",
        version="2.0.0",
        docs_url="/docs",
        redoc_url="/redoc"
    )

    app.include_router(predict_router)
    app.openapi = lambda: custom_openapi(app)

    return app