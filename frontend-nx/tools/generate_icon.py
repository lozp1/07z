# -*- coding: utf-8 -*-
"""
Genera el icono 256x256 de la app Switch '07z' (frontend del port de FIFA 07)
y el logo in-app  resources/romfs/img/07z_logo.png.

Diseno pedido por el usuario:
  - Texto exacto: '07z'  -> la z en MINUSCULA (nada de '07Z').
  - Tipografia: MISMA FAMILIA que el logo del juego FIFA 07 -> sans-serif
    BOLD, CONDENSADA y RECTA (estilo Helvetica/Arial Black condensada).
    SIN cursiva, SIN inclinacion, SIN adornos.
  - '07z' en ROJO (#E4002B) sobre fondo oscuro casi negro.
  - Forma squircle (estilo icono nativo de Switch / Horizon OS).

No depende de numpy: solo Pillow (ImageDraw/ImageFont/ImageFilter/ImageChops).

Salida:
  - icon.jpg      256x256 (JPEG, lo consume elf2nro via CMakeLists --icon=)
  - icon-256.png  256x256 (PNG)
  - resources/romfs/img/07z_logo.png  (512x512, logo del splash / Acerca de)

Uso:  python tools/generate_icon.py
"""

import os
import math
from PIL import Image, ImageDraw, ImageFilter, ImageFont, ImageChops

# ---------------------------------------------------------------- rutas
HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
OUT_JPG  = os.path.join(ROOT, "icon.jpg")
OUT_PNG  = os.path.join(ROOT, "icon-256.png")
OUT_LOGO = os.path.join(ROOT, "resources", "romfs", "img", "07z_logo.png")

# ---------------------------------------------------------------- fuentes
WIN_FONTS = r"C:\Windows\Fonts"
BAHNSCHRIFT = os.path.join(WIN_FONTS, "bahnschrift.ttf")  # variable: bold+condensed
ARIAL_BLACK = os.path.join(WIN_FONTS, "ariblk.ttf")       # muy gruesa (se condensa)
IMPACT      = os.path.join(WIN_FONTS, "impact.ttf")       # gruesa y condensada
INTER       = os.path.join(ROOT, "resources", "romfs", "fonts", "Inter.ttf")

# ---------------------------------------------------------------- paleta FIFA 07
BG_DEEP  = (0x03, 0x04, 0x06)   # negro casi puro
BG_TOP   = (0x16, 0x17, 0x1B)   # grafito (arriba del degradado)
RED_HI   = (0xFF, 0x33, 0x45)   # rojo luminoso (bisel superior)
RED_MAIN = (0xE4, 0x00, 0x2B)   # rojo principal del logo
RED_DEEP = (0xA8, 0x08, 0x20)   # rojo oscuro (base del degradado)

TEXT = "07z"                    # <- z en minuscula, obligatorio

S = 1024                        # lienzo de trabajo (supersampling 4x -> 256)
F = S // 256

_FONT_INFO = {"name": "?"}


def lerp(a, b, t):
    return tuple(int(round(a[i] + (b[i] - a[i]) * t)) for i in range(3))


def vgrad(size, c_top, c_bot):
    """Degradado vertical puro (sin numpy)."""
    w, h = size
    strip = Image.new("RGB", (1, h))
    px = strip.load()
    for y in range(h):
        px[0, y] = lerp(c_top, c_bot, y / max(h - 1, 1))
    return strip.resize((w, h), Image.BILINEAR)


def squircle_mask(size, n=5.0, margin=0):
    """Mascara de superelipse |x|^n+|y|^n<=1 (squircle tipo icono de Switch)."""
    m = Image.new("L", (size, size), 0)
    d = ImageDraw.Draw(m)
    half = size / 2.0 - margin
    c = size / 2.0
    pts = []
    steps = 1440
    for i in range(steps):
        t = 2.0 * math.pi * i / steps
        ct, st = math.cos(t), math.sin(t)
        x = math.copysign(abs(ct) ** (2.0 / n), ct)
        y = math.copysign(abs(st) ** (2.0 / n), st)
        pts.append((c + x * half, c + y * half))
    d.polygon(pts, fill=255)
    return m


def radial_bright(size):
    """Radial: blanco en el centro -> negro en el borde (glow/vineta)."""
    g = Image.radial_gradient("L").resize((size, size), Image.BILINEAR)
    return Image.eval(g, lambda v: 255 - v)       # invertido: brillante en el centro


def load_text_font(size):
    """Devuelve (fuente, factor_condensado). Prioriza una sans BOLD CONDENSADA."""
    if os.path.exists(BAHNSCHRIFT):
        try:
            f = ImageFont.truetype(BAHNSCHRIFT, size)
            for name in ("Bold Condensed", "SemiBold Condensed",
                         "Bold SemiCondensed", "Bold"):
                try:
                    f.set_variation_by_name(name)
                    _FONT_INFO["name"] = "Bahnschrift/" + name
                    return f, 1.0
                except Exception:
                    pass
            try:
                f.set_variation_by_axes([700, 75])   # (wght, wdth)
                _FONT_INFO["name"] = "Bahnschrift/Bold Condensed(axes)"
                return f, 1.0
            except Exception:
                pass
        except Exception:
            pass
    if os.path.exists(ARIAL_BLACK):
        try:
            _FONT_INFO["name"] = "Arial Black (condensada 0.80)"
            return ImageFont.truetype(ARIAL_BLACK, size), 0.80
        except Exception:
            pass
    if os.path.exists(IMPACT):
        try:
            _FONT_INFO["name"] = "Impact"
            return ImageFont.truetype(IMPACT, size), 0.94
        except Exception:
            pass
    _FONT_INFO["name"] = "Inter (fallback)"
    return ImageFont.truetype(INTER, size), 0.86


