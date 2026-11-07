#!/usr/bin/env python3
"""Gera os diagramas do relatório em SVG (sem dependências).

Uso: python3 gerar_figuras.py   (grava os .svg nesta pasta)

Notação de variabilidade: OVM de Pohl et al. (2005): VP (triângulo), variante (caixa
com "V"), dependências opcional/obrigatória, escolha alternativa [min..max],
dependências de artefato e restrições requires_v_v.
"""
import math
from pathlib import Path
from xml.sax.saxutils import escape

OUT = Path(__file__).resolve().parent
FONT = "DejaVu Sans, Liberation Sans, Arial, sans-serif"
INK = "#1d2330"
GRAY = "#f3f4f7"
DASH, DOT, DASHDOT = "6 4", "2 3", "9 3 2 3"

DEFS = (
    "<defs>"
    '<marker id="open" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="9" markerHeight="9" orient="auto">'
    f'<path d="M1,1 L9,5 L1,9" fill="none" stroke="{INK}" stroke-width="1.4"/></marker>'
    '<marker id="solid" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="9" markerHeight="9" orient="auto">'
    f'<path d="M1,1 L9,5 L1,9 z" fill="{INK}" stroke="{INK}"/></marker>'
    "</defs>"
)


class Svg:
    def __init__(self, w, h):
        self.w, self.h, self.items = w, h, []

    def add(self, s):
        self.items.append(s)

    def rect(self, x, y, w, h, fill="#fff", stroke=INK, sw=1.5, rx=0, dash=None):
        d = f' stroke-dasharray="{dash}"' if dash else ""
        self.add(f'<rect x="{x}" y="{y}" width="{w}" height="{h}" rx="{rx}" fill="{fill}" '
                 f'stroke="{stroke}" stroke-width="{sw}"{d}/>')

    def text(self, x, y, s, size=12, anchor="middle", weight="normal", fill=INK, italic=False):
        """Texto multilinha centrado verticalmente em y."""
        lines = s.split("\n")
        lh = size * 1.25
        y0 = y - (len(lines) - 1) * lh / 2 + size * 0.35
        style = ' font-style="italic"' if italic else ""
        spans = "".join(f'<tspan x="{x}" y="{y0 + i * lh:.1f}">{escape(l)}</tspan>' for i, l in enumerate(lines))
        self.add(f'<text font-family="{FONT}" font-size="{size}" font-weight="{weight}" '
                 f'text-anchor="{anchor}" fill="{fill}"{style}>{spans}</text>')

    def line(self, pts, dash=None, arrow=None, sw=1.5):
        d = " ".join(f"{x:.1f},{y:.1f}" for x, y in pts)
        da = f' stroke-dasharray="{dash}"' if dash else ""
        m = f' marker-end="url(#{arrow})"' if arrow else ""
        self.add(f'<polyline points="{d}" fill="none" stroke="{INK}" stroke-width="{sw}"{da}{m}/>')

    def path(self, d, sw=1.5):
        self.add(f'<path d="{d}" fill="none" stroke="{INK}" stroke-width="{sw}"/>')

    def circle(self, x, y, r, fill):
        self.add(f'<circle cx="{x}" cy="{y}" r="{r}" fill="{fill}" stroke="{INK}" stroke-width="1.5"/>')

    def polygon(self, pts, fill="#fff"):
        d = " ".join(f"{x:.1f},{y:.1f}" for x, y in pts)
        self.add(f'<polygon points="{d}" fill="{fill}" stroke="{INK}" stroke-width="1.5"/>')

    def box(self, x, y, w, h, label, size=12, fill="#fff", dash=None, weight="normal"):
        self.rect(x, y, w, h, fill=fill, dash=dash, rx=3)
        self.text(x + w / 2, y + h / 2, label, size=size, weight=weight)

    def save(self, name):
        body = "\n".join(self.items)
        svg = (f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {self.w} {self.h}" '
               f'width="{self.w}" height="{self.h}">\n<rect width="100%" height="100%" fill="#fff"/>\n'
               f"{DEFS}\n{body}\n</svg>\n")
        (OUT / name).write_text(svg, encoding="utf-8")


