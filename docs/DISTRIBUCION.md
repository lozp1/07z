# Distribucion final de FIFA 07 NX (portable `fifa07`)

Estado: **HECHO, FUNCIONANDO Y LISTO PARA REPARTIR**. El runtime se ha
recompilado con la raiz `sdmc:/switch/fifa07` **compilada dentro**, se ha
desplegado en la SD y se ha borrado la carpeta `sdmc:/switch/wine` que el runtime
viejo recreaba. Detalle en la seccion 6 y en el documento hermano
`docs/RUNTIME-RAIZ-POR-PORT.md`. Arranque, pantalla (16:9), mandos y rendimiento
estan cerrados; ver la seccion 0.

---

## 0. Estado final (lo que hay que repartir)

### Instalacion del usuario final (3 pasos, sin nada mas)

1. **Atmosphere con sigpatches** ya instalado (usa su `sysMMC` o su `emuMMC`).
2. **Copiar la carpeta** `fifa07` a `sdmc:/switch/fifa07/` y meter dentro su
   propia copia de FIFA 07.
3. **Instalar el `.nsp`** del forwarder (`07z-forwarder.nsp`).

**NO necesita**: particiones nuevas, **kips**, overclock, ni pasar por el
asistente de *setup* de Autorun. El `config/settings.json` que va dentro de la
carpeta ya lleva `setup-complete=1`, `run-the-chosen-program=true` y
`reopen-the-launcher-on-exit=false`, asi que el arranque es directo.

**Arranque**: encender -> Hekate -> su entrada de CFW -> **icono `07z` en el
HOME** -> frontend propio -> runtime + juego, con Wine **invisible**. **Nunca**
lanzar desde el Homebrew Menu (applet de 64 bits -> *"address space unavailable"*).

### Pantalla (el hallazgo del dia)

FIFA 07 tiene **UN solo modo 16:9 nativo: `1280x720`**. En el juego:
*Mi FIFA 07 -> Ajustes -> Pantalla* y elegir **1280x720** (una vez; el juego lo
guarda en su perfil). **NO** 1280x1024 (es 5:4 y deja barras negras). El runtime
**no estira** (escala con `min()` y centra), asi que con contenido no-16:9 las
barras son inevitables. Tabla de modos en `fifa07.exe` ~offset `0x4c42e8`
(registros de 16 B: `W:u16, 0000, H:u16, 20 00 00 00`). El perfil vive en
`drive_c/users/steamuser/Documents/FIFA 07/A. Profiles/A. Profiles`
(`OPTIONS/RESOLUTION=<n>`, indice 0-based); **no editarlo a mano** (checksum).

### Rendimiento

**55-60 FPS** estables en partido con graficos y resolucion en **ALTO** + el
overclock del usuario (UltraHand / lo que use; **el port NO lo exige**). Los
bajones de los menus 3D **no eran CPU/GPU**: eran **compilacion de shaders** y
**I/O de la SD**. Aplicado: `sync=horizon`, `four-cores=1`, `frame-limit=60` en
`fifa07.wine-nx.txt`, y un `dxvk.conf` junto al `.exe` con
`dxvk.numCompilerThreads=4`, `dxvk.enableStateCache=True`,
`d3d9.maxFrameLatency=2`. DXVK en uso: build `v3.1-17-g878473ba` (etiquetado
como version 2.3).

### Mandos (mapa final)

`keys.txt` en las 3 rutas (`sdmc:/switch/fifa07/`, `.../config/`, `.../drive_c/FIFA 07/`),
`input-mode=2` (teclado sintetizado) + shim `DINPUT.dll` junto al `.exe`.
Ver la tabla en §5.

### NO romper nunca

`fifa07.exe` (md5 `cc271e0a1b05b3d17b0415ce3aa0d33f` = fabrica), el puente
grafico (`d3d8.dll` + `dxwrapper.dll` + `dxwrapper.ini` + `d3d9.dll` DXVK
v3.1-17), los shims `DINPUT.dll` y `dmusic.dll`, los `keys.txt`, ni el mod de
audio mexicano (`data/audio/audio.big`, `data/audio/dat_mex.big`,
`data/cmn/fe/mex.db`, `config.dat`).

