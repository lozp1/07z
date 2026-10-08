# Diagnóstico: el stick izquierdo cambia las tácticas en FIFA 07

Estado: **causa raíz encontrada, corregida y compilada**. Falta un solo paso del
usuario: copiar el `DINPUT.dll` corregido a la SD (no se ha tocado la SD desde
esta sesión).

---

## 1. Síntoma

«Al mover el stick izquierdo, FIFA 07 sigue cambiando las tácticas.» El usuario
ya probó a ajustar el mapa del stick.

Mapa vigente del jugador 1 (`sdmc:/switch/wine/drive_c/FIFA 07/fifa07.keys.txt`,
copiado también en `sdmc:/switch/wine/config/keys.txt` y `sdmc:/switch/wine/keys.txt`):

```
UP/DOWN/LEFT/RIGHT = 0x26/0x28/0x25/0x27   (flechas)
LUP/LDOWN/LLEFT/LRIGHT = 0x26/0x28/0x25/0x27 (flechas)
A=0x53 B=0x44 X=0x57 Y=0x41 ZR=0x20 ZL=0x1b R=0x45 L=0x10
PLUS=0x1b MINUS=0x0d STICKL=0x00 STICKR=0x00
RUP=0x10 RDOWN=0x5a RLEFT=0x00 RRIGHT=0x00
RSTICK=keys LSTICK=keys DPAD=keys input-mode=2
```

## 2. Lo que NO es la causa (descartado con código)

**El runtime no inventa teclado numérico a partir del stick.** Comprobado:

* `horizon-wine/source/input_profile.c` — `input_map_keys()` sólo emite el
  código que figura en `keys.txt` para cada control. No hay ninguna síntesis de
  `0x60..0x6f` (teclado numérico) ni ninguna tabla de tácticas.
* `input_profile.c` no conoce `LSTICK`, `RSTICK` ni `DPAD`: sus 24 fuentes son
  `A B X Y L R ZL ZR PLUS MINUS STICKL STICKR UP DOWN LEFT RIGHT LUP LDOWN
  LLEFT LRIGHT RUP RDOWN RLEFT RRIGHT`. Es decir, `LSTICK=keys`, `RSTICK=keys` y
  `DPAD=keys` son líneas que **se ignoran** (el valor `keys` ni siquiera parsea
  como código). No cambian nada.
* El stick manda exactamente las flechas: `source_value()` (fuente 16..19 = LUP
  /LDOWN/LLEFT/LRIGHT) toma el eje 0/1 y `input_map_keys()` publica el VK 0x26
  /0x28/0x25/0x27. Es correcto y no hay tácticas ahí.

**Tampoco hay tácticas de teclado con Q + numérico**: como el mapa no tiene Q ni
teclado numérico, la única forma de que FIFA cambie táctica es que *reciba* esos
códigos por otro camino.

## 3. Causa raíz real

FIFA 07 sobre Wine-NX **no lee el teclado por VK, lo lee por DirectInput**. En
`input-mode=2` (teclado) el runtime sintetiza los VK de `keys.txt` como eventos
de teclado de Win32 (`dlls/win32u/winnx_drv.c:wine_nx_send_key`), y el juego los
recupera a través de **nuestro shim** `DINPUT.dll` que vive junto al `.exe`
(`sdmc:/switch/wine/drive_c/FIFA 07/dinput.dll`, md5 `8ba89c42…`, idéntico a
`build/fifa07-shims/DINPUT.dll`). El shim reconstruye la tabla de 256 códigos
DirectInput (`DIK`) desde el estado de teclado con `GetKeyboardState`.

El fallo está en esa reconstrucción, `read_keyboard()`:

```c
sc = MapVirtualKeyA(vk, MAPVK_VK_TO_VSC);
if (!sc || sc > 0x7f) continue;
out[sc] = 0x80;                                 /* <-- aquí está el problema */
if (vk_is_extended(vk)) out[0x80 | sc] = 0x80;
```

