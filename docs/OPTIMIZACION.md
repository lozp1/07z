# OPTIMIZACION — FIFA 07 (Wine-NX / Switch), sin overclock

**Fecha:** 2026-10-07
**Alcance:** acercar el port a **60 FPS estables SIN overclock y sin tocar hardware**.
Todo lo aplicado es **reversible** (backup de cada fichero tocado) y **no cambia**
nada del arranque, audio, mandos ni pantalla completa ya funcionando.
**NO se ha tocado:** overclock, `keys.txt` / mapa de controles, ni el frontend.

**Tarjeta:** letra `D:` (raíz del runtime `D:\switch\wine`). Comprobado con
`for L in D E F G...; do [ -d "$L:/switch/wine" ] ...` — no asumir la letra de otra sesión.

---

## 0. Resumen en una linea

He aplicado 4 cambios (preset grafico del juego al minimo + dxvk.conf por juego +
limpieza de logs + herramienta de medida). El **cuello de botella real medido NO
es la CPU** (el port usa ~0,9–1,1 nucleos de los 3 que tiene), y el medidor
objetivo que trae el propio runtime dice **49,1 FPS de media** en partida
(p50 = 50,8). Conclusion honesta en la seccion 7.

---

## 1. Punto de partida medido (lo que SI se puede medir sin consola)

El runtime escribe estadisticas propias en `D:/switch/wine/logs/fifa07.log`.
Del ultimo run real (7-oct 04:44), parseado con `tools/medir-fps.py`:

| Metrica (149 tramos de 10 s en partida) | Valor |
|---|---|
| FPS medio | **49,1** |
| p10 / p50 / p90 | 44,3 / **50,8** / 55,6 |
| FPS maximo de un tramo | 59,4 |
| FPS minimo (transicion/carga, no partida) | 5,6 |
| Tramo a >=58 FPS | **4 de 149** |
| Tramo a >=55 FPS | 20 de 149 |

**CPU (linea `[THREADS]`):** `40 threads use 0.92 cores` — reparto tipico
`4w@1 45% · 56w:dxvk-cs@3 23% · 52w:dxvk-queue@0 13% · ...`.
=> el port **no esta saturado de CPU** (0,92 de 3,00 nucleos). El hilo principal
esta *esperando* ~la mitad del tiempo (present/vsync/GPU), no calculando.

**I/O de tarjeta en todo el run:** `1686 lecturas (902 MB, 12,8 s)` y
`515 escrituras (1,3 s)`. Casi todo ocurre **en la carga**, no en partida
(entre los segundos 177 y 197 solo +5 lecturas).

**Lo que ya estaba bien (verificado, no cambiado):**

- `logs/fifa07.log`: `[INIT] verbose traces off (verbose.txt)`,
  `[INIT] profiler off (profile.txt)`.
- `[SETTINGS] .../fifa07.wine-nx.txt: verbose global, profiler global, windows
  compositor, Direct3D DXVK + VKD3D` y `[DXVK] HUD FPS, frame limit Off, VSync on`.
- `config/settings.json`: `verbose-log=false`, `profiler=false`,
  `vulkan-probe=false`, `core-balancing=true` (necesario), `windows-through-opengl=true`.
- `[CORES] 44 dxvk-cs: core 3, priority 63` → el **offload de los hilos graficos
  al nucleo 3 ya funciona solo**. No hay nada que activar ahi.
- **Caches de shaders: SI persisten en la SD**
  - DXVK: `drive_c/users/steamuser/AppData/Local/dxvk/33a216341833ba70.dxvk.bin`
    (279.307 B) + `.dxvk.lut` (6.231 B). El log dice `Found cache file: ...`.
  - NVK (Mesa): `D:/.mesa/mesa_shader_cache_sf` — **40,5 MB**, con entrada
    `nvk-26.2.3` (la version del driver en uso). No hay nada que arreglar aqui.

---

## 2. CAMBIOS APLICADOS (fichero tocado y antes/despues)

### 2.1 `drive_c/FIFA 07/data/cmn/cfg_pc_h.ini` — preset HIGH -> LOW

- Antes: perfil **HIGH** de FIFA 07 (2.336 B, sha256 `9c9b9150…6f51`).
- Ahora: **copia byte a byte del perfil LOW** (2.620 B, sha256 `3b980031…3d64`,
  identico a `cfg_pc_l.ini`).
- Backup: `cfg_pc_h.ini.bak-antes-optimizacion`.

Cambios de linea (extracto de las claves con efecto en rendimiento):