---

## 1. Objetivo

Que un usuario final:

1. descargue **una sola carpeta** llamada `fifa07` y la pegue en `sdmc:/switch/`,
2. instale **un** NSP,
3. pulse el icono en el HOME y **vea su frontend (marca 07z)**, y desde ahi
   arranque el juego.

Durante todo el flujo **Wine no se ve nunca**: ni catalogo de Autorun, ni
pantallas de Wine, ni ningun menu intermedio. Se siente como un juego nativo.

---

## 2. Estructura final de carpetas (objetivo: una sola carpeta)

```
sdmc:/switch/fifa07/                 <- LA UNICA CARPETA PORTABLE
├── wine-nx-runtime.nro              # runtime Wine-NX (raiz de Wine = esta carpeta)
├── 07z.nro                       # EL FRONTEND (marca 07z).  <- el NRO del frontend va AQUI
├── config/                          # settings.json, keys.txt, ...
│   └── settings.json
├── drive_c/                         # el prefijo de Wine
│   ├── FIFA 07/                     # <-- EL USUARIO PONE AQUI SU JUEGO
│   │   ├── fifa07.exe               #     (no se distribuye; es suyo)
│   │   ├── fifa07.wine-nx.txt       #     ajustes por juego (dxvk-hud, etc.)
│   │   ├── fifa07.keys.txt          #     mapa de teclado  (mando -> tecla)
│   │   ├── fifa07.player2.keys.txt  #     mapa del jugador 2 (2 Joy-Con)
│   │   └── ...                      #     resto de la instalacion del juego
│   ├── windows/                     # modulos Wine del paquete (system32, syswow64)
│   └── users/steamuser/             # perfil que el runtime espera
├── share/wine/                      # fuentes y datos NLS del paquete
└── logs/                            # autorun_runtime.log, horizon-trace.log
```

Notas:

- El runtime resuelve **todas** sus rutas relativas a la carpeta donde vive su
  `.nro` (raiz configurable, seccion 6). Por eso todo cuelga de `fifa07/`.
- `07z.nro` vive **dentro** de la misma carpeta para cumplir "una sola
  carpeta". Su log (`fifa07nx.log`) tambien se escribe ahi.
- `drive_c/FIFA 07/` puede venir **vacia** en el paquete descargable; el usuario
  deja dentro su propia copia de FIFA 07.

### Compatibilidad con la instalacion actual

El runtime que **ya esta compilado** tiene la raiz fijada a `sdmc:/switch/wine`.
Mientras no se recompile (seccion 6), la carpeta portable funciona igual pero
**con la raiz en `sdmc:/switch/wine`**. Para no romper nada, el frontend resuelve
la raiz asi:

- si existe `sdmc:/switch/fifa07/wine-nx-runtime.nro` -> raiz = `sdmc:/switch/fifa07`
- si no, si existe `sdmc:/switch/wine/wine-nx-runtime.nro` -> raiz = `sdmc:/switch/wine`
- si no, por defecto `sdmc:/switch/fifa07`

Asi el **mismo** `07z.nro` sirve para las dos disposiciones: hoy (runtime en
`wine`) y en cuanto se recompile el runtime (todo en `fifa07`).

---

## 3. Cadena de arranque

```
HOME (icono "07z")
        │  NSP forwarder (AddressSpaceType=3, 39-bit no-alias, 4 cores)
        ▼
07z.nro  (frontend, 07z)      <-- modo APLICACION (39-bit, ventana baja libre).
        │                              Marca 07z visible.
        │  envSetNextLoad(runtime, "runtime" "fifa07.exe")
        ▼
wine-nx-runtime.nro  +  fifa07.exe   <-- el runtime entra DIRECTO al juego:
        │                                  con argv[1] NO abre su catalogo/menu.
        ▼
FIFA 07  (Wine invisible; se siente nativo)
        │  al salir, el runtime termina -> vuelve al HOME
        ▼
HOME
```

