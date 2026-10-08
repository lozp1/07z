/* dpnhpast.dll shim for FIFA 07 on Wine-NX.
 *
 * WHY THIS EXISTS
 * ---------------
 * fifa07.exe carries its own DirectX capability probe list as debug strings:
 *
 *     Couldn't LoadLibrary DDraw
 *     Couldn't LoadLibrary DInput
 *     Couldn't create CLSID_DirectMusic
 *     Couldn't LoadLibrary dpnhpast.dll
 *
 * DirectDraw, DirectInput and DirectMusic all succeed under Wine-NX now (the
 * first two always did, DirectMusic via src/shims/dmusic_fifa07.c). dpnhpast.dll
 * is the last entry on that list, and the game reports it itself:
 *
 *     warn:module:load_dll Failed to load module L"dpnhpast.dll"; status=c0000135
 *     warn:debugstr:OutputDebugStringA "Couldn't LoadLibrary dpnhpast.dll"
 *
 * That warning is the only DirectX failure left in the log, and the game shows
 * its "You will need to install DirectX 9.0c to run FIFA" dialog with it. On
 * Windows the same dialog disappears once the DirectX 9.0c runtime is
 * installed, which is what puts dpnhpast.dll (the DirectPlay NAT helper) in
 * System32 in the first place.
 *
 * WHAT IT DOES
 * ------------
 * The real file is a DirectPlay NAT helper that registers itself as a COM
 * in-process server: its entire export table is DllGetClassObject,
 * DllCanUnloadNow, DllRegisterServer and DllUnregisterServer. EA only probes
 * the load, so a minimal COM stub satisfies it - a class factory that answers
 * for any class id and an object with a working IUnknown. Nothing is ever
 * called through it, and nothing needs registering: the game loads it by name,
 * so a copy next to fifa07.exe wins the search order.
 *
 * Build: see tools/build-fifa07-shims.py (i686-w64-mingw32-gcc).
 */
#define WIN32_LEAN_AND_MEAN
#include <windows.h>
#include <objbase.h>

#pragma GCC diagnostic ignored "-Wunused-parameter"

typedef struct DpShim {
    const void **vtable;
    LONG ref;
} DpShim;

static ULONG WINAPI dp_AddRef(DpShim *self);

static HRESULT WINAPI dp_QueryInterface(DpShim *self, REFIID riid, void **out)
{
    /* Permissive on purpose: EA probes the module's presence, and refuses
     * nothing that a probe of the NAT helper could ask for. Never called. */
    (void)riid;
    if (!out)
        return E_POINTER;
    *out = self;
    dp_AddRef(self);
    return S_OK;
}

static ULONG WINAPI dp_AddRef(DpShim *self)
{
    return (ULONG)InterlockedIncrement(&self->ref);
}

static ULONG WINAPI dp_Release(DpShim *self)
{
    LONG left = InterlockedDecrement(&self->ref);
    if (left == 0)
        HeapFree(GetProcessHeap(), 0, self);
    return (ULONG)left;
}

#define DP_STUB(nm, args) static HRESULT WINAPI nm args { return E_NOTIMPL; }

DP_STUB(dp_Extra0, (DpShim *self, DWORD a, DWORD b))
DP_STUB(dp_Extra1, (DpShim *self, DWORD a, DWORD b))
DP_STUB(dp_Extra2, (DpShim *self, DWORD a, DWORD b))
DP_STUB(dp_Extra3, (DpShim *self, DWORD a, DWORD b))
DP_STUB(dp_Extra4, (DpShim *self, DWORD a, DWORD b))
DP_STUB(dp_Extra5, (DpShim *self, DWORD a, DWORD b))
DP_STUB(dp_Extra6, (DpShim *self, DWORD a, DWORD b))
DP_STUB(dp_Extra7, (DpShim *self, DWORD a, DWORD b))

static const void *dp_vtable[] = {
    (const void *)dp_QueryInterface,
    (const void *)dp_AddRef,
    (const void *)dp_Release,
    (const void *)dp_Extra0,
    (const void *)dp_Extra1,
    (const void *)dp_Extra2,
    (const void *)dp_Extra3,
    (const void *)dp_Extra4,
    (const void *)dp_Extra5,
    (const void *)dp_Extra6,
    (const void *)dp_Extra7,
};

static struct {
    IClassFactoryVtbl *lpVtbl;
    LONG ref;
} dp_factory;

static HRESULT WINAPI fac_QueryInterface(IClassFactory *iface, REFIID riid, void **out)
{
    (void)riid;
    if (!out)
        return E_POINTER;
    *out = iface;
    InterlockedIncrement(&dp_factory.ref);
    return S_OK;
}

static ULONG WINAPI fac_AddRef(IClassFactory *iface)
{
    (void)iface;
    return (ULONG)InterlockedIncrement(&dp_factory.ref);
}

static ULONG WINAPI fac_Release(IClassFactory *iface)
{
    (void)iface;
    return (ULONG)InterlockedDecrement(&dp_factory.ref);
}

static HRESULT WINAPI fac_CreateInstance(IClassFactory *iface, IUnknown *outer,
                                         REFIID riid, void **out)
{
    DpShim *shim;

    (void)iface;
    (void)riid;
    if (outer)
        return CLASS_E_NOAGGREGATION;
    if (!out)
        return E_POINTER;
    *out = NULL;

    shim = HeapAlloc(GetProcessHeap(), HEAP_ZERO_MEMORY, sizeof(*shim));
    if (!shim)
        return E_OUTOFMEMORY;
    shim->vtable = dp_vtable;
    shim->ref = 1;
    *out = shim;
    return S_OK;
}

static HRESULT WINAPI fac_LockServer(IClassFactory *iface, BOOL lock)
{
    (void)iface;
    (void)lock;
    return S_OK;
}

static IClassFactoryVtbl dp_factory_vtbl = {
    fac_QueryInterface, fac_AddRef, fac_Release, fac_CreateInstance, fac_LockServer,
};

/* ---- the four exports the real dpnhpast.dll has -------------------------- */

HRESULT WINAPI DllGetClassObject(REFCLSID rclsid, REFIID riid, void **out)
{
    (void)rclsid;                     /* any class: EA only probes the module */
    if (!out)
        return E_POINTER;
    *out = NULL;
    if (!dp_factory.lpVtbl)
        dp_factory.lpVtbl = &dp_factory_vtbl;
    dp_factory.ref = 1;
    return dp_factory.lpVtbl->QueryInterface((IClassFactory *)&dp_factory, riid, out);
}

HRESULT WINAPI DllCanUnloadNow(void)
{
    return S_FALSE;
}

HRESULT WINAPI DllRegisterServer(void)
{
    return S_OK;
}

HRESULT WINAPI DllUnregisterServer(void)
{
    return S_OK;
}

BOOL WINAPI DllMain(HINSTANCE hinst, DWORD reason, LPVOID reserved)
{
    (void)hinst; (void)reason; (void)reserved;
    return TRUE;
}
