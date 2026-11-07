"""Recomendação de produtos a partir do perfil (histórico de compilações) do usuário.

Cada compilação registra as features escolhidas. A recomendação é explicável:
  1. backend mais usado pelo usuário;
  2. otimizações que ele usa em pelo menos metade das compilações;
  3. uma sugestão nova: feature que usuários de perfil parecido (similaridade de
     Jaccard) usam e ele ainda não usou; sem outros usuários, o próximo passo natural
     (semantic -> constant_folding -> dead_code);
  4. o resultado é completado com as dependências do modelo de features (`complete`),
     então a recomendação é sempre um produto válido.
Usuário sem histórico recebe o produto mais popular entre todos.
"""
import json
import sqlite3
import threading
from collections import Counter

from features import BACKENDS, OPTIONAL, complete, derive

SELECTABLE = OPTIONAL + BACKENDS
DEFAULT_BACKEND = "codegen_python"


class HistoryStore:
    """Histórico de compilações em SQLite (use ':memory:' nos testes)."""

    def __init__(self, path=":memory:"):
        self.lock = threading.Lock()
        self.db = sqlite3.connect(path, check_same_thread=False)
        with self.db:
            self.db.execute(
                "CREATE TABLE IF NOT EXISTS history ("
                "id INTEGER PRIMARY KEY AUTOINCREMENT, user TEXT NOT NULL, "
                "features TEXT NOT NULL, ts TEXT DEFAULT CURRENT_TIMESTAMP)"
            )

    def add(self, user, features):
        chosen = sorted(set(features) & set(SELECTABLE))
        with self.lock, self.db:
            self.db.execute(
                "INSERT INTO history (user, features) VALUES (?, ?)", (user, json.dumps(chosen))
            )

    def _rows(self, where="", args=()):
        with self.lock:
            cur = self.db.execute(f"SELECT features FROM history {where} ORDER BY id", args)
            return [json.loads(row[0]) for row in cur.fetchall()]

    def by_user(self, user):
        return self._rows("WHERE user = ?", (user,))

    def others(self, user):
        return self._rows("WHERE user != ?", (user,))

    def everyone(self):
        return self._rows()


def _product(features):
    """Features ordenadas e pipeline do produto recomendado."""
    chosen = complete(features)
    ordered = [f for f in SELECTABLE if f in chosen]
    return ordered, derive(ordered)


def recommend(store, user):
    mine = store.by_user(user)
    if not mine:
        return _popular(store, user)

    used = Counter(f for s in mine for f in s)
    n = len(mine)
    backends = [b for b in BACKENDS if used[b]]
    backend = max(backends, key=lambda b: used[b]) if backends else DEFAULT_BACKEND
    base = {f for f in OPTIONAL if used[f] * 2 >= n}
    reasons = [f"baseado em {n} compilação(ões) do usuário", f"backend mais usado: {backend}"]
    if base:
        reasons.append("otimizações frequentes: " + ", ".join(sorted(base)))

    mine_features = set(used)
    scores = Counter()
    for s in store.others(user):
        other = set(s)
        union = other | mine_features
        weight = len(other & mine_features) / len(union) if union else 0
        if weight:
            for f in (other & set(OPTIONAL)) - mine_features:
                scores[f] += weight

    suggestion = None
    candidates = [f for f in OPTIONAL if scores[f] > 0]
    if candidates:
        suggestion = max(candidates, key=lambda f: scores[f])
        reasons.append(f"usuários com perfil parecido também usam {suggestion}")
    else:
        for f in OPTIONAL:
            if f not in mine_features:
                suggestion = f
                reasons.append(f"próximo passo natural: experimentar {suggestion}")
                break

    features, pipeline = _product(base | {backend} | ({suggestion} if suggestion else set()))
    return {"user": user, "features": features, "pipeline": pipeline,
            "suggestion": suggestion, "reasons": reasons}


def _popular(store, user):
    rows = store.everyone()
    if not rows:
        features, pipeline = _product({DEFAULT_BACKEND})
        return {"user": user, "features": features, "pipeline": pipeline, "suggestion": None,
                "reasons": ["sem histórico: produto básico recomendado"]}

    used = Counter(f for s in rows for f in s)
    n = len(rows)
    backends = [b for b in BACKENDS if used[b]]
    backend = max(backends, key=lambda b: used[b]) if backends else DEFAULT_BACKEND
    base = {f for f in OPTIONAL if used[f] * 2 >= n}
    features, pipeline = _product(base | {backend})
    return {"user": user, "features": features, "pipeline": pipeline, "suggestion": None,
            "reasons": [f"usuário novo: produto mais popular entre {n} compilação(ões) registradas"]}
