# Guía de instalación de 07z — FIFA 07 en Nintendo Switch

> 07z es un proyecto **no oficial**, sin relación con **EA**. **No incluye el juego**:
> tú aportas tu propia copia de FIFA 07 de PC.

*Copia de trabajo (repositorio del PC). La versión que se publica con el paquete
es `dist/github-07z/docs/INSTALACION.md`; el contenido es el mismo.*

---

## Resumen en 3 pasos

1. **Custom firmware**: ten **Atmosphere con sigpatches** ya instalado (usa tu
   `sysMMC` o tu `emuMMC`, el que tengas).
2. **Copia la carpeta** `fifa07` completa a `sdmc:/switch/fifa07/` y mete dentro
   **tu copia** del juego.
3. **Instala el NSP** `07z-forwarder.nsp`. En el HOME aparece el icono **07z**.

**No hace falta**: particiones nuevas, **kips**, overclock, ni pasar por el
asistente de setup de Autorun. El `config/settings.json` que viene dentro de la
carpeta ya trae `setup-complete=1`, `run-the-chosen-program=true` y
`reopen-the-launcher-on-exit=false`, así que arranca directo.

---

## 0. Antes de empezar — qué necesitas

- Una **Nintendo Switch** con **custom firmware** (Atmosphere) y **sigpatches**
  recientes. Vale tanto `sysMMC` como `emuMMC`.
- **Tu propia copia de FIFA 07 de PC** (`fifa07.exe`, sus datos y sus DLLs).
- Una **tarjeta SD** con ~250 MB libres (runtime + frontend + tu copia del juego).
- Un **instalador de NSP**: **DBI, Goldleaf, Tinfoil o Awoo Installer**.
- Los **ficheros de 07z**:
  - la **carpeta `fifa07`** (runtime `wine-nx-runtime.nro` + frontend `07z.nro`
    + `config/` + `drive_c/` + `share/wine/`), desde la pestaña **Releases**;
  - el **NSP** → [`install/07z-forwarder.nsp`](../../dist/github-07z/install/07z-forwarder.nsp).

> **Sin kips, sin particiones, sin overclock.** En esta versión la ventana de
> direcciones que necesita `fifa07.exe` la resuelve la propia cadena 07z (el
> program id del forwarder). No instales el antiguo «parche low-window» ni el
> `.kip` de Autorun: no se usan y son de una receta anterior.

---

## 1. Copia la carpeta y tu juego

Con la SD en el PC (o por FTP/MTP), deja la carpeta **exactamente** aquí:

```
sdmc:/switch/fifa07/
├── wine-nx-runtime.nro        # runtime (Releases)
├── 07z.nro                    # frontend 07z (Releases)
├── config/                    # ajustes; se crean solos
├── drive_c/
│   ├── FIFA 07/               # <-- AQUÍ PONES TU PROPIA COPIA DEL JUEGO
│   │   └── fifa07.exe
│   └── windows/               # módulos del paquete
└── share/wine/                # datos/fuentes del paquete
```

1. Copia la carpeta `fifa07` a `sdmc:/switch/` (si ya existe, **fusiona** sin
   borrar `config/` ni `drive_c/`).
2. Copia tu **copia propia** de FIFA 07 (PC) dentro de
   `sdmc:/switch/fifa07/drive_c/FIFA 07/`, de forma que exista esta ruta exacta:

```
sdmc:/switch/fifa07/drive_c/FIFA 07/fifa07.exe
```

Junto al `.exe` deben ir los **datos y DLLs** de tu instalación del juego. Los
nombres y la carpeta deben ser **exactamente** esos: el icono del HOME apunta a
`sdmc:/switch/fifa07/07z.nro`.

---

## 2. Instala el NSP

1. Copia `07z-forwarder.nsp` a la SD (por ejemplo a `/switch/` o al raíz).
2. Instálalo con **DBI / Goldleaf / Tinfoil / Awoo Installer**.
3. Si tu instalador lo pide, usa tus `prod.keys` (solo para instalar el NSP).