Clave: el NSP **ya no** lanza el runtime directamente, lanza **el frontend**.
El frontend es quien hace el hand-off invisible al runtime pasandole el juego.

### Por que el NSP es imprescindible (applet vs aplicacion)

`fifa07.exe` tiene `IMAGE_FILE_RELOCS_STRIPPED=1`: solo se mapea en su
`ImageBase` (0x400000). Lo que necesita es que **0x400000 este libre**, no un
espacio de 32 bits: el runtime es AArch64 y quiere vivir por encima de 4 GiB
dejando la "ventana baja" para las imagenes Win32. Eso lo decide el NPDM de
**quien lanza la cadena**, no el runtime (y el propio runtime lo comprueba:
`address_space_bits == 39` en `launcher_setup.c`):

- **NSP / icono del HOME** -> `AppletType_Application`, **39-bit no alias**
  (`AddressSpaceType=3`) **y** con el program id que el parche low-window de
  Atmosphere reconoce (`HasAutorunLowWindow() == 0x0548EABB35576000`, el del
  forwarder "main" del propio runtime). Asi la region ASLR empieza en 0x200000 ->
  0x400000 queda libre -> **se juega**. `AddressSpaceType=3` es lo que escribe el
  generador de forwarders del propio runtime (`forwarder.c`: `3u <<
  ADDRESS_SPACE_SHIFT`); el program id lo fija `tools/build-fifa07-forwarder.py`.
- **NSP con otro title id** (un forwarder normal, derivado de la ruta del NRO) ->
  sigue siendo 39-bit, pero **sin** ventana baja: la *alias code region* empieza en
  0x08000000 y el runtime rechaza el juego con "Address space unavailable"
  (`[LOWVA] stock layout` en su log). Es lo que pasaba antes de este arreglo.
- **Homebrew Menu (hbmenu) / nx-hbloader** -> applet con otra base ASLR (0x400000
  ocupado) -> el runtime no puede mapear el juego. **Desde ahi NO es posible
  jugar.**
- **AddressSpaceType=2 (32-bit no alias)** -> el loader muere en el hand-off con
  `User Break` / `Result 0xD401` (`InvalidMemoryState`). Ver
  `docs/FORWARDER-39BIT-FIX.md`.

La ventana baja la concede el parche low-window de Atmosphere
(`atmosphere/mesosphere.bin` + `atmosphere/kips/autorun-loader.kip`), que **solo**
se la da al program id 0x0548EABB35576000. Ese parche es obligatorio para jugar;
sin el no hay forma de mapear `fifa07.exe` en 0x400000.

> **NOTA (estado final, 2026-10-07):** el reparto final **ya no pide instalar ese
> parche ni ningun kip**. La cadena 07z (`07z-forwarder.nsp`, con el program id
> `0548EABB35576000`, + el runtime con la raiz `fifa07` compilada dentro) resuelve
> por si sola el espacio de direcciones del juego; el usuario final solo necesita
> Atmosphere con **sigpatches**. Este apartado se conserva como explicacion
> tecnica del **por que** (y de por que el Homebrew Menu **no** sirve). Si en
> consola apareciera *"Address space unavailable"* con el NSP de 07z, entonces si
> habria que volver a revisar esta parte (ventana baja / program id).

Por eso, lanzado como applet, el frontend **no** abre el catalogo de Wine (para
no mostrar nada de Wine): muestra un aviso "Abre desde el menu de inicio".

---

## 4. Que copia el usuario (y que NO)

**El usuario copia:**

1. La carpeta `fifa07` completa a `sdmc:/switch/` (runtime, `config/`, prefijo
   `drive_c/` con `windows/`, `share/wine/`, su `07z.nro`).
2. Su instalacion **propia** de FIFA 07 dentro de `sdmc:/switch/fifa07/drive_c/FIFA 07/`
   (`fifa07.exe` + datos + DLLs del juego).
3. Instala `07z-forwarder.nsp` (via DBI / Goldleaf / Tinfoil / Awoo).

**El usuario NO copia / NO se distribuye:**

