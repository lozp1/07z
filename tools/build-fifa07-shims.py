#!/usr/bin/env python3
"""Build the three 32-bit shim DLLs FIFA 07 needs and verify them.

fifa07.exe statically imports one function from each of DINPUT.dll and
SensApi.dll, and the variant B graphics chain needs dxwrapper.dll, which imports
MSIMG32.dll and OLEACC.dll. The Wine-NX payload ships none of them, and
Wine/Wine-NX does not synthesise a whole missing module for a static import, so
the loader aborts with STATUS_DLL_NOT_FOUND (0xC0000135): before the game draws
anything when it is DINPUT/SensApi, and inside dxwrapper.dll (whose stub then
switches itself off) when it is MSIMG32/OLEACC. Scraping the host's
C:\\Windows\\SysWOW64 copies is not an option: those are Windows 10/11 binaries
whose api-set imports Wine-NX cannot resolve.

OLEACC.dll is the one entry not built here: Wine's own build ships in the other
Wine-NX payload on the card (pes13-fex/drive_c/windows/syswow64) and already
exports the two functions dxwrapper imports, so
tools/package_fifa07_diag.py copies it from there.

This tool builds drop-in replacements from src/shims/ and then verifies them the
way that matters:

  * both are 32-bit (i386) PE images,
  * each exports exactly the functions the game imports,
  * neither imports any api-ms-*/ext-ms-* api-set,
  * neither is byte-identical to a host system DLL.

Only after all of that passes are they installed into the packages.

Requires i686-w64-mingw32-gcc (MSYS2 package mingw-w64-i686-gcc).
"""
from __future__ import annotations

import argparse
import hashlib
import os
import shutil
import struct
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

# name -> (source, definition file, libraries)
SHIMS = {
    "DINPUT.dll": ("dinput_fifa07.c", "dinput_fifa07.def", ["-ldxguid", "-luser32"]),
    "sensapi.dll": ("sensapi_fifa07.c", "sensapi_fifa07.def", ["-luser32"]),
    "msimg32.dll": ("msimg32_fifa07.c", "msimg32_fifa07.def", ["-lgdi32"]),
    "dmusic.dll": ("dmusic_fifa07.c", "dmusic_fifa07.def", ["-lole32"]),
    "dpnhpast.dll": ("dpnhpast_fifa07.c", "dpnhpast_fifa07.def", ["-lole32"]),
}
# Exports the guest actually resolves, per the import tables of fifa07.exe, of
# dxwrapper.dll (MSIMG32/OLEACC) and of the in-process COM server the game
# reaches through CoCreateInstance (dmusic).
EXPECTED_EXPORTS = {
    "DINPUT.dll": {"DirectInputCreateA"},
    "sensapi.dll": {"IsNetworkAlive", "IsDestinationReachableA", "IsDestinationReachableW"},
    "msimg32.dll": {"AlphaBlend", "GradientFill", "TransparentBlt"},
    "dmusic.dll": {"DllGetClassObject", "DllCanUnloadNow"},
    "dpnhpast.dll": {"DllGetClassObject", "DllCanUnloadNow",
                     "DllRegisterServer", "DllUnregisterServer"},
}
# On-disk name: spelled as the import table spells it, so a case-sensitive
# lookup cannot miss it either.
INSTALL_NAMES = {
    "DINPUT.dll": "DINPUT.dll",
    "sensapi.dll": "sensapi.dll",
    "msimg32.dll": "MSIMG32.dll",
    "dmusic.dll": "dmusic.dll",
    "dpnhpast.dll": "dpnhpast.dll",
}
COMPILER_CANDIDATES = (
    Path(r"C:\msys64\mingw32\bin\i686-w64-mingw32-gcc.exe"),
    Path(r"C:\msys64\mingw64\bin\i686-w64-mingw32-gcc.exe"),
)


def find_compiler(explicit: Path | None) -> Path:
    if explicit:
        if explicit.is_file():
            return explicit
        raise SystemExit(f"compiler not found: {explicit}")
    for candidate in COMPILER_CANDIDATES:
        if candidate.is_file():
            return candidate
    found = shutil.which("i686-w64-mingw32-gcc")
    if found:
        return Path(found)
    raise SystemExit(
        "i686-w64-mingw32-gcc not found. Install it with:\n"
        r"  C:\msys64\usr\bin\pacman.exe -S --needed mingw-w64-i686-gcc")


