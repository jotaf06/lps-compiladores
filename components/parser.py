"""Componente Parser: data["tokens"] -> data["ast"].

Gramática:
    program := stmt*
    stmt    := 'let' ID '=' expr ';' | ID '=' expr ';' | 'print' expr ';'
             | 'while' expr block | 'if' expr block ['else' block]
    block   := '{' stmt* '}'
    expr    := precedência: ==,!=  <  <,>,<=,>=  <  +,-  <  *,/,%  <  unário '-'
"""
from .errors import CompileError

PREC = {
    "==": 1, "!=": 1,
    "<": 2, ">": 2, "<=": 2, ">=": 2,
    "+": 3, "-": 3,
    "*": 4, "/": 4, "%": 4,
}


class Parser:
    # palavra-chave -> método. Para adicionar funções: registre "fn"/"return" aqui.
    KEYWORD_STMTS = {
        "let": "let_stmt",
        "print": "print_stmt",
        "while": "while_stmt",
        "if": "if_stmt",
    }

    def __init__(self, tokens):
        self.toks = tokens
        self.i = 0

    # --- utilitários ---
    def peek(self):
        return self.toks[self.i]

    def advance(self):
        tok = self.toks[self.i]
        if tok[0] != "EOF":
            self.i += 1
        return tok

    def match(self, kind, value=None):
        tok = self.peek()
        return tok[0] == kind and (value is None or tok[1] == value)

    def expect(self, kind, value=None):
        if not self.match(kind, value):
            _, text, line = self.peek()
            raise CompileError(
                f"linha {line}: esperado {value or kind}, encontrado {text or 'fim do arquivo'!r}"
            )
        return self.advance()

    # --- estrutura ---
    def program(self):
        body = []
        while not self.match("EOF"):
            body.append(self.statement())
        return {"t": "program", "body": body}

    def block(self):
        self.expect("PUNCT", "{")
        body = []
        while not self.match("PUNCT", "}"):
            if self.match("EOF"):
                raise CompileError(f"linha {self.peek()[2]}: bloco não fechado")
            body.append(self.statement())
        self.expect("PUNCT", "}")
        return body

    def statement(self):
        kind, text, line = self.peek()
        if kind == "KW" and text in self.KEYWORD_STMTS:
            return getattr(self, self.KEYWORD_STMTS[text])()
        if kind == "ID" and self.toks[self.i + 1][1] == "=":
            return self.assign_stmt()
        raise CompileError(f"linha {line}: comando inválido {text or 'fim do arquivo'!r}")

    def let_stmt(self):
        self.advance()
        name = self.expect("ID")[1]
        self.expect("OP", "=")
        e = self.expr()
        self.expect("PUNCT", ";")
        return {"t": "let", "n": name, "e": e}

    def assign_stmt(self):
        name = self.advance()[1]
        self.expect("OP", "=")
        e = self.expr()
        self.expect("PUNCT", ";")
        return {"t": "assign", "n": name, "e": e}

    def print_stmt(self):
        self.advance()
        e = self.expr()
        self.expect("PUNCT", ";")
        return {"t": "print", "e": e}

    def while_stmt(self):
        self.advance()
        cond = self.expr()
        return {"t": "while", "c": cond, "body": self.block()}

    def if_stmt(self):
        self.advance()
        cond = self.expr()
        then = self.block()
        other = []
        if self.match("KW", "else"):
            self.advance()
            other = self.block()
        return {"t": "if", "c": cond, "then": then, "else": other}

    # --- expressões ---
    def expr(self, min_prec=1):
        left = self.unary()
        while self.match("OP") and self.peek()[1] in PREC and PREC[self.peek()[1]] >= min_prec:
            op = self.advance()[1]
            right = self.expr(PREC[op] + 1)
            left = {"t": "bin", "op": op, "l": left, "r": right}
        return left

    def unary(self):
        if self.match("OP", "-"):
            self.advance()
            return {"t": "neg", "e": self.unary()}
        return self.primary()

    def primary(self):
        kind, text, line = self.peek()
        if kind == "NUM":
            self.advance()
            return {"t": "num", "v": int(text)}
        if kind == "ID":
            self.advance()
            return {"t": "var", "n": text}  # futuro: se seguir "(", gerar nó "call"
        if self.match("PUNCT", "("):
            self.advance()
            e = self.expr()
            self.expect("PUNCT", ")")
            return e
        raise CompileError(f"linha {line}: expressão esperada, encontrado {text or 'fim do arquivo'!r}")


def run(data):
    return {"ast": Parser(data["tokens"]).program()}
