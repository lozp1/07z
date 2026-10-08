#!/usr/bin/env bash
# Restaura el estado FUNCIONAL del port 07z (antes del experimento de 2 jugadores).
# Uso:  bash restaurar-funcional.sh <letra_sd>        ej:  bash restaurar-funcional.sh D
#
# Devuelve: el runtime que funciona, los 3 ficheros de teclas, la config del juego
# y el settings.json, y borra cualquier keys2.txt que hubiera quedado.
set -e
SD=$(echo "${1:-D}" | tr -d ':/')
P="/$SD/switch/fifa07"
B="/$SD/07z-backups/antes-de-2jugadores"

if [ ! -d "$B" ]; then echo "ERROR: no encuentro el respaldo en $B"; exit 1; fi
echo "Restaurando desde $B ..."

# 1) teclas (las 3 rutas)
cp -f "$B/keys.txt.FUNCIONA"              "$P/keys.txt"
cp -f "$B/keys.config.txt.FUNCIONA"       "$P/config/keys.txt"
cp -f "$B/fifa07.keys.txt.FUNCIONA"       "$P/drive_c/FIFA 07/fifa07.keys.txt"

# 2) config del juego y del port
cp -f "$B/fifa07.wine-nx.txt.FUNCIONA"    "$P/drive_c/FIFA 07/fifa07.wine-nx.txt"
cp -f "$B/settings.json.FUNCIONA"         "$P/config/settings.json"

# 3) fuera cualquier keys2.txt del experimento
rm -f "$P/keys2.txt" "$P/config/keys2.txt" "$P/drive_c/FIFA 07/fifa07.player2.keys.txt"

# 4) el runtime que funciona (md5 5889cb9e...)
cp -f "$B/wine-nx-runtime.nro.5889cb9e-FUNCIONA" "$P/wine-nx-runtime.nro"

echo "--- huellas despues de restaurar (comprobar que coinciden):"
for f in "wine-nx-runtime.nro" "keys.txt" "config/keys.txt" "drive_c/FIFA 07/fifa07.keys.txt" "drive_c/FIFA 07/fifa07.wine-nx.txt"; do
  printf "  %-42s %s\n" "$f" "$(md5sum "$P/$f" | cut -c1-16)"
done
echo "Esperado: runtime 5889cb9eb246ce34 · keys 5d0b1ddd3ea74c5a (x3) · wine-nx b9c1f95aaeb109f2"
echo "LISTO. (En Windows, antes de sacar la tarjeta: Write-VolumeCache -DriveLetter $SD)"
