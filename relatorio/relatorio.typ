#set document(title: "Linha de Produto de Software para Compiladores")
#set page(paper: "a4", margin: (x: 2.5cm, y: 2.5cm), numbering: "1")
#set text(font: "New Computer Modern", size: 11pt, lang: "pt")
#set par(justify: true, first-line-indent: 1.2cm, leading: 0.7em)
#set heading(numbering: "1.")
#show heading: set block(above: 1.4em, below: 0.9em)
#show raw: set text(size: 9pt)
#show figure.caption: set text(size: 9pt)

// Figuras ainda não desenhadas: troque por #image("figuras/arquivo.png", width: 100%)
#let pendente(texto) = rect(
  width: 100%, height: 5cm, stroke: (dash: "dashed"), inset: 1em,
  align(center + horizon, emph[Figura a inserir: #texto]),
)

#let parte(titulo) = {
  v(0.8em)
  heading(level: 1, numbering: none, titulo)
}

// ---------------- Capa ----------------
#page(numbering: none)[
  #set par(first-line-indent: 0pt)
  #align(center)[
    #align(center)[
    #grid(
      columns: 2,
      align: horizon,
      image("logos/ufal.jpg", height: 10em),
      image("logos/ic.png", height: 6em)

    )
  ]

    #text(weight: "bold", size: 17pt)[Universidade Federal de Alagoas] \
    #text(weight: "bold", size: 17pt)[Instituto de Computação] \
    #v(2cm)
    José Félix de Oliveira Neto
    #v(1fr)
    #text(size: 16pt)[Linha de Produto de Software para Compiladores] \
    #v(0.3cm)
    _Microservices e Componentes de Software_
    #v(1fr)
    #align(right)[
      #box(width: 8cm)[
        #set align(left)
        #set par(justify: true)
        Trabalho apresentado ao professor Arturo Hernández Domínguez para a
        disciplina de Tópicos em Engenharia de Software --- Projetando Linhas
        de Produto de Software.
      ]
    ]
    #v(1cm)
    Repositório: LINK_DO_GITHUB
    #v(0.5cm)
    Maceió, DATA
  ]
]

#outline(title: "Sumário", indent: 1em)
#pagebreak()

// ---------------- Conteúdo ----------------
= Enunciado

Um compilador traduz código escrito em uma linguagem-fonte para outra forma, como
código em outra linguagem ou instruções para uma máquina virtual. Compiladores
diferentes compartilham a mesma estrutura de fases (análise léxica, sintática,
semântica, otimização e geração de código), mas variam no que fazem em cada fase:
qual linguagem-alvo produzem, se verificam erros semânticos e quais otimizações
aplicam.

Este projeto é uma Linha de Produto de Software (LPS) para compiladores de uma
linguagem imperativa simples, com aritmética, variáveis, `print`, `if` e `while`. A
partir de componentes reutilizáveis, o usuário monta um produto escolhendo as
_features_ em uma tela de configuração e compila programas com ele. Cada fase do
compilador é um microservice, e um microservice adicional de recomendação sugere
produtos a partir do perfil (histórico de compilações) do usuário.

#parte[Parte 1 --- Modelagem]

= Metodologia Ágil Escolhida

Foi escolhido o *Scrum*, adaptado a uma equipe de uma pessoa, que acumula os papéis de
Product Owner, Scrum Master e Time de Desenvolvimento. Foram mantidos os elementos
que organizam o trabalho:

#list(
  [*Product Backlog*: lista priorizada de histórias de usuário (seção 5).],
  [*Sprints* curtos, cada um com *Sprint Backlog* e um incremento funcional.],
  [*Sprint Planning* no início, *Sprint Review* ao final (demonstração do incremento) e
   *Retrospectiva* para ajustar o processo.],
  [*Definição de pronto*: código com testes automatizados aprovados e documentado.],
)

= Técnicas de Reuso de Software Utilizadas

O projeto combina três técnicas de reuso:

