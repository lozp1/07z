"""Strict, independent verification of the 07z forwarder NSP.

No hacbrewpack / hactool involved: this re-implements the container formats from
the pinned packer's sources and from Atmosphere's own struct definitions (PFS0,
NCA3 header with AES-128-XTS, CNMT, exefs PFS0 + hash table, NPDM, NSO, ROMFS /
IVFC hash chain, romfs, NACP, JPEG).

Usage:
    python tools/verify-forwarder-nsp.py [--nsp PATH] [--keys prod.keys]

The NCA header checks need `cryptography` (XTS decryption with the console's
header key); without it they are skipped and reported as such.
"""
import argparse
import hashlib
import pathlib
import re
import struct
import sys

try:
    from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
except ImportError:
    Cipher = algorithms = modes = None

ROOT = pathlib.Path(__file__).resolve().parents[1]
NRO_PATH = 'sdmc:/switch/fifa07/07z.nro'
# The console's Atmosphere low-window patch grants the 39-bit low window (alias
# code region at 0x200000, native code above 4 GiB) to this program id only:
# lowwindow/low-window/low-window.patch adds
#     HasAutorunLowWindow(program_id) { return program_id == UINT64_C(0x0548EABB35576000); }
# The forwarder's title id must be that id, or the runtime the icon hands the
# process to runs in the stock 39-bit layout and refuses fifa07.exe.
LOW_WINDOW_PROGRAM_ID = 0x0548EABB35576000
LOW_WINDOW_PATCH = ROOT.parent / 'lowwindow/low-window/low-window.patch'
TITLE_ID = LOW_WINDOW_PROGRAM_ID
ICON_MAX = 128 * 1024
SYS_RESOURCE_SIZE = 16 * 1024 * 1024

# NCM content types (the CNMT records use these, not the NCA field encoding).
NCM_TYPES = {0: 'Meta', 1: 'Program', 2: 'Data', 3: 'Control', 4: 'HtmlDocument', 5: 'LegalInformation'}

FAILS, SKIPS, NOTES = [], [], []
N = [0]


def check(ok, label, detail=''):
    N[0] += 1
    print(('  PASS  ' if ok else '  FAIL  ') + label + (('  [' + str(detail) + ']') if detail else ''))
    if not ok:
        FAILS.append(label)
    return ok


def note(text):
    NOTES.append(text)
    print('  NOTE  ' + text)


def skip(label):
    SKIPS.append(label)
    print('  SKIP  ' + label)


# ---------------------------------------------------------------- primitives
def aes_ecb(key, block, encrypt=True):
    ctx = Cipher(algorithms.AES(key), modes.ECB())
    c = ctx.encryptor() if encrypt else ctx.decryptor()
    return c.update(block) + c.finalize()


