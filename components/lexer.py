"""Componente Lexer: data["source"] -> data["tokens"] ([tipo, texto, linha])."""
import re

from .errors import CompileError

# Para adicionar funções: inclua "fn" e "return" aqui.
KEYWORDS = {"let", "print", "while", "if", "else"}

SPEC = [
    ("COMMENT", r"#[^\n]*"),
    ("NUM", r"\d+"),
    ("ID", r"[A-Za-z_]\w*"),
    ("OP", r"==|!=|<=|>=|[-+*/%<>=]"),
    ("PUNCT", r"[;{}(),]"),
    ("WS", r"[ \t\r]+"),
    ("NL", r"\n"),
    ("BAD", r"."),
]
TOKEN_RE = re.compile("|".join(f"(?P<{name}>{pattern})" for name, pattern in SPEC))


def run(data):
    tokens = []
    line = 1
    for m in TOKEN_RE.finditer(data["source"]):
        kind, text = m.lastgroup, m.group()
        if kind == "NL":
            line += 1
        elif kind in ("WS", "COMMENT"):
            continue
        elif kind == "BAD":
            raise CompileError(f"linha {line}: caractere inesperado {text!r}")
        else:
            if kind == "ID" and text in KEYWORDS:
                kind = "KW"
            tokens.append([kind, text, line])
    tokens.append(["EOF", "", line])
    return {"tokens": tokens}
