#!/usr/bin/env python3
"""Gera os cards de notícia do FastGrid para o Instagram (1080x1350, JPEG).

Uso:
    python3 noticias/gerar_cards.py post.json

Formato do JSON:
{
  "tipo": "semanal" | "urgente",
  "pasta": "noticias/posts/2026-11-16_semanal",   # onde salvar os JPEGs
  "periodo": "9 a 15 de novembro",                 # só no semanal (capa)
  "gancho": "Frase de impacto da capa (F1)",       # só no semanal (capa)
  "noticias": [
    {"categoria": "F1", "titulo": "...", "resumo": "...", "fonte": "Motorsport.com"}
  ]
}

Semanal  -> 01_capa.jpg, 02..NN (um card por notícia), último card de chamada.
Urgente  -> 01_urgente.jpg (um card só com a primeira notícia).

Sessão de GP (treino, sprint, classificação, corrida) -> tipo "sessao":
{
  "tipo": "sessao",
  "pasta": "noticias/gp/2026-las-vegas/03_tl3",
  "gp": "GP de Las Vegas",
  "sessao": "Treino Livre 3",          # título grande da capa
  "sigla": "TL3",                      # TL1 TL2 TL3 SQ SPRINT CLASSIF CORRIDA
  "eh_corrida": false,                 # true na corrida e na sprint (capa "PÓDIO", tabela "RESULTADO")
  "eh_classificacao": false,           # true na classificação e na sprint quali (tabela "GRID DE LARGADA")
  "gancho": "Frase curta da capa",
  "resultado": [                       # todos os carros, na ordem oficial
    {"pos": 1, "piloto": "Lando Norris", "equipe": "McLaren", "tempo": "1:33.456"},
    {"pos": 2, "piloto": "Gabriel Bortoleto", "equipe": "Audi", "tempo": "+0.123", "br": true},
    {"pos": "NC", "piloto": "...", "equipe": "...", "tempo": "Abandono"}
  ],
  "nota_tabela": "Opcional: punições, etc. (aparece embaixo da última tabela)",
  "destaques": ["2 a 4 frases curtas"],
  "pergunta": "Pergunta do card final",
  "fonte": "Formula1.com / FIA"
}
Sessão -> 01_capa.jpg, 02/03_tabela.jpg (até 11 pilotos por card), destaques, final.
"""
import json
import os
import sys

from PIL import Image, ImageDraw, ImageFont

W, H = 1080, 1350
PRETO = (10, 10, 10)
CINZA = (28, 28, 28)
VERMELHO = (225, 6, 0)
BRANCO = (255, 255, 255)
TEXTO2 = (205, 205, 205)
MARGEM = 80
HANDLE = "@fast_grid"  # perfil do Instagram

FONT_DIRS = ["/usr/share/fonts/opentype/inter", "/usr/share/fonts/truetype/dejavu"]
FONTES = {
    "black": ["InterDisplay-Black.otf", "Inter-Black.otf", "DejaVuSans-Bold.ttf"],
    "bold": ["Inter-Bold.otf", "DejaVuSans-Bold.ttf"],
    "semi": ["Inter-SemiBold.otf", "DejaVuSans.ttf"],
    "regular": ["Inter-Regular.otf", "DejaVuSans.ttf"],
    "italic": ["InterDisplay-BlackItalic.otf", "Inter-BlackItalic.otf", "DejaVuSans-BoldOblique.ttf"],
}


def fonte(peso, tamanho):
    for nome in FONTES[peso]:
        for d in FONT_DIRS:
            p = os.path.join(d, nome)
            if os.path.exists(p):
                return ImageFont.truetype(p, tamanho)
    return ImageFont.load_default(tamanho)


def quebrar(draw, texto, f, largura):
    linhas, atual = [], ""
    for palavra in texto.split():
        teste = (atual + " " + palavra).strip()
        if draw.textlength(teste, font=f) <= largura:
            atual = teste
        else:
            if atual:
                linhas.append(atual)
            atual = palavra
    if atual:
        linhas.append(atual)
    return linhas