# ---------------- elementos da notação OVM ----------------
def vp(s, cx, top, name, w=132, h=72):
    """Ponto de variação. Devolve (centro da base, ponto médio da aresta esquerda)."""
    s.polygon([(cx, top), (cx - w / 2, top + h), (cx + w / 2, top + h)])
    cap = 0.42
    s.polygon([(cx, top), (cx - w * cap / 2, top + h * cap), (cx + w * cap / 2, top + h * cap)], fill=INK)
    s.text(cx, top + h * cap * 0.7, "VP", size=10, weight="bold", fill="#fff")
    s.text(cx, top + h * 0.74, name, size=11)
    return (cx, top + h), (cx - w / 4, top + h / 2)


def variant(s, cx, top, name, w=124, h=40):
    x = cx - w / 2
    s.rect(x, top, w, h)
    s.rect(x, top, 20, 16, fill=INK)
    s.text(x + 10, top + 8, "V", size=10, weight="bold", fill="#fff")
    s.text(cx, top + h / 2 + 4, name, size=11)


def alt_arc(s, x, y, label, r=26, a=60, lxy=None):
    dx, dy = r * math.sin(math.radians(a)), r * math.cos(math.radians(a))
    s.path(f"M {x - dx:.1f} {y + dy:.1f} A {r} {r} 0 0 0 {x + dx:.1f} {y + dy:.1f}")
    lx, ly = lxy or (x + 8, y + 36)  # entre as linhas, abaixo do arco
    s.text(lx, ly, label, size=10, anchor="start")


def ovm_group(s, cx, top, vp_name, names, arc=None, spacing=140, vw=124):
    """VP + variantes abaixo, ligadas por dependências opcionais (tracejadas)."""
    base, left = vp(s, cx, top, vp_name)
    vy = top + 72 + 42
    n = len(names)
    boxes = []
    for i, name in enumerate(names):
        vcx = cx + (i - (n - 1) / 2) * spacing
        s.line([base, (vcx, vy)], dash=DASH)
        boxes.append((vcx, vy, vw, 40))
    if arc:
        alt_arc(s, base[0], base[1], arc)
    for (vcx, y, w, h), name in zip(boxes, names):
        variant(s, vcx, y, name, w=w, h=h)
    return {"vp_left": left, "variants": boxes}


def component(s, cx, top, name, w=124, h=36):
    x = cx - w / 2
    s.rect(x, top, w, h, rx=2)
    s.rect(x - 7, top + 7, 14, 7, rx=1)
    s.rect(x - 7, top + h - 14, 14, 7, rx=1)
    s.text(cx + 4, top + h / 2, name, size=11)


def requires(s, pts, label, label_xy, anchor="middle"):
    s.line(pts, dash=DOT, arrow="open")
    s.text(label_xy[0], label_xy[1], label, size=10, italic=True, anchor=anchor)


