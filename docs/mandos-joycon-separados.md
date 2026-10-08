# Mandos: Joy-Con separados (requisitos del parche del runtime)

## Estado actual
El runtime Autorun sondea **un solo mando**:
- `horizon-wine/source/runtime.c:543` → `static PadState wine_nx_pad;` (un unico PadState)
- `wine_nx_pointer_poll()` (runtime.c:854-871) → `padConfigureInput(1, HidNpadStyleSet_NpadStandard)`
- `HidNpadStyleSet_NpadStandard` = `NpadFullKey | NpadJoyDual` → **NO cubre** `NpadJoyLeft` / `NpadJoyRight`

Consecuencia: **dos Joy-Con separados no llegan** (uno queda como No1/JoyLeft y el otro como No2/JoyRight,
fuera del conjunto configurado). Solo funciona un mando completo o el par junto.

## Cambio propuesto (runtime.c, `wine_nx_pointer_poll()`)
1. La configuracion de input debe abarcar los estilos sueltos:
   `padConfigureInput(2, HidNpadStyleSet_NpadStandard | HidNpadStyleSet_NpadJoyLeft | HidNpadStyleSet_NpadJoyRight);`
2. Dos estados: `padInitialize(&wine_nx_pad[0], HidNpadIdType_No1);` y `padInitialize(&wine_nx_pad[1], HidNpadIdType_No2);`
3. En el sondeo, mezclar: `all_held = (conectado0 ? padGetButtons(&pad[0]) : 0) | (conectado1 ? padGetButtons(&pad[1]) : 0)`
   y tomar el stick de la mitad que este conectada.
4. Opcional (via XInput, no la del shim): `horizon-wine/source/xinput_unix.c:43`
   `nx_xinput_get_state_unix()` cortocircuita `index != 0`; para exponer el 2do Joy-Con como jugador 2
   hay que atender index 0 y 1 con su propio pad.

Requiere **recompilar el NRO**, y hay que hacerlo con `horizon-wine/build-low-window.sh`
(NO con el build normal) para conservar el parche de ventana baja.
El parche de Atmosphere (mesosphere.bin / autorun-loader.kip) **no** hay que rehacerlo:
se empareja por program ID (0x0548EABB35576000), no por bytes del NRO.

## REQUISITO AÑADIDO: mapeo de los botones que solo existen separados
Cuando los Joy-Con estan **separados**, cada mitad en horizontal tiene:
- **SL y SR** (los botones del riel) → son los **unicos hombros** disponibles
- **NO tiene L, R, ZL ni ZR** (esos van en el riel, y en horizontal quedan inaccesibles)
- Un solo stick (no hay stick derecho)

Por tanto el parche DEBE incluir, de forma explicita:
1. **SL → L y SR → R** (o el criterio que se elija, pero mapeados: si no, el usuario se queda
   sin sprint / sin control de ritmo / sin desmarque con un solo Joy-Con)
2. Documentar **que dos acciones de FIFA quedan sin boton** con un solo Joy-Con y elegir las
   menos criticas de forma consciente (no dejarlo al azar).
3. Con los **dos Joy-Con separados**, repartir las acciones entre las dos mitades.

Sin este mapeo, el soporte de Joy-Con separados queda a medias: detectaria los mandos pero
el juego no tendria botones suficientes.
