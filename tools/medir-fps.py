#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""medir-fps.py - Medicion objetiva del port FIFA 07 (Wine-NX / Autorun) en Switch.

Lee el log que el runtime escribe en la SD y saca los FPS reales por tramo, el
minimo (los "bajones") y cuantos tramos caen por debajo de 20 y de 10 FPS.
Sirve para comparar ANTES / DESPUES de un cambio de configuracion SIN consola.

USO
    python medir-fps.py                                   # SD en D:, log por defecto
    python medir-fps.py --sd D                            # elige la letra de la SD
    python medir-fps.py --sd E:  --out informe.txt        # guarda el informe
    python medir-fps.py --log "D:/switch/fifa07/logs/fifa07.log"
    python medir-fps.py D:/ informe.txt                   # posicional (compat)

    (no instala nada: solo la libreria estandar de Python 3)

QUE LEE
    <sd>/switch/fifa07/logs/fifa07.log      (log del runtime; por defecto)
    <sd>/switch/fifa07/fifa07nx.log         (fallback si no existe el anterior)

LINEAS DEL RUNTIME QUE PARSEA
    [PROGRESS] <t>s ... frames=<N>   -> fotogramas PRESENTADOS acumulados (fuente de FPS)
    [THREADS]  <n> threads use X cores: ...   -> reparto de CPU (¿es CPU-bound?)
    [SYNC]     Standard | Horizon              -> confirma el ajuste "sync"
    [CORES]    ...                             -> confirma el modo "four-cores"
    [INIT]     processors=N ...                -> nucleos vistos por Wine
    info: Found config file: ...               -> dxvk.conf en uso
    info: DXVK: Using N compiler threads       -> workers de compilacion de shaders
    info: Found cache file: ...                -> cache de pipelines DXVK cargada
    [NXVK] present <N>: ...                    -> contador de presentaciones de la capa NVK

INTERPRETACION RAPIDA
    - Los "bajones" de los menus 3D son tramos con FPS < 20 (o < 10).
    - El PRIMER arranque tras cambiar dxvk.conf / la cache recompila shaders y va
      PEOR. Mide en el SEGUNDO arranque.
