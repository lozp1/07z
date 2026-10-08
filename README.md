<img align="right" src="https://visitor-badge.laobi.icu/badge?page_id=lozp1.07z" />

<h1 align="center">
    <img src="https://readme-typing-svg.herokuapp.com/?font=Righteous&size=40&center=true&vCenter=true&width=720&height=80&duration=4000&color=1D4ED8&lines=07z;FIFA+07+en+tu+Nintendo+Switch;Proyecto+NO+oficial" />
</h1>

<h3 align="center">⚽ 07z — juega a tu <b>FIFA 07</b> de PC en Nintendo Switch, como un juego más 🎮</h3>

<div align="center">

![Platform](https://img.shields.io/badge/Platform-Nintendo%20Switch-E60012?style=for-the-badge&logo=nintendoswitch&logoColor=white)
![Version](https://img.shields.io/badge/Versi%C3%B3n-v1.0.0-1D4ED8?style=for-the-badge)
![Runtime](https://img.shields.io/badge/Runtime-Wine--NX-A072D2?style=for-the-badge)
![UI](https://img.shields.io/badge/UI-Borealis-3B82F6?style=for-the-badge)
![License](https://img.shields.io/badge/Licencia-MIT-10E761?style=for-the-badge)

</div>

<hr/>

## 🌟 ¿Qué es 07z?

**07z** es un **frontend homebrew** —y el envoltorio que lo acompaña— para **jugar a tu propia copia de FIFA 07 de PC en una Nintendo Switch con custom firmware**, y hacerlo **como si fuera un juego nativo de la consola**.

La idea es sencilla: que **no notes que por debajo hay una capa de compatibilidad**. Enciendes la consola, ves un **icono propio** («07z») en el menú de inicio, lo pulsas, aparece **una interfaz hecha a medida** y, al darle a **Jugar**, el partido arranca directamente. **Wine no se muestra nunca**: ni catálogos, ni menús intermedios, ni configuraciones raras a la vista. Al salir del partido vuelves directo al **HOME**.

- 🔵 **Se siente nativo.** Icono en el HOME, menú propio y arranque directo del juego.
- 🎛️ **Todo integrado.** Interfaz con estética Horizon y ajustes desde la propia consola.
- 🎮 **Pensado para el mando.** Los controles vienen preconfigurados para jugar sentado en el sofá.
- 🧰 **Un proyecto personal.** 07z lo hace **una sola persona, por afición**: es un port **no oficial**, experimental y en mejora constante.

> 07z es un **proyecto personal y experimental**. La compatibilidad puede variar según la versión de firmware y la copia del juego de cada usuario.

<hr/>

## ⚠️ Aviso importante — léelo antes de nada

> **07z es un proyecto NO oficial y SIN relación alguna con EA (Electronic Arts).**
>
> Este paquete **NO incluye ni distribuye el juego FIFA 07** (ni `fifa07.exe`, ni sus datos, ni ningún fichero con copyright de EA). **El juego es propiedad de cada usuario**: tú debes aportar **tu propia copia** de FIFA 07 de PC.
>
> Aquí solo se distribuye **el frontend/homebrew 07z**, el **NSP forwarder** que lo lanza desde el menú de inicio y el **runtime** (software libre de terceros, ver *Créditos* y *Licencia*). Nada de lo que hay en este repositorio contiene material de EA.
>
> «FIFA» se usa únicamente de forma **descriptiva**, para indicar con qué juego de PC es compatible.

<hr/>

## ✨ Características

Esto es lo que hace 07z:

- 🏠 **Icono propio en el HOME.** El juego aparece en el menú de inicio de la consola como un título más, con el nombre **07z**. No hay que entrar al Homebrew Menu para cada partida.
- 🎨 **Interfaz propia.** Menú hecho a medida (estética tipo Horizon) con navegación en **carrusel**.
- 🕹️ **Wine invisible.** El frontend hace un *hand-off* transparente al runtime, pasándole tu `fifa07.exe`. Nunca ves una ventana ni un menú de Wine: solo pulsas **Jugar** y entra el partido.
- ⌨️ **Ajustes de teclas.** Los mapas de teclas se pueden editar desde la propia pantalla **Configuración** de 07z, sin tocar archivos a mano.
- ⚡ **Arranque directo y fluido.** Una vez configurado, el juego se lanza de forma directa; **el tiempo de carga depende de tu tarjeta SD y de tu firmware** (no prometemos cifras: tu resultado puede variar).
- ♻️ **Limpio de desinstalar.** 07z no escribe nada fuera de su carpeta en la SD.

<hr/>

## 🧪 En desarrollo / experimental

Hay cosas que estamos probando y que **todavía no podemos prometer**. Las dejamos aquí, con transparencia:

- 🎮 **Un jugador.** Es el modo por defecto y el único verificado: un mando completo (o la consola en modo portátil). El **segundo jugador no forma parte de este paquete** y no se anuncia como función disponible.
- 🧩 **Compatibilidad y rendimiento.** Pueden variar según el firmware y la copia del juego de cada usuario.

> Si encuentras fallos, o simplemente quieres contar que algo funciona (o no), escríbeme: [francopaolo_lg@outlook.com](mailto:francopaolo_lg@outlook.com).

<hr/>

## ✅ Requisitos

| # | Necesitas | Detalle |
|---|-----------|---------|
| 1 | **Nintendo Switch** con **custom firmware** | Atmosphere **1.11.2 OFICIAL** (revisión `5388824…`) con sigpatches — vale `sysMMC` o `emuMMC`. **El parche de ventana baja es un kernel: va por versión exacta de Atmosphere Y de firmware** (ver nota de abajo) |
| 2 | **Tu propia copia de FIFA 07 de PC** | `fifa07.exe` + sus datos. **No se incluye** |
| 3 | **Tarjeta SD** con espacio | ~60 MB del port **+** lo que ocupe tu copia del juego (2-4 GB) |
| 4 | **Un instalador de NSP** en la consola | DBI, Goldleaf, Tinfoil, Awoo Installer… |
| 5 | **`prod.keys`** (solo para instalar NSP) | El que ya uses habitualmente en tu consola |
| 6 | Los ficheros de **07z** | La **carpeta `fifa07`** (runtime + frontend `07z.nro`) desde **Releases**, y el **NSP** en [`install/`](install/) |

> ⚙️ **Lo único que SÍ hay que añadir**: el **parche de «ventana baja»** de Autorun
> (`atmosphere/mesosphere.bin` + `atmosphere/kips/autorun-loader.kip`) — **sin él el juego no
> arranca**: pulsás Jugar y te devuelve al menú. Es un **kernel**, así que va por **versión
> exacta**: este es para **Atmosphere 1.11.2 (revisión `5388824…`)**. Si tu consola está en
> otra versión (AMS distinto, firmware más nuevo) puede **no encajar y quedarse en pantalla
> negra** al añadirlo — se quitan los dos ficheros y arranca normal. Cómo se instala:
> [`docs/PARCHE-VENTANA-BAJA.md`](docs/PARCHE-VENTANA-BAJA.md).
>
> ✅ **Lo que NO hace falta**: ni particiones nuevas, ni overclock, ni pasar por ningún
> asistente de setup.
> La carpeta `fifa07` ya trae un `config/settings.json` con
> `run-the-chosen-program=true` y `reopen-the-launcher-on-exit=false`, y la
> biblioteca y el objetivo ya fijados (`launcher.txt` / `target.txt`).

> Para **jugar** es imprescindible lanzar 07z **desde el icono del menú de inicio** (el NSP).
> Arrancarlo desde el *Homebrew Menu* **no** permite jugar (ver la guía de instalación).

<hr/>

## 📥 Instalación (resumen)

Lo que descargas es **una carpeta `switch/` (con `fifa07/` dentro) y un `.nsp`**.
Nada más: **no necesitas —ni debes copiar— `bootloader/` ni `emuMMC/`**, que son
cosas de la consola, no de 07z.

1. **Descarga** de la pestaña **Releases** la carpeta `fifa07` y déjala tal cual en
   `sdmc:/switch/fifa07/`. Dentro deben quedar, entre otros:
   - `wine-nx-runtime.nro` → `sdmc:/switch/fifa07/wine-nx-runtime.nro`
   - `07z.nro` → `sdmc:/switch/fifa07/07z.nro`
2. **Pon tu juego**: copia tu FIFA 07 dentro de `sdmc:/switch/fifa07/drive_c/FIFA 07/`, de modo que exista `sdmc:/switch/fifa07/drive_c/FIFA 07/fifa07.exe`.
3. **Copia** el NSP de [`install/07z-forwarder.nsp`](https://github.com/lozp1/07z/releases) a la SD e **instálalo** con tu instalador habitual (DBI / Goldleaf / Tinfoil / Awoo).
4. En el **HOME** aparecerá el icono **07z**. Púlsalo y luego pulsa **Jugar**. 🎉
5. **Una vez**: en el juego entra en **Mi FIFA 07 → Ajustes → Pantalla** y elige **1280x720** (ver [Pantalla](#️-pantalla-elige-1280x720-una-vez)).

📖 La guía **paso a paso, con todos los detalles**, está en [`docs/INSTALACION-07z.md`](docs/INSTALACION-07z.md) y en [`install/LEEME.txt`](install/LEEME.txt).

<hr/>

## 🗂️ Estructura que queda en la SD

```
sdmc:/switch/fifa07/
├── wine-nx-runtime.nro        # runtime (descarga desde Releases)
├── 07z.nro                    # EL FRONTEND 07z (descarga desde Releases)
├── config/                    # ajustes (se crean solos)
├── drive_c/
│   ├── FIFA 07/               # <-- AQUÍ PONES TU PROPIA COPIA DEL JUEGO
│   │   └── fifa07.exe         #     (no se distribuye; es tuya)
│   └── windows/               # módulos del paquete
└── share/wine/                # datos del paquete
```

<hr/>

## 🖥️ Pantalla: elige 1280x720 (una vez)

El runtime **no estira** la imagen: la escala con `min()` y la centra, así que con un
aspecto que no sea 16:9 aparecen **barras negras**. FIFA 07 tiene **un solo modo 16:9
nativo: `1280x720`**, y hay que elegirlo **una vez** en el propio juego:

> **Mi FIFA 07 → Ajustes → Pantalla → 1280x720**

- **NO** elijas **1280x1024**: es 5:4 y deja barras a los lados.
- El juego lo guarda solo en su perfil; no hay que editar nada a mano.
- Si ves barras negras, es que el juego no está en 16:9: vuelve a la pantalla de
  ajustes y selecciona 1280x720.

<hr/>

## 🎮 Controles

Los controles vienen **preconfigurados**. El runtime traduce el mando de Switch a las
teclas de FIFA 07 (modo teclado); se editan desde la pantalla **Configuración** de 07z.

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

> Las tácticas (**Q**) y el **teclado numérico** **no** se mapean a propósito: el
> teclado numérico comparte códigos con las flechas y disparaba las tácticas solas.

<hr/>

## ⚡ Rendimiento

- **55-60 FPS** estables en partido con gráficos y resolución en **ALTO**.
- Los **bajones de los menús 3D** (selección de equipos, plantillas) **no eran de
  CPU ni de GPU**: eran **compilación de shaders** y **I/O de la tarjeta**. El
  **segundo arranque** de un menú ya va fluido (la caché de shaders se guarda en la SD).
- El paquete ya trae los ajustes de rendimiento puestos (`sync`, `frame-limit`,
  `dxvk.conf`): **no hay que tocar nada**.
- El **overclock es opcional**: el port no lo necesita. Si quieres margen extra, aplícalo
  tú (p. ej. con **UltraHand**).

<hr/>

## ❓ Preguntas frecuentes

**¿El juego se descarga aquí?**
No. Este repositorio **no aloja ni distribuye FIFA 07** ni ningún archivo con copyright de EA. Para jugar necesitas **tu propia copia** de FIFA 07 de PC, adquirida legalmente.

**¿Hace falta internet la primera vez?**
Solo para **descargar** los ficheros (el NSP y los dos `.nro`). Una vez copiados a la SD, **07z no necesita conexión a internet** para jugar.

**¿Puedo jugar desde el Homebrew Menu?**
No. Para jugar hay que lanzar 07z **desde el icono del HOME** (el NSP). Desde el *Homebrew Menu* el frontend solo muestra un aviso: `fifa07.exe` solo se mapea en `0x400000`, y esa dirección baja queda libre **únicamente** al lanzarlo como *aplicación* con el NSP 07z (el Homebrew Menu lo lanza como *applet* de 64 bits, con esa dirección ocupada).

**¿Necesito instalar algún kip o parche de Atmosphere?**
**Sí: el «parche de ventana baja»** — es obligatorio. Son dos ficheros
(`atmosphere/mesosphere.bin` y `atmosphere/kips/autorun-loader.kip`) que van en el Release, en
`parche-ventana-baja/`. FIFA 07 es un ejecutable con direcciones fijas (`0x400000`): sin ese
parche el kernel no le da la ventana baja y el juego **no arranca** (pulsás Jugar y volvés al
menú). Es un **kernel**, así que va por **versión exacta**: este es para Atmosphere 1.11.2
(revisión `5388824…`). Si tu consola está en otra versión puede no encajar y quedarse en
**pantalla negra** — se quitan los dos ficheros y vuelve a arrancar. Guía:
[`docs/PARCHE-VENTANA-BAJA.md`](docs/PARCHE-VENTANA-BAJA.md). No hace falta nada más: ni
particiones nuevas, ni overclock, ni el asistente de setup de Wine-NX.

**¿Qué pasa si no me arranca?**
**Si el síntoma es «pulso Jugar y me devuelve al menú», casi seguro te falta el parche de ventana baja** (ver *Requisitos* y [`docs/PARCHE-VENTANA-BAJA.md`](docs/PARCHE-VENTANA-BAJA.md)). Si no es eso, casi siempre es una de estas tres cosas: la ruta del `.nro` no es exacta, falta algún dato del juego, o el runtime no está emparejado con su versión. Revisa la sección **Solución de problemas** justo aquí debajo y la guía [`docs/INSTALACION-07z.md`](docs/INSTALACION-07z.md).

**¿Está relacionado con EA?**
No. 07z es un proyecto **no oficial**, hecho por un aficionado, **sin ninguna relación, patrocinio ni respaldo** de EA.

**¿Lo puedo modificar o redistribuir?**
El frontend 07z y este repositorio son **MIT** (ver [`LICENSE`](LICENSE)); el runtime es software libre de terceros (**LGPL-2.1-or-later**, ver [`patches/`](patches/)).

<hr/>

## 🛠️ Solución de problemas

| Síntoma | Causa probable | Solución |
|---|---|---|
| El icono del HOME no abre el frontend | Ruta del `.nro` distinta | Comprueba que `sdmc:/switch/fifa07/07z.nro` existe con ese nombre exacto. |
| Sale un aviso «Abre desde el menú de inicio» | Lanzado desde el Homebrew Menu | Ábrelo desde el icono del HOME (el NSP). |
| El juego no arranca / error `c0000135` o `c000007b` | Runtime y módulos no emparejados, o falta el juego | Vuelve a copiar el runtime de **Releases** tal cual y verifica `drive_c/FIFA 07/fifa07.exe`. |
| Pantalla en negro al cargar | Copia del juego incompleta | Comprueba que copiaste **todos** los datos del juego, no solo el `.exe`. |
| Va lento o con tirones | SD lenta o firmware antiguo | Usa una SD de buena velocidad y mantén el firmware / Atmosphere actualizados. |

> ¿Nada de esto lo resuelve? Escríbeme a [francopaolo_lg@outlook.com](mailto:francopaolo_lg@outlook.com) contando tu firmware, tu SD y qué pasa exactamente. Ayuda muchísimo.

<hr/>

## 📄 Licencia

- El **frontend/homebrew 07z** y el contenido de este repositorio (scripts, documentación, *landing*) son obra de **Franco Lopez (lozp1)** bajo licencia **MIT** — ver [`LICENSE`](LICENSE).
- El **runtime** (`wine-nx-runtime.nro`) **es software de terceros**: deriva de **Wine** y **Wine-NX/Autorun**, distribuidos bajo **LGPL-2.1-or-later**. Su código y los **parches** que este proyecto le aplica están disponibles en [`patches/`](patches/) (ver [`patches/README.md`](patches/README.md)).
- FIFA 07 y sus marcas son propiedad de **EA**. Este proyecto es **no oficial**.

<hr/>

## ❤️ Apoya el proyecto

**07z es gratuito y sin ánimo de lucro.** No hay publicidad, no hay versión de pago y no genera ningún ingreso. Es el trabajo de **una sola persona** y lleva **muchísimo tiempo**: noches construyendo, compilando, probando en consola y corrigiendo errores, casi siempre para que un partido arranque sin que se note todo lo que hay detrás.

Si 07z te ha gustado y **quieres que siga publicando ports de otros juegos** para Nintendo Switch, la mejor forma de ayudarme es esta:

- 💙 **Una donación** por PayPal: [**paypal.me/francopaololg**](https://paypal.me/francopaololg). Es lo que me permite dedicar tiempo y recuperar parte de lo invertido en seguir portando.
- 📣 **Difundir el proyecto.** Si no puedes donar, compártelo con quien tenga una Switch y disfrute de estos juegos. Que se conozca también ayuda muchísimo.

**Cada aporte se traduce directamente en más ports.** Y si no puedes colaborar de ninguna forma, no pasa nada: entra, juega y disfrútalo. Con eso ya merece la pena.

<div align="center">

<a href="https://paypal.me/francopaololg" target="_blank">
    <img src="https://img.shields.io/badge/PayPal-Donar-0070BA?style=for-the-badge&logo=paypal&logoColor=white" />
</a>
<a href="mailto:francopaolo_lg@outlook.com">
    <img src="https://img.shields.io/badge/Contacto-0078D4?style=for-the-badge&logo=microsoft-outlook&logoColor=white" />
</a>

</div>

<hr/>

## 🙏 Créditos

07z no existiría sin el trabajo de mucha gente. Todo el mérito de las piezas base es suyo:

- **Wine** — [winehq.org](https://www.winehq.org/) · los autores de Wine.
- **Wine-NX / Autorun** — el runtime de Windows sobre Horizon OS ([autorunhq/autorun](https://github.com/autorunhq/autorun)). Es la base de esta obra.
- **Borealis** — framework de interfaz homebrew para Switch ([XITRIX/Borealis](https://github.com/XITRIX/borealis)).
- **libnx** y **devkitPro / devkitA64** — el toolchain y la base de todo homebrew de Switch ([devkitPro](https://devkitpro.org/), [switchbrew/libnx](https://github.com/switchbrew/libnx)).
- **FEXTendo / PES13-NX** ([Ibnuard/pes13_nx](https://github.com/Ibnuard/pes13_nx)) — wrapper y referencia de integración del que aprendimos el patrón de *forwarder* + runtime.
- Y a la **comunidad homebrew de Nintendo Switch** en general.
- Este repositorio es un fork de **FEXTendo / PES13-NX**; el README original del wrapper
  se conserva en [`README-UPSTREAM.md`](README-UPSTREAM.md).

> FIFA 07 y las marcas asociadas son propiedad de **EA (Electronic Arts)**. Este proyecto no está afiliado, patrocinado ni respaldado por EA. «*FIFA*» se usa únicamente de forma descriptiva para indicar con qué juego de PC es compatible.

---

<div align="center">
    <sub>Hecho con ❤️ por <b>lozp1</b> · Proyecto no oficial, sin relación con EA · No se distribuye el juego.</sub>
</div>