#list(
  [*Linha de Produto de Software*: o núcleo de ativos (componentes) é reutilizado para
   derivar vários compiladores. A variabilidade é descrita por um modelo de features,
   com restrições, e produtos são arquivos de configuração (`products/*.json`).],
  [*Componentes de software*: cada feature é um componente com a mesma interface,
   `run(data) -> dict`, registrado em um registro de componentes. Trocar uma variante
   (por exemplo, o backend) não altera os demais componentes.],
  [*Microservices*: cada componente também é exposto como um serviço HTTP independente
   (FastAPI). Um API gateway é o ponto de entrada, e o `docker-compose` de um produto
   sobe apenas os serviços de suas features.],
)

= Desenvolvimento do Projeto segundo o Scrum e as Técnicas de Reuso

O desenvolvimento foi dividido em sprints. A cada sprint, o backlog foi planejado, um
incremento foi entregue e demonstrado, e a retrospectiva orientou a sprint seguinte:

#list(
  [*Sprint 1 --- Modelagem:* modelo de features, restrições, produtos e diagramas.],
  [*Sprint 2 --- Componentes:* lexer, parser, análise semântica, otimizações,
   backends, registro de componentes e testes. Produto: LPS funcionando em linha de
   comando, com componentes no mesmo processo.],
  [*Sprint 3 --- Microservices e implantação:* serviços FastAPI, orquestrador, gateway,
   derivação de produto e `docker-compose` por produto.],
  [*Sprint 4 --- Recomendação e tela de configuração:* microservice de recomendação
   com histórico em SQLite, seletor de features, construção de novo produto e painel de
   microservices.],
  [*Sprint 5 --- Documentação:* relatório, diagramas e publicação do repositório.],
)

A técnica de reuso orientou a ordem: primeiro os ativos (componentes, Sprint 2), depois
sua exposição como serviços (Sprint 3) e, por fim, a derivação de produtos pela tela
(Sprint 4).

= Product Backlog e Sprint Backlog

#heading(level: 2, numbering: none)[Product Backlog]

#table(
  columns: (auto, 1fr, auto, auto),
  align: (left, left, center, center),
  [*ID*], [*História de usuário*], [*Prioridade*], [*Sprint*],
  [US1], [Como engenheiro de LPS, quero um modelo de features com restrições para derivar produtos válidos.], [Alta], [1],
  [US2], [Como usuário, quero compilar um programa-fonte (léxico e sintático).], [Alta], [2],
  [US3], [Como usuário, quero escolher o backend (Python, C ou máquina de pilha).], [Alta], [2],
  [US4], [Como usuário, quero opcionalmente validar variáveis (análise semântica).], [Média], [2],
  [US5], [Como usuário, quero opcionalmente otimizar o código (constant folding e dead code).], [Média], [2],
  [US6], [Como arquiteto, quero cada componente como microservice independente.], [Alta], [3],
  [US7], [Como usuário, quero um gateway único para compilar.], [Alta], [3],
  [US8], [Como operador, quero subir via Docker só os serviços do produto.], [Média], [3],
  [US9], [Como usuário, quero receber recomendação de produto pelo meu histórico.], [Alta], [4],
  [US10], [Como usuário, quero uma tela para selecionar features e construir um produto.], [Alta], [4],
  [US11], [Como usuário, quero ver quais microservices estão no ar e em quais portas.], [Média], [4],
  [US12], [Como avaliador, quero o relatório e o repositório documentados.], [Alta], [5],
)

#heading(level: 2, numbering: none)[Sprint Backlog]

#table(
  columns: (auto, 1fr),
  align: (left, left),
  [*Sprint*], [*Tarefas (histórias)*],
  [1], [Definir features e restrições (US1); diagrama de features; descrever produtos `mini`, `seguro` e `otimizado`.],
  [2], [Lexer e parser (US2); backends Python, C e VM (US3); semântica (US4); constant folding e dead code (US5); testes.],
  [3], [Serviço genérico FastAPI e orquestrador (US6); gateway (US7); `compose` por produto e Dockerfile (US8).],
  [4], [Serviço `recommender` e histórico em SQLite (US9); tela de configuração e construção de produto (US10); painel de serviços (US11).],
  [5], [Relatório em Typst, diagramas, README e GitHub (US12).],
)