| Clave | Antes (HIGH) | Ahora (LOW) |
|---|---|---|
| `RMGRASS_ENABLED` | 1 | **0** (sin hierba) |
| `SKY_RENDER` | 1 | **0** (sin cielo) |
| `PITCH_SHADOW_RENDER` | 1 | **0** |
| `TRACK_RENDER` | 1 | **0** |
| `DISABLE_NET_PHYSICS` | 0 | **1** (sin fisica de red de la porteria) |
| `GAMEPLAY_LINESMEN_DISABLED` | 0 | **1** (sin jueces de linea) |
| `GAMEPLAY_REF_DISABLED` | 0 | **1** (sin arbitro) |
| `CROWD_ANIMATION` | 1 | **0** (grada estatica) |
| `RMRAIN_ENABLED` | 1 (+21 lineas RMRAIN_*) | **0** (sin lluvia ni particulas de lluvia) |
| `RMFLASH_ENABLED` / `FLARES_*` / `STREAMERS_*` / `LIGHTGLOWS_*` / `CAMERA_FLASHES_ENABLED` / `SMALLFLAG_ENABLED(_PERCENTAGE)` | 1 (varios) | **0** (sin flashes, bengalas, focos, banderines, camaras) |
| `SIDELINE_ELEMENT_RENDER` / `RMFOG_ENABLED` | (no existia) | 0 |
| `PCCONFIG_GAMELOOP_AITICKS` | 1 | **3** |
| `DISABLE_DOF` | 0 | **1** (sin profundidad de campo) |
| `DISABLE_POSTFX` | 0 | **1** (sin post-proceso) |
| `PLAYERSHADOW_USELOWENDSOFTSHADOWS` | 0 | **1** (sombras blandas baratas) |
| `BAKED_LIGHTING` | 0 | 1 |
| `RENDER_RATE_MODE` | 7 | 5 |
| `PLAYER_LOD_*` / `PLAYERHEAD_LOD_*` | valores HIGH | valores LOW |
| `ACTIVE_CONIFG` | `PC_H` | `PC_L` |

### 2.2 `drive_c/FIFA 07/data/cmn/cfg_pc_m.ini` — preset MEDIUM -> LOW

- Antes: perfil **MEDIUM** (2.561 B, sha256 `9aa445f8…817f`).
- Ahora: misma copia exacta del perfil LOW (2.620 B, `3b980031…3d64`).
- Backup: `cfg_pc_m.ini.bak-antes-optimizacion`.
- Cambios propios de este fichero (M ya tenia DOF y PostFX a 1):
  `RMGRASS_ENABLED 0->0` (ya estaba), `SKY_RENDER 1->0`,
  `TRACK_RENDER 1->0`, `DISABLE_NET_PHYSICS 0->1`,
  `GAMEPLAY_LINESMEN_DISABLED 0->1`, `GAMEPLAY_REF_DISABLED 0->1`,
  `RMRAIN_ENABLED 1 -> 0`, `SMALLFLAG_ENABLED_PERCENTAGE 50 -> 0`,
  `FLARES/STREAMERS/LIGHTGLOWS/CAMERA_FLASHES -> 0`,
  `PCCONFIG_GAMELOOP_AITICKS 2->3`, `PLAYER_LOD_*` a valores LOW.

### 2.3 `drive_c/FIFA 07/data/cmn/cfg_pc_l.ini` — SIN CAMBIOS

Solo se creo el backup `cfg_pc_l.ini.bak-antes-optimizacion` (identico,
sha256 `3b980031…3d64`) para que la reversion sea simetrica.

> **Por que los tres a LOW:** no se puede determinar sin consola *cual* de los
> tres perfiles elige FIFA 07 (la tabla `PC_H/PC_M/PC_L -> data\cmn\cfg_pc_*.ini`
> esta dentro de `fifa07.exe`; en `data/cmn/` solo existen esos 3 `.ini` sueltos;
> `pc_cl.bin` es una base de datos de **nombres de jugadores**, no de tarjetas
> graficas; y no hay ninguna clave de registro de nivel grafico). Igualando los
> tres al perfil LOW, **elijas el que elijas el juego, acabas en LOW**. El juego
> NO reescribe estos ficheros (su fecha era la del pack, 25-jun-2022), asi que el
> cambio es estable.

### 2.4 `drive_c/FIFA 07/dxvk.conf` — NUEVO (ajustes DXVK por juego)

Antes **no existia** ningun `dxvk.conf` junto al `.exe`. Creado (2.027 B,
sha256 `08ae9705…1e40`). Claves activas:

```
d3d9.presentInterval        = 1     # VSync FIFO (mismo valor que el global)
d3d9.maxFrameLatency        = 2     # 2 frames en vuelo (absorbe jitter corto)
dxvk.numCompilerThreads     = 1     # "menos workers dejan mas CPU al juego"
dxvk.enableStateCache       = True  # cache de pipelines siempre activa
d3d9.forceSwapchainMSAA     = 0     # el juego no usa AA
d3d9.samplerAnisotropy      = 0     # el juego no usa anisotropico
d3d9.deviceLocalConstantBuffers = False  # Tegra X1 es memoria unificada
```

