"""Backend C: data["ast"] -> data["code"] (programa C).

Variáveis são declaradas todas no topo de main (escopo plano, como no Python).
"""
from .ast_utils import collect_lets, dispatch


def _bin(e):
    return f"({expr(e['l'])} {e['op']} {expr(e['r'])})"


EXPR = {
    "num": lambda e: str(e["v"]),
    "var": lambda e: "v_" + e["n"],
    "neg": lambda e: f"(-{expr(e['e'])})",
    "bin": _bin,
}


def expr(e):
    return dispatch(EXPR, e)


def _assign(s, d):
    return ["    " * d + f"v_{s['n']} = {expr(s['e'])};"]


def _print(s, d):
    return ["    " * d + f'printf("%ld\\n", (long)({expr(s["e"])}));']


def _while(s, d):
    return ["    " * d + f"while ({expr(s['c'])}) {{"] + block(s["body"], d + 1) + ["    " * d + "}"]


def _if(s, d):
    lines = ["    " * d + f"if ({expr(s['c'])}) {{"] + block(s["then"], d + 1)
    if s["else"]:
        lines += ["    " * d + "} else {"] + block(s["else"], d + 1)
    return lines + ["    " * d + "}"]


STMT = {"let": _assign, "assign": _assign, "print": _print, "while": _while, "if": _if}


def block(stmts, d):
    lines = []
    for s in stmts:
        lines += dispatch(STMT, s, d)
    return lines


def run(data):
    ast = data["ast"]
    lines = ["#include <stdio.h>", "", "int main(void) {"]
    names = collect_lets(ast)
    if names:
        lines.append("    long " + ", ".join(f"v_{n} = 0" for n in names) + ";")
    lines += block(ast["body"], 1)
    lines += ["    return 0;", "}"]
    return {"target": "c", "code": "\n".join(lines) + "\n"}
