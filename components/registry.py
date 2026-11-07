"""Registro de componentes: nome da feature -> função run(data) -> dict.

Cada componente recebe o payload acumulado do pipeline e devolve apenas o que
acrescenta/substitui (tokens, ast, code...). É a mesma interface usada
localmente (composição) e pelos microservices.
"""
from . import (
    codegen_c,
    codegen_python,
    codegen_vm,
    constant_folding,
    dead_code,
    lexer,
    parser,
    semantic,
)
from .errors import CompileError

REGISTRY = {
    "lexer": lexer.run,
    "parser": parser.run,
    "semantic": semantic.run,
    "constant_folding": constant_folding.run,
    "dead_code": dead_code.run,
    "codegen_python": codegen_python.run,
    "codegen_c": codegen_c.run,
    "codegen_vm": codegen_vm.run,
}


def invoke(name, data):
    """Executa um componente; erros do fonte viram data["errors"]."""
    try:
        return {**data, **REGISTRY[name](data)}
    except CompileError as e:
        return {**data, "errors": [str(e)]}
