import os
import shutil
import struct
import re

PES_SOURCE = r"C:\Users\f.paolo\Downloads\pes13-fex"
GAME_SOURCE = r"C:\Users\f.paolo\Desktop\NINTENDO SWITCH\NRO\FIFA 07 (Steam Deck)\FIFA 07"
DIST_DIR = r"C:\Projects\ports\fifa07\dist\fifa07-nx"
DESKTOP_DIR = r"C:\Users\f.paolo\Desktop\NINTENDO SWITCH\NRO\fifa07-nx"

print("=== Building FIFA 07 standalone port package ===")

# 1. Clean / create dist directory
if os.path.exists(DIST_DIR):
    shutil.rmtree(DIST_DIR)
os.makedirs(DIST_DIR, exist_ok=True)

# 2. Patch NRO binary
print("[1/6] Patching NRO binary for FIFA 07...")
nro_in_path = os.path.join(PES_SOURCE, "pes13-fex.nro")
nro_out_path = os.path.join(DIST_DIR, "fifa07-nx.nro")

with open(nro_in_path, "rb") as f:
    nro_data = bytearray(f.read())

# Binary patch string replacements (exact lengths):
# 'pes13-fex' (9 bytes) -> 'fifa07-nx' (9 bytes)
# 'sdmc:/switch/pes13-fex/drive_c/PES13/pes2013.exe' (47 bytes) -> 'sdmc:/switch/fifa07-nx/drive_c/FIFA07/fifa07.exe' (47 bytes)
# 'PES13/pes2013.keys.txt' (22 bytes) -> 'FIFA07/fifa07.keys.txt' (22 bytes)
# 'PES13/pes2013.csmt.txt' (22 bytes) -> 'FIFA07/fifa07.csmt.txt' (22 bytes)
# 'PES13' -> 'FIFA07' where appropriate
replacements = [
    (b"sdmc:/switch/pes13-fex/drive_c/PES13/pes2013.exe", b"sdmc:/switch/fifa07-nx/drive_c/FIFA07/fifa07.exe"),
    (b"PES13/pes2013.keys.txt", b"FIFA07/fifa07.keys.txt"),
    (b"PES13/pes2013.csmt.txt", b"FIFA07/fifa07.csmt.txt"),
    (b"Fextendo could not start PES13", b"Fextendo could not run FIFA07 "),
    (b"pes13-fex", b"fifa07-nx"),
]

for src, dst in replacements:
    assert len(src) == len(dst), f"Length mismatch: {src} vs {dst}"
    count = nro_data.count(src)
    nro_data = bytearray(nro_data.replace(src, dst))
    print(f"  Replaced '{src.decode('latin1')}' -> '{dst.decode('latin1')}' ({count} times)")

# Update NACP in ASET section
nro_size = struct.unpack("<I", nro_data[0x18:0x1c])[0]
if len(nro_data) > nro_size and nro_data[nro_size:nro_size+4] == b"ASET":
    aset_bytes = nro_data[nro_size:]
    icon_off, icon_sz, nacp_off, nacp_sz, romfs_off, romfs_sz = struct.unpack("<QQQQQQ", aset_bytes[8:56])
    nacp_start = nro_size + nacp_off
    print(f"  Found NACP at offset {hex(nacp_start)}")
    
    # Each language entry is 0x300 bytes: 0x200 (512) title, 0x100 (256) author
    new_title = "FIFA 07".encode("utf-8")
    new_author = "EA SPORTS".encode("utf-8")
    
    for lang in range(16):
        entry_offset = nacp_start + lang * 0x300
        # Zero out old title and author
        nro_data[entry_offset:entry_offset + 0x300] = b"\x00" * 0x300
        nro_data[entry_offset:entry_offset + len(new_title)] = new_title
        nro_data[entry_offset + 0x200:entry_offset + 0x200 + len(new_author)] = new_author

with open(nro_out_path, "wb") as f:
    f.write(nro_data)
print(f"  Saved patched NRO: {nro_out_path} ({len(nro_data)} bytes)")

# 3. Create configuration.ini and direct boot bypass flag
print("[2/6] Configuring direct boot (no launcher)...")
config_content = """[runtime]
fex_fast=1
fex_fastest=1
fex_diskcache=0
fex_fast_api=1
run_guest_tests=1
"""
with open(os.path.join(DIST_DIR, "configuration.ini"), "w", encoding="utf-8") as f:
    f.write(config_content)

# Flag file that forces immediate boot without launcher UI
with open(os.path.join(DIST_DIR, "run-guest-tests.txt"), "w", encoding="utf-8") as f:
    f.write("1\n")

# Copy FEX flags
fex_flags = [
    "fex_auto_core3", "fex_diskcache", "fex_dxvk_balance", "fex_dxvk_core3",
    "fex_fast_api", "fex_hot_profile", "fex_jit_large", "fex_jit_small",
    "fex_polling", "fex_short_trace_off"
]
for flag in fex_flags:
    flag_src = os.path.join(PES_SOURCE, flag)
    flag_dst = os.path.join(DIST_DIR, flag)
    if os.path.exists(flag_src):
        shutil.copy2(flag_src, flag_dst)
    else:
        with open(flag_dst, "wb") as f:
            f.write(b"1\n")

