# ARRANQUE DIRECTO — por qué fifa07.exe hace page fault y qué se ha restaurado

Última pasada: **2026-10-07 (3ª pasada: barras negras 16:9 y controles; ver §7)**.
Pasada anterior: 2026-10-07 (2ª pasada: diff por hash copia-buena vs SD; ver §2-§6).

## 1. Síntoma y punto exacto del fallo

El juego arranca, se ve el puntero/ventana y se cierra a los pocos segundos. Final
de `sdmc:/switch/fifa07/logs/fifa07.log`:

```
wine: Unhandled page fault on read access to 00000000 at address 00409F9B (thread 0004), starting debugger...
[LIFECYCLE] final tid=4 code=c0000005 ...
[EXIT] NtTerminateProcess(self) exit_code=0xc0000005
```

Desensamblado del punto de fallo (RVA 0x9F9B, image base 0x400000, bytes
`80 3E 00 57`). Es el cuerpo de una asignación `std::string` (MSVC,
`basic_string::assign(const char*)`) con **ESI = 0**:

```
00409f80: 53           push ebx
00409f81: 8b d9        mov  ebx,ecx          ; ebx = this (la std::string destino)
00409f83: 56           push esi
00409f84: 8b 74 24 0c  mov  esi,[esp+0xc]    ; esi = const char* ORIGEN
00409f88: 8d 43 08     lea  eax,[ebx+8]
00409f8b: 89 43 48     mov  [ebx+0x48],eax
00409f8e: c7 03 00 00 00 00   mov dword [ebx],0      ; len = 0
00409f94: c7 43 04 00 00 00 00  mov dword [ebx+4],0
00409f9b: 80 3e 00     cmp  byte [esi],0     <-- ESI=0  => PAGE FAULT
```

Conclusión: **una API del prefijo devolvió NULL donde el motor esperaba una
cadena C**, y el motor la asignó a un `std::string` sin comprobar NULL. El fallo
es de arranque (hilo principal tid=4), justo después de crear la ventana
`hwnd ... says FIFA 07` y de que el compositor entregue la pantalla: es el
momento en que el motor inicializa la capa de datos/gráfica y empieza la intro.

## 2. La diferencia real (diff por hash: copia buena vs SD)

Copia buena = `C:\Projects\ports\fifa07\dist\fifa07-diag\switch\wine` (idéntica a
`C:\Users\f.paolo\Desktop\NINTENDO SWITCH\NRO\fifa07-diag\switch\wine`).
SD = `sdmc:/switch/fifa07`. Comparación por tamaño + md5, no por fecha.

**Dato clave:** de 5.207 ficheros presentes en ambos lados de la carpeta del
juego, **ninguno tiene contenido distinto con el mismo tamaño**. Es decir: en la
carpeta del juego NO hay nada "alterado silenciosamente", sólo cosas **que
faltan** (más 3 ficheros de tamaño distinto, §2b).

### 2a. Faltaba en la carpeta del juego (restaurado)

| Fichero | Bytes | md5 |
|---|---|---|
| `drive_c/FIFA 07/d3d8.dll` | 486.912 | `2164ef1ddd22b58da93246c802223cf8` |
| `drive_c/FIFA 07/d3d9.dll` | 7.766.016 | `d7e955e0c59d0caa567b7bf26985c4da` |
| `drive_c/FIFA 07/dxwrapper.dll` | 7.931.392 | `9eb4cf416ab42908770b0cf8cc6baf19` |
| `drive_c/FIFA 07/dxwrapper.ini` | 3.857 | `8cfb7fb03ff926793c2dda2db4712625` |
| `drive_c/FIFA 07/DrvMgt.dll` | 41.472 | `8ee0093b1535a37f3c8781aa65d9e836` |
| `drive_c/FIFA 07/Stub.ini` | 147 | `301d981c448c7fd9ca0d1f224e13cc78` |
| `drive_c/FIFA 07/config.dat` | 24.856 | `bd223cd468998a313660284919c6cdd2` |
| `drive_c/FIFA 07/filelist.txt` | 131.847 | — |
| `drive_c/FIFA 07/fifapc.ico` | 25.622 | — |
| `drive_c/FIFA 07/FIFA_07_Readme.txt` | 3.159 | — |
| `drive_c/FIFA 07/FIFA_07_Registry_Fix.reg` | 1.404 | — |
| `drive_c/FIFA 07/SECDRV.SYS` | 12.528 | — |
| `drive_c/FIFA 07/alocale/eal_engp.vp6` (logo EA inglés) | 473.384 | — |
| `alocale/eal_dutp / eal_frep / eal_gerp / eal_itap .vp6` | 441.992–568.652 | — |
| `drive_c/FIFA 07/alocale/eas_frep.vp6` | 12.581.108 | — |
| `alocale/attr_p, attrf_p, bun_p, bunf_p, bung_p, eplf_p, eplg_p .vp6` | 42–170 MB c/u (~780 MB) | — |
| raíz: `verbose.txt`=`1`, `run-entry.txt`=`1`, `args.txt`=`C:\FIFA 07\fifa07.exe` | 3 / 3 / 23 | — |