El NSP solo crea el **acceso directo** del HOME: **no** contiene el juego.

> ℹ️ El NSP 07z usa un **program id concreto** que es lo que hace que Atmosphere
> conceda a la cadena el espacio de direcciones bajo que `fifa07.exe` necesita.
> Por eso hay que usar **este** NSP con **su** `07z.nro` en la ruta indicada, y
> por eso no hace falta ningún kip adicional.

---

## 3. Arranca y juega

1. En el **HOME** aparece el icono **07z**. Púlsalo.
2. Se abre **la interfaz de 07z** (menú propio, sin nada de Wine).
3. Pulsa **Jugar**. El juego arranca **como si fuera nativo**.
4. Al salir del juego, vuelves al **HOME**.

### Regla de oro

> Para **jugar**, lanza 07z **desde el icono del HOME (el NSP)**.
> Desde el **Homebrew Menu** (hbmenu) **no es posible jugar**: ahí el frontend
> solo muestra un aviso. El juego (`fifa07.exe`) está compilado con las
> reubicaciones eliminadas y solo funciona si se mapea en `0x400000`, lo que
> únicamente ocurre al lanzarlo como *aplicación* con el program id del NSP 07z;
> el Homebrew Menu lo lanza como *applet* de 64 bits y esa dirección queda
> ocupada («Address space unavailable»).

---

## 4. Pantalla: elige **1280x720** una vez

El runtime **no estira**: escala con `min()` y centra, así que si el juego usa un
aspecto que no es 16:9 aparecen **barras negras** inevitables. Por eso hay que
hacer que el juego renderice 16:9.

**FIFA 07 tiene UN solo modo 16:9 nativo: `1280x720`.**

En el juego: **Mi FIFA 07 → Ajustes → Pantalla** y elige **1280x720**.
Hazlo **una sola vez**: el juego lo guarda en su perfil.

- **NO** elijas **1280x1024**: es 5:4 y deja barras negras a los lados.
- La tabla de modos del ejecutable (registros de 16 B: `W:u16, 0000, H:u16,
  20 00 00 00`) está en `fifa07.exe`, ~offset `0x4c42e8`.
- El perfil del juego vive en
  `drive_c/users/steamuser/Documents/FIFA 07/A. Profiles/A. Profiles`
  (texto `OPTIONS/RESOLUTION=<n>`, índice 0-based). **No edites ese fichero a
  mano** salvo que sepas lo que haces: lleva un checksum y editarlo mal hace que
  el juego se cierre. Cámbialo desde la pantalla del juego (sección 4) y listo.

---

## 5. Controles

Modo de entrada: **teclado sintetizado** (`input-mode=2` en `fifa07.wine-nx.txt`)
+ el shim `DINPUT.dll` junto al `.exe`. El runtime traduce cada botón del mando a
teclas de FIFA. El mapa vive en `keys.txt` (en `sdmc:/switch/fifa07/`,
`sdmc:/switch/fifa07/config/` y `sdmc:/switch/fifa07/drive_c/FIFA 07/`); se puede
editar desde la pantalla **Configuración** de 07z o a mano.

| Botón Switch | Tecla | En menús | En partido |
|---|---|---|---|
| **A** | `0x0d + 0x53` (ENTER + S) | Confirmar | Pase |
| **B** | `0x44` (D) | — (usa **PLUS** para atrás) | Tiro / entrada |
| **X** | `0x57` (W) | — | Pase filtrado / salida del portero |
| **Y** | `0x41` (A) | — | Centro / pase largo |
| **R** | `0x45` (E) | — | Sprint |
| **L** | `0x10` (Mayús) | — | Regate / skill move |
| **ZR** | `0x20` (ESPACIO) | — | reservado (FIFA 07 no usa ESPACIO) |
| **ZL** | `0x53` (S) | — | Pase (redundante con **A**) |
| **PLUS** | `0x1b` (ESCAPE) | Atrás | Pausa |
| **MINUS** | `0x0d` (ENTER) | Confirmar | — |
| **Cruceta** | Flechas | Navegar | Mover jugador |
| **Stick izq.** | Flechas | Navegar | Mover jugador |
| **Clic stick izq.** (STICKL) | `0x5a` (Z) | — | Amago (dummy) |
| **Clic stick der.** (STICKR) | `0x43` (C) | — | Control de ritmo |

