/* SensApi.dll shim for FIFA 07 on Wine-NX.
 *
 * WHY THIS EXISTS
 * ---------------
 * fifa07.exe statically imports exactly one function from SensApi.dll:
 * IsNetworkAlive. The Wine-NX payload does not ship sensapi.dll, and the loader
 * aborts on an unresolvable static import with STATUS_DLL_NOT_FOUND
 * (0xC0000135), so the game never reaches its first window.
 *
 * The port previously used a copy of the host's C:\Windows\SysWOW64\sensapi.dll.
 * That is a Windows 10/11 binary which imports
 * api-ms-win-core-sysinfo-l1-2-0.dll!GetOsSafeBootMode; Wine answers with a dummy
 * stub address and calling through it faults. This shim has no api-set imports.
 *
 * BEHAVIOUR
 * ---------
 * Always reports "no network connection". FIFA 07 is a single-player football
 * game; the only consequence is that online features are unavailable, which is
 * the correct answer for a console with no usable network path.
 *
 * Build: see tools/build-fifa07-shims.py (i686-w64-mingw32-gcc).
 */
#define WIN32_LEAN_AND_MEAN
#include <windows.h>

BOOL WINAPI IsNetworkAlive(LPDWORD flags)
{
    /* No LAN, WAN or Internet connection flags. */
    if (flags) *flags = 0;
    return FALSE;
}

/* Declared with void* on purpose: the wire ABI is a pointer either way and this
 * avoids depending on sensapi.h. Both always report "unreachable". */
BOOL WINAPI IsDestinationReachableA(LPCSTR destination, LPVOID info)
{
    (void)destination;
    if (info) *(DWORD *)info = 0;
    return FALSE;
}

BOOL WINAPI IsDestinationReachableW(LPCWSTR destination, LPVOID info)
{
    (void)destination;
    if (info) *(DWORD *)info = 0;
    return FALSE;
}

BOOL WINAPI DllMain(HINSTANCE hinst, DWORD reason, LPVOID reserved)
{
    (void)hinst; (void)reason; (void)reserved;
    return TRUE;
}
