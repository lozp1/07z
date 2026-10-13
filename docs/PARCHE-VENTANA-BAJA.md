# Parche de "ventana baja" (Autorun) — **requisito obligatorio**

> **Sin este parche, FIFA 07 NO ARRANCA.** El síntoma es exactamente este:
> pulsas **Jugar** en 07z y te **devuelve al menú de inicio** sin ningún mensaje.

## Por qué hace falta

El `fifa07.exe` es un ejecutable de 32 bits con **direcciones fijas**
(`IMAGE_FILE_RELOCS_STRIPPED`): **solo se puede mapear en `0x00400000`**. Para eso el
kernel tiene que darle al proceso una **"ventana baja"** (región de alias desde
`0x00200000`, con el código nativo y el heap por encima de 4 GiB).

Esa ventana **la concede un parche de Atmosphere** (de Autorun / Wine-NX), y **solo** a los
procesos con el *program id* `0548EABB35576000` — que es justo el del forwarder de 07z.

Sin el parche: el exe no se puede mapear → el runtime no arranca → **vuelta al menú**.

## Qué necesitas

**El parche es un kernel: va por versión exacta de Atmosphere.** Elegí el tuyo (miralo en
**Ajustes → Sistema**, donde sale por ejemplo `23.0.1 | AMS 1.12.0 | S`):

| Tu Atmosphere | Firmware | Descarga | `mesosphere.bin` | `autorun-loader.kip` |
|---|---|---|---|---|
| **AMS 1.11.2** (rev. `5388824b…`) | hasta 22.5.0 | `2-07z-PARCHE-VENTANA-BAJA.zip` | 675.840 B · md5 `2e1d04d6ea1a…` | 158.432 B · md5 `d6cdc924bf7b…` |
| **AMS 1.12.0** (tag `28d6a2e1…`) | 23.0.x | `4-07z-PARCHE-VENTANA-BAJA-AMS-1.12.0.zip` | 684.032 B · sha256 `fc1bd5665aec6618…` | 190.636 B · sha256 `22e60b857d457c65…` |

> ¿Otro AMS? Preguntá: el parche se reconstruye para esa versión exacta.
> Un `mesosphere.bin` de **otra** versión deja la consola en **pantalla negra** al encender.

> **Si al arrancar te queda la pantalla negra** (y solo ves Hekate/imagen al inicio):
> el parche no encaja con tu versión. **Apaga, borra solo los dos ficheros que
> acabas de copiar y arranca normal** — vuelve todo a como estaba. Si quieres el parche
> para tu versión, avisa: se reconstruye para esas versiones exactas.

Los dos ficheros van en el **ZIP completo** del Release (`1-07z-PAQUETE-COMPLETO.zip`), o sueltos en `2-07z-PARCHE-VENTANA-BAJA.zip` (`README.txt` y
`LICENSE.Atmosphere.txt` incluidos).

## Instalación

1. **Apaga la consola** (apagado completo, no suspensión).
2. **Copia de seguridad**: guarda tu `atmosphere/mesosphere.bin` actual por si acaso.
3. Copia a la SD:
   ```
   atmosphere/mesosphere.bin
   atmosphere/kips/autorun-loader.kip
   ```
4. **Si arrancas con Hekate** (entradas `fss0`/`pkg3`): duplica tu entrada que funciona y
   añade estas dos líneas **justo después** de la línea `fss0`/`pkg3`, sin tocar lo demás:
   ```ini
   kernel=atmosphere/mesosphere.bin
   kip1=atmosphere/kips/autorun-loader.kip
   ```
   **Si arrancas con `fusee.bin`**: no hay que añadir nada, Fusee lee estos ficheros solo.
5. Enciende y lanza **07z desde el icono del HOME**.

> ⚠️ **No borres ni edites tu entrada original de arranque**: déjala intacta para poder
> volver a arrancar si algo falla. Y **no sobrescribas** un `mesosphere.bin` propio sin copia.

## Deshacerlo

Apaga, borra **solo** estos dos ficheros (restaura tu `mesosphere.bin` anterior si tenías
uno) y arranca normal. **No toca partidas ni ajustes.**

## Nota para el usuario avanzado

El parche **no sustituye `package3`**: usa los *overrides* de la SD. En arranques por
`payload=fusee.bin` los lee Fusee; en arranques por Hekate hay que declararlos con
`kernel=` y `kip1=` como arriba. Ver `README.txt` del parche (autoritativo) y
`LICENSE.Atmosphere.txt`.
