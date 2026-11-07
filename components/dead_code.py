"""Otimização: remove código inalcançável com condição constante.

Depende de constant_folding (que transforma condições em literais).
"""


def clean(stmts):
    out = []
    for s in stmts:
        const = s["t"] in ("if", "while") and s["c"]["t"] == "num"
        if s["t"] == "if":
            if const:
                out.extend(clean(s["then"] if s["c"]["v"] != 0 else s["else"]))
            else:
                out.append({**s, "then": clean(s["then"]), "else": clean(s["else"])})
        elif s["t"] == "while":
            if not (const and s["c"]["v"] == 0):
                out.append({**s, "body": clean(s["body"])})
        else:
            out.append(s)
    return out


def run(data):
    return {"ast": {**data["ast"], "body": clean(data["ast"]["body"])}}