# ---------------- 1. diagrama de features ----------------
def features():
    s = Svg(740, 480)
    rc = lambda i: 32 + i * 42
    H = 32
    xr, wr = 15, 130
    x1, w1 = 235, 175
    x2, w2 = 505, 205
    l1 = [("Frontend", 0.5, "M"), ("Análise\nSemântica", 2, "O"), ("Otimização", 3.5, "O"),
          ("Backend", 6, "M"), ("Recomendação\n(microservice)", 8, "O")]
    l2 = [("Lexer", 0, "M", 0), ("Parser", 1, "M", 0),
          ("Constant Folding", 3, "O", 2), ("Dead Code Elimination", 4, "O", 2),
          ("Python", 5, None, 3), ("C", 6, None, 3), ("Máquina de Pilha\n(bytecode + VM)", 7, None, 3)]
    root_row = sum(r for _, r, _ in l1) / len(l1)
    root = (xr + wr, rc(root_row))

    # arestas
    for _, row, _ in l1:
        s.line([root, (x1, rc(row))])
    for _, row, _, parent in l2:
        s.line([(x1 + w1, rc(l1[parent][1])), (x2, rc(row))])
    # caixas
    s.box(xr, rc(root_row) - H / 2, wr, H, "Compilador", size=13, fill="#dfe8fb", weight="bold")
    for name, row, _ in l1:
        s.box(x1, rc(row) - H / 2, w1, H, name, fill="#eef2fb")
    for name, row, _, _ in l2:
        s.box(x2, rc(row) - H / 2, w2, H, name)
    # marcadores obrigatória (preenchido) / opcional (vazio)
    for _, row, kind in l1:
        s.circle(x1, rc(row), 5, INK if kind == "M" else "#fff")
    for _, row, kind, _ in l2:
        if kind:
            s.circle(x2, rc(row), 5, INK if kind == "M" else "#fff")
    # grupo alternativo (XOR) do backend
    px, py = x1 + w1, rc(l1[3][1])
    a = math.atan2(42, x2 - px)
    r = 42
    s.path(f"M {px + r * math.cos(a):.1f} {py - r * math.sin(a):.1f} "
           f"A {r} {r} 0 0 1 {px + r * math.cos(a):.1f} {py + r * math.sin(a):.1f}")
    s.text(px + r + 6, py - 10, "XOR", size=10, anchor="start")

    # legenda e restrições
    y = 410
    s.circle(25, y, 5, INK)
    s.text(36, y, "obrigatória", size=11, anchor="start")
    s.circle(140, y, 5, "#fff")
    s.text(151, y, "opcional", size=11, anchor="start")
    s.path(f"M 235 {y - 9} A 12 12 0 0 1 235 {y + 9}")
    s.text(252, y, "alternativa (XOR: exatamente uma)", size=11, anchor="start")
    s.text(15, 440, "Restrições: Constant Folding requer Análise Semântica; "
                    "Dead Code Elimination requer Constant Folding.", size=11, anchor="start")
    s.text(15, 460, "Recomendação é um microservice fora do pipeline de compilação.", size=11, anchor="start")
    s.save("features.svg")


# ---------------- 2. arquitetura em camadas + variabilidade ----------------
def camadas():
    s = Svg(1000, 760)

    def layer(y, h, title):
        s.rect(20, y, 470, h, fill=GRAY, rx=6)
        s.text(32, y + 14, title, size=12, anchor="start", weight="bold")

    layer(20, 84, "Cliente")
    s.box(36, 48, 215, 44, "Tela de configuração\n(HTML + JavaScript)")
    s.box(259, 48, 215, 44, "CLI\n(lps.py)")
    layer(124, 106, "Gateway")
    for i, label in enumerate(["API Gateway\n(FastAPI, :8000)", "Orquestrador\n(pipeline do produto)",
                               "Derivação de produto\n(validação + compose)"]):
        s.box(36 + i * 154, 152, 146, 62, label, size=11)
    layer(250, 290, "Serviços (um microservice por componente)")
    rows = ["Frontend: lexer, parser (obrigatórios)", "Análise semântica: semantic",
            "Otimizações: constant_folding, dead_code",
            "Backends: codegen_python | codegen_c | codegen_vm", "Recomendação: recommender"]
    row_y = [282 + 50 * i for i in range(5)]
    for y, label in zip(row_y, rows):
        s.box(36, y, 438, 38, label)
    layer(560, 70, "Dados")
    s.box(36, 588, 438, 30, "SQLite (histórico de compilações por usuário)")
    for y1, y2 in [(104, 124), (230, 250)]:
        s.line([(255, y1), (255, y2)], arrow="solid")
    s.line([(255, row_y[4] + 38), (255, 588)], arrow="solid")

    # variabilidade (direita)
    cx = 770
    g_sem = ovm_group(s, cx, 20, "Semântica", ["Análise\nSemântica"])
    g_opt = ovm_group(s, cx, 210, "Otimização", ["Constant\nFolding", "Dead Code\nElimination"],
                      arc="[0..2]", spacing=150)
    g_bk = ovm_group(s, cx, 400, "Backend", ["Python", "C", "Máquina\nde Pilha"], arc="[1..1]", spacing=140)
    g_rec = ovm_group(s, cx, 590, "Recomendação", ["Recomendação\npor histórico"])
    for g, row in zip([g_sem, g_opt, g_bk, g_rec], [1, 2, 3, 4]):
        s.line([g["vp_left"], (478, row_y[row] + 19)], dash=DASHDOT, arrow="open")

    # restrições entre variantes
    cf, dc = g_opt["variants"]
    sem = g_sem["variants"][0]
    y1, y2 = sem[1] + 20, cf[1] + 20
    requires(s, [(cf[0] - 62, y2), (556, y2), (556, y1), (sem[0] - 62, y1)],
             "requires_v_v", (562, (y1 + y2) / 2), anchor="start")
    yb = dc[1] + 40
    requires(s, [(dc[0] - 25, yb), (dc[0] - 25, yb + 14), (cf[0] + 25, yb + 14), (cf[0] + 25, yb)],
             "requires_v_v", ((cf[0] + dc[0]) / 2, yb + 28))
    s.save("camadas.svg")


