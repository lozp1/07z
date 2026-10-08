/* DINPUT.dll shim for FIFA 07 on Wine-NX.
 *
 * WHY THIS EXISTS
 * ---------------
 * fifa07.exe statically imports exactly one function from DINPUT.dll:
 * DirectInputCreateA. The Wine-NX payload (test-build-2/3) does not ship a
 * dinput.dll at all, and Wine/Wine-NX does not synthesise a whole missing
 * module for a static import, so the loader aborts with STATUS_DLL_NOT_FOUND
 * (0xC0000135) before the game creates a single window.
 *
 * Note that this is NOT a forwarder to dinput8.dll: Wine builds dinput.dll and
 * dinput8.dll from the same source but with different interface versions, and
 * a DirectInput8 object does not hand out IDirectInputA.
 *
 * WHAT IT DOES
 * ------------
 * Implements the DirectInput 1-7 interfaces just far enough for the game to
 * run:
 *   - IDirectInputA / IDirectInput2A (v1 vtable: this is what the A entry point
 *     is documented to return).
 *   - IDirectInputDevice7A, so a QueryInterface for DeviceA/Device2A/Device7A
 *     all succeed. The 7A vtable is a true superset with identical signatures.
 *   - GetDeviceState for the keyboard is real: it reports the Win32 keyboard
 *     state, so the controller mapping Wine-NX already performs (keys.txt ->
 *     key events) reaches the game.
 *   - GetDeviceData synthesises an edge-triggered stream from the same state,
 *     for games that use buffered input.
 *   - The mouse returns the standard DIMOUSESTATE, with no movement (Wine-NX
 *     drives the keyboard mapping, not the pointer).
 *
 * Everything else reports success or DIERR_UNSUPPORTED. Nothing here is a
 * reimplementation of DirectInput.
 *
 * Build: see tools/build-fifa07-shims.py (i686-w64-mingw32-gcc, -ldxguid).
 */
#define DIRECTINPUT_VERSION 0x0700
#define WIN32_LEAN_AND_MEAN
#include <windows.h>
#include <dinput.h>
#include <string.h>

#define DI_SHIM_NAME_A "Keyboard (Wine-NX DINPUT shim)"

/* ------------------------------------------------------------------ */
/* Extended keys: their DIK codes carry the 0x80 "extended" prefix.    */
/* ------------------------------------------------------------------ */
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

/* Fill the 256-byte DirectInput keyboard layout from the Win32 key state.
 * DirectInput uses PC scan codes, so every virtual key is converted back.
 *
 * The state is read with GetKeyboardState (the per-thread input queue), not
 * with the asynchronous polling call. Wine-NX synthesises the keys mapped from
 * keys.txt as real key events, so they land in the thread's input state; the
 * asynchronous poll does not observe them in this runtime, which is exactly
 * why the game answered no button when the shim polled it. */
static void read_keyboard(unsigned char out[256])
{
    UINT vk;

    memset(out, 0, 256);
    BYTE kb[256];
    GetKeyboardState(kb);
    for (vk = 1; vk < 256; vk++) {
        UINT sc;
        if (!(kb[vk] & 0x80)) continue;
        sc = MapVirtualKeyA(vk, MAPVK_VK_TO_VSC);
        if (!sc || sc > 0x7f) continue;
        /* An extended key (an arrow, Right Ctrl, Home/End...) carries a scan
         * code whose low byte is the very code of a numeric-keypad key:
         * MapVirtualKeyA(VK_LEFT, ...) is 0x4B, and 0x4B is DIK for NumPad 4.
         * Writing that bare code in addition to the 0x80-prefixed one therefore
         * reports every arrow as a keypad key -- and FIFA 07 reads the keypad
         * digits 2/4/6/8 as its in-game team-tactics hotkeys, so a left-stick
         * push (mapped to the arrow keys) changed tactics.  An extended key
         * must land ONLY on its 0x80-prefixed DirectInput code. */
        if (vk_is_extended(vk)) out[0x80 | sc] = 0x80;
        else out[sc] = 0x80;
    }
}

/* ------------------------------------------------------------------ */
/* Device object                                                      */
/* ------------------------------------------------------------------ */
typedef struct DiDevice {
    const IDirectInputDevice7AVtbl *lpVtbl;
    LONG ref;
    int is_mouse;
    int acquired;
    unsigned char prev_keys[256];
    DWORD prev_buttons;
    HWND hwnd;
} DiDevice;