def pe_dirs(path: Path) -> tuple[int, list[tuple[int, int, int]], list[str], list[str]]:
    """Return (machine, sections, imports, exports) of a PE image."""
    data = path.read_bytes()
    pe = struct.unpack_from("<I", data, 0x3C)[0]
    if data[pe:pe + 4] != b"PE\0\0":
        raise SystemExit(f"{path} is not a PE image")
    machine = struct.unpack_from("<H", data, pe + 4)[0]
    nsec = struct.unpack_from("<H", data, pe + 6)[0]
    opt = pe + 24
    data_dir = opt + 96
    table = opt + struct.unpack_from("<H", data, pe + 20)[0]
    secs = []
    for i in range(nsec):
        base = table + i * 40
        vsz, va, rsz, ptr = struct.unpack_from("<IIII", data, base + 8)
        secs.append((va, max(vsz, rsz), ptr))

    def rva2off(rva: int) -> int | None:
        for va, size, ptr in secs:
            if va <= rva < va + size:
                return ptr + (rva - va)
        return None

    def string_at(rva: int) -> str:
        o = rva2off(rva)
        return data[o:data.index(b"\0", o)].decode("latin1") if o is not None else ""

    imports = []
    rva = struct.unpack_from("<I", data, data_dir + 1 * 8)[0]
    if rva:
        o = rva2off(rva)
        while o and data[o:o + 20] != b"\0" * 20:
            imports.append(string_at(struct.unpack_from("<I", data, o + 12)[0]))
            o += 20

    exports = []
    rva, size = struct.unpack_from("<II", data, data_dir + 0 * 8)
    if rva:
        o = rva2off(rva)
        nnames = struct.unpack_from("<I", data, o + 24)[0]
        off_names = struct.unpack_from("<I", data, o + 32)[0]
        for i in range(nnames):
            name_rva = struct.unpack_from("<I", data, rva2off(off_names + i * 4))[0]
            exports.append(string_at(name_rva))
    return machine, secs, imports, exports


def host_syswow64_hashes() -> dict[str, str]:
    out: dict[str, str] = {}
    root = Path(r"C:\Windows\SysWOW64")
    if not root.is_dir():
        return out
    for entry in root.glob("*.dll"):
        try:
            out[entry.name.lower()] = hashlib.sha256(entry.read_bytes()).hexdigest()
        except OSError:
            pass
    return out


def native(path) -> str:
    """Forward-slash path: the compiler is a native program, not an MSYS one."""
    return str(path).replace("\\", "/")


def build(compiler: Path, name: str, outdir: Path) -> Path:
    source, defs, libs = SHIMS[name]
    # Written under the name the import table spells, so the packager can copy
    # it straight into the game folder.
    target = outdir / INSTALL_NAMES.get(name, name)
    cmd = [native(compiler), "-shared", "-O2", "-Wall", "-Wextra",
           "-Wl,--no-insert-timestamp",
           "-o", native(target), native(ROOT / "src" / "shims" / source),
           native(ROOT / "src" / "shims" / defs)]
    cmd += libs + ["-lkernel32"]
    # cc1.exe and collect2.exe live under the gcc lib directory, but their own
    # DLLs (libmpfr, libwinpthread, libzstd, ...) are resolved through PATH from
    # mingw32/bin. A shell that can start gcc.exe (its DLLs sit next to it) but
    # has not got mingw32/bin on PATH gets a bare "exit status 1" with no
    # message at all - the driver cannot even run its own compiler.
    env = dict(os.environ)
    env["PATH"] = str(compiler.parent) + os.pathsep + env.get("PATH", "")
    print("  " + " ".join(cmd[1:]))
    subprocess.run(cmd, check=True, env=env)
    return target


def verify(built: Path, name: str, host: dict[str, str]) -> None:
    machine, _secs, imports, exports = pe_dirs(built)
    assert machine == 0x014C, f"{name}: machine 0x{machine:04x}, expected 0x014c (i386)"
    got = set(exports)
    expected = EXPECTED_EXPORTS[name]
    missing = expected - got
    assert not missing, f"{name}: missing exports {sorted(missing)} (has {sorted(got)})"
    bad = [d for d in imports if d.lower().startswith(("api-ms-", "ext-ms-"))]
    assert not bad, f"{name}: imports api-sets that Wine-NX does not provide: {bad}"
    digest = hashlib.sha256(built.read_bytes()).hexdigest()
    assert host.get(name.lower()) != digest, f"{name} is a copy of the host's system DLL"
    print(f"  {name}: i386 OK, exports {sorted(got)}, imports {imports}, "
          f"{built.stat().st_size} bytes, sha256 {digest[:16]}")


def install(built: dict[str, Path], packages: list[Path]) -> None:
    for package in packages:
        game = package / "switch" / "wine" / "drive_c" / "FIFA 07"
        if not game.is_dir():
            print(f"  skip (no game folder): {game}")
            continue
        for name, path in built.items():
            # Named exactly as the import table spells it.
            target = game / INSTALL_NAMES.get(name, name)
            shutil.copy2(path, target)
            print(f"  {target}")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--compiler", type=Path, default=None)
    parser.add_argument("--out", type=Path, default=ROOT / "build" / "fifa07-shims")
    parser.add_argument("--package", type=Path, action="append", default=None,
                        help="package root to install into (repeatable)")
    parser.add_argument("--build-only", action="store_true")
    args = parser.parse_args()

    compiler = find_compiler(args.compiler)
    print(f"compiler: {compiler}")
    args.out.mkdir(parents=True, exist_ok=True)

    print("[1/3] building")
    built = {name: build(compiler, name, args.out) for name in SHIMS}

    print("[2/3] verifying")
    host = host_syswow64_hashes()
    for name, path in built.items():
        verify(path, name, host)

    if args.build_only:
        print("done (build only)")
        return 0

    packages = args.package or [
        ROOT / "dist" / "fifa07-diag",
        Path(os.path.expandvars(
            r"%USERPROFILE%\Desktop\NINTENDO SWITCH\NRO\fifa07-diag")),
    ]
    print("[3/3] installing into packages")
    install(built, packages)
    print("done")
    return 0


if __name__ == "__main__":
    sys.exit(main())
