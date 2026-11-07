"""Backend VM: data["ast"] -> data["code"] (bytecode textual de máquina de pilha)."""
from .ast_utils import OPNAMES, dispatch


class Emitter:
    def __init__(self):
        self.lines = []
        self.labels = 0

    def label(self):
        self.labels += 1
        return f"L{self.labels}"

    def emit(self, text):
        self.lines.append(text)

    # --- expressões ---
    def expr(self, e):
        dispatch(self.EXPR, e, self)

    def _num(e, self):
        self.emit(f"PUSH {e['v']}")

    def _var(e, self):
        self.emit(f"LOAD {e['n']}")

    def _neg(e, self):
        self.expr(e["e"])
        self.emit("NEG")

    def _bin(e, self):
        self.expr(e["l"])
        self.expr(e["r"])
        self.emit(OPNAMES[e["op"]])

    EXPR = {"num": _num, "var": _var, "neg": _neg, "bin": _bin}

    # --- comandos ---
    def block(self, stmts):
        for s in stmts:
            dispatch(self.STMT, s, self)

    def _store(s, self):
        self.expr(s["e"])
        self.emit(f"STORE {s['n']}")

    def _print(s, self):
        self.expr(s["e"])
        self.emit("PRINT")

    def _while(s, self):
        start, end = self.label(), self.label()
        self.emit(f"{start}:")
        self.expr(s["c"])
        self.emit(f"JZ {end}")
        self.block(s["body"])
        self.emit(f"JMP {start}")
        self.emit(f"{end}:")

    def _if(s, self):
        other, end = self.label(), self.label()
        self.expr(s["c"])
        self.emit(f"JZ {other}")
        self.block(s["then"])
        self.emit(f"JMP {end}")
        self.emit(f"{other}:")
        self.block(s["else"])
        self.emit(f"{end}:")

    STMT = {"let": _store, "assign": _store, "print": _print, "while": _while, "if": _if}


def run(data):
    em = Emitter()
    em.block(data["ast"]["body"])
    em.emit("HALT")
    return {"target": "vm", "code": "\n".join(em.lines) + "\n"}
