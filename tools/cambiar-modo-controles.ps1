<#
  cambiar-modo-controles.ps1

  Alterna, de forma REVERSIBLE, entre la via de MANDO y la via de TECLADO para
  FIFA 07 sobre Wine-NX, escribiendo la clave `input-mode` en el fichero de
  ajustes por juego:

      <SD>:\switch\wine\drive_c\FIFA 07\fifa07.wine-nx.txt

  Ese fichero es el ultimo que aplica el runtime para los controles y ademas el
  frontend NO lo pisa (solo reescribe su linea dxvk-hud), asi que el cambio
  sobrevive a guardar los mandos desde el frontend.

      input-mode=1  ->  MANDO   (FIFA ve un mando Xbox; sus iconos y Mi FIFA 07 -> Controls)
      input-mode=2  ->  TECLADO (el runtime sintetiza las teclas de keys.txt)

  Escribe ademas, de forma coherente, esos mismos valores en los tres ficheros
  de teclas (raiz, config y junto al .exe) para que todo el estado sea
  consistente; el frontend los pondra a 2 otra vez si se guardan mandos, pero el
  .wine-nx.txt seguira mandando.

  Uso:
    powershell -ExecutionPolicy Bypass -File tools\cambiar-modo-controles.ps1 -Modo mando
    powershell -ExecutionPolicy Bypass -File tools\cambiar-modo-controles.ps1 -Modo teclado
    powershell -ExecutionPolicy Bypass -File tools\cambiar-modo-controles.ps1 -Modo mando -Drive E:

  No hace nada mas: ni copia el runtime, ni toca el frontend, ni el shim.
#>
[CmdletBinding()]
param(
    [Parameter(Mandatory = $true)]
    [ValidateSet('mando', 'teclado', '1', '2')]
    [string]$Modo,

    [string]$Drive,                                    # p.ej. 'D:' (opcional)
    [string]$GameSub = 'switch\fifa07\drive_c\FIFA 07',
    [string]$WineSub = 'switch\fifa07'
)

$ErrorActionPreference = 'Stop'

$value = if ($Modo -eq 'mando' -or $Modo -eq '1') { '1' } else { '2' }
$label = if ($value -eq '1') { 'MANDO (input-mode=1)' } else { 'TECLADO (input-mode=2)' }

function Info($m) { Write-Host "[ctrl] $m" }
function Fail($m) { Write-Host "[ctrl] $m" -ForegroundColor Red; exit 1 }

function Set-InputMode([string]$path, [string]$value) {
    if (-not (Test-Path -LiteralPath $path)) {
        Info "no existe (se omite): $path"
        return $false
    }
    $lines  = [System.Collections.Generic.List[string]]::new()
    $lines.AddRange([string[]](Get-Content -LiteralPath $path))
    $seen = $false
    for ($i = 0; $i -lt $lines.Count; $i++) {
        if ($lines[$i] -match '^\s*input-mode\s*=') {
            $lines[$i] = "input-mode=$value"
            $seen = $true
        }
    }
    if (-not $seen) { $lines.Add("input-mode=$value") }

    $stamp  = Get-Date -Format 'yyyyMMdd-HHmmss'
    $backup = "$path.bak-modo-$stamp"
    Copy-Item -LiteralPath $path -Destination $backup -Force
    # LF como el resto del runtime; sin BOM.
    $text = ($lines -join "`n") + "`n"
    [System.IO.File]::WriteAllText($path, $text, (New-Object System.Text.UTF8Encoding($false)))
    Info "escrito input-mode=$value en $path (backup: $backup)"
    return $true
}

# --- localizar la tarjeta ---------------------------------------------------
$letters = if ($Drive) { @($Drive.TrimEnd('\').TrimEnd(':')) } else { @('D', 'E') }
$game = $null; $wine = $null
foreach ($L in $letters) {
    $root = "${L}:\"
    if (-not (Test-Path -LiteralPath $root)) { continue }
    $cand = Join-Path $root $GameSub
    if (Test-Path -LiteralPath $cand -PathType Container) {
        $game = $cand
        $wine = Join-Path $root $WineSub
        break
    }
}
if (-not $game) {
    Fail "No encuentro la SD con '$GameSub'. Inserta la tarjeta (o pasa -Drive D:) y reintenta."
}

Info "SD: $game"
Info "modo destino: $label"

# --- 1) el fichero que manda (el que el frontend no pisa) -------------------
$master = Join-Path $game 'fifa07.wine-nx.txt'
if (-not (Test-Path -LiteralPath $master)) {
    Info "no existia fifa07.wine-nx.txt; se crea"
    New-Item -ItemType File -Path $master | Out-Null
    Set-Content -LiteralPath $master -Value '' -NoNewline
}
Set-InputMode $master $value | Out-Null

# --- 2) los tres ficheros de teclas (coherencia) ----------------------------
foreach ($p in @(
        (Join-Path $game 'fifa07.keys.txt'),
        (Join-Path $wine 'config\keys.txt'),
        (Join-Path $wine 'keys.txt'))) {
    Set-InputMode $p $value | Out-Null
}

Info "listo. Arranca el juego desde el icono del HOME para probar."
if ($value -eq '1') {
    Info "en MANDO: configura los botones dentro del juego (Mi FIFA 07 -> Controls)."
} else {
    Info "en TECLADO: el mapa de keys.txt (editable desde el frontend) es el que manda."
}
