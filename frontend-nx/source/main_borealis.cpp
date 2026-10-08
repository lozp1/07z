// =============================================================================
// 07z — NRO hermano (frontend) para FIFA 07 en Nintendo Switch
// -----------------------------------------------------------------------------
// Basado en FileZzz (C++20 + Borealis + libnx). Reutiliza literalmente:
//   - QrCodeView  : generador/renderizador QR vectorial (NanoVG + qrcodegen)
//   - la vista de donaciones (resources/romfs/xml/view_about.xml), con UN QR
//   - SplashActivity / el patron de arranque (registerXMLView / mainLoop)
//   - la estetica nativa Horizon (temas Dark / AMOLED)
//   - el patron de FileZzz de "cubrir y ocultar" la Activity anterior
// Lo unico nuevo es el menu principal (view_menu.xml) y el enlazado de pantallas.
// =============================================================================

#include <switch.h>
#include <borealis.hpp>
#include <nanovg.h>
#include <sys/stat.h>
#include <unistd.h>
#include <cstdio>
#include <cstdlib>
#include <cmath>
#include <algorithm>
#include <functional>
#include <string>
#include <utility>
#include <vector>

#include <borealis/views/hint.hpp>
#include <borealis/views/rectangle.hpp>

#include "qrcodegen.hpp"
#include "config.hpp"

using namespace brls::literals;

// --- Raiz del runtime / juego (UNICO punto de cambio de rutas) --------------
// La carpeta portable del producto vive en sdmc:/switch/fifa07. Para no romper
// la instalacion clasica (runtime + prefijo de Wine en sdmc:/switch/wine) se
// admite esa raiz como respaldo. IMPORTANTE: la eleccion NO se hace mirando un
// unico fichero, porque el paquete portable puede traer drive_c/FIFA 07/ VACIA:
// un runtime suelto en fifa07 no implica que el juego este ahi. Por eso se
// comprueba la existencia REAL (stat) del runtime Y del .exe del juego, y gana
// la raiz que tenga el juego (que es lo que de verdad hay que lanzar).
static const char* PRODUCT_ROOT = "sdmc:/switch/fifa07";
static const char* LEGACY_ROOT  = "sdmc:/switch/wine";

static const char* RUNTIME_NRO_REL = "/wine-nx-runtime.nro";
static const char* GAME_EXE_REL    = "/drive_c/FIFA 07/fifa07.exe";

// Existencia REAL en disco. Se usa stat() (y no access()) porque access() en
// newlib resuelve via stat y aqui interesa el mismo camino que usa fopen: solo
// cuenta si el fichero esta de verdad en la tarjeta.
static bool pathExists(const std::string& p) {
    struct stat st;
    return stat(p.c_str(), &st) == 0;
}

static std::string computeWineRoot() {
    const std::string pRt   = std::string(PRODUCT_ROOT) + RUNTIME_NRO_REL;
    const std::string lRt   = std::string(LEGACY_ROOT)  + RUNTIME_NRO_REL;
    const std::string pGame = std::string(PRODUCT_ROOT) + GAME_EXE_REL;
    const std::string lGame = std::string(LEGACY_ROOT)  + GAME_EXE_REL;

    const bool pRtOk   = pathExists(pRt);
    const bool lRtOk   = pathExists(lRt);
    const bool pGameOk = pathExists(pGame);
    const bool lGameOk = pathExists(lGame);

    // 1) Instalacion COMPLETA (runtime + juego) en una raiz: manda esa raiz.
    if (pRtOk && pGameOk) return PRODUCT_ROOT;
    if (lRtOk && lGameOk) return LEGACY_ROOT;
    // 2) El juego (fifa07.exe) solo esta en una raiz: es la que hay que lanzar.
    if (pGameOk && !lGameOk) return PRODUCT_ROOT;
    if (lGameOk && !pGameOk) return LEGACY_ROOT;
    // 3) Sin juego localizable todavia: la raiz que tenga el runtime
    //    (sdmc:/switch/fifa07 se prefiere; si solo esta en wine, se usa wine).
    if (pRtOk) return PRODUCT_ROOT;
    if (lRtOk) return LEGACY_ROOT;
    // 4) No se encontro nada: raiz clasica. launchGame() avisara en pantalla.
    return LEGACY_ROOT;
}

// Cache de la raiz resuelta. Se re-resuelve en main() y justo antes de lanzar el
// juego (por si los ficheros aparecieron/desaparecieron entre medias).
static std::string& wineRootRef() {
    static std::string root = computeWineRoot();
    return root;
}
static const std::string& wineRoot() { return wineRootRef(); }
static void refreshWineRoot() { wineRootRef() = computeWineRoot(); }

// Une la raiz elegida con una ruta relativa (rel empieza siempre por '/').
static std::string winePath(const char* rel) { return wineRoot() + rel; }

// --- Enlace de donacion (unico punto de cambio: QR + texto lo usan) ----------
static const char* PAYPAL_URL = "https://paypal.me/francopaololg";

// -----------------------------------------------------------------------------
// Fondo de pantalla (mecanismo portado de FileZzz + fondo por defecto del romfs)
// -----------------------------------------------------------------------------
// El fondo efectivo es el elegido por el usuario si existe; si no, la imagen
// incluida en el romfs del NRO (resources/romfs/img/default_wallpaper.jpg).
static std::string effectiveWallpaperPath() {
    // Fondo elegido por el usuario (si el fichero existe de verdad en disco).
    const std::string& p = AppConfig::get().wallpaperPath;
    if (!p.empty() && access(p.c_str(), F_OK) == 0) return p;
    // Por defecto: la imagen incluida en el romfs del NRO. No se comprueba con
    // access() porque la carga la realiza NanoVG directamente desde el romfs.
    return FIFA_DEFAULT_WALLPAPER;
}

static bool hasWallpaper() {
    return !effectiveWallpaperPath().empty();
}

// -----------------------------------------------------------------------------
// Tema nativo Horizon (adaptado de FileZzz). Temas soportados: "Dark" y
// "AMOLED" (por defecto). El tema claro (Light) se elimino de la app.
// Con fondo de pantalla activo, los fondos solidos pasan a ser translucidos
// para dejar ver la imagen.
// -----------------------------------------------------------------------------
static void applyAppTheme(const std::string& themeName) {
    bool hasWp = hasWallpaper();

    if (themeName == "AMOLED") {
        brls::Theme::getDarkTheme().addColor("brls/background", hasWp ? nvgRGBA(0, 0, 0, 0) : nvgRGB(0, 0, 0));
        brls::Theme::getDarkTheme().addColor("brls/clear", nvgRGB(0, 0, 0));
        brls::Theme::getDarkTheme().addColor("brls/sidebar/background", hasWp ? nvgRGBA(10, 10, 10, 220) : nvgRGB(8, 8, 8));
        brls::Theme::getDarkTheme().addColor("brls/sidebar/separator", nvgRGB(28, 28, 30));
        brls::Theme::getDarkTheme().addColor("brls/applet_frame/separator", nvgRGB(40, 40, 45));
        brls::Theme::getDarkTheme().addColor("brls/highlight/background", nvgRGB(22, 22, 24));
        brls::Theme::getDarkTheme().addColor("brls/accent", nvgRGB(0, 242, 254));
        brls::Theme::getDarkTheme().addColor("brls/text", nvgRGB(255, 255, 255));
        brls::Theme::getDarkTheme().addColor("brls/text_disabled", nvgRGB(156, 163, 175));
        brls::Theme::getDarkTheme().addColor("brls/sidebar/active_item", nvgRGB(0, 242, 254));
        // AMOLED: alpha 38/255 = ~15% opaco (85% transparente).
        brls::Theme::getDarkTheme().addColor("brls/menu/row", nvgRGBA(18, 18, 18, 38));
        brls::Application::getPlatform()->setThemeVariant(brls::ThemeVariant::DARK);
    } else { // "Dark"
        brls::Theme::getDarkTheme().addColor("brls/background", hasWp ? nvgRGBA(45, 45, 45, 0) : nvgRGB(45, 45, 45));
        brls::Theme::getDarkTheme().addColor("brls/clear", nvgRGB(45, 45, 45));
        brls::Theme::getDarkTheme().addColor("brls/sidebar/background", hasWp ? nvgRGBA(35, 38, 44, 220) : nvgRGB(35, 38, 44));
        brls::Theme::getDarkTheme().addColor("brls/sidebar/separator", nvgRGB(60, 64, 72));
        brls::Theme::getDarkTheme().addColor("brls/applet_frame/separator", nvgRGB(80, 85, 95));
        brls::Theme::getDarkTheme().addColor("brls/highlight/background", nvgRGB(40, 44, 52));
        brls::Theme::getDarkTheme().addColor("brls/accent", nvgRGB(56, 189, 248));
        brls::Theme::getDarkTheme().addColor("brls/text", nvgRGB(255, 255, 255));
        brls::Theme::getDarkTheme().addColor("brls/text_disabled", nvgRGB(156, 163, 175));
        brls::Theme::getDarkTheme().addColor("brls/sidebar/active_item", nvgRGB(56, 189, 248));
        // Dark: alpha 46/255 = ~18% opaco (82% transparente).
        brls::Theme::getDarkTheme().addColor("brls/menu/row", nvgRGBA(42, 46, 54, 46));
        brls::Application::getPlatform()->setThemeVariant(brls::ThemeVariant::DARK);
    }
}

// -----------------------------------------------------------------------------
// Contenedor raiz que dibuja el fondo de pantalla detras de su contenido.
// Es un brls::Box (axis column), asi que puede sustituir a la raiz normal sin
// cambiar el resto del codigo (getView() y el foco siguen funcionando).
// -----------------------------------------------------------------------------
class WallpaperFrame : public brls::Box {
public:
    WallpaperFrame() : brls::Box(brls::Axis::COLUMN) {
        this->setWidthPercentage(100);
        this->setHeightPercentage(100);
    }

    explicit WallpaperFrame(brls::View* content) : WallpaperFrame() {
        if (content) {
            content->setWidthPercentage(100);
            content->setGrow(1.0f);
            this->addView(content);
        }
    }

    void draw(NVGcontext* vg, float x, float y, float width, float height,
              brls::Style style, brls::FrameContext* ctx) override {
        // La ruta del fondo se resuelve UNA sola vez (o cuando el usuario cambia
        // la preferencia). Antes se recalculaba en CADA frame: construia un
        // std::string y, con fondo personalizado, hacia un access()/stat() a la
        // tarjeta SD por frame -> tirones en el menu. Ahora, si nada cambia, es
        // O(1) y no toca el sistema de ficheros.
        const std::string& cfgWp = AppConfig::get().wallpaperPath;
        if (!m_wpResolved || m_cfgWallpaper != cfgWp) {
            m_cfgWallpaper = cfgWp;
            m_wpPath       = effectiveWallpaperPath();
            m_wpResolved   = true;
        }
        const std::string& wpPath = m_wpPath;

        if (!wpPath.empty()) {
            if (m_lastWpPath != wpPath) {
                if (m_wpImage > 0) nvgDeleteImage(vg, m_wpImage);
                m_wpImage   = nvgCreateImage(vg, wpPath.c_str(), 0);
                m_lastWpPath = wpPath;
            }
            if (m_wpImage > 0) {
                float op = AppConfig::get().wallpaperOpacity;
                if (op < 0.0f) op = 0.0f;
                if (op > 1.0f) op = 1.0f;

                NVGpaint imgPaint = nvgImagePattern(vg, x, y, width, height, 0.0f, m_wpImage, op);
                nvgBeginPath(vg);
                nvgRect(vg, x, y, width, height);
                nvgFillPaint(vg, imgPaint);
                nvgFill(vg);

                // Tinte de contraste para mantener legible el texto (tema oscuro).
                NVGcolor overlay = nvgRGBA(20, 20, 20, (int)((1.0f - op) * 220.0f));
                nvgBeginPath(vg);
                nvgRect(vg, x, y, width, height);
                nvgFillColor(vg, overlay);
                nvgFill(vg);
            }
        } else if (m_wpImage > 0) {
            nvgDeleteImage(vg, m_wpImage);
            m_wpImage    = 0;
            m_lastWpPath = "";
        }

        brls::Box::draw(vg, x, y, width, height, style, ctx);
    }

private:
    int m_wpImage = 0;
    std::string m_lastWpPath;
    std::string m_wpPath;          // ruta de fondo ya resuelta (cache)
    std::string m_cfgWallpaper;    // preferencia con la que se resolvio
    bool m_wpResolved = false;
};