- `fifa07.exe` ni **ningun dato del juego** (copyright: el juego es propiedad de
  cada usuario; el paquete solo trae el runtime y el frontend).
- `prod.keys` ni claves de consola.
- Nada a `sdmc:/switch/wine/` (salvo que quiera conservar la instalacion antigua;
  son independientes).

---

## 5. Instalacion y desinstalacion

### Instalacion (pasos exactos del usuario final)

1. **Copia** la carpeta `fifa07` a la SD: `sdmc:/switch/fifa07/`.
2. **Pon tu juego**: copia tu FIFA 07 (PC) dentro de
   `sdmc:/switch/fifa07/drive_c/FIFA 07/`, de forma que exista
   `sdmc:/switch/fifa07/drive_c/FIFA 07/fifa07.exe`.
3. (Opcional) ajusta `fifa07.wine-nx.txt` / `fifa07.keys.txt` desde el propio
   frontend (pantalla Configuracion) o editando esos ficheros.
4. **Instala el NSP** `07z-forwarder.nsp` con tu instalador habitual.
5. En el **HOME** aparece el icono **07z**. Pulsalo.
6. Se abre **tu frontend (07z)**; pulsa **Jugar**. El juego arranca **sin ver
   nada de Wine**. Al salir del juego vuelves al HOME.

> Regla de oro: **para jugar, siempre desde el icono del HOME**. Abrirlo desde el
> Homebrew Menu no permite jugar (ver seccion 3).

### Controles (mapa final, `keys.txt`)

`input-mode=2` (teclado sintetizado) + shim `DINPUT.dll` junto al `.exe`. El mismo
`keys.txt` va en las 3 rutas (`sdmc:/switch/fifa07/`, `.../config/`,
`.../drive_c/FIFA 07/`).

| Boton Switch | Tecla (scancode) | En menus | En partido |
|---|---|---|---|
| **A** | `0x0d + 0x53` (ENTER + S) | Confirmar | Pase |
| **B** | `0x44` (D) | — (atras = PLUS) | Tiro / entrada |
| **X** | `0x57` (W) | — | Pase filtrado / salida del portero |
| **Y** | `0x41` (A) | — | Centro / pase largo |
| **R** | `0x45` (E) | — | Sprint |
| **L** | `0x10` (Mayus) | — | Regate / skill move |
| **ZR** | `0x20` (ESPACIO) | — | reservado (FIFA 07 no usa ESPACIO) |
| **ZL** | `0x53` (S) | — | Pase (redundante con A) |
| **PLUS** | `0x1b` (ESCAPE) | Atras | Pausa |
| **MINUS** | `0x0d` (ENTER) | Confirmar | — |
| **Cruceta / Stick izq.** | Flechas (`0x26/0x28/0x25/0x27`) | Navegar | Mover |
| **Clic stick izq.** (STICKL) | `0x5a` (Z) | — | Amago (dummy) |
| **Clic stick der.** (STICKR) | `0x43` (C) | — | Control de ritmo |

- **A es un acorde** (ENTER **+** S): en menu FIFA vale ENTER, en partido vale S.
- **B ya NO lleva ESCAPE** (era lo que hacia que "A/B no hicieran nada").
- **A proposito NO se mapean** la tecla **Q** (tacticas) ni el **teclado
  numerico** (comparte scan codes con las flechas y disparaba las tacticas).

### Desinstalacion

1. Desinstala el NSP del HOME (Ajustes de datos / tu instalador).
2. Borra la carpeta `sdmc:/switch/fifa07/` completa.
3. No queda nada mas: el port no escribe fuera de esa carpeta (log incluido).

---

## 6. Ruta base del runtime: compilada dentro (COMPILADO Y DESPLEGADO)

### Fuente unica de verdad

El runtime ya tenia **una** constante raiz, pero estaba duplicada en varios
sitios. Se ha centralizado en el header que ya compartian todos los modulos:

`C:\Projects\ports\autorun-src\dlls\ntdll\unix\horizon_runtime_paths.h`

