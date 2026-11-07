import pytest
from fastapi.testclient import TestClient

import orchestrator
from components.recommender import HistoryStore, recommend
from components.registry import invoke
from derivation import build_compose
from features import complete, derive, services_for, validate
from services import gateway
from services.recommender_app import create_app as create_recommender


# ---------- modelo de features ----------
def test_complete_adds_required_features():
    assert complete({"dead_code"}) == {"dead_code", "constant_folding", "semantic"}


def test_recommendation_is_extra_not_pipeline():
    features = ["codegen_c", "recommendation"]
    assert not validate(features)
    assert "recommendation" not in derive(features)
    assert services_for(features)[-1] == "recommender"
    assert "recommender" not in services_for(["codegen_c"])


def test_compose_has_only_product_services():
    compose = build_compose("seguro", ["semantic", "codegen_c"])
    assert "  codegen-c:" in compose and "  semantic:" in compose
    assert "codegen-vm" not in compose and "recommender" not in compose
    assert "- semantic" in compose  # depends_on


def test_compose_all_services():
    compose = build_compose("seguro", ["semantic", "codegen_c"], all_services=True)
    for host in ["lexer", "constant-folding", "dead-code", "codegen-vm", "recommender"]:
        assert f"  {host}:" in compose
    assert "./products:/app/products" in compose


def test_compose_with_recommendation_has_volume():
    compose = build_compose("p", ["codegen_python", "recommendation"])
    assert "  recommender:" in compose and "recommender-data:/data" in compose


# ---------- recomendação ----------
def test_cold_start_recommends_basic_product():
    r = recommend(HistoryStore(), "novo")
    assert r["features"] == ["codegen_python"]


def test_recommendation_uses_history_and_is_valid():
    store = HistoryStore()
    for _ in range(3):
        store.add("ana", ["semantic", "codegen_c"])
    r = recommend(store, "ana")
    assert "codegen_c" in r["features"] and "semantic" in r["features"]
    assert r["suggestion"] == "constant_folding"  # próximo passo natural
    assert not validate(r["features"])


def test_recommendation_uses_similar_users():
    store = HistoryStore()
    store.add("ana", ["semantic", "constant_folding", "dead_code", "codegen_vm"])
    store.add("bia", ["semantic", "codegen_vm"])
    r = recommend(store, "bia")
    assert r["suggestion"] == "constant_folding"
    assert "codegen_vm" in r["features"]
    assert not validate(r["features"])


def test_new_user_gets_popular_product():
    store = HistoryStore()
    for _ in range(3):
        store.add("ana", ["semantic", "constant_folding", "codegen_vm"])
    r = recommend(store, "novato")
    assert set(r["features"]) == {"semantic", "constant_folding", "codegen_vm"}


def test_recommender_service_endpoints():
    client = TestClient(create_recommender(HistoryStore()))
    assert client.get("/health").json()["service"] == "recommender"
    client.post("/history", json={"user": "ana", "features": ["codegen_c", "semantic"]})
    assert client.get("/history/ana").json()["history"] == [["codegen_c", "semantic"]]
    assert client.get("/recommend/ana").json()["features"]


# ---------- gateway ----------
@pytest.fixture
def client(monkeypatch, tmp_path):
    rec = TestClient(create_recommender(HistoryStore()))

    def fake_call_service(name, method, path, payload=None, timeout=10):
        if name != "recommender":
            raise ConnectionError("serviço fora do ar")
        r = rec.request(method, path, json=payload)
        r.raise_for_status()
        return r.json()

    monkeypatch.setattr(orchestrator, "call_remote", lambda name, data: invoke(name, data))
    monkeypatch.setattr(orchestrator, "call_service", fake_call_service)
    monkeypatch.setattr(gateway, "PRODUCTS_DIR", tmp_path)
    product = {"name": "otimizado", "features": ["semantic", "constant_folding", "codegen_vm"]}
    return TestClient(gateway.create_app(product))


def test_gateway_model_and_index(client):
    model = client.get("/api/model").json()
    assert model["backends"] and model["default"]["name"] == "otimizado"
    assert "LPS de Compiladores" in client.get("/").text


def test_gateway_validate(client):
    ok = client.post("/api/validate", json={"features": ["codegen_c"]}).json()
    assert ok["valid"] and ok["pipeline"] == ["lexer", "parser", "codegen_c"]
    bad = client.post("/api/validate", json={"features": ["dead_code", "codegen_c"]}).json()
    assert not bad["valid"] and bad["errors"]


def test_gateway_builds_new_product(client, tmp_path):
    r = client.post("/api/products", json={"name": "meu-produto", "features": ["codegen_c"]})
    assert r.status_code == 200
    assert (tmp_path / "meu-produto.json").exists()
    assert "  codegen-c:" in r.json()["compose"]
    assert client.post("/api/products", json={"name": "../x", "features": ["codegen_c"]}).status_code == 422
    assert client.post("/api/products", json={"name": "ok", "features": []}).status_code == 422


def test_gateway_compile_runs_vm_and_records_history(client):
    body = {"source": "print 2 + 3;", "features": ["semantic", "codegen_vm", "recommendation"], "user": "ana"}
    r = client.post("/compile", json=body).json()
    assert r["output"] == "5"
    assert r["pipeline"] == ["lexer", "parser", "semantic", "codegen_vm"]
    assert r["history"] == "registrado"
    rec = client.get("/api/recommend/ana").json()
    assert "codegen_vm" in rec["features"]


def test_gateway_compile_uses_default_product_and_reports_errors(client):
    ok = client.post("/compile", json={"source": "print 1;"}).json()
    assert ok["target"] == "vm"
    err = client.post("/compile", json={"source": "print x;"}).json()
    assert err["errors"] and "output" not in err
    assert client.post("/compile", json={"source": "print 1;", "features": []}).status_code == 422


def test_gateway_vm_infinite_loop_is_bounded(client):
    r = client.post("/compile", json={"source": "while 1 { }", "features": ["codegen_vm"]}).json()
    assert "limite de passos" in r["output"]


def test_gateway_status_lists_all_services(client):
    rows = client.get("/api/status").json()
    assert len(rows) == 9
    assert {row["name"]: row["up"] for row in rows}["recommender"] is True
    assert {row["name"]: row["up"] for row in rows}["lexer"] is False