== Diagrama de Features

#figure(
  image("figuras/features.svg", width: 100%),
  caption: [Diagrama de features da LPS de compiladores.],
)

#table(
  columns: (auto, 1fr),
  align: (left, left),
  [*Feature*], [*Descrição*],
  [Lexer], [Converte o texto-fonte em tokens com tipo, texto e linha.],
  [Parser], [Constrói a árvore sintática abstrata (AST) por descida recursiva, com precedência de operadores.],
  [Análise Semântica], [Verifica variáveis declaradas e redeclaradas, usando uma pilha de escopos.],
  [Constant Folding], [Avalia em tempo de compilação expressões com operandos constantes.],
  [Dead Code Elimination], [Remove `if` e `while` com condição constante, mantendo só o ramo alcançável.],
  [Backend Python], [Gera um programa Python equivalente.],
  [Backend C], [Gera um programa C equivalente (`main` com `printf`).],
  [Backend Máquina de Pilha], [Gera bytecode textual executado por uma VM de pilha incluída no projeto.],
  [Recomendação], [Registra o histórico do usuário e recomenda um produto válido (seção 6.1).],
)

#table(
  columns: (auto, auto, 1fr),
  align: (left, left, left),
  [*Restrição*], [*Tipo*], [*Justificativa*],
  [Exatamente um backend], [XOR], [O compilador precisa de uma única linguagem-alvo.],
  [Constant Folding exige Análise Semântica], [requires], [Otimizar só programas validados.],
  [Dead Code exige Constant Folding], [requires], [As condições só se tornam constantes após o folding.],
)

#table(
  columns: (auto, 1fr, auto),
  align: (left, left, left),
  [*Produto*], [*Features (além de Lexer e Parser)*], [*Alvo*],
  [`mini`], [Backend Python], [Python],
  [`seguro`], [Análise Semântica, Backend C], [C],
  [`otimizado`], [Análise Semântica, Constant Folding, Dead Code, Backend Máquina de Pilha], [VM],
)

== Arquitetura em Camadas e Diagrama de Variabilidade

A arquitetura segue o estilo de pipeline sobre três camadas: *cliente* (tela de
configuração ou CLI), *gateway* e *serviços*. O gateway valida a configuração,
monta o pipeline do produto e aciona os serviços.

A variabilidade é representada na notação de modelos de variabilidade de Pohl et al.
(2005), resumida na Figura abaixo: pontos de variação (VP), variantes (V), dependências
opcionais e obrigatórias, escolha alternativa com cardinalidade `[min..max]`,
dependências de artefato e restrições `requires_v_v`.

#figure(
  image("figuras/legenda.svg", width: 100%),
  caption: [Notação de variabilidade utilizada nos diagramas.],
)

Na Figura seguinte, à esquerda estão as camadas da arquitetura; à direita, os pontos de
variação. As setas traço-ponto ligam cada VP ao elemento da arquitetura que ele
parametriza: a variante escolhida determina quais serviços entram no pipeline.

#figure(
  image("figuras/camadas.svg", width: 100%),
  caption: [Arquitetura em camadas e diagrama de variabilidade.],
)

#table(
  columns: (auto, auto, 1fr),
  align: (left, left, left),
  [*Ponto de variação (VP)*], [*Tipo*], [*Variantes*],
  [Backend], [Alternativo (XOR)], [Python, C, Máquina de Pilha],
  [Otimização], [Opcional (OR)], [Constant Folding, Dead Code Elimination],
  [Semântica], [Opcional], [Análise Semântica],
  [Recomendação], [Opcional], [Recomendação por histórico],
)

== Diagrama de Componentes e Diagrama de Variabilidade

Cada feature é um componente com a mesma interface, `run(data) -> dict`: recebe o
conteúdo acumulado do pipeline (código, tokens, AST) e devolve apenas o que acrescenta
ou substitui. O registro de componentes associa o nome da feature ao componente.

