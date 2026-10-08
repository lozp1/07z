"""Construye el ZIP publicable del port 07z: SOLO lo del port, nada de EA, nada de basura.

  - En `drive_c/FIFA 07/` viaja SOLO la lista blanca (shims, puente grafico,
    dxvk.conf, keys y wine-nx). Todo lo demas de esa carpeta es el juego del
    usuario (EA) y NO se empaqueta. Fuera `_shims-desactivados/`, `Support/`,
    `filelist.txt`, `fifapc.ico`, `.big`, etc.
  - Fuera del juego se excluyen restos de otras instalaciones que habia en el
    prefijo: `swapprobe/`, `The Sims 2 Setup/`, `WarCraft III Setup/`.
  - De `Documents/FIFA 07/` solo se conserva el perfil (`A. Profiles`/`A. Perfiles`)
    para que el juego arranque ya en 16:9.
  - Backups (*.bak*), logs y ficheros de sesion (*.shm) nunca entran.

Al final verifica e imprime lo que quedo en la carpeta del juego.
"""
import os, sys, zipfile, hashlib, time

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SRC = os.path.join(REPO, "dist", "07z-paquete", "switch", "fifa07")
OUT = os.path.join(REPO, "dist", "07z-port-v1.0.0.zip")

JUEGO = os.path.join("drive_c", "FIFA 07")
PERFIL_DIR = os.path.join("drive_c", "users", "steamuser", "Documents", "FIFA 07")

ALLOW = {
    "d3d8.dll", "d3d8.ini", "d3d9.dll", "dmusic.dll", "dpnhpast.dll",
    "dxwrapper.dll", "dxwrapper.ini", "dxvk.conf", "ddraw.dll",
    "dinput.dll", "msimg32.dll", "oleacc.dll", "sensapi.dll",
    "fifa07.keys.txt", "fifa07.wine-nx.txt",
}

BAN_DIRS = {"swapprobe", "the sims 2 setup", "warcraft iii setup", "warcraft iii",
            "_shims-desactivados", "support", "_backup", "temp", "tmp"}
BASURA_EXT = {".log", ".shm", ".tmp", ".bak"}

if not os.path.isdir(SRC):
    sys.exit(f"no existe {SRC}")

n = 0
total = 0
motivos = {"juego": 0, "basura": 0, "perfil": 0, "otras_instalaciones": 0}
t0 = time.time()
juego_zip = []
with zipfile.ZipFile(OUT, "w", zipfile.ZIP_DEFLATED, compresslevel=6) as z:
    for root, dirs, files in os.walk(SRC):
        rel = os.path.relpath(root, SRC)
        partes = [] if rel == "." else rel.split(os.sep)
        bajo = [p.lower() for p in partes]
        en_juego = len(partes) >= 2 and os.path.join(*partes[:2]).lower() == JUEGO.lower()
        bajo_perfil = os.path.join(*partes[:5]).lower().startswith(PERFIL_DIR.lower()) if partes else False
        dirs[:] = [d for d in dirs if d.lower() not in BAN_DIRS and not d.lower().startswith("bak-")]
        for f in files:
            ext = os.path.splitext(f)[1].lower()
            if ext in BASURA_EXT or ".bak" in f.lower():
                motivos["basura"] += 1
                continue
            if any(p in BAN_DIRS for p in bajo):
                motivos["otras_instalaciones"] += 1
                continue
            if en_juego:
                sub = os.path.join(*partes[2:]) if len(partes) > 2 else ""
                if sub or f.lower() not in ALLOW:
                    motivos["juego"] += 1
                    continue
                juego_zip.append(os.path.join("drive_c", "FIFA 07", f))
            if bajo_perfil and not f.startswith("A."):
                motivos["perfil"] += 1
                continue
            p = os.path.join(root, f)
            z.write(p, os.path.join(rel, f).replace("\\", "/"))
            n += 1
            total += os.path.getsize(p)

print(f"  incluidos: {n} ficheros ({total/1048576:.0f} MB sin comprimir)")
print(f"  excluidos -> juego/EA: {motivos['juego']} | datos de usuario: {motivos['perfil']}"
      f" | otras instalaciones: {motivos['otras_instalaciones']} | basura: {motivos['basura']}")
print(f"  zip: {OUT}  ({os.path.getsize(OUT)/1048576:.1f} MB, {time.time()-t0:.0f}s)")
print("  --- lo unico que va dentro de drive_c/FIFA 07/ (debe ser solo el port):")
for f in sorted(juego_zip):
    print("     ", f)
with zipfile.ZipFile(OUT) as z:
    fuera = [i.filename for i in z.infolist()
             if not i.filename.startswith("drive_c/FIFA 07/")
             and os.path.splitext(i.filename)[1].lower() in (".exe", ".dat", ".ico", ".big", ".vp6")]
    print(f"  --- ejecutables/datos fuera de la carpeta del juego: {len(fuera)} {fuera[:8]}")
    print(f"  --- 'The Sims' / 'WarCraft' / 'swapprobe' dentro del zip: "
          f"{[i.filename for i in z.infolist() if any(k in i.filename.lower() for k in ('sims', 'warcraft', 'swapprobe'))]}")
h = hashlib.sha256(open(OUT, "rb").read()).hexdigest()
print(f"  sha256: {h}")