static void fill_device_name(char *dst, size_t cap, const char *text)
{
    size_t n = strlen(text);
    if (n >= cap) n = cap - 1;
    memcpy(dst, text, n);
    dst[n] = 0;
}

static HRESULT STDMETHODCALLTYPE dev_QueryInterface(IDirectInputDevice7A *iface,
                                                    REFIID riid, void **out)
{
    if (!out) return E_POINTER;
    if (IsEqualIID(riid, &IID_IUnknown) ||
        IsEqualIID(riid, &IID_IDirectInputDeviceA) ||
        IsEqualIID(riid, &IID_IDirectInputDevice2A) ||
        IsEqualIID(riid, &IID_IDirectInputDevice7A)) {
        *out = iface;
        ((DiDevice *)iface)->ref++;
        return DI_OK;
    }
    *out = NULL;
    return E_NOINTERFACE;
}

static ULONG STDMETHODCALLTYPE dev_AddRef(IDirectInputDevice7A *iface)
{
    return (ULONG)InterlockedIncrement(&((DiDevice *)iface)->ref);
}

static ULONG STDMETHODCALLTYPE dev_Release(IDirectInputDevice7A *iface)
{
    DiDevice *dev = (DiDevice *)iface;
    LONG left = InterlockedDecrement(&dev->ref);
    if (!left) HeapFree(GetProcessHeap(), 0, dev);
    return (ULONG)left;
}

static HRESULT STDMETHODCALLTYPE dev_GetCapabilities(IDirectInputDevice7A *iface,
                                                     LPDIDEVCAPS caps)
{
    DiDevice *dev = (DiDevice *)iface;
    if (!caps) return E_POINTER;
    memset(caps, 0, caps->dwSize);
    caps->dwFlags = DIDC_ATTACHED | DIDC_EMULATED;
    caps->dwDevType = dev->is_mouse ? DIDEVTYPE_MOUSE : DIDEVTYPE_KEYBOARD;
    caps->dwAxes = dev->is_mouse ? 3 : 0;
    caps->dwButtons = dev->is_mouse ? 4 : 0;
    caps->dwPOVs = 0;
    return DI_OK;
}

static HRESULT STDMETHODCALLTYPE dev_EnumObjects(IDirectInputDevice7A *iface,
                                                 LPDIENUMDEVICEOBJECTSCALLBACKA cb,
                                                 LPVOID ref, DWORD flags)
{
    (void)iface; (void)cb; (void)ref; (void)flags;
    return DI_OK;   /* the game never needs the key table from us */
}

static HRESULT STDMETHODCALLTYPE dev_GetProperty(IDirectInputDevice7A *iface,
                                                 REFGUID guid, LPDIPROPHEADER hdr)
{
    (void)iface; (void)guid; (void)hdr;
    return DIERR_UNSUPPORTED;
}

static HRESULT STDMETHODCALLTYPE dev_SetProperty(IDirectInputDevice7A *iface,
                                                 REFGUID guid, LPCDIPROPHEADER hdr)
{
    (void)iface; (void)guid; (void)hdr;
    return DI_OK;
}

static HRESULT STDMETHODCALLTYPE dev_Acquire(IDirectInputDevice7A *iface)
{
    ((DiDevice *)iface)->acquired = 1;
    return DI_OK;
}

static HRESULT STDMETHODCALLTYPE dev_Unacquire(IDirectInputDevice7A *iface)
{
    ((DiDevice *)iface)->acquired = 0;
    return DI_OK;
}

static HRESULT STDMETHODCALLTYPE dev_GetDeviceState(IDirectInputDevice7A *iface,
                                                    DWORD cb, LPVOID data)
{
    DiDevice *dev = (DiDevice *)iface;

    if (!data) return E_POINTER;
    if (dev->is_mouse) {
        DIMOUSESTATE *ms = (DIMOUSESTATE *)data;
        if (cb < sizeof(DIMOUSESTATE)) return DIERR_INVALIDPARAM;
        memset(ms, 0, sizeof(*ms));
        return DI_OK;
    }
    if (cb < 256) return DIERR_INVALIDPARAM;
    read_keyboard((unsigned char *)data);
    return DI_OK;
}

