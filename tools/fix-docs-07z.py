"""Ajustes de la documentacion de 07z verificados contra el estado real del port.

Corrige:
 1) la afirmacion 'setup-complete=1' (VERIFICADO: esa clave NO existe en el
    config/settings.json del port; el arranque directo se debe a
    run-the-chosen-program=true + reopen-the-launcher-on-exit=false + biblioteca fijada),
 2) el tamano de SD necesario (~250 MB era falso: el juego ocupa GB),
 3) ZR (es ESPACIO para avanzar, no 'reservado'),
 4) anade 'que se descarga' y el aviso de NO copiar bootloader/ ni emuMMC/.
"""
import os, re, shutil

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
os.chdir(REPO)

DOC = "docs/INSTALACION-07z.md"
RM = "dist/github-07z/README.md"
LEEME = "dist/github-07z/install/LEEME.txt"

def sub(path, old, new, n=1):
    t = open(path, encoding="utf-8").read()
    c = t.count(old)
    assert c == n, f"{path}: esperaba {n} ocurrencia(s), hay {c}:\n{old[:120]}"
    open(path, "w", encoding="utf-8", newline="").write(t.replace(old, new))
    print(f"  ok  {path}: {old.splitlines()[0][:70]}...")

# ---------- 1) setup-complete (dato falso) ----------
sub(DOC,
"""asistente de setup de Autorun. El `config/settings.json` que viene dentro de la
carpeta ya trae `setup-complete=1`, `run-the-chosen-program=true` y
`reopen-the-launcher-on-exit=false`, así que arranca directo.""",
"""asistente de setup de Autorun. El `config/settings.json` que viene dentro de la
carpeta ya trae `run-the-chosen-program=true` y
`reopen-the-launcher-on-exit=false`, con la biblioteca y el objetivo ya fijados
(`launcher.txt` / `target.txt`), así que arranca directo al juego.""")

sub(RM,
"""> La carpeta `fifa07` ya trae un `config/settings.json` con `setup-complete=1`,
> `run-the-chosen-program=true` y `reopen-the-launcher-on-exit=false`.""",
"""> La carpeta `fifa07` ya trae un `config/settings.json` con
> `run-the-chosen-program=true` y `reopen-the-launcher-on-exit=false`, y la
> biblioteca y el objetivo ya fijados (`launcher.txt` / `target.txt`).""")

sub(LEEME,
"""  overclock, ni pasar por el asistente de setup de Autorun: el
  config/settings.json que va dentro de la carpeta ya lleva todo lo
  necesario (setup-complete=1, run-the-chosen-program=true,
  reopen-the-launcher-on-exit=false).""",
"""  overclock, ni pasar por el asistente de setup de Autorun: el
  config/settings.json que va dentro de la carpeta ya lleva el arranque
  directo (run-the-chosen-program=true,
  reopen-the-launcher-on-exit=false) y la biblioteca y el objetivo fijados.""")

# ---------- 2) tamano de SD (~250 MB era falso) ----------
sub(DOC,
"- Una **tarjeta SD** con ~250 MB libres (runtime + frontend + tu copia del juego).",
"- Una **tarjeta SD** con espacio suficiente: el port ocupa **~60 MB** y tu copia\n  del juego lo que ocupe en tu PC (normalmente **2-4 GB**).")

sub(RM,
"| 3 | **Tarjeta SD** con espacio | ~250 MB libres (runtime + frontend + tus datos del juego) |",
"| 3 | **Tarjeta SD** con espacio | ~60 MB del port **+** lo que ocupe tu copia del juego (2-4 GB) |")

# ---------- 3) ZR ----------
sub(DOC,
"| **ZR** | `0x20` (ESPACIO) | — | reservado (FIFA 07 no usa ESPACIO) |",
"| **ZR** | `0x20` (ESPACIO) | Avanzar en las pantallas que lo pidan | — (FIFA 07 no usa ESPACIO en partido) |")

sub(RM,
"| **ZR** | — | reservado |",
"| **ZR** | Avanzar en las pantallas que lo pidan | — |")

sub(LEEME,
"  ZR    = ESPACIO     (reservado)",
"  ZR    = ESPACIO     (avanzar en las pantallas que lo pidan)")

# ---------- 4) que se descarga + aviso bootloader/emuMMC ----------
BLOQUE = """---

## ¿Qué descargo? (contenido del paquete)

```
07z/
├── switch/
│   └── fifa07/            <-- el port: copia ESTA carpeta a sdmc:/switch/
└── 07z-forwarder.nsp      <-- el instalador del icono del HOME
```

**Solo eso.** Copia la carpeta `switch/` a la raíz de la SD (fusionando) y el
`.nsp` donde quieras; luego lo instalas (sección 2).

> ⚠️ **NO copies `bootloader/` ni `emuMMC/`** aunque los veas en *otras*
> distribuciones de homebrew: **son cosas de la consola** (la configuración de
> arranque de Hekate y la emuMMC de quien las hizo). Copiarlos encima **no aporta
> nada a 07z y puede desconfigurar tu consola.**
>
> 07z **no crea particiones**, no instala kips y no añade entradas de arranque:
> vive entero dentro de `sdmc:/switch/fifa07/`.

"""
sub(DOC, "---\n\n## 0. Antes de empezar — qué necesitas", BLOQUE + "---\n\n## 0. Antes de empezar — qué necesitas")

sub(RM,
"## 📥 Instalación (resumen)\n\n1. **Descarga**",
"""## 📥 Instalación (resumen)

Lo que descargas es **una carpeta `switch/` (con `fifa07/` dentro) y un `.nsp`**.
Nada más: **no necesitas —ni debes copiar— `bootloader/` ni `emuMMC/`**, que son
cosas de la consola, no de 07z.

1. **Descarga**""")

sub(LEEME,
"""PASOS
-----""",
"""PASOS
-----
0. Lo que descargas es: la carpeta "switch" (con "fifa07" dentro) y
   "07z-forwarder.nsp". NO copies carpetas "bootloader" ni "emuMMC"
   de otras distribuciones: son de la consola, no de 07z.
""")

# ---------- 5) publicar la guia en dist (misma copia) ----------
t = open(DOC, encoding="utf-8").read()
t = t.replace("""*Copia de trabajo (repositorio del PC). La versión que se publica con el paquete
es `dist/github-07z/docs/INSTALACION.md`; el contenido es el mismo.*

""", "")
os.makedirs("dist/github-07z/docs", exist_ok=True)
open("dist/github-07z/docs/INSTALACION.md", "w", encoding="utf-8", newline="").write(t)
print("  ok  dist/github-07z/docs/INSTALACION.md regenerado desde la guia")
print("LISTO")
