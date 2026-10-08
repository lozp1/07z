# Instalación de 07z — FIFA 07 en Nintendo Switch

> Proyecto **no oficial**, sin relación con EA. **No incluye el juego**: tenés que
> aportar **tu propia copia** de FIFA 07 de PC.

## Qué necesitás

- Una Switch con **Atmosphere y sigpatches** (da igual `sysMMC` o `emuMMC`).
- **Tu copia de FIFA 07 de PC**.
- Una **SD** con espacio: el port ocupa ~60 MB y tu juego lo que ocupe en tu PC.
- Un **instalador de NSP**: DBI, Goldleaf, Tinfoil o Awoo.
- Los ficheros de 07z: la **carpeta `fifa07`** y **`07z-forwarder.nsp`**
  (pestaña **Releases** del repositorio).

## Instalación

1. Copiá la carpeta **`fifa07`** a `sdmc:/switch/fifa07/`.
2. Copiá **tu juego** dentro de `sdmc:/switch/fifa07/drive_c/FIFA 07/`, de modo que
   exista esta ruta:

   ```
   sdmc:/switch/fifa07/drive_c/FIFA 07/fifa07.exe
   ```

3. Instalá **`07z-forwarder.nsp`** con DBI, Goldleaf, Tinfoil o Awoo.
4. En el **menú de inicio** aparece el icono **07z**. Pulsalo y después **Jugar**.

**No hay que instalar kips, ni crear particiones, ni overclock, ni pasar por ningún**
**asistente de configuración.**

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
| Sale «Abre desde el menú de inicio» | Lo lanzaste desde el Homebrew Menu: usá el icono del HOME |
| El juego no arranca | Comprobá que copiaste **todos** los datos del juego, no solo el `.exe` |
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