/* Buffered input: emit one entry per key whose state changed since the last
 * call. dwOfs is the DirectInput key code. */
static HRESULT STDMETHODCALLTYPE dev_GetDeviceData(IDirectInputDevice7A *iface,
                                                   DWORD cbObject, LPDIDEVICEOBJECTDATA rgdod,
                                                   LPDWORD inout, DWORD flags)
{
    DiDevice *dev = (DiDevice *)iface;
    unsigned char now[256];
    DWORD want, made = 0, i;

    (void)flags;
    if (!inout) return E_POINTER;
    if (!dev->acquired) { *inout = 0; return DIERR_NOTACQUIRED; }
    if (dev->is_mouse) { *inout = 0; return DI_OK; }
    if (cbObject < sizeof(DIDEVICEOBJECTDATA)) return DIERR_INVALIDPARAM;

    read_keyboard(now);
    want = *inout;
    for (i = 0; i < 256 && made < want; i++) {
        if (now[i] == dev->prev_keys[i]) continue;
        rgdod[made].dwOfs = (DWORD)i;
        rgdod[made].dwData = now[i];
        rgdod[made].dwTimeStamp = GetTickCount();
        rgdod[made].dwSequence = 0;
        made++;
    }
    memcpy(dev->prev_keys, now, sizeof(now));
    *inout = made;
    return DI_OK;
}

static HRESULT STDMETHODCALLTYPE dev_SetDataFormat(IDirectInputDevice7A *iface,
                                                   LPCDIDATAFORMAT fmt)
{
    (void)iface;
    /* The layout is fixed: 256 key codes for the keyboard, DIMOUSESTATE for
     * the mouse. The game always passes c_dfDIKeyboard / c_dfDIMouse here. */
    return fmt ? DI_OK : E_POINTER;
}

static HRESULT STDMETHODCALLTYPE dev_SetEventNotification(IDirectInputDevice7A *iface,
                                                          HANDLE event)
{
    (void)iface; (void)event;
    return DI_OK;
}

static HRESULT STDMETHODCALLTYPE dev_SetCooperativeLevel(IDirectInputDevice7A *iface,
                                                         HWND hwnd, DWORD flags)
{
    (void)flags;
    ((DiDevice *)iface)->hwnd = hwnd;
    return DI_OK;
}

static HRESULT STDMETHODCALLTYPE dev_GetObjectInfo(IDirectInputDevice7A *iface,
                                                   LPDIDEVICEOBJECTINSTANCEA info,
                                                   DWORD obj, DWORD how)
{
    DiDevice *dev = (DiDevice *)iface;
    if (!info) return E_POINTER;
    if (how == DIPH_BYOFFSET && dev->is_mouse && obj != DIMOFS_X && obj != DIMOFS_Y &&
        obj != DIMOFS_Z && obj != DIMOFS_BUTTON0 && obj != DIMOFS_BUTTON1 &&
        obj != DIMOFS_BUTTON2 && obj != DIMOFS_BUTTON3)
        return DIERR_OBJECTNOTFOUND;
    memset(info, 0, info->dwSize);
    fill_device_name(info->tszName, sizeof(info->tszName), DI_SHIM_NAME_A);
    info->dwType = dev->is_mouse ? DIDFT_PSHBUTTON : DIDFT_BUTTON;
    info->wUsage = (WORD)obj;
    return DI_OK;
}

static HRESULT STDMETHODCALLTYPE dev_GetDeviceInfo(IDirectInputDevice7A *iface,
                                                   LPDIDEVICEINSTANCEA info)
{
    DiDevice *dev = (DiDevice *)iface;
    if (!info) return E_POINTER;
    memset(info, 0, info->dwSize);
    info->dwSize = sizeof(DIDEVICEINSTANCEA);
    info->guidInstance = dev->is_mouse ? GUID_SysMouse : GUID_SysKeyboard;
    info->guidProduct = info->guidInstance;
    info->dwDevType = dev->is_mouse ? DIDEVTYPE_MOUSE : DIDEVTYPE_KEYBOARD;
    fill_device_name(info->tszInstanceName, sizeof(info->tszInstanceName), DI_SHIM_NAME_A);
    fill_device_name(info->tszProductName, sizeof(info->tszProductName), DI_SHIM_NAME_A);
    return DI_OK;
}

