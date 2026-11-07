"""Executa o código gerado (apenas alvos python e vm; C precisa de gcc)."""
import contextlib
import io

from . import vm


def run_code(target, code):
    if target == "python":
        buf = io.StringIO()
        with contextlib.redirect_stdout(buf):
            exec(code, {"__name__": "__main__"})
        return buf.getvalue()
    if target == "vm":
        return "".join(line + "\n" for line in vm.execute(code))
    raise ValueError(f"alvo {target!r} não pode ser executado aqui (compile o código gerado)")
