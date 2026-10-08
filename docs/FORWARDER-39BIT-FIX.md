# Forwarder `07z`: por qué el runtime decía "Address space unavailable" y el arreglo

Estado: **arreglado**. Artefacto nuevo en
`dist/fifa07-forwarder/FIFA-FZ-forwarder.nsp` y
`dist/github-07z/install/07z-forwarder.nsp` (y copiado a `sdmc:/07z-forwarder.nsp` y
`sdmc:/switch/07z-forwarder.nsp`).

| | |
| --- | --- |
| NSP | `dist/fifa07-forwarder/FIFA-FZ-forwarder.nsp` |
| tamaño | 248024 bytes |
| sha256 | `16c912f006c2f8548f4122a981d8dca682d1e5cea37d527db73460d0017cb0e0` |
| title id (program id) | `0548EABB35576000` |
| nextNroPath / nextArgv | `sdmc:/switch/fifa07/07z.nro` |
| verificación | `python3 tools/verify-forwarder-nsp.py` → **148/148 checks** |

> Los tres apartados siguientes sustituyen al diagnóstico que tenía antes este
> fichero ("AddressSpaceType=2 + loader de Sphaira"). Aquello ya está aplicado (el
> NPDM es 39-bit y el loader es el del runtime) y **no** era lo que quedaba por
> arreglar: el frontend 07z ya arrancaba bien desde el icono. Lo que faltaba es lo
> de abajo.

## Síntoma

Desde el icono del HOME, 07z arranca y hace el *hand-off* correctamente
(`sdmc:/switch/wine/fifa07nx.log`: `Jugar: appletType=0 appMode=true
envHasNextLoad=true rc=0x00000000` y `07z cerrado correctamente`), pero el runtime
que recibe el testigo se niega a lanzar el juego con el mensaje
**"Address space unavailable"**.

El diagnóstico que circulaba decía que el subtítulo mostrado era *"Start Autorun
from its 39-bit forwarder…"*, es decir la primera rama de `address_space_fits()`
(`l->options->address_space_bits != 39`). **El log del runtime demuestra que no**:
el espacio de direcciones **sí** es de 39 bits y lo que falta es otra cosa.

## Evidencia dura: el log del runtime de la sesión que falló

`sdmc:/switch/wine/logs/autorun_runtime.log` (sesión de las 09:48, la del fallo):

```
[BUILD] nx-amd64-fex-2640 from sdmc:/switch/wine/wine-nx-runtime.nro (address space 39 bits)
[LOWVA] forwarder title 058f3083dc72b000
[LOWVA] stock layout; fixed-low Win32 titles require the Atmosphere low-address patch
```

Tres líneas que fijan el diagnóstico:

1. `(address space 39 bits)` lo imprime `runtime.c` con
   `runtime_address_space_bits()` (`horizon-wine/source/runtime.c:3469-3480`, que
   lee `svcGetInfo(AslrRegionAddress/Size)`); devuelve **39**. El `AddressSpaceType=3`
   del NPDM **ya está bien**.
2. `[LOWVA] stock layout` lo imprime `wine_nx_low_window_probe()`
   (`horizon-wine/source/low_window.c:127-139`) cuando su bandera `low_window` es 0,
   o sea cuando `wine_nx_is_low_window(base, size)` (`source/low_window.h:10-13`) es
   falsa. Esa función exige `base == 0x200000` y
   `size == 0x8000000000 - 0x200000`.
3. `[LOWVA] forwarder title 058f3083dc72b000` es el **program id del proceso**
   (`svcGetInfo(InfoType_ProgramId)`, `runtime.c:3572`), y es el title id del
   forwarder antiguo.

Con eso, `address_space_fits()` (`horizon-wine/source/launcher.c:1978-1982`)

```c
return l->options->address_space_bits == 39 &&
       (l->options->low_window || launcher_program_address_space( p->path ) != LAUNCHER_ADDRESS_LOW);
```

falla por la **segunda** condición: `address_space_bits == 39` es verdadero,
`low_window` es 0 y `fifa07.exe` es un programa de dirección baja
(`LAUNCHER_ADDRESS_LOW`, porque va con `IMAGE_FILE_RELOCS_STRIPPED` y sólo mapea en
su `ImageBase` `0x400000`). El subtítulo que corresponde a ese caso es el **otro**
(`launcher.c:2012-2014`): *"This game requires the Atmosphere low-address patch.
Restart with the patched loader and Mesosphere."*

En resumen: **no falta "un espacio de 39 bits", falta la ventana baja** (la región
de alias/código por debajo de 4 GiB que el parche de Atmosphere concede a un
program id concreto).

## Causa raíz