#figure(
  image("figuras/componentes.svg", width: 100%),
  caption: [Diagrama de componentes e variabilidade.],
)

No diagrama, cada componente variável (embaixo) realiza uma variante (caixa com V) de um
VP. O núcleo (Gateway, Orchestrator, Registry, Lexer e Parser) está sempre presente. As
setas `requires_v_v` expressam as restrições do modelo de features: Constant Folding
requer Análise Semântica, e Dead Code requer Constant Folding.

*Evolução da LPS.* Novas variantes encaixam nos VPs sem alterar o núcleo: um novo
backend (por exemplo, JavaScript) é um componente `codegen_js` no VP Backend; uma
nova otimização entra no VP Otimização e em `PIPELINE_ORDER`; funções na linguagem
exigem uma palavra-chave no lexer, métodos em `KEYWORD_STMTS` no parser e handlers
`func`, `call` e `return` nas tabelas de dispatch da análise semântica (que já usa
pilha de escopos) e dos backends.

== Tela de Configuração e Construção de um Novo Produto

A tela de configuração é servida pelo gateway em `/`. O usuário seleciona as features
(obrigatórias travadas, backend como escolha única) e a tela aplica as restrições do
modelo na hora: marcar Dead Code marca também Constant Folding e Análise Semântica, e
desmarcar uma feature desmarca as que dependem dela. Ao clicar em *Construir produto*, o
gateway valida a seleção, grava `products/<nome>.json` e gera o `docker-compose.yml` do
produto.

#figure(
  grid(
    columns: 2, gutter: 1.2cm, align: top,
    image("figuras/seletor.png", height: 9.5cm),
    image("figuras/produto-construido.png", height: 9.5cm),
  ),
  caption: [Seletor de features com a validação do modelo (esquerda) e produto construído,
   com o arquivo salvo e o `docker-compose.yml` gerado (direita).],
)

#parte[Arquitetura do Sistema com Microservices]

= Arquitetura Baseada em Microserviços

== Arquitetura do Sistema usando Microservices e Recomendação

Cliente, gateway e serviços formam três camadas. O cliente fala só com o gateway, que
aciona cada fase do compilador como um microservice e consulta o microservice de
recomendação.

#figure(
  image("figuras/microservices.svg", width: 80%),
  caption: [Arquitetura baseada em microservices (Client, Gateway e Services).],
)

*Microservice de recomendação.* O perfil do usuário é o histórico das features que ele
usou nas compilações, gravado em SQLite. A recomendação é explicável e sempre um produto
válido do modelo de features:

#list(
  [escolhe o *backend mais usado* pelo usuário;],
  [mantém as *otimizações usadas em pelo menos metade* das compilações dele;],
  [acrescenta uma *sugestão nova*: a feature que usuários de perfil parecido
   (similaridade de Jaccard entre conjuntos de features) usam e ele ainda não usou. Se
   não há outros usuários, sugere o próximo passo natural
   (semântica, depois constant folding, depois dead code);],
  [completa o resultado com as dependências do modelo de features;],
  [usuário sem histórico recebe o produto mais popular entre todos os registros.],
)

== Especificação do API Gateway

Todos os endpoints estão documentados no código (docstrings) e na interface interativa
do FastAPI em `/docs`.

#table(
  columns: (auto, auto, 1fr),
  align: (left, left, left),
  [*Método*], [*Rota*], [*Função*],
  [GET], [`/`], [Tela de configuração.],
  [GET], [`/health`], [Produto padrão do gateway e seu pipeline.],
  [GET], [`/api/model`], [Modelo de features, restrições, portas, produtos salvos e produto padrão.],
  [POST], [`/api/validate`], [Valida a seleção de features; devolve pipeline e serviços necessários.],
  [POST], [`/api/products`], [Constrói um produto: grava o JSON e gera o `docker-compose`.],
  [POST], [`/compile`], [Compila o código-fonte acionando os microservices; devolve código, serviços acionados e, no alvo VM, a saída da execução.],
  [GET], [`/api/recommend/{user}`], [Recomendação do usuário (consulta o `recommender`).],
  [GET], [`/api/status`], [Estado e porta de cada microservice.],
)