Contexto: el runtime ya escribe un `dxvk.conf` **global** en
`drive_c/users/steamuser/AppData/Local/Autorun/dxvk.conf` (3 lineas:
`dxgi.syncInterval=1`, `d3d9.presentInterval=1`, `dxvk.enableDescriptorBuffer=False`)
y pasa `DXVK_CONFIG_FILE` al guest. El propio runtime documenta
*"A local dxvk.conf takes priority"* y DXVK lee `dxvk.conf` del directorio del
ejecutable, por eso el sitio correcto es junto a `fifa07.exe` (fichero que el
runtime **no** posee, asi no lo sobreescribe).
**DXVK real en uso:** `v3.1-17-g878473ba`, GPU `Tegra X1 GM20B (NVK 26.2.3)`.

### 2.5 Limpieza en la SD (no es rendimiento en partida, es higiene)

Movidos a `C:\Projects\ports\fifa07\local\backup-logs-optimizacion\`:

- `switch/wine/logs/fifa07_verbose.log` — **757 MB** (resto de un run verbose)
- `switch/wine/logs/horizon-trace.log` — 11,6 MB
- `switch/wine/logs/swapprobe_verbose.log` — 79 KB

No estaban siendo escritos (fecha 6-oct 15:22) pero ocupaban ~770 MB de tarjeta.

> **NO tocado a proposito:** `logs/fifa07.log`, `logs/stdout.txt` y
> `logs/autorun_runtime.log` (los usa el runtime; son solo ~0,5 MB por run y
> `verbose traces off` ya los mantiene minimos), `config/settings.json`
> (ya estaba optimo), `fifa07.wine-nx.txt` (ya estaba optimo), el `dxvk.conf`
> global del runtime (es suyo y lo puede reescribir), `keys.txt`/mapa de mandos,
> overclock y frontend.

---

## 3. Impacto esperado de cada cambio y por que

| Cambio | Impacto esperado | Por que |
|---|---|---|
| Preset LOW (2.1/2.2) | **Alto** (el mayor de todos) | Quita sistemas enteros por fotograma: hierba, cielo, sombra de campo, marcas de cesped, lluvia (2048 gotas en 6 regiones), flashes, bengalas, focos, banderines, camaras de flash, animacion de grada, fisica de red de porteria, arbitro y jueces de linea. Ademas `DISABLE_POSTFX=1` y `DISABLE_DOF=1` eliminan pases de post-proceso (caros en la GPU/Anvil-like de NVK) y `PCCONFIG_GAMELOOP_AITICKS` de 1/2 a 3 reduce trabajo de IA por tick. En un juego D3D8->d3d8to9->DXVK cada objeto eliminado es *varias* llamadas a D3D8 y a DXVK menos por frame. |
| `dxvk.numCompilerThreads=1` (2.4) | Bajo-medio | El log mostraba `DXVK: Using 3 compiler threads` compitiendo con el juego (los `dxvk-shader-h` van a nucleos 0-2). Menos workers = menos picos de CPU que descuadran el frame time. Con las caches calientes apenas hay compilacion, asi que no deberia costar nada. |
| `d3d9.maxFrameLatency=2` (2.4) | Bajo-medio | Con VSync FIFO a 60 Hz, tener 2 frames en vuelo absorbe variaciones cortas de CPU/GPU y suaviza la salida. Es exactamente el candidato "smooth queue" del propio runtime (`config/fex/dxvk-smooth-queue.conf`). Contra: +1 frame de latencia (~16 ms). |
| `forceSwapchainMSAA=0`, `samplerAnisotropy=0` (2.4) | Bajo | Quita trabajo de GPU que este juego no usa; coste cero si ya estaban efectivamente en off. |
| `deviceLocalConstantBuffers=False` (2.4) | Bajo | Tegra X1 es UMA: los constant buffers "device local" no son mas rapidos y cambian el camino de subida. |
| `enableStateCache=True` (2.4) | Mantenimiento | Deja explicito lo que ya pasaba (la cache DXVK persiste). Evita tirones de compilacion en cada arranque. |
| Limpieza de logs (2.5) | Nulo en FPS | Solo libera ~770 MB de SD. |

**Lo que NO aporta y por eso no lo he tocado:** todo lo de GPU pura (descriptor
buffers/heaps, `maxMemoryBudget`, `textureMemory`, LOD bias, etc.). El medidor
dice que la CPU esta al ~30% y el juego renderiza a 800x600: el limitador no es
memoria de GPU ni filtrado de texturas.

---

## 4. AUDIO — analizado, no es cuello de botella

- El hilo de audio aparece en `[THREADS]` como `104w:wine_dsound_mixer@2 ~1,1%`
  (un 1% **de un nucleo**). El driver es `nxaudio`
  (`[Software\Wine\Drivers] "Audio"="nxaudio"`).
- La decodificacion de los videos VP6/`.asf` y el audio latino anadido se hace
  en carga/intro, no en cada frame de partida.
- **Conclusion:** no hay ganancia real que rascar aqui sin quitar sonido.
  Recomendacion: **no tocar** (el audio latino es parte del valor del port).

---

## 5. MEDICION (como comparar antes/despues)

Herramienta creada: **`C:\Projects\ports\fifa07\tools\medir-fps.py`**

```sh
python tools/medir-fps.py D:/                 # SD en D:
python tools/medir-fps.py E:/ informe.txt     # otra letra / guardar informe
```

Lee `switch/wine/logs/fifa07.log` y saca: FPS por tramo de 10 s (del contador
`[PROGRESS] ... frames=` del propio runtime), medio/min/max/p10-p90, cuantos
tramos llegan a 58/55 FPS, los nucleos usados (`[THREADS]`), el I/O de tarjeta y
el estado de las dos caches de shaders (DXVK y NVK), con su fecha.

**Protocolo antes/despues (5 min):**

1. Arranca desde el **icono del HOME** (NSP → frontend → runtime → juego).
2. Juega **el mismo tramo** (mismo partido, mismas camaras; p.ej. 3 minutos de
   primer tiempo con la camara por defecto) **una vez con cada configuracion**.
3. Sal del juego (que el runtime cierre el log limpiamente) y ejecuta:
   `python tools/medir-fps.py D:/ antes.txt` / `... despues.txt`.
4. Compara `FPS medio`, `p10` (peor caso) y `tramos a >=58 FPS`.

**Medidor que ve el usuario:** el HUD de DXVK ya esta activo
(`dxvk-hud=fps` en `fifa07.wine-nx.txt`). Para ver tambien el **tiempo de frame**
(lo que delata la inestabilidad) cambia esa linea a
`dxvk-hud=api,fps,frametimes` (y vuelve a `fps` para jugar). Coste: el HUD se
dibuja cada frame y, ademas, con HUD activo DXVK desactiva los descriptor
buffers.

**Aviso de interpretacion:** el contador del runtime mide **fotogramas
presentados** (los que entrega su compositor OpenGL). El HUD de DXVK mide los
`Present()` del juego. Si el HUD te da ~58-60 y `medir-fps.py` da ~49, el
limitador esta en **la presentacion** (compositor/upscale), no en el juego —
ver el experimento C de la seccion 6.

---

## 6. PENDIENTES / EXPERIMENTOS (no aplicados: no se pueden validar sin consola)

Los tres son un cambio de una linea, triviales de revertir. Recomiendo probarlos
**de uno en uno**, midiendo con el protocolo de la seccion 5.

### A. `four-cores=1` en `fifa07.wine-nx.txt` (sync Horizon en vez de Standard)

- Hoy el log dice `[SYNC] Standard` (= peticiones al servidor de Wine).
  `four-cores=1` cambia a "sincronizacion directa + despertares dirigidos".
- **Por que puede ayudar:** el hilo principal pasa ~la mitad del tiempo
  bloqueado; quitar round-trips al wineserver puede recortar esa espera y bajar
  la latencia de entrada.
- **Riesgo:** cambia la semantica de sincronizacion del guest. Es la clase de
  cambio que puede volver un juego *inestable o colgado*. **Probar y si hay
  cualquier rareza, quitarlo.**
- Revertir: borrar la linea `four-cores=1`.

### B. `windows=framebuffer` (o `windows-through-opengl=false` en `settings.json`)

- Hoy: `windows=compositor` (el runtime presenta **por OpenGL**, con copia y
  escalado 800x600 -> 1280x720). La alternativa: el framebuffer "copia los
  pixeles de la ventana directamente a la pantalla".
- **Por que puede ayudar:** si el limitador es el compositor (seccion 5),
  quitar ese pase puede subir directamente los FPS.
- **Riesgo:** es la ruta de *fallback* del runtime ("para cuando el compositor
  OpenGL se porta mal"). Puede dar artefactos o cambiar el escalado. **Si algo
  se ve mal, volver a `compositor`.**
- Revertir: `windows=compositor` / `windows-through-opengl=true`.

### C. `frame-limit`

- Hoy: `frame limit Off` + VSync on (cap de 60 Hz por la pantalla).
- Si aparece tearing o el juego oscila, probar `frame-limit=60` en
  `fifa07.wine-nx.txt` para que DXVK limite a 60 exactos sin depender del VSync.

### D. Extras del preset (mas agresivos, cambian un poco lo visual)

Sobre el LOW ya aplicado, en `data/cmn/cfg_pc_h/m/l.ini` (los tres):

- `RMPARTICLES_DISABLED = 1` — apaga el sistema de particulas (el propio LOW lo
  deja en 0). Ahorro pequeno; efecto visual pequeno.
- `RMRAIN_ENABLED = 0` ya esta.
- **NO** bajar `PCCONFIG_GAMELOOP_AITICKS` por debajo de lo que trae el preset:
  eso es logica de juego (IA), no solo graficos.

### E. Verificar en hardware que los cambios entraron (2 minutos)

1. `dxvk.conf` por juego: tras jugar, en `logs/fifa07.log` busca
   `info: Found config file:` — debe apuntar a
   `C:\FIFA 07\dxvk.conf` (el local) y **no** solo al de `AppData\Local\Autorun`.
   Si siguiera saliendo solo el global, copia las claves de la seccion 2.4 al
   `drive_c/users/steamuser/AppData/Local/Autorun/dxvk.conf` (hazle antes un
   `.bak-antes-optimizacion`).
2. Preset: la cache de shaders (`D:/.mesa/...`) y la fecha de
   `...\AppData\Local\dxvk\*.dxvk.bin` deben **cambiar** tras jugar el preset
   nuevo (hay pipelines distintos que compilar).
3. Que nada se rompe: arranque, pantalla completa, audio latino y mandos.

---

## 7. CONCLUSION HONESTA: ¿60 FPS estables SIN overclock?

**Con lo aplicado, muy probablemente NO se garantizan 60 estables. Y el motivo
no es el que parecia: no es CPU.**

Lo que dicen los datos del propio runtime:

1. **El port NO esta limitado por CPU.** 40 hilos consumen **0,92–1,12 nucleos
   de los 3** disponibles; el hilo mas cargado va al ~50% y esta *esperando*, no
   calculando. Asi que optimizar "logica de juego" o "hilos" (lo tipico para un
   juego emulado) da poco: no hay CPU que recuperar.
2. **El medidor dice 49,1 FPS de media y 50,8 de mediana**, con p90 de 55,6 y
   **solo 4 tramos de 149 por encima de 58 FPS**. Es decir: el "casi 60" que se
   percibe es optimista; la realidad medida es **~50 con picos de 55-59**. Y no
   hay tirones, solo un techo un poco por debajo de 60 (coherente con "un poco
   inestables").
3. Con VSync FIFO a 60 Hz y un techo real a ~50, el frame time se queda en
   ~20 ms: eso **no** es saturación, es un **limite de tiempo por frame** —
   candidatos: (a) coste de GPU/servidor de comandos de NVK a 720p con DXVK y
   el upscale del compositor, (b) serialización present/vsync con 1-2 buffers.

Lo que **si** deberia notarse con lo aplicado (y hay que medirlo en consola):

- El preset LOW recorta muchisimo trabajo por frame (post-proceso, DOF, lluvia,
  flashes, focos, animacion de grada, IA extra). Si el limitador tenia un
  componente GPU, es el cambio que mas puede subir el techo.
- `maxFrameLatency=2` + `numCompilerThreads=1` atacan la *estabilidad* (frame
  time mas regular), no el techo.

**Sinceramente:** apostaria a que tras estos cambios el port queda en un rango
**~52-58 FPS** (mas regular, y con mas tramos a 55-60), no en 60 clavados. Para
"saber si se llega a 60" hay que jugar y medir (seccion 5); y si tras medir el
techo sigue por debajo de 60 con la CPU al 30%, lo que queda **no son ajustes de
configuracion** sino:
- reducir la resolucion de render (540p con `upscaling`), que es exactamente la
  palanca que si toca GPU — **cambio de propuesta**, no aplicado porque cambia
  la nitidez que el usuario ya valida;
- seguir el camino de driver/runtime (NVK / compositor), que se sale del alcance
  "sin overclock y sin tocar hardware".

En resumen: **se puede acercar y sobre todo estabilizar, pero garantizar 60 FPS
clavados sin overclock no es honesto prometerlo con los datos que hay.**

---

## 8. COMO REVERTIR TODO

### 8.1 Preset grafico (volver a HIGH/MEDIUM/LOW originales)

```sh
cd "/d/switch/wine/drive_c/FIFA 07/data/cmn"
cp -f cfg_pc_h.ini.bak-antes-optimizacion cfg_pc_h.ini
cp -f cfg_pc_m.ini.bak-antes-optimizacion cfg_pc_m.ini
cp -f cfg_pc_l.ini.bak-antes-optimizacion cfg_pc_l.ini   # ya era identico
```
(o, si prefieres limpiar, borra los `.bak-antes-optimizacion` cuando estes
seguro). Verificacion: los 3 deben volver a sus sha256 originales
`9c9b9150…6f51` (H), `9aa445f8…817f` (M), `3b980031…3d64` (L).

### 8.2 DXVK por juego

```sh
rm "/d/switch/wine/drive_c/FIFA 07/dxvk.conf"
```
No habia ninguno antes: borrarlo deja exactamente el estado previo.

### 8.3 Logs movidos

```sh
cp -f "C:/Projects/ports/fifa07/local/backup-logs-optimizacion/"*.log \
      "/d/switch/wine/logs/"
