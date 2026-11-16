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
        if len(linhas) <= max_linhas:
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


def salvar(img, pasta, nome):
    caminho = os.path.join(pasta, nome)
    img.save(caminho, "JPEG", quality=90, optimize=True)
    return caminho


def main():
    with open(sys.argv[1], encoding="utf-8") as fh:
        post = json.load(fh)
    pasta = post["pasta"]
    os.makedirs(pasta, exist_ok=True)
    noticias = post["noticias"]
    saidas = []
    if post["tipo"] == "urgente":
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
