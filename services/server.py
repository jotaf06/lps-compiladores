"""Sobe um componente como microservice.

Uso: python -m services.server <componente> [porta]
"""
import sys

import uvicorn

from features import port_for
from services.app import create_app


def main():
    if len(sys.argv) < 2:
        sys.exit("uso: python -m services.server <componente> [porta]")
    name = sys.argv[1]
    port = int(sys.argv[2]) if len(sys.argv) > 2 else port_for(name)
    if name == "recommender":
        from services.recommender_app import create_app as create_recommender

        app = create_recommender()
    else:
        app = create_app(name)
    uvicorn.run(app, host="0.0.0.0", port=port)


if __name__ == "__main__":
    main()
