"""Microservice de recomendação: histórico de compilações por usuário e recomendação de produto."""
import os

from fastapi import FastAPI
from pydantic import BaseModel

from components.recommender import HistoryStore, recommend


class HistoryEvent(BaseModel):
    """Uma compilação feita por um usuário."""

    user: str
    features: list[str]


def create_app(store=None):
    store = store or HistoryStore(os.environ.get("LPS_DB", "history.db"))
    app = FastAPI(
        title="lps-recommender",
        description="Recomenda produtos (conjuntos de features) a partir do histórico do usuário.",
    )

    @app.get("/health")
    def health():
        """Estado do serviço."""
        return {"service": "recommender", "status": "ok"}

    @app.post("/history")
    def add_history(event: HistoryEvent):
        """Registra as features usadas por `user` em uma compilação."""
        store.add(event.user, event.features)
        return {"user": event.user, "recorded": True}

    @app.get("/history/{user}")
    def get_history(user: str):
        """Histórico do usuário (lista de conjuntos de features)."""
        return {"user": user, "history": store.by_user(user)}

    @app.get("/recommend/{user}")
    def get_recommendation(user: str):
        """Produto recomendado para o usuário, com as razões da recomendação."""
        return recommend(store, user)

    return app