```c
#ifndef WINE_NX_SHARED_ROOT
#define WINE_NX_SHARED_ROOT "sdmc:/switch/wine"
#endif
/* DOS form (Z: es la raiz unix): solo para fuentes. */
#ifndef WINE_NX_RUNTIME_DOS_ROOT
#define WINE_NX_RUNTIME_DOS_ROOT "\\??\\Z:\\switch\\wine"
#endif
#define WINE_NX_RUNTIME_ROOT      WINE_NX_SHARED_ROOT
#define WINE_NX_RUNTIME_DRIVE_C   WINE_NX_RUNTIME_ROOT "/drive_c"
#define WINE_NX_RUNTIME_WINDOWS   WINE_NX_RUNTIME_DRIVE_C "/windows"
#define WINE_NX_RUNTIME_SYSTEM32  WINE_NX_RUNTIME_WINDOWS "/system32"
#define WINE_NX_RUNTIME_SYSWOW64  WINE_NX_RUNTIME_WINDOWS "/syswow64"
#define WINE_NX_RUNTIME_NRO       WINE_NX_RUNTIME_ROOT "/wine-nx-runtime.nro"
```

`runtime.c` deja de duplicar la raiz y la toma del header:

```c
#define WINE_ROOT WINE_NX_SHARED_ROOT      /* antes: "sdmc:/switch/wine" */
```

Y `dlls/ntdll/unix/horizon.c` (tambien dentro del runtime) usa el header para
sus dos rutas absolutas: el fichero de sesion compartida
(`.../wine-nx-session-%u.shm`) y el log de trazas (`.../logs/horizon-trace.log`).

### Como se fija la raiz

Se anaden dos opciones CMake que **solo actuan si se pasan** (por defecto, todo
queda exactamente igual):

```cmake
set(WINE_NX_WINE_ROOT "" CACHE STRING "...")
set(WINE_NX_WINE_DOS_ROOT "" CACHE STRING "...")
if(WINE_NX_WINE_ROOT)
    add_compile_definitions(WINE_NX_SHARED_ROOT="${WINE_NX_WINE_ROOT}")
endif()
if(WINE_NX_WINE_DOS_ROOT)
    add_compile_definitions(WINE_NX_RUNTIME_DOS_ROOT="${WINE_NX_WINE_DOS_ROOT}")
endif()
```

`add_compile_definitions` se aplica a **todos** los targets del proyecto, que es
lo necesario porque `horizon_runtime_paths.h` lo incluyen `ntdll/loader.c`,
`ntdll/unix/file.c`, `ntdll/unix/loader.c`, `win32u/font.c`,
`ntdll/unix/horizon.c` y `runtime.c`.

### El cambio NO rompe lo actual (verificado)

Por defecto el preprocesador produce **exactamente** las mismas cadenas literales
que antes (concatenacion de literales adyacentes), p. ej.
`WINE_NX_RUNTIME_SYSTEM32` -> `"sdmc:/switch/wine" "/drive_c" "/windows" "/system32"`.
Comprobado con el preprocesador de devkitA64:

```
DEFAULT:  WINE_NX_SHARED_ROOT       = "sdmc:/switch/wine"
          WINE_NX_RUNTIME_SYSTEM32  = "sdmc:/switch/wine" "/drive_c" "/windows" "/system32"
          WINE_NX_RUNTIME_DOS_ROOT  = "\\??\\Z:\\switch\\wine"
OVERRIDE: WINE_NX_SHARED_ROOT       = "sdmc:/switch/fifa07"
          WINE_NX_RUNTIME_DOS_ROOT  = "\??\Z:\switch\fifa07"
```

### Recompilar el runtime con la raiz `fifa07` (HECHO)

Hecho con `C:\Projects\ports\autorun-stage6-fifa07root-final.sh`: build **limpio**
(`rm -rf build-switch-amd64`), mismo configure que `autorun-stage4-2players.sh`
(2 jugadores + boot bundle low-window) mas las dos banderas de raiz. El build es
100% por contenedor (imagen `ghcr.io/autorunhq/switch-dev`, volumen `autorun-dev`,
PE build + FEX + box64). Comando completo, paso a paso, en
`docs/RUNTIME-RAIZ-POR-PORT.md` §3.

