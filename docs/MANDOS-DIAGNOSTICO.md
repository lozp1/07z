# MANDOS — diagnóstico y arreglo (FIFA 07 NX)

Sesión: 2026-10-07 (noche). Objetivo: que **A y B funcionen en menús Y en partido**
(el usuario reportaba «A y B no me funcionan» y «A me pausa el juego y no puedo pasar»).

---

## 0. TL;DR

1. La causa de que **A** no confirmara en menús: estaba mapeado a **ESPACIO (0x20)**,
   y FIFA 07 **no usa ESPACIO** ni en menús ni en partido (su confirmar es **ENTER**).
   Por eso A «no hacía nada» / el juego se quedaba bloqueado o pausado.
2. **B** estaba a **ESCAPE (0x1b)**: correcto como «atrás» en menús, pero en partido
   B debe ser el **tiro/entrada (D)**, no Escape.
3. Se ha corregido el mapa usando **acordes** (dos teclas por botón, que el runtime
   ya soporta): **A = ENTER + S** y **B = ESCAPE + D**. Así el mismo botón hace la
   función de menú **y** la de partido.
4. Se confirma **`input-mode=2`** (Keyboard) en los `fifa07.wine-nx.txt` y se copian
   los 3 `keys.txt`.

---

## 1. Teclas REALES de FIFA 07 en PC (de fábrica)

Fuentes: GameFAQs (guías PC de FIFA 07, por RummanDoesRule y futballfantic7),
gamepressure.com (FIFA 07 Dribbling/Controls) y el propio `FIFA_07_Readme.txt`.

**MENÚS** (navegación con teclado):
| Acción | Tecla |
|---|---|
| Mover por el menú | **Flechas** (arriba/abajo/izq/dcha) |
| Confirmar / aceptar | **ENTER** (Return) |
| Atrás / cancelar | **ESCAPE** |
| Pausa dentro del partido | **ESCAPE** (o botón *Start* del mando) |

(Fuente: gamefaqs: *«After you select the language and press ENTER, the main screen
comes up»*; *«To bring up the in-game pause menus, you can press the Start button…
or press ESC»*.)

**PARTIDO — esquema «Classic» (el de por defecto):**
| Acción | Tecla |
|---|---|
| Pase / cambiar de jugador | **S** |
| Tiro / entrada conservadora / despeje | **D** |
| Pase filtrado (through ball) / salida del portero | **W** |
| Centro / pase largo / entrada deslizante | **A** |
| Sprint | **E** |
| Jugada del compañero (trigger run) / modificador de tácticas | **Q** |
| Control de ritmo (pace / walk) | **C** |
| Cancelar / amago (dummy move) | **Z** |
| Regate / skill move | **Shift** |
| Tácticas rápidas | **Teclado numérico** 2/4/6/8 (+ Q en defensa) |

(Fuente: gamepressure *«Classic: [A] cross/long pass/sliding tackle; [S] switch
player/pass; [D] shot/conservative tackle; [W] through ball/goalkeeper charge;
[E] sprint»* y GameFAQs *«Pass/Switch = S; Through Ball/GK = W; Cross/Long
Pass/Sliding Tackle = A; Shoot/Conservative Tackle = D; Sprint = E; … Pace
Control = C; Cancel/Dummy = Z»*. El juego permite reasignar en *Mi FIFA 07 →
Controls*, pero esto es lo de fábrica.)

**Dato clave:** en FIFA 07 **ESPACIO no tiene función** (ni menú ni partido).

---

## 2. El conflicto de fondo: A = confirmar (menú) vs A = pase (partido)

Un mismo botón físico debe **confirmar** en menús (tecla **ENTER**) y **pasar** en
partido (tecla **S**). El runtime Wine-NX **no cambia de contexto**: manda teclas, no
sabe en qué pantalla está FIFA. Dos soluciones:

* **(S1) Elegir una sola función por botón** — p. ej. A = Enter (sólo menús) y dejar
  el pase en ZL/S. Simple, pero A **no** pasaría en partido.
* **(S2) Acorde (dos teclas a la vez)** — A = `ENTER+S`, B = `ESCAPE+D`. El runtime
  (`input_map_keys`, `input_profile.c:322`) publica **todas** las teclas de un binding
  al pulsar la fuente; en menú FIFA lee ENTER (y S no hace nada) y en partido lee S
  (y ENTER no hace nada). **Es la opción elegida.**

**¿Por qué teclado y no definir el mando como mando (modo 1, XInput)?** Ver §4: en
este runtime falta la DLL `xinput9_1_0.dll` en el payload y el backend XInput de FIFA
no arranca; además la vía teclado **ya funciona en hardware**. Se elige lo que no
rompe lo que funciona.

