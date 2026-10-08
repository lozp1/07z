// =============================================================================
// 07z — Configuracion persistente (adaptada de FileZzz/AppConfig)
// -----------------------------------------------------------------------------
// Guarda en  sdmc:/switch/07z/config.ini  las preferencias de interfaz:
//     tema (Dark | AMOLED), fondo de pantalla y su opacidad, e idioma.
//
// IMPORTANTE: el tema por defecto es AMOLED. Si NO existe el fichero de
// configuracion (primer arranque), se usan estos valores y se crea el fichero;
// si ya existe una preferencia guardada, SE RESPETA.
// =============================================================================
#pragma once

#include <string>
#include <fstream>
#include <sys/stat.h>

static const char* FIFA_KEYS_CONFIG_PATH = "sdmc:/switch/07z/config.ini";

// Fondo de pantalla por defecto incluido en el romfs del NRO.
static const char* FIFA_DEFAULT_WALLPAPER = "romfs:/img/default_wallpaper.jpg";

struct AppConfig {
    // UI
    std::string language        = "es-419";
    std::string theme           = "AMOLED";   // <-- por defecto AMOLED
    std::string wallpaperPath   = "";         // "" => usar el fondo incluido (romfs)
    float       wallpaperOpacity = 0.40f;
    bool        showFps          = false;     // contador de FPS en pantalla (dxvk-hud)

    static AppConfig& get() {
        static AppConfig s_instance;
        return s_instance;
    }

    void load(const std::string& path = FIFA_KEYS_CONFIG_PATH) {
        std::ifstream file(path);
        if (!file.is_open()) {
            // Primer arranque: no hay preferencia guardada -> valores por
            // defecto (tema AMOLED + fondo incluido) y se persiste el fichero.
            save(path);
            return;
        }

        std::string line;
        std::string currentSection;
        while (std::getline(file, line)) {
            size_t start = line.find_first_not_of(" \t\r\n");
            if (start == std::string::npos) continue;
            line = line.substr(start);
            if (line.empty() || line[0] == ';' || line[0] == '#') continue;

            if (line.front() == '[' && line.back() == ']') {
                currentSection = line.substr(1, line.size() - 2);
                continue;
            }

            size_t eq = line.find('=');
            if (eq == std::string::npos) continue;

            std::string key = line.substr(0, eq);
            std::string val = line.substr(eq + 1);

            key.erase(key.find_last_not_of(" \t\r\n") + 1);
            size_t vStart = val.find_first_not_of(" \t\r\n");
            if (vStart != std::string::npos) val = val.substr(vStart);
            val.erase(val.find_last_not_of(" \t\r\n") + 1);
            if (val.empty() && key.empty()) continue;

            if (currentSection == "UI") {
                try {
                    if (key == "Language") language = val;
                    else if (key == "Theme") theme = val;
                    else if (key == "Wallpaper") wallpaperPath = val;
                    else if (key == "WallpaperOpacity" && !val.empty()) wallpaperOpacity = std::stof(val);
                    else if (key == "ShowFps") showFps = (val == "1" || val == "true" || val == "True" || val == "on");
                } catch (...) {
                    // Valor corrupto: se conserva el valor por defecto.
                }
            }
        }
    }

    void save(const std::string& path = FIFA_KEYS_CONFIG_PATH) {
        mkdir("sdmc:/switch", 0777);
        mkdir("sdmc:/switch/07z", 0777);

        std::ofstream file(path);
        if (!file.is_open()) return;

        file << "; 07z - Fichero de configuracion\n\n";
        file << "[UI]\n";
        file << "Language = " << language << "\n";
        file << "Theme = " << theme << "\n";
        file << "Wallpaper = " << wallpaperPath << "\n";
        file << "WallpaperOpacity = " << wallpaperOpacity << "\n";
        file << "ShowFps = " << (showFps ? 1 : 0) << "\n";
    }
};
