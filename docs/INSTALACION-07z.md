# Instalación de 07z — FIFA 07 en Nintendo Switch

> Proyecto **no oficial**, sin relación con EA. **No incluye el juego**: tenés que
> aportar **tu propia copia** de FIFA 07 de PC.

## Qué necesitás

- Una Switch con **Atmosphere** y **sigpatches** (da igual `sysMMC` o `emuMMC`). El port
  soporta **dos** versiones de Atmosphere: **1.11.2** (firmware hasta 22.5.0) y
  **1.12.0** (firmware 23.0.x). Mirá la tuya en **Ajustes → Sistema**: sale algo como
  `23.0.1 | AMS 1.12.0 | S`.
- **El parche de «ventana baja»** — **sin él el juego NO arranca** (síntoma: pulsás Jugar y
  te devuelve al menú). **Es un kernel: va por versión exacta de Atmosphere.** Elegí el tuyo:
  · **AMS 1.11.2** → `2-07z-PARCHE-VENTANA-BAJA.zip`
  · **AMS 1.12.0** → `4-07z-PARCHE-VENTANA-BAJA-AMS-1.12.0.zip`

  Los dos vienen también (con todo lo demás ya colocado) en el **ZIP completo**:
  `1-07z-PAQUETE-COMPLETO.zip`. Cómo se instalan:
  [docs/PARCHE-VENTANA-BAJA.md](PARCHE-VENTANA-BAJA.md).
- **Tu copia de FIFA 07 de PC**, **instalada y funcional**. Para que sirva tiene que
  traer los datos completos:

  | Carpeta / fichero | Debe tener |
  |---|---|
  | `alocale/` | **21 archivos** |
  | `data/` | **3272 archivos** |
  | `fifa07.exe` | **5.242.880 bytes (5,00 MB)** |

  **NO sirven**: instaladores sueltos, ISOs, copias «a medias» ni packs raros con
  `plugins/` o `unins000` (esos son otra cosa, no una instalación del juego).
- Una **SD** con espacio: el port ocupa ~60 MB y tu juego lo que ocupe en tu PC.
- Un **instalador de NSP**: DBI, Goldleaf, Tinfoil o Awoo.
- Los ficheros de 07z: la **carpeta `fifa07`** y **`07z-forwarder.nsp`**
  (pestaña **Releases** del repositorio).

## Instalación

1. **Primero el parche de «ventana baja»** (ver *Qué necesitás*): con la consola **apagada**,
   copiá `atmosphere/mesosphere.bin` y `atmosphere/kips/autorun-loader.kip` a la SD y, si
   arrancás con **Hekate**, añadí las dos líneas de `kernel=` / `kip1=` que explica
   [docs/PARCHE-VENTANA-BAJA.md](PARCHE-VENTANA-BAJA.md).
   *(Si ya tenías Autorun / Wine-NX instalado, ya lo tenés: saltá este paso.)*
2. Copiá la carpeta **`fifa07`** a `sdmc:/switch/fifa07/`.
2. Copiá **tu juego** dentro de `sdmc:/switch/fifa07/drive_c/FIFA 07/`, de modo que
   exista esta ruta:

   ```
   sdmc:/switch/fifa07/drive_c/FIFA 07/fifa07.exe
   ```

   > ⚠️ **Copiá tu juego DENTRO de la carpeta, sin reemplazarla.** Los ficheros de 07z
   > (`DINPUT.dll`, `dmusic.dll`, `dpnhpast.dll`, `MSIMG32.dll`, `OLEACC.dll`, `sensapi.dll`,
   > `d3d8.dll`, `dxwrapper.dll`, `dxwrapper.ini`, `d3d9.dll`, `dxvk.conf`,
   > `fifa07.keys.txt`, `fifa07.wine-nx.txt`) tienen que quedar **junto a tu `fifa07.exe`**.
   > Si los pisas con tu copia del juego: pide **DirectX 9.0c**, o te quedas **sin mandos**,
   > o **pantalla negra**.

3. Instalá **`07z-forwarder.nsp`** con DBI, Goldleaf, Tinfoil o Awoo.
4. En el **menú de inicio** aparece el icono **07z**. Pulsalo y después **Jugar**.

**No hay que crear particiones, ni hacer overclock, ni pasar por ningún asistente de**
**configuración.** El único parche de kernel necesario es el de **«ventana baja»** (ver
*Qué necesitás*): si ya usas Autorun / Wine-NX en tu consola, seguramente ya lo tengas.

