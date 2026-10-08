# Deprecated: `package_fifa07.py`

This script built the shipped `dist/fifa07-nx/` package by replacing fixed-length
strings inside an already-compiled PES 2013 FEXTendo NRO taken from
`Downloads/pes13-fex/`.

It is kept only as a historical record. Do not use it.

Why it was retired:

- It rewrites a binary instead of building from this repository, so none of the
  source changes under `src/`, `patches/` or `tools/*_patches.py` reach the
  device.
- The replacement list was incomplete. The NRO shipped with 47 paths rewritten
  to `sdmc:/switch/fifa07-nx/` but three still pointing at
  `sdmc:/switch/pes13-nx/share/wine/fonts` and
  `sdmc:/switch/pes13-nx/drive_c/windows/fonts`, so Wine looks for its fonts in
  a directory that does not exist on the card.
- It ran no verification. It produced a package whose runtime files do not match
  `config/runtime-files.json` and which was missing
  `drive_c/windows/system32/winebox64.dll`.
- It wrote `run_guest_tests=1` and `run-guest-tests.txt`, the guest-stress flags,
  into a package meant to launch a game.

Replacements: `tools/package_fifa07_diag.py` (verified diagnostic package) and,
for the canonical build, `tools/release_package.py`.