```

### 8.4 Nada mas que revertir

`config/settings.json` y `fifa07.wine-nx.txt` **no se han modificado**.

### 8.5 Flush obligatorio antes de sacar la tarjeta

```powershell
Write-VolumeCache -DriveLetter D
```
Tras la ejection, lo unico que prueba de verdad que la escritura llego es
**reinsertar y volver a leer** (el read-back solo prueba la cache de Windows).

---

## 9. Ficheros de esta tarea

| Fichero | Que es |
|---|---|
| `docs/OPTIMIZACION.md` | este documento |
| `tools/medir-fps.py` | medidor objetivo (FPS, CPU, I/O, caches) |
| `local/backup-logs-optimizacion/` | logs verbose/arrancados de la SD |
| SD: `data/cmn/cfg_pc_{h,m,l}.ini.bak-antes-optimizacion` | backups del preset |
| SD: `drive_c/FIFA 07/dxvk.conf` | ajustes DXVK por juego (nuevo) |

*Basado en: `logs/fifa07.log`, `logs/autorun_runtime.log`, `logs/stdout.txt`,
`config/settings.json`, `drive_c/FIFA 07/fifa07.wine-nx.txt`, los 3
`cfg_pc_*.ini`, el `dxvk.conf` global del runtime, `D:/.mesa/mesa_shader_cache_sf`
y las cadenas del propio `wine-nx-runtime.nro` (tabla de claves de
`.wine-nx.txt`, opciones DXVK y textos de su UI).*

---

# 10. BAJONES DE LOS MENUS 3D — 2a pasada (2026-10-07)

**Problema del usuario:** en partido 48–60 FPS (bien); en los **menus 3D**
(seleccion de equipos, plantillas, formaciones) cae a **1–10 FPS**.
**Objetivo:** subir los MINIMOS. Sin tocar resolucion, sin overclock, sin mover
el juego a la NAND. Todo reversible y medible.

> **Correccion de rutas:** esta tarjeta usa **`sdmc:/switch/fifa07`**, no
> `switch/wine`. Confirmado el runtime en uso:
> `wine-nx-runtime.nro` sha256 `9aa989088f6ddabc0a8e183d0044e09193afe4874894b72883b0a5da7075a58f`.
> `fifa07.exe` intacto (md5 `2060e77242ad68ca1d3fdba051f96edd`).

## 10.1 Linea base MEDIDA de los bajones (antes de tocar nada)

`python tools/medir-fps.py --sd D` sobre `logs/fifa07.log` (informe completo en
`docs/medicion-antes-20261007.txt`). 34 tramos utiles de 10 s:

| Metrica | Valor |
|---|---|
| FPS medio del run | **37,1** |
| FPS minimo (peor tramo) | **1,4** |
| p10 / p50 / p90 | **5,4** / 39,6 / 60,1 |
| Tramos < 30 FPS | **9 / 34** |
| Tramos < 20 FPS | **8 / 34** |
| Tramos < 10 FPS | **4 / 34** |

El trazado enseña el patron exacto que reporta el usuario: 47–107 s a **60 FPS**
(el partido), y luego 117–197 s cayendo 41→30→23→14→14→16→**5,4→2,7** (los menus
3D). La CPU, mientras tanto, va a **1,00 nucleos** (`[THREADS]`), asi que el
bajon **no es de calculo**: es **compilacion/espera de shaders de DXVK** en los
pipelines nuevos del menu (y I/O).

## 10.2 CAMBIOS APLICADOS (con la prueba en el fuente del runtime)

Fichero `sdmc:/switch/fifa07/drive_c/FIFA 07/fifa07.wine-nx.txt` **y** su copia
`sdmc:/switch/fifa07/config/fifa07.wine-nx.txt` (quedan **identicos**, `cmp` OK).
Se anaden 3 lineas (formato `clave=valor`, CRLF conservado):

| clave | valor | Donde el fuente lo valida (**fichero:linea**) |
|---|---|---|
| `four-cores` | `1` | `launcher_settings.h:405` (`four_cores = launcher_setting_state(kv,"four-cores") != 0`); valores validos `1`/`on` y `0`/`off` en `launcher_settings.h:390-391`; se aplica en `runtime.c:3934` → `wine_nx_thread_configure_cores()` (`runtime.c:4012`) |
| `sync` | `horizon` | `launcher_settings.h:403` (`fast_sync = ... && !strcasecmp(value,"horizon")`); se aplica en `runtime.c:3930` |
| `frame-limit` | `60` | `launcher_settings.h:215-217` (label `"60"`); parseo en `launcher_settings.h:442-444`; se traduce a DXVK `maxFrameRate` en `launcher_settings.h:243-250` |

**Aviso honesto sobre `four-cores`:** con la clave **ausente** el parser ya
devuelve `true` (`-1 != 0`, `launcher_settings.h:405`) y el log **de antes** ya
decia `[CORES] graphics workers may use core 3 at priority 63`
(= 4 nucleos activos, `thread_profile.c:131-134`). Es decir:
**`four-cores=1` es un no-op** que solo lo deja explicito; quien lo apaga es
`four-cores=0`. No lo vendo como ganancia.
**`sync=horizon` SI es un cambio real:** el log de antes decia `[SYNC] Standard`.

### Fichero NUEVO `sdmc:/switch/fifa07/drive_c/FIFA 07/dxvk.conf`

Aqui **no existia** ningun `dxvk.conf` junto al `.exe`. Contenido final exacto:

```
# FIFA 07 - ajustes DXVK por juego.
# El runtime (wine-nx) LEE este fichero y anexa su contenido al dxvk.conf que
# genera y pasa a DXVK por DXVK_CONFIG_FILE (drive_c/users/steamuser/AppData/
# Local/Autorun/dxvk.conf). Lo ultimo gana, asi que estas lineas mandan.
# Revertir = BORRAR este fichero (antes no existia).
# Claves verificadas en source/dxvk_options.c del runtime (dxvk.numCompilerThreads
# y dxvk.enableStateCache) y en la tabla d3d9 (d3d9.maxFrameLatency).
dxvk.numCompilerThreads = 4
dxvk.enableStateCache = True
d3d9.maxFrameLatency = 2
```

Por que este fichero y no el global: el runtime **lee** el `dxvk.conf` de al lado
del ejecutable, **anexa** su texto al que genera, y lo **escribe** en
`.../AppData/Local/Autorun/dxvk.conf`, que es el que pasa a DXVK por
`DXVK_CONFIG_FILE` (`runtime.c:3968-3981` lee+anexa; `:3984` guarda;
`DXVK_CONFIG_FILE` en `runtime.c:1696`). El fichero global **se reescribe en cada
arranque**, asi que las claves se ponen en el del juego (que el runtime **no**
posee). Se vera en el log:
`[DXVK] …\FIFA 07\dxvk.conf read after the launcher's settings`.