`MapVirtualKeyA(vk, MAPVK_VK_TO_VSC)` devuelve el **byte bajo** del scan code, y
en las teclas extendidas ese byte es *el mismo* que el de una tecla del teclado
numérico. Medido en Windows real (a través de `user32!MapVirtualKeyA`):

| VK que emite el stick | `MapVirtualKeyA(vk,0)` | Es el DIK de |
|---|---:|---|
| `VK_UP`    0x26 | 0x48 | **NumPad 8** (táctica ~Contraataque) |
| `VK_LEFT`  0x25 | 0x4B | **NumPad 4** (táctica ~3rd man) |
| `VK_RIGHT` 0x27 | 0x4D | **NumPad 6** (táctica ~Wing play) |
| `VK_DOWN`  0x28 | 0x50 | **NumPad 2** (táctica ~Box overload) |

El código escribía **las dos** casillas: `out[0x4B]` (NumPad 4) y `out[0xCB]`
(flecha izquierda). FIFA 07 usa el teclado numérico para las tácticas rápidas de
ataque (`NumPad 2/4/6/8`; las defensivas son `Q + NumPad`). Resultado: cada
empujón del stick —y también de la cruceta, que va a las mismas flechas—
publicaba «flecha» **y** «NumPad», y FIFA cambiaba la táctica además de mover al
jugador.

Evidencia directa del binario que corre hoy en la SD:

* `sdmc:/switch/wine/logs/autorun_runtime.log` registra
  `[NXLDR] load name=DINPUT.DLL` desde la carpeta del juego → el shim es el que
  contesta. (Su md5 en la SD es el del shim, no una DLL de Wine/Windows.)

Evidencia de la mecánica (reproductor del algoritmo, `tools/_test_dinput_dik.c`,
compilado y ejecutado en este host contra `user32!MapVirtualKeyA`):

```
VK_UP   (arriba)  numpadDIK 0x48 -> viejo:PRESIONADO  nuevo:libre  | arrowDIK PRESSED
VK_LEFT (izq)     numpadDIK 0x4B -> viejo:PRESIONADO  nuevo:libre  | arrowDIK PRESSED
VK_RIGHT(dcha)    numpadDIK 0x4D -> viejo:PRESIONADO  nuevo:libre  | arrowDIK PRESSED
VK_DOWN (abajo)   numpadDIK 0x50 -> viejo:PRESIONADO  nuevo:libre  | arrowDIK PRESSED
VK_NUMPAD4 real   numpadDIK 0x4B -> viejo:PRESIONADO  nuevo:PRESIONADO
CONCLUSION: flechas que se colaban como teclado numerico -> viejo=4, nuevo=0
TEST OK: el bug existe y el fix lo elimina
```

## 4. Corrección aplicada

Una tecla extendida (flechas, Ctrl derecho, Inicio/Fin/RePág/AvPág…) **sólo** se
publica en su código DirectInput con prefijo `0x80`; nunca en el byte bajo «desnudo»,
que es el del teclado numérico.

`src/shims/dinput_fifa07.c`, en `read_keyboard()`:

```diff
         sc = MapVirtualKeyA(vk, MAPVK_VK_TO_VSC);
         if (!sc || sc > 0x7f) continue;
-        out[sc] = 0x80;
+        /* An extended key (an arrow, Right Ctrl, Home/End...) carries a scan
+         * code whose low byte is the very code of a numeric-keypad key:
+         * MapVirtualKeyA(VK_LEFT, ...) is 0x4B, and 0x4B is DIK for NumPad 4.
+         * Writing that bare code in addition to the 0x80-prefixed one therefore
+         * reports every arrow as a keypad key -- and FIFA 07 reads the keypad
+         * digits 2/4/6/8 as its in-game team-tactics hotkeys, so a left-stick
+         * push (mapped to the arrow keys) changed tactics.  An extended key
+         * must land ONLY on its 0x80-prefixed DirectInput code. */
         if (vk_is_extended(vk)) out[0x80 | sc] = 0x80;
+        else out[sc] = 0x80;
     }
```