# 4. Registry files
print("[3/6] Setting up Windows registry for FIFA 07...")
fifa_reg = """WINE REGISTRY Version 2

[Software\\\\EA SPORTS\\\\FIFA 07]
"DisplayName"="FIFA 07"
"Install Dir"="C:\\\\FIFA07\\\\"
"Installed From"="D:\\\\"
"Language"="English UK"
"Locale"="en_uk"
"CD Drive"="D:\\\\"

[Software\\\\Wow6432Node\\\\EA SPORTS\\\\FIFA 07]
"DisplayName"="FIFA 07"
"Install Dir"="C:\\\\FIFA07\\\\"
"Installed From"="D:\\\\"
"Language"="English UK"
"Locale"="en_uk"
"CD Drive"="D:\\\\"
"""
with open(os.path.join(DIST_DIR, "fifa07-install.reg"), "w", encoding="utf-8") as f:
    f.write(fifa_reg)
with open(os.path.join(DIST_DIR, "pes13-install.reg"), "w", encoding="utf-8") as f:
    f.write(fifa_reg)

# system.reg & user.reg
system_reg_src = os.path.join(PES_SOURCE, "system.reg")
if os.path.exists(system_reg_src):
    with open(system_reg_src, "r", encoding="utf-8", errors="ignore") as f:
        sys_reg_content = f.read()
    
    fifa_sys_reg_addition = """
[Software\\\\EA SPORTS\\\\FIFA 07] 1790193100
#time=1dd4b94f34aee00
"DisplayName"="FIFA 07"
"Install Dir"="C:\\\\FIFA07\\\\"
"Language"="English UK"
"Locale"="en_uk"

[Software\\\\Wow6432Node\\\\EA SPORTS\\\\FIFA 07] 1790193100
#time=1dd4b94f34aee00
"DisplayName"="FIFA 07"
"Install Dir"="C:\\\\FIFA07\\\\"
"Language"="English UK"
"Locale"="en_uk"
"""
    with open(os.path.join(DIST_DIR, "system.reg"), "w", encoding="utf-8") as f:
        f.write(sys_reg_content + fifa_sys_reg_addition)

user_reg_src = os.path.join(PES_SOURCE, "user.reg")
if os.path.exists(user_reg_src):
    shutil.copy2(user_reg_src, os.path.join(DIST_DIR, "user.reg"))

# 5. Copy Wine runtime system and share folders
print("[4/6] Copying Wine runtime and shared system files...")
shutil.copytree(os.path.join(PES_SOURCE, "drive_c", "windows"),
                os.path.join(DIST_DIR, "drive_c", "windows"), dirs_exist_ok=True)
shutil.copytree(os.path.join(PES_SOURCE, "drive_c", "dxvk"),
                os.path.join(DIST_DIR, "drive_c", "dxvk"), dirs_exist_ok=True)
shutil.copytree(os.path.join(PES_SOURCE, "share"),
                os.path.join(DIST_DIR, "share"), dirs_exist_ok=True)

# 6. Copy FIFA 07 game files
print("[5/6] Copying FIFA 07 game files...")
fifa_game_dest = os.path.join(DIST_DIR, "drive_c", "FIFA07")
shutil.copytree(GAME_SOURCE, fifa_game_dest, dirs_exist_ok=True)

# Also ensure DXVK d3d9.dll is in the game directory
dxvk_d3d9 = os.path.join(PES_SOURCE, "drive_c", "dxvk", "d3d9.dll")
if os.path.exists(dxvk_d3d9):
    shutil.copy2(dxvk_d3d9, os.path.join(fifa_game_dest, "d3d9.dll"))

# Copy dxvk.conf and fifa07.wine-nx.txt
dxvk_conf = os.path.join(PES_SOURCE, "launcher", "presets", "dxvk.conf")
if os.path.exists(dxvk_conf):
    shutil.copy2(dxvk_conf, os.path.join(fifa_game_dest, "dxvk.conf"))

# Create mirror directory "FIFA 07" with space just in case
fifa_space_dest = os.path.join(DIST_DIR, "drive_c", "FIFA 07")
shutil.copytree(fifa_game_dest, fifa_space_dest, dirs_exist_ok=True)

# 7. Mirror to Desktop for convenient access
print("[6/6] Mirroring package to Desktop: C:\\Users\\f.paolo\\Desktop\\NINTENDO SWITCH\\NRO\\fifa07-nx ...")
if os.path.exists(DESKTOP_DIR):
    shutil.rmtree(DESKTOP_DIR)
shutil.copytree(DIST_DIR, DESKTOP_DIR, dirs_exist_ok=True)

print("=== Package build completed successfully! ===")