Claves verificadas en `source/dxvk_options.c` (nombre y valores admitidos):

| clave en dxvk.conf | fuente | valores admitidos |
|---|---|---|
| `dxvk.numCompilerThreads` | `dxvk_options.c:209` (valores `:18-30`) | `0`(auto)/`1`/`2`/`3`/**`4`**/`6`/`8`/`12`/`16` |
| `dxvk.enableStateCache` | `dxvk_options.c:233` | booleano `True`/`False` |
| `d3d9.maxFrameLatency` | `dxvk_options.c:269` (valores `:102-112`) | `0`/`1`/**`2`**/`3`/`4`/`8`/`16` |

**Correccion al plan (clave inexistente):** `dxvk.maxFrameLatency` **NO existe**
ni en DXVK ni en la tabla del runtime. Las claves reales de latencia son
`dxgi.maxFrameLatency` y **`d3d9.maxFrameLatency`** (`dxvk_options.c:266,269`).
FIFA 07 va por `d3d8 → d3d8to9 → d3d9`, asi que la correcta es
**`d3d9.maxFrameLatency`**. Descartada la del plan por no existir.

**`numCompilerThreads`:** el plan decia que el fichero anterior ponia `1`; en la
tarjeta **no habia** dxvk.conf y el log de antes dice
`DXVK: Using 3 compiler threads` (auto). Se pone `4`.
**Hipotesis a validar en el log** (no comprobable sin ejecutar): el 2o arranque
debe mostrar `DXVK: Using 4 compiler threads`.