> **Importante**: para jugar lanzá 07z **desde el icono del HOME**. Desde el
> *Homebrew Menu* no arranca el juego.

## Una vez dentro del juego: 1280x720

Entrá a **Mi FIFA 07 → Ajustes → Pantalla** y elegí **`1280x720`**.

Es el único modo 16:9 del juego: **con cualquier otro se ven barras negras a los
lados**. El juego lo guarda solo, no hay que repetirlo.

## Controles

Vienen configurados. Se cambian desde la pantalla **Configuración** de 07z.

| Botón | En menús | En partido |
|---|---|---|
| **A** | Confirmar | Pase |
| **B** | — (para atrás, **PLUS**) | Tiro / entrada |
| **X** | — | Pase filtrado / salida del portero |
| **Y** | — | Centro / pase largo |
| **R** | — | Sprint |
| **L** | — | Regate |
| **ZR** | Avanzar donde lo pida | — |
| **ZL** | — | Pase (igual que A) |
| **PLUS** | Atrás | Pausa |
| **MINUS** | Confirmar | — |
| **Cruceta / Stick izq.** | Navegar | Mover jugador |
| **Clic stick izq.** | — | Amago |
| **Clic stick der.** | — | Control de ritmo |

## Si algo falla

| Síntoma | Qué hacer |
|---|---|
| El icono del HOME no abre 07z | Comprobá que existe `sdmc:/switch/fifa07/07z.nro` con ese nombre exacto |
| **Pulso Jugar y me devuelve al menú** | **Causa nº1: te falta el parche de «ventana baja»** (Atmosphere 1.11.2 + `mesosphere.bin` + `autorun-loader.kip`): es *su* síntoma exacto → instalalo según [docs/PARCHE-VENTANA-BAJA.md](PARCHE-VENTANA-BAJA.md). Si ya lo tenés: **(2) tenés instalado un forwarder VIEJO** — mirá `logs/autorun_runtime.log`: la línea `[LOWVA] forwarder title <id>` debe decir **0548eabb35576000**; si dice otro (el viejo es `058f3083dc72b000`) el juego **nunca** arranca → instalá el `07z-forwarder.nsp` **actual** y **borrá el icono viejo** (te quedan dos). (3) lanzalo desde el **icono del HOME** — **ni** Homebrew Menu **ni** instalador (en *modo applet* no hay memoria para el runtime). (4) **Cerrá cualquier juego abierto en segundo plano y reiniciá la consola**. (5) Comprobá que tu copia está **completa**: `wine-nx-runtime.nro` (43 MB) y `drive_c/windows/` además de `drive_c/FIFA 07/` |
| Sale «Abre desde el menú de inicio» | Lo lanzaste desde el Homebrew Menu: usá el icono del HOME |
| El juego no arranca | Comprobá que copiaste **todos** los datos del juego, no solo el `.exe` |
| **Sale una ventana de Windows** (o pide **«install DirectX 9.0c»**) | Faltan los ficheros de 07z junto al `.exe`: **los pisaste** al copiar tu juego → volvé a copiar el paquete de **Releases** sin reemplazar la carpeta |
| **Los mandos no responden a nada** | Falta `DINPUT.dll` junto al `.exe` → recopialo del paquete |
| **Pantalla negra** o no entra al partido | Falta el puente gráfico (`d3d8.dll`, `dxwrapper.dll`, `dxwrapper.ini`, `d3d9.dll`, `dxvk.conf`) → recopialos del paquete |
| El juego no arranca y tu copia vino de un pack | Usá una instalación **normal** de FIFA 07 (ver «Qué necesitás»): packs con `plugins/` o `unins000` no sirven |
| Se ven barras negras | Ajustes → Pantalla → **1280x720** |
| La primera vez va a tirones | Está compilando shaders: a la segunda vez va fluido |
| Error `0xc0000135` o `0xc000007b` | Volvé a copiar el runtime de **Releases** y verificá el `.exe` del juego |

## Desinstalar

1. Desinstalá el NSP desde *Ajustes de datos → Gestión de datos → Software*.
2. Borrá la carpeta `sdmc:/switch/fifa07/`.

No queda nada más: 07z no escribe fuera de esa carpeta.

## Créditos y licencia

- **Runtime**: Wine y **Wine-NX / Autorun** — *LGPL-2.1-or-later*.
- **Frontend 07z y su documentación** — *MIT*.
- **FIFA 07** y sus marcas son propiedad de **EA**. Proyecto **no oficial**.
