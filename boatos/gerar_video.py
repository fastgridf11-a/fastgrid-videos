#!/usr/bin/env python3
"""Gera o vídeo vertical (1080x1920, 30 fps) do quadro "Boatos no GP".

Uso:
    python3 boatos/gerar_video.py boatos/AAAA-MM-DD/video.json narracao.mp3 saida.mp4

video.json:
{
  "periodo": "Semana de 13 a 19/nov",
  "gancho": "Treta em Las Vegas e MotoGP com match point",
  "blocos": [
    {"tipo": "abertura", "fim": 5.2},
    {"selo": "CONFIRMADO", "categoria": "F1", "titulo": "...", "apoio": "...", "fim": 19.0},
    ...
    {"tipo": "final", "titulo": "BEARMAN FICA NA HAAS?", "fim": 82.4}
  ]
}
"fim" = segundo da narração em que o bloco termina (o início é o fim do anterior).
Identidade: a mesma de noticias/gerar_cards.py (preto, faixas diagonais cinza,
barra vermelha no topo, Inter, FAST GRID e @fast_grid).
"""
import json
import math
import os
import subprocess
import sys
import tempfile

from PIL import Image, ImageDraw, ImageFont

W, H, FPS = 1080, 1920, 30
PRETO = (10, 10, 10)
CINZA = (28, 28, 28)
VERMELHO = (225, 6, 0)
BRANCO = (255, 255, 255)
TEXTO2 = (205, 205, 205)
MARGEM = 80
HANDLE = "@fast_grid"
SELOS = {
    "CONFIRMADO": ((22, 163, 74), BRANCO),
    "BOATO": (VERMELHO, BRANCO),
    "OPINIÃO": (BRANCO, PRETO),
}
FONT_DIR = "/usr/share/fonts/opentype/inter"
FONTES = {
    "black": "InterDisplay-Black.otf",
    "bold": "Inter-Bold.otf",
    "semi": "Inter-SemiBold.otf",
    "regular": "Inter-Regular.otf",
    "italic": "InterDisplay-BlackItalic.otf",
}
_cache = {}


def fonte(peso, tam):
    k = (peso, tam)
    if k not in _cache:
        _cache[k] = ImageFont.truetype(os.path.join(FONT_DIR, FONTES[peso]), tam)
    return _cache[k]


def quebrar(d, texto, f, largura):
    linhas, atual = [], ""
    for p in texto.split():
        t = (atual + " " + p).strip()
        if d.textlength(t, font=f) <= largura:
            atual = t
        else:
            if atual:
                linhas.append(atual)
            atual = p
    if atual:
        linhas.append(atual)
    return linhas


def caber(d, texto, peso, maior, menor, largura, max_linhas):
    for t in range(maior, menor - 1, -4):
        f = fonte(peso, t)
        l = quebrar(d, texto, f, largura)
        if len(l) <= max_linhas:
            return f, l
    f = fonte(peso, menor)
    return f, quebrar(d, texto, f, largura)


def ease(x):
    x = max(0.0, min(1.0, x))
    return 1 - (1 - x) ** 3


def texto_rgba(linha, f, cor):
    d0 = ImageDraw.Draw(Image.new("RGBA", (1, 1)))
    w = int(d0.textlength(linha, font=f)) + 20
    h = int(f.size * 1.3)
    im = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    ImageDraw.Draw(im).text((0, 0), linha, font=f, fill=cor + (255,))
    return im


def com_alpha(im, a):
    if a >= 1:
        return im
    r, g, b, al = im.split()
    al = al.point(lambda v: int(v * a))
    return Image.merge("RGBA", (r, g, b, al))


