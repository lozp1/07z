# -*- coding: utf-8 -*-
"""
Genera el DIAGRAMA DEL MANDO de la pantalla "Configuracion de mandos" del
frontend 07z a partir de una IMAGEN REAL de uso libre:

  Nintendo Switch Joy-Con Grip Controller.png
  Autor : Owen1962 (Wikimedia Commons)
  Licencia: dominio publico (PD-self) del autor; tambien ofrecida como
            CC-BY-SA-4.0 (licencia dual, se usa la opcion PD).
  Fuente: https://commons.wikimedia.org/wiki/File:Nintendo_Switch_Joy-Con_Grip_Controller.png
  Ver tambien: resources/romfs/img/controller_switch.LICENSE.txt

Es una vista FRONTAL recta de un par de Joy-Con en su grip, ya recortada y con
fondo transparente (tools/controller_source.png). El aspecto ~1.28:1 viene de la
propia foto; main_borealis.cpp DEBE usar las MISMAS kCtrlDiagramW/kCtrlDiagramH
para encajarla sin deformar.

Encima de la imagen, ya en tiempo de ejecucion, el C++ dibuja:
  * la TECLA ACTUAL de cada control (leida del fichero de teclas del juego), y
  * el RESALTE inset del control seleccionado (mismo estilo que el menu).

Salidas:
  resources/romfs/img/controller_switch.png   (imagen base con borde/rim, sin teclas)
  tools/preview_controller.png                (preview: base + teclas de ejemplo + resalte)

Uso:  python tools/generate_controller.py
"""

import os
from PIL import Image, ImageDraw, ImageFilter, ImageFont, ImageChops

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
SRC_PNG = os.path.join(HERE, "controller_source.png")
OUT_PNG = os.path.join(ROOT, "resources", "romfs", "img", "controller_switch.png")
OUT_PREVIEW = os.path.join(HERE, "preview_controller.png")
FONT_PATH = os.path.join(ROOT, "resources", "romfs", "fonts", "Inter.ttf")

# ------------------------------------------------------------------ lienzo
# Debe coincidir con kCtrlDiagramW / kCtrlDiagramH de main_borealis.cpp.
W, H = 1000, 782

ACCENT = (0, 242, 254)
KEY_TXT = (126, 233, 248)
PILL_BG = (8, 10, 14, 170)
RIM = (128, 146, 176)

# ------------------------------------------------------------------ imagen base
base = Image.open(SRC_PNG).convert("RGBA")
if base.size != (W, H):
    raise SystemExit("controller_source.png debe medir %dx%d, mide %s" % (W, H, base.size))

alpha = base.split()[3]
# Rim light: halo exterior suave + borde interior claro, para que la silueta
# (sobre todo las empunaduras negras del grip) se recorte sobre el fondo oscuro.
glow = alpha.filter(ImageFilter.GaussianBlur(5))
glow = ImageChops.subtract(glow, alpha)
glow = glow.point(lambda v: min(255, int(v * 0.75)))
inner = ImageChops.subtract(alpha, alpha.filter(ImageFilter.MinFilter(3)))
inner = inner.point(lambda v: min(255, int(v * 0.55)))

final = base.copy()
rim = Image.new("RGBA", (W, H), RIM + (255,))
final = Image.alpha_composite(final, Image.composite(rim, Image.new("RGBA", (W, H), (0, 0, 0, 0)), glow))
final = Image.alpha_composite(final, Image.composite(rim, Image.new("RGBA", (W, H), (0, 0, 0, 0)), inner))
final.save(OUT_PNG, "PNG", optimize=True)
print("PNG:", OUT_PNG, final.size)


# =====================================================================
# TABLA DE GEOMETRIA  (coordenadas medidas sobre la foto, lienzo 1000x782)
# ---------------------------------------------------------------------
#   align: 0 = centrado, 1 = izquierda, 2 = derecha
#   shape: 0 = rect (hx,hy,hw,hh)     1 = anillo (hx,hy = centro, hw = radio)
# =====================================================================
ELEMS = []


def E(control, lx, ly, align, shape, *hp):
    ELEMS.append((control, lx, ly, align, shape, hp))


# --- Stick izquierdo (250, 198) r=53 ... y su clic ---------------------------
E(18, 250.0, 198.0, 0, 1, 250, 198, 50)                       # STICKL
E(4,  250.0, 120.0, 0, 0, 230, 125, 40, 40)                   # LUP
E(5,  250.0, 272.0, 0, 0, 230, 231, 40, 40)                   # LDOWN
E(6,  183.0, 198.0, 2, 0, 177, 178, 40, 40)                   # LLEFT
E(7,  317.0, 198.0, 1, 0, 283, 178, 40, 40)                   # LRIGHT

# --- Cruceta (botones de direccion del Joy-Con izq: (250,402) r=52) ----------
E(0,  250.0, 308.0, 0, 1, 250, 350, 25)                       # UP
E(1,  250.0, 492.0, 0, 1, 250, 454, 25)                       # DOWN
E(2,  162.0, 402.0, 2, 1, 198, 402, 25)                       # LEFT
E(3,  338.0, 402.0, 1, 1, 302, 402, 25)                       # RIGHT

# --- Minus (315,88) ---------------------------------------------------------
E(17, 315.0, 52.0, 0, 1, 315, 88, 24)                         # MINUS

# --- Hombros izquierdos -----------------------------------------------------
E(14, 200.0, 24.0, 0, 0, 125, 4, 150, 40)                     # ZL
E(12, 200.0, 58.0, 0, 0, 125, 38, 150, 40)                    # L