static brls::View* wrapWallpaper(brls::View* content) {
    return new WallpaperFrame(content);
}

// -----------------------------------------------------------------------------
// Generador y renderizador vectorial de Codigo QR (copiado literal de FileZzz)
// -----------------------------------------------------------------------------
class QrCodeView : public brls::View {
public:
    QrCodeView(const std::string& text, float size = 180.0f) : m_text(text), m_qrSize(size) {
        this->setWidth(size);
        this->setHeight(size);
        generateQr();
    }

    void setText(const std::string& text) {
        if (m_text != text) {
            m_text = text;
            generateQr();
        }
    }

    void generateQr() {
        if (m_text.empty()) {
            m_modules.clear();
            m_size = 0;
            return;
        }
        try {
            qrcodegen::QrCode qr = qrcodegen::QrCode::encodeText(m_text.c_str(), qrcodegen::QrCode::Ecc::MEDIUM);
            m_size = qr.getSize();
            m_modules.resize(m_size * m_size);
            for (int y = 0; y < m_size; y++) {
                for (int x = 0; x < m_size; x++) {
                    m_modules[y * m_size + x] = qr.getModule(x, y);
                }
            }
        } catch (...) {
            m_modules.clear();
            m_size = 0;
        }
    }

    void draw(NVGcontext* vg, float x, float y, float width, float height, brls::Style style, brls::FrameContext* ctx) override {
        (void)style;
        (void)ctx;
        if (m_modules.empty() || m_size <= 0) return;

        // Fondo BLANCO solido que cubre TODO el area del widget: incluye el
        // margen blanco obligatorio ('quiet zone') alrededor del QR, que es lo
        // que ANY lector necesita para localizarlo. La esquina redondeada (12px)
        // queda muy por dentro de la quiet zone, asi que no recorta modulos.
        nvgBeginPath(vg);
        nvgRoundedRect(vg, x, y, width, height, 12.0f);
        nvgFillColor(vg, nvgRGB(255, 255, 255));
        nvgFill(vg);

        // Quiet zone de 4 modulos (estandar QR): modulos mas gruesos y margen
        // blanco generoso alrededor -> el movil lo detecta con facilidad.
        const float quietModules = 4.0f;
        float moduleSize = width / ((float)m_size + quietModules * 2.0f);
        float pad        = quietModules * moduleSize;

        nvgBeginPath(vg);
        for (int row = 0; row < m_size; row++) {
            for (int col = 0; col < m_size; col++) {
                if (m_modules[row * m_size + col]) {
                    nvgRect(vg, x + pad + col * moduleSize,
                            y + pad + row * moduleSize,
                            moduleSize + 0.25f, moduleSize + 0.25f);
                }
            }
        }
        // Negro puro sobre blanco puro: maximo contraste para la camara.
        nvgFillColor(vg, nvgRGB(0, 0, 0));
        nvgFill(vg);
    }

private:
    std::string m_text;
    float m_qrSize;
    int m_size = 0;
    std::vector<bool> m_modules;
};

// -----------------------------------------------------------------------------
// Lanzamiento del juego (hand-off NRO -> runtime wine-nx)
// -----------------------------------------------------------------------------
// IMPORTANTE (documentado en dist/fifa07-diag/LEEME.txt y confirmado en consola):
//   El runtime wine-nx SOLO puede cargar fifa07.exe con un espacio de
//   direcciones de 32 bits no-alias, porque fifa07.exe tiene
//   IMAGE_FILE_RELOCS_STRIPPED=1 y solo se mapea en su ImageBase 0x400000.
//   Ese espacio NO lo decide este NRO: lo hereda de quien lo lanza. Abierto
//   desde el Homebrew Menu somos un applet y el chainloader (nx-hbloader)
//   propaga AppletType_LibraryApplet al siguiente NRO, que hereda 64 bits; el
//   runtime entonces no puede mapear el juego, termina solo y se vuelve al
//   Homebrew Menu. En modo aplicacion (icono del HOME / forwarder con
//   AddressSpaceType=2) si se juega, asi que ahi se pasa el .exe como argv[1].
// -----------------------------------------------------------------------------
// Definida mas abajo (tras MessageActivity): aviso a pantalla completa.
static void showLaunchWarning(const std::string& title, const std::string& message);

static void launchGame() {
#ifdef __SWITCH__
    // Re-resolver la raiz justo antes de lanzar: si los ficheros estan en
    // sdmc:/switch/wine (instalacion clasica) en vez de en fifa07, aqui se elige
    // la raiz correcta para TODAS las rutas (runtime, exe, keys, config, log).
    refreshWineRoot();

    AppletType at = appletGetAppletType();
    bool appMode = (at == AppletType_Application || at == AppletType_SystemApplication);

    std::string runtime = winePath(RUNTIME_NRO_REL);
    std::string game    = winePath(GAME_EXE_REL);

    // Antes del hand-off, comprobar de VERDAD que existen el runtime y el juego.
    // Si falta cualquiera de los dos se avisa en pantalla en vez de salir en
    // silencio (que es lo que parecia "no pasa nada / se cierra").
    if (!pathExists(runtime)) {
        brls::Logger::error("Jugar: no existe el runtime ({})", runtime);
        showLaunchWarning("Falta el runtime de Wine",
                          "No se encuentra wine-nx-runtime.nro ni en sdmc:/switch/fifa07 "
                          "ni en sdmc:/switch/wine.\n\n"
                          "Copia wine-nx-runtime.nro en una de esas dos carpetas y vuelve a intentarlo.");
        return;
    }
    if (!pathExists(game)) {
        brls::Logger::error("Jugar: no existe el juego ({})", game);
        showLaunchWarning("No se encuentra FIFA 07",
                          "No se encuentra fifa07.exe:\n" + game + "\n\n"
                          "Copia tu instalacion de FIFA 07 en la carpeta 'drive_c/FIFA 07/' "
                          "de sdmc:/switch/fifa07 o de sdmc:/switch/wine.");
        return;
    }

    if (!appMode) {
        // Lanzado como applet (Homebrew Menu): no hereda un espacio de
        // direcciones de 32 bits, asi que el runtime NO podria mapear
        // fifa07.exe. Y para no mostrar NADA de Wine, NO se abre su catalogo:
        // se avisa y el frontend se queda donde esta. Para jugar hay que
        // entrar desde el icono del HOME (NSP forwarder, modo aplicacion).
        brls::Logger::info("Jugar: applet (64-bit); no se lanza el runtime");
        brls::Application::notify(std::string("Desde el menu de inicio / From the HOME menu"));
        return;
    }

    // Modo aplicacion (icono del HOME / forwarder, 32 bits no-alias): hand-off
    // invisible al runtime, pasandole el .exe del juego como argv[1]. El runtime
    // entra directo al juego sin mostrar su catalogo ni ninguna pantalla.
    std::string argvStr = "\"" + runtime + "\" \"" + game + "\"";
    Result rc = envSetNextLoad(runtime.c_str(), argvStr.c_str());
    brls::Logger::info("Jugar: appletType={} appMode={} envHasNextLoad={} rc=0x{:08x} argv={}",
                       (int)at, appMode, envHasNextLoad(), (unsigned)rc, argvStr);

    if (!envHasNextLoad() || R_FAILED(rc)) {
        // Sin chainloader no hay forma de lanzar el runtime: avisar en vez de
        // cerrar la app (que es lo que parecia "no pasa nada").
        brls::Logger::error("envSetNextLoad fallo: no hay chainloader");
        brls::Application::notify("hints/launch_fail"_i18n);
        return;
    }
#endif
    brls::Application::quit();
}

// -----------------------------------------------------------------------------
// Pantalla simple de aviso ("proximamente") para secciones aun no implementadas
// -----------------------------------------------------------------------------
class MessageActivity : public brls::Activity {
public:
    MessageActivity(std::string title, std::string message)
        : m_title(std::move(title)), m_msg(std::move(message)) {}

    brls::View* createContentView() override {
        brls::Box* root = new brls::Box(brls::Axis::COLUMN);
        root->setGrow(1.0f);
        root->setAlignItems(brls::AlignItems::CENTER);
        root->setJustifyContent(brls::JustifyContent::CENTER);
        root->setBackgroundColor(brls::Application::getTheme()["brls/background"]);

        brls::Label* title = new brls::Label();
        title->setText(m_title);
        title->setFontSize(30);
        title->setTextColor(brls::Application::getTheme()["brls/text"]);
        title->setMarginBottom(16);
        root->addView(title);

        brls::Label* msg = new brls::Label();
        msg->setText(m_msg);
        msg->setFontSize(17);
        // Ancho acotado + wrapping: los avisos largos (p.ej. "falta fifa07.exe")
        // se reparten en varias lineas en vez de salirse de la pantalla.
        msg->setWidth(1040.0f);
        msg->setIsWrapping(true);
        msg->setHorizontalAlign(brls::HorizontalAlign::CENTER);
        msg->setTextColor(brls::Application::getTheme()["brls/text_disabled"]);
        root->addView(msg);

        return wrapWallpaper(root);
    }

    void onContentAvailable() override {
        brls::Activity::onContentAvailable();
        brls::View* root = this->getContentView();
        if (root) {
            root->setFocusable(true);
            root->setHideHighlight(true);
            brls::Application::giveFocus(root);
            root->registerAction("hints/back"_i18n, brls::BUTTON_B, [](brls::View*) {
                brls::Application::popActivity();
                return true;
            });
        }
    }

private:
    std::string m_title;
    std::string m_msg;
};

// Aviso a pantalla completa (lo usa launchGame cuando falta el runtime o el
// juego, en vez de cerrar la app sin decir nada).
static void showLaunchWarning(const std::string& title, const std::string& message) {
    brls::Application::pushActivity(new MessageActivity(title, message));
}

// -----------------------------------------------------------------------------
// "Acerca de y donaciones": view_about.xml con UN UNICO codigo QR (PayPal).
// -----------------------------------------------------------------------------
class AboutActivity : public brls::Activity {
public:
    brls::View* createContentView() override {
        return wrapWallpaper(brls::View::createFromXMLFile("romfs:/xml/view_about.xml"));
    }