static HRESULT STDMETHODCALLTYPE dev_RunControlPanel(IDirectInputDevice7A *iface,
                                                     HWND hwnd, DWORD flags)
{
    (void)iface; (void)hwnd; (void)flags;
    return DI_OK;
}

static HRESULT STDMETHODCALLTYPE dev_Initialize(IDirectInputDevice7A *iface,
                                                HINSTANCE hinst, DWORD version,
                                                REFGUID guid)
{
    (void)iface; (void)hinst; (void)version; (void)guid;
    return DI_OK;
}

static HRESULT STDMETHODCALLTYPE dev_CreateEffect(IDirectInputDevice7A *iface,
                                                  REFGUID guid, LPCDIEFFECT eff,
                                                  LPDIRECTINPUTEFFECT *out, LPUNKNOWN outer)
{
    (void)iface; (void)guid; (void)eff; (void)outer;
    if (out) *out = NULL;
    return DIERR_UNSUPPORTED;
}

static HRESULT STDMETHODCALLTYPE dev_EnumEffects(IDirectInputDevice7A *iface,
                                                 LPDIENUMEFFECTSCALLBACKA cb,
                                                 LPVOID ref, DWORD type)
{
    (void)iface; (void)cb; (void)ref; (void)type;
    return DI_OK;
}

static HRESULT STDMETHODCALLTYPE dev_GetEffectInfo(IDirectInputDevice7A *iface,
                                                   LPDIEFFECTINFOA info, REFGUID guid)
{
    (void)iface; (void)info; (void)guid;
    return DIERR_UNSUPPORTED;
}

static HRESULT STDMETHODCALLTYPE dev_GetForceFeedbackState(IDirectInputDevice7A *iface,
                                                           LPDWORD out)
{
    (void)iface;
    if (out) *out = 0;
    return DIERR_UNSUPPORTED;
}

static HRESULT STDMETHODCALLTYPE dev_SendForceFeedbackCommand(IDirectInputDevice7A *iface,
                                                              DWORD cmd)
{
    (void)iface; (void)cmd;
    return DIERR_UNSUPPORTED;
}

static HRESULT STDMETHODCALLTYPE dev_EnumCreatedEffectObjects(IDirectInputDevice7A *iface,
                                                              LPDIENUMCREATEDEFFECTOBJECTSCALLBACK cb,
                                                              LPVOID ref, DWORD flags)
{
    (void)iface; (void)cb; (void)ref; (void)flags;
    return DI_OK;
}

static HRESULT STDMETHODCALLTYPE dev_Escape(IDirectInputDevice7A *iface,
                                            LPDIEFFESCAPE esc)
{
    (void)iface; (void)esc;
    return DIERR_UNSUPPORTED;
}

static HRESULT STDMETHODCALLTYPE dev_Poll(IDirectInputDevice7A *iface)
{
    (void)iface;
    return DI_OK;
}

static HRESULT STDMETHODCALLTYPE dev_SendDeviceData(IDirectInputDevice7A *iface,
                                                    DWORD cbObject,
                                                    LPCDIDEVICEOBJECTDATA rgdod,
                                                    LPDWORD inout, DWORD flags)
{
    (void)iface; (void)cbObject; (void)rgdod; (void)flags;
    if (inout) *inout = 0;
    return DI_OK;
}

static HRESULT STDMETHODCALLTYPE dev_EnumEffectsInFile(IDirectInputDevice7A *iface,
                                                       LPCSTR file,
                                                       LPDIENUMEFFECTSINFILECALLBACK cb,
                                                       LPVOID ref, DWORD flags)
{
    (void)iface; (void)file; (void)cb; (void)ref; (void)flags;
    return DIERR_UNSUPPORTED;
}

static HRESULT STDMETHODCALLTYPE dev_WriteEffectToFile(IDirectInputDevice7A *iface,
                                                       LPCSTR file, DWORD entries,
                                                       LPDIFILEEFFECT rg, DWORD flags)
{
    (void)iface; (void)file; (void)entries; (void)rg; (void)flags;
    return DIERR_UNSUPPORTED;
}

/* Designated initialisers: the compiler checks every name and the order comes
 * from the header, so the vtable cannot drift from the real interface. */