def fundo(t):
    img = Image.new("RGB", (W, H), PRETO)
    d = ImageDraw.Draw(img)
    desl = (t * 18) % 70
    for i in range(-1, 7):
        x0 = W - 420 + i * 70 + desl
        d.polygon([(x0, 0), (x0 + 30, 0), (x0 - 300, H), (x0 - 330, H)], fill=CINZA)
    d.rectangle([0, 0, W, 16], fill=VERMELHO)
    # marca no topo (fora da área coberta pela interface do Reels/TikTok)
    f = fonte("italic", 46)
    d.text((MARGEM, 70), "FAST", font=f, fill=BRANCO)
    d.text((MARGEM + d.textlength("FAST ", font=f), 70), "GRID", font=f, fill=VERMELHO)
    f2 = fonte("semi", 32)
    d.text((W - MARGEM - d.textlength(HANDLE, font=f2), 80), HANDLE, font=f2, fill=TEXTO2)
    return img, d


def selo_img(texto, tam=92):
    fundo_c, txt_c = SELOS[texto]
    f = fonte("black", tam)
    d0 = ImageDraw.Draw(Image.new("RGBA", (1, 1)))
    w = int(d0.textlength(texto, font=f)) + 90
    h = tam + 64
    im = Image.new("RGBA", (w + 20, h + 20), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    d.rounded_rectangle([10, 10, 10 + w, 10 + h], radius=18, fill=fundo_c + (255,))
    d.rounded_rectangle([22, 22, w - 2, h - 2], radius=12, outline=txt_c + (255,), width=5)
    d.text((10 + 45, 10 + 22), texto, font=f, fill=txt_c + (255,))
    return im


def wipe(img, t):
    """Faixa vermelha diagonal que cruza a tela na abertura de cada bloco."""
    p = t / 0.35
    if p >= 1:
        return
    d = ImageDraw.Draw(img)
    x = -600 + p * (W + 1200)
    d.polygon([(x, 0), (x + 260, 0), (x - 340, H), (x - 600, H)], fill=VERMELHO)


def barra_progresso(d, tg, total):
    y = 1530
    d.rectangle([MARGEM, y, W - MARGEM, y + 8], fill=(45, 45, 45))
    d.rectangle([MARGEM, y, MARGEM + int((W - 2 * MARGEM) * min(1, tg / total)), y + 8], fill=VERMELHO)


class Bloco:
    def __init__(self, b, idx, n_itens, cfg):
        self.b, self.idx, self.n, self.cfg = b, idx, n_itens, cfg
        d = ImageDraw.Draw(Image.new("RGB", (W, H)))
        larg = W - 2 * MARGEM
        tipo = b.get("tipo", "item")
        self.tipo = tipo
        if tipo == "item":
            self.selo = selo_img(b["selo"])
            f, linhas = caber(d, b["titulo"].upper(), "black", 120, 70, larg, 4)
            self.titulo = [texto_rgba(l, f, BRANCO) for l in linhas]
            self.passo = int(f.size * 1.04)
            f2, l2 = caber(d, b.get("apoio", ""), "semi", 56, 40, larg, 4)
            self.apoio = [texto_rgba(l, f2, TEXTO2) for l in l2]
            self.passo2 = int(f2.size * 1.3)
        elif tipo == "abertura":
            self.titulo = [texto_rgba(l, fonte("black", 190), BRANCO) for l in ["BOATOS", "NO GP"]]
            self.passo = 196
            f2, l2 = caber(d, cfg.get("gancho", ""), "bold", 60, 44, larg, 3)
            self.apoio = [texto_rgba(l, f2, BRANCO) for l in l2]
            self.passo2 = int(f2.size * 1.2)
            self.selos = [selo_img(s, 44) for s in SELOS]
        else:  # final
            f, linhas = caber(d, b["titulo"].upper(), "black", 130, 80, larg, 4)
            self.titulo = [texto_rgba(l, f, BRANCO) for l in linhas]
            self.passo = int(f.size * 1.04)

    def frame(self, t, tg, total):
        img, d = fundo(tg)
        if self.tipo == "item":
            self._item(img, d, t)
        elif self.tipo == "abertura":
            self._abertura(img, d, t)
        else:
            self._final(img, d, t)
        barra_progresso(d, tg, total)
        wipe(img, t)
        return img

    def _cabecalho(self, img, d, t, y=240):
        a = ease(t / 0.3)
        f = fonte("black", 36)
        texto = "BOATOS NO GP"
        w = d.textlength(texto, font=f)
        d.rectangle([MARGEM, y, MARGEM + w + 36, y + 62], fill=VERMELHO)
        d.text((MARGEM + 18, y + 11), texto, font=f, fill=BRANCO)
        cat = self.b.get("categoria", "").upper()
        if cat:
            x = MARGEM + w + 56
            wc = d.textlength(cat, font=f)
            d.rectangle([x, y, x + wc + 36, y + 62], fill=(60, 60, 60))
            d.text((x + 18, y + 11), cat, font=f, fill=BRANCO)
        f3 = fonte("bold", 40)
        c = f"{self.idx:02d}/{self.n:02d}"
        d.text((W - MARGEM - d.textlength(c, font=f3), y + 10), c, font=f3, fill=TEXTO2)

    def _item(self, img, d, t):
        # número grande do item, discreto, no rodapé
        fn = fonte("black", 380)
        num = f"{self.idx:02d}"
        d.text((W - MARGEM + 30 - d.textlength(num, font=fn), 1090), num, font=fn, fill=(36, 36, 36))
        self._cabecalho(img, d, t)
        # selo: carimbo que entra grande e assenta com leve rotação
        p = ease((t - 0.15) / 0.28)
        if t > 0.15:
            esc = 1.7 - 0.7 * p
            ang = -6 + 3 * p
            s = self.selo.resize((int(self.selo.width * esc), int(self.selo.height * esc)), Image.LANCZOS)
            s = s.rotate(ang, expand=True, resample=Image.BICUBIC)
            s = com_alpha(s, min(1, p * 1.5))
            cx, cy = MARGEM + self.selo.width // 2, 470 + self.selo.height // 2
            img.paste(s, (int(cx - s.width / 2), int(cy - s.height / 2)), s)
        y = 690
        for i, li in enumerate(self.titulo):
            q = ease((t - 0.45 - i * 0.09) / 0.35)
            if q > 0:
                img.paste(com_alpha(li, q), (MARGEM, int(y + (1 - q) * 50)), com_alpha(li, q))
            y += self.passo
        y += 24
        q = ease((t - 0.8) / 0.4)
        d.rectangle([MARGEM, y, MARGEM + int(160 * q), y + 12], fill=VERMELHO)
        y += 56
        for i, li in enumerate(self.apoio):
            q = ease((t - 1.0 - i * 0.1) / 0.4)
            if q > 0:
                im = com_alpha(li, q)
                img.paste(im, (MARGEM + int((1 - q) * 40), y), im)
            y += self.passo2

    def _abertura(self, img, d, t):
        y = 400
        for i, li in enumerate(self.titulo):
            q = ease((t - 0.1 - i * 0.15) / 0.4)
            if q > 0:
                im = com_alpha(li, q)
                img.paste(im, (MARGEM - int((1 - q) * 120), y), im)
            y += self.passo
        q = ease((t - 0.5) / 0.4)
        f = fonte("bold", 46)
        d.text((MARGEM, y + 40), self.cfg.get("periodo", "").upper(), font=f, fill=VERMELHO)
        d.rectangle([MARGEM, y + 120, MARGEM + int(200 * q), y + 132], fill=VERMELHO)
        y += 190
        for i, li in enumerate(self.apoio):
            q = ease((t - 0.8 - i * 0.1) / 0.4)
            if q > 0:
                im = com_alpha(li, q)
                img.paste(im, (MARGEM, y), im)
            y += self.passo2
        y += 60
        x = MARGEM
        for i, s in enumerate(self.selos):
            q = ease((t - 1.4 - i * 0.25) / 0.3)
            if q > 0:
                im = com_alpha(s, q)
                img.paste(im, (x, int(y + (1 - q) * 30)), im)
            x += s.width + 6

    def _final(self, img, d, t):
        y = 560
        for i, li in enumerate(self.titulo):
            q = ease((t - 0.1 - i * 0.1) / 0.35)
            if q > 0:
                im = com_alpha(li, q)
                img.paste(im, (MARGEM, int(y + (1 - q) * 60)), im)
            y += self.passo
        y += 40
        q = ease((t - 0.6) / 0.4)
        f = fonte("black", 72)
        if q > 0:
            d.text((MARGEM, y), "COMENTA AÍ", font=f, fill=VERMELHO)
        y += 140
        q2 = ease((t - 1.0) / 0.4)
        if q2 > 0:
            f2 = fonte("bold", 50)
            d.text((MARGEM, y), "Segue o @fast_grid", font=f2, fill=BRANCO)
            d.text((MARGEM, y + 70), "pra não perder nada!", font=f2, fill=TEXTO2)


def render_bloco(bloco, ini, fim, total, saida):
    n = round((fim - ini) * FPS)
    tmp = saida[:-4] + ".tmp.mp4"
    cmd = ["ffmpeg", "-y", "-loglevel", "error", "-f", "rawvideo", "-pix_fmt", "rgb24",
           "-s", f"{W}x{H}", "-r", str(FPS), "-i", "-", "-c:v", "libx264", "-crf", "18",
           "-preset", "veryfast", "-pix_fmt", "yuv420p", tmp]
    p = subprocess.Popen(cmd, stdin=subprocess.PIPE)
    for k in range(n):
        t = k / FPS
        p.stdin.write(bloco.frame(t, ini + t, total).tobytes())
    p.stdin.close()
    if p.wait() != 0:
        raise SystemExit("ffmpeg falhou em " + saida)
    os.replace(tmp, saida)
    return n


def montar(cfg, audio, saida, so_frames=None):
    blocos = cfg["blocos"]
    total = blocos[-1]["fim"]
    n_itens = sum(1 for b in blocos if b.get("tipo", "item") == "item")
    objs, idx = [], 0
    for b in blocos:
        if b.get("tipo", "item") == "item":
            idx += 1
        objs.append(Bloco(b, idx, n_itens, cfg))
    if so_frames:  # prévias: [(bloco, t), ...]
        for i, (bi, t) in enumerate(so_frames):
            ini = 0 if bi == 0 else blocos[bi - 1]["fim"]
            objs[bi].frame(t, ini + t, total).save(f"{so_frames_dir}/previa_{i:02d}.jpg", quality=90)
        return
    tmpd = tempfile.mkdtemp()
    arquivos, ini, quadros = [], 0.0, 0
    for i, (b, o) in enumerate(zip(blocos, objs)):
        # fronteiras em quadros inteiros para não acumular desvio
        fim_q = round(b["fim"] * FPS)
        ini_q = quadros
        arq = os.path.join(tmpd, f"cena_{i:02d}.mp4")
        render_bloco(o, ini_q / FPS, fim_q / FPS, total, arq)
        quadros = fim_q
        arquivos.append(arq)
        print(f"cena {i}: {ini_q / FPS:.2f}–{fim_q / FPS:.2f}s", flush=True)
    lista = os.path.join(tmpd, "lista.txt")
    with open(lista, "w") as fh:
        fh.writelines(f"file '{a}'\n" for a in arquivos)
    mudo = os.path.join(tmpd, "mudo.mp4")
    subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-f", "concat", "-safe", "0", "-i", lista,
                    "-c", "copy", mudo], check=True)
    tmp = saida[:-4] + ".tmp.mp4"
    subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-i", mudo, "-i", audio, "-map", "0:v",
                    "-map", "1:a", "-c:v", "copy", "-c:a", "aac", "-b:a", "192k", "-shortest",
                    "-movflags", "+faststart", tmp], check=True)
    os.replace(tmp, saida)


so_frames_dir = "."

if __name__ == "__main__":
    cfg = json.load(open(sys.argv[1], encoding="utf-8"))
    if sys.argv[2] == "--previas":
        so_frames_dir = sys.argv[3]
        os.makedirs(so_frames_dir, exist_ok=True)
        pares = [(i, 2.5) for i in range(len(cfg["blocos"]))] + [(1, 0.3)]
        montar(cfg, None, None, so_frames=pares)
    else:
        montar(cfg, sys.argv[2], sys.argv[3])
