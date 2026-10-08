<h1 align="center">07z — FIFA 07 en Nintendo Switch</h1>

<p align="center">
  <b>Se instala como un juego. Se arranca desde el icono del HOME. Wine no se ve.</b><br/>
  Proyecto no oficial, sin relación con EA. No incluye el juego.
</p>

**07z** es un frontend homebrew y el envoltorio que lo acompaña para **jugar a tu
propia copia de FIFA 07 de PC en una Nintendo Switch con custom firmware**, y
hacerlo **como si fuera un juego nativo de la consola**: aparece un **icono «07z»
en el menú de inicio**, lo pulsas, sale **una interfaz hecha a medida** y al darle a
**Jugar** entra el partido. **Wine no se muestra nunca**: ni catálogos, ni menús
intermedios, ni ventanas. Al salir del partido vuelves directo al HOME.

| | |
|---|---|
| **Página del proyecto** | https://lozp1.github.io/07z/ |
| **Guía paso a paso** | [`docs/INSTALACION-07z.md`](docs/INSTALACION-07z.md) |
| **Descargas (NSP + port)** | [Releases](https://github.com/lozp1/07z/releases) |

---

## Aviso importante

> **07z es un proyecto NO oficial y SIN relación alguna con EA (Electronic Arts).**
>
> Este repositorio **NO incluye ni distribuye el juego FIFA 07** (ni `fifa07.exe`,
> ni sus datos, ni ningún fichero con copyright de EA). **El juego es propiedad de
> cada usuario**: tú aportas **tu propia copia** de FIFA 07 de PC.
>
> Aquí solo se distribuye **el frontend 07z**, el **NSP forwarder** que lo lanza
> desde el menú de inicio, el **runtime** (software libre de terceros, ver
> *Créditos*) y las **herramientas y documentación** del port. Nada de lo que hay
> en este repositorio contiene material de EA.
>
> «FIFA» se usa únicamente de forma **descriptiva**, para indicar con qué juego de
> PC es compatible.

---

## Requisitos

| # | Necesitas | Detalle |
|---|---|---|
| 1 | **Nintendo Switch con custom firmware** | Atmosphere **con sigpatches** (vale `sysMMC` o `emuMMC`) |
| 2 | **Tu propia copia de FIFA 07 de PC** | `fifa07.exe` + sus datos. **No se incluye** |
| 3 | **Tarjeta SD con espacio** | ~60 MB del port **+** lo que ocupe tu copia del juego (2-4 GB) |
| 4 | **Un instalador de NSP** en la consola | DBI, Goldleaf, Tinfoil, Awoo Installer… |

**Lo que NO hace falta**: ni particiones nuevas, ni **kips**, ni overclock, ni pasar
por ningún asistente de setup. Basta con tu Atmosphere + sigpatches de siempre.

---

## Instalación

1. **Copia el port**: deja la carpeta `fifa07` en `sdmc:/switch/fifa07/`.
   Deben quedar, entre otros, `wine-nx-runtime.nro` y `07z.nro` en esa ruta.
2. **Pon tu juego**: copia tu FIFA 07 (PC) dentro de
   `sdmc:/switch/fifa07/drive_c/FIFA 07/`, de forma que exista
   `sdmc:/switch/fifa07/drive_c/FIFA 07/fifa07.exe`.
3. **Instala el NSP** `07z-forwarder.nsp` con DBI / Goldleaf / Tinfoil / Awoo.
4. En el **HOME** aparece el icono **07z**. Púlsalo y luego **Jugar**.
5. **Una sola vez**, dentro del juego: **Mi FIFA 07 → Ajustes → Pantalla → 1280x720**.

> **Regla de oro**: para jugar, lanza 07z **desde el icono del HOME (el NSP)**.
> Desde el **Homebrew Menu** no es posible: ahí se lanza como *applet* de 64 bits y
> `fifa07.exe` no puede mapearse en su base fija («address space unavailable»).

---

## Pantalla: elige 1280x720 (una vez)

El runtime **no estira** la imagen: la escala con `min()` y la centra, así que con un
aspecto que no sea 16:9 aparecen **barras negras**. FIFA 07 tiene **un solo modo 16:9
nativo: `1280x720`**, y se elige **una vez** en el propio juego:

> **Mi FIFA 07 → Ajustes → Pantalla → 1280x720**

**No** elijas `1280x1024` (es 5:4 y deja barras a los lados). El juego lo guarda solo
en su perfil; no hay que editar nada a mano.

---

## Controles

Los controles vienen **preconfigurados** y se editan desde la pantalla
**Configuración** de 07z.

| Botón Switch | En menús | En partido |
|---|---|---|
| **A** | Confirmar | Pase |
| **B** | — (usa **PLUS** para atrás) | Tiro / entrada |
| **X** | — | Pase filtrado / salida del portero |
| **Y** | — | Centro / pase largo |
| **R** | — | Sprint |
| **L** | — | Regate / skill move |
| **ZR** | Avanzar en las pantallas que lo pidan | — |
| **ZL** | — | Pase (igual que **A**) |
| **PLUS** | Atrás | Pausa |
| **MINUS** | Confirmar | — |
| **Cruceta / Stick izq.** | Navegar | Mover jugador |
| **Clic stick izq.** | — | Amago (dummy) |
| **Clic stick der.** | — | Control de ritmo |

> Las tácticas (**Q**) y el **teclado numérico** no se mapean a propósito: el teclado
> numérico comparte códigos con las flechas y disparaba las tácticas solas.

---

## Rendimiento

- **55-60 FPS** en partido con gráficos y resolución en **ALTO**.
- Los **bajones de los menús 3D** (selección de equipos, plantillas) no eran de CPU ni
  de GPU: eran **compilación de shaders** y **I/O de la tarjeta**. El **segundo arranque**
  de un menú ya va fluido (la caché de shaders se guarda en la SD).
- El port ya trae los ajustes puestos (`sync`, `frame-limit`, `dxvk.conf`): no hay que
  tocar nada. El **overclock es opcional** (p. ej. con UltraHand).

---

## Estructura del repositorio

| Carpeta | Qué es |
|---|---|
| [`frontend-nx/`](frontend-nx/) | El frontend **07z** (app `07z.nro`, framework Borealis) |
| [`src/shims/`](src/shims/) | Shims de compatibilidad para FIFA 07 (DINPUT, DirectMusic, DPNHPAST, SensApi, MSIMG32) |
| [`docs/`](docs/) | Guía de instalación, distribución, diagnóstico de mandos, optimización, resolución |
| [`patches/`](patches/) | Parches aplicados al runtime Wine-NX |
| [`tools/`](tools/) | Scripts del forwarder, verificación, medición de FPS y empaquetado |

---

## Créditos y licencia

- **07z** (frontend, port y documentación): **Franco López (`lozp1`)** — [MIT](LICENSE).
- **Runtime**: **Wine** y **[Wine-NX / Autorun](https://github.com/autorunhq/autorun)** —
  **LGPL-2.1-or-later**. Los parches aplicados están en [`patches/`](patches/).
- **[Borealis](https://github.com/XITRIX/borealis)** (interfaz), **[libnx /
  devkitPro](https://devkitpro.org/)** (toolchain), **[FEX-Emu](https://github.com/FEX-Emu/FEX)**
  (traducción x86→ARM).
- Este repositorio es un **fork de [FEXTendo / PES13-NX](https://github.com/Ibnuard/pes13_nx)**
  (AndroSwitch Project / Ibnuard). El README original del wrapper se conserva en
  [`README-UPSTREAM.md`](README-UPSTREAM.md).

**FIFA 07 y sus marcas son propiedad de EA (Electronic Arts).** Este proyecto es
**no oficial**: no está afiliado, patrocinado ni respaldado por EA. «FIFA» se usa
únicamente de forma descriptiva.

Contacto: [francopaolo_lg@outlook.com](mailto:francopaolo_lg@outlook.com)
