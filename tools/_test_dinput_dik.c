/* Replicates the two variants of read_keyboard() from src/shims/dinput_fifa07.c
 * and checks what a held arrow key publishes to the DirectInput key array.
 * VK_LEFT/VK_UP/VK_RIGHT/VK_DOWN are what the runtime synthesises for the
 * d-pad and the left stick (see input_profile.c / keys.txt). */
#include <windows.h>
#include <stdio.h>
#include <string.h>

static int vk_is_extended(UINT vk)
{
    switch (vk) {
    case VK_RCONTROL: case VK_RMENU: case VK_INSERT: case VK_DELETE:
    case VK_HOME: case VK_END: case VK_PRIOR: case VK_NEXT:
    case VK_LEFT: case VK_RIGHT: case VK_UP: case VK_DOWN:
    case VK_NUMLOCK: case VK_DIVIDE: case VK_SNAPSHOT:
        return 1;
    default:
        return 0;
    }
}

/* old = 1 reproduces the shipped bug; old = 0 is the fixed variant. */
static void fill(int old, const BYTE kb[256], unsigned char out[256])
{
    UINT vk;
    memset(out, 0, 256);
    for (vk = 1; vk < 256; vk++) {
        UINT sc;
        if (!(kb[vk] & 0x80)) continue;
        sc = MapVirtualKeyA(vk, MAPVK_VK_TO_VSC);
        if (!sc || sc > 0x7f) continue;
        if (old) {
            out[sc] = 0x80;
            if (vk_is_extended(vk)) out[0x80 | sc] = 0x80;
        } else {
            if (vk_is_extended(vk)) out[0x80 | sc] = 0x80;
            else out[sc] = 0x80;
        }
    }
}

struct probe { const char *name; UINT vk; int numpad_dik; int arrow_dik; };
static const struct probe probes[] = {
    { "VK_UP   (arriba)",  VK_UP,    0x48, 0xC8 },
    { "VK_LEFT (izq)   ",  VK_LEFT,  0x4B, 0xCB },
    { "VK_RIGHT(dcha)  ",  VK_RIGHT, 0x4D, 0xCD },
    { "VK_DOWN (abajo) ",  VK_DOWN,  0x50, 0xD0 },
    { "VK_NUMPAD4 real ",  VK_NUMPAD4, 0x4B, -1 },
    { "VK_NUMPAD8 real ",  VK_NUMPAD8, 0x48, -1 },
};

int main(void)
{
    int i, bad_old = 0, bad_new = 0;
    printf("vk=0x25..0x28 son las flechas que el runtime sintetiza para el stick.\n\n");
    for (i = 0; i < (int)(sizeof(probes) / sizeof(probes[0])); i++) {
        BYTE kb[256]; unsigned char o[256], n[256];
        memset(kb, 0, sizeof(kb));
        kb[probes[i].vk] = 0x80;
        fill(1, kb, o); fill(0, kb, n);
        printf("%s  numpadDIK 0x%02X -> viejo:%s  nuevo:%s | arrowDIK %s\n",
               probes[i].name, probes[i].numpad_dik,
               o[probes[i].numpad_dik] ? "PRESIONADO" : "libre     ",
               n[probes[i].numpad_dik] ? "PRESIONADO" : "libre     ",
               probes[i].arrow_dik < 0 ? "-" :
                   (n[probes[i].arrow_dik] ? "PRESIONADO" : "libre"));
        /* An extended arrow must NOT look like the keypad key, and a real
         * keypad key must still publish its own code. */
        if (probes[i].arrow_dik >= 0) {
            if (o[probes[i].numpad_dik]) bad_old++;
            if (n[probes[i].numpad_dik]) bad_new++;
            if (!n[probes[i].arrow_dik]) bad_new++;
        } else {
            if (!n[probes[i].numpad_dik]) bad_new++;
        }
    }
    printf("\nCONCLUSION: flechas que se colaban como teclado numerico -> viejo=%d, nuevo=%d\n",
           bad_old, bad_new);
    printf("%s\n", bad_old == 4 && bad_new == 0 ? "TEST OK: el bug existe y el fix lo elimina" : "TEST FALLO");
    return bad_new != 0;
}
