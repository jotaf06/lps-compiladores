"""Componente Semântico: verifica variáveis declaradas e redeclaradas.

Usa uma pilha de escopos (um por bloco), já pronta para receber funções.
Não há shadowing: redeclarar um nome visível é erro.
"""
from .ast_utils import dispatch
from .errors import CompileError


def _visible(name, scopes):
    return any(name in s for s in scopes)


def _expr_var(e, scopes):
    if not _visible(e["n"], scopes):
        raise CompileError(f"variável não declarada: {e['n']}")


def _expr_bin(e, scopes):
    check_expr(e["l"], scopes)
    check_expr(e["r"], scopes)


EXPR = {
    "num": lambda e, s: None,
    "var": _expr_var,
    "neg": lambda e, s: check_expr(e["e"], s),
    "bin": _expr_bin,
}


def check_expr(e, scopes):
    dispatch(EXPR, e, scopes)


def _let(s, scopes):
    check_expr(s["e"], scopes)
    if _visible(s["n"], scopes):
        raise CompileError(f"variável já declarada: {s['n']}")
    scopes[-1].add(s["n"])


def _assign(s, scopes):
    if not _visible(s["n"], scopes):
        raise CompileError(f"atribuição a variável não declarada: {s['n']}")
    check_expr(s["e"], scopes)


def _print(s, scopes):
    check_expr(s["e"], scopes)


def _while(s, scopes):
    check_expr(s["c"], scopes)
    check_block(s["body"], scopes)


def _if(s, scopes):
    check_expr(s["c"], scopes)
    check_block(s["then"], scopes)
    check_block(s["else"], scopes)


STMT = {"let": _let, "assign": _assign, "print": _print, "while": _while, "if": _if}


def check_block(stmts, scopes):
    scopes.append(set())
    for s in stmts:
        dispatch(STMT, s, scopes)
    scopes.pop()


def run(data):
    check_block(data["ast"]["body"], [])
    return {}
