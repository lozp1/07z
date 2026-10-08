# Un runtime propio por cada port (la raíz va compilada dentro)

**Regla de oro: cada port necesita SU PROPIO `wine-nx-runtime.nro`, compilado con
SU carpeta como raíz. Un runtime no se comparte entre ports.**

En la SD del usuario esto ya es la norma en los ports que funcionan:

```
sdmc:/switch/pes13-fex/           <- UNA carpeta, autosuficiente
├── pes13-fex.nro                 <- runtime COMPILADO con raiz sdmc:/switch/pes13-fex
│                                    (47 apariciones de la cadena dentro del binario)
├── configuration.ini             <- su configuracion
├── drive_c/                      <- su prefijo de Wine (KONAMI/PES13, windows/, ...)
├── share/  system.reg  user.reg  launcher/
└── wine-nx-session-*.shm
```

`sdmc:/switch/fifa07/` sigue el mismo patron con `wine-nx-runtime.nro` + `07z.nro`
(frontend) + `config/` + `drive_c/` + `logs/` + `registry/` + `share/` +
`horizon-dlls/`.

---

## 1. Por qué (la causa, ya demostrada)

El runtime Wine-NX no descubre su carpeta en tiempo de ejecución: la **lleva
compilada dentro**. La fuente única de verdad es:

```
C:\Projects\ports\autorun-src\dlls\ntdll\unix\horizon_runtime_paths.h
```

```c
#ifndef WINE_NX_SHARED_ROOT
#define WINE_NX_SHARED_ROOT "sdmc:/switch/wine"      /* <-- raiz por defecto */
#endif
#ifndef WINE_NX_RUNTIME_DOS_ROOT
#define WINE_NX_RUNTIME_DOS_ROOT "\\??\\Z:\\switch\\wine"
#endif
#define WINE_NX_RUNTIME_ROOT      WINE_NX_SHARED_ROOT
#define WINE_NX_RUNTIME_DRIVE_C   WINE_NX_RUNTIME_ROOT "/drive_c"
#define WINE_NX_RUNTIME_WINDOWS   WINE_NX_RUNTIME_DRIVE_C "/windows"
```

Todo lo demas (`config/`, `logs/`, `drive_c/`, `registry/`, el NRO del forwarder,
las fuentes NLS) deriva de `WINE_NX_SHARED_ROOT`. `runtime.c` ya no duplica la
raiz: `#define WINE_ROOT WINE_NX_SHARED_ROOT`.

**Consecuencia real (el fallo que bloqueaba FIFA 07):** aunque el frontend lanzaba
el runtime desde `sdmc:/switch/fifa07/wine-nx-runtime.nro` pasandole el juego,
aquel binario tenia `sdmc:/switch/wine` grabado dentro. Resultado en la consola:

- El runtime **recreo `sdmc:/switch/wine/`** desde cero (`config/ drive_c/
  horizon-dlls/ logs/ registry/ launcher.txt launcher-library-v2.ini target.txt`).
- Su log (`sdmc:/switch/wine/logs/autorun_runtime.log`) lo confirma:
  ```
  [BUILD] nx-amd64-fex-2640 from sdmc:/switch/fifa07/wine-nx-runtime.nro (39 bits)
  ```
  es decir: lanzado desde `fifa07`, escribiendo en `wine`.
- Por eso mostraba **su catalogo vacio** en vez de arrancar el juego.

No es un bug del frontend ni del forwarder: es el binario del runtime apuntando
a la carpeta equivocada. Se arregla recompilando el runtime con su raiz.

---

## 2. Cómo se fija la raiz al compilar

Dos opciones CMake (solo actuan si se pasan; por defecto queda igual):

```cmake
set(WINE_NX_WINE_ROOT     "" CACHE STRING "Root of the Wine prefix on the SD card")
set(WINE_NX_WINE_DOS_ROOT "" CACHE STRING "DOS (Z:) form of the root")
if(WINE_NX_WINE_ROOT)
    add_compile_definitions(WINE_NX_SHARED_ROOT="${WINE_NX_WINE_ROOT}")
endif()
if(WINE_NX_WINE_DOS_ROOT)
    add_compile_definitions(WINE_NX_RUNTIME_DOS_ROOT="${WINE_NX_WINE_DOS_ROOT}")
endif()
```