def caber(draw, texto, peso, maior, menor, largura, max_linhas):
    """Escolhe o maior tamanho de fonte em que o texto cabe em max_linhas."""
    for t in range(maior, menor - 1, -4):
        f = fonte(peso, t)
        linhas = quebrar(draw, texto, f, largura)
        if len(linhas) <= max_linhas and all(draw.textlength(l, font=f) <= largura for l in linhas):
            return f, linhas, t
    f = fonte(peso, menor)
    linhas = quebrar(draw, texto, f, largura)[:max_linhas]
    linhas[-1] = linhas[-1].rstrip(".,;") + "…"
    return f, linhas, menor


def escrever(draw, x, y, linhas, f, cor, entre=1.12):
    tam = f.size
    for l in linhas:
        draw.text((x, y), l, font=f, fill=cor)
        y += int(tam * entre)
    return y


def base():
    img = Image.new("RGB", (W, H), PRETO)
    d = ImageDraw.Draw(img)
    # faixas diagonais de fundo (assinatura visual)
    for i in range(6):
        x0 = W - 380 + i * 70
        d.polygon([(x0, 0), (x0 + 30, 0), (x0 - 170, H), (x0 - 200, H)], fill=CINZA)
    d.rectangle([0, 0, W, 14], fill=VERMELHO)
    return img, d


def marca(d, y=H - 110):
    f = fonte("italic", 40)
    d.text((MARGEM, y), "FAST", font=f, fill=BRANCO)
    d.text((MARGEM + d.textlength("FAST ", font=f), y), "GRID", font=f, fill=VERMELHO)
    f2 = fonte("semi", 30)
    txt = HANDLE
    d.text((W - MARGEM - d.textlength(txt, font=f2), y + 8), txt, font=f2, fill=TEXTO2)


def tag(d, x, y, texto, cor=VERMELHO, tam=34):
    f = fonte("black", tam)
    w = d.textlength(texto, font=f)
    d.rectangle([x, y, x + w + 36, y + tam + 26], fill=cor)
    d.text((x + 18, y + 11), texto, font=f, fill=BRANCO)
    return y + tam + 26


