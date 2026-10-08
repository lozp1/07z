# Mando vs. teclado en FIFA 07 NX

> **Nota de vigencia:** documento de la etapa previa del port. La raíz de la SD es
> ahora **`sdmc:/switch/fifa07`** (aquí se ven rutas `sdmc:/switch/wine`, la raíz
> antigua). El modo final en uso es **teclado (`input-mode=2`)** + shim `DINPUT.dll`;
> la guía vigente es `docs/INSTALACION-07z.md`.

Este documento explica los **dos caminos de entrada** que soporta el runtime
Wine-NX para FIFA 07, cómo alternar entre ellos sin doble entrada y qué se gana y
se pierde con cada uno. La idea es que el usuario pueda volver a la vía de mando
(que FIFA dibuje SUS iconos de botón y se configure en *Mi FIFA 07 → Controls*)
de forma **reversible**, y volver a la de teclado si algo no cuadra.

---

## 1. La palanca: `input-mode`

El runtime tiene un único selector, `input-mode`, dentro del perfil de controles
(`input_profile.h`: `INPUT_CONTROLLER = 1`, `INPUT_KEYBOARD_MOUSE = 2`):

| `input-mode` | Nombre | Qué hace el runtime |
|---|---|---|
| `1` | Controller (mando) | **No** sintetiza teclas. Expone el mando de Switch como **Xbox 360 vía XInput**. |
| `2` | Keyboard / mouse | **Sí** sintetiza las teclas de `keys.txt` como eventos de teclado de Win32. XInput responde «desconectado». |

Y los dos caminos son **mutuamente excluyentes por diseño**, que es exactamente
lo que evita la doble entrada:

* `runtime.c → wine_nx_pointer_poll()`:
  `emulate = !keyboard && profile->mode == INPUT_KEYBOARD_MOUSE;`
  → con `input-mode=1` **no se emite ni una tecla**.
* `xinput_unix.c → nx_xinput_get_state_unix()`:
  `if (params->index || wine_nx_input_profile.mode == INPUT_KEYBOARD_MOUSE) return STATUS_SUCCESS;`
  → con `input-mode=2` el pad XInput se reporta **desconectado**.

Nunca se leen los dos a la vez. No hay que desactivar nada a mano ni pelear con
`joy.cpl` de Wine.

## 2. Dónde se escribe (y por qué importa)

`input-mode` se lee de los ficheros de teclas, **en este orden** (el último gana):

1. `sdmc:/switch/wine/keys.txt`
2. `sdmc:/switch/wine/config/keys.txt`
3. `sdmc:/switch/wine/drive_c/FIFA 07/fifa07.keys.txt`   (junto al `.exe`)
4. `sdmc:/switch/wine/drive_c/FIFA 07/fifa07.wine-nx.txt` ← **manda**

El 4.º es el bueno para alternar, por dos motivos:

* **Es el último que se aplica**, así que su `input-mode` pisa a los otros tres.
  (`input_profile_program()` lo carga con
  `launcher_program_settings_path()`, que para una ruta `sdmc:/…` resuelve al
  fichero hermano `NAME.wine-nx.txt`.)
* **El frontend no lo pisa**: el frontend sólo reescribe `dxvk-hud` en ese
  fichero (y conserva el resto de líneas tal cual); en cambio **fuerza
  `input-mode=2`** en los tres ficheros de teclas cada vez que se pulsa
  *Guardar* en la pantalla de Mandos. Si pones `input-mode=1` en
  `fifa07.keys.txt`, la próxima vez que guardes controles desde el frontend
  volvería a `2`.

> Sin `input-mode` en ningún sitio, el valor por defecto es
> `INPUT_CONTROLLER` (=1, mando).

## 3. Cómo alternar

### 3.1. Pasar a **MANDO** (lo que quiere el usuario)

En `sdmc:/switch/wine/drive_c/FIFA 07/fifa07.wine-nx.txt`, añade/cambia:

```ini
input-mode=1
```

(Se puede dejar `input-mode=2` en los `keys.txt`; el de `fifa07.wine-nx.txt`
gana igualmente.)

Hay un script en el repo que hace este cambio con copia de seguridad:

```powershell
powershell -ExecutionPolicy Bypass -File tools\cambiar-modo-controles.ps1 -Modo mando
```

### 3.2. Volver a **TECLADO**

```powershell
powershell -ExecutionPolicy Bypass -File tools\cambiar-modo-controles.ps1 -Modo teclado
```

o, a mano, `input-mode=2` (o borra la línea) en ese mismo fichero. Como los
`keys.txt` ya traen `input-mode=2`, basta con poner `2`/borrar en el `.wine-nx.txt`.

### 3.3. Comprobar en la consola

En el log de arranque del runtime (`sdmc:/switch/wine/logs/autorun_runtime.log`)
se ve `[INPUT] could not read controller settings` sólo si NINGÚN fichero se
pudo leer; con el fichero presente no aparece ese aviso. Para ver el efecto
inmediato: en modo mando el juego deja de responder a teclas y responde al pad;
en modo teclado al revés.

## 4. Qué se gana y qué se pierde

### Vía MANDO (`input-mode=1`)

**Se gana**

