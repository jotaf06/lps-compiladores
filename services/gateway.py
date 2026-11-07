"""API Gateway da LPS: tela de configuração, derivação de produtos e compilação.

Uso: python -m services.gateway products/otimizado.json [porta]

O gateway é o único ponto de entrada do cliente. Ele valida a configuração contra o
modelo de features, aciona os microservices do pipeline (modo remoto), registra o
histórico no `recommender` e repassa as recomendações. Documentação interativa da API
em /docs.
"""
import json
import re
import sys
from pathlib import Path
from urllib.parse import quote

import httpx
import uvicorn
from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse
from pydantic import BaseModel

import orchestrator
from components import vm
from derivation import build_compose, save_product
from features import SERVICES, derive, model, port_for, services_for, validate

ROOT = Path(__file__).resolve().parent.parent
STATIC = Path(__file__).resolve().parent / "static"
PRODUCTS_DIR = ROOT / "products"
VM_MAX_STEPS = 100_000  # evita laço infinito na execução de demonstração
NAME_RE = re.compile(r"^[a-z0-9_-]{1,40}$")


class FeatureSet(BaseModel):
    """Seleção de features."""

    features: list[str]


class NewProduct(BaseModel):
    """Novo produto: nome (letras minúsculas, números, - e _) e features."""

    name: str
    features: list[str]


class CompileRequest(BaseModel):
    """Compilação: código-fonte, features (padrão: as do produto do gateway) e usuário."""

    source: str
    features: list[str] | None = None
    user: str | None = None


def _bad_request(errors):
    raise HTTPException(status_code=422, detail=errors)


def _run_vm(code):
    try:
        return "\n".join(vm.execute(code, max_steps=VM_MAX_STEPS))
    except (ZeroDivisionError, KeyError, RuntimeError) as e:
        return f"erro de execução: {e!r}"


def create_app(product):
    app = FastAPI(
        title=f"lps-gateway-{product['name']}",
        description="API Gateway da LPS de compiladores (Client > Gateway > Services).",
    )

    @app.get("/", include_in_schema=False)
    def index():
        return FileResponse(STATIC / "index.html")

    @app.get("/health", tags=["gateway"])
    def health():
        """Produto padrão do gateway e seu pipeline."""
        return {"product": product["name"], "pipeline": derive(product["features"])}

    @app.get("/api/model", tags=["configuração"])
    def get_model():
        """Modelo de features, restrições, portas, produtos salvos e produto padrão."""
        products = [json.loads(p.read_text()) for p in sorted(PRODUCTS_DIR.glob("*.json"))]
        return {**model(), "default": product, "products": products}

    @app.post("/api/validate", tags=["configuração"])
    def validate_features(body: FeatureSet):
        """Valida a seleção de features e devolve pipeline e serviços necessários."""
        errors = validate(body.features)
        if errors:
            return {"valid": False, "errors": errors, "pipeline": [], "services": []}
        return {
            "valid": True,
            "errors": [],
            "pipeline": derive(body.features),
            "services": [{"name": s, "port": port_for(s)} for s in services_for(body.features)],
        }

    @app.post("/api/products", tags=["configuração"])
    def new_product(body: NewProduct):
        """Constrói um novo produto: grava products/<nome>.json e gera o docker-compose."""
        if not NAME_RE.match(body.name):
            _bad_request(["nome inválido: use letras minúsculas, números, - e _"])
        errors = validate(body.features)
        if errors:
            _bad_request(errors)
        path = save_product(body.name, body.features, PRODUCTS_DIR)
        return {
            "name": body.name,
            "file": f"products/{path.name}",
            "pipeline": derive(body.features),
            "compose": build_compose(body.name, body.features),
        }

    @app.post("/compile", tags=["compilação"])
    def compile_(req: CompileRequest):
        """Compila o código-fonte com o produto escolhido, acionando os microservices.

        Devolve o resultado do pipeline, a lista de serviços acionados (`pipeline`) e,
        para o alvo vm, a saída da execução (`output`). Se a feature `recommendation`
        estiver selecionada e `user` informado, a compilação entra no histórico do usuário.
        """
        features = req.features if req.features is not None else product["features"]
        errors = validate(features)
        if errors:
            _bad_request(errors)

        trace = []
        try:
            result = orchestrator.compile_source(req.source, features, remote=True, trace=trace)
        except httpx.HTTPError as e:
            raise HTTPException(status_code=502, detail=[f"microservice indisponível: {e}"])

        result["pipeline"] = trace
        if not result.get("errors"):
            if result.get("target") == "vm":
                result["output"] = _run_vm(result["code"])
            if "recommendation" in features and req.user:
                try:
                    orchestrator.call_service(
                        "recommender", "POST", "/history", {"user": req.user, "features": features}
                    )
                    result["history"] = "registrado"
                except Exception:
                    result["history"] = "recommender indisponível"
        return result

    @app.get("/api/recommend/{user}", tags=["recomendação"])
    def recommend(user: str):
        """Produto recomendado para o usuário (consulta o microservice recommender)."""
        try:
            return orchestrator.call_service("recommender", "GET", f"/recommend/{quote(user)}")
        except httpx.HTTPError as e:
            raise HTTPException(status_code=503, detail=[f"recommender indisponível: {e}"])

    @app.get("/api/status", tags=["gateway"])
    def status():
        """Estado e porta de cada microservice."""
        rows = []
        for name in SERVICES:
            try:
                orchestrator.call_service(name, "GET", "/health", timeout=1)
                up = True
            except Exception:
                up = False
            rows.append({"name": name, "port": port_for(name), "up": up})
        return rows

    return app


def main():
    if len(sys.argv) < 2:
        sys.exit("uso: python -m services.gateway <produto.json> [porta]")
    with open(sys.argv[1]) as f:
        product = json.load(f)
    port = int(sys.argv[2]) if len(sys.argv) > 2 else 8000
    uvicorn.run(create_app(product), host="0.0.0.0", port=port)


if __name__ == "__main__":
    main()
