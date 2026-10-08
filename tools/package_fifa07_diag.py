#!/usr/bin/env python3
"""Assemble the FIFA 07 diagnostic package on top of the logging Wine-NX runtime.

WHY THIS EXISTS
---------------
The FEXTendo production NRO shipped in `dist/fifa07-nx/` is built with every
runtime log disabled (see docs/FEXTENDO-PRODUCTION-NO-LOG.md). A port that does
not boot cannot be diagnosed without a log, so this tool assembles a package
around `wine-test-build-2.zip`, the pinned Wine-NX release that *does* log to
`sdmc:/switch/wine/wine-nx-runtime.log`.

This is deliberately NOT a binary patcher. It copies the runtime exactly as the
upstream release ships it, places the game where the runtime already looks for
it, and then verifies every runtime file against `config/runtime-files.json`.
Nothing inside the NRO is rewritten.

LAYOUT
------
`sdmc:/switch/wine/` is the root compiled into the pinned Wine-NX runtime, so
the package keeps it. That is why the diagnostic package does not use the
canonical `sdmc:/switch/fifa07-nx/` root: changing it would mean patching the
NRO, which is the practice this project is moving away from.

Graphics: variant B is the default and is INSTALLED into the game folder.

FIFA 07 imports d3d8.dll (no d3d9), so DXVK cannot serve it directly. Variant A
left the game on Wine's builtin d3d8 through wined3d, and the log of the last
run shows what that costs: the loader probed

    [NTOPEN] NtCreateFile name='\\??\\C:\\FIFA 07\\d3d8.dll' -> status=0xc0000034

(absent), fell back to syswow64's builtin, and the game gave up with its
"You will need to install DirectX 9.0c to run FIFA" dialog.

The Steam Deck copy of the game already shipped the community's fix inside the
game folder (dxwrapper's d3d8 stub + dxwrapper.dll + D3d8to9=1). Variant B
installs that chain AND copies DXVK's d3d9.dll next to the game - the step that
is Switch-specific, because Proton supplied that d3d9 on the Deck while
Wine-NX's syswow64/d3d9.dll is wined3d/OpenGL. Chain: d3d8 stub -> dxwrapper ->
DXVK d3d9 -> Vulkan. `--variant-a` restores the old, now proven-broken
behaviour; the files stay staged in `_variant-b-dxvk/` either way.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import shutil
import sys
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

# The Steam Deck / Proton overlay. None of it is read by Wine-NX, and the
# dxwrapper chain is variant B, so it is staged rather than installed.
STEAMDECK_OVERLAY = (
    "dxwrapper.dll",
    "d3d8.dll",
    "dxwrapper.ini",
    "Stub.ini",
    "DrvMgt.dll",
    "fifa07.wine-nx.txt",
)

# EMPTY ON PURPOSE. Do not fill this with DLLs taken from the host's
# C:\Windows\SysWOW64.
#
# History: fifa07.exe statically imports DINPUT.dll and SensApi.dll, which the
# pinned Wine-NX payload does not ship in syswow64, so an app-local copy once
# looked like the obvious fix. It is not. The copies used were byte-identical to
# the host's 32-bit system DLLs, i.e. Windows 10/11 binaries, and those import
# api-sets that Wine-NX does not provide:
#   dinput.dll  delay-loads ext-ms-win-mininput-inputhost-l1-1-1.dll
#               (CreateInputHostForProcess) and ...-l1-1-0.dll
#               (CreateGenericInputHost); an unresolved delay import makes the
#               MSVC helper raise 0xC06D007E (= ERROR_MOD_NOT_FOUND, 126) and
#               fifa07.exe terminates itself.
#   sensapi.dll imports api-ms-win-core-sysinfo-l1-2-0.dll!GetOsSafeBootMode,
#               which Wine stubs to a dummy address that then faults.
# Wine-NX already synthesises a dummy module for these, which is what the
# "No implementation for ... setting to <addr>" log lines are. Let it.
APP_LOCAL_DLLS: tuple[str, ...] = ()

# The modules the guest's import tables need that the Wine-NX payload does not
# ship. DINPUT/sensapi come from fifa07.exe; MSIMG32 from dxwrapper.dll; dmusic
# is the in-process COM server behind the game's DirectX 9.0c probe.
# These are OUR builds from src/shims/ (verified i386, exact exports, no api-set
# imports, not host copies) - never a copy of a Windows system DLL.
SHIM_DLLS = ("DINPUT.dll", "sensapi.dll", "MSIMG32.dll", "dmusic.dll", "dpnhpast.dll")

# CLSID_DirectMusic. fifa07.exe contains this GUID and no other DirectMusic
# symbol: the "You will need to install DirectX 9.0c to run FIFA" dialog is this
# one class failing to instantiate. See src/shims/dmusic_fifa07.c.
DMUSIC_CLSID = "{636B9F10-0C7D-11D1-95B2-0020AFDC7421}"
DMUSIC_DLL = r"C:\FIFA 07\dmusic.dll"

# Timestamp Wine writes after a section heading. Any value works; this one keeps
# the injected keys looking like the rest of the file.
WINE_REG_TIME = 1791268407


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for block in iter(lambda: f.read(1 << 20), b""):
            h.update(block)
    return h.hexdigest()


def extract_runtime(archive: Path, runtime_root: Path) -> None:
    """Copy only the runtime payload: the sample executables are left behind."""
    wanted_prefixes = (
        "switch/wine/drive_c/windows/",
        "switch/wine/drive_c/dxvk/",
        "switch/wine/share/wine/",
    )
    wanted_files = ("switch/wine/keys.txt",)
    with zipfile.ZipFile(archive) as z:
        names = z.namelist()
        picked = [n for n in names
                  if n.startswith(wanted_prefixes) or n in wanted_files]
        if not picked:
            raise SystemExit(f"{archive}: no runtime payload found")
        for name in picked:
            rel = Path(name).relative_to("switch/wine")
            target = runtime_root / rel
            target.parent.mkdir(parents=True, exist_ok=True)
            with z.open(name) as src, target.open("wb") as dst:
                shutil.copyfileobj(src, dst)
        nro = runtime_root / "wine-nx-runtime.nro"
        with z.open("switch/wine/wine-nx-runtime.nro") as src, nro.open("wb") as dst:
            shutil.copyfileobj(src, dst)


def copy_game(source: Path, destination: Path, overlay: Path) -> None:
    destination.mkdir(parents=True, exist_ok=True)
    overlay.mkdir(parents=True, exist_ok=True)
    for entry in sorted(source.iterdir()):
        name = entry.name
        # Never mutate the user's source install: the overlay is a copy.
        if name in STEAMDECK_OVERLAY:
            if entry.is_file():
                shutil.copy2(entry, overlay / name)
            continue
        target = destination / name
        if entry.is_dir():
            shutil.copytree(entry, target, dirs_exist_ok=True)
        else:
            shutil.copy2(entry, target)


def install_app_local(source: Path, game_dir: Path) -> list[str]:
    """Place the app-local 32-bit DLLs fifa07.exe imports but Wine-NX lacks."""
    installed = []
    for name in APP_LOCAL_DLLS:
        candidate = source / name
        if candidate.is_file():
            shutil.copy2(candidate, game_dir / name)
            installed.append(name)
    return installed


def install_shims(shims: Path, game_dir: Path) -> list[str]:
    """Install the two built shim DLLs. See src/shims/dinput_fifa07.c.

    fifa07.exe imports one function each from DINPUT.dll and SensApi.dll, and the
    Wine-NX payload ships neither, so the loader aborts with c0000135 before the
    game draws anything. These replacements are built and verified by
    tools/build-fifa07-shims.py.
    """
    installed = []
    for name in SHIM_DLLS:
        source = shims / name
        if not source.is_file():
            raise SystemExit(
                f"missing shim {source}\n"
                f"build it first: python tools/build-fifa07-shims.py")
        shutil.copy2(source, game_dir / name)
        installed.append(name)
    return installed


def install_registry(prefix: Path, runtime_root: Path) -> str:
    """Ship the Wine-NX prefix registry, with CLSID_DirectMusic registered.

    This used to be staged only: the game booted from a freshly created prefix
    and a hand-placed registry was worth avoiding. That changed once the DirectX
    probe turned out to be CoCreateInstance(CLSID_DirectMusic): COM learns which
    module serves a class from the registry, nothing else writes that entry, and
    a package that does not carry the registry (or loses it on a re-copy) puts
    the "install DirectX 9.0c" dialog straight back.
    """
    installed = []
    for name in ("system.reg", "user.reg"):
        source = prefix / name
        if source.is_file():
            shutil.copy2(source, runtime_root / name)
            installed.append(name)
    if not (runtime_root / "system.reg").is_file():
        raise SystemExit(f"{prefix} has no system.reg to ship; pass --prefix")
    installed.append(install_dmusic_registry(runtime_root))
    return ", ".join(installed)


LEEME = """FIFA 07 - paquete de DIAGNOSTICO (no es el paquete final)
=========================================================