"""
import argparse
import datetime
import glob
import os
import re
import sys

# ---------------------------------------------------------------- regexes
PROG = re.compile(r"\[PROGRESS\]\s+(\d+)s\b.*?\bframes=(\d+)")
THR = re.compile(r"\[THREADS\]\s+(\d+)\s+threads use\s+([\d.]+)\s+cores:(.*)")
SYNC = re.compile(r"\[SYNC\]\s*(.*)")
CORES = re.compile(r"\[CORES\]\s*(.*)")
PROC = re.compile(r"\[INIT\]\s*processors=(\d+).*")
CFG = re.compile(r"Found config file:\s*(.*)")
CTHREADS = re.compile(r"DXVK: Using (\d+) compiler threads")
CACHE = re.compile(r"Found cache file:\s*(.*)")
NXVK_PRESENT = re.compile(r"\[NXVK\]\s+(?:scaled )?present\s+(\d+)\s*:")


def read_text(path):
    for enc in ("utf-8", "latin-1"):
        try:
            with open(path, "r", encoding=enc, errors="replace") as fh:
                return fh.read()
        except OSError:
            return None
    return None


def pct(sorted_vals, p):
    if not sorted_vals:
        return float("nan")
    i = int(round((len(sorted_vals) - 1) * p / 100.0))
    return sorted_vals[i]


def intervals(rows):
    """De pares (t, frames) consecutivos -> (t0, t1, dt, dframes, fps)."""
    out = []
    for i in range(1, len(rows)):
        t0, f0 = rows[i - 1]
        t1, f1 = rows[i]
        dt = t1 - t0
        if dt <= 0:
            continue
        out.append((t0, t1, dt, f1 - f0, (f1 - f0) / float(dt)))
    return out


def resolve_sd(value):
    """Acepta 'D', 'D:', 'D:/' o 'D:\\' -> 'D:/'."""
    if not value:
        return "D:/"
    v = value.replace("\\", "/").strip()
    if len(v) == 1 and v.isalpha():
        v = v + ":"
    v = v.rstrip("/")
    return v + "/" if v else "D:/"


def main():
    ap = argparse.ArgumentParser(add_help=True, description="Medicion de FPS del port FIFA 07 (Wine-NX).")
    ap.add_argument("--sd", default=None, help="letra o raiz de la SD (por defecto: D:)")
    ap.add_argument("--log", default=None, help="ruta completa del log (por defecto: <sd>/switch/fifa07/logs/fifa07.log)")
    ap.add_argument("--out", default=None, help="guarda el informe en este fichero")
    ap.add_argument("pos", nargs="*", help="[sd] [salida.txt]  (forma posicional compatible)")
    args = ap.parse_args()

    sd = args.sd
    out_path = args.out
    log_path = args.log
    pos = list(args.pos)
    if sd is None and pos:
        sd = pos.pop(0)
    if out_path is None and pos:
        out_path = pos.pop(0)
    sd_root = resolve_sd(sd)

    if not log_path:
        for candidate in (sd_root + "switch/fifa07/logs/fifa07.log",
                          sd_root + "switch/fifa07/fifa07nx.log"):
            if os.path.isfile(candidate):
                log_path = candidate
                break
        if not log_path:
            log_path = sd_root + "switch/fifa07/logs/fifa07.log"

    L = []

    def w(s=""):
        print(s)
        L.append(s)

    w("=" * 74)
    w("MEDICION FIFA 07 (Wine-NX/Autorun)   SD=" + sd_root + "   log=" + log_path)
    w("=" * 74)

    txt = read_text(log_path)
    if not txt:
        w("!! No se pudo leer el log.")
        w("   Mira que la SD este montada y usa la letra correcta:  --sd D   (o E, F, G...)")
        return 2

    # ---- ajustes efectivos (confirman que los cambios entraron) ----------
    w("CONFIGURACION EFECTIVA (segun el propio log)")
    for m in SYNC.finditer(txt):
        w("  [SYNC]  " + m.group(1).strip() + "        (Standard=normal, Horizon=sincronizacion directa)")
    seen = set()
    for m in CORES.finditer(txt):
        line = m.group(1).strip()
        if line not in seen:
            seen.add(line)
            w("  [CORES] " + line)
    m = PROC.search(txt)
    if m:
        w("  [INIT]  processors=" + m.group(1) + "   (nucleos vistos por Wine)")
    for rx, tag in ((CFG, "dxvk.conf en uso"), (CTHREADS, "workers de compilacion"),
                    (CACHE, "cache DXVK cargada")):
        last = None
        for m in rx.finditer(txt):
            last = m
        if last:
            w("  " + tag + ": " + last.group(1).strip())

    # ---- FPS desde [PROGRESS] frames= ------------------------------------
    rows = [(int(a), int(b)) for a, b in PROG.findall(txt)]
    samples = intervals(rows)

    w("")
    w("-" * 74)
    if not samples:
        w("AVISO: el log no tiene lineas utiles [PROGRESS] ... frames=N.")
        w("       El runtime las escribe mientras presenta fotogramas; arranca el")
        w("       juego, juega/entra a los menus y vuelve a ejecutar el script.")
        nv = [int(x) for x in NXVK_PRESENT.findall(txt)]
        if len(nv) >= 2:
            w("       (El log SI tiene un contador [NXVK] present: %d -> %d)"
              % (nv[0], nv[-1]))
        if out_path:
            with open(out_path, "w", encoding="utf-8") as fh:
                fh.write("\n".join(L) + "\n")
        return 1

    w("FPS POR TRAMO  (frames presentados / tiempo, lineas [PROGRESS])")
    w("-" * 74)
    w("%10s %8s %7s  %s" % ("tramo(s)", "frames", "FPS", "barra"))
    vals = []
    lows20 = lows10 = lows30 = 0
    for t0, t1, dt, df, fps in samples:
        # tramos utiles: 2 s <= dt <= 40 s y con fotogramas (no huecos de carga)
        valido = 2 <= dt <= 40 and df >= 0
        if valido:
            vals.append(fps)
            if fps < 30:
                lows30 += 1
            if fps < 20:
                lows20 += 1
            if fps < 10:
                lows10 += 1
        barra = "#" * int(max(0.0, min(fps, 60.0)))
        nota = "" if valido else "  (hueco de carga, descartado)"
        w("%4d-%4ds %8d %7.1f  %s%s" % (t0, t1, df, fps, barra, nota))

    w("")
    if vals:
        s = sorted(vals)
        media = sum(vals) / len(vals)
        # media global del run (primer y ultimo fotograma con tiempo)
        glob_fps = float("nan")
        if rows and rows[-1][0] > rows[0][0]:
            glob_fps = (rows[-1][1] - rows[0][1]) / float(rows[-1][0] - rows[0][0])
        w("RESUMEN DE FPS  (%d tramos utiles)" % len(vals))
        w("  FPS medio (media de tramos) : %6.1f" % media)
        w("  FPS medio global del run    : %6.1f" % glob_fps)
        w("  FPS minimo (peor tramo)     : %6.1f   <-- el 'bajon'" % s[0])
        w("  FPS maximo (mejor tramo)    : %6.1f" % s[-1])
        w("  percentiles p10 / p50 / p90 : %6.1f / %6.1f / %6.1f"
          % (pct(s, 10), pct(s, 50), pct(s, 90)))
        w("")
        w("  BAJONES (lo que hay que reducir):")
        w("    tramos < 30 FPS : %d de %d" % (lows30, len(vals)))
        w("    tramos < 20 FPS : %d de %d" % (lows20, len(vals)))
        w("    tramos < 10 FPS : %d de %d" % (lows10, len(vals)))
        w("")
        w("  ULTIMOS 5 VALORES: "
          + "  ".join("%.1f" % v for v in [x[4] for x in samples[-5:]]))
    else:
        w("No hay tramos utiles (todos con dt fuera de 2-40 s). Revisa el log.")

    # ---- CPU -------------------------------------------------------------
    w("")
    w("-" * 74)
    w("CPU / NUCLEOS  ([THREADS]: 1.00 = un nucleo al 100%)")
    w("-" * 74)
    last = None
    for m in THR.finditer(txt):
        last = m
    if last:
        w("  ultima muestra: %s hilos usan %s nucleos" % (last.group(1), last.group(2)))
        w("  reparto: " + " ".join(last.group(3).split()))
        try:
            if float(last.group(2)) < 2.5:
                w("  => el port NO esta saturado de CPU (sobra CPU); el techo no es de calculo.")
        except ValueError:
            pass
    else:
        w("  (sin lineas [THREADS])")

    # ---- caches de shaders ----------------------------------------------
    w("")
    w("-" * 74)
    w("CACHES DE SHADERS (deben EXISTIR; su fecha debe avanzar tras jugar)")
    w("-" * 74)
    cached = glob.glob(sd_root + "switch/fifa07/drive_c/users/steamuser/AppData/Local/dxvk/*")
    if cached:
        for p in sorted(cached):
            try:
                mt = datetime.datetime.fromtimestamp(os.path.getmtime(p)).isoformat(timespec="seconds")
                w("  DXVK %-24s %8d B  mtime=%s" % (os.path.basename(p), os.path.getsize(p), mt))
            except OSError:
                pass
    else:
        w("  DXVK: NO se encontro la cache en "
          "drive_c/users/steamuser/AppData/Local/dxvk/")
    base = sd_root + ".mesa/mesa_shader_cache_sf"
    if os.path.isdir(base):
        total = 0
        for dp, _dn, fn in os.walk(base):
            for f in fn:
                try:
                    total += os.path.getsize(os.path.join(dp, f))
                except OSError:
                    pass
        w("  NVK(Mesa) %s : %.1f MB" % (base, total / 1048576.0))

    w("")
    w("COMO COMPARAR ANTES/DESPUES")
    w("  1) Arranca el juego desde el icono del HOME y juega el MISMO tramo")
    w("     (mismo partido + los MISMOS menus: seleccion de equipos, plantillas,")
    w("     formaciones, que es donde caia a 1-10 FPS).")
    w("  2) Sal del juego y ejecuta otra vez este script.")
    w("  3) Compara: FPS minimo, 'tramos < 20 FPS' y 'tramos < 10 FPS'.")
    w("  IMPORTANTE: el PRIMER arranque tras cambiar dxvk.conf va PEOR")
    w("  (recompila shaders). Mide en el SEGUNDO arranque.")

    if out_path:
        with open(out_path, "w", encoding="utf-8") as fh:
            fh.write("\n".join(L) + "\n")
        print("\nInforme guardado en " + out_path)
    return 0


if __name__ == "__main__":
    sys.exit(main())
