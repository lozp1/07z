# -*- coding: utf-8 -*-
"""
MAQUETA (mock) de la pantalla "Configuracion de mandos" a 1280x720, para
verificar el encaje del diagrama con el resto de la pantalla. NO es una captura
de la consola: reproduce a mano la composicion (cabecera, subtitulo, diagrama,
pista y barra de ayuda) con las MISMAS metricas y la MISMA tabla de geometria
que usa el C++.

Las filas de accion (FPS / guardar / recargar) ya NO estan en esta pantalla:
viven en la pantalla de Opciones, que se abre con [X] (asi el diagrama dispone
de toda la altura y el foco no puede escaparse del dibujo).

Uso: python tools/preview_screen_mock.py
Salida: tools/preview_screen_mock.png
"""
import os
import sys
from PIL import Image, ImageDraw, ImageFont

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
CTRL = os.path.join(ROOT, "resources", "romfs", "img", "controller_switch.png")
FONT = os.path.join(ROOT, "resources", "romfs", "fonts", "Inter.ttf")
OUT  = os.path.join(HERE, "preview_screen_mock.png")

W, H = 1280, 720
S = 2                      # supersampling del mock
ACCENT = (0, 242, 254)
TXT = (255, 255, 255)
DIS = (156, 163, 175)
BG = (10, 11, 13)
SEP = (40, 40, 45)

# --- misma tabla que kCtrlDiagram en main_borealis.cpp ----------------------
ELEMS = [
    (18, 250.0, 198.0, 0, 1, 250, 198, 50, 0),
    ( 4, 250.0, 120.0, 0, 0, 230, 125, 40, 40),
    ( 5, 250.0, 272.0, 0, 0, 230, 231, 40, 40),
    ( 6, 183.0, 198.0, 2, 0, 177, 178, 40, 40),
    ( 7, 317.0, 198.0, 1, 0, 283, 178, 40, 40),
    ( 0, 250.0, 308.0, 0, 1, 250, 350, 25, 0),
    ( 1, 250.0, 492.0, 0, 1, 250, 454, 25, 0),
    ( 2, 162.0, 402.0, 2, 1, 198, 402, 25, 0),
    ( 3, 338.0, 402.0, 1, 1, 302, 402, 25, 0),
    (17, 315.0,  52.0, 0, 1, 315,  88, 24, 0),
    (14, 200.0,  24.0, 0, 0, 125, 4, 150, 40),
    (12, 200.0,  58.0, 0, 0, 125, 38, 150, 40),
    (15, 770.0,  24.0, 0, 0, 695, 4, 150, 40),
    (13, 770.0,  58.0, 0, 0, 695, 38, 150, 40),
    (10, 765.0, 109.0, 0, 1, 765, 147, 27, 0),
    ( 9, 801.0, 257.0, 1, 1, 765, 257, 27, 0),
    (11, 674.0, 202.0, 2, 1, 710, 202, 27, 0),
    ( 8, 856.0, 202.0, 1, 1, 820, 202, 27, 0),
    (16, 674.0,  90.0, 2, 1, 708,  90, 24, 0),
    (19, 771.0, 402.0, 0, 1, 771, 402, 62, 0),
    (20, 771.0, 317.0, 0, 0, 751, 317, 40, 40),
    (21, 771.0, 487.0, 0, 0, 751, 449, 40, 40),
    (22, 692.0, 402.0, 2, 0, 686, 382, 40, 40),
    (23, 850.0, 402.0, 1, 0, 816, 382, 40, 40),
]
DIA_W, DIA_H = 1000.0, 782.0
KEYS = {18: "Z", 4: "\u2191", 5: "\u2193", 6: "\u2190", 7: "\u2192",
        0: "\u2191", 1: "\u2193", 2: "\u2190", 3: "\u2192", 17: "ENTER",
        14: "ESC", 12: "MAY\u00daS", 15: "ESPACIO", 13: "E",
        10: "W", 9: "D", 11: "A", 8: "S", 16: "ESC",
        19: "Q", 20: "\u2191", 21: "\u2193", 22: "\u2190", 23: "\u2192"}
SEL = 8               # boton A -> el resalte inset es un anillo bien visible
if len(sys.argv) > 1:   # opcional: control resaltado (util para revisar el resalte)
    SEL = int(sys.argv[1])
FONT_LAB_PX = 22.0    # misma base que usa el C++ (se multiplica por sc)

img = Image.new("RGB", (W * S, H * S), BG)
d = ImageDraw.Draw(img)
F = lambda px: ImageFont.truetype(FONT, max(6, int(round(px * S))))


def rr(x, y, w, h, r, fill, outline=None, width=1):
    d.rounded_rectangle([x * S, y * S, (x + w) * S, (y + h) * S], radius=r * S,
                        fill=fill, outline=outline, width=int(round(width * S)))


def text(x, y, s, font, fill, anchor="la"):
    d.text((x * S, y * S), s, font=font, fill=fill, anchor=anchor)


