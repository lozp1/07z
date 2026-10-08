# Estado del overclock en la SD (FIFA 07 NX)

Revisión hecha **solo leyendo** la tarjeta (`D:\`), sin aplicar cambios.
Fecha de la revisión: 2026-10-07.

---

## 1. Resumen (lo importante)

* **No hay ningún kip de overclock.** En `sdmc:/atmosphere/kips/` sólo está
  `autorun-loader.kip`; no existe `hoc.kip` ni ningún kip de relojes.
* **`hekate_ipl.ini` no pide ningún kip de overclock**: no hay ninguna línea
  `kip1=` con un kip de OC.
* **SÍ está instalado y configurado `sys-clk`** (sysmodule + overlay + gestor +
  `config.ini` con perfiles por título, a 1785 / 921 / 1600 MHz).
* **Pero falta lo más importante para que se aplique al juego**: el `config.ini`
  **no tiene entrada para el title id bajo el que corre el juego** cuando se lanza
  desde el icono del HOME. Tal como está, sys-clk **no** le sube los relojes a
  FIFA 07.

## 2. Qué hay en `sdmc:/atmosphere/kips/`

```
autorun-loader.kip    158432 bytes   (parche del cargador/ventana de Autorun)
```

Nada más. No hay `hoc.kip`, `loader.kip`, `smc.kip` ni equivalente. **Sin kip de
OC, los relojes máximos quedan en los de stock.**

## 3. `sdmc:/bootloader/hekate_ipl.ini`

Contenido relevante (sin ninguna línea de OC):

```ini
[Atmosphere (EMUMMC)]
payload=bootloader/payloads/fusee.bin

[Atmosphere (EMUMMC) - pkg3]
pkg3=atmosphere/package3
kip1patch=nosigchk
emummcforce=1

[Stock]
fss0=atmosphere/package3
stock=1
emummc_force_disable=1
```

`kip1patch=nosigchk` es la firma de seguridad; **no** carga ningún kip. No hay
`kip1=atmosphere/kips/hoc.kip` ni ninguna otra línea `kip1=`.

> Dato útil: Atmosphere **carga automáticamente** todos los `.kip` que haya en
> `sdmc:/atmosphere/kips/`. Por eso, para añadir un kip de OC no hay que tocar
> `hekate_ipl.ini`: basta con dejar el `.kip` en esa carpeta (y reiniciar).

## 4. `sys-clk`: instalado y con perfiles

Está completo:

| Pieza | Ruta | Estado |
|---|---|---|
| Sysmodule | `sdmc:/atmosphere/contents/00FF0000636C6BFF/exefs.nsp` | presente |
| Arranque | `sdmc:/atmosphere/contents/00FF0000636C6BFF/flags/boot2.flag` | presente (carga al arrancar) |
| Overlay | `sdmc:/switch/.overlays/sys-clk-overlay.ovl` | presente |
| Gestor | `sdmc:/switch/sys-clk-manager.nro` | presente |
| Config | `sdmc:/config/sys-clk/config.ini` | presente |

`config.ini` (sin el texto de ejemplo) tiene exactamente:

```ini
[05B0354496B71000]
handheld_cpu=1785
handheld_gpu=921
handheld_mem=1600

[018D425BE282F000]
docked_cpu=1785
docked_gpu=921
docked_mem=1600

[0548EABB35576000]
handheld_cpu=1785
handheld_gpu=921
handheld_mem=1600
```

* `[0548EABB35576000]` es el **program id del runtime Wine-NX/Autorun** (así lo
  documenta `docs/mandos-joycon-separados.md`): sirve si se lanza el runtime
  **directamente**.
* 1785 / 921 / 1600 MHz son los **máximos de stock de una consola Erista (V1)**
  (CPU / GPU / MEM). Es decir: es un «overclock» respecto a los relojes de
  portátil por defecto (CPU ~1020, GPU 384-768), pero **es el techo sin kip de
  OC**. Si la consola es Mariko (V2), sus máximos son más altos
  (1963 / 1267 / 1996) y estos valores dejan margen.
* sys-clk evalúa, en este orden: `handheld_charging_*` → `handheld_*`; y en dock,
  `docked_*`. Las claves que falten se ignoran y se usa stock.

## 5. Lado Autorun

* `sdmc:/switch/wine/config/settings.json` sólo contiene opciones del runtime
  (`core-balancing`, `verbose-log`, `dxvk-for-new-games`, …). **No hay ninguna
  opción de overclock.**
* `autorun-loader.kip` es un parche del **cargador/ventana baja**, no de relojes.
* El runtime no toca relojes: en modo teclado/mando, gráficos, etc., no hay
  ningún ajuste de frecuencia. El único camino de OC en esta instalación es
  **sys-clk**.

## 6. Lo que le falta exactamente al usuario

### Obligatorio para que el OC se aplique al juego

1. **Que sys-clk vea el title id correcto.** El juego se lanza desde el icono del
   HOME → NSP forwarder **07z** (title id **`0x051D3B463F87C000`**, construido el
   2026-10-07, `local/forwarder-build-fifa07/hacbrewpack_nsp/051d3b463f87c000.nsp`,
   idéntico en tamaño al `/d/FIFA-FZ-forwarder.nsp` de la SD) → `FifaFZ.nro` →
   `wine-nx-runtime.nro` → `fifa07.exe`. Todo el proceso corre bajo ese title id.
   **Ese id NO está en `config.ini`.**

   *Comprobación en la consola (sin escribir nada):* abre el **overlay de sys-clk**
   (Tesla: `L + D-Pad Abajo + R-Stick`, o desde `ovlmenu`) mientras el juego está
   en primer plano. El overlay muestra el *Application ID* en foco y los relojes
   aplicados.

   *Corrección:* añadir a `sdmc:/config/sys-clk/config.ini` un bloque con **ese**
   id, con los mismos valores, p. ej.:

   ```ini
   [051D3B463F87C000]
   handheld_cpu=1785
   handheld_gpu=921
   handheld_mem=1600
   docked_cpu=1785
   docked_gpu=921
   docked_mem=1600
   ```

   (También se puede fijar desde el propio overlay mientras se juega; sys-clk lo
   escribe en el `config.ini`.)

2. **Confirmar que sys-clk está vivo.** Con `boot2.flag` presente debería cargarse
   al arrancar; verifícalo en `ovlSysmodules` o porque el overlay de sys-clk
   responde. Si el overlay dice que no hay servicio de sys-clk, el sysmodule no se
   cargó.

3. **Elegir los perfiles según uso.** Los bloques actuales del runtime sólo traen
   `handheld_*`. Si juegas **en dock**, añade también `docked_*` (o usa el id que
   corresponda); si juegas **portátil**, `handheld_*` es lo que aplica.

### Sólo si quiere pasar de los máximos de stock

4. **Añadir un kip de overclock.** No hay ninguno. Para superar
   1785 / 921 / 1600 en una Erista hace falta un kip tipo `hoc.kip` (familia
   *OC Suite*). Se coloca en:

   ```
   sdmc:/atmosphere/kips/hoc.kip
   ```

   **No hay que tocar `hekate_ipl.ini`**: Atmosphere auto-carga todo `.kip` de esa
   carpeta. Reinicia la consola después.

   Advertencia: subir de los máximos de stock aumenta consumo y temperatura; en
   portátil, vigila la batería y usa el overlay de temperaturas.

## 7. Por qué no lo he aplicado

La tarea pedía **averiguar y documentar, sin aplicar**. Además, (a) escribir en
la SD estaba fuera del alcance de esta sesión y (b) elegir el bloque de sys-clk
correcto depende de **un dato que sólo se ve en la consola** (el *Application ID*
que muestra el overlay), así que lo suyo es confirmarlo ahí antes de escribir el
`config.ini`.
