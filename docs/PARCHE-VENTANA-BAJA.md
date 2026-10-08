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

| Requisito | Valor |
|---|---|
| **Atmosphere** | **1.11.2**, revisión `5388824be146a89619e8d641acd64599cf1c5f62`. **El parche es un kernel: va por versión exacta de Atmosphere y de firmware.** Si tu consola está en otra versión (AMS distinto, firmware más nuevo) puede **no encajar** → pantalla negra (ver aviso de abajo). **AMS 1.11.2 llega hasta firmware 22.5.0**: el firmware **23.0.x** todavía no está soportado por Atmosphere, así que ahí **no hay parche posible** (ni este ni otro) hasta que salga la versión que lo soporte |
| `atmosphere/mesosphere.bin` | 675.840 bytes · md5 `2e1d04d6ea1a…` |
| `atmosphere/kips/autorun-loader.kip` | 158.432 bytes · md5 `d6cdc924bf7b…` |

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