    void onContentAvailable() override {
        brls::Activity::onContentAvailable();

        // QR de donacion: PayPal (el unico que queda). Mas grande y con quiet
        // zone de 4 modulos para que los moviles lo detecten.
        if (brls::Box* box = dynamic_cast<brls::Box*>(this->getView("boxCoffeeQr"))) {
            box->addView(new QrCodeView(PAYPAL_URL, 360.0f));
        }

        // El enlace en texto sale de la MISMA constante que el QR: cambiar
        // PAYPAL_URL actualiza las dos cosas a la vez.
        if (brls::Label* lbl = dynamic_cast<brls::Label*>(this->getView("lblDonateUrl"))) {
            std::string shown = PAYPAL_URL;
            const std::string scheme = "https://";
            if (shown.rfind(scheme, 0) == 0) shown.erase(0, scheme.size());
            lbl->setText(shown);
        }

        // IMPORTANTE: la pantalla toma el foco (y oculta su resaltado) igual que
        // la Activity contenedora de FileZzz. Sin esto, Application::giveFocus()
        // ignora el nullptr y el foco se queda en la fila del menu, cuyo
        // resaltado se sigue dibujando ENCIMA de esta pantalla (el bug de las
        // "opciones fijadas por detras").
        if (brls::View* root = this->getContentView()) {
            root->setFocusable(true);
            root->setHideHighlight(true);
            brls::Application::giveFocus(root);
        }

        // B vuelve al menu principal
        this->registerAction("hints/back"_i18n, brls::BUTTON_B, [](brls::View*) {
            brls::Application::popActivity();
            return true;
        });
    }
};

// =============================================================================
// CONFIGURACION DE MANDOS
// -----------------------------------------------------------------------------
// Lee y escribe el mapa de controles del runtime wine-nx. El fichero real del
// juego es  sdmc:/switch/wine/drive_c/FIFA 07/fifa07.keys.txt  (manda sobre los
// otros dos) y ademas se sincronizan:
//     sdmc:/switch/wine/keys.txt
//     sdmc:/switch/wine/config/keys.txt
// Formato: una linea  NOMBRE=VALOR  por control (VALOR = codigo de tecla virtual
// de Windows en hex), mas lineas de modo (input-mode=2, LSTICK=keys|mouse...).
// Al guardar se conservan intactas todas las lineas desconocidas y comentarios.
// =============================================================================

// Rutas derivadas de wineRoot() (funciones, no constantes: se resuelven en main).
static std::string keysGamePath()   { return winePath("/drive_c/FIFA 07/fifa07.keys.txt"); }
static std::string keysRootPath()   { return winePath("/keys.txt"); }
static std::string keysConfigPath() { return winePath("/config/keys.txt"); }

struct ControlDef { const char* name; const char* label; };

static const ControlDef kControls[] = {
    { "UP",     "D-Pad Arriba"         },
    { "DOWN",   "D-Pad Abajo"          },
    { "LEFT",   "D-Pad Izquierda"      },
    { "RIGHT",  "D-Pad Derecha"        },
    { "LUP",    "Stick L Arriba"       },
    { "LDOWN",  "Stick L Abajo"        },
    { "LLEFT",  "Stick L Izquierda"    },
    { "LRIGHT", "Stick L Derecha"      },
    { "A",      "A  (boton derecho)"   },
    { "B",      "B  (boton inferior)"  },
    { "X",      "X  (boton superior)"  },
    { "Y",      "Y  (boton izquierdo)" },
    { "L",      "L  (gatillo sup. izq.)"  },
    { "R",      "R  (gatillo sup. der.)"  },
    { "ZL",     "ZL (gatillo inf. izq.)"  },
    { "ZR",     "ZR (gatillo inf. der.)"  },
    { "PLUS",   "Plus  (+)"            },
    { "MINUS",  "Minus (-)"            },
    { "STICKL", "Click Stick L"        },
    { "STICKR", "Click Stick R"        },
    { "RUP",    "Stick R Arriba"       },
    { "RDOWN",  "Stick R Abajo"        },
    { "RLEFT",  "Stick R Izquierda"    },
    { "RRIGHT", "Stick R Derecha"      },
};
static const int kControlCount = (int)(sizeof(kControls) / sizeof(kControls[0]));

// Perfil Switch ya decidido por el usuario (lo que hay hoy en la tarjeta).
static const int kControlDefaults[kControlCount] = {
    0x26, 0x28, 0x25, 0x27,   // UP DOWN LEFT RIGHT
    0x26, 0x28, 0x25, 0x27,   // LUP LDOWN LLEFT LRIGHT
    0x0d, 0x1b, 0x57, 0x41,   // A B X Y
    0x10, 0x45, 0x53, 0x44,   // L R ZL ZR
    0x1b, 0x0d, 0x5a, 0x51,   // PLUS MINUS STICKL STICKR
    0x10, 0x5a, 0x00, 0x00,   // RUP RDOWN RLEFT RRIGHT  (ver docs/CONTROLES-DIAGNOSTICO.md)
};

static std::vector<int> g_controlValues;
static bool g_controlValuesLoaded = false;

// Teclas virtuales de Windows que se pueden asignar desde el selector.
struct KeyOption { int vk; const char* name; };
static const KeyOption kKeyOptions[] = {
    { 0x00, "Ninguna" },
    { 0x26, "Flecha Arriba" },   { 0x28, "Flecha Abajo" },
    { 0x25, "Flecha Izquierda" },{ 0x27, "Flecha Derecha" },
    { 0x0d, "Enter" },           { 0x1b, "Escape" },        { 0x20, "Espacio" },
    { 0x10, "Mayus (Shift)" },   { 0x11, "Ctrl" },          { 0x09, "Tab" },
    { 0x08, "Retroceso" },       { 0x2e, "Suprimir" },      { 0x14, "Bloq Mayus" },
    { 0x51, "Q" }, { 0x57, "W" }, { 0x45, "E" }, { 0x52, "R" }, { 0x54, "T" },
    { 0x59, "Y" }, { 0x55, "U" }, { 0x49, "I" }, { 0x4f, "O" }, { 0x50, "P" },
    { 0x41, "A" }, { 0x53, "S" }, { 0x44, "D" }, { 0x46, "F" }, { 0x47, "G" },
    { 0x48, "H" }, { 0x4a, "J" }, { 0x4b, "K" }, { 0x4c, "L" },
    { 0x5a, "Z" }, { 0x58, "X" }, { 0x43, "C" }, { 0x56, "V" }, { 0x42, "B" },
    { 0x4e, "N" }, { 0x4d, "M" },
    { 0x30, "0" }, { 0x31, "1" }, { 0x32, "2" }, { 0x33, "3" }, { 0x34, "4" },
    { 0x35, "5" }, { 0x36, "6" }, { 0x37, "7" }, { 0x38, "8" }, { 0x39, "9" },
    { 0x24, "Inicio" }, { 0x23, "Fin" }, { 0x21, "RePag" }, { 0x22, "AvPag" },
    { 0xbc, "Coma" }, { 0xbe, "Punto" }, { 0xbd, "Guion" }, { 0xbb, "Igual" },
    { 0x70, "F1" }, { 0x71, "F2" }, { 0x72, "F3" }, { 0x73, "F4" }, { 0x74, "F5" },
};
static const int kKeyOptionCount = (int)(sizeof(kKeyOptions) / sizeof(kKeyOptions[0]));

static std::string trimStr(const std::string& s) {
    size_t a = 0, b = s.size();
    while (a < b && (unsigned char)s[a] <= ' ') ++a;
    while (b > a && (unsigned char)s[b - 1] <= ' ') --b;
    return s.substr(a, b - a);
}

static std::string upperStr(const std::string& s) {
    std::string r = s;
    for (char& c : r) if (c >= 'a' && c <= 'z') c = (char)(c - 'a' + 'A');
    return r;
}

static int controlIndexByName(const std::string& rawName) {
    std::string name = upperStr(trimStr(rawName));
    for (int i = 0; i < kControlCount; ++i)
        if (name == kControls[i].name) return i;
    return -1;
}

static const char* keyNameFor(int vk) {
    for (int i = 0; i < kKeyOptionCount; ++i)
        if (kKeyOptions[i].vk == vk) return kKeyOptions[i].name;
    return nullptr;
}

static std::string readWholeFile(const char* path) {
    FILE* f = fopen(path, "rb");
    if (!f) return std::string();
    std::string s;
    char buf[4096];
    size_t n;
    while ((n = fread(buf, 1, sizeof(buf), f)) > 0) s.append(buf, n);
    fclose(f);
    return s;
}

static bool writeWholeFile(const char* path, const std::string& content) {
    FILE* f = fopen(path, "wb");
    if (!f) return false;
    size_t n = fwrite(content.data(), 1, content.size(), f);
    fclose(f);
    return n == content.size();
}

static void ensureKeysDirs() {
    mkdir("sdmc:/switch", 0777);
    mkdir(wineRoot().c_str(), 0777);
    mkdir(winePath("/config").c_str(), 0777);
    mkdir(winePath("/drive_c").c_str(), 0777);
    mkdir(winePath("/drive_c/FIFA 07").c_str(), 0777);
}

// Aplica NOMBRE=VALOR de un fichero sobre el mapa en memoria (ignora el resto).
static void applyKeysContent(const std::string& content) {
    size_t start = 0;
    while (start < content.size()) {
        size_t nl = content.find('\n', start);
        std::string line = (nl == std::string::npos) ? content.substr(start) : content.substr(start, nl - start);
        start = (nl == std::string::npos) ? content.size() : nl + 1;
        if (!line.empty() && line.back() == 0x0d) line.pop_back();
        std::string t = trimStr(line);
        if (t.empty() || t[0] == '#') continue;
        size_t eq = t.find('=');
        if (eq == std::string::npos) continue;
        int idx = controlIndexByName(t.substr(0, eq));
        if (idx < 0) continue;
        std::string val = trimStr(t.substr(eq + 1));
        if (val.empty()) continue;
        g_controlValues[idx] = (int)strtol(val.c_str(), nullptr, 0) & 0xffff;
    }
}

// Orden de precedencia del runtime: config < wine/keys.txt < fichero propio del juego.
static void loadControls() {
    g_controlValues.assign(kControlDefaults, kControlDefaults + kControlCount);
    applyKeysContent(readWholeFile(keysConfigPath().c_str()));
    applyKeysContent(readWholeFile(keysRootPath().c_str()));
    applyKeysContent(readWholeFile(keysGamePath().c_str()));
    g_controlValuesLoaded = true;
}

