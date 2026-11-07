"""Interpretador do bytecode gerado por codegen_vm (usado por --run e pelos testes)."""
from .ast_utils import OPNAMES, apply_op

BINOPS = {name: op for op, name in OPNAMES.items()}


def execute(code, max_steps=None):
    prog, labels = [], {}
    for line in code.splitlines():
        line = line.strip()
        if not line:
            continue
        if line.endswith(":"):
            labels[line[:-1]] = len(prog)
        else:
            prog.append(line.split())

    stack, env, out, pc, steps = [], {}, [], 0, 0
    while pc < len(prog):
        steps += 1
        if max_steps is not None and steps > max_steps:
            raise RuntimeError("limite de passos excedido")
        op, *args = prog[pc]
        pc += 1
        if op == "PUSH":
            stack.append(int(args[0]))
        elif op == "LOAD":
            stack.append(env[args[0]])
        elif op == "STORE":
            env[args[0]] = stack.pop()
        elif op == "PRINT":
            out.append(str(stack.pop()))
        elif op == "NEG":
            stack.append(-stack.pop())
        elif op == "JMP":
            pc = labels[args[0]]
        elif op == "JZ":
            if stack.pop() == 0:
                pc = labels[args[0]]
        elif op == "HALT":
            break
        elif op in BINOPS:
            b, a = stack.pop(), stack.pop()
            stack.append(apply_op(BINOPS[op], a, b))
        else:
            raise ValueError(f"instrução desconhecida: {op}")
    return out