== Especificação de Cada Microservice

Os serviços das fases do compilador são instâncias do mesmo serviço genérico
(`services/app.py`) com um componente diferente; todos expõem `GET /health` e
`POST /run`. O corpo é o conteúdo acumulado do pipeline e a resposta é o mesmo conteúdo
acrescido do que a fase produz; em caso de erro no programa-fonte, a resposta traz
`errors`.

#table(
  columns: (auto, auto, 1fr, 1fr),
  align: (left, left, left, left),
  [*Serviço*], [*Porta*], [*Entrada*], [*Saída acrescentada*],
  [`lexer`], [8001], [`source`], [`tokens`],
  [`parser`], [8002], [`tokens`], [`ast`],
  [`semantic`], [8003], [`ast`], [nada (ou `errors`)],
  [`constant_folding`], [8004], [`ast`], [`ast` otimizada],
  [`dead_code`], [8005], [`ast`], [`ast` sem código inalcançável],
  [`codegen_python`], [8006], [`ast`], [`code`, `target`],
  [`codegen_c`], [8007], [`ast`], [`code`, `target`],
  [`codegen_vm`], [8008], [`ast`], [`code`, `target`],
  [`recommender`], [8009], [histórico do usuário], [produto recomendado e razões],
)

Endpoints do `recommender`:

#table(
  columns: (auto, auto, 1fr),
  align: (left, left, left),
  [*Método*], [*Rota*], [*Função*],
  [GET], [`/health`], [Estado do serviço.],
  [POST], [`/history`], [Registra as features usadas por um usuário em uma compilação.],
  [GET], [`/history/{user}`], [Histórico do usuário.],
  [GET], [`/recommend/{user}`], [Produto recomendado, com as razões.],
)

== Microservices em Execução e suas Portas

#figure(
  image("figuras/portas.png", width: 6.5cm),
  caption: [Painel de microservices: os 9 serviços em execução (pontos verdes) e suas
   portas, de 8001 a 8009. O gateway responde na porta 8000.],
)

== Passo a Passo para Construir uma Aplicação (Produto) a partir da LPS

#enum(
  [Instale as dependências: `pip install -r requirements.txt`.],
  [Suba os microservices das features desejadas (um terminal por serviço, com
   `python -m services.server <componente>`) e o gateway
   (`python -m services.gateway products/otimizado.json`). Alternativa: gerar o
   `docker-compose.yml` do produto e executar `docker compose up --build`.],
  [Abra `http://127.0.0.1:8000` e, em *Configuração do produto*, selecione o backend e
   as features opcionais. A tela aplica as restrições e mostra o pipeline derivado.],
  [Informe um nome e clique em *Construir produto*. O gateway grava
   `products/<nome>.json` e gera o `docker-compose.yml` apenas com os serviços do
   produto.],
  [Escreva o programa-fonte, informe o usuário e clique em *Compilar*. A tela mostra os
   microservices acionados, o código gerado e, no alvo VM, a saída.],
  [Com a feature *Recomendação* marcada, cada compilação entra no histórico; use
   *Ver recomendação* para receber o produto sugerido e *Aplicar recomendação* para
   preencher o seletor.],
)

Pela linha de comando, o equivalente é `python lps.py new <nome> <features...>`,
`python lps.py compile products/<nome>.json programa.src --run` e
`python lps.py compose products/<nome>.json`.

#parte[Parte 2 --- Implementação]

= Tecnologias Utilizadas

#table(
  columns: (3.9cm, 3.9cm, 2.4cm, 1fr),
  align: (left, left, left, left),
  [*Microservice*], [*Linguagem*], [*Banco de dados*], [*Observação*],
  [Gateway], [Python 3.12 + FastAPI], [nenhum], [Serve a tela (HTML, CSS e JavaScript puros).],
  [`lexer`, `parser`, `semantic`], [Python 3.12 + FastAPI], [nenhum], [Sem estado.],
  [`constant_folding`, `dead_code`], [Python 3.12 + FastAPI], [nenhum], [Sem estado.],
  [`codegen_python`, `codegen_c`, `codegen_vm`], [Python 3.12 + FastAPI], [nenhum], [Sem estado.],
  [`recommender`], [Python 3.12 + FastAPI], [SQLite], [Histórico de compilações por usuário.],
)