Objetivo: conseguir un LOG de por que no arranca el juego. El paquete de
produccion (dist/fifa07-nx) tiene todos los logs desactivados por diseno, asi
que con el no se puede diagnosticar nada.

COMO SE ARRANCA (flujo real, confirmado en la consola)
------------------------------------------------------
El NRO TIENE QUE ARRANCAR CON ESPACIO DE DIRECCIONES DE 32 BITS. Eso NO lo
decide el NRO: lo decide quien lo lanza (el tipo de applet y el NPDM del
forwarder). Lanzado COMO APPLET desde el Homebrew Menu recibe 64 bits y el
juego no se puede cargar: por eso el propio runtime, cuando termina asi, dice
    [EXIT] parked after runtime handoff; close from HOME

El flujo que si funciona:
  1. Enciende la consola -> Homebrew Menu (mantener R sobre un juego) ->
     entra en "Autorun" (es este mismo wine-nx-runtime.nro).
  2. Dentro, anade FIFA 07 al catalogo y pulsa A para jugar. Te ofrecera
     crear un forwarder: acepta. El runtime lo instala y se queda "pausado"
     a proposito (no puede jugar en modo applet). Cierralo.
  3. Ya aparece la app en el MENU DE LA CONSOLA (HOME). Entra DESDE AHI.
     Ese arranque si es una aplicacion de verdad y recibe los 32 bits.
  4. Pulsa A para arrancar el juego y espera.

Regla de oro: para JUGAR, siempre desde el icono del HOME, nunca desde el
Homebrew Menu. El Homebrew Menu solo sirve para crear el forwarder la primera
vez. Si el forwarder ya existe, ve directo al punto 3.

Sintomas exactos si se arranca con el espacio equivocado (ya reproducido):
    horizon-trace.log: [VA] Horizon ASLR region ... limit=0x8000000000   <-- 64 bits
    horizon-trace.log: [IV] map_view(fixed 0x400000) -> 0xc0000018
    horizon-trace.log: [MI] done status=0xc000007b
    wine-nx-runtime.log: [FAIL] map target status=c000007b

Por que (dos causas distintas, ambas ya reproducidas):
 1) fifa07.exe tiene IMAGE_FILE_RELOCS_STRIPPED=1 y sin tabla .reloc, o sea
    que SOLO se puede cargar en su ImageBase 0x400000. Con un espacio de
    64 bits esa direccion ya esta ocupada (0xC0000018), el loader cae a
    0x8000000 y al no poder reubicar la imagen devuelve 0xC000007B.
 2) Con espacio de 32 bits el mapeo en 0x400000 SI funciona
    (map_view(fixed 0x400000) -> 0x0) pero el build nx-wow64-dynarec-108
    sigue terminando en [MI] done status=0xc000007b: su mapeador de
    secciones rechaza esta imagen. El build nx-wow64-dynarec-218 SI la mapea
    (su log muestra [IMAGE] base=0x400000 size=0x6df000 entry_rva=0x420fe3,
    que coincide exactamente con este fifa07.exe).

Por eso este paquete usa el par de build 218: el NRO 218 Y su
winebox64.dll emparejado (los bytes son distintos de los del 108). Enviar
solo uno de los dos fue justo el fallo del intento anterior, que murio en
[WOW64] native DLLs status=c0000135.