def card_noticia(n, idx=None, total=None, urgente=False):
    img, d = base()
    y = 90
    if urgente:
        y = tag(d, MARGEM, y, "URGENTE", tam=44) + 24
        y = tag(d, MARGEM, y, n["categoria"].upper(), cor=(60, 60, 60), tam=32)
    else:
        y = tag(d, MARGEM, y, n["categoria"].upper())
        if idx is not None:
            f = fonte("bold", 32)
            t = f"{idx:02d}/{total:02d}"
            d.text((W - MARGEM - d.textlength(t, font=f), 100), t, font=f, fill=TEXTO2)
    y += 70
    largura = W - 2 * MARGEM
    f, linhas, t = caber(d, n["titulo"].upper(), "black", 96, 56, largura, 6)
    y = escrever(d, MARGEM, y, linhas, f, BRANCO, entre=1.05)
    y += 30
    d.rectangle([MARGEM, y, MARGEM + 140, y + 10], fill=VERMELHO)
    y += 50
    espaco = (H - 260) - y
    max_l = max(2, espaco // 52)
    f2, l2, _ = caber(d, n["resumo"], "regular", 42, 32, largura, max_l)
    escrever(d, MARGEM, y, l2, f2, TEXTO2, entre=1.3)
    if n.get("fonte"):
        f3 = fonte("semi", 28)
        d.text((MARGEM, H - 190), "Fonte: " + n["fonte"], font=f3, fill=(140, 140, 140))
    marca(d)
    return img


def card_capa(periodo, gancho, n_noticias):
    img, d = base()
    y = 110
    y = tag(d, MARGEM, y, "RESUMO DA SEMANA")
    y += 60
    f = fonte("black", 150)
    for l in ["A SEMANA", "NO GRID"]:
        d.text((MARGEM, y), l, font=f, fill=BRANCO)
        y += 160
    f = fonte("bold", 44)
    d.text((MARGEM, y + 40), periodo.upper(), font=f, fill=VERMELHO)
    y += 170
    largura = W - 2 * MARGEM
    f, linhas, _ = caber(d, gancho, "bold", 64, 44, largura, 4)
    y = escrever(d, MARGEM, y, linhas, f, BRANCO, entre=1.15)
    f = fonte("semi", 36)
    d.text((MARGEM, H - 220), f"{n_noticias} notícias  →  arrasta pro lado", font=f, fill=TEXTO2)
    marca(d)
    return img


def card_final():
    img, d = base()
    largura = W - 2 * MARGEM
    y = 380
    f, linhas, _ = caber(d, "QUAL FOI A MAIOR NOTÍCIA DA SEMANA?", "black", 110, 70, largura, 4)
    y = escrever(d, MARGEM, y, linhas, f, BRANCO, entre=1.05)
    y += 50
    f = fonte("bold", 50)
    d.text((MARGEM, y), "Comenta aí", font=f, fill=VERMELHO)
    y += 140
    f = fonte("semi", 40)
    d.text((MARGEM, y), f"Siga o {HANDLE} pra não perder", font=f, fill=TEXTO2)
    d.text((MARGEM, y + 56), "nada do automobilismo.", font=f, fill=TEXTO2)
    marca(d)
    return img


# ---------------------------------------------------------------------------
# Posts de fim de semana de GP (tipo "sessao")
# ---------------------------------------------------------------------------

CORES_EQUIPE = {
    "mclaren": (255, 128, 0),
    "ferrari": (220, 0, 40),
    "mercedes": (39, 244, 210),
    "red bull": (54, 113, 198),
    "racing bulls": (102, 146, 255),
    "aston martin": (34, 153, 113),
    "alpine": (0, 147, 204),
    "williams": (100, 196, 255),
    "haas": (182, 186, 189),
    "audi": (245, 70, 40),
    "cadillac": (200, 170, 100),
}
BR_FUNDO = (52, 8, 8)
LINHA_ALT = (20, 20, 20)


def cor_equipe(equipe):
    e = (equipe or "").lower()
    # "racing bulls" antes de "red bull"
    for chave in sorted(CORES_EQUIPE, key=len, reverse=True):
        if chave in e:
            return CORES_EQUIPE[chave]
    return (120, 120, 120)


def cabecalho_gp(d, gp, sigla, pagina=None):
    y = tag(d, MARGEM, 70, gp.upper(), tam=32)
    f = fonte("black", 32)
    x = MARGEM + d.textlength(gp.upper(), font=f) + 36 + 14
    tag(d, x, 70, sigla.upper(), cor=(60, 60, 60), tam=32)
    if pagina:
        f2 = fonte("bold", 30)
        d.text((W - MARGEM - d.textlength(pagina, font=f2), 82), pagina, font=f2, fill=TEXTO2)
    return y


def nome_curto(nome):
    partes = nome.split()
    return partes[-1].upper() if partes else nome.upper()


def card_sessao_capa(post):
    img, d = base()
    res = post["resultado"]
    y = cabecalho_gp(d, post["gp"], post["sigla"]) + 50
    largura = W - 2 * MARGEM
    f, linhas, _ = caber(d, post["sessao"].upper(), "black", 130, 80, largura, 2)
    y = escrever(d, MARGEM, y, linhas, f, BRANCO, entre=1.0)
    y += 20
    rotulo = "PÓDIO" if post.get("eh_corrida") else ("TOP 3" if not post.get("eh_classificacao") else "LARGAM NA FRENTE")
    frot = fonte("black", 34)
    d.text((MARGEM, y), rotulo, font=frot, fill=VERMELHO)
    xr = MARGEM + d.textlength(rotulo, font=frot) + 20
    d.rectangle([xr, y + 16, W - MARGEM, y + 20], fill=VERMELHO)
    y += 64
    for r in res[:3]:
        d.rectangle([MARGEM, y, W - MARGEM, y + 130], fill=CINZA)
        d.rectangle([MARGEM, y, MARGEM + 12, y + 130], fill=cor_equipe(r["equipe"]))
        fpos = fonte("black", 96)
        d.text((MARGEM + 40, y + 10), str(r["pos"]), font=fpos, fill=VERMELHO)
        fn = fonte("black", 58)
        d.text((MARGEM + 150, y + 14), r["piloto"].upper() if d.textlength(r["piloto"].upper(), font=fn) < 560 else nome_curto(r["piloto"]), font=fn, fill=BRANCO)
        fe = fonte("semi", 30)
        d.text((MARGEM + 152, y + 84), r["equipe"], font=fe, fill=TEXTO2)
        ft = fonte("bold", 36)
        t = r.get("tempo", "")
        d.text((W - MARGEM - 30 - d.textlength(t, font=ft), y + 80), t, font=ft, fill=BRANCO)
        y += 148
    y += 20
    espaco = H - 260 - y
    if post.get("gancho") and espaco > 60:
        f, linhas, _ = caber(d, post["gancho"], "bold", 46, 34, largura, max(1, espaco // 56))
        escrever(d, MARGEM, y, linhas, f, BRANCO, entre=1.18)
    f = fonte("semi", 32)
    d.text((MARGEM, H - 190), "Resultado completo  →  arrasta pro lado", font=f, fill=TEXTO2)
    marca(d)
    return img


def card_sessao_tabela(post, linhas_res, pagina, ultima=True):
    img, d = base()
    y = cabecalho_gp(d, post["gp"], post["sigla"], pagina) + 40
    titulo = post.get("titulo_tabela") or ("RESULTADO" if post.get("eh_corrida") else ("GRID DE LARGADA" if post.get("eh_classificacao") else "TEMPOS"))
    d.text((MARGEM, y), titulo, font=fonte("black", 72), fill=BRANCO)
    y += 96
    alt = 76
    for i, r in enumerate(linhas_res):
        br = r.get("br")
        fundo = BR_FUNDO if br else (LINHA_ALT if i % 2 == 0 else PRETO)
        d.rectangle([MARGEM - 20, y, W - MARGEM + 20, y + alt - 4], fill=fundo)
        fpos = fonte("black", 40)
        pos = str(r["pos"])
        d.text((MARGEM + 40 - d.textlength(pos, font=fpos) / 2, y + 14), pos, font=fpos,
               fill=VERMELHO if str(r["pos"]) in ("1", "2", "3") else BRANCO)
        d.rectangle([MARGEM + 90, y + 12, MARGEM + 98, y + alt - 16], fill=cor_equipe(r["equipe"]))
        fn = fonte("bold", 36)
        nome = r["piloto"]
        d.text((MARGEM + 118, y + 6), nome, font=fn, fill=BRANCO)
        fe = fonte("regular", 24)
        d.text((MARGEM + 119, y + 45), r["equipe"], font=fe, fill=(150, 150, 150))
        if br:
            fb = fonte("black", 22)
            xb = MARGEM + 118 + d.textlength(nome, font=fn) + 16
            d.rectangle([xb, y + 14, xb + 46, y + 42], fill=VERMELHO)
            d.text((xb + 8, y + 16), "BR", font=fb, fill=BRANCO)
        ft = fonte("semi", 34)
        t = r.get("tempo", "")
        d.text((W - MARGEM - d.textlength(t, font=ft), y + 16), t, font=ft, fill=BRANCO if t[:1] != "+" else TEXTO2)
        y += alt
    rodape = []
    if post.get("nota_tabela") and ultima:
        rodape.append(post["nota_tabela"])
    if post.get("fonte"):
        rodape.append("Fonte: " + post["fonte"])
    f = fonte("regular", 25)
    y += 12
    for txt in rodape:
        for l in quebrar(d, txt, f, W - 2 * MARGEM)[:2]:
            d.text((MARGEM, y), l, font=f, fill=(140, 140, 140))
            y += 32
    marca(d)
    return img


def card_sessao_destaques(post):
    img, d = base()
    y = cabecalho_gp(d, post["gp"], post["sigla"]) + 50
    d.text((MARGEM, y), "DESTAQUES", font=fonte("black", 96), fill=BRANCO)
    y += 140
    largura = W - 2 * MARGEM - 60
    itens = post["destaques"][:4]
    espaco_total = H - 280 - y
    por_item = espaco_total // max(1, len(itens))
    for txt in itens:
        d.rectangle([MARGEM, y + 14, MARGEM + 24, y + 38], fill=VERMELHO)
        max_l = max(1, (por_item - 30) // 56)
        f, linhas, t = caber(d, txt, "bold", 46, 32, largura, max_l)
        yy = escrever(d, MARGEM + 60, y, linhas, f, BRANCO, entre=1.2)
        y = max(yy + 34, y + 70)
    marca(d)
    return img


def card_sessao_final(post):
    img, d = base()
    largura = W - 2 * MARGEM
    y = 360
    f, linhas, _ = caber(d, post.get("pergunta", "O que você achou?").upper(), "black", 110, 66, largura, 5)
    y = escrever(d, MARGEM, y, linhas, f, BRANCO, entre=1.05)
    y += 50
    d.text((MARGEM, y), "Comenta aí", font=fonte("bold", 50), fill=VERMELHO)
    y += 140
    f = fonte("semi", 40)
    d.text((MARGEM, y), f"Siga o {HANDLE} pra acompanhar", font=f, fill=TEXTO2)
    d.text((MARGEM, y + 56), "o fim de semana inteiro.", font=f, fill=TEXTO2)
    marca(d)
    return img


def gerar_sessao(post, pasta):
    res = post["resultado"]
    if len(res) < 3 or not post.get("destaques"):
        sys.exit("A sessão precisa de pelo menos 3 linhas em resultado e de destaques.")
    saidas = [salvar(card_sessao_capa(post), pasta, "01_capa.jpg")]
    meio = (len(res) + 1) // 2 if len(res) > 11 else len(res)
    blocos = [res[:meio], res[meio:]] if meio < len(res) else [res]
    n = 2
    for b in blocos:
        pagina = f"{res.index(b[0]) + 1}–{res.index(b[-1]) + 1} de {len(res)}"
        saidas.append(salvar(card_sessao_tabela(post, b, pagina, b is blocos[-1]), pasta, f"{n:02d}_tabela.jpg"))
        n += 1
    saidas.append(salvar(card_sessao_destaques(post), pasta, f"{n:02d}_destaques.jpg"))
    n += 1
    saidas.append(salvar(card_sessao_final(post), pasta, f"{n:02d}_final.jpg"))
    return saidas


def salvar(img, pasta, nome):
    caminho = os.path.join(pasta, nome)
    img.save(caminho, "JPEG", quality=90, optimize=True)
    return caminho


def main():
    with open(sys.argv[1], encoding="utf-8") as fh:
        post = json.load(fh)
    pasta = post["pasta"]
    os.makedirs(pasta, exist_ok=True)
    noticias = post.get("noticias", [])
    saidas = []
    if post["tipo"] == "sessao":
        saidas = gerar_sessao(post, pasta)
    elif post["tipo"] == "urgente":
        saidas.append(salvar(card_noticia(noticias[0], urgente=True), pasta, "01_urgente.jpg"))
    else:
        if not 2 <= len(noticias) <= 8:
            sys.exit("O semanal precisa de 2 a 8 notícias (carrossel máx. 10 imagens).")
        saidas.append(salvar(card_capa(post["periodo"], post["gancho"], len(noticias)), pasta, "01_capa.jpg"))
        for i, n in enumerate(noticias, 1):
            saidas.append(salvar(card_noticia(n, i, len(noticias)), pasta, f"{i + 1:02d}_noticia.jpg"))
        saidas.append(salvar(card_final(), pasta, f"{len(noticias) + 2:02d}_final.jpg"))
    for s in saidas:
        print(s)


if __name__ == "__main__":
    main()
