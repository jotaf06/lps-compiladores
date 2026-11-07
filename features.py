"""Modelo de features da LPS de compiladores e derivação do pipeline.

Árvore de features:
    Compilador
    ├── lexer, parser                      (obrigatórias)
    ├── semantic                           (opcional)
    ├── constant_folding, dead_code        (opcionais)
    ├── backend: codegen_python | codegen_c | codegen_vm   (XOR, exatamente um)
    └── recommendation                     (opcional, fora do pipeline: microservice
                                            que recomenda produtos pelo histórico do usuário)
"""

MANDATORY = ["lexer", "parser"]
OPTIONAL = ["semantic", "constant_folding", "dead_code"]
BACKENDS = ["codegen_python", "codegen_c", "codegen_vm"]
EXTRAS = ["recommendation"]  # features que não são fases do compilador

# Ordem de execução das fases do compilador.
PIPELINE_ORDER = ["lexer", "parser", "semantic", "constant_folding", "dead_code", *BACKENDS]

# Todos os microservices (fases do pipeline + recomendação).
SERVICES = [*PIPELINE_ORDER, "recommender"]

# Restrições cross-tree: feature -> features que ela exige.
REQUIRES = {
    "constant_folding": ["semantic"],
    "dead_code": ["constant_folding"],
}

BASE_PORT = 8001


def validate(features):
    """Retorna a lista de violações do modelo (vazia se a configuração é válida)."""
    selected = set(features) | set(MANDATORY)
    errors = []

    for f in sorted(selected - set(PIPELINE_ORDER) - set(EXTRAS)):
        errors.append(f"feature desconhecida: {f}")

    chosen = [b for b in BACKENDS if b in selected]
    if len(chosen) != 1:
        errors.append(f"escolha exatamente 1 backend entre {BACKENDS} (escolhidos: {chosen})")

    for feature, needs in REQUIRES.items():
        if feature in selected:
            for need in needs:
                if need not in selected:
                    errors.append(f"{feature} requer {need}")
    return errors


def derive(features):
    """Pipeline ordenado do produto (valida antes)."""
    errors = validate(features)
    if errors:
        raise ValueError("; ".join(errors))
    selected = set(features) | set(MANDATORY)
    return [f for f in PIPELINE_ORDER if f in selected]


def complete(features):
    """Fecho das restrições `requires`: acrescenta o que as features escolhidas exigem."""
    selected = set(features)
    pending = list(selected)
    while pending:
        for need in REQUIRES.get(pending.pop(), []):
            if need not in selected:
                selected.add(need)
                pending.append(need)
    return selected


def services_for(features):
    """Microservices que o produto precisa ter no ar."""
    services = derive(features)
    if "recommendation" in features:
        services.append("recommender")
    return services


def port_for(name):
    return BASE_PORT + SERVICES.index(name)


def model():
    """Descrição do modelo de features (usada pela tela de configuração)."""
    return {
        "mandatory": MANDATORY,
        "optional": OPTIONAL,
        "backends": BACKENDS,
        "extras": EXTRAS,
        "requires": REQUIRES,
        "ports": {s: port_for(s) for s in SERVICES},
    }