// Reescribe el fichero conservando comentarios y lineas desconocidas; garantiza
// todos los controles y  input-mode=2  (imprescindible para que se sinteticen teclas).
static std::string buildUpdatedKeysFile(const std::string& original) {
    std::string out;
    bool seen[64] = { false };
    bool inputModeSeen = false;

    if (!original.empty()) {
        size_t start = 0;
        while (start < original.size()) {
            size_t nl = original.find('\n', start);
            std::string line = (nl == std::string::npos) ? original.substr(start) : original.substr(start, nl - start);
            start = (nl == std::string::npos) ? original.size() : nl + 1;
            if (!line.empty() && line.back() == 0x0d) line.pop_back();

            std::string t = trimStr(line);
            if (t.empty() || t[0] == '#') { out += line; out += "\n"; continue; }
            size_t eq = t.find('=');
            if (eq == std::string::npos) { out += line; out += "\n"; continue; }

            std::string name = trimStr(t.substr(0, eq));
            int idx = controlIndexByName(name);
            if (idx >= 0 && idx < 64) {
                char buf[16];
                snprintf(buf, sizeof(buf), "0x%02x", g_controlValues[idx] & 0xffff);
                out += kControls[idx].name; out += "="; out += buf; out += "\n";
                seen[idx] = true;
            } else if (upperStr(name) == "INPUT-MODE") {
                out += "input-mode=2\n";
                inputModeSeen = true;
            } else {
                out += line; out += "\n";
            }
        }
    }

    for (int i = 0; i < kControlCount; ++i) {
        if (seen[i]) continue;
        char buf[16];
        snprintf(buf, sizeof(buf), "0x%02x", g_controlValues[i] & 0xffff);
        out += kControls[i].name; out += "="; out += buf; out += "\n";
    }
    if (!inputModeSeen) out += "input-mode=2\n";
    return out;
}

static bool saveControls() {
    ensureKeysDirs();
    const std::string paths[3] = { keysConfigPath(), keysRootPath(), keysGamePath() };
    bool allOk = true;
    for (int i = 0; i < 3; ++i) {
        std::string updated = buildUpdatedKeysFile(readWholeFile(paths[i].c_str()));
        if (!writeWholeFile(paths[i].c_str(), updated)) allOk = false;
    }
    return allOk;
}

// =============================================================================
// FPS en pantalla (DXVK HUD): config.ini + fifa07.wine-nx.txt
// =============================================================================
// El runtime lee  sdmc:/switch/wine/drive_c/FIFA 07/fifa07.wine-nx.txt  junto al
// ejecutable. La linea  dxvk-hud=fps  activa el contador en pantalla; si no
// esta, queda desactivado. Al reescribirlo se conservan intactas todas las
// demas lineas (comentarios, d3d=dxvk, address-space=..., etc.).
static std::string gameWineNxPath() { return winePath("/drive_c/FIFA 07/fifa07.wine-nx.txt"); }

static std::string lowerStr(const std::string& s) {
    std::string r = s;
    for (char& c : r) if (c >= 'A' && c <= 'Z') c = (char)(c - 'A' + 'a');
    return r;
}

static bool setDxvkHudFps(bool enabled) {
    std::string original = readWholeFile(gameWineNxPath().c_str());

    std::string out;
    bool removed = false;
    size_t start = 0;
    while (start < original.size()) {
        size_t nl = original.find('\n', start);
        std::string line = (nl == std::string::npos) ? original.substr(start) : original.substr(start, nl - start);
        start = (nl == std::string::npos) ? original.size() : nl + 1;
        std::string t = lowerStr(trimStr(line));
        if (t.rfind("dxvk-hud", 0) == 0) { removed = true; continue; }  // se elimina siempre
        out += line; out += "\n";
    }
    if (enabled) out += "dxvk-hud=fps\n";

    // Desactivar sin que existiera la linea (ni el fichero) no debe crear nada.
    if (!enabled && !removed) return true;
    if (original.empty() && !enabled) return true;

    ensureKeysDirs();
    return writeWholeFile(gameWineNxPath().c_str(), out);
}

// =============================================================================
// Widgets estilo EXPLORADOR DE ARCHIVOS de FileZzz
// -----------------------------------------------------------------------------
// Fila: [glifo] Titulo ................ VALOR (alineado a la derecha), con foco
// resaltado por el mecanismo nativo de Borealis (el mismo del menu principal).
// =============================================================================

// Cabecera: barra de acento #00F2FE (4x22) + titulo 24px + separador de 1px.
static brls::Box* makePageHeader(const std::string& title) {
    brls::Theme theme = brls::Application::getTheme();

    brls::Box* header = new brls::Box(brls::Axis::COLUMN);
    header->setWidthPercentage(100);
    header->setMarginBottom(18);

    brls::Box* row = new brls::Box(brls::Axis::ROW);
    row->setAlignItems(brls::AlignItems::CENTER);
    row->setMarginBottom(12);

    brls::Rectangle* bar = new brls::Rectangle(nvgRGB(0, 242, 254));
    bar->setWidth(4);
    bar->setHeight(22);
    bar->setMarginRight(12);
    row->addView(bar);

    brls::Label* lbl = new brls::Label();
    lbl->setText(title);
    lbl->setFontSize(24);
    lbl->setTextColor(theme["brls/text"]);
    row->addView(lbl);
    header->addView(row);

    brls::Box* sep = new brls::Box(brls::Axis::ROW);
    sep->setWidthPercentage(100);
    sep->setHeight(1);
    sep->setBackgroundColor(theme["brls/sidebar/separator"]);
    header->addView(sep);
    return header;
}

// Separador de 1px entre filas (identico al del explorador / menu).
static brls::Box* makeSeparator() {
    brls::Theme theme = brls::Application::getTheme();
    brls::Box* sep = new brls::Box(brls::Axis::ROW);
    sep->setWidthPercentage(100);
    sep->setHeight(1);
    sep->setBackgroundColor(theme["brls/sidebar/separator"]);
    return sep;
}

// Fila tipo explorador: [glifo 28px] Titulo 17px ... VALOR (derecha, acento).
// 'height' permite filas mas compactas (la pantalla de mandos las usa para
// dejar sitio al diagrama).
static brls::Box* makeExplorerRow(const std::string& glyph, const std::string& title,
                                  const std::string& value, brls::Label** valueOut = nullptr,
                                  float height = 56.0f) {
    brls::Theme theme = brls::Application::getTheme();

    brls::Box* row = new brls::Box(brls::Axis::ROW);
    row->setWidthPercentage(100);
    row->setHeight(height);
    row->setFocusable(true);
    row->setCornerRadius(6);
    row->setAlignItems(brls::AlignItems::CENTER);
    row->setPaddingLeft(18);
    row->setPaddingRight(18);

    if (!glyph.empty()) {
        brls::Label* ic = new brls::Label();
        ic->setText(glyph);
        ic->setFontSize(23);
        ic->setWidth(34);
        ic->setHorizontalAlign(brls::HorizontalAlign::CENTER);
        ic->setTextColor(theme["brls/text"]);
        ic->setMarginRight(12);
        row->addView(ic);
    }

    brls::Label* t = new brls::Label();
    t->setText(title);
    t->setFontSize(17);
    t->setTextColor(theme["brls/text"]);
    row->addView(t);

    brls::Box* spacer = new brls::Box(brls::Axis::ROW);
    spacer->setGrow(1.0f);
    row->addView(spacer);

    brls::Label* v = new brls::Label();
    v->setText(value);
    v->setFontSize(15);
    v->setTextColor(theme["brls/accent"]);
    v->setHorizontalAlign(brls::HorizontalAlign::RIGHT);
    v->setId("rowValue");
    row->addView(v);

    if (valueOut) *valueOut = v;
    return row;
}

static brls::Label* rowValueLabel(brls::Box* row) {
    if (!row) return nullptr;
    return dynamic_cast<brls::Label*>(row->getView("rowValue"));
}

// Panel de ayuda inferior: [A] accion   [B] accion   [+ texto opcional]
static brls::Box* makeHelpItem(const std::string& glyph, const std::string& text) {
    brls::Theme theme = brls::Application::getTheme();
    brls::Box* item = new brls::Box(brls::Axis::ROW);
    item->setAlignItems(brls::AlignItems::CENTER);
    item->setMarginRight(24);

    brls::Label* ic = new brls::Label();
    ic->setText(glyph);
    ic->setFontSize(19);
    ic->setTextColor(theme["brls/text"]);
    ic->setMarginRight(8);
    item->addView(ic);

    brls::Label* tx = new brls::Label();
    tx->setText(text);
    tx->setFontSize(14);
    tx->setTextColor(theme["brls/text_disabled"]);
    item->addView(tx);
    return item;
}

static brls::Box* makeHelpBar(const std::string& extraText, brls::Label** extraOut = nullptr,
                              const std::string& extraGlyph = std::string(),
                              const std::string& extraHint  = std::string()) {
    brls::Theme theme = brls::Application::getTheme();
    brls::Box* bar = new brls::Box(brls::Axis::ROW);
    bar->setWidthPercentage(100);
    bar->setAlignItems(brls::AlignItems::CENTER);
    bar->setMarginTop(14);

    bar->addView(makeHelpItem(brls::Hint::getKeyIcon(brls::BUTTON_A, true), "hints/change"_i18n));
    bar->addView(makeHelpItem(brls::Hint::getKeyIcon(brls::BUTTON_B, true), "hints/back"_i18n));
    if (!extraGlyph.empty())
        bar->addView(makeHelpItem(extraGlyph, extraHint));

    brls::Box* spacer = new brls::Box(brls::Axis::ROW);
    spacer->setGrow(1.0f);
    bar->addView(spacer);

    // Texto informativo a la derecha. Se crea SIEMPRE (aunque este vacio) para
    // que la pantalla de mandos pueda actualizarlo al cambiar de control.
    brls::Label* tx = new brls::Label();
    tx->setText(extraText);
    tx->setFontSize(13);
    tx->setTextColor(theme["brls/text_disabled"]);
    bar->addView(tx);
    if (extraOut) *extraOut = tx;
    return bar;
}

// Valor legible de una tecla virtual, p.ej. "ESPACIO (0x20)" / "ESCAPE (0x1b)".
static std::string keyValueText(int vk) {
    char buf[16];
    snprintf(buf, sizeof(buf), "0x%02x", vk & 0xffff);
    const char* n = keyNameFor(vk);
    if (!n) return std::string(buf);
    return upperStr(n) + " (" + buf + ")";
}

// Glifo/icono de boton de Switch asociado a cada control (los aporta Borealis).
// Ya no lo usa el diagrama (que muestra el mando real), pero se conserva por si
// se quiere volver a la lista plana o usar el glifo en otro sitio.
[[maybe_unused]] static std::string controlGlyph(int idx) {
    switch (idx) {
        case 0:  case 4:  return brls::Hint::getKeyIcon(brls::BUTTON_UP, true);
        case 1:  case 5:  return brls::Hint::getKeyIcon(brls::BUTTON_DOWN, true);
        case 2:  case 6:  return brls::Hint::getKeyIcon(brls::BUTTON_LEFT, true);
        case 3:  case 7:  return brls::Hint::getKeyIcon(brls::BUTTON_RIGHT, true);
        case 8:           return brls::Hint::getKeyIcon(brls::BUTTON_A, true);
        case 9:           return brls::Hint::getKeyIcon(brls::BUTTON_B, true);
        case 10:          return brls::Hint::getKeyIcon(brls::BUTTON_X, true);
        case 11:          return brls::Hint::getKeyIcon(brls::BUTTON_Y, true);
        case 12:          return brls::Hint::getKeyIcon(brls::BUTTON_LB, true);
        case 13:          return brls::Hint::getKeyIcon(brls::BUTTON_RB, true);
        case 14:          return brls::Hint::getKeyIcon(brls::BUTTON_LT, true);
        case 15:          return brls::Hint::getKeyIcon(brls::BUTTON_RT, true);
        case 16:          return brls::Hint::getKeyIcon(brls::BUTTON_START, true);
        case 17:          return brls::Hint::getKeyIcon(brls::BUTTON_BACK, true);
        case 18:          return brls::Hint::getKeyIcon(brls::BUTTON_LSB, true);
        case 19:          return brls::Hint::getKeyIcon(brls::BUTTON_RSB, true);
        default:          return std::string();
    }
}