# ---------------- 3. componentes + variabilidade ----------------
def componentes():
    s = Svg(880, 612)
    s.text(20, 12, "Núcleo (sempre presente)", size=11, anchor="start", weight="bold")
    for i, name in enumerate(["API Gateway", "Orchestrator", "Registry", "Lexer", "Parser"]):
        component(s, 20 + i * 170 + 75, 28, name, w=150, h=38)
    for i in range(2):
        s.line([(20 + i * 170 + 150 + 7, 47), (20 + (i + 1) * 170 - 7, 47)], arrow="open")

    def group(cx, top, vp_name, items, arc=None, spacing=140):
        g = ovm_group(s, cx, top, vp_name, [v for v, _ in items], arc=arc, spacing=spacing)
        for (vcx, vy, _, vh), (_, comp) in zip(g["variants"], items):
            ctop = vy + vh + 34
            component(s, vcx, ctop, comp)
            s.line([(vcx, ctop), (vcx, vy + vh)], dash=DOT, arrow="open")
        return g

    g_sem = group(225, 110, "Semântica", [("Análise\nSemântica", "Semantic")])
    g_opt = group(665, 110, "Otimização", [("Constant\nFolding", "ConstantFolding"),
                                           ("Dead Code\nElimination", "DeadCode")], arc="[0..2]")
    group(225, 370, "Backend", [("Python", "CodegenPython"), ("C", "CodegenC"),
                                ("Máquina\nde Pilha", "CodegenVM")], arc="[1..1]")
    group(665, 370, "Recomendação", [("Recomendação\npor histórico", "Recommender")])

    cf, dc = g_opt["variants"]
    sem = g_sem["variants"][0]
    y = cf[1] + 20
    requires(s, [(cf[0] - 62, y), (sem[0] + 62, y)], "requires_v_v", ((cf[0] - 62 + sem[0] + 62) / 2, y - 10))
    yb = dc[1] + 40
    requires(s, [(dc[0] - 25, yb), (dc[0] - 25, yb + 13), (cf[0] + 25, yb + 13), (cf[0] + 25, yb)],
             "requires_v_v", ((cf[0] + dc[0]) / 2, yb + 25))
    s.save("componentes.svg")


