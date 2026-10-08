"""Build the FIFA FZ NSP forwarder: 39-bit no-alias, four cores, svcDebug off.

The forwarder launches OUR frontend on the SD card at
`/switch/fifa07/07z.nro`. The frontend then hands off (envSetNextLoad) to the
Wine-NX runtime with FIFA 07's executable as argv[1], so the chain
NSP -> frontend -> runtime + game is completely invisible (no Wine menu).

Why a forwarder and not a normal homebrew: the layout is chosen by the NPDM of
whatever launches the chain, not by the runtime. The chain needs the "low
window" layout the Wine-NX runtime expects: an AddressSpaceType=3 (39-bit,
no alias) process whose ASLR region starts at 0x200000, so fifa07.exe (which has
IMAGE_FILE_RELOCS_STRIPPED and only maps at its ImageBase 0x400000) still fits
below 4 GiB while the AArch64 host lives above it. That is exactly what the
runtime's own forwarder generator writes (`3u << ADDRESS_SPACE_SHIFT`) and what
its setup screen calls "a 39-bit address space". The 64-bit Homebrew Menu applet
gets a different layout (its low addresses are taken), so the frontend refuses
to launch the runtime from there.

AddressSpaceType=3 alone is not enough on this console: the project's Atmosphere
low-window patch (atmosphere/mesosphere.bin + atmosphere/kips/autorun-loader.kip)
hands the low window -- alias code region at 0x200000, native code and heap above
4 GiB -- to one program id only, HasAutorunLowWindow() = 0x0548EABB35576000, the
runtime's own generation-2 main forwarder for sdmc:/switch/wine/wine-nx-runtime.nro.
So the title id below is that id, not one derived from our NRO, and it is asserted
against the patch's constant. See docs/FORWARDER-39BIT-FIX.md.

The forwarder is a compiled AArch64 loader plus an NPDM whose address-space /
core / debug capabilities are set for full-application launches. The loader is
NOT Sphaira's stock hbl: see tools/forwarder-loader/PROVENANCE.md. Sphaira's hbl
reads the next NRO with size = g_heapSize and, on the second pass (frontend ->
runtime hand-off), that FS request is rejected with
KERNELRESULT(InvalidMemoryState) = 0xD401 and the forwarder dies with a user
break. The loader used here (the one the Wine-NX runtime installs into the
forwarders it creates) validates the NRO image size first and keeps the NRO above
4 GiB so the low window stays free.

Keys are used locally during packing only; they are never bundled.

See docs/FEXTENDO-FORWARDER.md for the pinned upstream revisions and rationale.
"""
import argparse
import hashlib
import json
import os
from pathlib import Path
import re
import shutil
import struct
import subprocess
import tempfile

from nro_assets import jpeg_dimensions

ROOT = Path(__file__).resolve().parents[1]
SPHAIRA_REV = '72a94b905816de24817594109fb012a8f7107d8c'
PACKER_REV = '745b16ecfc9ce055743067d200572204cb2aac6c'
# The loader is vendored from the Wine-NX runtime tree (see its PROVENANCE.md):
# the forwarder loader that is known to work on the console for this exact chain.
LOADER_REV = 'cbb0e4e6e7fa7f47f328d92441f51bfb507f266f'
LOADER_FILES = ('source/main.c', 'source/trampoline.s', 'source/low_window.h',
                'hbl.json', 'nx-hbloader.LICENSE.md')
# The runtime's own forwarder sets this; keep it identical so the runtime gets
# the system resource it asks for in application mode.
SYS_RESOURCE_SIZE = 16 * 1024 * 1024

# What the HOME icon launches (the hbl loader strips a leading "sdmc:").
# The icon opens OUR frontend (brand 07Z), not the Wine runtime: the chain is
# NSP -> 07z.nro -> (envSetNextLoad) runtime + fifa07.exe, all invisible.
NRO_PATH = 'sdmc:/switch/fifa07/07z.nro'
# The frontend decides the game path itself (single root constant), so no argv
# is handed to it. Kept for the report / --game override.
GAME_EXE = 'sdmc:/switch/fifa07/drive_c/FIFA 07/fifa07.exe'
USER_ARGS = ''
NEXT_ARGV = NRO_PATH if not USER_ARGS else NRO_PATH + ' ' + USER_ARGS