// =============================================================================
// DIAGRAMA VISUAL DEL MANDO
// -----------------------------------------------------------------------------
// Sustituye a la lista plana de la pantalla de configuracion. El dibujo del
// mando es un PRO CONTROLLER de Nintendo Switch en su disposicion REAL: cuerpo
// con dos agarraderas redondeadas (no un rectangulo), stick izquierdo ARRIBA y
// cruceta ABAJO, botones A/B/X/Y en rombo ARRIBA y stick derecho ABAJO, +/-
// en el centro y hombros L/ZL R/ZR en los bordes superiores. Es una imagen
// VECTORIAL generada por tools/generate_controller.py e incrustada en el romfs.
// Encima, en tiempo real, se pintan:
//   * la TECLA ACTUAL de cada control, leida del fichero de teclas real, y
//   * el RESALTE inset del control seleccionado (mismo estilo que el menu: un
//     trazo interior de 2 px con radio de esquina, sin glow).
// IMAGEN BASE: foto REAL de un mando de Switch (par de Joy-Con en su grip) de
// uso libre (Owen1962, dominio publico; ver controller_switch.LICENSE.txt junto
// al PNG). La vista la escala SIN deformar a partir de kCtrlDiagramW/H, que
// DEBEN coincidir con el tamano del PNG que genera tools/generate_controller.py.
//
// NAVEGACION: la cruceta y el stick emiten BUTTON_NAV_LEFT/RIGHT/UP/DOWN (en
// libnx, HidNpadButton_AnyX). Los CUATRO se registran como ACCIONES de esta
// vista, de modo que se CONSUMEN antes que la navegacion normal: mientras el
// diagrama tiene el foco es IMPOSIBLE que el foco se escape a otra fila.
//   * izquierda/derecha: recorren los 24 controles en orden, con envolvimiento.
//   * arriba/abajo     : saltan de ZONA en ZONA del mando (tambien con vuelta).
// Solo se sale con [B] (volver) o con [X] (pantalla de opciones).
// =============================================================================

// Geometria del diagrama (espacio de diseno 1000 x 782, el del PNG).
// La tabla la GENERA tools/generate_controller.py: si se retoca el dibujo hay
// que volver a volcar la tabla para que las etiquetas y el resalte cuadren.
struct CtrlDiagramElem {
    int   control;                     // indice en kControls
    float lx, ly;                      // anclaje de la etiqueta de tecla
    int   align;                       // 0 = centrado, 1 = izquierda, 2 = derecha
    int   shape;                       // 0 = rectangulo, 1 = anillo
    float hx, hy, hw, hh;              // rect (x,y,w,h) o (centro, radio, -)
};
static const CtrlDiagramElem kCtrlDiagram[] = {
    { 18,  250.0,  198.0, 0, 1, 250, 198, 50, 0 },
    {  4,  250.0,  120.0, 0, 0, 230, 125, 40, 40 },
    {  5,  250.0,  272.0, 0, 0, 230, 231, 40, 40 },
    {  6,  183.0,  198.0, 2, 0, 177, 178, 40, 40 },
    {  7,  317.0,  198.0, 1, 0, 283, 178, 40, 40 },
    {  0,  250.0,  308.0, 0, 1, 250, 350, 25, 0 },
    {  1,  250.0,  492.0, 0, 1, 250, 454, 25, 0 },
    {  2,  162.0,  402.0, 2, 1, 198, 402, 25, 0 },
    {  3,  338.0,  402.0, 1, 1, 302, 402, 25, 0 },
    { 17,  315.0,   52.0, 0, 1, 315,  88, 24, 0 },
    { 14,  200.0,   24.0, 0, 0, 125,   4, 150, 40 },
    { 12,  200.0,   58.0, 0, 0, 125,  38, 150, 40 },
    { 15,  770.0,   24.0, 0, 0, 695,   4, 150, 40 },
    { 13,  770.0,   58.0, 0, 0, 695,  38, 150, 40 },
    { 10,  765.0,  109.0, 0, 1, 765, 147, 27, 0 },
    {  9,  801.0,  257.0, 1, 1, 765, 257, 27, 0 },
    { 11,  674.0,  202.0, 2, 1, 710, 202, 27, 0 },
    {  8,  856.0,  202.0, 1, 1, 820, 202, 27, 0 },
    { 16,  674.0,   90.0, 2, 1, 708,  90, 24, 0 },
    { 19,  771.0,  402.0, 0, 1, 771, 402, 62, 0 },
    { 20,  771.0,  317.0, 0, 0, 751, 317, 40, 40 },
    { 21,  771.0,  487.0, 0, 0, 751, 449, 40, 40 },
    { 22,  692.0,  402.0, 2, 0, 686, 382, 40, 40 },
    { 23,  850.0,  402.0, 1, 0, 816, 382, 40, 40 },
};
static const int   kCtrlDiagramCount = (int)(sizeof(kCtrlDiagram) / sizeof(kCtrlDiagram[0]));
static const float kCtrlDiagramW     = 1000.0f;
static const float kCtrlDiagramH     = 782.0f;

// Orden de recorrido del diagrama (indices en kControls): izquierda/derecha
// avanzan uno a uno por esta lista y envuelven al llegar al final.
static const int kCtrlWalk[] = {
    0, 1, 2, 3,        // cruceta (D-Pad)
    4, 5, 6, 7,        // stick izquierdo
    8, 9, 10, 11,      // botones A/B/X/Y
    12, 13, 14, 15,    // hombros L / R / ZL / ZR
    16, 17,            // + / -
    18, 19,            // clic de stick L / R
    20, 21, 22, 23,    // stick derecho
};
static const int kCtrlWalkCount = (int)(sizeof(kCtrlWalk) / sizeof(kCtrlWalk[0]));

// Limites de ZONA del mando: arriba/abajo saltan de una zona a la siguiente.
static const int kCtrlZone[] = { 0, 4, 8, 12, 16, 18, 20, 24 };
static const int kCtrlZoneCount = (int)(sizeof(kCtrlZone) / sizeof(kCtrlZone[0])) - 1;

// Elemento de dibujo asociado a un control (o nullptr si no existe).
static const CtrlDiagramElem* ctrlDiagramFor(int control) {
    for (int i = 0; i < kCtrlDiagramCount; ++i)
        if (kCtrlDiagram[i].control == control) return &kCtrlDiagram[i];
    return nullptr;
}

static int ctrlWalkPos(int control) {
    for (int i = 0; i < kCtrlWalkCount; ++i)
        if (kCtrlWalk[i] == control) return i;
    return -1;
}
static const char* kCtrlDiagramImage = "romfs:/img/controller_switch.png";

// Texto COMPACTO de una tecla virtual para el diagrama: cabe junto al elemento
// (a diferencia de keyValueText, que es el nombre largo con el codigo hex).
static std::string keyShortText(int vk) {
    char buf[8];
    switch (vk & 0xffff) {
        case 0x00: return "\u2014";                                  // sin uso
        case 0x26: return "\u2191";  case 0x28: return "\u2193";     // flechas
        case 0x25: return "\u2190";  case 0x27: return "\u2192";
        case 0x0d: return "ENTER";
        case 0x1b: return "ESC";
        case 0x20: return "ESPACIO";
        case 0x10: return "MAY\u00daS";
        case 0x11: return "CTRL";
        case 0x09: return "TAB";
        case 0x08: return "RETRO";
        case 0x2e: return "SUPR";
        case 0x14: return "BLOQ";
        default: break;
    }
    const char* n = keyNameFor(vk);
    if (n && std::string(n) != "Ninguna") return upperStr(n);
    snprintf(buf, sizeof(buf), "0x%02x", vk & 0xff);
    return std::string(buf);
}

// Vista del diagrama: dibuja la imagen del mando, el resalte inset del control
// seleccionado y la tecla actual de los 24 controles.
class ControllerDiagramView : public brls::Box {
public:
    ControllerDiagramView() : brls::Box(brls::Axis::ROW) {
        // Ocupa todo el area que le da su contenedor y ESCALA el dibujo para
        // encajar en ella (nunca se sale de la pantalla, sea cual sea el alto
        // que quede libre con los demas textos).
        this->setWidthPercentage(100);
        this->setHeightPercentage(100);
        this->setFocusable(true);
        this->setHideHighlight(true);   // el resalte lo pinta draw()

        // La cruceta y el stick emiten BUTTON_NAV_LEFT/RIGHT/UP/DOWN. Los
        // CUATRO se registran como ACCIONES (se consumen ANTES de la navegacion
        // normal) para que el foco NO PUEDA salir del diagrama:
        //   * izq./der. recorren los 24 controles, con envolvimiento;
        //   * arriba/abajo saltan de ZONA en ZONA del mando.
        // Para salir solo hay [B] (volver) o [X] (pantalla de opciones).
        this->registerAction("", brls::BUTTON_NAV_LEFT, [this](brls::View*) {
            this->step(-1);
            return true;
        }, false, true);
        this->registerAction("", brls::BUTTON_NAV_RIGHT, [this](brls::View*) {
            this->step(1);
            return true;
        }, false, true);
        this->registerAction("", brls::BUTTON_NAV_UP, [this](brls::View*) {
            this->stepZone(-1);
            return true;
        }, false, true);
        this->registerAction("", brls::BUTTON_NAV_DOWN, [this](brls::View*) {
            this->stepZone(1);
            return true;
        }, false, true);
    }

    // m_selected guarda el INDICE DE CONTROL (0..kControlCount-1), no la fila de
    // la tabla de dibujo: asi el recorrido es el logico del mando (cruceta ->
    // stick izq. -> A/B/X/Y -> hombros -> +/- -> clics -> stick der.).
    int selected() const { return m_selected; }
    void setSelected(int control) {
        if (kControlCount <= 0) return;
        control %= kControlCount;
        if (control < 0) control += kControlCount;
        if (control == m_selected) return;
        m_selected = control;
        if (onSelectionChanged) onSelectionChanged(m_selected);
    }
    // Izquierda/derecha: control anterior/siguiente del recorrido, con vuelta.
    void step(int delta) {
        int p = ctrlWalkPos(m_selected);
        if (p < 0) { setSelected(0); return; }
        p = (p + delta) % kCtrlWalkCount;
        if (p < 0) p += kCtrlWalkCount;
        setSelected(kCtrlWalk[p]);
    }
    // Arriba/abajo: salta al primer control de la zona anterior/siguiente.
    void stepZone(int delta) {
        int z = 0;
        for (int i = 0; i < kCtrlZoneCount; ++i)
            if (m_selected >= kCtrlZone[i]) z = i;
        z = (z + delta) % kCtrlZoneCount;
        if (z < 0) z += kCtrlZoneCount;
        setSelected(kCtrlZone[z]);
    }

    // La Activity la usa para refrescar la barra de ayuda al cambiar de control.
    std::function<void(int)> onSelectionChanged;

    void onFocusGained() override { brls::Box::onFocusGained(); m_focused = true; }
    void onFocusLost() override { brls::Box::onFocusLost(); m_focused = false; }

