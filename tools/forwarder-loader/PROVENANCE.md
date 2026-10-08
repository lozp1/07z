# Forwarder loader (vendored)

This directory holds the AArch64 loader that the `07z` NSP forwarder runs before
it starts `sdmc:/switch/fifa07/07z.nro`.

## Where it comes from

Taken verbatim (only the include path of `low_window.h` and the notice string
were adjusted) from the Wine-NX runtime that this project already ships, which
installs exactly this loader into the HOME-menu forwarders it creates on the
console:

| File | Origin |
| --- | --- |
| `main.c` | `horizon-wine/hbl/source/main.c` |
| `trampoline.s` | `horizon-wine/hbl/source/trampoline.s` |
| `low_window.h` | `horizon-wine/source/low_window.h` |
| `hbl.json` | `horizon-wine/hbl/hbl.json` |
| `nx-hbloader.LICENSE.md` | `horizon-wine/hbl/nx-hbloader.LICENSE.md` |

Source revision: `cbb0e4e6e7fa7f47f328d92441f51bfb507f266f`
(`C:/Projects/ports/autorun-src`, the Wine-NX runtime tree).
Upstream: nx-hbloader (ISC, behemoth/HookedBehemoth), as carried by Sphaira
(GPL-3.0) and then patched by the Wine-NX runtime.

## Why this loader and not Sphaira's stock `hbl`

Sphaira's `hbl` (`local/forwarder-tools/sphaira/hbl`) is the upstream nx-hbloader
and works for a single NRO launch in a 36/39-bit address space. It does not work
for this chain:

1. **It reads the NRO with `size = g_heapSize`** (`fsFileRead(&f, 0, start,
   g_heapSize, ...)`, with the source's own `todo: Detect whether NRO fits into
   heap or not`) instead of the file's image size. When the loader has to load
   the 41 MiB `wine-nx-runtime.nro` on the *second* pass (the frontend returned
   from `envSetNextLoad`), the FS IPC is rejected by the kernel and the loader
   aborts with `KERNELRESULT(InvalidMemoryState)` = `0xD401`
   (`Atmosphère Crash Report ... Result: 0xD401 (2001-0106)`, `User Break`,
   `LR ... forwarder + 0x3e7c` = inside `diagAbortWithResult`, `ReturnAddress[00]
   ... forwarder + 0x788` = the `diagAbortWithResult(rc)` tail of `loadNro`).
2. **It has no low-window handling.** This loader maps the NRO above
   `WINE_NX_NATIVE_BASE` (4 GiB) whenever the process gets the "low window"
   address space, so the Win32 guest image (fixed at `0x400000`) can still be
   mapped below 4 GiB by the runtime. Without it the NRO can land in the low
   window and the game never maps.

The runtime also refuses to play in the wrong layout: its setup screen states
"Start Autorun directly from the HOME Menu with a **39-bit address space** and
access to all four CPU cores", and `launcher_setup.c` gates on
`options->address_space_bits == 39 && options->four_cores_available`.

## Address space

`build-fifa07-forwarder.py` patches `address_space_type` to **3** (39-bit, no
alias) — the value the runtime's own forwarder generator writes
(`horizon-wine/source/forwarder.c`: `meta.flags = (meta.flags &
~ADDRESS_SPACE_MASK) | (3u << ADDRESS_SPACE_SHIFT)`). `AddressSpaceType = 2`
(32-bit no-alias) is what the earlier build used and it is wrong for this chain:
the loader crashes on the hand-off and the Win32 runtime cannot work in a 4 GiB
address space.

39-bit is necessary but **not sufficient**: the *low window* (alias code region at
`0x200000`, native code above 4 GiB) is granted by the console's Atmosphere
low-window patch to **one program id only**, `HasAutorunLowWindow()` =
`0x0548EABB35576000`, and the forwarder's title id must be exactly that id. See
`docs/FORWARDER-39BIT-FIX.md`; `tools/build-fifa07-forwarder.py` asserts it.