`d3d8.dll` + `dxwrapper.dll` + `dxwrapper.ini` + `d3d9.dll` son **exactamente la
"variante B" documentada en LEEME.txt** (`_variant-b-dxvk/`, la receta de Steam
Deck): stub `d3d8.dll` → `dxwrapper.dll` (`D3d8to9=1`) → `d3d9.dll` = DXVK.
El `d3d9.dll` restaurado es **byte a byte el payload DXVK que el usuario tenía
cuando jugó** (`v3.1-17-g878473ba`, 7.766.016 B) y es el mismo que ya estaba en
`drive_c/dxvk/versions/2.3/d3d9.dll` (la pasada anterior lo repuso ahí).

### 2b. Existe en ambos pero con contenido distinto

| Fichero | Copia buena | SD antes de esta pasada |
|---|---|---|
| `drive_c/FIFA 07/data/audio/audio.big` | 2.274.836, md5 `1246dccf2f696d5acfa948b39de7369a` | 1.058.076, md5 `b329ce4a57faef748179626275fc9ad3` (**intruso**: el bueno seguía en la SD como `audio.big.bak-del-pack`) → **restaurado** |
| `drive_c/FIFA 07/data/cmn/cfg_pc_h.ini` | 2.336 | 2.620 → **NO tocado** (cfg del juego, prohibido) |
| `drive_c/FIFA 07/data/cmn/cfg_pc_m.ini` | 2.561 | 2.620 → **NO tocado** |
| `drive_c/FIFA 07/fifa07.wine-nx.txt` | 93 B (sin `windows=` ni `input-mode=`) | 125 B (**+`windows=compositor` +`input-mode=2`**) → **NO tocado** (ajuste deliberado del usuario) |
| `registry/system.reg` / `user.reg` | 17.777 / 3.600 B | 145.418 / 4.197 B |
| `wine-nx-runtime.nro` | 35.700.784 (`nx-wow64-dynarec-218` / payload `wine-test-build-2` — el que funcionaba) | 42.947.640 (`nx-amd64-fex-2640`) |

### 2c. Registro: qué se comparó y qué sale