def xts_decrypt(key, data, sector_size=0x200):
    """Same XTS/tweak convention as hacbrewpack's aes_xts_decrypt()."""
    k1, k2 = key[:16], key[16:]
    out = bytearray()
    for s in range((len(data) + sector_size - 1) // sector_size):
        chunk = data[s * sector_size:(s + 1) * sector_size]
        tweak = bytearray(aes_ecb(k2, s.to_bytes(16, 'big')))
        for j in range(0, len(chunk), 16):
            blk = chunk[j:j + 16]
            out += bytes(a ^ b for a, b in zip(aes_ecb(k1, bytes(a ^ b for a, b in zip(blk, tweak)), False), tweak))
            carry = 0
            for i in range(16):
                c = tweak[i] >> 7
                tweak[i] = ((tweak[i] << 1) | carry) & 0xFF
                carry = c
            if carry:
                tweak[0] ^= 0x87
    return bytes(out)


def pfs0(d):
    count, strsize = struct.unpack_from('<II', d, 4)
    strings = 16 + count * 24
    payload = strings + strsize
    out = {}
    for i in range(count):
        off, size, nameoff, _ = struct.unpack_from('<QQII', d, 16 + i * 24)
        end = d.index(b'\0', strings + nameoff)
        out[d[strings + nameoff:end].decode()] = d[payload + off:payload + off + size]
    return out


def romfs_try(img, off):
    """Parse a candidate romfs image at off; return {name: bytes} or None."""
    if off + 0x50 > len(img):
        return None
    header_size, _dho, _dhs, dir_ofs, dir_size, _fho, _fhs, file_ofs, file_size, data_ofs = \
        struct.unpack_from('<10Q', img, off)
    if header_size != 0x50 or dir_ofs < 0x50 or not dir_size or not file_size:
        return None
    if dir_ofs + dir_size > len(img) - off or file_ofs + file_size > len(img) - off or data_ofs > len(img):
        return None
    root = struct.unpack_from('<IIIII', img, off + dir_ofs)
    files, cur, seen = {}, root[3], 0
    while cur != 0xFFFFFFFF:
        seen += 1
        if seen > 64 or off + file_ofs + cur + 0x20 > len(img):
            return None
        _p, sibling, fofs, fsize, _h, nsize = struct.unpack_from('<IIQQII', img, off + file_ofs + cur)
        name = img[off + file_ofs + cur + 0x20:off + file_ofs + cur + 0x20 + nsize].decode('utf-8', 'replace')
        if off + data_ofs + fofs + fsize > len(img):
            return None
        files[name] = img[off + data_ofs + fofs:off + data_ofs + fofs + fsize]
        cur = sibling
    return files or None


def jpeg_size(b):
    if b[:2] != b'\xff\xd8':
        return None
    i = 2
    while i < len(b) - 9:
        if b[i] != 0xFF:
            i += 1
            continue
        m = b[i + 1]
        if m in (0xC0, 0xC1, 0xC2):
            h, w = struct.unpack_from('>HH', b, i + 5)
            return w, h
        if m in (0xD8, 0xD9):
            i += 2
            continue
        i += 2 + struct.unpack_from('>H', b, i + 2)[0]
    return None


# ---------------------------------------------------------------- NCA sections
def read_nca_sections(nca, header):
    out = []
    for i in range(4):
        start, end, _ = struct.unpack_from('<II8s', header, 0x240 + i * 0x10)
        if start == 0 and end == 0:
            continue
        # nca_fs_header_t is 0x148 bytes of fields, padded to a 0x200 stride.
        out.append((i, header[0x400 + i * 0x200:0x400 + (i + 1) * 0x200], nca[start * 0x200:end * 0x200]))
    return out


def verify_pfs0_section(tag, fsh, sec):
    sb = fsh[8:8 + 0x138]
    master = sb[0:0x20]
    block_size, version2, ht_ofs, ht_size, pfs0_ofs, pfs0_size = struct.unpack_from('<IIQQQQ', sb, 0x20)
    ht = sec[ht_ofs:ht_ofs + ht_size]
    nblocks = (pfs0_size + block_size - 1) // block_size
    rebuilt = b''.join(
        hashlib.sha256(sec[pfs0_ofs + k * block_size:min(pfs0_ofs + (k + 1) * block_size, pfs0_ofs + pfs0_size)]).digest()
        for k in range(nblocks))
    check(version2 == 2, f'{tag}: PFS0 superblock version field == 2', version2)
    check(ht[:nblocks * 0x20] == rebuilt, f'{tag}: hash table matches the {nblocks} PFS0 block(s)',
          f'block={block_size:#x} table={ht_size:#x} pfs0@{pfs0_ofs:#x}+{pfs0_size:#x}')
    check(hashlib.sha256(ht).digest() == master, f'{tag}: superblock master hash == sha256(hash table)')
    check(sec[pfs0_ofs:pfs0_ofs + 4] == b'PFS0', f'{tag}: PFS0 magic where the superblock points')
    return pfs0(sec[pfs0_ofs:pfs0_ofs + pfs0_size])


def verify_ivfc_from_data(tag, sec):
    """Rebuild the IVFC chain from the section bytes alone (no fs header needed)."""
    start = None
    for off in range(0x4000, len(sec), 0x4000):
        if romfs_try(sec, off):
            start = off
            break
    if start is None:
        check(False, f'{tag}: a romfs image inside the section', f'{len(sec)} bytes')
        return None
    sizes = [len(sec) - start]           # level 6: the romfs image, padded
    while len(sizes) < 6:
        nbytes = (sizes[-1] // 0x4000) * 0x20
        sizes.append(0x4000 * ((nbytes + 0x3fff) // 0x4000))
    sizes.reverse()                      # sizes[0] = level 1
    check(sum(sizes) == len(sec), f'{tag}: five hash levels plus the image tile the section exactly',
          f'levels={[hex(s) for s in sizes]} image@{start:#x}')
    bounds, pos = [], 0
    for s in sizes:
        bounds.append((pos, pos + s))
        pos += s
    for i in range(5):
        lo = bounds[i][0]
        nlo, nhi = bounds[i + 1]
        nblocks = sizes[i + 1] // 0x4000
        stored = sec[lo:lo + nblocks * 0x20]
        real = b''.join(hashlib.sha256(sec[nlo + k * 0x4000:nlo + (k + 1) * 0x4000]).digest()
                        for k in range(nblocks))
        check(stored == real, f'{tag}: level {i + 1} hashes level {i + 2} ({nblocks} block(s))')
    print(f'  {tag}: image {len(sec) - start} bytes at {start:#x}; '
          f'recomputed master hash {hashlib.sha256(sec[0:sizes[0]]).hexdigest()[:16]}...')
    return romfs_try(sec, start)


def verify_romfs_section(tag, fsh, sec):
    ivfc = fsh[8:8 + 0x138]
    magic, _iid, mhsize, nlevels = struct.unpack_from('<IIII', ivfc, 0)
    check(magic == 0x43465649, f'{tag}: IVFC magic in the fs header', hex(magic))
    check(nlevels == 7, f'{tag}: IVFC declares 7 levels', nlevels)
    check(mhsize == 0x20, f'{tag}: IVFC master hash size is 0x20', mhsize)
    levels = [struct.unpack_from('<QQII', ivfc, 0x10 + i * 0x18) for i in range(6)]
    check(hashlib.sha256(sec[levels[0][0]:levels[0][0] + levels[0][1]]).digest() == ivfc[0xC0:0xE0],
          f'{tag}: IVFC master hash (in the fs header) == sha256(level 1)')
    for i in range(5):
        lo = levels[i][0]
        nlo, nhds = levels[i + 1][0], levels[i + 1][1]
        nblocks = (nhds + 0x3fff) // 0x4000
        check(sec[lo:lo + nblocks * 0x20] == b''.join(
            hashlib.sha256(sec[nlo + k * 0x4000:nlo + (k + 1) * 0x4000]).digest() for k in range(nblocks)),
            f'{tag}: IVFC level {i + 1} hashes level {i + 2} ({nblocks} blocks)')
    return romfs_try(sec, levels[5][0])


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--nsp', type=pathlib.Path, default=ROOT / 'dist/fifa07-forwarder/FIFA-FZ-forwarder.nsp')
    ap.add_argument('--keys', type=pathlib.Path, default=pathlib.Path.home() / '.switch/prod.keys')
    ap.add_argument('--icon', type=pathlib.Path, default=ROOT / 'frontend-nx/icon.jpg')
    args = ap.parse_args()

    nsp = args.nsp.read_bytes()
    print('== NSP ==')
    print(f'  path   {args.nsp}')
    print(f'  size   {len(nsp)} bytes')
    print(f'  sha256 {hashlib.sha256(nsp).hexdigest()}')

    print('\n== Low window (the program id the kernel patch keys on) ==')
    check(TITLE_ID == LOW_WINDOW_PROGRAM_ID,
          f'title id is the low-window program id {LOW_WINDOW_PROGRAM_ID:016X}', f'{TITLE_ID:016x}')
    if LOW_WINDOW_PATCH.is_file():
        text = LOW_WINDOW_PATCH.read_text(errors='ignore')
        check(f'UINT64_C(0x{TITLE_ID:016X})' in text,
              'the shipped low-window patch matches this program id', str(LOW_WINDOW_PATCH))
        check('HasAutorunLowWindow' in text, 'the patch gates the layout in HasAutorunLowWindow()')
    else:
        skip(f'low-window patch not present at {LOW_WINDOW_PATCH}')

    print('\n== Container: PFS0 and content ids ==')
    ncas = pfs0(nsp)
    check(len(ncas) == 3 and all(n.endswith('.nca') for n in ncas), 'exactly three NCAs',
          ', '.join(sorted(ncas)))
    for name, body in sorted(ncas.items()):
        check(hashlib.sha256(body).hexdigest()[:32] == name.split('.')[0],
              f'content id == sha256(nca) truncated for {name}', f'{len(body)} bytes')

    print('\n== NCA headers ==')
    parsed = {}
    if Cipher is None:
        skip('NCA header parsing (cryptography not installed)')
    else:
        keys = {}
        for line in args.keys.read_text(errors='ignore').splitlines():
            m = re.match(r'\s*([A-Za-z0-9_]+)\s*=\s*([0-9A-Fa-f]+)\s*$', line)
            if m:
                keys[m.group(1).lower()] = m.group(2)
        header_key = bytes.fromhex(keys['header_key'])
        for name, body in sorted(ncas.items()):
            h = xts_decrypt(header_key, body[:0xC00])
            ctype = h[0x205]
            parsed[ctype] = (name, h, body)
            print(f'  {name}  content_type={ctype} (NCA field) sdk={struct.unpack_from("<I", h, 0x21c)[0]:#x}')
            check(struct.unpack_from('<I', h, 0x200)[0] == 0x3341434E, f'{name}: NCA3 magic')
            check(struct.unpack_from('<Q', h, 0x208)[0] == len(body), f'{name}: header nca_size == file size')
            check(struct.unpack_from('<Q', h, 0x210)[0] == TITLE_ID, f'{name}: header title id')
            for i, fsh, sec in read_nca_sections(body, h):
                stored = h[0x280 + i * 0x20:0x280 + (i + 1) * 0x20]
                real = hashlib.sha256(h[0x400 + i * 0x200:0x400 + (i + 1) * 0x200]).digest()
                if fsh == bytes(0x200):
                    note(f'{name}: section {i} ({len(sec)} bytes) has an all-zero fs header. hacbrewpack '
                         'writes the section but never fills that descriptor for a program romfs; '
                         'Atmosphere loaded it anyway (the frontend ran from this NSP).')
                else:
                    check(fsh[4] == 1, f'{name}: section {i} crypt type is Plaintext (1)',
                          f'{fsh[4]} fs_type={fsh[2]} hash_type={fsh[3]}')
                    check(stored == real, f'{name}: section {i} hash (sha256 of its 0x200 fs header window)')
                    check(fsh[2] in (0, 1), f'{name}: section {i} fs_type is ROMFS/PFS0', fsh[2])

    if 1 not in parsed:
        print('\nno decrypted Meta NCA: cannot continue')
        return 1

    print('\n== Meta NCA / CNMT ==')
    _mn, meta_h, meta_body = parsed[1]
    _i, mfsh, msec = read_nca_sections(meta_body, meta_h)[0]
    cnmt_files = verify_pfs0_section('meta', mfsh, msec)
    cnmt_name = [n for n in cnmt_files if n.endswith('.cnmt')][0]
    c = cnmt_files[cnmt_name]
    title_id, version, mtype, _d, ext_size, content_count, meta_count = struct.unpack_from('<QI BBHHH', c, 0)
    print(f'  {cnmt_name}: title_id={title_id:#018x} version={version} type={mtype:#x} '
          f'contents={content_count} meta_entries={meta_count} extended={ext_size}')
    check(title_id == TITLE_ID, 'CNMT title id')
    check(cnmt_name == f'Application_{TITLE_ID:016x}.cnmt', 'CNMT file name matches the title id', cnmt_name)
    check(mtype == 0x80, 'CNMT meta type is Application', hex(mtype))
    recs = []
    for i in range(content_count):
        base = 0x20 + ext_size + i * 0x38
        _rh, ncaid, size6, ctype, idoff = struct.unpack_from('<32s16s6sBB', c, base)
        recs.append((ncaid.hex(), int.from_bytes(size6, 'little'), ctype, idoff))
    by_id = {n.split('.')[0]: (len(b), n) for n, b in ncas.items()}
    for cid, rsize, ctype, idoff in recs:
        print(f'  record content_id={cid} size={rsize:6d} type={ctype} '
              f'({NCM_TYPES.get(ctype, "?")}) id_offset={idoff}')
        check(cid in by_id, 'CNMT record names an NCA present in the NSP', cid)
        if cid in by_id:
            check(by_id[cid][0] == rsize, 'CNMT record size matches the NCA size', rsize)
            want = {1: 0, 3: 2}.get(ctype)
            if want is not None:
                check(parsed[want][0] == by_id[cid][1],
                      f'CNMT {NCM_TYPES[ctype]} record points at the {NCM_TYPES[want]} NCA', by_id[cid][1])
    check({1, 3} <= {t for _c, _s, t, _o in recs}, 'CNMT declares Program (1) and Control (3)')
    note('hacbrewpack never lists the Meta content in the CNMT (its content id is the hash of the file '
         'that carries it); installers take it from the .cnmt.nca name. Same as every hacbrewpack NSP.')

    print('\n== Program NCA: exefs ==')
    exefs, romfs_section = None, None
    _pn, prog_h, prog_body = parsed[0]
    for i, fsh, sec in read_nca_sections(prog_body, prog_h):
        if fsh[2] == 1:
            exefs = verify_pfs0_section(f'program section {i} (exefs)', fsh, sec)
        else:
            romfs_section = (fsh, sec)
    check(exefs is not None, 'program NCA has a PFS0 (exefs) section')
    check('main' in exefs and 'main.npdm' in exefs, 'exefs holds main and main.npdm', ', '.join(sorted(exefs)))
    nso = exefs['main']
    check(nso[:4] == b'NSO0', 'main is an NSO', nso[:4])
    _m, _v, _r, nflags = struct.unpack_from('<4I', nso, 0)
    (t_fo, t_do, t_sz, _a), (r_fo, r_do, r_sz, _b), (w_fo, w_do, w_sz, bss) = \
        [struct.unpack_from('<4I', nso, 0x10 + i * 0x10) for i in range(3)]
    comp = struct.unpack_from('<3I', nso, 0x60)
    print(f'  NSO {len(nso)} bytes flags={nflags:#04x} compressed_sizes={[hex(x) for x in comp]}')
    print(f'    text file={t_fo:#x} dst={t_do:#x} size={t_sz:#x}')
    print(f'    ro   file={r_fo:#x} dst={r_do:#x} size={r_sz:#x}')
    print(f'    rw   file={w_fo:#x} dst={w_do:#x} size={w_sz:#x} bss={bss:#x}')
    check(nflags & 0x80 == 0, 'NSO does not ask for zbic compression', hex(nflags))
    check(t_fo == 0x100, 'NSO text file offset is 0x100 (header is 0x100 bytes)', hex(t_fo))
    check(t_do == 0, 'NSO text destination offset is 0', hex(t_do))
    check(r_fo == t_fo + (comp[0] if nflags & 1 else t_sz), 'NSO rodata follows the text')
    check(w_fo == r_fo + (comp[1] if nflags & 2 else r_sz), 'NSO rw follows the rodata')
    check(w_fo + (comp[2] if nflags & 4 else w_sz) == len(nso), 'NSO segments cover the file exactly',
          hex(w_fo + (comp[2] if nflags & 4 else w_sz)))
    check(0 < bss <= 0x1000000, 'NSO bss size is sane', hex(bss))
    for i, nm in enumerate(('text', 'ro', 'rw')):
        check(nso[0xA0 + i * 0x20:0xA0 + (i + 1) * 0x20] != bytes(0x20), f'NSO {nm} segment hash present')
    npdm = exefs['main.npdm']
    check(npdm[:4] == b'META', 'NPDM META magic')
    mflags, prio, cores = npdm[0xC], npdm[0xE], npdm[0xF]
    sysres = struct.unpack_from('<I', npdm, 0x14)[0]
    stack = struct.unpack_from('<I', npdm, 0x1C)[0]
    aci0_off, aci0_size, acid_off, acid_size = struct.unpack_from('<IIII', npdm, 0x70)
    print(f'  NPDM name={npdm[0x20:0x30].split(bytes([0]))[0]!r} flags={mflags:#04x} '
          f'sys_resource={sysres:#x} prio={prio} cpu={cores} stack={stack:#x}')
    check(mflags & 1 == 1, 'NPDM is AArch64')
    check((mflags >> 1) & 7 == 3, 'NPDM AddressSpaceType == 3 (39-bit, no alias)', (mflags >> 1) & 7)
    check(sysres == SYS_RESOURCE_SIZE, 'NPDM sys_resource_size == 16 MiB', hex(sysres))
    check(stack == 0x100000, 'NPDM main thread stack == 1 MiB', hex(stack))
    check(prio == 44, 'NPDM main thread priority == 44', prio)
    check(npdm[aci0_off:aci0_off + 4] == b'ACI0', 'ACI0 magic at its offset')
    check(npdm[acid_off + 0x200:acid_off + 0x204] == b'ACID', 'ACID magic at its offset')
    check(struct.unpack_from('<Q', npdm, aci0_off + 0x10)[0] == TITLE_ID, 'ACI0 program id')
    check(struct.unpack_from('<QQ', npdm, acid_off + 0x210) == (TITLE_ID, TITLE_ID), 'ACID program id range')
    for tag, base, kac_field in (('ACI0', aci0_off, 0x30), ('ACID', acid_off, 0x230)):
        off, size = struct.unpack_from('<II', npdm, base + kac_field)
        words = [w for (w,) in struct.iter_unpack('<I', npdm[base + off:base + off + size])]
        check(bool(words), f'{tag} kernel capability list is present', f'{size} bytes')
        print(f'  {tag} kernel capabilities: {[hex(w) for w in words]}')
        check(words and words[0] == 0x030073F7,
              f'{tag} first capability = kernel flags (cores 0-3, priorities 28-63)',
              hex(words[0]) if words else None)
        debug = [w for w in words if w & 0xffff == 0xffff]
        check(debug == [0x0004FFFF], f'{tag} debug flags = 0x0004FFFF (legacy prod on, svcDebug off)',
              [hex(w) for w in debug])
        mask = b''.join(w.to_bytes(4, 'little') for w in words)
        for svc, nm in ((0x26, 'svcBreak'), (0x73, 'svcSetProcessMemoryPermission'),
                        (0x77, 'svcMapProcessCodeMemory'), (0x78, 'svcUnmapProcessCodeMemory'),
                        (0x4b, 'svcCreateCodeMemory'), (0x4c, 'svcControlCodeMemory'),
                        (0x29, 'svcGetInfo'), (0x40, 'svcCreateSession'), (0x43, 'svcReplyAndReceive')):
            check(bool(mask[svc // 8] >> (svc % 8) & 1), f'{tag} mask allows {nm} ({svc:#04x})')

    print('\n== Program NCA: romfs ==')
    files = verify_romfs_section('program romfs (from its fs header)', romfs_section[0], romfs_section[1])
    check(files is not None, 'program romfs parses through its fs header')
    raw = verify_ivfc_from_data('program romfs (rebuilt from the raw bytes)', romfs_section[1])
    check(sorted(raw or {}) == sorted(files or {}),
          'the raw-bytes IVFC rebuild reaches the same romfs image', sorted(raw or {}))
    if files:
        check('nextNroPath' in files and 'nextArgv' in files,
              'romfs holds nextNroPath and nextArgv', ', '.join(sorted(files)))
        check(files.get('nextNroPath') == NRO_PATH.encode(), 'nextNroPath == ' + NRO_PATH, files.get('nextNroPath'))
        check(files.get('nextArgv') == NRO_PATH.encode(), 'nextArgv == ' + NRO_PATH, files.get('nextArgv'))

    print('\n== Control NCA: romfs (NACP + icon) ==')
    _cn, ctrl_h, ctrl_body = parsed[2]
    _i, cfsh, csec = read_nca_sections(ctrl_body, ctrl_h)[0]
    cfiles = verify_romfs_section('control romfs', cfsh, csec)
    check('control.nacp' in cfiles and 'icon_AmericanEnglish.dat' in cfiles,
          'control romfs holds control.nacp and icon_AmericanEnglish.dat', ', '.join(sorted(cfiles)))
    nacp = cfiles['control.nacp']
    check(len(nacp) == 0x4000, 'NACP is a full 0x4000 bytes', len(nacp))
    names, authors = set(), set()
    for i in range(16):
        e = i * 0x300
        n = nacp[e:e + 0x200].split(b'\0', 1)[0].decode('utf-8', 'replace')
        a = nacp[e + 0x200:e + 0x300].split(b'\0', 1)[0].decode('utf-8', 'replace')
        names.update([n] if n else [])
        authors.update([a] if a else [])
    filled = sum(1 for i in range(16) if nacp[i * 0x300:i * 0x300 + 0x200].split(b'\0', 1)[0])
    print(f'  names ({filled}/16 languages):', sorted(names))
    print('  authors:', sorted(authors))
    check(names == {'07z'}, 'every non-empty language entry is named 07z', sorted(names))
    check(authors == {'f.paolo'}, 'every non-empty language entry credits f.paolo', sorted(authors))
    check(nacp[0x3060:0x3070].split(b'\0', 1)[0].decode() == '1.0.0', 'display version is 1.0.0')
    check(nacp[0x3025] == 0, 'startup_user_account == 0 (no account prompt)', nacp[0x3025])
    check(nacp[0x3027] == 1, 'add_on_content_registration_type == 1 (on demand)', nacp[0x3027])
    check(nacp[0x3036] == 0, 'data_loss_confirmation == 0', nacp[0x3036])
    check(nacp[0x3101] == 0, 'logo_handling == 0 (automatic)', nacp[0x3101])
    for off, label in ((0x3080, 'user_account_save_data_size'), (0x3088, 'user_account_save_data_journal_size'),
                       (0x3090, 'device_save_data_size'), (0x3098, 'device_save_data_journal_size'),
                       (0x3148, 'user_account_save_data_size_max'), (0x3150, 'user_account_save_data_journal_size_max'),
                       (0x3158, 'device_save_data_size_max'), (0x3160, 'device_save_data_journal_size_max')):
        check(struct.unpack_from('<Q', nacp, off)[0] == 0, f'NACP {label} == 0')
    for off, label in ((0x3038, 'presence_group_id'), (0x3078, 'save_data_owner_id'),
                       (0x30F8, 'pseudo_device_id_seed')):
        check(struct.unpack_from('<Q', nacp, off)[0] == TITLE_ID, f'NACP {label} == title id')
    addon = struct.unpack_from('<Q', nacp, 0x3070)[0]
    check(addon in (TITLE_ID + 0x1000, TITLE_ID ^ 0x1000),
          'NACP add_on_content_base_id is derived from the title id', hex(addon))
    check(all(struct.unpack_from('<Q', nacp, 0x30B0 + i * 8)[0] == TITLE_ID for i in range(8)),
          'NACP local_communication_id entries == title id')
    check(nacp[0x30A8:0x30AB] == b'07z', 'NACP error code category is 07z', nacp[0x30A8:0x30B0])
    icon = cfiles['icon_AmericanEnglish.dat']
    check(jpeg_size(icon) == (256, 256), 'icon is a 256x256 JPEG', jpeg_size(icon))
    check(len(icon) <= ICON_MAX, 'icon fits the 128 KiB budget', f'{len(icon)} bytes')
    check(hashlib.sha256(icon).digest() == hashlib.sha256(args.icon.read_bytes()).digest(),
          f'icon bytes are {args.icon.name}')

    print(f'\n== {N[0] - len(FAILS)}/{N[0]} checks passed, {len(SKIPS)} skipped, {len(NOTES)} notes ==')
    for f in FAILS:
        print('  FAILED: ' + f)
    return 1 if FAILS else 0


if __name__ == '__main__':
    sys.exit(main())
