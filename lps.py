"""CLI da LPS de compiladores.

    python lps.py new meu-produto semantic codegen_c
    python lps.py validate products/otimizado.json
    python lps.py compile products/otimizado.json examples/exemplo.src [--remote] [--run]
    python lps.py compose products/otimizado.json > docker-compose.yml
"""
import argparse
import json
import sys

from components.runner import run_code
from derivation import build_compose, save_product
from features import derive, validate
from orchestrator import compile_source


def load_product(path):
    with open(path) as f:
        return json.load(f)


def cmd_new(args):
    errors = validate(args.features)
    if errors:
        print("configuração inválida:", *errors, sep="\n - ", file=sys.stderr)
        return 1
    path = save_product(args.name, args.features)
    print(f"produto salvo em {path}. pipeline: {' -> '.join(derive(args.features))}")
    return 0


def cmd_validate(args):
    product = load_product(args.product)
    errors = validate(product["features"])
    if errors:
        print("configuração inválida:")
        for e in errors:
            print(" -", e)
        return 1
    print(f"produto '{product['name']}' válido. pipeline: {' -> '.join(derive(product['features']))}")
    return 0


def cmd_compile(args):
    product = load_product(args.product)
    with open(args.source) as f:
        source = f.read()
    result = compile_source(source, product["features"], remote=args.remote)
    if result.get("errors"):
        print("erro de compilação:", *result["errors"], sep="\n  ", file=sys.stderr)
        return 1
    print(result["code"])
    if args.run:
        print("--- saída da execução ---")
        print(run_code(result["target"], result["code"]), end="")
    return 0


def cmd_compose(args):
    product = load_product(args.product)
    print(build_compose(product["name"], product["features"], all_services=args.all), end="")
    return 0


def main():
    p = argparse.ArgumentParser(description="LPS de compiladores")
    sub = p.add_subparsers(dest="cmd", required=True)

    n = sub.add_parser("new", help="cria products/<nome>.json a partir de uma lista de features")
    n.add_argument("name")
    n.add_argument("features", nargs="+")
    n.set_defaults(fn=cmd_new)

    v = sub.add_parser("validate", help="valida o produto contra o modelo de features")
    v.add_argument("product")
    v.set_defaults(fn=cmd_validate)

    c = sub.add_parser("compile", help="compila um programa-fonte com o produto")
    c.add_argument("product")
    c.add_argument("source")
    c.add_argument("--remote", action="store_true", help="usa os microservices via HTTP")
    c.add_argument("--run", action="store_true", help="executa o código gerado (python/vm)")
    c.set_defaults(fn=cmd_compile)

    d = sub.add_parser("compose", help="gera docker-compose.yml só com os serviços do produto")
    d.add_argument("product")
    d.add_argument("--all", action="store_true", help="sobe todos os serviços, não só os do produto")
    d.set_defaults(fn=cmd_compose)

    args = p.parse_args()
    sys.exit(args.fn(args))


if __name__ == "__main__":
    main()