    void draw(NVGcontext* vg, float x, float y, float width, float height,
              brls::Style style, brls::FrameContext* ctx) override {
        (void)style;

        // --- Encaje del dibujo en el area disponible ------------------------
        // El lienzo del diagrama es de kCtrlDiagramW x kCtrlDiagramH; se escala
        // de forma uniforme (SIN deformar) para caber en el hueco y se centra.
        if (width <= 1.0f || height <= 1.0f) return;
        float sc = width / kCtrlDiagramW;
        if (height / kCtrlDiagramH < sc) sc = height / kCtrlDiagramH;
        if (sc <= 0.05f) return;
        const float dw = kCtrlDiagramW * sc;
        const float dh = kCtrlDiagramH * sc;
        const float ox = x + (width - dw) * 0.5f;
        const float oy = y + (height - dh) * 0.5f;

        // --- Imagen del mando (una sola vez; NanoVG la cachea) --------------
        if (m_img == 0 && !m_imgFailed)
            m_img = nvgCreateImage(vg, kCtrlDiagramImage, 0);
        m_imgFailed = (m_img == 0);
        if (m_img > 0) {
            NVGpaint p = nvgImagePattern(vg, ox, oy, dw, dh, 0.0f, m_img, 1.0f);
            nvgBeginPath(vg);
            nvgRect(vg, ox, oy, dw, dh);
            nvgFillPaint(vg, p);
            nvgFill(vg);
        }

        const CtrlDiagramElem* selElem = ctrlDiagramFor(m_selected);
        if (!selElem) return;   // tabla desincronizada

        const NVGcolor accent = ctx->theme.getColor("brls/accent");

        // --- Resalte inset del control seleccionado (estilo del menu) -------
        {
            const CtrlDiagramElem& e = *selElem;
            NVGcolor hl = accent;
            hl.a = m_focused ? 0.95f : 0.40f;
            nvgBeginPath(vg);
            if (e.shape == 0)
                nvgRoundedRect(vg, ox + e.hx * sc, oy + e.hy * sc, e.hw * sc, e.hh * sc, 10.0f * sc);
            else
                nvgCircle(vg, ox + e.hx * sc, oy + e.hy * sc, e.hw * sc);
            nvgStrokeWidth(vg, 3.4f * sc);
            nvgStrokeColor(vg, hl);
            nvgStroke(vg);
        }

        // --- Tecla actual de cada control -----------------------------------
        const int font = brls::Application::getDefaultFont();
        nvgFontFaceId(vg, font);
        nvgFontBlur(vg, 0.0f);
        for (int i = 0; i < kCtrlDiagramCount; ++i) {
            const CtrlDiagramElem& e = kCtrlDiagram[i];
            const std::string t = keyShortText(g_controlValues[e.control]);
            if (t.empty()) continue;

            const bool small = (e.control == 18 || e.control == 19);  // clicks de stick
            const bool sel   = (e.control == m_selected);
            const float px = ox + e.lx * sc;
            const float py = oy + e.ly * sc;
            const int ha = (e.align == 0) ? NVG_ALIGN_CENTER
                         : (e.align == 1) ? NVG_ALIGN_LEFT : NVG_ALIGN_RIGHT;

            // Sobre la FOTO hace falta una pastilla de fondo para que la tecla
            // se lea siempre; la del control elegido va rellena de acento.
            nvgFontSize(vg, (small ? 20.0f : 22.0f) * sc);
            nvgTextAlign(vg, ha | NVG_ALIGN_MIDDLE);

            float b[4];
            nvgTextBounds(vg, px, py, t.c_str(), nullptr, b);
            nvgBeginPath(vg);
            nvgRoundedRect(vg, b[0] - 8.0f * sc, b[1] - 4.0f * sc,
                           (b[2] - b[0]) + 16.0f * sc, (b[3] - b[1]) + 9.0f * sc, 7.0f * sc);
            if (sel) {
                nvgFillColor(vg, accent);
                nvgFill(vg);
                nvgFillColor(vg, nvgRGB(6, 10, 12));
            } else {
                nvgFillColor(vg, nvgRGBA(8, 10, 14, 175));
                nvgFill(vg);
                NVGcolor kc = accent;
                kc.a = 0.95f;
                nvgFillColor(vg, kc);
            }
            nvgText(vg, px, py, t.c_str(), nullptr);
        }
    }

private:
    int  m_selected  = 0;
    bool m_focused   = false;
    int  m_img       = 0;
    bool m_imgFailed = false;
};

// --- Selector de tecla virtual para un control (mismo estilo de explorador) --
class KeyPickerActivity : public brls::Activity {
public:
    explicit KeyPickerActivity(int controlIndex) : m_idx(controlIndex) {}

    brls::View* createContentView() override {
        brls::Theme theme = brls::Application::getTheme();

        brls::Box* root = new brls::Box(brls::Axis::COLUMN);
        root->setGrow(1.0f);
        root->setPadding(25, 45, 20, 45);
        root->setBackgroundColor(theme["brls/background"]);

        std::string title = std::string("hints/key_picker_title"_i18n) + "  \u00b7  " + kControls[m_idx].label;
        root->addView(makePageHeader(title));

        brls::Label* cur = new brls::Label();
        cur->setText(std::string("hints/key_current"_i18n) + ":  " + keyValueText(g_controlValues[m_idx]));
        cur->setFontSize(14);
        cur->setTextColor(theme["brls/accent"]);
        cur->setMarginBottom(12);
        root->addView(cur);

        brls::ScrollingFrame* scroll = new brls::ScrollingFrame();
        scroll->setWidthPercentage(100);
        scroll->setGrow(1.0f);
        brls::Box* content = new brls::Box(brls::Axis::COLUMN);
        content->setWidthPercentage(100);

        brls::Box* firstFocus = nullptr;
        for (int i = 0; i < kKeyOptionCount; ++i) {
            char code[16];
            snprintf(code, sizeof(code), "0x%02x", kKeyOptions[i].vk & 0xffff);
            std::string value = code;
            if (kKeyOptions[i].vk == g_controlValues[m_idx])
                value += std::string("  \u00b7  ") + "hints/key_current"_i18n;

            brls::Box* row = makeExplorerRow(std::string(), kKeyOptions[i].name, value);
            int vk  = kKeyOptions[i].vk;
            int idx = m_idx;
            row->registerClickAction([vk, idx](brls::View*) {
                g_controlValues[idx] = vk;
                brls::Application::notify(std::string(kControls[idx].name) + " = " + keyValueText(vk));
                brls::Application::popActivity();
                return true;
            });
            content->addView(row);
            content->addView(makeSeparator());
            if (!firstFocus) firstFocus = row;
        }
        content->setPaddingBottom(20);

        scroll->setContentView(content);
        root->addView(scroll);

        root->addView(makeHelpBar(std::string()));
        m_firstFocus = firstFocus;
        return wrapWallpaper(root);
    }

    void onContentAvailable() override {
        brls::Activity::onContentAvailable();
        if (m_firstFocus) brls::Application::giveFocus(m_firstFocus);
        this->registerAction("hints/back"_i18n, brls::BUTTON_B, [](brls::View*) {
            brls::Application::popActivity();
            return true;
        });
    }

private:
    int m_idx;
    brls::View* m_firstFocus = nullptr;
};

// --- Pantalla de configuracion de mandos: DIAGRAMA VISUAL -------------------
// DIAGRAMA DEL MANDO: una FOTO REAL de un mando de Switch (par de Joy-Con en su
// grip, de uso libre) con la tecla actual de cada control encima y el resalte
// inset del control seleccionado. La cruceta y el stick recorren los 24
// controles DENTRO del dibujo y no pueden sacar el foco de ahi: solo se sale
// con [B] (volver) o [X] (pantalla de opciones).
//
// La lectura/escritura de los tres ficheros de teclas no cambia. Las filas de
// accion (FPS / guardar / recargar) viven en ControlsOptionsActivity, que se
// abre con [X]; asi el diagrama dispone de toda la altura de la pantalla.
static const float kControlsActionRowH = 48.0f;

// --- Pantalla de OPCIONES (FPS / guardar / recargar) -------------------------
// Se abre con [X] desde la pantalla de mandos. Vive APARTE para dos cosas: (a)
// el diagrama dispone de TODA la altura de la pantalla (se ve mas grande) y (b)
// su foco no puede escaparse a ninguna fila, porque la pantalla de mandos ya no
// tiene ninguna otra vista enfocable.
class ControlsOptionsActivity : public brls::Activity {
public:
    brls::View* createContentView() override {
        brls::Theme theme = brls::Application::getTheme();

        brls::Box* root = new brls::Box(brls::Axis::COLUMN);
        root->setGrow(1.0f);
        root->setPadding(25, 45, 20, 45);
        root->setBackgroundColor(theme["brls/background"]);

        root->addView(makePageHeader("hints/options"_i18n));

        // --- Video: contador de FPS en pantalla -------------------------------
        // Persiste en config.ini y sincroniza la linea 'dxvk-hud=fps' de
        // fifa07.wine-nx.txt (junto al .exe), conservando el resto de lineas.
        m_fpsRow = makeExplorerRow(std::string(), "hints/menu_fps"_i18n,
                                   AppConfig::get().showFps ? "hints/on"_i18n : "hints/off"_i18n,
                                   nullptr, kControlsActionRowH);
        m_fpsRow->registerClickAction([this](brls::View*) {
            AppConfig& cfg = AppConfig::get();
            cfg.showFps = !cfg.showFps;
            cfg.save();
            if (!setDxvkHudFps(cfg.showFps))
                brls::Application::notify("hints/controls_save_fail"_i18n);
            refreshValues();
            return true;
        });
        root->addView(m_fpsRow);
        root->addView(makeSeparator());

        // --- Acciones: guardar / recargar -------------------------------------
        brls::Box* rowSave = makeExplorerRow(std::string(), "hints/controls_save"_i18n,
                                             "(A)", nullptr, kControlsActionRowH);
        rowSave->registerClickAction([](brls::View*) {
            if (saveControls())
                brls::Application::notify("hints/controls_save_ok"_i18n);
            else
                brls::Application::notify("hints/controls_save_fail"_i18n);
            return true;
        });
        root->addView(rowSave);
        root->addView(makeSeparator());

        brls::Box* rowReload = makeExplorerRow(std::string(), "hints/controls_reload"_i18n,
                                               "(A)", nullptr, kControlsActionRowH);
        rowReload->registerClickAction([this](brls::View*) {
            loadControls();
            refreshValues();
            brls::Application::notify("hints/controls_reload_ok"_i18n);
            return true;
        });
        root->addView(rowReload);
        root->addView(makeSeparator());

        brls::Box* spacer = new brls::Box(brls::Axis::COLUMN);
        spacer->setGrow(1.0f);
        root->addView(spacer);

        root->addView(makeHelpBar(std::string()));
        return wrapWallpaper(root);
    }

    void onContentAvailable() override {
        brls::Activity::onContentAvailable();
        if (m_fpsRow) brls::Application::giveFocus(m_fpsRow);
        this->registerAction("hints/back"_i18n, brls::BUTTON_B, [](brls::View*) {
            brls::Application::popActivity();
            return true;
        });
    }

    void willAppear(bool resetState = false) override {
        brls::Activity::willAppear(resetState);
        refreshValues();
    }

    void onPause() override {
        if (brls::View* v = this->getContentView()) v->setVisibility(brls::Visibility::GONE);
    }

