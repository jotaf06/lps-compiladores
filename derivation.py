"""Derivação de produto: arquivo de configuração e docker-compose."""
import json
from pathlib import Path

from features import SERVICES, port_for, services_for


def save_product(name, features, directory="products"):
    """Grava products/<name>.json e devolve o caminho."""
    path = Path(directory) / f"{name}.json"
    path.write_text(json.dumps({"name": name, "features": list(features)}, indent=2) + "\n")
    return path


def build_compose(name, features, all_services=False):
    """docker-compose.yml com os microservices do produto (ou todos), mais o gateway.

    `all_services` sobe todos os serviços, útil para trocar de produto na tela.
    """
    services = list(SERVICES) if all_services else services_for(features)
    host = lambda svc: svc.replace("_", "-")  # hostname DNS não aceita "_"

    lines = ["services:"]
    for svc in services:
        lines += [
            f"  {host(svc)}:",
            "    build: .",
            f"    command: python -m services.server {svc} 8000",
            "    ports:",
            f'      - "{port_for(svc)}:8000"',
        ]
        if svc == "recommender":
            lines += [
                "    environment:",
                "      LPS_DB: /data/history.db",
                "    volumes:",
                "      - recommender-data:/data",
            ]
    lines += [
        "  gateway:",
        "    build: .",
        f"    command: python -m services.gateway products/{name}.json 8000",
        "    environment:",
        '      LPS_URL_TEMPLATE: "http://{name}:8000"',
        "    ports:",
        '      - "8000:8000"',
        "    volumes:",
        "      - ./products:/app/products",  # produtos criados na tela aparecem no disco
        "    depends_on:",
        *[f"      - {host(svc)}" for svc in services],
    ]
    if "recommender" in services:
        lines += ["volumes:", "  recommender-data:"]
    return "\n".join(lines) + "\n"