El parche **low-window** del proyecto (`atmosphere/mesosphere.bin` +
`atmosphere/kips/autorun-loader.kip`, base Atmosphere 1.11.2 rev `5388824b`,
origen `lowwindow/low-window/low-window.patch`) concede la ventana baja a **un
único program id**:

```c
/* low-window.patch, svc_memory_map.hpp (líneas 111-116) */
constexpr inline bool HasAutorunLowWindow(u64 program_id) {
    return program_id == UINT64_C(0x0548EABB35576000);
}
constexpr inline u64 AutorunNativeAddressStart = UINT64_C(0x100000000);
```

y sólo entonces mueve las regiones del proceso:

| Fichero (hunk del parche) | Qué hace si `HasAutorunLowWindow(program_id)` |
| --- | --- |
| `kern_k_process.cpp` (parche línea 99) | pasa `HasAutorunLowWindow(params.program_id)` como `low_window` a la page table |
| `kern_k_page_table_base.cpp` (parche líneas 81-85) | `m_code_region_start = 0x100000000` y **`m_alias_code_region_start = AddressSmallMap32Start = 0x00200000`** |
| `ldr_process_creation.cpp` (parche líneas 126-129) | `aslr_start = 0x100000000` (el código del NRO va por encima de 4 GiB) |

`InfoType_AslrRegionAddress/Size` devuelven justamente esa *alias code region*
(`vendor/Atmosphere/libraries/libmesosphere/source/svc/kern_svc_info.cpp:67-72`), de
modo que sólo ese id ve `0x00200000` + `0x7FFE00000` → `wine_nx_is_low_window()`
verdadera y `runtime_address_space_bits()` = 39.

Cualquier **otro** id recibe el 39-bit de fábrica: alias code region
`[0x08000000, 0x8000000000)`, porque `AddressMap39Start = AddressNullGuard64Size`
= 128 MiB (`vendor/Atmosphere/libraries/libvapours/include/vapours/svc/svc_memory_map.hpp:66,96-98`).
Con `base = 0x08000000`, `wine_nx_is_low_window()` es falsa → `[LOWVA] stock layout`.

**`0x0548EABB35576000` es el title id del forwarder "main" que el propio
instalador del runtime crea** para `sdmc:/switch/wine/wine-nx-runtime.nro`
(`forwarder_hash()` con `FORWARDER_GENERATION = 2`,
`horizon-wine/source/forwarder.c:919-939`); es `AUTORUN_TITLE_ID`
(`horizon-wine/source/forwarder_launch.h:7`) y es el valor contra el que
`horizon-wine/tests/check_low_window_routing.py` comprueba el parche. Lo dice
también su `mesosphere/README.txt`: *"Only 39-bit processes with program ID
0548EABB35576000 receive the new layout."*

El generador anterior (`tools/build-fifa07-forwarder.py`) derivaba el title id de
**nuestro** NRO con el esquema de Sphaira
(`sha256("sdmc:/switch/fifa07/07z.nro" + nextArgv)`), lo que daba
`058F3083DC72B000`: un id que el parche **no** reconoce. De ahí el espacio de 39
bits *sin* ventana baja.

### Por qué el id se hereda

07z **no crea un proceso nuevo**: hace `envSetNextLoad(...wine-nx-runtime.nro...)`
y el loader del forwarder carga ese NRO **en el mismo proceso**
(`horizon-wine/hbl/source/main.c`, `loadNro()`). Por tanto el program id con el que
corre el runtime es, literalmente, el title id del NSP del icono. Ese es el único
sitio donde se puede arreglar.

## El arreglo

En `tools/build-fifa07-forwarder.py`, `TITLE_ID` ya **no** se deriva de nuestro
NRO: se fija al id del parche y se **calcula y asevera** contra la misma fórmula
que usa el runtime (`low_window_program_id()` reproduce
`forwarder_hash(nro, NULL, generation=2)` sobre
`sdmc:/switch/wine/wine-nx-runtime.nro`):

```python
LOW_WINDOW_GENERATION   = 2
LOW_WINDOW_RUNTIME_NRO  = 'sdmc:/switch/wine/wine-nx-runtime.nro'
LOW_WINDOW_PROGRAM_ID   = 0x0548EABB35576000      # HasAutorunLowWindow(), mesosphere/README.txt

def low_window_program_id(): ...                  # sha256(nro+nro+"\naddress-space=3\nautorun-forwarder=2")

assert low_window_program_id() == LOW_WINDOW_PROGRAM_ID
TITLE_ID = LOW_WINDOW_PROGRAM_ID
```

Todo lo demás del paquete se genera a partir de `TITLE_ID`, así que el id nuevo
llega a los tres sitios que el kernel y el instalador miran:

* cabecera de las tres NCAs (`program_id`),
* NPDM `ACI0.program_id` y `ACID.program_id_min/max`,
* CNMT (`Application_0548eabb35576000.cnmt`) y los campos derivados del NACP
  (`presence_group_id`, `save_data_owner_id`, `pseudo_device_id_seed`,
  `add_on_content_base_id`, `local_communication_id`).

El resto del forwarder no cambia: `AddressSpaceType = 3` (39-bit, no alias),
`is_64_bit`, `sys_resource_size = 16 MiB`, núcleos 0-3 / prioridades 28-63, hbl del
runtime vendorizado (`tools/forwarder-loader/`) y `nextNroPath` a
`sdmc:/switch/fifa07/07z.nro`.

### Por qué esto sí da la ventana baja

Porque el program id del proceso pasa a ser el que el parche compara. Con él:

* el mesosphere parcheado pone la *alias code region* en `0x00200000`
  → `svcGetInfo(AslrRegionAddress) == 0x200000` y
  `svcGetInfo(AslrRegionSize) == 0x7FFE00000` → `wine_nx_is_low_window()` **verdadera**;
* el loader parcheado pone el código del NRO (07z primero, el runtime después) por
  encima de 4 GiB (`aslr_start = 0x100000000`), así que la ventana
  `[0x200000, 0x100000000)` queda libre para las imágenes Win32 — exactamente lo que
  necesita `fifa07.exe` en `0x400000`;
* `runtime_address_space_bits()` sigue contestando 39 (límite `0x8000000000`).

Y el loader vendorizado ya sabe mantener el NRO por encima de 4 GiB cuando detecta
la ventana baja (`hbl/source/main.c`, `wine_nx_is_low_window(aslr_base, aslr_size)`).

### Efecto lateral (intencionado, a saber)

El NSP comparte title id con el forwarder "main" de Autorun. Consecuencias:

* Instalarlo **sustituye** ese icono (el usuario verá "07z" donde antes veía
  "Autorun"). Es el mismo forwarder para el mismo runtime; el nuestro además
  arranca 07z antes. Si el usuario reinstala el de Autorun desde sus ajustes,
  recuperará ese icono (y seguirá teniendo ventana baja, pero sin el frontend 07z).
* Dentro del runtime, `own_forwarder` (`runtime.c:3817`) pasa a ser verdadero
  (antes era falso). Sólo alimenta el estado del *forwarder* en la pantalla de
  Ajustes/Setup (`launcher_setup.c:118`); es correcto: el icono **sí** es el
  forwarder del runtime.
* DBI avisa de que el title id está por encima de `01FFFF…` (igual que pasaba con
  el id anterior) y de la falta de ticket/firma: normal en un NSP *homebrew*.

## Comparación con forwarders que funcionan

Los NSP de `sdmc:/forwarders/ports_juegos/*.nsp` que el usuario tiene instalados y
funcionan (**no** necesitan ventana baja: lanzan NROs ARM nativos) llevan un NPDM
**distinto** al nuestro — y eso es correcto para ellos:

| | 07z (nuevo) | Sphaira (`ports_juegos` en la SD) | Forwarder *main* de Autorun |
| --- | --- | --- | --- |
| title id | `0548EABB35576000` (id del parche) | `01D6ECCC00xx0000` (esquema propio de Sphaira) | `0548EABB35576000` |
| NPDM `AddressSpaceType` | **3** (39-bit, no alias) | **1** (36-bit) | 3 (`forwarder.c` escribe 3) |
| NPDM `sys_resource_size` | `0x1000000` (16 MiB) | `0x0` | 16 MiB |
| kernel flags (ACI0[0]) | `0x030073F7` (núcleos 0-3, prio 28-63) | `0x020073B7` (menos núcleos) | igual que el nuestro |
| loader `main` (NSO) | 22696 B — *hbl* del runtime | 54085 B — *hbl* stock de Sphaira | *hbl* del runtime |
| `nextNroPath` | `sdmc:/switch/fifa07/07z.nro` | su `.nro` nativo | `sdmc:/switch/wine/wine-nx-runtime.nro` |
| ¿necesita ventana baja? | **sí** (`fifa07.exe` fijo en `0x400000`) | no | sí |

Datos medidos con un parser propio sobre los NSP reales de la SD y sobre el nuestro
(mismo formato que `tools/verify-forwarder-nsp.py`). El NPDM de los forwarders de
Sphaira (36-bit, `sys_resource_size = 0`) explica por qué copiar su receta no vale
para esta cadena: un proceso de 36 bits ni siquiera llega a los 39 bits que el
runtime exige, y sin el id del parche tampoco hay ventana baja.

Comparación directa de `loader`: los dos son nx-hbloader, pero el de la SD es el
stock (54085 B) y el nuestro es el que el runtime instala en sus propios forwarders
(22696 B; valida el tamaño de la imagen del NRO y mantiene el NRO por encima de
4 GiB — ver `tools/forwarder-loader/PROVENANCE.md`).

