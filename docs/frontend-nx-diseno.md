# Frontend FIFA 07 NX - diseno

## Pantallas
- Menu principal: Jugar | Configuracion | Creditos/Donaciones | Salir
- Configuracion: opciones de rendimiento/graficos (escribe NOMBRE.wine-nx.txt) y mapeo de mandos (NOMBRE.keys.txt)
- Creditos/Donaciones: texto + enlaces + QR
- Navegacion: D-Pad, A selecciona, B vuelve

## Lanzamiento invisible
NRO propio que ejecuta el runtime Wine-NX pasandole la ruta de fifa07.exe como argv[1].
Al salir vuelve al HOME gracias a reopen-the-launcher-on-exit=false (ya puesto).

## Donaciones
- https://paypal.me/francopaololg
- https://buymeacoffee.com/z.frnk
QR: generar un PNG por enlace (qrencode) e incrustarlos como recursos del NRO.

## Primer hito
1. Instalar devkitPro
2. Estructura: fifa07_nx_frontend/{Makefile, source/main.c, data/, resources/}
3. Prototipo: NRO con libnx que muestre pantalla de bienvenida, los dos enlaces
   y permita salir con A.

## Recomendacion
Adaptar el estilo del proyecto de referencia del usuario: C:\Projects\angular\AndromedaDownload (colores, tipografia, tamanos y espaciados) y escribir un parser/escritor C
ligero para .wine-nx.txt y .keys.txt.


## Referencia de estilo OBLIGATORIA
C:\Projects\angular\AndromedaDownload (proyecto de referencia del usuario para tamanos, espaciados y patrones visuales).
NO inventar valores: tomarlos de ahi.

### Tokens encontrados (muestra)
- `--bg-base:        #0B1120;`
- `--bg-surface:     #060913;`
- `--bg-input:       #0E1526;`
- `--bg-input-focus: #111A2E;`
- `--bg-card:        #0E1526;`
- `--bg-card-about:  #161B27;`
- `--bg-dock:        #07111F;`
- `--border-subtle:  #1E293B;`
- `--border-accent:  #26344A;`
- `--border-input:   #26344A;`
- `--border-card:    #1E293B;`
- `--border-about:   #232B3E;`
- `--text-primary:   #F8FAFC;`
- `--text-secondary: #94A3B8;`
- `--text-muted:     #64748B;`
- `--text-dark:      #0F172A;`
- `--accent-blue:    #1D4ED8;`
- `--accent-blue-h:  #2563EB;`
- `--accent-blue-b:  #3B82F6;`
- `--accent-cyan:    #38BDF8;`
- `--accent-green:   #10E761;`
- `--accent-green-b: #059669;`
- `--accent-amber:   #F59E0B;`
- `--accent-amber-b: #D97706;`
- `--accent-red:     #EF4444;`
- `--accent-red-b:   #DC2626;`
- `--paint-fill:     #080C14;`
- `--paint-stroke:   #3B82F6;`
- `--radius-window:  16px;`
- `--radius-modal:   16px;`
- `--radius-card:    10px;`
- `--radius-btn:     9px;`
- `--radius-input:   8px;`
- `--radius-badge:   3px;`
- `--bg-base:        #E2E8F0;`
- `--bg-surface:     #FFFFFF;`
- `--bg-input:       #FFFFFF;`
- `--bg-input-focus: #FFFFFF;`
- `--bg-card:        #F8FAFC;`
- `--bg-card-about:  #FFFFFF;`
- `--bg-dock:        #E2E8F0;`
- `--border-subtle:  #CBD5E1;`
- `--border-accent:  #94A3B8;`
- `--border-input:   #94A3B8;`
- `--border-card:    #CBD5E1;`
