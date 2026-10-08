# Frontend-NX (NRO hermano) para FIFA 07 — diseño basado en FileZzz

Hermano homebrew de **FIFA 07** para Switch: un NRO propio que muestra un menú,
una pantalla de **configuración por juego** (que lee/escribe los ficheros del
runtime) y una pantalla de **donaciones con QR**, y que lanza el juego de forma
**invisible** (sin la biblioteca del runtime) devolviendo el control al HOME al
salir. Se parte del proyecto propio **FileZzz** (`C:\Projects\c++\EzFiles`), su
arquitectura, estética nativa Horizon, navegación con Joy-Con y la vista
"Acerca de / donaciones (QR)".

> Nombre propuesto: **Fifa07NX.nro** (`com.paolo.fifa07nx`), datos en
> `sdmc:/switch/Fifa07NX/`. Carpeta nueva sugerida:
> `C:\Projects\ports\fifa07\frontend-nx\`.

---

## (a) Estructura exacta del proyecto

Partiendo del esqueleto de FileZzz, se **conservan** `CMakeLists.txt`,
`deploy_switch.ps1`, `icon.jpg`, la carpeta `resources/romfs/{xml,i18n,img}` y
`source/qrcodegen.cpp`; se **eliminan** los módulos de gestor de archivos
(`usb_mtp.c`, MTP/FTP/explorador, `title_manager`, `app_updater`) y se añaden
dos módulos nuevos (`wine_nx_settings`, `key_map`).

```
C:\Projects\ports\fifa07\frontend-nx\        (= copia adaptada de EzFiles)
├── CMakeLists.txt                 # project(Fifa07NX), PACKAGE_NAME com.paolo.fifa07nx,
│                                  #   MAIN_SRC = source/main_borealis.cpp source/qrcodegen.cpp
│                                  #   (se quitan usb_mtp.c y switch_wrapper.c de la app)
├── icon.jpg                       # icono 256x256 (NACP + forwarder)
├── deploy_switch.ps1              # copiado de FileZzz, destino sdmc:/switch/Fifa07NX/
├── include/
│   ├── app_config.hpp             #  [adaptado de config.hpp] idioma/tema/última pantalla
│   ├── wine_nx_settings.hpp       #  NUEVO: parser/escritor de fifa07.wine-nx.txt
│   └── key_map.hpp                #  NUEVO: parser/escritor de fifa07.keys.txt
├── source/
│   ├── main_borealis.cpp          #  [adaptado] MainActivity, SplashActivity, SettingsActivity,
│   │                              #   QrCodeView, Helpers, main()
│   └── qrcodegen.cpp              #  [literal de FileZzz] generador QR (Nayuki)
└── resources/romfs/
    ├── xml/
    │   ├── main_tabs.xml          #  [adaptado] un solo Tab "Menú" (o sin TabFrame)
    │   ├── view_menu.xml          #  NUEVO: 4 filas (Jugar / Configuración / Acerca de / Salir)
    │   ├── view_settings.xml      #  NUEVO: filas de ajustes del runtime + mapeo de mandos
    │   ├── view_about.xml         #  [reutilizado de FileZzz] dos columnas QR
    │   └── view_splash.xml        #  [reutilizado] splash
    ├── i18n/<13 idiomas>/hints.json   # [de FileZzz] es, es-419, en-US, de, fr, it, pt, ru,
    │                                  #   nl, ja, ko, zh-Hans, zh-Hant
    ├── img/                       # logos + iconos (se reutilizan los *_dark.png de FileZzz)
    └── fonts/                     # si se conservan fuentes auxiliares
```

`CMakeLists.txt` mantiene el patrón de FileZzz:
`program_target(Fifa07NX "${MAIN_SRC}")`, `target_link_libraries(… borealis nx)`,
`if(PLATFORM_SWITCH)` → `nacptool` + `elf2nro --icon --nacp --romfsdir`. Solo hay
que cambiar el nombre del proyecto, `PACKAGE_NAME`, la lista `MAIN_SRC` y la ruta
de copia del `.nro` final.

---

## (b) Qué se reutiliza de FileZzz (literal) y qué es nuevo

### Reutilizado literal / casi literal
- **`QrCodeView`** (`source/main_borealis.cpp`, ~líneas 472–538): renderizador
  vectorial con **NanoVG + `qrcodegen`**, sin PNG. API:
  `QrCodeView(text, size)` y `setText()`. El constructor ya fija
  `setWidth/setHeight(size)`. `source/qrcodegen.cpp` se copia tal cual.
- **`AboutTab` + `view_about.xml`** (vista "Acerca de, donaciones (QR) y
  créditos"): se reutiliza entera. Ya monta el QR con
  `new QrCodeView("https://paypal.me/francopaololg", 200.0f)` dentro del `Box`
  `boxCoffeeQr` de 230×230, y registra `BUTTON_B` para volver. Se **añade un
  segundo** `Box` (`boxCoffeeQr2`) con `QrCodeView("https://buymeacoffee.com/z.frnk", 200.0f)`.
- **i18n** (`resources/romfs/i18n/**/hints.json`): esquema `hints/<clave>` y
  `"hints/<clave>"_i18n`. Se conservan las claves `about_title`, `about_support`,
  `about_scan_qr`, `about_developer` = *"Desarrollador: Franco Paolo López
  Gálvez"*, `about_paypal`, `about_coffee`, `ok/cancel/back/exit/exit_hint`.
  Se **depuran** las claves exclusivas del gestor de archivos.
- **Estética nativa Horizon**: `applyAppTheme()` con temas `Light / Dark /
  AMOLED` y acentos cyan `#00F2FE` / `#38BDF8`; fondo `brls/background` opaco;
  separadores `brls/sidebar/separator`; tipografía del sistema
  (`PlSharedFontType_Standard`).