## 10.3 Que se espera de cada cambio (honesto)

| Cambio | Esperado en los MINIMOS de los menus | Por que |
|---|---|---|
| `sync=horizon` | Medio | Sincronizacion directa: el hilo principal deja de esperar al wineserver; en pausas de compilacion de shaders hay menos round-trips. |
| `dxvk.numCompilerThreads=4` | **Alto en menus 3D** | Los menus compilan pipelines nuevos; mas workers = menos tiempo bloqueado en picos (el propio DXVK enumera los stutter de "compiling pipeline" al cargar menus). |
| `dxvk.enableStateCache=True` | Mantenimiento | Asegura que la cache de pipelines se conserva → el 2o arranque no recompila. |
| `d3d9.maxFrameLatency=2` | Bajo-medio (suaviza) | 2 frames en vuelo absorben el jitter corto. +1 frame de latencia (~16 ms). |
| `frame-limit=60` | **Solo Pacing** (no sube minimos) | Limita a 60 exactos por DXVK en vez de depender del VSync. **No mejora los bajones.** |
| `four-cores=1` | Ninguno (ya estaba) | Ver 10.2. |

**No aplicado a proposito:** `windows=framebuffer` (ojo: el plan decia que hoy
era `framebuffer`, pero el fichero dice **`windows=compositor`**; se deja
`compositor` sin tocar), resolucion/upscaling, overclock, mover a NAND, y el
`dxvk-hud` (sigue `fps`).