> Nota de la sesion: Docker si arranca en esta maquina. El anterior "PENDIENTE:
> Docker caido" era del entorno donde se escribio este documento; aqui se pudo
> compilar y desplegar.

Comando (identico a `autorun-stage4-2players.sh`, mas las dos banderas nuevas):

```sh
docker run --rm -v autorun-dev:/work -w /work -e DEVKITPRO=/opt/devkitpro-release \
  ghcr.io/autorunhq/switch-dev:2026.10.01 sh -ec '
  cmake -S horizon-wine -B horizon-wine/build-switch-amd64 -G Ninja \
    -DCMAKE_TOOLCHAIN_FILE=/work/horizon-wine/cmake/switch-devkitA64.cmake \
    -DWINE_NX_PE_BUILD_DIR=/work/horizon-wine/build-wine-amd64-pe \
    -DWINE_NX_AMD64=ON -DWINE_NX_FEX=1 -DWINE_NX_BOX64_INTERPRETER=ON -DWINE_NX_BOX64_DYNAREC=ON \
    -DWINE_NX_USB_STORAGE=ON \
    -DWINE_NX_WINE_ROOT="sdmc:/switch/fifa07" \
    -DWINE_NX_WINE_DOS_ROOT="\??\Z:\switch\fifa07" \
    -DWINE_NX_BOOT_BUNDLE=/work/horizon-wine/toolchains/boot-payloads/bundle \
    -DCMAKE_BUILD_TYPE=Release
  cmake --build horizon-wine/build-switch-amd64 --target wine-nx-runtime-nro -j"$(nproc)"'
```

**Artefacto compilado y desplegado:**

- Ruta (build): `C:\Projects\ports\runtime-fifa07root\wine-nx-runtime.nro`.
- Copia en la SD: `sdmc:/switch/fifa07/wine-nx-runtime.nro`.
- Tamano: **42.951.736 B**.
- sha256: `f6c58bfcfe6ba622e179e828c5327feb5d12742baaa80c9950e42b8d859069d3`.
- Marca de build: `nx-amd64-fex-2640` (AMD64/FEX) + `[LOWVA]` (low-window dentro).
- 0 errores. Avisos: el conjunto es **identico** al de un build sin las banderas
  de raiz (diff de logs: 3538 = 3538; el cambio de raiz no anade ni quita
  ninguno).

Prueba de que la raiz compilada es la correcta (`grep` sobre el binario):

```
sdmc:/switch/fifa07                    53
sdmc:/switch/fifa07/drive_c            31
sdmc:/switch/fifa07/config              2
sdmc:/switch/fifa07/logs                7
sdmc:/switch/wine/config                0   <- la raiz vieja ya NO se usa
sdmc:/switch/wine/logs                  0
cuerpo \"NRO0\" @0x10                    OK (cabecera NRO valida)
```

**Respaldos:** del runtime anterior en la SD,
`sdmc:/switch/fifa07/wine-nx-runtime.nro.bak-antes-raiz-fifa07`
(`sha256 = 7ddd34476892598e4f9a1ff6cc70b9568ab7b39107cef72a0190e056cd981355`,
42.947.640 B); del build previo de 2 jugadores (raiz `wine`),
`C:\Projects\ports\runtime-2players\wine-nx-runtime.nro`
(`sha256 = 8bba69384ca3437105bc223604fcf50c63e959be78795ac27970cf26229b639d`,
42.951.736 B).

### Sitios con la raiz aun fija (no bloquean el arranque invisible)

Estos no se han tocado a proposito (cambio quirurgico); solo importan si se usa
**el catalogo/launcher de Wine**, que en este producto NO se muestra:

