"""Orquestrador: monta o pipeline do produto e o executa.

Modo local  -> compõe os componentes no mesmo processo.
Modo remoto -> chama cada componente como microservice via HTTP.
A URL do serviço vem de LPS_URL_TEMPLATE (campos {name} e {port}).
"""
import os

from components.registry import invoke
from features import derive, port_for

DEFAULT_URL_TEMPLATE = "http://127.0.0.1:{port}"


def service_url(name):
    template = os.environ.get("LPS_URL_TEMPLATE", DEFAULT_URL_TEMPLATE)
    return template.format(name=name.replace("_", "-"), port=port_for(name))


def call_service(name, method, path, payload=None, timeout=10):
    """Chamada HTTP genérica a um microservice; devolve o JSON da resposta."""
    import httpx

    response = httpx.request(method, service_url(name) + path, json=payload, timeout=timeout)
    response.raise_for_status()
    return response.json()


def call_remote(name, data):
    return call_service(name, "POST", "/run", data)


def compile_source(source, features, remote=False, trace=None):
    """Executa o pipeline do produto. `trace`, se dado, recebe os serviços acionados."""
    data = {"source": source}
    for name in derive(features):
        data = call_remote(name, data) if remote else invoke(name, data)
        if trace is not None:
            trace.append(name)
        if data.get("errors"):
            break
    return data
