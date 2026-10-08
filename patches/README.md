# Parches del runtime — cumplimiento de licencia (LGPL-2.1-or-later)

El **runtime** que la 07z usa (`wine-nx-runtime.nro`) **no es obra original de este proyecto**:
deriva de **Wine** y de **Wine-NX / Autorun**, ambos distribuidos bajo
**GNU LGPL-2.1-or-later**. Al distribuir el binario del runtime, la LGPL obliga a
**ofrecer los cambios** realizados sobre el código original. Eso es exactamente lo que
contiene este directorio.

## Código fuente base (upstream)

| Componente | Repositorio | Commit de referencia |
|---|---|---|
| Wine-NX (Autorun) | <https://github.com/danfromtico/wine-nx.git> | `1bc4e45163f0d2328cdfd35c7f471dd9821bb879` (release *test-build-2*) |
| Autorun (proyecto actual) | <https://github.com/autorunhq/autorun> | — |
| Box64 | <https://github.com/ptitSeb/box64.git> | `dae0917c47b4edd8956f314210417a20fd225c4b` |

Los parches de abajo se aplican **sobre ese árbol de fuentes**, en
`horizon-wine/source/`. Las rutas de los `diff` conservan el prefijo `a/… b/…` del
árbol original.

## Parches incluidos

| Fichero | Qué cambia | Por qué |
|---|---|---|
| `input_profile.h.diff` | Añade a `struct input_profile` los campos `joycon_hold` y `joycon_rotate`, y declara el perfil del jugador 2. | Habilita dos mapas de teclas y el *roll* de stick de un Joy-Con suelto. |
| `input_profile.c.diff` | Lee los ajustes `joycon-hold` / `joycon-rotate` desde el fichero de teclas y añade `input_profile_defaults_player2()` + `input_profile_program_player2()`. | El jugador 2 tiene su propio mapa, cargado de `keys2.txt` / `config/keys2.txt` / `<programa>.player2.keys.txt`. |
| `runtime.c.diff` | Separa la lectura de mandos en **jugador 1** (Handheld + `No1`) y **jugador 2** (`No2`), orienta el stick de un Joy-Con suelto y fusiona las dos salidas antes de entregarlas al juego. | **Lectura separada de los dos mandos** (experimental, **sin verificar en consola**) sin que un mando en reposo enmascare al otro; la fusión en un solo jugador sigue siendo el comportamiento por defecto. |
| `low-window-39bit.patch` | Ampliación del *forwarder* de 39 bits / *low window* (base Atmosphere 1.11.2, `5388824be146a89619e8d641acd64599cf1c5f62`). Añade `HasAutorunLowWindow()`, que concede el hueco bajo a **un solo program id**, `0548EABB35576000` (el forwarder "main" del runtime). | Deja el hueco de direcciones bajas (`0x00200000`) que `fifa07.exe` necesita al estar con las reubicaciones eliminadas (`IMAGE_FILE_RELOCS_STRIPPED=1`). El NSP 07z lleva **ese mismo title id** (`tools/build-fifa07-forwarder.py`), o el parche no lo reconocería; ver `docs/FORWARDER-39BIT-FIX.md`. |

## Cómo reproducirlo

1. Clona el árbol base en el commit indicado.
2. Aplica los `*.diff` desde `horizon-wine/` y, si procede, el `low-window-39bit.patch`
   según su propio `README` (requiere Atmosphere 1.11.2 y devkitA64/libnx).
3. Recompila con el toolchain de devkitPro/devkitA64.

## Nota

- Si necesitas el **código fuente correspondiente completo** (no solo los parches), el
  propio upstream (Wine-NX/Autorun) es público en los repositorios de la tabla de arriba;
  los parches de este directorio son las únicas modificaciones aplicadas por 07z.
- El **juego FIFA 07** no forma parte de la licencia ni de este repositorio.
