/* dmusic.dll shim for FIFA 07 on Wine-NX.
 *
 * WHY THIS EXISTS
 * ---------------
 * FIFA 07's "You will need to install DirectX 9.0c to run FIFA" dialog is, in
 * practice, the game asking "can I create CLSID_DirectMusic?":
 *
 *   - fifa07.exe contains exactly ONE DirectMusic GUID, CLSID_DirectMusic
 *     ({636B9F10-0C7D-11D1-95B2-0020AFDC7421}), and no other member of the
 *     family, nor any ".dls"/"dmsynth"/"dmloader" string. DirectMusic is a
 *     capability probe here, not the music system (music goes through
 *     DirectSound, which the game also imports and Wine does implement).
 *   - The same install on Windows shows the same dialog until the DirectX 9.0c
 *     runtime is installed - i.e. until DirectMusic exists - and works after.
 *   - The DirectX version registry values are NOT the difference: a working
 *     Windows box and this Wine prefix carry the same ones byte for byte
 *     (Version "4.09.00.0904", InstalledVersion 00 00 00 09 00 00 00 00).
 *   - Wine implements no DirectMusic at all, so on the console the probe fails:
 *       err:ole:com_get_class_object class {636b9f10-...} not registered
 *       warn:debugstr:OutputDebugStringA "Couldn't create CLSID_DirectMusic"
 *
 * WHAT IT DOES
 * ------------
 * Exactly what the probe needs and nothing more: DllGetClassObject for
 * CLSID_DirectMusic handing back a class factory, and an object with a working
 * IUnknown so that CoCreateInstance succeeds and the game can release it. No
 * sound is produced on this path, and none is expected: FIFA 07 plays through
 * DirectSound.
 *
 * The factory deliberately ignores the requested IID and always returns the
 * object. A probe tests SUCCEEDED(CoCreateInstance(...)) and must not fail on
 * whichever interface revision the game asked for.
 *
 * Build: see tools/build-fifa07-shims.py (i686-w64-mingw32-gcc).
 * Register: tools/package_fifa07_diag.py writes the CLSID into the prefix
 * registry next to the game, pointing at C:\FIFA 07\dmusic.dll.
 */
#define WIN32_LEAN_AND_MEAN
#include <windows.h>
#include <objbase.h>

/* mingw-w64 ships no DirectMusic header, so the interface below is written from
 * the documented IDirectMusic shape rather than checked against a header. That
 * is acceptable *here* because the game never calls into the object: it only
 * creates and releases it. Slots are padded past the real method count so a
 * stray call lands on a stub rather than off the end of the table. */
#pragma GCC diagnostic ignored "-Wunused-parameter"

static const GUID dm_clsid_directmusic =
    { 0x636B9F10, 0x0C7D, 0x11D1, { 0x95, 0xB2, 0x00, 0x20, 0xAF, 0xDC, 0x74, 0x21 } };

typedef struct DmShim {
    const void **vtable;
    LONG ref;
} DmShim;

/* ---- IUnknown ------------------------------------------------------------ */

static ULONG WINAPI dm_AddRef(DmShim *self);

static HRESULT WINAPI dm_QueryInterface(DmShim *self, REFIID riid, void **out)
{
    /* Deliberately permissive. A capability probe tests SUCCEEDED() on whichever
     * interface revision the game was built against, and this shim exists only
     * so that call succeeds; refusing an IID we cannot name would put the
     * "install DirectX 9.0c" dialog straight back. Nothing is ever called
     * through the pointer. */
    (void)riid;
    if (!out)
        return E_POINTER;
    *out = self;
    dm_AddRef(self);
    return S_OK;
}

static ULONG WINAPI dm_AddRef(DmShim *self)
{
    return (ULONG)InterlockedIncrement(&self->ref);
}

static ULONG WINAPI dm_Release(DmShim *self)
{
    LONG left = InterlockedDecrement(&self->ref);
    if (left == 0)
        HeapFree(GetProcessHeap(), 0, self);
    return (ULONG)left;
}

/* ---- every other IDirectMusic method ------------------------------------ */

#define DM_STUB(nm, args) static HRESULT WINAPI nm args { return E_NOTIMPL; }