### Qué se gana y qué no se pierde

* El stick **sigue moviendo** (la flecha se publica igual: DIK `0xCB/0xC8/0xCD/0xD0`).
* El stick y la cruceta **ya no cambian tácticas** (desaparece la publicación de
  `0x48/0x4B/0x4D/0x50`).
* Un teclado numérico de verdad (si algún día se mapea en `keys.txt`, p. ej.
  `SOMEBUTTON=0x62`) sigue funcionando: los VK `VK_NUMPAD*` no son extendidos y
  publican su código correcto.

### Artefacto

```
build/fifa07-shims/DINPUT.dll                          (corregido)
  sha256 e46117f6768ac1f1ce972faf6fa0293cc0822db3074980743332d76ccf5b1e82
  md5    53bc6ceb2838301262ca79f3128a30bd
build/fifa07-shims/DINPUT.dll.antes-del-fix-numpad     (copia del anterior)
  md5    8ba89c42ccabaedfbaef7b436e1765cd   <- el que está ahora en la SD
```

Compilado y verificado con el script del propio repo
(`python tools/build-fifa07-shims.py --build-only`): i386, export
`DirectInputCreateA`, sin `api-ms-*`, no copia de una DLL del PC.

### Cómo desplegarlo (lo hace el usuario, no esta sesión)

```powershell
powershell -ExecutionPolicy Bypass -File tools\instalar-shim-en-sd.ps1
```

Copia `build\fifa07-shims\DINPUT.dll` a
`sdmc:/switch/wine/drive_c/FIFA 07/dinput.dll` (con copia de seguridad y
apartando antes los `dinput` de Windows, si los hubiera).

## 5. Pendiente relacionado (no aplicado a propósito)

El mismo sesgo existe, en menor medida, en el runtime al **inyectar** la tecla:
`dlls/win32u/winnx_drv.c:wine_nx_send_key` (líneas ~611-620) pone
`input.ki.wScan = scan & 0xff` y sólo marca `KEYEVENTF_EXTENDEDKEY` si el byte
alto del scan code es `0xE0`. Si la implementación de `NtUserMapVirtualKeyEx`
de Wine-NX no devolviera el `0xE0` (en mi prueba sobre `user32!MapVirtualKeyEx`
de Windows, `MAPVK_VK_TO_VSC_EX` devolvió `0x004B`, sin `0xE0`), la tecla
inyectada llevaría el scan code del NumPad sin la marca de extendida.

No lo he tocado porque: (1) el shim recalcula el DIK desde el **VK**, así que su
corrección ya resuelve el síntoma; (2) endurecerlo exige recompilar el runtime
compartido y probarlo en hardware. Queda anotado como mejora defensiva:

```c
/* defensivo: las flechas y demás extendidas deben llevar la marca E0 */
static int vk_is_extended_key( UINT vk ) { return vk == VK_LEFT || vk == VK_RIGHT ||
                                                  vk == VK_UP   || vk == VK_DOWN; }
...
if ((scan & 0xff00) == 0xe000 || event->code == INPUT_NUMPAD_ENTER ||
    vk_is_extended_key( event->code )) input.ki.dwFlags |= KEYEVENTF_EXTENDEDKEY;
```

## 6. Nota sobre un mapa de teclas antiguo

En `dist/fifa07-diag/…/fifa07.keys.txt` y en el volcado de
`tools/package_fifa07_diag.py` se afirmaba que el fichero propio del juego se lee
«porque `fifa07.wine-nx.txt` pone `own-controls=1`». Eso es **inexacto**:
`own-controls` no lo parsea nadie en el runtime. El fichero `fifa07.keys.txt` se
lee porque el runtime recibe la ruta del `.exe` y aplica
`input_profile_program()` (ver `runtime.c` ~1843). No afecta a este fallo, pero
conviene no apoyarse en esa clave.
