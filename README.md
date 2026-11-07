# LPS de Compiladores (Microservices + Componentes)

Linha de Produto de Software que deriva compiladores diferentes para uma linguagem
simples (aritmética, variáveis, `print`, `if`, `while`) a partir de features:
backend (Python, C ou máquina de pilha), análise semântica, otimizações
(constant folding, dead code) e recomendação de produtos pelo histórico do usuário.

## Executar

```bash
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
python -m pytest -v
```

### Linha de comando (componentes no mesmo processo)

```bash
python lps.py validate products/otimizado.json
python lps.py compile products/otimizado.json examples/exemplo.src --run
python lps.py new meu-produto semantic codegen_c      # cria um novo produto
```

### Microservices (um terminal por serviço, com o venv ativado)

```bash
python -m services.server lexer              # 8001
python -m services.server parser             # 8002
python -m services.server semantic           # 8003
python -m services.server constant_folding   # 8004
python -m services.server dead_code          # 8005
python -m services.server codegen_python     # 8006
python -m services.server codegen_c          # 8007
python -m services.server codegen_vm         # 8008
python -m services.server recommender        # 8009
python -m services.gateway products/otimizado.json   # gateway em 8000
```

Abra http://127.0.0.1:8000 para a tela de configuração (seletor de features,
construção de produto, compilação, recomendação e status dos serviços) e
http://127.0.0.1:8000/docs para a documentação da API.

### Docker

```bash
python lps.py compose products/otimizado.json > docker-compose.yml
docker compose up --build
```

## Estrutura

- `features.py`: modelo de features, restrições e derivação do pipeline.
- `components/`: um componente por feature (interface `run(data) -> dict`).
- `services/`: microservices FastAPI, gateway e tela de configuração.
- `orchestrator.py`, `derivation.py`: execução do pipeline e geração de produtos.
- `products/`: configurações de produtos. `tests/`: testes. `relatorio/`: relatório em Typst.
