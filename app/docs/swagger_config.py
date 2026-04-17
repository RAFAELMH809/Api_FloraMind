from fastapi.openapi.utils import get_openapi

def custom_openapi(app):
    if app.openapi_schema:
        return app.openapi_schema

    openapi_schema = get_openapi(
        title="FloraMind API",
        version="2.0.0",
        description="Floramind's Api for plant indentification",
        routes=app.routes,
    )

    app.openapi_schema = openapi_schema
    return app.openapi_schema