    void onResume() override {
        if (brls::View* v = this->getContentView()) v->setVisibility(brls::Visibility::VISIBLE);
    }

private:
    brls::Box* m_fpsRow = nullptr;

    void refreshValues() {
        if (m_fpsRow) {
            brls::Label* l = rowValueLabel(m_fpsRow);
            if (l) l->setText(AppConfig::get().showFps ? "hints/on"_i18n : "hints/off"_i18n);
        }
    }
};

class ControlsActivity : public brls::Activity {
public:
    ControlsActivity() {
        if (!g_controlValuesLoaded) loadControls();
    }

    brls::View* createContentView() override {
        brls::Theme theme = brls::Application::getTheme();

        brls::Box* root = new brls::Box(brls::Axis::COLUMN);
        root->setGrow(1.0f);
        root->setPadding(25, 45, 20, 45);
        root->setBackgroundColor(theme["brls/background"]);

        // Cabecera con barra de acento + titulo + separador
        root->addView(makePageHeader("hints/controls_title"_i18n));

        brls::Label* sub = new brls::Label();
        sub->setText("hints/controls_subtitle"_i18n);
        sub->setFontSize(14);
        sub->setTextColor(theme["brls/text_disabled"]);
        sub->setMarginBottom(8);
        root->addView(sub);

        // --- DIAGRAMA DEL MANDO ------------------------------------------------
        // Es lo UNICO que toma el foco en esta pantalla. La cruceta y el stick
        // (incluidas sus cuatro direcciones) los consume la propia vista para
        // moverse por los 24 controles del dibujo; A abre el selector de teclas
        // y X lleva a la pantalla de opciones. El foco no puede escaparse.
        brls::Box* stage = new brls::Box(brls::Axis::ROW);
        stage->setWidthPercentage(100);
        stage->setGrow(1.0f);

        m_diagram = new ControllerDiagramView();
        m_diagram->onSelectionChanged = [this](int) { refreshHelpInfo(); };
        m_diagram->registerClickAction([this](brls::View*) {
            brls::Application::pushActivity(new KeyPickerActivity(m_diagram->selected()));
            return true;
        });
        stage->addView(m_diagram);
        root->addView(stage);

        // Pista de navegacion bajo el diagrama.
        brls::Label* nav = new brls::Label();
        nav->setText("hints/controls_nav_hint"_i18n);
        nav->setFontSize(13);
        nav->setTextColor(theme["brls/text_disabled"]);
        nav->setHorizontalAlign(brls::HorizontalAlign::CENTER);
        nav->setWidthPercentage(100);
        nav->setMarginTop(4);
        root->addView(nav);

        // Panel de ayuda: [A] cambiar, [B] volver, [X] opciones + detalle del
        // control seleccionado a la derecha.
        root->addView(makeHelpBar(std::string(), &m_helpInfo,
                                  brls::Hint::getKeyIcon(brls::BUTTON_X, true),
                                  "hints/options"_i18n));
        refreshHelpInfo();

        return wrapWallpaper(root);
    }

    void onContentAvailable() override {
        brls::Activity::onContentAvailable();
        if (m_diagram) brls::Application::giveFocus(m_diagram);
        this->registerAction("hints/back"_i18n, brls::BUTTON_B, [](brls::View*) {
            brls::Application::popActivity();
            return true;
        });
        // [X]: unico modo explicito de dejar el diagrama (ademas de [B]).
        this->registerAction("hints/options"_i18n, brls::BUTTON_X, [](brls::View*) {
            brls::Application::pushActivity(new ControlsOptionsActivity());
            return true;
        });
    }

    // Al volver del selector de teclas (o de la pantalla de opciones) se
    // refresca el detalle de la barra de ayuda; el diagrama se redibuja solo
    // porque lee g_controlValues cada frame.
    void willAppear(bool resetState = false) override {
        brls::Activity::willAppear(resetState);
        refreshHelpInfo();
    }

    // Igual que en el menu: al quedar cubierta por otra pantalla, el contenido
    // se oculta por completo y se restaura al volver.
    void onPause() override {
        if (brls::View* v = this->getContentView()) v->setVisibility(brls::Visibility::GONE);
    }

    void onResume() override {
        if (brls::View* v = this->getContentView()) v->setVisibility(brls::Visibility::VISIBLE);
    }

private:
    ControllerDiagramView* m_diagram = nullptr;
    brls::Label* m_helpInfo = nullptr;

    // Detalle del control seleccionado en la barra de ayuda: "ZR -> ESCAPE (0x1b)".
    void refreshHelpInfo() {
        if (!m_helpInfo || !m_diagram) return;
        int i = m_diagram->selected();
        if (i < 0 || i >= kControlCount) return;
        m_helpInfo->setText(std::string(kControls[i].name) + "  \u2192  " +
                            keyValueText(g_controlValues[i]));
    }
};


// =============================================================================
// MENU VERTICAL estilo PlayStation (lista de arriba a abajo)
// -----------------------------------------------------------------------------
// Borealis (este fork) NO expone setScale()/setRotation() sobre las vistas: solo
// traslacion (setTranslationX/Y) y alpha. Para conseguir el efecto del menu se
// transforma el contexto NanoVG directamente en draw(): cada tarjeta se dibuja
// con nvgTranslate + nvgScale alrededor de su propio centro. La tarjeta
// CENTRAL/ENFOCADA va mas grande y sin atenuar; las de arriba/abajo mas
// pequenas y con menos opacidad; y toda la lista se desplaza EN VERTICAL para
// centrar la opcion seleccionada (transicion suave con brls::Animatable).
// =============================================================================

// Tarjeta individual de la lista (icono + titulo + descripcion).
static brls::Box* makeCarouselCard(const std::string& id,
                                   const std::string& imagePath,
                                   const std::string& title,
                                   const std::string& desc) {
    brls::Theme theme = brls::Application::getTheme();

    brls::Box* card = new brls::Box(brls::Axis::ROW);
    card->setId(id);
    card->setWidth(760.0f);
    card->setHeight(96.0f);
    card->setFocusable(true);
    card->setHideHighlight(true);   // el resaltado lo dibuja la lista (transformado)
    card->setCornerRadius(14.0f);
    card->setAlignItems(brls::AlignItems::CENTER);
    card->setPaddingLeft(26.0f);
    card->setPaddingRight(26.0f);
    card->setMarginBottom(12.0f);   // separacion entre filas de la lista vertical
    card->setBackgroundColor(theme["brls/menu/row"]);

    brls::Image* icon = new brls::Image();
    icon->setImageFromFile(imagePath);
    icon->setWidth(56.0f);
    icon->setHeight(56.0f);
    icon->setMarginRight(24.0f);
    card->addView(icon);

    brls::Box* texts = new brls::Box(brls::Axis::COLUMN);
    texts->setGrow(1.0f);
    texts->setJustifyContent(brls::JustifyContent::CENTER);

    brls::Label* t = new brls::Label();
    t->setText(title);
    t->setFontSize(24.0f);
    t->setTextColor(theme["brls/text"]);
    t->setHorizontalAlign(brls::HorizontalAlign::LEFT);
    texts->addView(t);

    brls::Label* d = new brls::Label();
    d->setText(desc);
    d->setFontSize(13.0f);
    d->setTextColor(theme["brls/text_disabled"]);
    d->setHorizontalAlign(brls::HorizontalAlign::LEFT);
    d->setMarginTop(4.0f);
    texts->addView(d);

    card->addView(texts);

    return card;
}

class CarouselFrame : public brls::Box {
public:
    CarouselFrame() : brls::Box(brls::Axis::COLUMN) {
        this->setWidthPercentage(100);
        this->setHeightPercentage(100);
        this->setAlignItems(brls::AlignItems::CENTER);
        this->setJustifyContent(brls::JustifyContent::CENTER);
    }

    // Anima el carrusel hacia el indice indicado (transicion suave, no seca).
    void setSelected(int idx) {
        if (idx < 0) idx = 0;
        if (idx == m_target) return;
        m_target = idx;
        m_anim.stop();
        m_anim.reset();   // conserva el valor actual como origen de la animacion
        m_anim.addStep((float)idx, 300, brls::EasingFunction::quadraticOut);
        m_anim.start();
    }

    // Cuando una tarjeta recibe el foco (D-Pad/stick arriba/abajo), la lista la
    // desliza hasta el centro.
    void onChildFocusGained(brls::View* directChild, brls::View* focusedView) override {
        brls::Box::onChildFocusGained(directChild, focusedView);
        auto& kids = this->getChildren();
        for (size_t i = 0; i < kids.size(); ++i) {
            if (kids[i] == directChild) { m_focused = (int)i; setSelected((int)i); break; }
        }
    }