def render_text_mask(text, target_w, target_h):
    """Mascara L (SxS) con 'text' centrado, condensado y RECTO (sin inclinar)."""
    font, cond = load_text_font(420)
    canvas = Image.new("L", (S, S), 0)
    d = ImageDraw.Draw(canvas)
    bx = font.getbbox(text)
    x = (S - (bx[2] - bx[0])) / 2.0 - bx[0]
    y = (S - (bx[3] - bx[1])) / 2.0 - bx[1]
    d.text((x, y), text, font=font, fill=255)

    b = canvas.getbbox()
    if b is None:
        return canvas
    crop = canvas.crop(b)
    # Condensar (deformar en horizontal) SIN inclinar -> sigue siendo recto.
    new_w = max(1, int(round(crop.size[0] * cond)))
    crop = crop.resize((new_w, crop.size[1]), Image.LANCZOS)
    # Ajustar al tamano objetivo (maximo) conservando la proporcion.
    scale = min(target_w / crop.size[0], target_h / crop.size[1])
    if scale != 1.0:
        crop = crop.resize((max(1, int(round(crop.size[0] * scale))),
                            max(1, int(round(crop.size[1] * scale)))), Image.LANCZOS)

    out = Image.new("L", (S, S), 0)
    out.paste(crop, ((S - crop.size[0]) // 2, (S - crop.size[1]) // 2))
    return out


# =====================================================================
# 1. Fondo: degradado grafito -> negro + halo rojo + vineta
# =====================================================================
base = vgrad((S, S), BG_TOP, BG_DEEP).convert("RGBA")

glow = radial_bright(S).point(lambda v: int(v * 0.32))
glow = glow.filter(ImageFilter.GaussianBlur(S * 0.05))
red_layer = Image.new("RGBA", (S, S), RED_DEEP + (255,))
red_layer.putalpha(glow)
base = Image.alpha_composite(base, red_layer)

vig = radial_bright(S).point(lambda v: int((255 - v) * 0.88))
dark = Image.new("RGBA", (S, S), BG_DEEP + (255,))
dark.putalpha(vig)
base = Image.alpha_composite(base, dark)

# =====================================================================
# 2. Texto '07z' (BOLD CONDENSADA RECTA) -> glow rojo + sombra + relleno
# =====================================================================
mask = render_text_mask(TEXT, target_w=S * 0.80, target_h=S * 0.40)

# glow rojo suave detras del texto
tglow = Image.new("RGBA", (S, S), RED_MAIN + (255,))
tglow.putalpha(mask.point(lambda v: int(v * 0.85)))
tglow = tglow.filter(ImageFilter.GaussianBlur(26 * F))
base = Image.alpha_composite(base, tglow)

# sombra dura (profundidad), ligeramente desplazada
sh = Image.new("RGBA", (S, S), (0, 0, 0, 255))
sh.putalpha(mask.point(lambda v: int(v * 0.6)))
sh = sh.transform((S, S), Image.AFFINE, (1, 0, 4 * F, 0, 1, 6 * F), resample=Image.BICUBIC)
sh = sh.filter(ImageFilter.GaussianBlur(4 * F))
base = Image.alpha_composite(base, sh)

# relleno: rojo luminoso arriba -> rojo oscuro abajo
fill = vgrad((S, S), RED_HI, RED_DEEP)
txt = Image.new("RGBA", (S, S), (0, 0, 0, 0))
txt.paste(fill, (0, 0), mask)
base = Image.alpha_composite(base, txt)

# =====================================================================
# 3. Squircle (recorte) + brillo superior   (SIN aro rojo perimetral)
# =====================================================================
# El borde/halo ROJO exterior se ha eliminado por peticion del usuario: antes se
# pintaba un anillo rojo justo por dentro del contorno del squircle
# (ring = square - inner_m), que es lo que se veia como "aro rojo" alrededor del
# icono. Ahora el contorno queda limpio: fondo oscuro + texto 07z en rojo con su
# sombra sutil, sin aro perimetral.
square = squircle_mask(S, n=5.0, margin=6 * F)
fg = base.copy()

# brillo superior (sheen)
sheen = Image.new("RGBA", (S, S), (0, 0, 0, 0))
ImageDraw.Draw(sheen).arc([18 * F, 18 * F, S - 18 * F, S - 18 * F],
                          start=-100, end=-25, fill=(255, 255, 255, 70), width=5 * F)
sheen = sheen.filter(ImageFilter.GaussianBlur(9 * F))
fg = Image.alpha_composite(fg, sheen)

# =====================================================================
# 4. Composicion final: recorte squircle sobre fondo negro -> RGB
# =====================================================================
out = Image.new("RGBA", (S, S), BG_DEEP + (255,))
out.paste(fg, (0, 0), square)

final = out.convert("RGB").resize((256, 256), Image.LANCZOS)
final.save(OUT_PNG, "PNG", optimize=True)
final.save(OUT_JPG, "JPEG", quality=95, subsampling=0, optimize=True)

# Logo in-app (splash / Acerca de): mismo diseno a 512x512.
logo = out.convert("RGB").resize((512, 512), Image.LANCZOS)
logo.save(OUT_LOGO, "PNG", optimize=True)

print("ok", final.size, final.mode, "| texto", TEXT,
      "| fuente", _FONT_INFO["name"], "| rojo #%02X%02X%02X" % RED_MAIN)
print("salidas:", OUT_JPG, OUT_PNG, OUT_LOGO)