static const IDirectInputDevice7AVtbl device_vtbl = {
    .QueryInterface            = dev_QueryInterface,
    .AddRef                    = dev_AddRef,
    .Release                   = dev_Release,
    .GetCapabilities           = dev_GetCapabilities,
    .EnumObjects               = dev_EnumObjects,
    .GetProperty               = dev_GetProperty,
    .SetProperty               = dev_SetProperty,
    .Acquire                   = dev_Acquire,
    .Unacquire                 = dev_Unacquire,
    .GetDeviceState            = dev_GetDeviceState,
    .GetDeviceData             = dev_GetDeviceData,
    .SetDataFormat             = dev_SetDataFormat,
    .SetEventNotification      = dev_SetEventNotification,
    .SetCooperativeLevel       = dev_SetCooperativeLevel,
    .GetObjectInfo             = dev_GetObjectInfo,
    .GetDeviceInfo             = dev_GetDeviceInfo,
    .RunControlPanel           = dev_RunControlPanel,
    .Initialize                = dev_Initialize,
    .CreateEffect              = dev_CreateEffect,
    .EnumEffects               = dev_EnumEffects,
    .GetEffectInfo             = dev_GetEffectInfo,
    .GetForceFeedbackState     = dev_GetForceFeedbackState,
    .SendForceFeedbackCommand  = dev_SendForceFeedbackCommand,
    .EnumCreatedEffectObjects  = dev_EnumCreatedEffectObjects,
    .Escape                    = dev_Escape,
    .Poll                      = dev_Poll,
    .SendDeviceData            = dev_SendDeviceData,
    .EnumEffectsInFile         = dev_EnumEffectsInFile,
    .WriteEffectToFile         = dev_WriteEffectToFile,
};

static IDirectInputDevice7A *device_create(int is_mouse)
{
    DiDevice *dev = (DiDevice *)HeapAlloc(GetProcessHeap(), HEAP_ZERO_MEMORY, sizeof(*dev));
    if (!dev) return NULL;
    dev->lpVtbl = &device_vtbl;
    dev->ref = 1;
    dev->is_mouse = is_mouse;
    dev->acquired = 0;
    if (!is_mouse) read_keyboard(dev->prev_keys);
    return (IDirectInputDevice7A *)dev;
}

/* ------------------------------------------------------------------ */
/* DirectInput object                                                 */
/* ------------------------------------------------------------------ */
typedef struct DiObject {
    const IDirectInputAVtbl *lpVtbl;
    LONG ref;
} DiObject;

static HRESULT STDMETHODCALLTYPE di_QueryInterface(IDirectInputA *iface,
                                                   REFIID riid, void **out)
{
    if (!out) return E_POINTER;
    /* A and 2A share this vtable. 7A adds CreateDeviceEx/EnumDevicesEx and
     * changes Initialize's signature, so it is deliberately NOT answered: a
     * game asking for it is better served by an honest E_NOINTERFACE. */
    if (IsEqualIID(riid, &IID_IUnknown) || IsEqualIID(riid, &IID_IDirectInputA) ||
        IsEqualIID(riid, &IID_IDirectInput2A)) {
        *out = iface;
        ((DiObject *)iface)->ref++;
        return DI_OK;
    }
    *out = NULL;
    return E_NOINTERFACE;
}

static ULONG STDMETHODCALLTYPE di_AddRef(IDirectInputA *iface)
{
    return (ULONG)InterlockedIncrement(&((DiObject *)iface)->ref);
}

static ULONG STDMETHODCALLTYPE di_Release(IDirectInputA *iface)
{
    DiObject *obj = (DiObject *)iface;
    LONG left = InterlockedDecrement(&obj->ref);
    if (!left) HeapFree(GetProcessHeap(), 0, obj);
    return (ULONG)left;
}

static HRESULT STDMETHODCALLTYPE di_CreateDevice(IDirectInputA *iface, REFGUID guid,
                                                 LPDIRECTINPUTDEVICEA *out,
                                                 LPUNKNOWN outer)
{
    (void)iface; (void)outer;
    if (!out) return E_POINTER;
    *out = NULL;
    if (IsEqualGUID(guid, &GUID_SysKeyboard))
        *out = (LPDIRECTINPUTDEVICEA)device_create(0);
    else if (IsEqualGUID(guid, &GUID_SysMouse))
        *out = (LPDIRECTINPUTDEVICEA)device_create(1);
    else
        return DIERR_DEVICENOTREG;
    return *out ? DI_OK : E_OUTOFMEMORY;
}

