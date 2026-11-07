"""Backend Python: data["ast"] -> data["code"] (programa Python)."""
from .ast_utils import dispatch

PRELUDE = """def _div(a, b):
    q = abs(a) // abs(b)
    return q if (a < 0) == (b < 0) else -q


def _mod(a, b):
    return a - _div(a, b) * b


"""

COMPARISONS = {"==", "!=", "<", ">", "<=", ">="}


def _bin(e):
    l, r, op = expr(e["l"]), expr(e["r"]), e["op"]
    if op == "/":
        return f"_div({l}, {r})"
    if op == "%":
        return f"_mod({l}, {r})"
    if op in COMPARISONS:
        return f"int({l} {op} {r})"
    return f"({l} {op} {r})"


EXPR = {
    "num": lambda e: str(e["v"]),
    "var": lambda e: "v_" + e["n"],
    "neg": lambda e: f"(-{expr(e['e'])})",
    "bin": _bin,
}


def expr(e):
    return dispatch(EXPR, e)


def _assign(s, d):
    return ["    " * d + f"v_{s['n']} = {expr(s['e'])}"]


def _print(s, d):
    return ["    " * d + f"print({expr(s['e'])})"]


def _while(s, d):
    return ["    " * d + f"while {expr(s['c'])}:"] + block(s["body"], d + 1)


def _if(s, d):
    lines = ["    " * d + f"if {expr(s['c'])}:"] + block(s["then"], d + 1)
    if s["else"]:
        lines += ["    " * d + "else:"] + block(s["else"], d + 1)
    return lines


STMT = {"let": _assign, "assign": _assign, "print": _print, "while": _while, "if": _if}


def block(stmts, d):
    lines = []
    for s in stmts:
        lines += dispatch(STMT, s, d)
    return lines or ["    " * d + "pass"]


def run(data):
    code = PRELUDE + "\n".join(block(data["ast"]["body"], 0)) + "\n"
    return {"target": "python", "code": code}