## Cómo verificar en consola que el espacio es de 39 bits (y con ventana baja)

`sdmc:/switch/wine/logs/autorun_runtime.log` se reescribe en cada arranque del
runtime. Tras lanzar 07z desde el icono y pulsar Jugar, el fichero debe empezar así:

```
[BUILD] nx-amd64-fex-2640 from sdmc:/switch/wine/wine-nx-runtime.nro (address space 39 bits)
[LOWVA] forwarder title 0548eabb35576000
[LOWVA] RX execute at 00400000: PASS (rc=0x0)
[LOWVA] RW alias at ffff0000: PASS (rc=0x0)
[LOWVA] PASS: low window reserved for Wine; native allocations above 4 GiB
```

Qué mirar:

* **`(address space 39 bits)`** — `runtime_address_space_bits()` (ya salía antes;
  sin él no hay nada que hacer).
* **`[LOWVA] forwarder title 0548eabb35576000`** — el proceso lleva el program id
  del parche. Si aquí sale otro id, el kernel no concede la ventana baja.
* **`[LOWVA] PASS: low window reserved for Wine; native allocations above 4 GiB`** —
  la ventana baja está concedida (`wine_nx_low_window_probe()` verdadero).

Qué sale cuando **falla** (para distinguirlo):

* `[LOWVA] stock layout; fixed-low Win32 titles require the Atmosphere low-address
  patch` → es el síntoma de este documento: layout de 39 bits de fábrica, sin
  ventana baja (parche no instalado, o program id que el parche no reconoce).
* `[LOWVA] FAIL: native layout or guest reservation; reinstall the main forwarder`
  → el parche está, pero algo del proceso (heap/alias/stack por debajo de 4 GiB) no
  cuadra; reinstalar el forwarder.
* `[LOWVA] RX execute at 00400000: FAIL` / `RW alias at ffff0000: FAIL` → el kernel
  no permite mapear el código en la ventana baja.
* En pantalla, "Address space unavailable" con el subtítulo *"Start Autorun from its
  39-bit forwarder…"* significa `address_space_bits != 39` (NPDM/launch
  equivocados), que **no** es este caso.

Comprobación en el PC, sin consola, de que el NSP lleva el id correcto:

```sh
python3 tools/verify-forwarder-nsp.py        # 148/148, incluye "title id is the low-window program id"
```

## Cómo se regenera

```sh
DEVKITPRO=C:/devkitPro python tools/build-fifa07-forwarder.py --keys <prod.keys>
python3 tools/verify-forwarder-nsp.py                     # 148/148
cp dist/fifa07-forwarder/FIFA-FZ-forwarder.nsp dist/github-07z/install/07z-forwarder.nsp
```

Requisitos en la consola: Atmosphere 1.11.2 con el parche low-window instalado
(`atmosphere/mesosphere.bin` + `atmosphere/kips/autorun-loader.kip`; hashes en
`lowwindow/low-window/manifest.json`) y CFW con sigpatches/`nosigchk` para lanzar
títulos sin firma oficial, como cualquier NSP *homebrew*.

## Sobre los avisos de DBI al instalar

El NSP es un NSP *homebrew* sin firma de Nintendo, como todos los de
hacBrewPack/Sphaira. DBI avisa por eso, no porque el fichero esté roto: sin ticket
(las secciones van en claro, `crypt_type=1`), firma de NCA no verificada (cabecera
con la clave ACID pública, parcheada) y sin HTML doc/legal info. Además, title id
por encima de `01FFFF…` (mismo aviso que con el id anterior). Nada de eso impide la
instalación; el NSP anterior ya se instalaba y el frontend arrancaba.

## Pendientes / no verificado

* **No está probado en consola desde aquí**: no hay acceso a la Switch en este
  entorno. Lo verificado es estático (148/148) y documental: el id del NSP es
  exactamente el que el parche compara y el que el propio instalador de Autorun
  calcula para el mismo NRO.
* El NSP no es reproducible byte a byte (hacBrewPack firma cada cabecera NCA con
  RSA-PSS y sal aleatoria); el sha256 de arriba es el del artefacto actual. Lo
  estable es el contenido (title id, rutas, NPDM, NACP, loader).
* Si algún día se quiere que los forwarders *por juego* de Autorun
  (`--library-game=N`, otro title id) también tengan ventana baja, hay que ampliar
  `HasAutorunLowWindow()` en el parche y reconstruir mesosphere.bin + kip; queda
  fuera del alcance de este arreglo.
* Alternativa sin NSP (sin recompilar nada): abrir "Autorun" desde el Homebrew
  Menu, añadir el juego y aceptar "Install forwarder"; ese icono ya usa el id del
  parche y funciona, sólo que no muestra el frontend 07z.