    void draw(NVGcontext* vg, float x, float y, float width, float height,
              brls::Style style, brls::FrameContext* ctx) override {
        (void)style;
        auto& kids = this->getChildren();
        const int n = (int)kids.size();
        if (n <= 0) return;

        // Buffers reutilizados entre frames (antes se creaba un std::vector y se
        // ordenaba en CADA frame, con asignacion de heap incluida).
        if ((int)m_scale.size() != n) {
            m_scale.assign(n, 1.0f);
            m_alpha.assign(n, 1.0f);
            m_dy.assign(n, 0.0f);
            m_order.resize(n);
            m_lastSel  = -1.0e9f;   // fuerza primer recalculo
            m_geoValid = false;
        }

        // --- Geometria base: se recalcula SOLO si cambio el layout -----------
        // (los frames de las tarjetas son estables, asi que esto se hace una vez)
        float cy0 = kids[0]->getFrame().getMinY() + kids[0]->getHeight() / 2.0f;
        float cyn = kids[n - 1]->getFrame().getMinY() + kids[n - 1]->getHeight() / 2.0f;
        float anchorY = y + height / 2.0f;   // centro vertical de la lista
        if (!m_geoValid || cy0 != m_geoCy0 || cyn != m_geoCyn || anchorY != m_geoAnchorY) {
            m_spacing = (n > 1) ? (cyn - cy0) / (float)(n - 1) : kids[0]->getHeight();
            if (m_spacing <= 1.0f) m_spacing = kids[0]->getHeight();
            m_geoCy0 = cy0; m_geoCyn = cyn; m_geoAnchorY = anchorY;
            m_geoValid  = true;
            m_lastSel   = -1.0e9f;  // geometria nueva -> recalcular transform
        }

        // --- Transformaciones por tarjeta: SOLO mientras el carrusel se mueve -
        // Con el carrusel quieto (sel == ultimo valor dibujado) no se recalcula
        // nada: se reutilizan escala / alpha / desplazamiento ya cacheados.
        const float sel = m_anim.getValue();
        if (sel != m_lastSel) {
            // Lista vertical: se respeta casi la separacion del layout para que
            // las cuatro opciones no se pisen; la central domina por escala/alpha.
            const float compress = 0.92f;

            for (int i = 0; i < n; ++i) {
                float off = std::fabs((float)i - sel);
                // e = 1 en el centro, 0 a partir de una fila de distancia.
                float e = 1.0f - off;
                if (e < 0.0f) e = 0.0f;

                float scale = 0.82f + 0.24f * e;   // centro 1.06 / vecinas 0.82
                if (off > 1.0f) scale -= 0.07f * (off - 1.0f);
                if (scale < 0.60f) scale = 0.60f;

                float cy = kids[i]->getFrame().getMinY() + kids[i]->getHeight() / 2.0f;
                float desired = anchorY + ((float)i - sel) * m_spacing * compress;

                m_scale[i] = scale;
                m_alpha[i] = 0.45f + 0.55f * e;    // centro 1.0 / vecinas 0.45
                m_dy[i]    = desired - cy;
            }

            // Orden de dibujo: primero las mas alejadas del centro, la central al
            // final (queda por encima). Da la sensacion de profundidad 3D.
            for (int i = 0; i < n; ++i) m_order[i] = i;
            std::sort(m_order.begin(), m_order.end(), [sel](int a, int b) {
                return std::fabs((float)a - sel) > std::fabs((float)b - sel);
            });

            m_lastSel = sel;
        }

        // --- Dibujo (cada frame, reutilizando los valores cacheados) ---------
        for (int k = 0; k < n; ++k) {
            int i = m_order[k];
            brls::View* child = kids[i];
            brls::Rect fr = child->getFrame();
            float fw = child->getWidth();
            float fh = child->getHeight();
            float cx = fr.getMinX() + fw / 2.0f;
            float cy = fr.getMinY() + fh / 2.0f;

            nvgSave(vg);
            nvgGlobalAlpha(vg, m_alpha[i]);
            nvgTranslate(vg, 0.0f, m_dy[i]);
            nvgTranslate(vg, cx, cy);
            nvgScale(vg, m_scale[i], m_scale[i]);
            nvgTranslate(vg, -cx, -cy);
            child->frame(ctx);

            // Resaltado propio (en el espacio transformado) del elemento central.
            // Se pinta INSET (por dentro de la tarjeta) y concentrico con su
            // radio de esquina: radio_borde = radio_tarjeta - inset. Asi el
            // trazo (2 px, centrado en el path) cae siempre dentro de la
            // silueta redondeada de la tarjeta y NUNCA se sale por las
            // esquinas a tocar la tarjeta vecina. Sin glow ni expansion.
            if (i == m_focused) {
                const float cardRadius = 14.0f;   // mismo radio que makeCarouselCard
                const float inset      = 4.0f;    // margen interior (px)
                const float bw         = 2.0f;    // grosor del borde (px)
                NVGcolor ac = ctx->theme.getColor("brls/accent");
                ac.a = 0.85f; // opacidad al 85% (sin glow)
                nvgBeginPath(vg);
                nvgRoundedRect(vg, fr.getMinX() + inset, fr.getMinY() + inset,
                               fw - 2.0f * inset, fh - 2.0f * inset,
                               cardRadius - inset);
                nvgStrokeWidth(vg, bw);
                nvgStrokeColor(vg, ac);
                nvgStroke(vg);
            }

            nvgRestore(vg);
        }
    }

private:
    brls::Animatable m_anim = 0.0f;   // posicion "continua" del carrusel
    int m_target  = 0;
    int m_focused = 0;

    // Caches de layout/animacion: evitan recalcular todo en cada frame. Solo se
    // refrescan cuando el carrusel se mueve o cambia el layout.
    std::vector<float> m_scale, m_alpha, m_dy;  // por tarjeta
    std::vector<int>   m_order;                 // orden de pintado
    float m_spacing    = 0.0f;                  // separacion entre filas
    float m_geoCy0     = 0.0f;                  // claves de la geometria cacheada
    float m_geoCyn     = 0.0f;
    float m_geoAnchorY = 0.0f;
    float m_lastSel    = -1.0e9f;               // ultimo 'sel' dibujado
    bool  m_geoValid   = false;
};

// -----------------------------------------------------------------------------
// Menu principal (view_menu.xml): Jugar / Configuracion / Acerca de / Salir
// -----------------------------------------------------------------------------
class MenuActivity : public brls::Activity {
public:
    brls::View* createContentView() override {
        brls::View* root = brls::View::createFromXMLFile("romfs:/xml/view_menu.xml");

        // El XML reserva un contenedor vacio (id="carouselHost"). Aqui se monta
        // la LISTA VERTICAL con las cuatro opciones (se mantienen los mismos ids
        // rowPlay/rowSettings/rowAbout/rowExit para las acciones y el foco).
        if (brls::Box* host = dynamic_cast<brls::Box*>(root->getView("carouselHost"))) {
            CarouselFrame* car = new CarouselFrame();

            brls::Box* c0 = makeCarouselCard("rowPlay", "romfs:/img/icon_nro_sm.png",
                                             "hints/menu_play"_i18n, "hints/menu_play_desc"_i18n);
            brls::Box* c1 = makeCarouselCard("rowSettings", "romfs:/img/icon_theme.png",
                                             "hints/menu_settings"_i18n, "hints/menu_settings_desc"_i18n);
            brls::Box* c2 = makeCarouselCard("rowAbout", "romfs:/img/icon_about.png",
                                             "hints/menu_about"_i18n, "hints/menu_about_desc"_i18n);
            brls::Box* c3 = makeCarouselCard("rowExit", "romfs:/img/icon_exit.png",
                                             "hints/exit"_i18n, "hints/menu_exit_desc"_i18n);

            car->addView(c0);
            car->addView(c1);
            car->addView(c2);
            car->addView(c3);
            // Las cuatro filas van de arriba a abajo; el draw() centra en vertical
            // la opcion enfocada (mas grande) y atenua/encoge las demas.

            host->addView(car);
        }

        return wrapWallpaper(root);
    }

    void onContentAvailable() override {
        brls::Activity::onContentAvailable();

        // Jugar -> hand-off DIRECTO al runtime (sin dialogo de confirmacion)
        if (brls::View* row = this->getView("rowPlay")) {
            row->registerClickAction([](brls::View*) {
                launchGame();
                return true;
            });
        }

        // Configuracion -> pantalla de mandos (lee/escribe fifa07.keys.txt)
        if (brls::View* row = this->getView("rowSettings")) {
            row->registerClickAction([](brls::View*) {
                brls::Application::pushActivity(new ControlsActivity());
                return true;
            });
        }

        // Acerca de y donaciones -> AboutActivity (dos QR)
        if (brls::View* row = this->getView("rowAbout")) {
            row->registerClickAction([](brls::View*) {
                brls::Application::pushActivity(new AboutActivity());
                return true;
            });
        }

        // Salir -> dialogo nativo
        auto doExit = [](brls::View*) {
            brls::Dialog* d = new brls::Dialog("hints/exit_hint"_i18n);
            d->addButton("hints/cancel"_i18n, []() {});
            d->addButton("hints/exit"_i18n, []() { brls::Application::quit(); });
            d->open();
            return true;
        };
        if (brls::View* row = this->getView("rowExit")) {
            row->registerClickAction(doExit);
        }

        // Foco inicial en la primera fila (navegacion D-Pad / stick)
        if (brls::View* first = this->getView("rowPlay")) {
            brls::Application::giveFocus(first);
        }

        // Pie de ayuda identico en espiritu al footer nativo de FileZzz:
        // iconos de boton + texto (A / B / -).
        if (brls::Box* footer = dynamic_cast<brls::Box*>(this->getView("menuFooter"))) {
            footer->addView(makeHelpItem(brls::Hint::getKeyIcon(brls::BUTTON_A, true), "hints/select"_i18n));
            footer->addView(makeHelpItem(brls::Hint::getKeyIcon(brls::BUTTON_B, true), "hints/back"_i18n));
            footer->addView(makeHelpItem(brls::Hint::getKeyIcon(brls::BUTTON_BACK, true), "hints/exit"_i18n));
        }

        // Atajo de salida con '-' (Minus / BUTTON_BACK)
        this->registerAction("hints/exit"_i18n, brls::BUTTON_BACK, doExit);
    }

    // Patron de FileZzz (FeatureActivity + WallpaperAppletFrame): cuando otra
    // Activity se coloca encima, el contenido previo se oculta por completo en
    // lugar de quedarse dibujado por detras. Al volver, se restaura.
    void onPause() override {
        if (brls::View* v = this->getContentView()) v->setVisibility(brls::Visibility::GONE);
    }

    void onResume() override {
        if (brls::View* v = this->getContentView()) v->setVisibility(brls::Visibility::VISIBLE);
    }
};

// -----------------------------------------------------------------------------
// Pantalla de Inicio / Splash (copiada de FileZzz, adaptada)
// -----------------------------------------------------------------------------
class SplashActivity : public brls::Activity {
public:
    brls::View* createContentView() override {
        return wrapWallpaper(brls::View::createFromXMLFile("romfs:/xml/view_splash.xml"));
    }

    SplashActivity() {}

    void onContentAvailable() override {
        brls::Activity::onContentAvailable();

        if (this->getContentView()) {
            this->getContentView()->setFocusable(true);
            this->getContentView()->setHideHighlight(true);
            brls::Application::giveFocus(this->getContentView());
        }

        auto dismissed = std::make_shared<bool>(false);
        auto dismiss = [dismissed](brls::View*) {
            if (!*dismissed) {
                *dismissed = true;
                brls::Application::popActivity(brls::TransitionAnimation::FADE);
            }
            return true;
        };

        this->registerAction("", brls::BUTTON_A, dismiss);
        this->registerAction("", brls::BUTTON_B, dismiss);
        if (this->getContentView()) {
            this->getContentView()->registerClickAction([dismiss](brls::View* v) {
                return dismiss(v);
            });
        }

        // Transicion automatica suave a los 1100 ms
        brls::delay(1100, [dismissed]() {
            if (!*dismissed) {
                *dismissed = true;
                brls::Application::popActivity(brls::TransitionAnimation::FADE);
            }
        });
    }
};

// -----------------------------------------------------------------------------
// main
// -----------------------------------------------------------------------------
int main(int argc, char* argv[]) {
    (void)argc;
    (void)argv;

    mkdir("sdmc:/switch", 0777);
    mkdir("sdmc:/switch/fifa07", 0777);
    mkdir(wineRoot().c_str(), 0777);

    // Preferencias del usuario (tema / fondo de pantalla). En el primer arranque
    // no hay fichero: se usan los valores por defecto (tema AMOLED + fondo
    // incluido en el romfs) y se crea config.ini. Si ya existe, se respeta.
    AppConfig::get().load();

    std::string logPath = wineRoot() + "/fifa07nx.log";
    FILE* logf = fopen(logPath.c_str(), "w");
    if (logf) {
        setvbuf(logf, NULL, _IONBF, 0);
        brls::Logger::setLogLevel(brls::LogLevel::LOG_DEBUG);
        brls::Logger::setLogOutput(logf);
        brls::Logger::info("07z iniciando...");
    }

    brls::Platform::APP_LOCALE_DEFAULT = AppConfig::get().language;

    if (!brls::Application::init()) {
        brls::Logger::error("No se pudo inicializar Borealis");
        if (logf) fclose(logf);
        return EXIT_FAILURE;
    }

    brls::Application::createWindow("07z");
    applyAppTheme(AppConfig::get().theme);
    brls::Application::setGlobalQuit(false);

    try {
        brls::Application::pushActivity(new MenuActivity());
        brls::Application::pushActivity(new SplashActivity(), brls::TransitionAnimation::NONE);
        while (brls::Application::mainLoop());
    } catch (const std::exception& e) {
        brls::Logger::error("Excepcion interceptada: {}", e.what());
    }

    if (logf) {
        brls::Logger::info("07z cerrado correctamente.");
        fclose(logf);
    }

    return EXIT_SUCCESS;
}