# --- fondo con veteado sutil (simula el wallpaper translucido) --------------
for y in range(0, H, 4):
    t = y / H
    c = (int(12 + 26 * t), int(14 + 30 * t), int(19 + 34 * t))
    d.rectangle([0, y * S, W * S, (y + 4) * S], fill=c)

PADL, PADR, PADT = 45, 45, 25
CX0 = PADL
CW = W - PADL - PADR

# --- cabecera: barra de acento + titulo + separador ------------------------
rr(CX0, PADT + 3, 4, 22, 2, ACCENT)
text(CX0 + 16, PADT + 3, "CONFIGURACIÓN DE MANDOS", F(24), TXT)
hdr_bottom = PADT + 3 + 29
d.rectangle([CX0 * S, (hdr_bottom + 12) * S, (CX0 + CW) * S, (hdr_bottom + 13) * S], fill=SEP)
y = hdr_bottom + 12 + 1 + 18

# --- subtitulo --------------------------------------------------------------
text(CX0, y, "FIFA 07 · Asigna los botones y teclas del juego", F(14), DIS)
y += 17 + 8

# --- area del diagrama: escalar como hace el C++ ---------------------------
nav_h = 16 + 4
help_h = 14 + 23
stage_h = (H - 20) - y - nav_h - help_h
sc = CW / DIA_W
if stage_h / DIA_H < sc:
    sc = stage_h / DIA_H
dw, dh = DIA_W * sc, DIA_H * sc
ox = CX0 + (CW - dw) / 2.0
oy = y + (stage_h - dh) / 2.0
print("stage_h=%.1f  sc=%.4f  dibujo=%.0fx%.0f  oy=%.1f  etiqueta=%.1fpx" %
      (stage_h, sc, dw, dh, oy, FONT_LAB_PX * sc))

ctrl = Image.open(CTRL).convert("RGBA").resize((int(round(dw * S)), int(round(dh * S))), Image.LANCZOS)
img.paste(ctrl, (int(round(ox * S)), int(round(oy * S))), ctrl)


def PX(v):  # design x -> mock px
    return (ox + v * sc) * S


def PY(v):  # design y -> mock px
    return (oy + v * sc) * S


star = int(round(3 * sc * S)) or 1
f_lab = F(FONT_LAB_PX * sc)
f_small = F(20 * sc)

# resalte del control seleccionado (debajo del texto)
for (idx, lx, ly, al, sh, hx, hy, hw, hh) in ELEMS:
    if idx != SEL:
        continue
    if sh == 1:
        d.ellipse([PX(hx - hw), PY(hy - hw), PX(hx + hw), PY(hy + hw)], outline=ACCENT, width=star)
    else:
        d.rounded_rectangle([PX(hx), PY(hy), PX(hx + hw), PY(hy + hh)],
                            radius=int(round(10 * sc * S)) or 1, outline=ACCENT, width=star)

for (idx, lx, ly, al, sh, hx, hy, hw, hh) in ELEMS:
    t = KEYS.get(idx, "")
    if not t:
        continue
    font = f_small if idx in (18, 19) else f_lab
    anchor = {0: "mm", 1: "lm", 2: "rm"}[al]
    px, py = PX(lx), PY(ly)
    bb = d.textbbox((px, py), t, font=font, anchor=anchor)
    if idx == SEL:
        d.rounded_rectangle([bb[0] - 10 * sc * S, bb[1] - 5 * sc * S, bb[2] + 10 * sc * S, bb[3] + 5 * sc * S],
                            radius=int(round(8 * sc * S)) or 1, fill=ACCENT)
        d.text((px, py), t, font=font, fill=(6, 10, 12), anchor=anchor)
    else:
        d.rounded_rectangle([bb[0] - 8 * sc * S, bb[1] - 4 * sc * S, bb[2] + 8 * sc * S, bb[3] + 4 * sc * S],
                            radius=int(round(7 * sc * S)) or 1, fill=(8, 10, 14))
        d.text((px, py), t, font=font, fill=(126, 233, 248), anchor=anchor)

y = y + stage_h + 4
text(W / 2, y, "Cruceta o stick: recorrer los botones  ·  A: asignar tecla  ·  X: opciones", F(13), DIS, anchor="ma")
y += nav_h

# --- barra de ayuda ---------------------------------------------------------
items = [("\u24b6", "Cambiar"), ("\u24b7", "Atr\u00e1s"), ("\u24cd", "Opciones")]
x = CX0
for g, t in items:
    text(x, y + 14, g, F(19), TXT)
    text(x + 24, y + 17, t, F(14), DIS)
    x += 24 + 26 + d.textbbox((0, 0), t, font=F(14))[2] / S + 20
info = "A  \u2192  S (0x53)"
bb = d.textbbox((0, 0), info, font=F(13))
text(CX0 + CW - (bb[2] - bb[0]) / S, y + 17, info, F(13), DIS)

img.resize((W, H), Image.LANCZOS).save(OUT, "PNG", optimize=True)
print("MOCK:", OUT)