## 10.4 Cache de shaders de DXVK (NO se ha borrado ni movido)

```
sdmc:/switch/fifa07/drive_c/users/steamuser/AppData/Local/dxvk/33a216341833ba70.dxvk.bin
sdmc:/switch/fifa07/drive_c/users/steamuser/AppData/Local/dxvk/33a216341833ba70.dxvk.lut
```
El log la carga al arrancar: `info: Found cache file: ...33a216341833ba70.dxvk.bin`.
Es lo que hace que el **2o arranque vaya mejor**. Cache NVK/Mesa:
`sdmc:/.mesa/mesa_shader_cache_sf`.

## 10.5 MEDICION — script y comando exacto

Herramienta: **`C:\Projects\ports\fifa07\tools\medir-fps.py`** (reescrito; solo
libreria estandar, sin dependencias; python 3.13 o 3.14 sirven igual).

```sh
# con la SD en D:  (usa el log por defecto <sd>/switch/fifa07/logs/fifa07.log)
python tools/medir-fps.py --sd D

# guardando el informe, para comparar
python tools/medir-fps.py --sd D --out docs/medicion-despues.txt

# otra letra de SD o ruta de log explicita
python tools/medir-fps.py --sd E: --log "E:/switch/fifa07/logs/fifa07.log"
```