DM_STUB(dm_EnumMasterClock,  (DmShim *self, DWORD index, void **clock))
DM_STUB(dm_GetMasterClock,   (DmShim *self, GUID *guid, void **clock))
DM_STUB(dm_SetMasterClock,   (DmShim *self, void *clock))
DM_STUB(dm_GetDefaultPort,   (DmShim *self, GUID *guid, void **port))
DM_STUB(dm_SetDirectSound,   (DmShim *self, void *dsound, HWND hwnd))
DM_STUB(dm_GetPort,          (DmShim *self, GUID *guid, void **port))
DM_STUB(dm_EnumPort,         (DmShim *self, DWORD index, void *caps))
DM_STUB(dm_SetPort,          (DmShim *self, void *port))
DM_STUB(dm_SetSynth,         (DmShim *self, void *synth, void *sink))
DM_STUB(dm_SetTrack,         (DmShim *self, GUID *guid, void *track, DWORD mask))
DM_STUB(dm_GetTrack,         (DmShim *self, GUID *guid, void **track))
DM_STUB(dm_SetAutoDownload,  (DmShim *self, GUID *guid, void *object))
DM_STUB(dm_GetAutoDownload,  (DmShim *self, GUID *guid, void **object))
DM_STUB(dm_GetSyncTime,      (DmShim *self, void *time))
DM_STUB(dm_GetClockTime,     (DmShim *self, void *time))
DM_STUB(dm_GetNotification,  (DmShim *self, void **notify))
DM_STUB(dm_GetBumperLength,  (DmShim *self, void *len))
DM_STUB(dm_Extra0,           (DmShim *self, DWORD a, DWORD b))
DM_STUB(dm_Extra1,           (DmShim *self, DWORD a, DWORD b))
DM_STUB(dm_Extra2,           (DmShim *self, DWORD a, DWORD b))
DM_STUB(dm_Extra3,           (DmShim *self, DWORD a, DWORD b))
DM_STUB(dm_Extra4,           (DmShim *self, DWORD a, DWORD b))
DM_STUB(dm_Extra5,           (DmShim *self, DWORD a, DWORD b))
DM_STUB(dm_Extra6,           (DmShim *self, DWORD a, DWORD b))
DM_STUB(dm_Extra7,           (DmShim *self, DWORD a, DWORD b))

static const void *dm_vtable[] = {
    (const void *)dm_QueryInterface,
    (const void *)dm_AddRef,
    (const void *)dm_Release,
    (const void *)dm_EnumMasterClock,
    (const void *)dm_GetMasterClock,
    (const void *)dm_SetMasterClock,
    (const void *)dm_GetDefaultPort,
    (const void *)dm_SetDirectSound,
    (const void *)dm_GetPort,
    (const void *)dm_EnumPort,
    (const void *)dm_SetPort,
    (const void *)dm_SetSynth,
    (const void *)dm_SetTrack,
    (const void *)dm_GetTrack,
    (const void *)dm_SetAutoDownload,
    (const void *)dm_GetAutoDownload,
    (const void *)dm_GetSyncTime,
    (const void *)dm_GetClockTime,
    (const void *)dm_GetNotification,
    (const void *)dm_GetBumperLength,
    (const void *)dm_Extra0,
    (const void *)dm_Extra1,
    (const void *)dm_Extra2,
    (const void *)dm_Extra3,
    (const void *)dm_Extra4,
    (const void *)dm_Extra5,
    (const void *)dm_Extra6,
    (const void *)dm_Extra7,
};

/* ---- class factory ------------------------------------------------------- */

typedef struct DmFactory {
    IClassFactoryVtbl *lpVtbl;
    LONG ref;
} DmFactory;

static DmFactory dm_factory;

static HRESULT WINAPI fac_QueryInterface(IClassFactory *iface, REFIID riid, void **out)
{
    if (!out)
        return E_POINTER;
    *out = iface;                     /* IUnknown, IClassFactory: one vtable */
    InterlockedIncrement(&dm_factory.ref);
    return S_OK;
}

static ULONG WINAPI fac_AddRef(IClassFactory *iface)
{
    (void)iface;
    return (ULONG)InterlockedIncrement(&dm_factory.ref);
}

static ULONG WINAPI fac_Release(IClassFactory *iface)
{
    (void)iface;
    return (ULONG)InterlockedDecrement(&dm_factory.ref);
}

static HRESULT WINAPI fac_CreateInstance(IClassFactory *iface, IUnknown *outer,
                                         REFIID riid, void **out)
{
    DmShim *shim;

    (void)iface;
    if (outer)
        return CLASS_E_NOAGGREGATION;
    if (!out)
        return E_POINTER;
    *out = NULL;

    shim = HeapAlloc(GetProcessHeap(), HEAP_ZERO_MEMORY, sizeof(*shim));
    if (!shim)
        return E_OUTOFMEMORY;
    shim->vtable = dm_vtable;
    shim->ref = 1;

    /* The IID is intentionally not checked; see the header comment. */
    (void)riid;
    *out = shim;
    return S_OK;
}

static HRESULT WINAPI fac_LockServer(IClassFactory *iface, BOOL lock)
{
    (void)iface;
    (void)lock;
    return S_OK;
}

static IClassFactoryVtbl dm_factory_vtbl = {
    fac_QueryInterface, fac_AddRef, fac_Release, fac_CreateInstance, fac_LockServer,
};

/* ---- in-process server entry points -------------------------------------- */

HRESULT WINAPI DllGetClassObject(REFCLSID rclsid, REFIID riid, void **out)
{
    if (!out)
        return E_POINTER;
    *out = NULL;
    if (!IsEqualGUID(rclsid, &dm_clsid_directmusic))
        return CLASS_E_CLASSNOTAVAILABLE;

    dm_factory.lpVtbl = &dm_factory_vtbl;
    if (dm_factory.ref == 0)
        dm_factory.ref = 1;
    return dm_factory.lpVtbl->QueryInterface((IClassFactory *)&dm_factory, riid, out);
}

HRESULT WINAPI DllCanUnloadNow(void)
{
    return S_FALSE;                   /* the object is a small fixed table */
}

BOOL WINAPI DllMain(HINSTANCE hinst, DWORD reason, LPVOID reserved)
{
    (void)hinst; (void)reason; (void)reserved;
    return TRUE;
}