# The title id is NOT derived from our NRO: it is the id the console's low-window
# patch keys on. That patch (atmosphere/mesosphere.bin + atmosphere/kips/
# autorun-loader.kip, built from lowwindow/low-window/low-window.patch) adds
#     HasAutorunLowWindow(program_id) { return program_id == 0x0548EABB35576000; }
# and only for that program id moves the process's alias code region to 0x200000
# (kern_k_page_table_base.cpp) and the ASLR start to 4 GiB (ldr_process_creation.cpp).
# Every other title keeps the stock layout, whose alias code region starts at
# 0x08000000, so wine_nx_is_low_window() is false and the runtime refuses any
# fixed-low Win32 image (fifa07.exe lives at 0x400000). 07z hands the process to
# the runtime with envSetNextLoad, so the runtime runs in the process the HOME
# menu created and inherits exactly this program id: it has to be the patch's.
#
# The id is what the runtime's own generator (horizon-wine/source/forwarder.c,
# forwarder_hash() with FORWARDER_GENERATION = 2) computes for the Wine-NX
# runtime NRO -- sha256(nro + nro + "\naddress-space=3\nautorun-forwarder=2")[0:8],
# little endian, masked to 0x00FFFFFFFFFFF000, into 0x0500000000000000 -- and it
# equals AUTORUN_TITLE_ID (horizon-wine/source/forwarder_launch.h) and the id
# horizon-wine/tests/check_low_window_routing.py asserts against the patch.
LOW_WINDOW_GENERATION = 2
LOW_WINDOW_RUNTIME_NRO = 'sdmc:/switch/wine/wine-nx-runtime.nro'
# What the shipped patch matches; mesosphere/README.txt: "Only 39-bit processes
# with program ID 0548EABB35576000 receive the new layout."
LOW_WINDOW_PROGRAM_ID = 0x0548EABB35576000


def low_window_program_id():
    """The generation-2 main-forwarder id, as forwarder.c computes it."""
    key = (LOW_WINDOW_RUNTIME_NRO + LOW_WINDOW_RUNTIME_NRO +
           '\naddress-space=3\nautorun-forwarder=' + str(LOW_WINDOW_GENERATION))
    return 0x0500000000000000 | (int.from_bytes(
        hashlib.sha256(key.encode()).digest()[:8], 'little') & 0x00FFFFFFFFFFF000)


assert low_window_program_id() == LOW_WINDOW_PROGRAM_ID, hex(low_window_program_id())
TITLE_ID = LOW_WINDOW_PROGRAM_ID

DISPLAY_NAME = '07z'
AUTHOR = 'f.paolo'
VERSION = '1.0.0'
OUTPUT_NAME = 'FIFA-FZ-forwarder.nsp'


def digest(data):
    return hashlib.sha256(data).hexdigest()


def run(args, **kwargs):
    return subprocess.run([str(a) for a in args], check=True, **kwargs)


def check_npdm(data):
    """Decode the NPDM layout and both capability lists from the actual file."""
    assert data[:4] == b'META'
    assert data[12] & 1, 'The native loader must remain AArch64'
    assert (data[12] >> 1) & 7 == 3, 'Expected a 39-bit no-alias address space'
    sys_resource_size = struct.unpack_from('<I', data, 0x14)[0]
    assert sys_resource_size == SYS_RESOURCE_SIZE, sys_resource_size
    aci, acid = struct.unpack_from('<I4xI', data, 0x70)
    assert data[aci:aci + 4] == b'ACI0'
    assert data[acid + 0x200:acid + 0x204] == b'ACID'
    assert struct.unpack_from('<Q', data, aci + 0x10)[0] == TITLE_ID
    assert struct.unpack_from('<QQ', data, acid + 0x210) == (TITLE_ID, TITLE_ID)
    report = {}
    for name, base, field in [('ACI0', aci, 0x30), ('ACID', acid, 0x230)]:
        offset, size = struct.unpack_from('<II', data, base + field)
        caps = [x[0] for x in struct.iter_unpack('<I', data[base + offset:base + offset + size])]
        cores = [x for x in caps if x & 0xf == 7]
        debug = [x for x in caps if x & 0x1ffff == 0xffff]
        assert cores == [0x030073f7], (name, cores)
        # Sphaira's Disabled setting: legacy prod flag retained, the newer
        # svcDebug/force_debug bit (19) false, allow_debug false.
        assert debug == [0x0004ffff], (name, debug)
        report[name] = {'cpu_ids': [0, 1, 2, 3], 'priority_range': [28, 63],
                        'svc_debug': False, 'allow_debug': False,
                        'force_debug': False, 'force_debug_prod': True,
                        'kernel_flags': hex(cores[0]), 'debug_descriptor': hex(debug[0])}
    return report