# ---------------- 4. arquitetura de microservices ----------------
def microservices():
    s = Svg(780, 640)
    s.text(12, 14, "Client", size=13, weight="bold", anchor="start")
    s.box(150, 28, 220, 50, "Navegador\n(tela de configuração)")
    s.box(410, 28, 220, 50, "CLI\n(lps.py, curl)")
    s.line([(260, 78), (260, 130)], arrow="solid")
    s.line([(520, 78), (390, 130)], arrow="solid")
    s.line([(0, 100), (780, 100)], dash=DASH, sw=1)
    s.text(12, 114, "Gateway", size=13, weight="bold", anchor="start")
    s.box(270, 130, 240, 56, "API Gateway (porta 8000)\nFastAPI: / · /compile · /api/*", size=12, fill="#eef2fb")
    s.line([(0, 206), (780, 206)], dash=DASH, sw=1)
    s.text(12, 220, "Services", size=13, weight="bold", anchor="start")
    s.line([(390, 186), (390, 238)], arrow="solid")
    s.text(398, 214, "HTTP POST /run (uma chamada por fase)", size=10, anchor="start", italic=True)

    s.rect(20, 238, 740, 340, fill=GRAY, rx=6)
    s.text(32, 252, "Rede interna do Docker Compose: um container por microservice (porta interna 8000)",
           size=11, anchor="start", weight="bold")
    row1 = [("lexer", 8001, False), ("parser", 8002, False), ("semantic", 8003, True),
            ("constant_folding", 8004, True), ("dead_code", 8005, True)]
    for i, (name, port, opt) in enumerate(row1):
        s.box(40 + i * 144, 275, 130, 58, f"{name}\n:{port}", dash=DASH if opt else None)
    s.rect(30, 355, 460, 112, rx=4, fill="none", dash=DOT)
    s.text(40, 368, "Backend: exatamente um", size=10, anchor="start", italic=True)
    row2 = [("codegen_python", 8006), ("codegen_c", 8007), ("codegen_vm", 8008)]
    for i, (name, port) in enumerate(row2):
        s.box(40 + i * 144, 385, 130, 58, f"{name}\n:{port}")
    s.box(616, 385, 130, 58, "recommender\n:8009", dash=DASH)
    s.line([(681, 443), (681, 488)], arrow="solid")
    s.add(f'<ellipse cx="681" cy="500" rx="55" ry="12" fill="#fff" stroke="{INK}" stroke-width="1.5"/>')
    s.add(f'<path d="M626 500 V540 A55 12 0 0 0 736 540 V500" fill="#fff" stroke="{INK}" stroke-width="1.5"/>')
    s.add(f'<ellipse cx="681" cy="500" rx="55" ry="12" fill="#fff" stroke="{INK}" stroke-width="1.5"/>')
    s.text(681, 530, "SQLite\n(histórico)", size=11)
    s.text(40, 500, "Ordem de chamada do gateway:\nlexer → parser → [semantic] → [constant_folding]\n→ [dead_code] → um backend",
           size=11, anchor="start")
    s.line([(30, 604), (70, 604)])
    s.text(78, 604, "obrigatório", size=11, anchor="start")
    s.line([(170, 604), (210, 604)], dash=DASH)
    s.text(218, 604, "opcional (borda tracejada)", size=11, anchor="start")
    s.save("microservices.svg")


# ---------------- legenda da notação ----------------
def legenda():
    s = Svg(830, 215)
    cells = [10, 205, 400, 595]

    def caption(i, y, text):
        s.text(cells[i] + 90, y, text, size=11)

    # linha 1
    vp(s, cells[0] + 90, 14, "nome", w=84, h=56)
    caption(0, 98, "Ponto de variação (VP)")
    variant(s, cells[1] + 90, 26, "nome", w=90, h=34)
    caption(1, 98, "Variante (V)")
    s.line([(cells[2] + 40, 34), (cells[2] + 140, 34)], dash=DASH)
    s.line([(cells[2] + 40, 62), (cells[2] + 140, 62)])
    s.text(cells[2] + 90, 98, "dependência opcional (tracejada)\ne obrigatória (contínua)", size=11)
    s.line([(cells[3] + 90, 14), (cells[3] + 50, 50)], dash=DASH)
    s.line([(cells[3] + 90, 14), (cells[3] + 130, 50)], dash=DASH)
    alt_arc(s, cells[3] + 90, 14, "[min..max]", r=20, lxy=(cells[3] + 140, 40))
    caption(3, 98, "escolha alternativa")
    # linha 2
    s.line([(cells[0] + 30, 150), (cells[0] + 150, 150)], dash=DOT, arrow="open")
    s.text(cells[0] + 90, 190, "dependência de artefato", size=11)
    s.line([(cells[1] + 30, 150), (cells[1] + 150, 150)], dash=DASHDOT, arrow="open")
    s.text(cells[1] + 90, 190, "dependência de artefato\nde um VP", size=11)
    s.line([(cells[2] + 30, 160), (cells[2] + 150, 160)], dash=DOT, arrow="open")
    s.text(cells[2] + 90, 146, "requires_v_v", size=10, italic=True)
    s.text(cells[2] + 90, 190, "restrição: a variante de\norigem requer a de destino", size=11)
    s.text(cells[3] + 90, 150, "[0..1]  [1..1]  [0..2]", size=12)
    s.text(cells[3] + 90, 190, "cardinalidade: quantas\nvariantes escolher", size=11)
    s.save("legenda.svg")


if __name__ == "__main__":
    for fn in (features, camadas, componentes, microservices, legenda):
        fn()
        print("gerado:", fn.__name__)
