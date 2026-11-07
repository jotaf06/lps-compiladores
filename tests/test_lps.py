from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from components.runner import run_code
from features import derive, validate
from orchestrator import compile_source
from services.app import create_app

SOURCE = (Path(__file__).parent.parent / "examples" / "exemplo.src").read_text()
EXPECTED = "120\n100\n"


def test_derive_adds_mandatory_and_orders():
    assert derive(["codegen_python"]) == ["lexer", "parser", "codegen_python"]
    assert derive(["codegen_vm", "semantic"]) == ["lexer", "parser", "semantic", "codegen_vm"]


def test_validation_rules():
    assert validate([])  # sem backend
    assert validate(["codegen_c", "codegen_vm"])  # dois backends
    assert validate(["codegen_c", "dead_code"])  # dead_code exige constant_folding
    assert validate(["codegen_c", "constant_folding"])  # exige semantic
    assert validate(["codegen_c", "inexistente"])
    assert not validate(["semantic", "constant_folding", "dead_code", "codegen_c"])


def test_derive_rejects_invalid():
    with pytest.raises(ValueError):
        derive(["dead_code", "codegen_c"])


@pytest.mark.parametrize("features,target", [
    (["codegen_python"], "python"),
    (["semantic", "codegen_python"], "python"),
    (["codegen_vm"], "vm"),
    (["semantic", "constant_folding", "dead_code", "codegen_vm"], "vm"),
    (["semantic", "constant_folding", "dead_code", "codegen_python"], "python"),
])
def test_products_produce_same_output(features, target):
    result = compile_source(SOURCE, features)
    assert not result.get("errors")
    assert result["target"] == target
    assert run_code(target, result["code"]) == EXPECTED


def test_c_backend_generates_code():
    code = compile_source(SOURCE, ["codegen_c"])["code"]
    assert "int main(void)" in code and "printf" in code


def test_optimizers_shrink_code():
    plain = compile_source(SOURCE, ["semantic", "codegen_vm"])["code"]
    opt = compile_source(SOURCE, ["semantic", "constant_folding", "dead_code", "codegen_vm"])["code"]
    assert len(opt.splitlines()) < len(plain.splitlines())
    assert "999" not in opt


def test_semantic_detects_undeclared_variable():
    result = compile_source("print x;", ["semantic", "codegen_python"])
    assert "não declarada" in result["errors"][0]


def test_without_semantic_no_error_check():
    assert not compile_source("print x;", ["codegen_python"]).get("errors")


def test_syntax_and_lexical_errors():
    assert compile_source("let = 3;", ["codegen_python"])["errors"]
    assert compile_source("let a = 3 $;", ["codegen_python"])["errors"]


def test_division_semantics_truncate_like_c():
    src = "print -7 / 2; print -7 % 2;"
    expected = "-3\n-1\n"
    for backend, target in [("codegen_python", "python"), ("codegen_vm", "vm")]:
        code = compile_source(src, [backend])["code"]
        assert run_code(target, code) == expected


def test_microservice_endpoint():
    client = TestClient(create_app("lexer"))
    assert client.get("/health").json()["service"] == "lexer"
    body = client.post("/run", json={"source": "let a = 1;"}).json()
    assert body["tokens"][0] == ["KW", "let", 1]


def test_microservice_reports_errors():
    client = TestClient(create_app("lexer"))
    assert client.post("/run", json={"source": "$"}).json()["errors"]