typedef struct EnumCtx { LPDIENUMDEVICESCALLBACKA cb; LPVOID ref; } EnumCtx;

static BOOL CALLBACK enum_one(LPCDIDEVICEINSTANCEA inst, LPVOID ref)
{
    return ((EnumCtx *)ref)->cb((LPDIDEVICEINSTANCEA)inst, ((EnumCtx *)ref)->ref);
}

static HRESULT STDMETHODCALLTYPE di_EnumDevices(IDirectInputA *iface, DWORD devtype,
                                                LPDIENUMDEVICESCALLBACKA cb,
                                                LPVOID ref, DWORD flags)
{
    EnumCtx ctx;
    static const int kinds[2] = {0, 1};
    int i;
    (void)iface; (void)flags;

    if (!cb) return E_POINTER;
    ctx.cb = cb;
    ctx.ref = ref;
    for (i = 0; i < 2; i++) {
        DIDEVICEINSTANCEA inst;
        DWORD type = kinds[i] ? DIDEVTYPE_MOUSE : DIDEVTYPE_KEYBOARD;
        if (devtype != DI8DEVCLASS_ALL && devtype != 0 && devtype != type) continue;
        memset(&inst, 0, sizeof(inst));
        inst.dwSize = sizeof(inst);
        inst.guidInstance = kinds[i] ? GUID_SysMouse : GUID_SysKeyboard;
        inst.guidProduct = inst.guidInstance;
        inst.dwDevType = type;
        fill_device_name(inst.tszInstanceName, sizeof(inst.tszInstanceName), DI_SHIM_NAME_A);
        fill_device_name(inst.tszProductName, sizeof(inst.tszProductName), DI_SHIM_NAME_A);
        if (!enum_one(&inst, &ctx)) break;   /* callback asked to stop */
    }
    return DI_OK;
}

static HRESULT STDMETHODCALLTYPE di_GetDeviceStatus(IDirectInputA *iface, REFGUID guid)
{
    (void)iface;
    /* Report only the devices this shim can serve as present. */
    if (IsEqualGUID(guid, &GUID_SysKeyboard) || IsEqualGUID(guid, &GUID_SysMouse)) return DI_OK;
    return DI_NOTATTACHED;
}

static HRESULT STDMETHODCALLTYPE di_RunControlPanel(IDirectInputA *iface, HWND hwnd, DWORD flags)
{
    (void)iface; (void)hwnd; (void)flags;
    return DI_OK;
}

static HRESULT STDMETHODCALLTYPE di_Initialize(IDirectInputA *iface, HINSTANCE hinst, DWORD version)
{
    (void)iface; (void)hinst; (void)version;
    return DI_OK;
}

static const IDirectInputAVtbl directinput_vtbl = {
    .QueryInterface  = di_QueryInterface,
    .AddRef          = di_AddRef,
    .Release         = di_Release,
    .CreateDevice    = di_CreateDevice,
    .EnumDevices     = di_EnumDevices,
    .GetDeviceStatus = di_GetDeviceStatus,
    .RunControlPanel = di_RunControlPanel,
    .Initialize      = di_Initialize,
};

/* ------------------------------------------------------------------ */
/* The one export fifa07.exe imports                                  */
/* ------------------------------------------------------------------ */
HRESULT WINAPI DirectInputCreateA(HINSTANCE hinst, DWORD version,
                                  LPDIRECTINPUTA *out, LPUNKNOWN outer)
{
    DiObject *obj;
    (void)hinst; (void)version; (void)outer;

    if (!out) return E_POINTER;
    *out = NULL;
    obj = (DiObject *)HeapAlloc(GetProcessHeap(), HEAP_ZERO_MEMORY, sizeof(*obj));
    if (!obj) return E_OUTOFMEMORY;
    obj->lpVtbl = &directinput_vtbl;
    obj->ref = 1;
    *out = (LPDIRECTINPUTA)obj;
    return DI_OK;
}

BOOL WINAPI DllMain(HINSTANCE hinst, DWORD reason, LPVOID reserved)
{
    (void)hinst; (void)reason; (void)reserved;
    return TRUE;
}
