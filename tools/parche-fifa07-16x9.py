#!/usr/bin/env python3
"""Parche 16:9 a BAJA resolucion para FIFA 07 (Wine-NX / Switch).

Reescribe la entrada idx1 de la tabla de modos de fifa07.exe (la 800x600,
la que el perfil del juego selecciona con OPTIONS/RESOLUTION=1) por 800x450.
800x450 es 16:9 exacto: min(1280/800, 720/450)=1.6 -> el blit del runtime
llena 1280x720 SIN barras y con MENOS pixeles que 800x600 (mejor FPS).

NO toca 1280x720 (idx3) ni ninguna otra entrada (duplicar valores rompio
el arranque en un intento previo). NO toca el puente d3d8/dxwrapper/d3d9.

Uso:
  python3 parche-fifa07-16x9.py --check  "D:/switch/fifa07/drive_c/FIFA 07/fifa07.exe"
  python3 parche-fifa07-16x9.py --apply  "..."   # hace .bak-antes-idx1-800x450
  python3 parche-fifa07-16x9.py --revert "..."   # restaura desde el .bak
"""
import sys, os, shutil

OFF = 0x4c42f8          # record idx1: w(u32) h(u32) 32(u32) 0(u32)
ORIG = bytes.fromhex("20030000" "58020000")   # 800x600
NEW  = bytes.fromhex("20030000" "c2010000")   # 800x450
BAK_SUFFIX = ".bak-antes-idx1-800x450"

def state(d):
    if d[OFF:OFF+8] == NEW:  return "16:9 800x450 (parcheado)"
    if d[OFF:OFF+8] == ORIG: return "4:3 800x600 (original, con barras)"
    return "desconocido: " + d[OFF:OFF+8].hex(' ')

def main():
    if len(sys.argv) != 3 or sys.argv[1] not in ("--check", "--apply", "--revert"):
        print(__doc__); sys.exit(2)
    mode, path = sys.argv[1], sys.argv[2]
    d = bytearray(open(path, 'rb').read())
    if len(d) < OFF + 8:
        print("ERROR: fichero demasiado pequeno"); sys.exit(1)
    print("estado actual:", state(d))
    if mode == "--check":
        return
    if mode == "--apply":
        if bytes(d[OFF:OFF+8]) == NEW:
            print("ya estaba parcheado; nada que hacer"); return
        if bytes(d[OFF:OFF+8]) != ORIG:
            print("ERROR: idx1 no tiene el valor original esperado; abortando"); sys.exit(1)
        bak = path + BAK_SUFFIX
        if not os.path.exists(bak):
            shutil.copy2(path, bak); print("backup ->", bak)
        d[OFF:OFF+8] = NEW
        open(path, 'wb').write(d)
        print("parcheado:", state(open(path, 'rb').read()))
    if mode == "--revert":
        bak = path + BAK_SUFFIX
        if not os.path.exists(bak):
            print("ERROR: no existe", bak); sys.exit(1)
        shutil.copy2(bak, path)
        print("revertido:", state(open(path, 'rb').read()))

if __name__ == "__main__":
    main()