Opciones, de mas simple a mas trabajo:
  a) Si usas Sphaira como menu, pon el espacio de direcciones en 32-bit
     no-alias al lanzar switch/wine/wine-nx-runtime.nro.
  b) Construir un forwarder PROPIO para este NRO de diagnostico, con
     AddressSpaceType=2 y su propia ruta, para no tocar ninguna instalacion
     existente. tools/build-fextendo-forwarder.py acepta --nro; hace falta
     prod.keys y local/forwarder-tools/ (Sphaira hbl + hacBrewPack).

AVISO IMPORTANTE
----------------
NO copies este NRO encima de sdmc:/switch/pes13-fex/pes13-fex.nro. Esa ruta
es de la instalacion de PES 13 NX y el forwarder "PES13 - FEXTendo" la
arranca: sustituir ese fichero deja PES 13 NX sin arrancar. Este paquete NO
incluye ninguna copia ahi y no escribe nada dentro de switch/pes13-fex/ ni de
switch/fifa07-nx/. Solo anade la carpeta nueva switch/wine/ .

Que contiene
------------
switch/wine/                     runtime Wine-NX que SI escribe log.
                                 NRO de build nx-wow64-dynarec-218 + su
                                 winebox64.dll emparejado, sobre el payload
                                 fijado (windows/, share/, NLS) del release
                                 wine-test-build-2
switch/wine/drive_c/FIFA 07/     tu instalacion de FIFA 07
switch/wine/drive_c/FIFA 07/DINPUT.dll   shim propio (DirectInput 1-7 minimo;
                                         GetDeviceState lee el estado real del
                                         teclado de Win32, asi que el mapeo
                                         mando->teclas de Wine-NX llega al juego)
switch/wine/drive_c/FIFA 07/sensapi.dll  shim propio (IsNetworkAlive -> FALSE)
switch/wine/drive_c/FIFA 07/MSIMG32.dll  shim propio (AlphaBlend, GradientFill,
                                         TransparentBlt). Lo importa dxwrapper.dll
                                         y el payload no lo trae; sin el, el modulo
                                         entero no carga y el stub se apaga.
switch/wine/drive_c/FIFA 07/OLEACC.dll   oleacc de Wine, copiado del payload de
                                         pes13-fex: dxwrapper.dll importa
                                         AccessibleObjectFromWindow/Event.
switch/wine/drive_c/FIFA 07/dmusic.dll   shim propio: CoCreateInstance(
                                         CLSID_DirectMusic) es la sonda con la
                                         que el juego decide si "hay DirectX
                                         9.0c" (ver el punto 8 del historial)
switch/wine/system.reg                   + la clave CLSID_DirectMusic apuntando
                                         a esa dll
switch/wine/drive_c/FIFA 07/  ->  variante B por defecto: d3d8.dll (stub),
                             dxwrapper.dll, dxwrapper.ini, Stub.ini, DrvMgt.dll,
                             fifa07.wine-nx.txt y d3d9.dll (DXVK)
switch/wine/target.txt           programa preseleccionado (fifa07.exe)
switch/wine/verbose.txt          1 = trazas detalladas al log
switch/wine/_variant-b-dxvk/     copia de la cadena, por si hay que reinstalarla
switch/wine/system.reg,user.reg  el registro del prefijo, AHORA SI SE ENVIA: COM
                                 aprende de ahi que modulo sirve CLSID_DirectMusic
switch/wine/_steamdeck-overlay/  archivos del setup de Steam Deck, sin instalar

Nada del NRO fue modificado: no hay parcheo de binarios. Lo que se escribe en
la carpeta del juego es SOLO aditivo: no se borra ni se sustituye ningun
fichero que ya estuviera ahi.

config/runtime-files.json tiene 206 entradas y conviene leerlas bien:
  - 180 coinciden byte a byte con la SD.
  - 1  (drive_c/windows/system32/winebox64.dll) es el winebox64.dll del par de
    build 218, que sustituye a proposito al del release fijado. El propio
    empaquetador lo informa como "replaced-by-runtime-pair", no como corrupcion.
  - 25 son DLLs que solo trae el payload de PES 13 (advpack, cabinet, gdiplus,
    oleacc, urlmon...), o sea entradas de mas del manifiesto: verify() siempre
    las echara en falta y por eso el empaquetador lo indica como nota.

Como usarlo
-----------
1. Copia la carpeta `switch` de este paquete a la RAIZ de la SD, fusionando.
   Queda como sdmc:/switch/wine/ , que es la ruta que el runtime trae compilada.
2. Borra sdmc:/switch/wine/wine-nx-runtime.log si existe, para no mezclar runs.
3. Arranca con 32 bits no-alias (ver arriba). Sale un menu con los programas de
   drive_c; FIFA 07 viene preseleccionado por target.txt. Pulsa A.
4. Espera 60-120 s y recupera:
       sdmc:/switch/wine/wine-nx-runtime.log
       sdmc:/switch/wine/horizon-trace.log        (si existe)
   Esos archivos son lo que hace falta para seguir.

Ojo: este runtime escribe `wine-nx-runtime.log`. Tu log anterior se llamaba
`game-fifa07.log` y venia de otro build (nx-wow64-dynarec-218), no de este.

Historial de fallos ya descartados
----------------------------------
1) build 218 sobre sdmc:/switch/wine : murio en
      [WOW64] native DLLs status=c0000135
   c0000135 = STATUS_DLL_NOT_FOUND: faltaba winebox64.dll en
   drive_c/windows/system32/ porque la copia a la SD estaba incompleta. Este
   paquete lo trae completo y verificado.
2) build 108 lanzado desde el Homebrew Menu: 0xc000007b al mapear la imagen,
   por el espacio de direcciones de 64 bits.
3) build 108 lanzado con 32 bits no-alias: el mapeo en 0x400000 funciona,
   pero su mapeador de secciones devuelve igualmente 0xc000007b. Es un
   defecto del 108 con esta imagen, no del arranque. De ahi el 218.