# --- Hombros derechos -------------------------------------------------------
E(15, 770.0, 24.0, 0, 0, 695, 4, 150, 40)                     # ZR
E(13, 770.0, 58.0, 0, 0, 695, 38, 150, 40)                    # R

# --- Botones de cara (765,202) orbita 55 r=22 -------------------------------
E(10, 765.0, 109.0, 0, 1, 765, 147, 27)                       # X
E(9,  801.0, 257.0, 1, 1, 765, 257, 27)                       # B
E(11, 674.0, 202.0, 2, 1, 710, 202, 27)                       # Y
E(8,  856.0, 202.0, 1, 1, 820, 202, 27)                       # A

# --- Plus (708,90) ----------------------------------------------------------
E(16, 674.0, 90.0, 2, 1, 708, 90, 24)                         # PLUS

# --- Stick derecho (771, 402) r=65 ... y su clic -----------------------------
E(19, 771.0, 402.0, 0, 1, 771, 402, 62)                       # STICKR
E(20, 771.0, 317.0, 0, 0, 751, 317, 40, 40)                   # RUP
E(21, 771.0, 487.0, 0, 0, 751, 449, 40, 40)                   # RDOWN
E(22, 692.0, 402.0, 2, 0, 686, 382, 40, 40)                   # RLEFT
E(23, 850.0, 402.0, 1, 0, 816, 382, 40, 40)                   # RRIGHT

# ---- muestra de teclas (mapa activo recomendado) para la preview --------
SAMPLE = {
    0: "\u2191", 1: "\u2193", 2: "\u2190", 3: "\u2192",
    4: "\u2191", 5: "\u2193", 6: "\u2190", 7: "\u2192",
    8: "S", 9: "D", 10: "W", 11: "A",
    12: "MAY\u00daS", 13: "E", 14: "ESC", 15: "ESPACIO",
    16: "ESC", 17: "ENTER", 18: "Z", 19: "Q",
    20: "\u2191", 21: "\u2193", 22: "\u2190", 23: "\u2192",
}
HILITE = 15   # ZR resaltado en la preview


# =====================================================================
# PREVIEW  (emula lo que pinta el C++: resalte + etiqueta de tecla)
# =====================================================================
def load_font(px):
    return ImageFont.truetype(FONT_PATH, int(round(px)))


f_lab = load_font(22)
f_small = load_font(20)

prev = final.copy()
pd = ImageDraw.Draw(prev)

# resaltes primero (debajo del texto)
for (idx, lx, ly, align, shape, hp) in ELEMS:
    if idx != HILITE:
        continue
    if shape == 1:
        pd.ellipse([hp[0] - hp[2], hp[1] - hp[2], hp[0] + hp[2], hp[1] + hp[2]],
                   outline=ACCENT, width=3)
    else:
        pd.rounded_rectangle([hp[0], hp[1], hp[0] + hp[2], hp[1] + hp[3]],
                             radius=10, outline=ACCENT, width=3)

for (idx, lx, ly, align, shape, hp) in ELEMS:
    t = SAMPLE.get(idx, "")
    if not t:
        continue
    font = f_small if idx in (18, 19) else f_lab
    anchor = {0: "mm", 1: "lm", 2: "rm"}[align]
    bb = pd.textbbox((lx, ly), t, font=font, anchor=anchor)
    if idx == HILITE:
        pd.rounded_rectangle([bb[0] - 10, bb[1] - 5, bb[2] + 10, bb[3] + 5],
                             radius=8, fill=ACCENT)
        pd.text((lx, ly), t, font=font, fill=(6, 10, 12), anchor=anchor)
    else:
        pd.rounded_rectangle([bb[0] - 8, bb[1] - 4, bb[2] + 8, bb[3] + 4],
                             radius=7, fill=PILL_BG)
        pd.text((lx, ly), t, font=font, fill=KEY_TXT, anchor=anchor)

prev.convert("RGB").save(OUT_PREVIEW, "PNG", optimize=True)
print("PREVIEW:", OUT_PREVIEW)


# =====================================================================
# EMITIR LA TABLA C++
# =====================================================================
print("\n// ---- tabla de geometria del diagrama (generada por tools/generate_controller.py) ----")
print("struct CtrlDiagramElem {")
print("    int   control;                                  // indice en kControls")
print("    float lx, ly;                                   // anclaje de la etiqueta de tecla")
print("    int   align;                                    // 0=centro 1=izq 2=der")
print("    int   shape;                                    // 0=rect 1=anillo")
print("    float hx, hy, hw, hh;                           // rect o (centro, radio)")
print("};")
print("static const CtrlDiagramElem kCtrlDiagram[] = {")
for (i, lx, ly, al, sh, hp) in ELEMS:
    if sh == 0:
        hs = "%.0f, %.0f, %.0f, %.0f" % (hp[0], hp[1], hp[2], hp[3])
    else:
        hs = "%.0f, %.0f, %.0f, 0" % (hp[0], hp[1], hp[2])
    print("    { %2d, %6.1f, %6.1f, %d, %d, %s }," % (i, lx, ly, al, sh, hs))
print("};")
print("static const int kCtrlDiagramCount = (int)(sizeof(kCtrlDiagram) / sizeof(kCtrlDiagram[0]));")
print("static const float kCtrlDiagramW = %.0f.0f;" % W)
print("static const float kCtrlDiagramH = %.0f.0f;" % H)