- **`WallpaperAppletFrame`** (opcional): si se quiere fondo de pantalla
  personalizado; no es imprescindible en el MVP.
- **Navegación con Joy-Con**: la de Borealis (D-Pad/Stick mueven el foco, A
  selecciona, B vuelve). Regla de FileZzz: **no** hacer `setFocusable(true)` en
  contenedores raíz, solo en filas/botones hijos.
- **`brls:TabFrame` / sidebar / `SplashActivity` / `registerXMLView`**, y el
  esqueleto de `deploy_switch.ps1` (cambia la ruta a `sdmc:/switch/Fifa07NX/`).

### Escrito nuevo
- **`wine_nx_settings.hpp`**: parser/escritor de la configuración por juego
  (`sdmc:/switch/wine/drive_c/FIFA 07/fifa07.wine-nx.txt`) — claves `title=`,
  `hidden=`, `verbose=`, `profile=`, `windows=compositor|framebuffer`,
  `d3d=dxvk`, `four-cores=1`, `vsync=0|1`, `upscaling=fsr|off|integer`,
  `frame-limit=`. Lee, edita y **reescribe** el fichero conservando el resto de
  líneas desconocidas.
- **`key_map.hpp`**: parser/escritor de `fifa07.keys.txt` (líneas
  `NOMBRE=0xNN`, VK de Windows). La UI mostrará las acciones y permitirá
  reasignar a un botón de Switch.
- **`view_menu.xml` + `MainActivity`**: menú de 4 filas.
- **`view_settings.xml` + `SettingsActivity`**: filas de opciones del runtime.
- **`launch` (dentro de `main_borealis.cpp`)**: hand-off al runtime (ver (d)).
- Claves i18n nuevas: `menu_play`, `menu_settings`, `menu_about`, `menu_exit`,
  `cfg_upscaling`, `cfg_framelimit`, `cfg_vsync`, `cfg_fourcores`, `cfg_windows`,
  `cfg_d3d`, `cfg_controls`, `cfg_saved`, `launch_error`.

---

## (c) Pantallas del NRO

### 1. Menú principal (`view_menu.xml`, `MainActivity`)
Lista vertical con filas enfocables estilo Horizon (icono + etiqueta + acción):
- **Jugar** → `launchGame()` (hand-off invisible al runtime, ver (d)).
- **Configuración** → `pushActivity(new SettingsActivity())`.
- **Acerca de y donaciones** → `AboutTab`.
- **Salir** → `brls::Application::quit()` (diálogo con `hints/exit_hint`).

### 2. Configuración (`view_settings.xml`, `SettingsActivity`)
Dos bloques, ambos **leyendo primero el fichero real y escribiéndolo al cambiar**:

*Bloque Rendimiento/Gráficos → `fifa07.wine-nx.txt`*
| Fila UI | Clave escrita |
|---|---|
| Ventana | `windows=compositor` / `framebuffer` |
| Renderizado | `d3d=dxvk` |
| Cuatro núcleos | `four-cores=1` |
| VSync | `vsync=1` / `0` |
| Escalado | `upscaling=fsr` / `off` / `integer` |
| Límite de FPS | `frame-limit=<n>` |
| Ocultar en el runtime | `hidden=1` (recomendado por defecto) |
| Diagnóstico | `verbose=0`, `profile=0` |

*Bloque Mandos → `fifa07.keys.txt`*
- Lista de acciones (`A, B, X, Y, Plus, Minus, ZL, ZR, L, R, START, STICKL…`) con
  su VK actual; al pulsar una fila, se captura el botón de Switch y se escribe
  `NOMBRE=0xNN`. Aplica el mapa por defecto de `docs/CONTROLLER.md` si el fichero
  no existe.