def patch_sys_resource_size(path):
    """Set Meta.sys_resource_size, as the runtime's own forwarder does."""
    data = bytearray(path.read_bytes())
    assert data[:4] == b'META', 'Not an NPDM'
    struct.pack_into('<I', data, 0x14, SYS_RESOURCE_SIZE)
    path.write_bytes(bytes(data))


def pfs_files(data):
    assert data[:4] == b'PFS0'
    count, strings_size = struct.unpack_from('<II', data, 4)
    strings_start = 16 + count * 24
    payload_start = strings_start + strings_size
    result = {}
    for i in range(count):
        offset, size, string_offset = struct.unpack_from('<QQI', data, 16 + i * 24)
        start = strings_start + string_offset
        name = data[start:data.index(0, start, payload_start)].decode()
        assert Path(name).name == name
        assert payload_start + offset + size <= len(data)
        result[name] = data[payload_start + offset:payload_start + offset + size]
    return result


def build_nacp(nacptool, icon_bytes):
    """A complete NACP for the HOME entry, with forwarder control settings."""
    with tempfile.TemporaryDirectory(prefix='fifa07-nacp-') as tmp:
        raw = Path(tmp) / 'control.nacp'
        run([nacptool, '--create', DISPLAY_NAME, AUTHOR, VERSION, raw])
        nacp = bytearray(raw.read_bytes())
    assert len(nacp) == 0x4000, 'nacptool must emit a full 0x4000 NACP'
    # Name is repeated for every language nacptool fills; give the console
    # language a name even if nacptool stopped at 12 entries.
    for i in range(16):
        entry = i * 0x300
        if not nacp[entry:entry + 0x200].split(b'\x00', 1)[0]:
            nacp[entry:entry + 0x200] = b'\x00' * 0x200
            nacp[entry:entry + len(DISPLAY_NAME)] = DISPLAY_NAME.encode()
            nacp[entry + 0x200:entry + 0x200 + len(AUTHOR)] = AUTHOR.encode()
    # Standard forwarder control settings: the game keeps its files on SD.
    nacp[0x3025:0x3028] = bytes((0, 0, 1))  # no account prompt; on-demand add-on
    nacp[0x3036] = 0  # no save-data-loss confirmation
    nacp[0x30f1] = 0  # Automatic logo handling (no custom logo is bundled).
    nacp[0x30f2] = 0
    nacp[0x30f3] = 0  # no linked network account requirement
    for offset in (0x3080, 0x3088, 0x3090, 0x3098, 0x3148, 0x3150, 0x3158, 0x3160):
        struct.pack_into('<Q', nacp, offset, 0)  # no Switch save data
    # Title-derived ids. Sphaira and the Wine-NX runtime both fill these in when
    # they build a forwarder: the HOME menu groups the entry and its data by them.
    struct.pack_into('<Q', nacp, 0x3038, TITLE_ID)          # presence_group_id
    struct.pack_into('<Q', nacp, 0x3070, TITLE_ID ^ 0x1000)  # add_on_content_base_id
    struct.pack_into('<Q', nacp, 0x3078, TITLE_ID)          # save_data_owner_id
    struct.pack_into('<Q', nacp, 0x30F8, TITLE_ID)          # pseudo_device_id_seed
    for i in range(8):
        struct.pack_into('<Q', nacp, 0x30B0 + i * 8, TITLE_ID)  # local_communication_id
    nacp[0x30A8:0x30B0] = b'07z' + bytes(5)          # error code category
    return bytes(nacp), icon_bytes


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--keys', required=True, type=Path)
    parser.add_argument('--icon', type=Path, default=ROOT / 'frontend-nx/icon.jpg')
    parser.add_argument('--loader', type=Path, default=ROOT / 'tools/forwarder-loader')
    parser.add_argument('--sphaira', type=Path, default=ROOT / 'local/forwarder-tools/sphaira')
    parser.add_argument('--packer', type=Path, default=ROOT / 'local/forwarder-tools/hacbrewpack/hacbrewpack')
    parser.add_argument('--libnx-license', type=Path, default=ROOT / 'local/forwarder-tools/libnx-LICENSE.md')
    parser.add_argument('--work', type=Path, default=ROOT / 'local/forwarder-build-fifa07')
    parser.add_argument('--out', type=Path, default=ROOT / 'dist/fifa07-forwarder')
    args = parser.parse_args()
    for name in ('keys', 'icon', 'loader', 'sphaira', 'packer', 'libnx_license', 'work', 'out'):
        setattr(args, name, getattr(args, name).resolve())
    libnx_license = args.libnx_license.read_bytes()

    for repo, expected in [(args.sphaira, SPHAIRA_REV), (args.packer.parent, PACKER_REV)]:
        actual = subprocess.check_output(['git', '-C', str(repo), 'rev-parse', 'HEAD'], text=True).strip()
        if actual != expected:
            raise ValueError('Unexpected upstream revision: ' + str(repo))
        if subprocess.check_output(['git', '-C', str(repo), 'diff', 'HEAD', '--'], text=True):
            raise ValueError('Modified upstream source: ' + str(repo))

    icon = args.icon.read_bytes()
    width, height = jpeg_dimensions(icon)
    assert (width, height) == (256, 256), 'Forwarder icon must be 256x256'
    assert len(icon) <= 128 * 1024, 'Forwarder icon exceeds the 128 KiB budget'

    for directory in ('exefs', 'romfs', 'control', 'source/hbl/source', 'licenses'):
        (args.work / directory).mkdir(parents=True, exist_ok=True)
    args.out.mkdir(parents=True, exist_ok=True)

    nacp, icon = build_nacp(Path(str(Path(os.environ.get('DEVKITPRO', '/opt/devkitpro')))) / 'tools/bin/nacptool', icon)
    (args.work / 'control/icon_AmericanEnglish.dat').write_bytes(icon)
    (args.work / 'control/control.nacp').write_bytes(nacp)
    (args.work / 'romfs/nextNroPath').write_text(NRO_PATH)
    (args.work / 'romfs/nextArgv').write_text(NEXT_ARGV)

    # The vendored loader (see tools/forwarder-loader/PROVENANCE.md). Its files
    # are hashed so the artifact can be tied to an exact loader.
    hbl = args.loader
    loader_sha256 = {}
    for filename in LOADER_FILES:
        source = hbl / filename
        if not source.is_file():
            raise ValueError('Missing loader file: ' + str(source))
        loader_sha256[filename] = digest(source.read_bytes())
    config = json.loads((hbl / 'hbl.json').read_text())
    # 3 = 39-bit, no alias: the layout the Wine-NX runtime needs and asks for.
    config.update(name='07z', address_space_type=3,
                  title_id=hex(TITLE_ID), title_id_range_min=hex(TITLE_ID), title_id_range_max=hex(TITLE_ID))
    for cap in config['kernel_capabilities']:
        if cap['type'] == 'kernel_flags':
            cap['value'].update(highest_thread_priority=63, lowest_thread_priority=28,
                                lowest_cpu_id=0, highest_cpu_id=3)
        if cap['type'] == 'debug_flags':
            cap['value'] = dict(allow_debug=False, force_debug_prod=True, force_debug=False)
    (args.work / 'forwarder.json').write_text(json.dumps(config, indent=2) + '\n')

    devkit = Path(os.environ.get('DEVKITPRO', '/opt/devkitpro'))
    env = dict(os.environ, DEVKITPRO=str(devkit))
    cc = devkit / 'devkitA64/bin/aarch64-none-elf-gcc'
    common = ['-O2', '-march=armv8-a+crc', '-mtune=cortex-a57', '-ffixed-x18', '-fPIE',
              '-ffunction-sections', '-fdata-sections', '-D__SWITCH__',
              '-DVERSION="3.0.0"', '-isystem', devkit / 'libnx/include']
    objects = []
    for filename in ('main.c', 'trampoline.s'):
        obj = args.work / (filename + '.o')
        run([cc, *common, '-c', hbl / 'source' / filename, '-o', obj], env=env)
        objects.append(obj)
        shutil.copy2(hbl / 'source' / filename, args.work / 'source/hbl/source' / filename)
    run([cc, *common, '-specs=' + str(devkit / 'libnx/switch.specs'),
         '-Wl,-wrap,exit', *objects, '-L' + str(devkit / 'libnx/lib'), '-lnx',
         '-o', args.work / 'forwarder.elf'], env=env)
    run([devkit / 'tools/bin/elf2nso', args.work / 'forwarder.elf', args.work / 'exefs/main'])
    run([devkit / 'tools/bin/npdmtool', args.work / 'forwarder.json', args.work / 'exefs/main.npdm'])
    patch_sys_resource_size(args.work / 'exefs/main.npdm')
    npdm = check_npdm((args.work / 'exefs/main.npdm').read_bytes())

    # Restrict the temporary keyset to the two keys needed by keygeneration 1.
    selected = {}
    for line in args.keys.read_text().splitlines():
        name, separator, value = line.partition('=')
        name, value = name.strip(), value.strip()
        if separator and name in ('header_key', 'key_area_key_application_00'):
            length = 64 if name == 'header_key' else 32
            if not re.fullmatch('[0-9a-fA-F]{' + str(length) + '}', value):
                raise ValueError('Invalid required key: ' + name)
            selected[name] = value
    if len(selected) != 2:
        raise ValueError('The keyset is missing required packing keys')
    with tempfile.TemporaryDirectory(prefix='fifa07-pack-') as temporary:
        keyfile = Path(temporary) / 'keys.dat'
        keyfile.write_text(''.join(f'{k} = {v}\n' for k, v in selected.items()))
        keyfile.chmod(0o600)
        packed = run([args.packer, '--keyset', keyfile, '--titleid', f'{TITLE_ID:016x}',
                      '--nologo', '--nopatchnacplogo', '--plaintext', '--keepncadir'],
                     cwd=args.work, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True)
    (args.work / 'pack.log').write_text('\n'.join(
        line for line in packed.stdout.splitlines() if 'key area key 2:' not in line.lower()) + '\n')
    payload = (args.work / 'hacbrewpack_nsp' / f'{TITLE_ID:016x}.nsp').read_bytes()
    entries = pfs_files(payload)
    assert len(entries) == 3 and all(name.endswith('.nca') for name in entries)
    for name, content in entries.items():
        assert digest(content)[:32] == name.split('.')[0], 'NCA content ID mismatch'
    assert check_npdm((args.work / 'exefs/main.npdm').read_bytes()) == npdm
    destination = args.out / OUTPUT_NAME
    destination.write_bytes(payload)
    report = {'title': DISPLAY_NAME, 'author': AUTHOR, 'version': VERSION,
              'title_id': f'{TITLE_ID:016x}', 'nro_path': NRO_PATH,
              'next_argv': NEXT_ARGV, 'game_exe': GAME_EXE,
              'address_space': '39-bit no-alias', 'native_architecture': 'AArch64',
              'cpu_cores': 4, 'svc_debug': False, 'capabilities': npdm,
              'sys_resource_size': SYS_RESOURCE_SIZE,
              'low_window_program_id': f'{LOW_WINDOW_PROGRAM_ID:016x}',
              'low_window_source': 'Autorun low-window patch (HasAutorunLowWindow)',
              'low_window_program_id_from_generator': f'{low_window_program_id():016x}',
              'icon_sha256': digest(icon), 'icon_source': str(args.icon),
              'loader': {'source': 'Wine-NX runtime hbl (tools/forwarder-loader)',
                         'revision': LOADER_REV, 'sha256': loader_sha256},
              'sphaira_revision': SPHAIRA_REV, 'hacbrewpack_revision': PACKER_REV,
              'nsp_bytes': len(payload), 'nsp_sha256': digest(payload),
              'nca_files': {name: digest(value) for name, value in entries.items()},
              'device_tested': False}
    (args.out / 'build.json').write_text(json.dumps(report, indent=2) + '\n')
    (args.out / 'icon.jpg').write_bytes(icon)
    shutil.copytree(args.work / 'source', args.out / 'source', dirs_exist_ok=True)
    shutil.copy2(__file__, args.out / 'source/build-fifa07-forwarder.py')
    shutil.copy2(ROOT / 'tools/nro_assets.py', args.out / 'source/nro_assets.py')
    shutil.copy2(args.work / 'forwarder.json', args.out / 'source/hbl/forwarder.json')
    # Ship the vendored loader with its provenance so the artifact is auditable.
    shutil.copytree(args.loader, args.out / 'source/forwarder-loader', dirs_exist_ok=True)
    (args.out / 'licenses').mkdir(exist_ok=True)
    shutil.copy2(args.sphaira / 'LICENSE', args.out / 'licenses/Sphaira-GPL-3.0.txt')
    shutil.copy2(hbl / 'nx-hbloader.LICENSE.md', args.out / 'licenses/nx-hbloader-ISC.txt')
    (args.out / 'licenses/libnx-ISC.txt').write_bytes(libnx_license)
    print(json.dumps({'nsp': str(destination), 'bytes': len(payload),
                      'sha256': digest(payload), 'title_id': f'{TITLE_ID:016x}',
                      'next_argv': NEXT_ARGV, 'settings_verified': True}, indent=2))


if __name__ == '__main__':
    main()
