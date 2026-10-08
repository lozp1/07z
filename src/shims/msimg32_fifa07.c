/* msimg32.dll shim for FIFA 07 on Wine-NX.
 *
 * WHY THIS EXISTS
 * ---------------
 * The variant B graphics chain is
 *
 *     fifa07.exe -> d3d8.dll (dxwrapper stub) -> dxwrapper.dll -> DXVK d3d9
 *
 * and dxwrapper.dll imports MSIMG32.dll and OLEACC.dll. The Wine-NX payload
 * ships neither, and one unresolvable static import kills the whole module:
 *
 *     warn:module:load_dll Failed to load module L"C:\\FIFA 07\\dxwrapper.dll"; status=c0000135
 *     err:module:import_dll Library MSIMG32.dll (which is needed by ...\\dxwrapper.dll) not found
 *     [NXLDR] load name=C:\\FIFA 07\\dxwrapper.dll status=c0000135
 *     "DxWrapper Stub | OK | Could not find DxWrapper.dll functions will be disabled!"
 *
 * With dxwrapper disabled the stub hands the game back to Wine's builtin d3d8
 * (wined3d -> OpenGL) and FIFA 07 ends on its "install DirectX 9.0c" dialog.
 *
 * dxwrapper needs exactly three functions from msimg32 (AlphaBlend,
 * GradientFill, TransparentBlt) and only for its GDI-side DirectDraw features,
 * which dxwrapper.ini leaves off (DdrawReadFromGDI=0, DdrawWriteToGDI=0,
 * DisableGDIGammaRamp=0). The D3d8to9 path - the only one this port enables -
 * does not call them. A copy of the host's C:\Windows\SysWOW64\msimg32.dll is
 * not an option: that Windows 10/11 binary imports five api-ms-win-core-*
 * api-sets, the exact failure mode documented for this port.
 *
 * BEHAVIOUR
 * ---------
 * AlphaBlend honours the one case plain GDI can express (an opaque AC_SRC_OVER
 * blend, SourceConstantAlpha 255, no AC_SRC_ALPHA) through StretchBlt. The
 * per-pixel alpha case and GradientFill/TransparentBlt report
 * ERROR_CALL_NOT_IMPLEMENTED and draw nothing, each noted once on stderr so the
 * runtime's stderr.txt shows if a disabled feature was actually reached.
 *
 * Build: see tools/build-fifa07-shims.py (i686-w64-mingw32-gcc).
 */
#define WIN32_LEAN_AND_MEAN
#include <windows.h>

/* wingdi.h declares these three as dllimport; we ARE the implementation, so the
 * redeclaration warning is expected and not worth any other noise. */
#pragma GCC diagnostic ignored "-Wattributes"

/* No stdio here on purpose: a shim DLL should not depend on the CRT being
 * initialised. GetStdHandle/WriteFile are kernel32 only. */
#define NOTE(text) note_once(text, (DWORD)(sizeof(text) - 1))

static void note_once(const char *text, DWORD length)
{
    static int done;
    HANDLE err;
    DWORD written;

    if (done)
        return;
    done = 1;

    err = GetStdHandle(STD_ERROR_HANDLE);
    if (err && err != INVALID_HANDLE_VALUE)
        WriteFile(err, text, length, &written, NULL);
}

BOOL WINAPI AlphaBlend(HDC hdcDest, int xDest, int yDest, int wDest, int hDest,
                       HDC hdcSrc, int xSrc, int ySrc, int wSrc, int hSrc,
                       BLENDFUNCTION blend)
{
    if (blend.BlendOp == AC_SRC_OVER && blend.SourceConstantAlpha == 255 &&
        blend.AlphaFormat == 0) {
        return StretchBlt(hdcDest, xDest, yDest, wDest, hDest,
                          hdcSrc, xSrc, ySrc, wSrc, hSrc, SRCCOPY);
    }

    NOTE("[msimg32-shim] AlphaBlend with per-pixel alpha: not implemented, "
         "drawing nothing\n");
    SetLastError(ERROR_CALL_NOT_IMPLEMENTED);
    return FALSE;
}

BOOL WINAPI TransparentBlt(HDC hdcDest, int xDest, int yDest, int wDest, int hDest,
                           HDC hdcSrc, int xSrc, int ySrc, int wSrc, int hSrc,
                           UINT crTransparent)
{
    (void)hdcDest; (void)xDest; (void)yDest; (void)wDest; (void)hDest;
    (void)hdcSrc; (void)xSrc; (void)ySrc; (void)wSrc; (void)hSrc;
    (void)crTransparent;

    NOTE("[msimg32-shim] TransparentBlt: not implemented, drawing nothing\n");
    SetLastError(ERROR_CALL_NOT_IMPLEMENTED);
    return FALSE;
}

BOOL WINAPI GradientFill(HDC hdc, PTRIVERTEX vertices, ULONG count,
                         PVOID mesh, ULONG meshCount, ULONG mode)
{
    (void)hdc; (void)vertices; (void)count;
    (void)mesh; (void)meshCount; (void)mode;

    NOTE("[msimg32-shim] GradientFill: not implemented, drawing nothing\n");
    SetLastError(ERROR_CALL_NOT_IMPLEMENTED);
    return FALSE;
}

BOOL WINAPI DllMain(HINSTANCE hinst, DWORD reason, LPVOID reserved)
{
    (void)hinst; (void)reason; (void)reserved;
    return TRUE;
}
