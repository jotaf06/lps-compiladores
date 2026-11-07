"""Fábrica do microservice de um componente: POST /run e GET /health."""
from fastapi import Body, FastAPI

from components.registry import REGISTRY, invoke


def create_app(component):
    if component not in REGISTRY:
        raise ValueError(f"componente desconhecido: {component}")
    app = FastAPI(title=f"lps-{component}")

    @app.get("/health")
    def health():
        return {"service": component, "status": "ok"}

    @app.post("/run")
    def run(payload: dict = Body(...)):
        return invoke(component, payload)

    return app