| Fichero | Constante | Uso |
|---|---|---|
| `horizon-wine/source/forwarder_launch.h` | `AUTORUN_NRO` | forwarder que crea el launcher de Wine |
| `horizon-wine/source/launcher_list.h`  | `LAUNCHER_DRIVE_C` | catalogo del launcher |
| `horizon-wine/source/launcher.c`, `launcher_console.c`, `lsfg.cpp` | varios | textos/cache del launcher y LSFG |
| `source/main.cpp`, `*_smoke.c`, `pe_*.c` | varios | ejecutables de prueba, no se distribuyen |

Si algun dia se quiere mover la raiz **por completo**, basta aplicarles el mismo
guion (`WINE_NX_SHARED_ROOT "/..."`, incluyendo el header).

---

## 7. Frontend: lanzamiento invisible (CAMBIO APLICADO Y RECOMPILADO)

Fichero: `C:\Projects\ports\fifa07\frontend-nx\source\main_borealis.cpp`

### Raiz unica derivada (una sola constante)

```cpp
static const char* PRODUCT_ROOT = "sdmc:/switch/fifa07";
static const char* LEGACY_ROOT  = "sdmc:/switch/wine";
static const std::string& wineRoot();          // resuelve una vez (fifa07 -> wine -> fifa07)
static std::string winePath(const char* rel);  // raiz + relativa
```

Todas las rutas (`runtime`, `fifa07.exe`, `fifa07.wine-nx.txt`,
`fifa07.keys.txt`, `keys.txt`, `config/keys.txt`, `mkdir`) se derivan de ahi.

### `launchGame()` (comportamiento final)

- **Modo aplicacion (NSP / HOME, 32-bit):**
  ```cpp
  envSetNextLoad(runtime, "\"" + runtime + "\" \"" + game + "\"");
  ```
  Lanza el runtime **pasandole el `.exe` del juego como argv[1]**, asi el runtime
  entra **directo al juego sin mostrar su catalogo** (nada de Wine). Luego
  `quit()` cede el control.
- **Modo applet (Homebrew Menu, 64-bit):** NO se puede jugar -> **no se abre
  nada de Wine**; se muestra un aviso y el frontend se queda. *(Este era el
  unico punto que mostraba Wine: antes abria el catalogo del runtime.)*

### Recompilado

```sh
# desde el shell MSYS2 de devkitPro
cd /c/Projects/ports/fifa07/frontend-nx/build && ninja 07z.nro   # -> exit 0
```

Artefacto: `C:\Projects\ports\fifa07\frontend-nx\07z.nro`
(14.640.223 B, sha256 `a3495cafe6d99d522386f3b0a83d8409d616dbcb6d8853d3924314bcf1cfd79a`).

---

## 8. NSP forwarder (CAMBIO APLICADO Y REGENERADO)

> Artefacto e id **actuales**: `dist/fifa07-forwarder/07z-forwarder.nsp`,
> sha256 `16c912f006c2f8548f4122a981d8dca682d1e5cea37d527db73460d0017cb0e0`,
> title id `0548EABB35576000` (el que reconoce el parche low-window). Toda la
> justificación está en `docs/FORWARDER-39BIT-FIX.md`; lo de abajo es histórico y
> corresponde a una generación anterior del fichero.

Fichero: `C:\Projects\ports\fifa07\tools\build-fifa07-forwarder.py`
El icono del HOME ahora lanza **el frontend**, no el runtime:

```python
NRO_PATH  = 'sdmc:/switch/fifa07/07z.nro'   # antes: switch/wine/wine-nx-runtime.nro
USER_ARGS = ''                                  # el frontend decide el juego
NEXT_ARGV = NRO_PATH
```

Regenerado con `DEVKITPRO=C:/devkitPro python tools/build-fifa07-forwarder.py --keys <prod.keys>`.
Artefacto: `C:\Projects\ports\fifa07\dist\fifa07-forwarder\07z-forwarder.nsp`
(247.512 B, sha256 `8dd02912cf468939de9a75a9c03b54c553b4381ade7a8f26235dd097e0c7365e`,
title_id `051d3b463f87c000`, nextNroPath `sdmc:/switch/fifa07/07z.nro`).
Copia anterior (lanzaba el runtime directo): `*.bak-wine-direct`.

---