- **A es un acorde** (ENTER **+** S): en menú FIFA lee ENTER y en partido lee S.
- **B ya no lleva ESCAPE** (era el causante de que "A/B no hicieran nada"); para
  "atrás" en menús usa **PLUS**.
- **A propósito NO se mapean** la tecla **Q** (tácticas) ni el **teclado
  numérico** (comparte scan codes con las flechas y disparaba las tácticas solas).

---

## 6. Rendimiento

- **Con gráficos y resolución en ALTO**: **55-60 FPS** estables en partido.
- Los **bajones de los menús 3D** (selección de equipos, plantillas) **no eran
  CPU/GPU**: eran **compilación de shaders** de DXVK y **I/O de la SD**. El
  **segundo arranque** de un menú ya va bien (la caché de shaders persiste en
  `drive_c/users/steamuser/AppData/Local/dxvk/`).
- Ajustes ya aplicados en el paquete (no hay que tocar nada):
  - `fifa07.wine-nx.txt`: `sync=horizon`, `four-cores=1`, `frame-limit=60`.
  - `dxvk.conf` junto al `.exe` (junto a `fifa07.exe`):
    `dxvk.numCompilerThreads=4`, `dxvk.enableStateCache=True`,
    `d3d9.maxFrameLatency=2`.
  - DXVK en uso: build `v3.1-17-g878473ba` (etiquetado como versión 2.3).
- El **overclock NO es requisito** del port. Si quieres margen extra, el usuario
  lo aplica por su cuenta (p. ej. **UltraHand**); el port va bien sin él.

---

## Desinstalar

1. Desinstala el NSP (`Ajustes de datos` → gestionar software, o tu instalador).
2. Borra la carpeta `sdmc:/switch/fifa07/` completa.
3. No queda nada más: 07z no escribe fuera de esa carpeta.

---

## Problemas frecuentes

| Síntoma | Causa probable | Solución |
|---|---|---|
| El icono del HOME no abre el frontend | Ruta del `.nro` distinta | Comprueba que `sdmc:/switch/fifa07/07z.nro` existe con ese nombre exacto. |
| «Abre desde el menú de inicio» | Lanzado desde el Homebrew Menu | Ábrelo desde el icono del HOME (NSP). |
| «Address space unavailable» al pulsar Jugar | Se lanzó desde el hbmenu, o el NSP instalado no es el de 07z | Lanza siempre desde el icono del HOME y usa el `07z-forwarder.nsp` de este paquete. |
| El juego no arranca / error `c0000135` o `c000007b` | Runtime y sus módulos no emparejados, o falta el juego | Vuelve a copiar el runtime de **Releases** tal cual y verifica `drive_c/FIFA 07/fifa07.exe`. |
| **Barras negras** a los lados | El juego no está en 16:9 | **Mi FIFA 07 → Ajustes → Pantalla** → **1280x720** (no 1280x1024). |
| Pantalla en negro al cargar | Copia del juego incompleta | Comprueba que copiaste **todos** los datos del juego, no solo el `.exe`. |
| Tirones al entrar por primera vez a un menú 3D | Compilación de shaders | Normal; vuelve a entrar (la caché de shaders ya está hecha) y va fluido. |

---

## Licencia y créditos

- Frontend/homebrew **07z** y su documentación: **MIT**.
- **Runtime**: software de terceros de **Wine / Wine-NX / Autorun**, bajo
  **LGPL-2.1-or-later**; los parches aplicados están en `dist/github-07z/patches/`.
- **FIFA 07** y sus marcas son propiedad de **EA**. Proyecto **no oficial**.
