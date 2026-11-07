"""Otimização: avalia em tempo de compilação expressões com operandos constantes."""
from .ast_utils import apply_op, dispatch


def _bin(e):
    l, r = fold_expr(e["l"]), fold_expr(e["r"])
    if l["t"] == "num" and r["t"] == "num" and not (e["op"] in "/%" and r["v"] == 0):
        return {"t": "num", "v": apply_op(e["op"], l["v"], r["v"])}
    return {**e, "l": l, "r": r}


def _neg(e):
    x = fold_expr(e["e"])
    return {"t": "num", "v": -x["v"]} if x["t"] == "num" else {**e, "e": x}


EXPR = {"num": lambda e: e, "var": lambda e: e, "neg": _neg, "bin": _bin}


def fold_expr(e):
    return dispatch(EXPR, e)


def _with_expr(s):
    return {**s, "e": fold_expr(s["e"])}


def _while(s):
    return {**s, "c": fold_expr(s["c"]), "body": fold_block(s["body"])}


def _if(s):
    return {**s, "c": fold_expr(s["c"]), "then": fold_block(s["then"]), "else": fold_block(s["else"])}


STMT = {"let": _with_expr, "assign": _with_expr, "print": _with_expr, "while": _while, "if": _if}


def fold_block(stmts):
    return [dispatch(STMT, s) for s in stmts]


def run(data):
    return {"ast": {**data["ast"], "body": fold_block(data["ast"]["body"])}}