---

## 3. Mapa aplicado (2026-10-07) — contenido de `keys.txt`

```
UP/DOWN/LEFT/RIGHT = 0x26/0x28/0x25/0x27    (flechas; menús y partido)
LUP/LDOWN/LLEFT/LRIGHT = 0x26/0x28/0x25/0x27 (stick izq = flechas)
A     = 0x0d+0x53   -> ENTER (confirmar menú) + S (pase)
B     = 0x1b+0x44   -> ESCAPE (atrás menú)   + D (tiro/entrada)
X     = 0x57        -> W  (pase filtrado / salida del portero)
Y     = 0x41        -> A  (centro / pase largo)
ZR    = 0x44        -> D  (tiro)     [redundante]
ZL    = 0x53        -> S  (pase)     [redundante]
R     = 0x45        -> E  (sprint)
L     = 0x10        -> Shift (regate / skill move)
STICKL= 0x5a        -> Z  (amago / dummy)
STICKR= 0x43        -> C  (control de ritmo)
PLUS  = 0x1b        -> ESCAPE (pausa / atrás)
MINUS = 0x0d        -> ENTER (confirmar)
RUP=0x10 RDOWN=0x5a RLEFT=0x00 RRIGHT=0x00
input-mode=2
```

Equivalencia pedida por el usuario: A = pase/confirmar, B = tiro/atrás, X = pase
filtrado/salida portero, Y = centro/pase largo, R = sprint, L = regate, clic stick izq
= amago, clic stick der = control de ritmo. ✔

**Riesgo a vigilar:** si al **tirar (B) en partido** se abriera el **menú de pausa**,
es que en este build ESCAPE sí pausa durante el partido. Entonces quitar Escape de B
(una línea):
```
B=0x44          # sólo tiro/entrada; para "atrás" en menús se usa PLUS (Escape)
```
Evidencia de que hoy **no** pasa: el mapa anterior ya tenía `B=0x1b`=Escape y el
usuario no reportó que B pausara; el que pausaba era A=ESPACIO. Por eso ESPACIO se
ha eliminado.

---

## 4. ¿Es viable el modo 1 (Controller + XInput)? — evaluación

El **modo 1** es la solución «nativa»: FIFA vería un mando Xbox 360 y resolvería menús
**y** partido con su propia configuración (desaparece el conflicto de §2).

Estado real:
* El runtime **sí** implementa XInput: `autorun-src/horizon-wine/source/xinput_unix.c`
  (`nx_xinput_get_state_unix`) mapea el mando de Switch como `XINPUT_GAMEPAD`. En modo
  mando también expone **movimiento analógico** e **iconos de botón** de Xbox.
* FIFA 07 PC usa XInput **sólo** a través de `data/input/XPadLib.dll` →
  `xinput9_1_0.dll`.
* **Problema (medido en el log):** `logs/fifa07.log` registra
  `[FS] …/lib/wine/i386-windows/xinput9_1_0.dll could not be opened: status c000000f`
  (y lo mismo en `lib/wine/`). El **payload del runtime no trae la `xinput9_1_0.dll`**
  que Wine necesita para resolver esa carga.