Estas opciones producen exactamente los mismos `-DWINE_NX_SHARED_ROOT=...` que se
pueden pasar a mano, y se aplican a **todos** los targets (los usa `ntdll/loader.c`,
`ntdll/unix/file.c`, `ntdll/unix/loader.c`, `win32u/font.c`, `ntdll/unix/horizon.c`
y `runtime.c`).

---

## 3. Comando exacto de compilacion (probado, `nx-amd64-fex-2640`)

Script: `C:\Projects\ports\autorun-stage6-fifa07root-final.sh`
(identico a `autorun-stage4-2players.sh` —2 jugadores + boot bundle low-window—
mas las dos banderas de raiz). El build es 100% por contenedor.

```sh
IMG="ghcr.io/autorunhq/switch-dev:2026.10.01"

# 1) sincronizar al volumen autorun-dev las fuentes actuales del host
docker run --rm -v "C:/Projects/ports/autorun-src:/host:ro" -v autorun-dev:/work alpine \
  sh -c 'cp -a /host/horizon-wine/CMakeLists.txt /work/horizon-wine/CMakeLists.txt
         cp -a /host/horizon-wine/source/runtime.c /work/horizon-wine/source/runtime.c
         cp -a /host/horizon-wine/source/input_profile.c /work/horizon-wine/source/input_profile.c
         cp -a /host/horizon-wine/source/input_profile.h /work/horizon-wine/source/input_profile.h
         cp -a /host/dlls/ntdll/unix/horizon.c /work/dlls/ntdll/unix/horizon.c
         cp -a /host/dlls/ntdll/unix/horizon_runtime_paths.h /work/dlls/ntdll/unix/horizon_runtime_paths.h'

# 2) build limpio (rm -rf) + configure con las dos banderas de raiz + build
docker run --rm -v autorun-dev:/work -w /work -e DEVKITPRO=/opt/devkitpro-release "$IMG" sh -ec '
  rm -rf horizon-wine/build-switch-amd64
  cmake -S horizon-wine -B horizon-wine/build-switch-amd64 -G Ninja \
    -DCMAKE_TOOLCHAIN_FILE=/work/horizon-wine/cmake/switch-devkitA64.cmake \
    -DWINE_NX_PE_BUILD_DIR=/work/horizon-wine/build-wine-amd64-pe \
    -DWINE_NX_AMD64=ON -DWINE_NX_FEX=1 -DWINE_NX_BOX64_INTERPRETER=ON -DWINE_NX_BOX64_DYNAREC=ON \
    -DWINE_NX_USB_STORAGE=ON \
    -DWINE_NX_WINE_ROOT="sdmc:/switch/fifa07" \
    -DWINE_NX_WINE_DOS_ROOT="\\\\??\\\\Z:\\\\switch\\\\fifa07" \
    -DWINE_NX_BOOT_BUNDLE=/work/horizon-wine/toolchains/boot-payloads/bundle \
    -DCMAKE_BUILD_TYPE=Release
  cmake --build horizon-wine/build-switch-amd64 --target wine-nx-runtime-nro -j"$(nproc)"'

# 3) sacar el NRO del volumen a disco
docker run --rm -v autorun-dev:/work -v "C:/Projects/ports/runtime-fifa07root:/out" alpine \
  sh -c 'cp /work/horizon-wine/build-switch-amd64/wine-nx-runtime.nro /out/wine-nx-runtime.nro'
```

**Para el port de otro juego**, cambia SOLO las dos banderas de raiz por su
carpeta (`-DWINE_NX_WINE_ROOT="sdmc:/switch/<port>"` +
`-DWINE_NX_WINE_DOS_ROOT="\\\\??\\\\Z:\\\\switch\\\\<port>"`) y el nombre del
directorio de salida. Todo lo demas igual.

