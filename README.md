# FEXTendo / PES13-NX

FEXTendo is a Nintendo Switch launcher and compatibility **wrapper for the
Windows PC version of PES 2013**. It uses Wine, FEX-Emu and DXVK to run the PC
game; this repository contains the wrapper, integration code and build tools.

The **Switch port and Horizon/Wine integration of FEX-Emu in FEXTendo** are
developed by **AndroSwitch Project / Ibnuard**. The CPU translation engine is
upstream **FEX-Emu**; the Wine/Horizon runtime foundation comes from
**Wine-NX / Autorun**. See the [FEX port source and commit record](docs/FEX-PORT-PROVENANCE.md)
for our implementation work and the components we reuse or adapt. Our initial
FEX guest PASS on Switch predates the later, explicitly credited Autorun timer
backport and CPU-placement experiments.

**Provide your own installed PES 2013 PC version 1.0.** The game executable,
game data and installation code are not supplied by this repository.

## 07z / FIFA 07

> **Este fork añade, sobre FEXTendo/PES13-NX, el port de FIFA 07 para Nintendo
> Switch: el proyecto `07z`.** El juego se lanza desde un **icono propio en el menú
> de inicio** (NSP forwarder), con un **frontend hecho a medida** (Borealis) y el
> runtime Wine-NX por debajo: **Wine no se ve nunca**, se siente como un juego nativo.

- **Instalación (3 pasos)**: Atmosphere con sigpatches → copiar la carpeta
  `sdmc:/switch/fifa07/` a la SD (con tu copia del juego dentro) → instalar el NSP
  del forwarder. **Sin kips, sin particiones, sin overclock, sin asistente de setup.**
- **Arranque**: desde el **icono del HOME**, nunca desde el Homebrew Menu.
- **Resolución**: en *Mi FIFA 07 → Ajustes → Pantalla* elige **1280x720** (es el
  único modo 16:9 nativo; el runtime no estira la imagen, así que cualquier otro
  aspecto deja barras negras).
- **Guía completa de instalación**: [`docs/INSTALACION-07z.md`](docs/INSTALACION-07z.md)
  (se publica como `docs/INSTALACION.md` dentro del paquete 07z).
- **Estado del port y notas técnicas**: [`docs/DISTRIBUCION.md`](docs/DISTRIBUCION.md),
  [`docs/OPTIMIZACION.md`](docs/OPTIMIZACION.md),
  [`docs/MANDOS-DIAGNOSTICO.md`](docs/MANDOS-DIAGNOSTICO.md),
  [`docs/RUNTIME-RAIZ-POR-PORT.md`](docs/RUNTIME-RAIZ-POR-PORT.md).
- **Frontend**: [`frontend-nx/`](frontend-nx/) (app `07z.nro`, Borealis).

> FIFA 07 y sus marcas son propiedad de **EA**. Este proyecto es **no oficial** y no
> incluye ni distribuye el juego.

El resto de este README se conserva del proyecto original **FEXTendo / PES13-NX**
(abajo).

---

## Setup

1. Download the `FEXTendo-<version>-sd.zip` from
   [Releases](https://github.com/Ibnuard/pes13_nx/releases) and extract `switch/`
   to your SD root. This complete package includes the NRO, NSP forwarder,
   Wine/FEX/DXVK runtime, launcher assets, presets and default `settings.dat`.
   The standalone NRO/NSP downloads are for existing installations.
2. Copy your own game installation (`pes2013.exe`, accompanying game DLLs and
   `img/`) into `switch/pes13-fex/drive_c/PES13/`.
3. On the Windows PC where PES is installed, run
   [tools/export-metadata.py](tools/export-metadata.py). Copy the resulting
   `local/config/pes13-install.reg` to `switch/pes13-fex/pes13-install.reg`.
4. Install and launch the included `FEXTendo-PES13.nsp`, targeting
   `sdmc:/switch/pes13-fex/pes13-fex.nro` (32-bit address space, no alias, 4 cores,
   svcDebug disabled). Its icon matches the NRO.

Expected layout at the SD root (runtime folders shown below come from the
complete package; keep their other supplied files):

```text
switch/pes13-fex/
├── pes13-fex.nro
├── configuration.ini
├── pes13-install.reg                 # from your own Windows installation
├── launcher/                        # FEXTendo artwork, fonts and presets
├── drive_c/
│   ├── PES13/
│   │   ├── pes2013.exe               # your PC game, version 1.0
│   │   ├── img/                     # your game data
│   │   ├── ...                      # the rest of your installed game files
│   │   ├── d3d9.dll                 # package-supplied DXVK
│   │   ├── dxvk.conf
│   │   └── pes2013.wine-nx.txt
│   ├── KONAMI/Pro Evolution Soccer 2013/settings.dat
│   ├── dxvk/d3d9.dll
│   └── windows/                     # package-supplied Wine/FEX modules
└── share/wine/                      # runtime fonts and NLS data
```

Keep the package's runtime DLLs and configuration when adding game files.
The launcher manages the canonical `drive_c/KONAMI/Pro Evolution Soccer
2013/settings.dat` and its compatibility copies. Keep installation metadata
private. Close the game before replacing runtime files.

Game-data and save directories are preserved in the release ZIP even when
empty. Only PRs merged into `main` run the package/release workflow. Each merge
publishes a versioned tag, release and generated changelog
(for example, `PES13 FEXTendo V.0.3.7`, with a revision for automatic packages).
See [release CI and runtime updates](docs/RELEASE-CI.md) for the approved
production input, checks and instructions for updating the runtime binaries.

The release runtime includes two controllers, horizontal Joy-Con mapping and
live keyboard editing with English labels and controller sprites. It retains
the production-v1 startup fix, silent runtime and pre-DFE FEX DLL.

## Credits

- **FEXTendo / AndroSwitch Project:** the FEX-Emu port to Nintendo Switch,
  including our Horizon/Wine adapter, JIT memory bridge and exception handling;
  the original native launcher and PES-specific integration.
- **[Autorun (formerly Wine-NX)](https://github.com/autorunhq/autorun), danfromtico
  and contributors:** the Wine/Horizon runtime foundation, engineering
  references and explicitly attributed runtime backports.
- **[FEX-Emu](https://github.com/FEX-Emu/FEX) and its contributors:** the upstream
  CPU translation engine used by our integration. Wine, DXVK, Mesa/mesa-switch,
  libnx and the other dependencies retain their original authorship.

See [THIRD_PARTY.md](THIRD_PARTY.md) for component origins, source revisions
and licenses. Project code uses
[LGPL-2.1-or-later](LICENSE); the new FEX adapter uses [MIT](src/fex/LICENSE).
Unofficial project; not affiliated with Konami or Nintendo.