## 9. Estado, riesgos y pendiente

**Aplicado y verificado**

- Documento este (actualizado) + `docs/RUNTIME-RAIZ-POR-PORT.md` (nuevo: el patron
  de "un runtime por port").
- Runtime: raiz centralizada y configurable (header + CMake), *default*
  byte-identico (verificado con preprocesador) y **recompilado hoy con la raiz
  `fifa07`** (0 errores; avisos identicos al baseline).
- **SD ordenada**: `sdmc:/switch/fifa07/wine-nx-runtime.nro` = runtime nuevo
  (sha256 `f6c58bfc…`); `sdmc:/switch/wine/` **borrada**; respaldos del binario
  anterior en la propia carpeta.
- Arranque directo: `target.txt`, `launcher-library-v2.ini` y
  `config/settings.json` (`"run-the-chosen-program": true`) apuntando a
  `sdmc:/switch/fifa07/drive_c/FIFA 07/fifa07.exe`.
- Frontend (07z), forwarder, keys.txt, mapa de controles, overclock y
  `cfg_pc_*.ini` del juego: **NO tocados**.

**Pendiente**

- Prueba en **hardware** de la cadena NSP -> frontend -> juego
  (`device_tested=false`): es lo unico que no se puede cerrar desde aqui.
- Aplicar el mismo guion a los ficheros de la tabla de la seccion 6 si se quiere
  mover la raiz al 100% (incluido el launcher de Wine).

**Riesgos**

- Si se instala el frontend fuera de `fifa07` (p. ej. en `switch/07z/`), el
  icono del HOME no lo encontrara: `nextNroPath` es fijo a `switch/fifa07/07z.nro`.
- ~~Doble raiz transitoria~~ **RESUELTO**: el runtime ya tiene la raiz `fifa07`
  compilada dentro, asi que la carpeta `fifa07` es autosuficiente y
  `sdmc:/switch/wine/` ha desaparecido.
- El runtime y su `winebox64.dll` emparejado deben ir **juntos** (ver
  `dist/fifa07-diag/LEEME.txt`); mezclar builds mata el arranque
  (`c0000135` / `c000007b`).
- Legal: el paquete no incluye ni `fifa07.exe` ni datos del juego.

---

## 10. Build reproducible (comandos)

Runtime (contenedor; raiz `fifa07`): ver seccion 6.
Frontend (local, devkitPro):

```sh
cmake -B frontend-nx/build -S frontend-nx -DCMAKE_BUILD_TYPE=Release -DPLATFORM_SWITCH=ON
ninja -C frontend-nx/build 07z.nro
```

Forwarder (local):

```sh
DEVKITPRO=C:/devkitPro python tools/build-fifa07-forwarder.py --keys C:/Users/<user>/.switch/prod.keys
```

---

*Referencias: `dist/fifa07-diag/LEEME.txt` (flujo real confirmado en consola),
`docs/frontend-nx-filezzz.md`, `docs/FEXTENDO-FORWARDER.md`.*

---

## 11. Arranque directo: recuperar el DXVK que funcionaba (crash 00409F9B)

Al mover el prefijo a `sdmc:/switch/fifa07`, el runtime lo tomo por instalacion
nueva y reinstalo los paquetes graficos: dejo `drive_c/dxvk/versions/` con SOLO
**3.1.1**, y con esa version el juego arranca (HUD de FPS) y se CIERRA con
`page fault ... 00409F9B` (`exit_code 0xc0000005`). El DXVK que SI funcionaba era
el build empaquetado `v3.1-17-g878473ba`; se ha restaurado como
`drive_c/dxvk/versions/2.3/d3d9.dll` y el fichero hermano pide `dxvk-version=2.3`.

**Sintoma, causa, correccion aplicada y las 3 alternativas de UNA LINEA (probar
en orden: 1) 2.3 sin shim de dmusic, 2) 2.3 con el shim, 3) `d3d=wine`), mas el
aviso de NO dejar que el runtime vuelva a descargar nada, estan en
`docs/ARRANQUE-DIRECTO.md`.**