* En el prefijo **sí** hay copias (`drive_c/windows/system32/xinput9_1_0.dll` 640 KB y
  `syswow64/xinput9_1_0.dll` 61 KB; la de Microsoft está en
  `C:\Projects\ports\dx9\files\`). Pero la DLL de Microsoft habla con el **driver
  XInput del sistema**, no con el shim XInput del runtime, así que **no está
  garantizado** que detecte el mando.
* El código fuente del runtime **sí** tiene `autorun-src/dlls/xinput9_1_0/` (el builtin
  de Wine, que comparte implementación con `xinput1_3.dll`).

**Conclusión:** el modo 1 es viable **si el runtime incorpora su propia
`xinput9_1_0.dll` builtin** (recompilar el `.nro` añadiendo `dlls/xinput9_1_0` al
payload, o aportarla junto al `.exe`). Hoy **falta esa DLL**; con la de Microsoft no
está garantizado. Como exige **tocar/recompilar el runtime que ya funciona**, **no se
aplica**: se mantiene el modo 2 (teclado) corregido. Queda documentado como vía futura.

---

## 5. Cambios aplicados en la SD (D:), con copia de seguridad

| Fichero | Antes | Ahora | Backup |
|---|---|---|---|
| `drive_c/FIFA 07/fifa07.keys.txt` | `A=0x20  B=0x1b` | `A=0x0d+0x53  B=0x1b+0x44` (+ comentarios) | `…fifa07.keys.txt.bak-antes-mandos-20261007` |
| `config/keys.txt` | igual | idéntico (md5 `8a7d87fa…`) | `config/keys.txt.bak-antes-mandos-20261007` |
| `keys.txt` (raíz) | igual | idéntico | `keys.txt.bak-antes-mandos-20261007` |
| `drive_c/FIFA 07/fifa07.wine-nx.txt` | `input-mode=2` | sin cambios (ya correcto) | — |
| `config/fifa07.wine-nx.txt` | `input-mode=2` | sin cambios (ya correcto) | — |

No se ha tocado: `fifa07.exe` (sigue md5 `315bfc2f…`), el puente gráfico
(`d3d8.dll`/`dxwrapper.dll`/`d3d9.dll`), `DINPUT.dll` (shim corregido, md5
`53bc6ceb…`), el audio/`config.dat`, las partidas ni el overclock.

> `input_binding_parse` (`input_profile.c:85`) acepta `0xNN+0xNN`: verificado que
> `0x0d+0x53` → `{13, 83}` y `0x1b+0x44` → `{27, 68}`.
> **Ojo con el frontend:** la pantalla «Mandos» sólo entiende una tecla por botón; si
> se pulsa *Guardar* ahí, reescribirá A/B sin el acorde. Editar el fichero a mano.

---

## 6. Instrucción de prueba (usuario) — botón por botón

1. Enciende la consola con la SD puesta, entra en el **Homebrew Menu** y lanza
   **FIFA 07** desde el icono **07z**. (No hay que recompilar nada.)

2. **En cualquier menú de FIFA:**
   * **Cruceta o stick izq.** → mueve la selección. *(flechas)*
   * **A** → **confirma / avanza**. *(ENTER)* ← **esto es lo que fallaba**
   * **B** → **atrás**. *(ESCAPE)*
   * Alternativa: **MINUS = confirmar**, **PLUS = atrás/pausa**.

3. **Dentro de un partido:**
   * Mover jugador: cruceta / stick izq.
   * **A** → **pase**. *(S)*
   * **B** → **tiro / entrada**. *(D)*
   * **X** → pase filtrado / salida del portero. *(W)*
   * **Y** → centro / pase largo. *(A)*
   * **R** → sprint. *(E)*
   * **L** → regate / skill move. *(Shift)*
   * **clic stick izq.** → amago (dummy). *(Z)*
   * **clic stick der.** → control de ritmo. *(C)*
   * **PLUS** → pausa.

4. Si A confirma en menú y pasa en partido, y B va atrás en menú y tira en partido:
   **objetivo conseguido**.

5. Si **B, al tirar en partido, abriera la pausa**: aplicar el ajuste de §3
   (`B=0x44`). Si A/B siguieran muertos: revisar §7.

### Cómo revertir

```bash
# volver al mapa anterior (D: = SD)
cd /d/switch/fifa07
cp -p "drive_c/FIFA 07/fifa07.keys.txt.bak-antes-mandos-20261007" "drive_c/FIFA 07/fifa07.keys.txt"
cp -p "config/keys.txt.bak-antes-mandos-20261007"                "config/keys.txt"
cp -p "keys.txt.bak-antes-mandos-20261007"                       "keys.txt"
```

---

## 7. Si aún no funciona

* Confirmar que `input-mode=2` está en `drive_c/FIFA 07/fifa07.wine-nx.txt` (es el
  fichero que **manda**). Si está en `1`, el runtime **no emite teclas**.
* Confirmar que el shim `DINPUT.dll` (md5 `53bc6ceb…`) está en la carpeta del juego
  (es lo que entrega las teclas a DirectInput; con el de Wine sin shim, FIFA no ve
  ninguna tecla).
* Hipótesis shim: probar el build antiguo `_shims-desactivados/DINPUT.dll` como control
  (tendrá el bug de tácticas con el stick).
* Ver entrada en vivo: `config/settings.json` → `"verbose-log": true`.

---

## 8. Histórico de la sesión anterior (input-mode / shims)

`input-mode` **NO** vale 0/1: es **1 = Controller**, **2 = Keyboard/mouse**
(`input_profile.h:12`; un `0` cae al default = 1). Solo el modo **2** emite teclas
(`runtime.c:982  emulate = !keyboard && profile->mode == INPUT_KEYBOARD_MOUSE;`) y en
modo 2 XInput se reporta desconectado (`xinput_unix.c:43`). Con `input-mode=1` el
runtime no sintetiza ni una tecla → el mapa de `keys.txt` no se aplica. `own-controls`
es una clave **inerte** (nadie la parsea). El shim `DINPUT.dll` corregido
(`53bc6ceb…`, sin el bug flechas→NumPad→tácticas) sigue activo y correcto.
