# Créditos y licencias de terceros — 07z

**07z** (frontend, shims, parches y herramientas de este repositorio) es obra de
**Franco López (`lozp1`)** y se publica bajo licencia **MIT** (ver [LICENSE](LICENSE)).

**El juego no se distribuye.** FIFA 07 y sus datos son propiedad de **EA**; cada
usuario aporta su propia copia de PC.

## Componentes de terceros

| Componente | Autoría | Licencia / texto |
| --- | --- | --- |
| **Wine / Wine-NX / Autorun** (runtime) | Autores de Wine; danfromtico y contribuidores de Autorun | **LGPL-2.1-or-later** — [licenses/LGPL-2.1.txt](licenses/LGPL-2.1.txt) · [repo](https://github.com/autorunhq/autorun) |
| **DXVK** (d3d9 sobre Vulkan) | Philip Rebohle, Joshua Ashton y contribuidores | zlib/libpng — [licenses/DXVK-LICENSE.txt](licenses/DXVK-LICENSE.txt) |
| **Mesa / mesa-switch** (NVK) | Autores de Mesa; danfromtico, NaGaa95 y contribuidores | Mayormente MIT, licencias individuales — [licenses/Mesa-license.rst](licenses/Mesa-license.rst) |
| **Box64** (traducción x86→ARM) | ptitSeb y contribuidores | MIT — [licenses/Box64-LICENSE.txt](licenses/Box64-LICENSE.txt) |
| **libnx** | switchbrew y contribuidores | ISC — [licenses/libnx-LICENSE.md.txt](licenses/libnx-LICENSE.md.txt) |
| **Borealis** (interfaz del frontend) | XITRIX y contribuidores | Ver [XITRIX/borealis](https://github.com/XITRIX/borealis) |
| **FEXTendo / PES13-NX** | AndroSwitch Project / Ibnuard | Referencia del patrón *forwarder + runtime*; ver [Ibnuard/pes13_nx](https://github.com/Ibnuard/pes13_nx). El README original del wrapper se conserva en [README-UPSTREAM.md](README-UPSTREAM.md) |
| **devkitPro / devkitA64** | devkitPro y contribuidores | Cada componente conserva su licencia |
| Librerías enlazadas (SDL2, FreeType, HarfBuzz, libpng, zlib, bzip2, zstd, Expat, libdrm_nouveau) | Sus respectivos autores | Ver [licenses/](licenses/) |

## Sobre este repositorio

- **Los ficheros de este repositorio son obra original** del autor de 07z, salvo lo
  indicado en la tabla anterior. Los ficheros adaptados de terceros conservan sus
  avisos de copyright y su licencia original.
- **El runtime no se incluye aquí**: se distribuye como binario
  (`wine-nx-runtime.nro`) en la sección **Releases**, y es software de terceros bajo
  **LGPL-2.1-or-later**. Los parches que este proyecto le aplica están en
  [`patches/`](patches/).
- **El forwarder** (`tools/forwarder-loader/`) parte del patrón de FEXTendo; su
  procedencia está anotada en `tools/forwarder-loader/PROVENANCE.md`.
- **Nada de este repositorio contiene material de EA.**