4) build 218 con su winebox64.dll: YA CARGA Y EJECUTA EL JUEGO. Mapea la
   imagen, carga ntdll/wow64/wow64win/winebox64, inicializa Wine, NLS,
   teclado y threads, y corre 2758 syscalls y 1536 bloques de dynarec. Murio
   por una DLL que metimos nosotros:
       0004:warn:module:import_dll No implementation for
       api-ms-win-core-sysinfo-l1-2-0.dll.GetOsSafeBootMode imported from
       L"\\C:\\FIFA 07\\SensApi.dll"
       ...load_dll Failed to load module L"ext-ms-win-mininput-inputhost-l1-1-1.dll"
       0008:warn:seh:dispatch_exception unknown exception (code=c06d007e)
       [EXIT] NtTerminateProcess(self) exit_code=0xc06d007e
   Ese c000007e = ERROR_MOD_NOT_FOUND (126) en la familia 0xC06D00xx: es la
   excepcion del helper de delay-load de MSVC. La disparaba nuestro
   dinput.dll, que resulto ser identico byte a byte a
   C:\\Windows\\SysWOW64\\dinput.dll del PC (Windows 11) y hace delay-load de
   ext-ms-win-mininput-inputhost-l1-1-1.dll!CreateInputHostForProcess, un
   api-set que Wine-NX no proporciona. Lo mismo con sensapi.dll,
   msimg32.dll y xinput9_1_0.dll: las cuatro eran DLLs del Windows del PC,
   metidas a mano, y ninguna existia en el paquete original de Steam Deck.
   Ya NO se envia ninguna DLL de Windows app-local: Wine-NX pone un modulo
   de relleno por si mismo (es justo el "setting to <addr>" del log).
5) Quitadas esas DLLs: el juego murio ANTES, con
       0004:warn:module:load_dll Failed to load module L"DINPUT.dll"; status=c0000135
       0004:err:module:loader_init Importing dlls for L"fifa07.exe" failed
       [EXIT] NtTerminateProcess(self) exit_code=0xc0000135
   Wine-NX NO sintetiza un modulo entero que falta en un import estatico: el
   "setting to <addr>" solo vale para exports que faltan de un modulo que SI
   carga. fifa07.exe importa UNA funcion de cada una:
       DINPUT.dll  -> DirectInputCreateA
       SensApi.dll -> IsNetworkAlive
   Solucion: los dos shims propios de arriba, compilados desde src/shims/ con
   i686-w64-mingw32-gcc y verificados por tools/build-fifa07-shims.py: i386,
   exports exactos, CERO imports api-ms-*/ext-ms-*, y no son copia de ninguna
   DLL del PC. Compilacion reproducible (-Wl,--no-insert-timestamp).
   PENDIENTE CONOCIDO: el DINPUT.dll propio no implementa gamepad por
   DirectInput. El teclado si funciona (lee GetAsyncKeyState de Win32). El
   siguiente paso es compilar el dinput.dll real de Wine (dlls/dinput), que
   trae DirectInput 1-7 completo, para que el mando funcione por su cuenta.
6) Variante A (d3d8 propio de Wine): el juego YA ARRANCA Y DIBUJA, pero muestra
   el dialogo de FIFA 07
       "You will need to install DirectX 9.0c to run FIFA"
   (ventana class=#32770 con boton OK; el juego sale limpio al pulsarlo).
   El log de ese intento lo explica:
       [NTOPEN] NtCreateFile name='\\??\\C:\\FIFA 07\\d3d8.dll' -> c0000034
       [NTOPEN] NtCreateFile name='\\??\\C:\\windows\\syswow64\\d3d8.dll' -> 0x0
   El loader mira PRIMERO junto al .exe (no estaba) y cae al d3d8 interno de
   Wine (wined3d -> OpenGL). Hasta ese punto el juego hace muchisimo mas de lo
   que parece: mapea la imagen, 11 hilos, 32.632 bloques de dynarec, crea
   DirectDraw + device D3D, y el compositor le entrega la pantalla a OpenGL.
   El UNICO fallo de DirectX que registra es:
       err:ole:com_get_class_object {636b9f10-0c7d-11d1-95b2-0020afdc7421}
       OutputDebugStringA "Couldn't create CLSID_DirectMusic"
   Ese CLSID es EL de DirectMusic, y Wine NO lo implementa en absoluto (en el
   payload no existe ningun dmusic.dll/dmloader.dll), asi que nunca estara
   registrado. Carencia conocida y no bloqueante: sin DirectMusic el juego
   arranca sin musica de menus.
7) Con la variante B ya instalada el juego avisa
       "DxWrapper Stub | OK | Could not find DxWrapper.dll functions will be
        disabled!"
   y vuelve al dialogo de DirectX 9.0c. Otra vez el log da la causa exacta:
       err:module:import_dll Library MSIMG32.dll (which is needed by
       L"C:\\FIFA 07\\dxwrapper.dll") not found
       err:module:import_dll Library OLEACC.dll (which is needed by ...) not found
       [NXLDR] load name=C:\\FIFA 07\\dxwrapper.dll status=c0000135
   dxwrapper.dll importa 7 DLLs (ADVAPI32, GDI32, KERNEL32, MSIMG32, OLEACC,
   SHLWAPI, USER32) y el payload no trae las dos del medio, asi que el modulo
   ENTERO no carga: no es un fallo parcial, y el stub se apaga y devuelve el
   juego al d3d8 de Wine. Solucion:
     - MSIMG32.dll propio. tools/build-fifa07-shims.py construye ahora TRES
       shims; este exporta AlphaBlend/GradientFill/TransparentBlt, que es
       exactamente lo que dxwrapper pide y solo usa en sus funciones GDI, todas
       desactivadas en dxwrapper.ini. AlphaBlend hace copia opaca por StretchBlt;
       lo demas devuelve ERROR_CALL_NOT_IMPLEMENTED y lo anota en stderr.txt.
     - OLEACC.dll de Wine, copiado del payload de pes13-fex, que ya exporta
       AccessibleObjectFromWindow y AccessibleObjectFromEvent.
   Con las dos, las 7 importaciones de dxwrapper.dll quedan satisfechas.