- Pie: **Guardar** (escribe ambos ficheros con `hints/cfg_saved`) y **B** para
  volver. Las escrituras van a `sdmc:/switch/wine/drive_c/FIFA 07/` (junto al
  `.exe`), que es donde el runtime busca `NAME.wine-nx.txt` y `NAME.keys.txt`.

### 3. Donaciones (`AboutTab` reutilizado, `view_about.xml`)
Columna izquierda: logo, versión, `about_developer`, repositorio, motor.
Columna derecha **apoyar el proyecto** con **dos QR** (bloques `boxCoffeeQr` y
`boxCoffeeQr2`), cada uno con su enlace en texto:
- `https://paypal.me/francopaololg`
- `https://buymeacoffee.com/z.frnk`
- Pie: `about_scan_qr` ("Escanea este código QR con la cámara de tu teléfono…").
Los QR son **vectoriales** (nítidos a cualquier tamaño) y se generan en la CPU
al mostrar la vista; no requieren PNG ni `qrencode` externo.

---

## (d) Lanzamiento invisible y vuelta al HOME

El runtime (`sdmc:/switch/wine/wine-nx-runtime.nro`) admite **el programa a
ejecutar como `argv[1]`**; con ese argumento **no** entra a su biblioteca/menú
(confirmado en el parche `patches/wine-nx.patch`: la rama `argc>1 && argv[1]`
fija `target` y evita `wine_nx_launcher_run`). Con
`reopen-the-launcher-on-exit=false` (ya puesto en `config/settings.json`), al
terminar el juego el runtime **no** relanza su launcher y se vuelve al HOME.

Flujo:
1. En el HOME, el icono abre el **forwarder/homebrew** que arranca
   **Fifa07NX.nro**.
2. El usuario configura si quiere y pulsa **Jugar**.
3. `Fifa07NX` pide el *next-load* al chainloader con libnx:
   ```
   envSetNextLoad(
     "sdmc:/switch/wine/wine-nx-runtime.nro",
     "\"sdmc:/switch/wine/wine-nx-runtime.nro\" "
     "\"sdmc:/switch/wine/drive_c/FIFA 07/fifa07.exe\"");
   brls::Application::quit();   // cede la pantalla; hbmenu carga el runtime
   ```
4. El runtime recibe `argv[1]` = ruta del `.exe`, lee
   `fifa07.wine-nx.txt` / `fifa07.keys.txt` junto al ejecutable, arranca el
   juego **invisible** (sin su biblioteca).
5. Al salir el juego, el runtime termina → con `reopen…=false` **vuelve al HOME**.

Alternativa equivalente (patrón del forwarder del repo, ver
`tools/build-fextendo-forwarder.py`, que escribe `romfs/nextNroPath` y
`romfs/nextArgv`): crear un **NSP forwarder** por juego cuyo
`nextNroPath = /switch/Fifa07NX/Fifa07NX.nro` hace que el propio icono del HOME
abra la pantalla de configuración; o un forwarder directo a
`nextNroPath = /switch/wine/wine-nx-runtime.nro` con
`nextArgv = sdmc:/switch/wine/drive_c/FIFA 07/fifa07.exe` para jugar sin menú.
La clave `hidden=1` en `fifa07.wine-nx.txt` mantiene el juego fuera de la
biblioteca del runtime.

---

## (e) PRIMER HITO (alcanzable) — pasos exactos

**Objetivo del hito:** un `Fifa07NX.nro` que arranque en la consola, muestre el
**menú principal** y la **pantalla de donaciones con los dos QR**, con navegación
Joy-Con y salida con B. *Sin* lanzamiento ni escritura de ajustes todavía
(eso son hitos 2 y 3).

1. **Instalar devkitPro** (devkitA64 + libnx) en Windows; añadir
   `$DEVKITPRO/devkitA64/bin` y `$DEVKITPRO/tools/bin` al PATH. Comprobar
   `aarch64-none-elf-gcc --version`.