* FIFA 07 ve un **Xbox 360** (XInput) y muestra **sus propios iconos de botón**
  (los de Xbox) en menús y en el HUD.
* Movimiento **analógico** (no 8 direcciones digitales): el jugador se mueve
  según cuánto inclinas el stick.
* Se configura **dentro del juego**: *Mi FIFA 07 → Controls*, con sus pantallas
  de «Classic/New», y el juego guarda esa configuración.
* Desaparece de raíz el fallo del stick que cambiaba tácticas (las tácticas se
  activan con el **teclado numérico**, y en modo mando el runtime no sintetiza
  teclas, así que no hay ninguna flecha/numérico que se cuele). Ver
  `docs/CONTROLES-DIAGNOSTICO.md`.
* Los gatillos/botones digitales del pad se leen como botones de mando, sin
  depender del mapa `keys.txt`.

**Se pierde / hay que tener en cuenta**

* **No vale el mapa de `keys.txt`**: en modo mando `fifa07.keys.txt` no hace
  nada (el runtime no emite teclas). Si querías un botón en una acción concreta,
  hay que reasignarlo **dentro del juego**.
* El juego pasa a depender de su backend XInput (`data/input/XPadLib.dll` →
  `xinput9_1_0.dll`, que sí está en el prefijo). Si un mando concreto no lo
  detectara, hay que revisar *Mi FIFA 07 → Controls* o el perfil de XInput.
* La cruceta sigue siendo digital; en modo mando FIFA la trata como tal.
* La navegación de los menús de FIFA con el pad es la del juego, no la del
  frontend.

### Vía TECLADO (`input-mode=2`) — la actual

**Se gana**

* **Funciona hoy, sin depender del backend XInput del juego.** El runtime inyecta
  teclas y el **shim `DINPUT.dll`** las entrega al juego; probado en hardware.
* Mapeo total y explícito de los 15+ botones de Switch a las teclas de FIFA
  (`keys.txt`), editable desde el frontend o a mano.
* El usuario ya conoce el esquema (flechas = mover, S/D/W/A = acciones, etc.).

**Se pierde**

* El juego ve un **teclado**: muestra **atajos de teclado**, no iconos de mando.
* Movimiento **digital** (8 direcciones), no analógico.
* No se configura en *Mi FIFA 07 → Controls* como un mando: se configura
  editando `keys.txt` (o desde la pantalla de Mandos del frontend).
* Exige que el shim `DINPUT.dll` esté corregido: con el shim antiguo, cada
  flecha se publicaba además como tecla del **teclado numérico** y las tácticas
  se disparaban solas (ver el documento de diagnóstico).

### Resumen

| | Mando (`input-mode=1`) | Teclado (`input-mode=2`) |
|---|---|---|
| Iconos de botón del juego | **Sí** | No |
| Configurar en *Mi FIFA 07 → Controls* | **Sí** | No (se edita `keys.txt`) |
| Movimiento | **Analógico** | Digital (8 dir.) |
| Depende del backend XInput del juego | **Sí** | No |
| `keys.txt` sirve para algo | No | **Sí** |
| Riesgo de «doble entrada» | No (XInput único) | No (XInput desconectado) |

## 5. Por qué el runtime separa los dos caminos (historia)

FIFA 07 en PC tiene un problema **conocido y documentado por la propia escena**:
lee la entrada dos veces porque cree que hay **dos mandos en el mismo puerto**
(lo dice el `FIFA_07_Readme.txt` que viene con la copia del usuario: «*the game
will read your input twice, because the game thinks that two controllers are
connected on the same port*»). El remedio que propone ese README es entrar en el
panel de mandos de Wine y **deshabilitar** uno de los dos.

Aquí eso no hace falta: el diseño del runtime **nunca** presenta las dos fuentes
a la vez (mando XOR teclado, sección 1). Y cuando se va por **mando**, sólo hay
**un** dispositivo (XInput); nuestro `DINPUT.dll` no anuncia ningún gamepad
DirectInput (sólo teclado y ratón), así que FIFA no ve el «segundo mando» que le
da el problema.

## 6. Qué había antes en el proyecto (para no confundirse)

* No existe ningún directorio `dls/` en el proyecto ni en la SD. Lo que hay con
  «dls» son **cadenas `.dls` de DirectMusic** (`src/shims/dmusic_fifa07.c`), que
  no tienen nada que ver con el mando.
* La vía de mando **no** es un fichero aparte: es el propio runtime exponiendo
  XInput cuando `input-mode=1`. Los shims de `src/shims/` son todos de
  **compatibilidad** (DirectInput de teclado/ratón, SensApi, MSIMG32, DirectMusic,
  DirectPlay NAT), no un backend de gamepad.
* El runtime sí detecta y mapea el mando (dos Joy-Con, hold horizontal, giro del
  stick de una mitad suelta): `mandos-joycon-separados.md` describe esa parte.
  Ese mapeo es el que XInput usa en modo mando.

## 7. Requisitos del mando (runtime)

El soporte de mando del runtime está puesto y documentado en
`docs/mandos-joycon-separados.md`. En resumen: un mando completo o el par junto
funcionan hoy; para **dos Joy-Con separados** el runtime necesita las líneas de
configuración adicionales descritas en ese documento (afecta a cómo se leen las
dos mitades, no a este interruptor).
