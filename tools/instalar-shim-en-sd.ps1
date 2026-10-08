<#
  instalar-shim-en-sd.ps1

  Instala el shim DirectInput corregido (GetKeyboardState) en la carpeta del
  juego FIFA 07 de la tarjeta SD, apartando los dinput de Windows que hubiera.

  Que hace, en la carpeta  <letra>:\switch\wine\drive_c\FIFA 07\  :
    1. Localiza la tarjeta (D: o E:) que contenga switch\wine\drive_c\FIFA 07.
    2. Hace copia de seguridad del dinput.dll / dinput8.dll que esten puestos
       (shim anterior o DLL de Windows) en  _shim-backup-<fecha>\  una sola vez.
    3. Renombra los dinput de Windows a _win-dinput.dll / _win-dinput8.dll
       (asi dejan de cargarse) si todavia tienen esos nombres.
    4. Copia el shim nuevo  build\fifa07-shims\DINPUT.dll  ->  dinput.dll.

  Uso:
    powershell -ExecutionPolicy Bypass -File tools\instalar-shim-en-sd.ps1
    powershell -ExecutionPolicy Bypass -File tools\instalar-shim-en-sd.ps1 -Drive E:

  Si la tarjeta no esta montada, el script lo dice y no toca nada.
#>
[CmdletBinding()]
param(
    [string]$Drive,                                      # p.ej. 'D:' (opcional)
    [string]$ShimDll,                                    # por defecto: ..\build\fifa07-shims\DINPUT.dll
    [string]$GameSub  = 'switch\wine\drive_c\FIFA 07',
    [string]$WindowsInputNames = 'dinput.dll,dinput8.dll',
    [string]$ParkedTo = '_win-dinput.dll,_win-dinput8.dll'
)

$ErrorActionPreference = 'Stop'

function Info($m) { Write-Host "[shim] $m" }
function Warn($m) { Write-Host "[shim] $m" -ForegroundColor Yellow }
function Fail($m) { Write-Host "[shim] $m" -ForegroundColor Red; exit 1 }

# --- 1. validar el shim de origen -----------------------------------------
if (-not $ShimDll) {
    $base = $PSScriptRoot
    if (-not $base) { $base = Split-Path -Parent -LiteralPath $MyInvocation.MyCommand.Path }
    if (-not $base) { $base = (Get-Location).Path }
    $ShimDll = Join-Path $base '..\build\fifa07-shims\DINPUT.dll'
}
$ShimDll = [System.IO.Path]::GetFullPath($ShimDll)
if (-not (Test-Path -LiteralPath $ShimDll)) {
    Fail "No existe el shim compilado: $ShimDll  (compila antes build\fifa07-shims\DINPUT.dll)"
}
$shim = Get-Item -LiteralPath $ShimDll
Info ("shim origen: {0}  ({1} bytes, md5 {2})" -f $shim.FullName, $shim.Length,
      (Get-FileHash -LiteralPath $shim.FullName -Algorithm MD5).Hash)

# --- 2. localizar la tarjeta y la carpeta del juego ------------------------
$letters = if ($Drive) { @($Drive.TrimEnd('\').TrimEnd(':')) } else { @('D','E') }
$game = $null
foreach ($L in $letters) {
    $root = "${L}:\"
    if (-not (Test-Path -LiteralPath $root)) { Info "unidad $L`: no montada"; continue }
    $cand = Join-Path $root $GameSub
    if (Test-Path -LiteralPath $cand -PathType Container) { $game = $cand; break }
    Info "unidad $L`: sin $GameSub"
}
if (-not $game) {
    Warn "Tarjeta SD no montada o sin la carpeta '$GameSub'."
    Warn "Shim listo en $($shim.FullName) : dejalo asi y reejecuta este script con la tarjeta puesta."
    exit 2
}
Info "carpeta del juego: $game"

# --- 3. copia de seguridad unica -------------------------------------------
$stamp = Get-Date -Format 'yyyyMMdd-HHmmss'
$backup = Join-Path $game "_shim-backup-$stamp"
$names = @('dinput.dll','dinput8.dll')
$parkOld = ($WindowsInputNames -split ',')
$parkNew = ($ParkedTo          -split ',')

$existing = @($names | Where-Object { Test-Path -LiteralPath (Join-Path $game $_) })
if ($existing.Count -gt 0) {
    New-Item -ItemType Directory -Path $backup | Out-Null
    foreach ($n in $existing) {
        Copy-Item -LiteralPath (Join-Path $game $n) -Destination (Join-Path $backup $n) -Force
        Info "backup: $n -> $backup\$n"
    }
} else {
    Info "no habia dinput puesto; no hace falta backup"
}

# --- 4. apartar los dinput de Windows si aun tienen su nombre --------------
for ($i = 0; $i -lt $parkOld.Count; $i++) {
    $from = Join-Path $game $parkOld[$i]
    if (-not (Test-Path -LiteralPath $from)) { continue }
    $to = Join-Path $game $parkNew[$i]
    if (Test-Path -LiteralPath $to) {
        Info "$($parkOld[$i]) ya apartado ($($parkNew[$i]) existe); no se toca"
        # el shim escribira dinput.dll mas abajo; el de Windows queda apartado
    } else {
        Move-Item -LiteralPath $from -Destination $to -Force
        Info "apartado: $($parkOld[$i]) -> $($parkNew[$i])"
    }
}

# --- 5. instalar el shim ----------------------------------------------------
$dst = Join-Path $game 'dinput.dll'
Copy-Item -LiteralPath $ShimDll -Destination $dst -Force
$out = Get-Item -LiteralPath $dst
Info ("instalado: {0}  ({1} bytes, md5 {2})" -f $out.FullName, $out.Length,
      (Get-FileHash -LiteralPath $out.FullName -Algorithm MD5).Hash)
Info "recuerda: input-mode=2 (INPUT_KEYBOARD_MOUSE) en keys.txt para que el pad"
Info "se traduzca a teclas; si no, el runtime no emite eventos de teclado."
Info "hecho."