`-DWINE_NX_BOOT_BUNDLE` es obligatorio: mete dentro del NRO el paquete de
arranque Atmosphere+HOC con el **parche low-window** (el que concede a
`0548EABB35576000` la ventana baja de 0x400000; sin el, `fifa07.exe` no se mapea).
El bundle del volumen (`toolchains/boot-payloads/bundle`) es byte-identico al que
usaba el runtime que funcionaba (`mesosphere.bin = fa025ce4…`), asi que se reusa.

---

## 4. Verificar el binario ANTES de desplegarlo

```sh
NRO=wine-nx-runtime.nro
stat -c%s "$NRO"                                   # ~42.95 MB (42.951.736 B con bundle)
xxd -l 32 "$NRO"                                   # cabecera: "NRO0" en 0x10
grep -a -o 'sdmc:/switch/fifa07'          "$NRO" | wc -l   # raiz correcta presente
grep -a -o 'sdmc:/switch/fifa07/drive_c'  "$NRO" | wc -l   # >=1
grep -a -o 'sdmc:/switch/wine/config'     "$NRO" | wc -l   # DEBE ser 0
grep -a -o 'sdmc:/switch/wine/logs'       "$NRO" | wc -l   # DEBE ser 0
grep -a -o '[LOWVA]'                      "$NRO" | wc -l   # low-window presente
sha256sum "$NRO"
```

(Siguen quedando unas pocas cadenas `sdmc:/switch/wine` inertes en el
**catalogo del launcher / forwarder / LSFG** — ver el anexo de
`DISTRIBUCION.md` §6. No son la raiz del runtime y no bloquean el arranque
invisible, porque el frontend lanza el juego con `argv[1]` y
`run-the-chosen-program=true`.)

---

## 5. Desplegar y dejar la SD con UNA sola carpeta

```sh
SD=/d/switch/fifa07
cp -v "$SD/wine-nx-runtime.nro" "$SD/wine-nx-runtime.nro.bak-antes-raiz-fifa07"   # copia del actual
cp -v runtime-fifa07root/wine-nx-runtime.nro "$SD/wine-nx-runtime.nro"
sha256sum "$SD/wine-nx-runtime.nro"                     # debe coincidir con el de arriba
rm -rf /d/switch/wine                                   # borrar la carpeta que el runtime viejo recreo
ls /d/switch/ | grep -i wine                            # no debe quedar nada
```

Y comprobar que el arranque directo queda configurado:

- `sdmc:/switch/fifa07/target.txt`          -> `sdmc:/switch/fifa07/drive_c/FIFA 07/fifa07.exe`
- `sdmc:/switch/fifa07/launcher-library-v2.ini` -> el juego apunta al mismo `.exe`
- `sdmc:/switch/fifa07/config/settings.json` -> `"run-the-chosen-program": true`
  (arranca el programa elegido en vez de mostrar el catalogo)
- existe `sdmc:/switch/fifa07/drive_c/FIFA 07/fifa07.exe`

---

## 6. Anexo — sitios con la raiz todavia fija (no bloquean)

Cambio quirurgico: solo se movio la raiz del **runtime**. Estos ficheros siguen
con `sdmc:/switch/wine` y solo importan si se usa **el catalogo/menu de Wine**,
que en este producto no se muestra:

| Fichero | Constante | Uso |
|---|---|---|
| `horizon-wine/source/forwarder_launch.h` | `AUTORUN_NRO` | forwarder que crea el launcher |
| `horizon-wine/source/launcher_list.h`    | `LAUNCHER_DRIVE_C` | catalogo del launcher |
| `horizon-wine/source/launcher.c`, `launcher_console.c`, `lsfg.cpp` | varios textos/cache | launcher y LSFG |
| `source/main.cpp`, `*_smoke.c`, `pe_*.c` | varios | ejecutables de prueba (no se distribuyen) |

Si algun dia se quiere mover la raiz al 100%, se les aplica el mismo guion
(`WINE_NX_SHARED_ROOT "/..."` incluyendo el header) y se recompila.