8) El dialogo "You will need to install DirectX 9.0c" NO era cosa del video, y la
   prueba esta en tu propio PC: con TODA la cadena del community instalada el
   juego seguia pidiendo DirectX hasta que instalaste el runtime de DirectX 9.0c,
   y solo despues arranco. Lo que ese runtime aporta y Wine no tiene es
   DIRECTMUSIC. Lo que lo confirma, medido sobre los ficheros:
     - fifa07.exe contiene UN solo GUID de DirectMusic, CLSID_DirectMusic
       ({636B9F10-0C7D-11D1-95B2-0020AFDC7421}), aparece una vez, y no hay
       ningun otro miembro de la familia ni cadenas ".dls"/"dmsynth"/"dmloader":
       no lo usa para nada funcional, es una sonda de capacidades.
     - El prefijo de Wine ya tiene EXACTAMENTE los mismos valores de version de
       DirectX que tu Windows que si funciona: Version "4.09.00.0904" e
       InstalledVersion 00 00 00 09 00 00 00 00. Asi que no es la version.
     - Wine no implementa DirectMusic en absoluto (en la SD no hay ni una
       dm*.dll), asi que la sonda falla siempre:
           err:ole:com_get_class_object class {636b9f10-...} not registered
   Solucion: dmusic.dll propio (src/shims/dmusic_fifa07.c), un servidor COM
   minimo que responde a CLSID_DirectMusic, mas la clave de registro que COM
   necesita para encontrarlo (en switch/wine/system.reg). Por ahi no suena nada
   y no hace falta: el juego reproduce la musica por DirectSound, que Wine si
9) El juego trae SU PROPIA LISTA DE SONDAS, y eso ahorra ir una por una. Son
   cadenas de depuracion dentro de fifa07.exe, y OutputDebugStringA las deja en
   el log:
       Couldn't LoadLibrary DDraw            -> funciona
       Couldn't LoadLibrary DInput           -> funciona
       Couldn't create CLSID_DirectMusic     -> arreglado en el punto 8
       Couldn't LoadLibrary dpnhpast.dll     -> ESTE era el que quedaba
   De esa lista, DirectDraw, DirectInput y DirectMusic ya pasan en el log, y
   dpnhpast.dll (el ayudante NAT de DirectPlay) era el unico que fallaba:
       warn:module:load_dll Failed to load module L"dpnhpast.dll"; status=c0000135
       OutputDebugStringA "Couldn't LoadLibrary dpnhpast.dll"
   Solucion: dpnhpast.dll propio (src/shims/dpnhpast_fifa07.c). La real es un
   servidor COM en proceso cuya tabla de exports es exactamente
   DllGetClassObject, DllCanUnloadNow, DllRegisterServer, DllUnregisterServer:
   basta un stub que exporte esas cuatro. No necesita registro, porque el juego
   la carga por nombre y la carpeta del juego gana el orden de busqueda.

   El .exe tambien nombra otras DLLs que puede cargar en otros caminos
   (XPadLib.dll, mscoree.dll, xinput9_1_0.dll, d3d8d.dll) pero ninguna aparece
   pedida en ningun log: solo cuentan las que el juego intenta de verdad.
   Ni el paso 8 ni el 9 dependen de la variante grafica.

POR QUE VARIANTE B ES AHORA LO POR DEFECTO
------------------------------------------
Tu propia copia "FIFA 07 (Steam Deck)" YA traia la receta del community dentro
de la carpeta del juego: d3d8.dll (stub de dxwrapper), dxwrapper.dll,
dxwrapper.ini con D3d8to9=1, Stub.ini, DrvMgt.dll y fifa07.wine-nx.txt
(address-space=32-bit, own-controls=1, d3d=dxvk). La SD no la tenia, y por eso
el loader del punto 6 caia al d3d8 de Wine en vez de usar el stub del juego.

Variante B (por defecto ahora) deja en drive_c/FIFA 07/ :
    d3d8.dll            stub de dxwrapper (viene de tu copia Steam Deck)
    dxwrapper.dll       nucleo de dxwrapper
    dxwrapper.ini       D3d8to9=1 -> traduce las llamadas D3D8 a D3D9
    Stub.ini            config del stub
    DrvMgt.dll          pieza de SecuROM que trae el pack del community
    fifa07.wine-nx.txt  config por juego que lee el runtime
    d3d9.dll            DXVK, copiado de drive_c/dxvk/d3d9.dll
                        <-- ESTE ES EL PASO PROPIO DE SWITCH
    MSIMG32.dll         shim propio: dxwrapper.dll lo importa y el payload no lo
                        trae (ver el punto 7 del historial)
    OLEACC.dll          oleacc de Wine, copiado del payload de pes13-fex
En Steam Deck ese d3d9.dll lo ponia Proton (DXVK). Wine-NX NO lo pone: su
syswow64/d3d9.dll es wined3d/OpenGL. Si no se copia DXVK junto al juego, la
cadena del community se queda en wined3d igual que la variante A.

Cadena completa: fifa07.exe -> d3d8.dll (stub) -> dxwrapper.dll (D3d8to9) ->
d3d9.dll (DXVK) -> Vulkan/NVK.

Variantes
---------
B) POR DEFECTO: cadena dxwrapper -> DXVK instalada en la carpeta del juego.
A) --variant-a deja el juego con el d3d8 propio de Wine (wined3d -> OpenGL),
   que es justo lo que produce el dialogo de DirectX 9.0c del punto 6.
C) Si el log muestra que el juego falla al leer sus claves EA SPORTS, el registro
   del prefijo ya se envia; anade las que falten con FIFA_07_Registry_Fix.reg o
   a mano sobre system.reg.