Demais ferramentas: *Uvicorn* (servidor ASGI), *httpx* (chamadas entre serviços),
*Docker* e *Docker Compose* (implantação), *pytest* (testes automatizados), *Typst*
(relatório), *draw.io* (diagramas) e *GitHub* (repositório).

= Telas do Funcionamento do Produto

A interface principal destaca os microservices utilizados: após cada compilação, a tela
mostra a lista de serviços acionados com suas portas, e o painel lateral mostra o estado
de todos os serviços.

#figure(
  image("figuras/tela-principal.png", width: 100%),
  caption: [Tela principal com o produto `otimizado` após uma compilação. Coluna 1:
   configuração do produto. Coluna 2: programa-fonte, microservices acionados (em
   destaque, com as portas), código gerado para a máquina de pilha e saída da execução.
   Coluna 3: recomendação e estado dos microservices.],
)

Para o programa `let a = 5; let b = 2; print a+b;`, o pipeline do produto `otimizado`
aciona seis serviços (`lexer`, `parser`, `semantic`, `constant_folding`, `dead_code` e
`codegen_vm`); o serviço do backend gera o bytecode e a saída é `7`.

#figure(
  image("figuras/recomendação.png", width: 6.5cm),
  caption: [Painel de recomendação: produto sugerido a partir do histórico do usuário,
   com as razões da recomendação.],
)

#figure(
  image("figuras/docker-curl.png", width: 100%),
  caption: [Produto `otimizado` executando com microservices no Docker: chamada
   `POST /compile` ao gateway e resposta com os serviços acionados, o código gerado e
   a saída (`120` e `100`).],
)

Programa de demonstração:

```
let n = 5;
let r = 1;
while n > 0 { r = r * n; n = n - 1; }
print r;
if 2 + 3 > 4 { print 100; } else { print 0; }
if 0 { print 999; }
```

Os produtos `mini` (Python) e `otimizado` (VM) produzem a mesma saída, `120` e `100`,
mas o código gerado difere: no produto otimizado, a condição `2 + 3 > 4` vira constante,
o `if` é substituído pelo ramo verdadeiro e o `if 0` desaparece. A suíte de testes
automatizados cobre derivação, restrições, equivalência entre backends, otimizações,
erros, serviços, gateway e recomendação.

= Código no GitHub

Todo o código está no repositório: *LINK_DO_GITHUB* (também na capa). O `README.md`
descreve como instalar, testar, executar localmente, subir os microservices e usar o
Docker.

= Referências

#set par(first-line-indent: 0pt)
#list(
  [FOWLER, M.; LEWIS, J. _Microservices_. martinfowler.com, 2014.],
  [CLEMENTS, P.; NORTHROP, L. _Software Product Lines: Practices and Patterns_.
   Addison-Wesley, 2001.],
  [POHL, K.; BÖCKLE, G.; VAN DER LINDEN, F. _Software Product Line Engineering:
   Foundations, Principles and Techniques_. Springer, 2005.],
  [KANG, K. et al. _Feature-Oriented Domain Analysis (FODA) Feasibility Study_. SEI,
   CMU, 1990.],
  [AHO, A. V.; LAM, M. S.; SETHI, R.; ULLMAN, J. D. _Compiladores: Princípios, Técnicas
   e Ferramentas_. 2. ed. Pearson, 2008.],
  [SCHWABER, K.; SUTHERLAND, J. _The Scrum Guide_. 2020.],
  [Documentação do FastAPI. fastapi.tiangolo.com.],
  [Material da disciplina: Variabilidade e Notação para Variabilidade; LPS: Introdução e
   Diagrama de Features; Conceitos e Ferramentas (SPLOT e FeatureIDE).],
)