Saca: **FPS medio / minimo / maximo**, percentiles **p10/p50/p90**, **cuantos
tramos < 30 / < 20 / < 10 FPS**, los **ultimos 5 valores**, los nucleos usados
(`[THREADS]`), y confirma que los ajustes entraron (`[SYNC]`, `[CORES]`,
`Found config file:`, `Using N compiler threads`, `Found cache file:`).
Base de datos = lineas `[PROGRESS] … frames=<N>` del runtime (con la hora `t s`);
tambien lee el contador `[NXVK] present` como respaldo.

## 10.6 Que debe hacer el usuario

1. **Arrancar el juego DOS veces.** El **primer** arranque tras cambiar el
   `dxvk.conf` **recompila shaders y va PEOR** — es normal, no midas ese.
2. En el **SEGUNDO** arranque: entra al partido **y** a los **menus 3D**
   (seleccion de equipos, plantillas, formaciones) — el mismo recorrido que
   antes daba 1–10 FPS — y sal del juego.
3. Ejecuta `python tools/medir-fps.py --sd D --out docs/medicion-despues.txt`.
4. Mira **`tramos < 20 FPS`** y **`tramos < 10 FPS`** (antes: **8/34** y
   **4/34**) y el **FPS minimo** (antes: **1,4**). El FPS medio del partido casi
   no cambiara: lo que tiene que bajar son los **bajones**.
5. En el log, confirma que entraron: `[SYNC] Horizon`,
   `Using 4 compiler threads`, y `…\FIFA 07\dxvk.conf read after the launcher's settings`.

## 10.7 COMO REVERTIR TODO

```sh
cd "/d/switch/fifa07"
# 1) ajustes (vuelve a NO tener four-cores/sync/frame-limit)
cp -f "drive_c/FIFA 07/fifa07.wine-nx.txt.bak-antes-optimizacion-20261007" "drive_c/FIFA 07/fifa07.wine-nx.txt"
cp -f "config/fifa07.wine-nx.txt.bak-antes-optimizacion-20261007"        "config/fifa07.wine-nx.txt"
# 2) dxvk.conf por juego (no existia antes -> borrar)
rm -f "drive_c/FIFA 07/dxvk.conf"
# 3) script de medicion (opcional)
cp -f "C:/Projects/ports/fifa07/tools/medir-fps.py.bak-antes-optimizacion-20261007" \
      "C:/Projects/ports/fifa07/tools/medir-fps.py"
```
Un cambio suelto tambien se revierte a mano: quita su linea del `.wine-nx.txt`
(four-cores / sync / frame-limit) o borra el `dxvk.conf`.

**Volcado antes de sacar la tarjeta:**
```powershell
Write-VolumeCache -DriveLetter D
```

## 10.8 Ficheros de esta 2a pasada

| Fichero | Que es |
|---|---|
| SD: `drive_c/FIFA 07/fifa07.wine-nx.txt` (+ `.bak-antes-optimizacion-20261007`) | ajustes del juego: +four-cores, +sync=horizon, +frame-limit |
| SD: `config/fifa07.wine-nx.txt` (+ `.bak-antes-optimizacion-20261007`) | copia identica |
| SD: `drive_c/FIFA 07/dxvk.conf` | **nuevo**: ajustes DXVK por juego |
| `tools/medir-fps.py` (+ `.bak-antes-optimizacion-20261007`) | medidor (FPS, bajones, caches) |
| `docs/medicion-antes-20261007.txt` | informe de la linea base |

*Fuente verificada: `C:\Projects\ports\autorun-src\horizon-wine\source\{launcher_settings.h, runtime.c, dxvk_options.c, thread_profile.c}`.*