"""


def stage_forwarder_target(output: Path, runtime_root: Path) -> None:
    """Copy the NRO to the path an installed 32-bit-no-alias forwarder launches.

    The 32-bit, no-alias address space is an NPDM setting of the launching NSP,
    not of the NRO. docs/FEXTENDO-FORWARDER.md pins the existing forwarder to
    `/switch/pes13-fex/pes13-fex.nro`, so the diagnostic runtime is also placed
    there and can then be started from HOME with the correct memory layout.
    """
    target = output / "switch" / "pes13-fex" / "pes13-fex.nro"
    target.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(runtime_root / "wine-nx-runtime.nro", target)
    (target.parent / "SOLO-PARA-EL-FORWARDER.txt").write_text(
        "Esta copia del mismo NRO existe solo para que el forwarder\n"
        "32-bit no-alias ya instalado la arranque desde el HOME.\n"
        "El runtime real y su payload viven en sdmc:/switch/wine/ .\n", encoding="utf-8")


def apply_runtime_pair(runtime_root: Path, nro: Path | None, overlay: Path | None) -> set[str]:
    """Install a newer NRO and its matched native modules over the payload.

    The pinned release and a later test build differ in the NRO *and* in the
    Wine-side native modules it talks to (here `winebox64.dll`, whose bytes
    differ between builds). Shipping one without the other produces
    `[WOW64] native DLLs status=c0000135` at runtime, which is exactly how the
    previous attempt failed. Both come from the same extracted build folder.
    """
    overridden: set[str] = set()
    if nro:
        shutil.copy2(nro, runtime_root / "wine-nx-runtime.nro")
    if overlay and overlay.is_dir():
        for item in sorted(overlay.rglob("*")):
            if not item.is_file():
                continue
            rel = item.relative_to(overlay)
            target = runtime_root / rel
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(item, target)
            overridden.add(rel.as_posix())
    return overridden


def write_readme(output: Path) -> None:
    (output / "LEEME.txt").write_text(LEEME, encoding="utf-8")


def stage_variant_b(runtime_root: Path, overlay: Path) -> None:
    """Stage the dxwrapper -> DXVK chain without installing it."""
    staged = runtime_root / "_variant-b-dxvk"
    staged.mkdir(parents=True, exist_ok=True)
    dxvk_dll = runtime_root / "drive_c" / "dxvk" / "d3d9.dll"
    if dxvk_dll.is_file():
        shutil.copy2(dxvk_dll, staged / "d3d9.dll")
    conf = runtime_root / "drive_c" / "dxvk" / "nfsu2-hud" / "dxvk.conf"
    if conf.is_file():
        shutil.copy2(conf, staged / "dxvk.conf")
    for name in STEAMDECK_OVERLAY:
        item = overlay / name
        if item.is_file():
            shutil.copy2(item, staged / name)


def install_variant_b(runtime_root: Path, overlay: Path, game_dir: Path) -> list[str]:
    """Install the dxwrapper -> DXVK chain into the game folder (variant B).

    Wine-NX resolves an import next to the .exe first, so placing dxwrapper's
    d3d8 stub beside fifa07.exe is what moves the game off Wine's builtin d3d8
    (wined3d/OpenGL) and onto D3D9. On the Deck Proton supplied the DXVK d3d9;
    here it has to be copied from drive_c/dxvk/ explicitly, otherwise the chain
    lands back on Wine's wined3d d3d9 and nothing improves.
    """
    installed = []
    for name in STEAMDECK_OVERLAY:
        item = overlay / name
        if not item.is_file():
            raise SystemExit(
                f"variant B needs {name}, not found in {overlay}\n"
                "it comes from the game's own 'FIFA 07 (Steam Deck)' folder")
        shutil.copy2(item, game_dir / name)
        installed.append(name)
    dxvk_dll = runtime_root / "drive_c" / "dxvk" / "d3d9.dll"
    if not dxvk_dll.is_file():
        raise SystemExit(f"variant B needs DXVK's d3d9.dll at {dxvk_dll}")
    shutil.copy2(dxvk_dll, game_dir / "d3d9.dll")
    installed.append("d3d9.dll (DXVK, from drive_c/dxvk)")
    return installed


def install_dmusic_registry(runtime_root: Path, dll_path: str = DMUSIC_DLL) -> str:
    """Register the dmusic.dll shim as CLSID_DirectMusic in the prefix registry.

    Wine implements no DirectMusic whatsoever, and the prefix registry is the
    only place COM learns which module serves a class, so without this entry
    CoCreateInstance(CLSID_DirectMusic) keeps failing and FIFA 07 keeps showing
    its "install DirectX 9.0c" dialog. Written in Wine's own .reg style, next to
    the keys Wine already put there. Idempotent.
    """
    path = runtime_root / "system.reg"
    if not path.is_file():
        raise SystemExit(f"the prefix registry is missing: {path}")
    text = path.read_text(encoding="utf-8")
    if DMUSIC_CLSID in text:
        return f"CLSID_DirectMusic already present in {path.name}"

    escaped = dll_path.replace("\\", "\\\\")
    block = (
        "\n"
        f"[Software\\\\Classes\\\\CLSID\\\\{DMUSIC_CLSID}] 1791268407\n"
        "#time=1dd555c9835d580\n"
        '@="DirectMusic"\n'
        "\n"
        f"[Software\\\\Classes\\\\CLSID\\\\{DMUSIC_CLSID}\\\\InprocServer32] 1791268407\n"
        "#time=1dd555c9835d580\n"
        f'@="{escaped}"\n'
        '"ThreadingModel"="Both"\n'
        "\n"
    )
    path.write_text(text + block, encoding="utf-8")
    return f"CLSID_DirectMusic -> {dll_path}"


def install_ea_registry(game_dir: Path, runtime_root: Path) -> str:
    """Add FIFA 07's own EA SPORTS keys to the prefix registry.

    The game sizes its on-disk swap and cache files from
    `HKLM\\SOFTWARE\\EA SPORTS\\FIFA 07` (`SwapSize`, `CacheSize`, `Install Dir`,
    the registration path...). The prefix has none of that key set, so at start
    up the game reports

        FIFA 07 requires at least 1 MB of free swap file space

    and refuses to run. The values are not invented here: the game ships them as
    a Windows .reg (`FIFA_07_Registry_Fix.reg`, UTF-16, HKEY_LOCAL_MACHINE\\...
    \\WOW6432Node\\EA SPORTS\\FIFA 07) and this converts that file into Wine's
    registry format, so the numbers stay the game's own. Idempotent.
    """
    source = game_dir / "FIFA_07_Registry_Fix.reg"
    if not source.is_file():
        return "no FIFA_07_Registry_Fix.reg in the game folder; EA keys not added"
    registry = runtime_root / "system.reg"
    if not registry.is_file():
        raise SystemExit(f"the prefix registry is missing: {registry}")

    sections: list[str] = []
    current: str | None = None
    for line in source.read_text(encoding="utf-16", errors="replace").splitlines():
        line = line.strip()
        if not line or line.startswith("Windows Registry Editor") or line.startswith(";"):
            continue
        heading = re.match(r"^\[(.+?)\]$", line)
        if heading:
            key = heading.group(1)
            # Keep WOW6432Node: the game is 32-bit, and a 32-bit app asking for
            # HKLM\Software\EA SPORTS is redirected by Windows *and Wine* to
            # HKLM\Software\WOW6432Node\EA SPORTS. Writing these keys to the
            # un-redirected path leaves the game unable to find SwapSize and it
            # dies with "requires at least N MB of free swap file space".
            key = re.sub(r"^HKEY_LOCAL_MACHINE\\", "", key, flags=re.I)
            key = re.sub(r"^SOFTWARE\\", "", key, flags=re.I)
            current = "[" + ("Software\\\\" + key.replace("\\", "\\\\")) + f"] {WINE_REG_TIME}"
            sections.append(current + "\n#time=1dd555c9835d580")
            continue
        value = re.match(r'^"([^"]*)"=(.*)$', line)
        if value and current is not None:
            name, raw = value.group(1), value.group(2).strip()
            if raw.lower().startswith("dword:"):
                sections.append(f'"{name}"=dword:{raw.split(":", 1)[1].lower()}')
            else:
                sections.append(f'"{name}"="{raw.strip(chr(34))}"')
    if not sections:
        return "FIFA_07_Registry_Fix.reg had no keys to convert"

    block = "\n" + "\n".join(sections) + "\n"
    text = registry.read_text(encoding="utf-8")
    if sections[0].split("]")[0] in text:
        return "EA SPORTS\\FIFA 07 already present in system.reg"
    registry.write_text(text + block, encoding="utf-8")
    return "EA SPORTS\\FIFA 07 keys added (SwapSize, CacheSize, Install Dir...)"


def find_oleacc(explicit: Path | None) -> Path:
    """Locate Wine's own OLEACC.dll, which dxwrapper.dll needs on variant B.

    It is not built from src/shims because it already exists as a Wine binary:
    the other Wine-NX payload on the card (the PES 13 / FEXTendo fork) ships it.
    Order: an explicit path, the card, then a package built earlier - so a
    rebuild still works with the card unplugged.
    """
    candidates: list[Path] = []
    if explicit:
        candidates.append(explicit)
    rel = Path("switch") / "pes13-fex" / "drive_c" / "windows" / "syswow64" / "oleacc.dll"
    candidates += [Path(f"{d}:") / rel for d in "defgh"]
    candidates.append(ROOT / "dist" / "fifa07-diag" / "switch" / "wine"
                      / "drive_c" / "FIFA 07" / "OLEACC.dll")
    for candidate in candidates:
        if candidate.is_file():
            return candidate
    raise SystemExit(
        "variant B needs Wine's OLEACC.dll and none was found. Tried:\n  "
        + "\n  ".join(str(c) for c in candidates)
        + "\nPlug in the card (pes13-fex/.../syswow64/oleacc.dll) or pass "
          "--oleacc-source.")


def install_oleacc(source: Path, game_dir: Path) -> str:
    """Copy OLEACC.dll next to the game, after verifying it is the right one.

    dxwrapper.dll imports AccessibleObjectFromEvent/AccessibleObjectFromWindow
    from it; a wrong or 64-bit file would fail the same way the missing one did.
    """
    from importlib.util import module_from_spec, spec_from_file_location

    spec = spec_from_file_location("build_fifa07_shims",
                                  ROOT / "tools" / "build-fifa07-shims.py")
    module = module_from_spec(spec)
    spec.loader.exec_module(module)          # reuse the verified PE reader

    machine, _secs, _imports, exports = module.pe_dirs(source)
    needed = {"AccessibleObjectFromEvent", "AccessibleObjectFromWindow"}
    missing = needed - set(exports)
    if machine != 0x014C or missing:
        raise SystemExit(
            f"{source}: machine 0x{machine:04x}, missing exports {sorted(missing)}"
            f" (has {sorted(exports)}) - expected i386 exporting {sorted(needed)}")
    shutil.copy2(source, game_dir / "OLEACC.dll")
    return f"OLEACC.dll ({sha256(source)[:16]}, from {source.parent.parent.name})"


def verify(runtime_root: Path, manifest: Path,
           overridden: frozenset[str] = frozenset()) -> tuple[int, list[str], list[str], list[str]]:
    """Check the payload against the manifest.

    `overridden` names files that a newer runtime pair legitimately replaces: the
    manifest documents the pinned release, so those are reported separately
    instead of being called corrupt.
    """
    entries = json.loads(manifest.read_text(encoding="utf-8"))
    ok, missing, bad, replaced = 0, [], [], []
    for entry in entries:
        path = runtime_root / Path(entry["path"])
        if not path.is_file():
            missing.append(entry["path"])
            continue
        if entry["path"] in overridden:
            replaced.append(entry["path"])
            continue
        if path.stat().st_size != entry["bytes"] or sha256(path) != entry["sha256"]:
            bad.append(entry["path"])
        else:
            ok += 1
    return ok, missing, bad, replaced


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--runtime-archive", type=Path,
                        default=ROOT / "wine-test-build-2.zip")
    parser.add_argument("--runtime-nro", type=Path, default=None,
                        help="NRO of a newer runtime pair, used instead of the one in "
                             "the archive (e.g. the nx-wow64-dynarec-218 build)")
    parser.add_argument("--runtime-overlay", type=Path, default=None,
                        help="folder whose contents are copied over the extracted payload "
                             "(the matched native modules that ship with --runtime-nro)")
    parser.add_argument("--game", type=Path,
                        default=Path(os.path.expandvars(
                            r"%USERPROFILE%\Desktop\NINTENDO SWITCH\NRO"
                            r"\FIFA 07 (Steam Deck)\FIFA 07")))
    parser.add_argument("--output", type=Path, default=ROOT / "dist" / "fifa07-diag")
    parser.add_argument("--mirror", type=Path,
                        default=Path(os.path.expandvars(
                            r"%USERPROFILE%\Desktop\NINTENDO SWITCH\NRO\fifa07-diag")))
    parser.add_argument("--app-local-source", type=Path, default=None,
                        help="folder to take APP_LOCAL_DLLS from. Leave unset: the list is "
                             "empty on purpose, because host Windows DLLs break Wine-NX")
    parser.add_argument("--shims", type=Path, default=ROOT / "build" / "fifa07-shims",
                        help="folder holding the built DINPUT.dll/sensapi.dll shims; "
                             "run tools/build-fifa07-shims.py first")
    parser.add_argument("--prefix", type=Path,
                        default=Path(os.path.expandvars(
                            r"%USERPROFILE%\Downloads\pes13-fex")),
                        help="proven Wine-NX prefix whose system.reg/user.reg is staged")
    parser.add_argument("--include-forwarder-copy", action="store_true",
                        help="ALSO copy the NRO to switch/pes13-fex/pes13-fex.nro, the "
                             "path the installed 'PES13 - FEXTendo' forwarder launches. "
                             "OFF by default: on a card that holds PES 13 NX this would "
                             "overwrite that installation's own NRO.")
    parser.add_argument("--variant-a", action="store_true",
                        help="leave the game on Wine's builtin d3d8 through wined3d. "
                             "This is the configuration that ends in FIFA 07's "
                             "'install DirectX 9.0c' dialog; kept for comparisons only.")
    parser.add_argument("--oleacc-source", type=Path, default=None,
                        help="Wine's own OLEACC.dll to copy next to the game for "
                             "variant B. Default: search the card for the other "
                             "Wine-NX payload (pes13-fex) that ships it.")
    parser.add_argument("--no-mirror", action="store_true")
    args = parser.parse_args()

    for label, path in (("runtime archive", args.runtime_archive), ("game", args.game)):
        if not path.exists():
            raise SystemExit(f"{label} not found: {path}")

    runtime_root = args.output / "switch" / "wine"
    if args.output.exists():
        shutil.rmtree(args.output)
    runtime_root.mkdir(parents=True)

    print("[1/5] extracting logging Wine-NX runtime payload")
    extract_runtime(args.runtime_archive, runtime_root)
    overridden = apply_runtime_pair(runtime_root, args.runtime_nro, args.runtime_overlay)
    if overridden:
        print("      runtime pair applied over the pinned payload:",
              ", ".join(sorted(overridden)))

    print("[2/5] installing FIFA 07 into drive_c/FIFA 07")
    game_dir = runtime_root / "drive_c" / "FIFA 07"
    overlay = runtime_root / "_steamdeck-overlay"
    copy_game(args.game, game_dir, overlay)
    installed = (install_app_local(args.app_local_source, game_dir)
                 if (args.app_local_source and APP_LOCAL_DLLS) else [])
    print("      app-local DLLs:", ", ".join(installed) if installed
          else "none (by design: no host Windows DLL is ever shipped)")
    shims = install_shims(args.shims, game_dir)
    print("      built shims:", ", ".join(shims))
    print("      directx probe:", install_dmusic_registry(runtime_root))
    stage_variant_b(runtime_root, overlay)   # keep a copy of the chain handy
    if args.variant_a:
        print("      graphics: variant A (Wine builtin d3d8 through wined3d)")
    else:
        chain = install_variant_b(runtime_root, overlay, game_dir)
        chain.append(install_oleacc(find_oleacc(args.oleacc_source), game_dir))
        print("      graphics: variant B installed ->", ", ".join(chain))

    print("[3/5] installing the prefix registry (with CLSID_DirectMusic)")
    if args.prefix.is_dir():
        print("      registry:", install_registry(args.prefix, runtime_root))
    else:
        raise SystemExit(
            f"no Wine-NX prefix to take the registry from: {args.prefix}\n"
            "pass --prefix, e.g. --prefix E:\\switch\\wine (the card's own)")
    print("      EA keys:", install_ea_registry(game_dir, runtime_root))

    print("[4/5] writing runtime configuration")
    write_readme(args.output)
    if args.include_forwarder_copy:
        stage_forwarder_target(args.output, runtime_root)
    (runtime_root / "target.txt").write_text(
        "sdmc:/switch/wine/drive_c/FIFA 07/fifa07.exe\n", encoding="utf-8")
    (runtime_root / "args.txt").write_text(
        "C:\\FIFA 07\\fifa07.exe\n", encoding="utf-8")
    (runtime_root / "verbose.txt").write_text("1\n", encoding="utf-8")
    (runtime_root / "run-entry.txt").write_text("1\n", encoding="utf-8")
    (runtime_root / "PROVENANCE.txt").write_text(
        "FIFA 07 diagnostic package.\n"
        f"Runtime: {args.runtime_archive.name} (pinned Wine-NX, logs to\n"
        "         sdmc:/switch/wine/wine-nx-runtime.log)\n"
        "Graphics: variant B installed in drive_c/FIFA 07/ - dxwrapper's d3d8\n"
        "         stub + dxwrapper.dll (D3d8to9) + DXVK's d3d9.dll. See LEEME.txt.\n"
        "Nothing in the NRO was modified.\n", encoding="utf-8")

    print("[5/5] verifying runtime against config/runtime-files.json")
    ok, missing, bad, replaced = verify(runtime_root, ROOT / "config" / "runtime-files.json",
                                        frozenset(overridden))
    print(f"      verified={ok} missing={len(missing)} corrupt={len(bad)} "
          f"replaced-by-runtime-pair={len(replaced)}")
    for name in missing:
        print("      MISSING:", name)
    for name in bad:
        print("      CORRUPT:", name)
    for name in replaced:
        print("      REPLACED:", name)

    if bad:
        raise SystemExit("runtime payload is corrupt; refusing to ship a package")

    if not args.no_mirror:
        print(f"      mirroring to {args.mirror}")
        if args.mirror.exists():
            shutil.rmtree(args.mirror)
        shutil.copytree(args.output, args.mirror)

    total = sum(f.stat().st_size for f in args.output.rglob("*") if f.is_file())
    print(f"done: {args.output} ({total / (1 << 30):.2f} GiB)")
    print(f"note: {len(missing)} manifest entries are supplied by the Wine PE build"
          if missing else "")
    return 0


if __name__ == "__main__":
    sys.exit(main())
