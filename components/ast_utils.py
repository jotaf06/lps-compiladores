"""Utilitários compartilhados pelos componentes.

A AST é feita de dicts JSON-serializáveis ({"t": tipo, ...}) para poder
trafegar entre microservices. Cada fase trata os nós por tabelas de dispatch
(tipo -> função); para adicionar um nó novo (ex.: função) basta registrar
um handler em cada tabela.
"""
from .errors import CompileError

# Operadores binários -> mnemônico da VM
OPNAMES = {
    "+": "ADD", "-": "SUB", "*": "MUL", "/": "DIV", "%": "MOD",
    "==": "EQ", "!=": "NE", "<": "LT", ">": "GT", "<=": "LE", ">=": "GE",
}


def dispatch(table, node, *args):
    handler = table.get(node["t"])
    if handler is None:
        raise CompileError(f"nó não suportado: {node['t']!r}")
    return handler(node, *args)


def walk(node):
    """Percorre todos os nós (dicts) da árvore, em profundidade."""
    if isinstance(node, dict):
        yield node
        for value in node.values():
            yield from walk(value)
    elif isinstance(node, list):
        for item in node:
            yield from walk(item)


def collect_lets(ast):
    """Nomes declarados com `let`, sem repetição, na ordem de aparição."""
    names = []
    for node in walk(ast):
        if node.get("t") == "let" and node["n"] not in names:
            names.append(node["n"])
    return names


def apply_op(op, a, b):
    """Semântica única da linguagem (divisão trunca em direção a zero, como em C)."""
    if op == "+":
        return a + b
    if op == "-":
        return a - b
    if op == "*":
        return a * b
    if op == "/":
        if b == 0:
            raise ZeroDivisionError("divisão por zero")
        q = abs(a) // abs(b)
        return q if (a < 0) == (b < 0) else -q
    if op == "%":
        return a - apply_op("/", a, b) * b
    if op == "==":
        return int(a == b)
    if op == "!=":
        return int(a != b)
    if op == "<":
        return int(a < b)
    if op == ">":
        return int(a > b)
    if op == "<=":
        return int(a <= b)
    if op == ">=":
        return int(a >= b)
    raise CompileError(f"operador desconhecido: {op}")