- `HKLM\Software\EA SPORTS\FIFA 07` (y su espejo real `Software\WOW6432Node\EA
  SPORTS\FIFA 07`): **presentes en los dos**, con `CD Drive` no vacío
  (`Z:\` ahora / `D:\` en la copia buena), `Install Dir`=`C:\FIFA 07\`,
  `Registration`=`SOFTWARE\Electronic Arts\EA SPORTS\FIFA 07\ergc`. El histórico
  *"not installed correctly"* está cubierto. La SD además tiene
  `SKIP_CD_CHECK=1` (inofensivo).
- `Software\Classes\CLSID\{636B9F10-0C7D-11D1-95B2-0020AFDC7421}\InprocServer32`
  = `C:\FIFA 07\dmusic.dll` (DirectMusic): **presente en los dos**.
- `Software\Microsoft\DirectX`: `InstalledVersion` 09.00.00 / `Version`
  4.09.00.0904 en los dos.
- `HKCU\Software\Wine\DllOverrides`: copia buena = **vacío**; SD =
  `d3d8=native,builtin` y `d3d9=native,builtin` → **se deja**, porque es lo que
  hace que se use la cadena app-local (antes no había ningún `d3d8.dll`/`d3d9.dll`
  nativo, así que la clave no servía para nada).
- Diferencias que son del *build* del runtime, no del juego (no se tocan):
  `Enum\PCI\VEN_10DE&DEV_0FE0` (Tegra real) vs `VEN_FFFF…` ("Wine NX GPU") y el
  GUID del dispositivo de audio en `MMDevices\Audio\Render\…`.
- Sin claves de EA en `HKCU` en ninguna de las dos.

## 3. Por qué esto explica el page fault (y por qué la pasada anterior no bastaba)

`fifa07.exe` importa **estáticamente** (tabla de imports del PE, comprobada):

```
d3d8.dll!Direct3DCreate8      DDRAW.dll!DirectDrawCreate    DINPUT.dll!DirectInputCreateA
DSOUND.dll  GDI32  IMM32  NETAPI32!Netbios  TAPI32  WINMM  SensApi!IsNetworkAlive  USER32
ole32!CoInitialize  OLEAUT32  KERNEL32  ADVAPI32  SHELL32!SHGetSpecialFolderPathA  SHLWAPI
```

**No importa `d3d9.dll`.** Por tanto DXVK *sólo* puede servir a este juego por el
puente `d3d8.dll(stub) → dxwrapper.dll → d3d9.dll(DXVK)` = variante B.

Consecuencias, con el log en la mano:

- **Estado anterior de la SD (dxvk-version=2.3, sin ficheros app-local):** el
  payload 2.3 no trae `d3d8.dll`, así que el juego cayó al `d3d8.dll` *de Wine*
  (wined3d/OpenGL). Lo confirma `logs/fifa07.log` de la última tirada: hilos
  `[CORES] NN wined3d_cs: core 3`, `[NXCOMP] presenting the screen through
  OpenGL on NV12B ... Mesa`, y **ni una sola línea `[DXVK]`**. Es decir: DXVK no
  tocaba el juego. Eso explica por qué "cambiar la versión de DXVK no cambiaba
  nada": no había puente.
- **Estado con 3.1.1 (pasada anterior):** ahí sí entraba el `d3d8.dll` de DXVK
  3.1.1, salía el HUD de FPS... y seguía el mismo page fault. El fallo cae igual
  con DXVK 3.1.1 y con wined3d → el motor no recibía bien algo del entorno.
- **Estado que SÍ funcionaba (copia buena):** puente app-local + DXVK build
  `v3.1-17-g878473ba` + set completo de shims + **`config.dat`** presente + **las
  intros `alocale/*.vp6` presentes**. Con ese set el usuario jugó partidos.

Las tres cosas restauradas que pueden devolver un NULL a la capa de datos:

1. `config.dat` (24.856 B): el fichero de configuración del propio juego; no
   estaba. El motor lo lee al arrancar.
2. `alocale/eal_engp.vp6` (+el resto de intros): el juego reproduce el logo EA en
   cuanto crea su ventana — **el instante exacto del crash**.
3. La cadena d3d8→d3d9→DXVK (`v3.1-17-g878473ba`), el build con el que se jugó: el
   resultado de las llamadas D3D8 cambia por completo.

No se puede asegurar *cuál de las tres* dispara el NULL; las tres se han
restaurado juntas, y ahora `verbose.txt=1` (también faltaba) hará que el próximo
log muestre el detalle de módulos y llamadas para cerrar el diagnóstico si aún
falla.

## 4. Lo aplicado en la SD (todo con copia previa `.bak-antes-restaurar-20261007`)

```
drive_c/FIFA 07/  d3d8.dll d3d9.dll dxwrapper.dll dxwrapper.ini DrvMgt.dll Stub.ini
                  config.dat filelist.txt fifapc.ico FIFA_07_Readme.txt
                  FIFA_07_Registry_Fix.reg SECDRV.SYS  + alocale/*.vp6 (12 ficheros)
drive_c/FIFA 07/data/audio/audio.big   (el bueno; el de ahora queda en .bak-antes-restaurar-…)
raíz del runtime  verbose.txt=1  run-entry.txt=1  args.txt="C:\FIFA 07\fifa07.exe"
```

Verificado por md5 contra la copia buena (todos OK) y `Write-VolumeCache -DriveLetter D`
ejecutado (en esta SD se han perdido escrituras antes; volver a insertar la
tarjeta es la única confirmación real).

**NO se ha tocado**: `07z.nro`, `keys.txt` (raíz y `config/`), el mapa de
controles, `data/cmn/cfg_pc_*.ini`, `fifa07.wine-nx.txt`, `config/settings.json`,
`drive_c/dxvk/versions/*`, overclock ni partidas guardadas.
`DINPUT.dll` sigue **fuera** (en `_shims-desactivados/`): el log demuestra que
Wine carga su propio `DINPUT.DLL` sin problema, y el mando va por el
`own-controls`/`input-mode` del runtime.

## 5. Alternativas de UNA LÍNEA (en este orden)

La SD está montada como unidad `D:`. Fichero del juego:
`D:/switch/fifa07/drive_c/FIFA 07/fifa07.wine-nx.txt`.

1. **Ya aplicada** — cadena app-local + DXVK `v3.1-17-g878473ba` + `DllOverrides`
   `d3d8/d3d9=native,builtin`. Es el estado con el que se jugó. Nada que cambiar.
2. **Si sigue el page fault → volver a Wine Direct3D puro** (quitar el puente; el
   juego usará el `d3d8.dll` de Wine, que también arranca):
   `mv "/d/switch/fifa07/drive_c/FIFA 07/d3d8.dll" "/d/switch/fifa07/drive_c/FIFA 07/d3d8.dll.off"`
   `mv "/d/switch/fifa07/drive_c/FIFA 07/d3d9.dll" "/d/switch/fifa07/drive_c/FIFA 07/d3d9.dll.off"`
   `mv "/d/switch/fifa07/drive_c/FIFA 07/dxwrapper.dll" "/d/switch/fifa07/drive_c/FIFA 07/dxwrapper.dll.off"`
3. **Si sigue → quitar el compositor** (la copia que funcionaba no lo tenía):
   borra la línea `windows=compositor` de `fifa07.wine-nx.txt`.
4. **Si sigue → probar el DXVK 3.1.1** (el que dibujaba el HUD): pon
   `dxvk-version=3.1.1` en `fifa07.wine-nx.txt`.
5. **Deshacer todo lo de esta pasada**: copia de vuelta cada `*.bak-antes-restaurar-20261007`.
6. **Para saber si la cadena dxwrapper entra**: en `dxwrapper.ini` cambia
   `DisableLogging = 1` por `0`; debe aparecer `dxwrapper.log` junto al exe.

Diagnóstico del próximo log (`sdmc:/switch/fifa07/logs/fifa07.log`): con
`verbose.txt=1` buscar `[DXVK]`, los hilos `wined3d_cs` (si aparecen y no hay
`[DXVK]`, el juego está en wined3d otra vez) y las líneas
`[NXLDR] enter/load name=D3D8.DLL … base=` (si `base=10000000` es el `d3d8.dll`
de Wine; la cadena app-local carga en otra base).

## 6. Historial (pasada anterior, 2026-10-07 ~11:00-11:40)

La pasada anterior diagnosticó el fallo como "es la capa gráfica" y cambió
`dxvk-version=3.1.1` → `2.3` con el payload que funcionaba
(`drive_c/dxvk/versions/2.3/d3d9.dll`, sha256 `4950c79d…`), dejando el shim
`dmusic.dll` fuera. Es un paso **correcto pero incompleto**: repuso el DXVK bueno
en el *payload* del prefijo, pero sin los ficheros app-local del puente
(`d3d8.dll` + `dxwrapper.dll` + `d3d9.dll`) el juego nunca llega a usar DXVK
porque importa `d3d8.dll`, no `d3d9.dll`. Esta pasada añade el puente que faltaba
y completa el set de ficheros del estado que funcionaba.

Aviso que sigue vigente: no dejes que el runtime **reinstale** paquetes gráficos
por su cuenta (consola sin Internet / 90DNS), o volverá a sustituir
`drive_c/dxvk/versions/2.3/` por el 3.1.1 oficial. Si eso pasa, vuelve a copiar
`dist/fifa07-diag/switch/wine/drive_c/FIFA 07/d3d9.dll` a
`drive_c/dxvk/versions/2.3/d3d9.dll`.

## 7. 3ª pasada (2026-10-07): barras negras 16:9 y controles

### 7a. Controles: por qué no respondían

- **El log no miente:** `logs/fifa07.log` **no** contiene `[INPUT] could not read controller settings`
  → el perfil de teclas SÍ se leyó. Las únicas líneas `[NXINPUT]` del log son del **cursor** del
  ratón (`the cursor is at 837,170, the stick moved 0,0`), no del remapeo; no existe ninguna línea
  tipo "0 controls remapped" en este runtime.
- **Dónde lee el runtime:** el `.nro` está compilado con `WINE_NX_SHARED_ROOT="sdmc:/switch/fifa07"`
  (esa cadena sale 53 veces en `wine-nx-runtime.nro`; sólo 6 de `sdmc:/switch/wine` y todas de
  `lsfg`). El jugador 1 se compone EN ESTE ORDEN (gana el último):
  `sdmc:/switch/fifa07/keys.txt` → `sdmc:/switch/fifa07/config/keys.txt` →
  `…/FIFA 07/fifa07.keys.txt` (hermano, ausente) → `…/FIFA 07/fifa07.wine-nx.txt` (sólo
  `input-mode=2`). Los `keys.txt` **estaban** en el sitio correcto, pero su mapa NO era el
  confirmado: tenían `A=0x53 B=0x44 ZR=0x20 ZL=0x1b` (el histórico de `CONTROLES-DIAGNOSTICO.md`),
  no `A=0x20 B=0x1b ZR=0x44 ZL=0x53`.
- **La causa real de "no responde":** faltaba el shim `DINPUT.dll` junto al `.exe`. En
  `input-mode=2` el runtime sintetiza las teclas de `keys.txt` como eventos Win32
  (`winnx_drv.c:wine_nx_send_key`) y **FIFA 07 las recupera por DirectInput**: el shim reconstruye
  la tabla DIK de 256 códigos desde `GetKeyboardState` (ver `docs/CONTROLES-DIAGNOSTICO.md`). Con
  el `DINPUT.DLL` de serie de Wine (sin shim) el juego **no ve ninguna tecla** → los botones "no
  hacen nada". El log lo delata: `[NXLDR] enter name=DINPUT.DLL` sin ruta `Z:\…` y
  `base=FF840000` = DLL de Wine; compárese con `dxwrapper.dll`, que sí sale con ruta completa
  (`Z:\switch\fifa07\…`) y `base=FE230000`. El aviso de la 2ª pasada ("el mando va por
  `own-controls`/`input-mode`") era **incorrecto**.

**Aplicado**
1. `keys.txt` (raíz) y `config/keys.txt` reescritos con el mapa confirmado
   (`A=0x20 B=0x1b X=0x57 Y=0x41 ZR=0x44 ZL=0x53 R=0x45 L=0x10 PLUS=0x1b MINUS=0x0d
   STICKL=0x5a STICKR=0x43 input-mode=2`). Copias: `*.bak-antes-arreglo-20261007`.
2. Shim `DINPUT.dll` devuelto junto al `.exe` desde el build **corregido**
   (`build/fifa07-shims/DINPUT.dll`, md5 `53bc6ceb2838301262ca79f3128a30bd`), que además elimina
   el bug flechas→teclado numérico (tácticas). El de `_shims-desactivados/` es un build anterior
   (`1f6157cb…`, el mismo de la copia buena) y queda como respaldo.

**Alternativas de una línea**
- Rarezas de entrada con el shim: borrar `drive_c/FIFA 07/DINPUT.dll` (vuelve al de Wine; los
  controles volverían a no responder).
- Volver al mapa anterior: `cp keys.txt.bak-antes-arreglo-20261007 keys.txt` (íd. en `config/`).
- `input-mode`: 1 = mando XInput (no emite teclas), 2 = teclado (actual). Está en los dos
  `keys.txt` y en `…/fifa07.wine-nx.txt`; manda el del `.wine-nx.txt`.

### 7b. Barras negras: por qué salían y qué se cambió

- **El runtime NO puede estirar:** el blit de `dlls/win32u/vulkan.c` (~línea 3492) hace
  `scale = min(host/w, host/h)` y centra (`offset = (host - size)/2`): conserva SIEMPRE el
  aspecto. El log lo canta: `[NXVK] swapchain 800x600 … scaled into 1280x720` y
  `[NXVK] scaled present 30 read back 1280x720: … left bar 000000` (barra negra a la izquierda).
  No hay clave de runtime que estire: `upscaling` sólo elige filtro (bilinear/FSR/integer), y
  `windows=framebuffer` es la ruta de reserva (copia sin escalar, **empeoraría**).
- **Por eso hay que hacer que el JUEGO renderice 16:9.** FIFA 07 sólo tiene UNA resolución 16:9
  nativa: **1280x720**. Su tabla de modos está en `fifa07.exe` (~offset 4997860): 640x480,
  800x600, 1024x768, **1280x720**, 1280x1024, 1600x1200 (32 bpp). El runtime publica UN único
  modo de pantalla, justo **1280x720** (`winnx_drv.c`: `WINE_NX_SCREEN_W/H`). El perfil del juego
  (`Documents/FIFA 07/A. Perfiles`) ya trae `OPTIONS/WIDESCREEN=1` y `OPTIONS/RESOLUTION=1`; ese
  `1` es el índice de 800x600 en la tabla → por eso renderiza 800x600.
- El puente de la copia buena (d3d8→dxwrapper→d3d9=DXVK) ya está activo y **no se toca**.

**Aplicado** (lo menos invasivo: fichero NUEVO del juego, borrable) —
`drive_c/FIFA 07/locale.ini` (raíz del juego), 64 bytes:

```
[]
WINDOWED = 0
WIDESCREEN = 1
RESOLUTION = 1280x720x32
[]
```

Es el override externo documentado para FIFA 07. Con `RESOLUTION = 1280x720x32` el juego crea una
swapchain de 1280x720 = tamaño de pantalla → blit 1:1, **sin barras**.

**Alternativas si no llena**
1. **En el juego:** *Mi FIFA 07 → Ajustes → Pantalla* y elegir **1280x720** (es el único modo que
   reporta el runtime; `WIDESCREEN=1` ya está). Lo más limpio, sin ficheros.
2. Si `locale.ini` no se leyese: en `Documents/FIFA 07/A. Perfiles/A. Perfiles` poner
   `OPTIONS/RESOLUTION=3` (=1280x720). OJO: ese fichero tiene un campo de 8 bytes en el offset 20
   que cambia al guardar (probable checksum/timestamp); editarlo a mano puede hacer que el juego
   lo resetee. **Copia antes.**
3. Último recurso (toca el puente, **no recomendado**): en `dxwrapper.ini`,
   `[FullScreen] FullScreen = 1` + `ForceWindowResize = 1` fuerza la ventana al tamaño de la
   pantalla; llenaría el ancho pero DXVK estiraría 800x600→1280x720 (aspecto deformado). Hacer
   `.bak` de `dxwrapper.ini` y revertir restaurándolo.
4. Revertir lo de esta pasada: borrar `drive_c/FIFA 07/locale.ini`.

### 7c. El arranque sigue intacto

- No se ha tocado `07z.nro`, el overclock, las partidas ni el puente. md5 sin cambios:
  `d3d8.dll 2164ef1ddd22b58da93246c802223cf8`, `dxwrapper.dll 9eb4cf416ab42908770b0cf8cc6baf19`,
  `d3d9.dll d7e955e0c59d0caa567b7bf26985c4da`, `dxwrapper.ini 8cfb7fb03ff926793c2dda2db4712625`.
- La cadena DXVK del último log (`DXVK: v3.1-17-g878473ba`, `d3d8.dll base=10000000`,
  `dxwrapper.dll base=FE230000`) es exactamente la que queda.

## 8. 4ª pasada (2026-10-07): 16:9 a BAJA resolución (llena la pantalla SIN perder FPS)

### 8a. Método de la comunidad (fuente)

WSGF — [FIFA 07 · Changing Resolution](https://www.wsgf.org/dr/fifa-07): el juego sólo tiene un
modo 16:9 nativo (1280x720); para cualquier otra resolución **se hex-edita `fifa07.exe`** buscando
`00 05 00 00 D0 02` (=1280x720) y sustituyéndolo por el hex de la resolución deseada, con formato
`w:WORD, 0000, h:WORD` (ej. 3840x2160 = `00 0F 00 00 70 08`). Después se selecciona **1280x720** en
el juego y éste renderiza al tamaño nuevo; el FOV/aspecto 16:9 lo fija `WIDESCREEN=1` del perfil.
Hilos de apoyo: [soccergaming](https://soccergaming.com/forums/threads/fifa-07-in-widescreen.134595/)
y [foro WSGF](https://wsgf.org/phpBB3/viewtopic.php?t=13733) — describen el `WIDESCREEN=0→1` del
perfil `A. Perfiles` con editor hex y el `locale.ini` en la raíz del juego para forzar resolución.
Conclusión de los hilos: **por debajo de 720p no hay modo 16:9 de fábrica** → hay que forzarlo.

### 8b. Qué resolución y por qué (la clave del port)

El runtime NO estira (`dlls/win32u/vulkan.c` ~3492: `scale=min(host/w,host/h)` y centra). Si el juego
renderiza 16:9 **exacto**, el blit de 1:1-en-aspecto llena 1280x720 SIN barras:

| resolución | escala a 1280x720 | px del juego | nota |
|---|---|---|---|
| 800x450 | min(1.6,1.6)=**1.6 → exacto** | 360.000 | **elegida** (−25% vs 800x600) |
| 640x360 | **2.0 → exacto** | 230.400 | la más ligera |
| 960x540 | **1.3333 → exacto** | 518.400 | la de más calidad de las bajas |
| 854x480 | 1.4988 → 1280x719 | 409.920 | NO exacta (deja ~1 px) |

800x450 se elige por equilibrio: llena exacto Y tiene **menos** carga que el actual 800x600, así que
no baja los FPS (los sube). 640x360 si se quiere máximo margen; 960x540 si se prima nitidez.

### 8c. Aplicado

1. **`fifa07.exe`** — tabla de modos (records de 8 bytes `w,0,h,0`, cada uno seguido de `20 00 00 00`=32bpp):
   - idx1 `800x600` @`0x4c42f8`: `20 03 00 00 58 02` → **`20 03 00 00 C2 01`** (800x450)
   - idx3 `1280x720` (slot 16:9 nativo) @`0x4c4318`: `00 05 00 00 D0 02` → **`20 03 00 00 C2 01`** (800x450)
   - Copia: `fifa07.exe.bak-ws800x450` (md5 `cc271e0a1b05b3d17b0415ce3aa0d33f`; parcheado = `0d369eecd54774fb58cab54bb33e91dc`).
2. **`drive_c/FIFA 07/locale.ini`** (coherente con lo anterior): `WINDOWED = 0` / `WIDESCREEN = 1` /
   `RESOLUTION = 800x450x32`. Copia del anterior (1280x720x32): `locale.ini.bak-ws1280x720`.
3. **Perfiles** (ambos traían `WIDESCREEN=1`): se fija `DEFAULTRESOLUTION=1` y `RESOLUTION=1`
   (= idx1, ya parcheado a 800x450). En `A. Profiles` el `RESOLUTION` estaba a `0` → pasado a `1`.
   Copias: `*.bak-liveprefs` / `*.bak-16x9`.

**No se ha tocado** el puente d3d8/dxwrapper/d3d9, `07z.nro`, `keys.txt`, overclock ni partidas.
md5 del puente sin cambios (§7c): `d3d8.dll 2164ef1d…`, `dxwrapper.dll 9eb4cf41…`,
`d3d9.dll d7e955e0…`, `dxwrapper.ini 8cfb7fb0…`.

### 8d. Alternativas y cómo revertir

- **Otra resolución baja:** re-escribir los DOS records de 8 bytes con el hex nuevo —
  `640x360: 80 02 00 00 68 01` · `960x540: C0 03 00 00 1C 02` · `854x480: 56 03 00 00 E0 01` (no exacta).
- **Revertir todo:**
  ```bash
  cd "<SD>/switch/fifa07/drive_c/FIFA 07"
  cp fifa07.exe.bak-ws800x450 fifa07.exe          # exe original (md5 cc271e0a…)
  cp locale.ini.bak-ws1280x720 locale.ini         # o: rm locale.ini
  # perfil: restaurar A. Profiles.bak-16x9 (RESOLUTION volvía a 0)
  ```
- Sin el exe parcheado las únicas opciones son 1280x720 nativo (más carga → menos FPS) o 800x600
  (barras negras). El parche del exe es la pieza que habilita el 16:9 bajo.

## 9. 5ª pasada (2026-10-07): por qué seguían las barras (diagnóstico del log) y arreglo

### 9a. La verdad del log: el juego renderizaba 640x480, NO 800x450

El log más reciente (`logs/fifa07.log`, 21:26) dice literalmente:

```
[NXVK] swapchain 640x480 format 44 scaled into 1280x720 screen buffers (fifo)
[NXVK] scaled present 30 read back 1280x720: centre 4d230e, left bar 000000, 10854 of 14400 samples lit
…
info: D3D9DeviceEx::ResetSwapChain:  Requested Presentation Parameters  Width: 640  Height: 480
info:  Setting display mode: 640x480@0
```

O sea: la swapchain del juego es **640x480** (índice 0 de la tabla), no 800x450. Con 640x480 el blit
hace `scale=min(1280/640, 720/480)=min(2.0, 1.5)=1.5` → **960x720 centrado → 160 px de barra negra a
cada lado**. Ese es el `left bar 000000`. **El parche del exe de §8c nunca llegó a usarse.**

### 9b. Causa raíz (doble)

1. **Dos records con el mismo valor** (`800x450` en idx1 **y** idx3, §8c) violaron la regla del §8d.
   Peor: `800x450` no es un modo estándar. El juego **valida** el modo elegido contra los modos que
   reporta el sistema (`fifa07.exe` importa `EnumDisplaySettingsA`/`ChangeDisplaySettingsA`); al no
   poder usar `800x450` **cayó al modo más bajo de la tabla**, `640x480` (idx0) → 4:3 → barras.
   *Prueba*: el log antiguo `fifa07_verbose.log` (14:12), cuando idx1 era el `800x600` original,
   muestra `Setting display mode: 800x600` — el juego **sí** usa el valor de la tabla; dejó de usarlo
   justo tras convertirlo en `800x450`.
2. **El perfil NO tenía `RESOLUTION=1`** (el §7/§8c se equivocaban). El perfil vivo
   (`Documents/FIFA 07/A. Profiles/A. Profiles`) dice, en texto ASCII:
   `OPTIONS/WIDESCREEN=1&OPTIONS/RESOLUTION=0&…` y `OPTIONS/DEFAULTRESOLUTION=1`.
   El único byte que difiere de las copias de seguridad es el `1` de `WIDESCREEN` (offset `0xB49`);
   `RESOLUTION` está en **`0`** (offset `0xBA3`). Editar el perfil a mano **no hace falta** (ver 9d).

### 9c. Aplicado (método de la comunidad, un solo record)

Se deja la tabla como el original **salvo el slot 16:9 nativo**, que es el que el juego usa al
elegir "1280x720" en pantalla:

| idx | offset | antes | después | significado |
|---|---|---|---|---|
| 1 | `0x4c42f8` | `20 03 00 00 C2 01` | `20 03 00 00 58 02` | 800x450 → **800x600** (restaurado) |
| 3 | `0x4c4318` | `00 05 00 00 D0 02` | `80 02 00 00 68 01` | 1280x720 → **640x360** |

Tabla final (6 valores DISTINTOS): 640x480 · 800x600 · 1024x768 · **640x360** · 1280x1024 · 1600x1200.
`640x360` es 16:9 exacto y `1280/640=720/360=2.0` → **escala entera 2×, llena 1280x720 justo, 0 barras**.
Además es un **25 % más ligero** que el 640x480 que rendía de verdad → sube los FPS, no baja.

- Fichero: `drive_c/FIFA 07/fifa07.exe`
- md5 antes (estado §8c): `315bfc2f26641e16fbe7ee42d85531b7`
- md5 después: **`2060e77242ad68ca1d3fdba051f96edd`**
- Copia del estado previo: `fifa07.exe.bak-antes-16x9-640x360` (md5 `315bfc2f…`)
- Original de fábrica (sin ningún parche): `fifa07.exe.bak-16x9` (md5 `cc271e0a1b05b3d17b0415ce3aa0d33f`)

No se ha tocado el puente d3d8/dxwrapper/d3d9, `DINPUT.dll`, `dmusic.dll`, `keys.txt`, `07z.nro`,
overclock, `data/` ni partidas.

### 9d. Qué debe hacer el usuario (una vez)

En el juego: **Mi FIFA 07 → Ajustes → Pantalla** y elegir el modo que ocupa el slot widescreen
(aparecerá como **640x360** si la lista sale de la tabla, o como **1280x720** si sale del sistema —
es el mismo registro). Al confirmar, el juego reescribe su perfil con checksum válido y ya renderiza
640x360 → pantalla llena. **No hay que editar el perfil a mano.**

### 9e. Cómo revertir

```bash
cd "<SD>/switch/fifa07/drive_c/FIFA 07"
cp fifa07.exe.bak-antes-16x9-640x360 fifa07.exe   # vuelve al estado 315bfc2f… (640x480, con barras)
# o, original de fábrica total:
cp fifa07.exe.bak-16x9 fifa07.exe                 # cc271e0a… (800x600, con barras)
```

### 9f. Si aún hubiera barras (siguiente hipótesis concreta)

Si tras elegir el modo en pantalla el log (`logs/fifa07.log`) sigue mostrando
`swapchain 640x480`, entonces el juego descarta valores con **alto < 480** (explicaría por qué
rechazó 800x450 y 640x360). En ese caso el slot widescreen debe ser **854x480** (16:9, alto 480,
llena 1280x719 ≈ 0 barras):

- idx3 `0x4c4318`: `80 02 00 00 68 01` → **`56 03 00 00 E0 01`** (854x480).
- Plan B sin exe: en `A. Profiles` poner `OPTIONS/RESOLUTION=3` (un solo carácter ASCII en el
  offset **`0xBA3`**); **hacer `.bak` antes** — el juego valida su cabecera.

## 10. 6ª pasada (2026-10-07): el RUNTIME publica un escritorio 640x360 (escala ×2 exacta)

### 10a. Qué se cambió (una sola cosa)

El único modo de escritorio que publica el runtime estaba fijo en 1280x720. Ahora publica **640x360**
(16:9 exacto). Fichero y líneas exactas:

- Fichero fuente (host): `C:\Projects\ports\autorun-src\dlls\win32u\winnx_drv.c`
- Línea **542** (comentario, coherente con el valor): `Report a single 640x360 primary monitor …`
- Líneas **545-546** (las constantes):

```c
#define WINE_NX_SCREEN_W 640     /* antes: 1280 */
#define WINE_NX_SCREEN_H 360     /* antes:  720 */
```

Son las únicas que alimentan `wine_nx_drv_UpdateDisplayDevices()`, que publica **un solo modo**
(`dm->add_modes( &current, 1, &mode, … )`). **No se tocó nada más del runtime.**

> El fichero que realmente compila el binario vive en el volumen Docker persistente `autorun-dev`,
> en `/work/dlls/win32u/winnx_drv.c` (lo referencia `build-switch-amd64/build.ninja`). El script de
> build lo **sincroniza desde el host**, así que el host es la fuente de verdad.
> md5 host = md5 volumen tras el cambio = `7e8e3fdb6b479a4d75ee33f0d3bf17d9`.

### 10b. Por qué 640x360

Blit del runtime (`dlls/win32u/vulkan.c` ~3492): `scale = min(host_w/w, host_h/h)` con `host` =
buffers de pantalla = **1280x720** fijos. Para que el blit llene **sin barras** hace falta
`scale = 2.0` exacto → `w,h = 640x360`. El juego (fullscreen) adopta el escritorio publicado, así que
con `RESOLUTION=3` (slot idx3 = `640x360` del exe, §9c) el swapchain pasa a ser 640x360 →
`min(1280/640, 720/360) = 2.0` → **1280x720 lleno, 0 px de barra**, y **sin coste** (el juego renderiza
230.400 px, un 25 % menos que el 640x480 con el que corría).

### 10c. Comando de compilación

Script nuevo: `C:\Projects\ports\autorun-stage8-fifa07root-1p-640x360.sh` (deriva de
`autorun-stage7-fifa07root-1p.sh`, mismos flags de raíz fifa07 y **sin** parche de 2 jugadores).

```bash
cd /c/Projects/ports && sh ./autorun-stage8-fifa07root-1p-640x360.sh
```

Internamente (idéntico al stage7 salvo que sólo sincroniza `winnx_drv.c` y hace build incremental):

```sh
# 8a) sincronizar SOLO el fuente cambiado al volumen
docker run --rm -v "C:/Projects/ports/autorun-src:/host:ro" -v autorun-dev:/work alpine \
  sh -c 'cp -a /host/dlls/win32u/winnx_drv.c /work/dlls/win32u/winnx_drv.c && touch /work/dlls/win32u/winnx_drv.c'
# 8b) compilar (mismo dir build, mismos flags del stage7)
docker run --rm -v autorun-dev:/work -w /work -e DEVKITPRO=/opt/devkitpro-release \
  ghcr.io/autorunhq/switch-dev:2026.10.01 \
  sh -ec 'cmake --build horizon-wine/build-switch-amd64 --target wine-nx-runtime-nro -j"$(nproc)"'
```

Resultado de la compilación: **0 errores**; ninja recompiló sólo
`CMakeFiles/wine-win32u-real.dir/work/dlls/win32u/winnx_drv.c.obj` y enlazó el NRO.

### 10d. Artefacto y despliegue en la SD

| | |
|---|---|
| NRO nuevo (host) | `C:\Projects\ports\runtime-fifa07root-1p-640x360\wine-nx-runtime.nro` |
| NRO nuevo (SD) | `D:\switch\fifa07\wine-nx-runtime.nro` |
| Tamaño | **42.947.640 B** (idéntico al anterior) |
| **sha256 nuevo** | **`9aa989088f6ddabc0a8e183d0044e09193afe4874894b72883b0a5da7075a58f`** |
| sha256 anterior | `e42afefaad820d0ab9b2fb55ed5d985e73f9ab4fb6e92586c7614b4f45cac4a7` |
| Copia de seguridad | `D:\switch\fifa07\wine-nx-runtime.nro.bak-antes-pantalla-640x360` (md5 = el anterior) |

Verificado tras copiar: el sha256 en la SD **coincide** con el del host; cabecera NRO válida
magic `NRO0` en el offset `0x10` (los 16 primeros bytes son idénticos al NRO que ya arrancaba);
contiene la cadena de raíz `sdmc:/switch/fifa07` (10 apariciones); **0** apariciones de cadenas de
2 jugadores (`player2`/`keys2`), igual que el binario anterior. `Cmd` de volcado:
`Write-VolumeCache -DriveLetter D` (OK) + `sync`.

**No se ha tocado** `fifa07.exe` (md5 sigue `2060e77242ad68ca1d3fdba051f96edd`), el perfil
(`OPTIONS/RESOLUTION=3`, `OPTIONS/WIDESCREEN=1`), `07z.nro`, el puente d3d8/dxwrapper/d3d9,
`DINPUT.dll`, `dmusic.dll`, `keys.txt`, el mod de audio, el overclock ni las partidas.

### 10e. Cómo revertir

```bash
cp "/d/switch/fifa07/wine-nx-runtime.nro.bak-antes-pantalla-640x360" \
   "/d/switch/fifa07/wine-nx-runtime.nro"
# y volcar caché:  powershell -c "Write-VolumeCache -DriveLetter D"
```

(deja el runtime que publicaba 1280x720, sha256 `e42afefa…`). En el código: poner de vuelta
`WINE_NX_SCREEN_W 1280` / `WINE_NX_SCREEN_H 720` en `winnx_drv.c` líneas 545-546 y reejecutar el
stage8. Se puede volver a `autorun-stage7-fifa07root-1p.sh` tal cual.

### 10f. Qué debe probar el usuario y qué debe verse en el log

1. Arrancar FIFA 07 como siempre (forwarder / `07z.nro`).
2. En el juego: **Mi FIFA 07 → Ajustes → Pantalla** y elegir el modo widescreen que ocupa el **idx3**
   (aparecerá como `640x360` si la lista sale de la tabla del exe). El perfil ya trae `RESOLUTION=3`,
   así que normalmente arranca ya en él.
3. Comprobar en `D:\switch\fifa07\logs\fifa07.log`:

```
[NXVK] swapchain 640x360 format 44 scaled into 1280x720 screen buffers (fifo)
[NXVK] scaled present … read back 1280x720: centre …, left bar 000000, … of … samples lit
```

Lo que confirma el éxito: **`swapchain 640x360`** (no 640x480 ni 800x600) y **ausencia de la
columna `left bar 000000`** (si la hubiera, sigue habiendo barras laterales). Con 640x360 el blit es
×2.0 exacto → 1280x720 lleno.

> **Aviso / estado previo a esta pasada:** el log anterior (última sesión, `logs/fifa07.log`) aún
> mostraba `swapchain 640x480 … left bar 000000` (`Setting display mode: 640x480@0`), es decir el
> juego todavía NO había adoptado el `640x360` del exe/perfil. Si tras esta pasada el log **sigue**
> en `swapchain 640x480`, el siguiente candidato es `854x480` en el idx3 (16:9, alto ≥ 480; §9f) —
> en ese caso esta pasada del runtime no basta y hay que re-tocar el exe.