2. **Copiar el esqueleto de FileZzz**: copiar
   `C:\Projects\c++\EzFiles` → `C:\Projects\ports\fifa07\frontend-nx\`,
   **excluyendo** `extern/borealis` del copiado selectivo (se puede reutilizar el
   submódulo/enlace de FileZzz o copiarlo tal cual) y borrando los ficheros del
   gestor de archivos (`usb_mtp.c`, vistas de explorador/juegos/MTP/FTP, headers
   de MTP/FTP/updater).
3. **Adaptar `CMakeLists.txt`**: `project(Fifa07NX)`,
   `PACKAGE_NAME com.paolo.fifa07nx`, `MAIN_SRC = source/main_borealis.cpp
   source/qrcodegen.cpp`; ajustar el `copy_if_different` final a
   `C:/Projects/ports/fifa07/frontend-nx/Fifa07NX.nro`.
4. **Recortar `main_borealis.cpp`**: dejar `QrCodeView`, `AboutTab`,
   `SplashActivity`, `applyAppTheme`, helpers, y `main()` con
   `registerXMLView("AboutTab", AboutTab::create)` etc.; sustituir
   `MainActivity`/`main_tabs.xml` por el **menú de 4 filas** (`view_menu.xml`).
5. **Añadir `view_menu.xml`** (4 filas con `@i18n/hints/menu_*`) y enlazar
   "Acerca de" → `AboutTab`.
6. **Duplicar la columna de donaciones** en `view_about.xml`: añadir
   `boxCoffeeQr2`; en `AboutTab` crear
   `QrCodeView("https://buymeacoffee.com/z.frnk", 200.0f)` (el de PayPal ya está).
7. **Añadir las claves i18n nuevas** (`menu_play/settings/about/exit`) en los 13
   `hints.json`.
8. **Compilar**:
   ```sh
   cd /c/Projects/ports/fifa07/frontend-nx
   cmake -B build -DCMAKE_BUILD_TYPE=Release -DPLATFORM_SWITCH=ON
   cmake --build build --target Fifa07NX.nro -j
   ```
   Resultado: `build/Fifa07NX.nro` (y copia en la raíz del proyecto).
9. **Desplegar** con el script (adaptado de `deploy_switch.ps1`):
   ```powershell
   powershell -ExecutionPolicy Bypass -File deploy_switch.ps1
   ```
   Copia `Fifa07NX.nro` a `sdmc:/switch/Fifa07NX/Fifa07NX.nro` vía MTP.
10. **Verificar en hardware** (Hekate/Atmosphere + hbmenu): abrir
    `Fifa07NX.nro`, comprobar el splash, el menú con navegación D-Pad/Stick,
    entrar en *Acerca de* y ver **los dos QR** legibles, y volver con **B**.
    Captura/log en `sdmc:/switch/Fifa07NX/` para la evidencia.

---

## (f) Riesgos y lo NO verificado

- **Ruta raíz del runtime (crítico).** El contexto da
  `sdmc:/switch/wine/…`, pero el parche del repo usa
  `WINE_ROOT = "sdmc:/switch/fifa07-fex"` y `DEFAULT_TARGET = WINE_DRIVE_C
  "/FIFA 07/fifa07.exe"`. Hay que **confirmar en la SD** cuál es la raíz activa
  antes de fijar rutas en el código; el diseño parametriza una única constante.
- **Esquema del `.wine-nx.txt`.** Las claves (`windows=`, `d3d=`, `four-cores=`,
  `vsync=`, `upscaling=`, `frame-limit=`, `title=`, `hidden=`, `verbose=`,
  `profile=`) vienen del contexto/`launcher_settings.h` (fuente externa, no leída
  aquí); los **valores aceptados** hay que contrastarlos con el runtime real.
  `upscaling=integer` y `fsr` no están verificados en hardware.
- **`envSetNextLoad` requiere chainloader.** El hand-off NRO→NRO depende de que
  el cargador (hbmenu/nx-hbloader u otro con soporte de *next-load*) procese
  `nextNroPath/nextArgv`; con NSP forwarders el comportamiento difiere. Sin
  chainloader compatible, "Jugar" no arrancaría el runtime.
- **Escritura en la carpeta del juego.** `fifa07.wine-nx.txt` y `fifa07.keys.txt`
  deben vivir junto al `.exe` en exFAT/FAT32; hay que manejar errores de
  escritura y no corromper líneas desconocidas del fichero.
- **Reutilización de i18n.** Copiar `hints.json` de FileZzz arrastra claves del
  gestor de archivos; hay que **depurarlas** y mantener paridad en los 13
  idiomas (regla de `AGENTS.md`).
- **No verificado aquí:** que los dos `QrCodeView` convivan sin recorte en la
  columna de 440px; el número exacto de claves que el runtime lee; que
  `reopen-the-launcher-on-exit=false` esté efectivamente en el
  `config/settings.json` del runtime instalado; y cualquier afirmación de
  60 FPS / navegación (son propiedades de FileZzz, no medidas en este NRO nuevo).
- **Legal:** no incluir jamás el ejecutable ni datos del juego; solo el NRO del
  frontend.

---

*Referencia primaria: `C:\Projects\c++\EzFiles` (FileZzz) — `AGENTS.md`,
`PROJECT_STRUCTURE.md`, `MASTER_PLAN.md`, `CMakeLists.txt`, `view_about.xml`,
`QrCodeView`/`AboutTab` en `source/main_borealis.cpp`, `i18n/*/hints.json`,
`deploy_switch.ps1`. Paleta web de AndromedaDownload (`docs/frontend-nx-diseno.md`)
solo como referencia puntual; el estilo elegido es la estética nativa Horizon de
FileZzz.*
