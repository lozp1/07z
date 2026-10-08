/* swapprobe.exe - diagnostic probe for the FIFA 07 "free swap file space" check.
 *
 * The game aborts with "FIFA 07 requires at least N MB of free swap file space"
 * and the log says nothing about which query failed. This prints every value a
 * Win32 program can read about memory, paging and free space, so the numbers
 * from a working Windows box and from Wine-NX can be diffed: whichever field is
 * zero (or absurd) on the console is the one the game is reading.
 *
 * Built for i386 by tools/build-fifa07-shims.py; run on Windows directly, or on
 * the console by placing it in drive_c so the runtime's programme list sees it.
 */
#define WIN32_LEAN_AND_MEAN
/* mingw's own printf: msvcrt.dll alone does not understand %llu. */
#define __USE_MINGW_ANSI_STDIO 1
#include <windows.h>
#include <psapi.h>
#include <stdio.h>

static void memory(void)
{
    MEMORYSTATUS ms;
    MEMORYSTATUSEX mx;
    PERFORMANCE_INFORMATION pi;

    ZeroMemory(&ms, sizeof ms);
    ms.dwLength = sizeof ms;
    GlobalMemoryStatus(&ms);
    printf("GlobalMemoryStatus      : memLoad=%lu%% totalPhys=%lu availPhys=%lu "
           "totalPageFile=%lu availPageFile=%lu totalVirtual=%lu availVirtual=%lu\n",
           ms.dwMemoryLoad, ms.dwTotalPhys, ms.dwAvailPhys,
           ms.dwTotalPageFile, ms.dwAvailPageFile,
           ms.dwTotalVirtual, ms.dwAvailVirtual);

    ZeroMemory(&mx, sizeof mx);
    mx.dwLength = sizeof mx;
    if (GlobalMemoryStatusEx(&mx))
        printf("GlobalMemoryStatusEx    : memLoad=%lu%% totalPhys=%llu availPhys=%llu "
               "totalPageFile=%llu availPageFile=%llu totalVirtual=%llu availVirtual=%llu\n",
               mx.dwMemoryLoad, mx.ullTotalPhys, mx.ullAvailPhys,
               mx.ullTotalPageFile, mx.ullAvailPageFile,
               mx.ullTotalVirtual, mx.ullAvailVirtual);
    else
        printf("GlobalMemoryStatusEx    : FAILED err=%lu\n", GetLastError());

    ZeroMemory(&pi, sizeof pi);
    {
        /* psapi.dll is not guaranteed to exist in a minimal prefix (the FEXTendo
           runtime's, for one), so resolve the call at run time and never import it. */
        HMODULE psapi = LoadLibraryA("psapi.dll");
        BOOL (WINAPI *get_perf)(PPERFORMANCE_INFORMATION, DWORD) = NULL;
        if (psapi)
            *(FARPROC *)&get_perf = GetProcAddress(psapi, "GetPerformanceInfo");
        if (get_perf && get_perf(&pi, sizeof pi))
            printf("GetPerformanceInfo      : commitTotal=%llu commitLimit=%llu commitPeak=%llu "
                   "physTotal=%llu physAvail=%llu sysCache=%llu pageSize=%llu\n",
                   (unsigned long long)pi.CommitTotal * pi.PageSize,
                   (unsigned long long)pi.CommitLimit * pi.PageSize,
                   (unsigned long long)pi.CommitPeak * pi.PageSize,
                   (unsigned long long)pi.PhysicalTotal * pi.PageSize,
                   (unsigned long long)pi.PhysicalAvailable * pi.PageSize,
                   (unsigned long long)pi.SystemCache * pi.PageSize,
                   (unsigned long long)pi.PageSize);
        else
            printf("GetPerformanceInfo      : no disponible (psapi.dll ausente o llamada fallida)\n");
        if (psapi) FreeLibrary(psapi);
    }
}

static void space(const char *path)
{
    ULARGE_INTEGER freeToCaller, total, totalFree;
    DWORD spc, bps, clustersFree, clustersTotal;

    if (GetDiskFreeSpaceExA(path, &freeToCaller, &total, &totalFree))
        printf("GetDiskFreeSpaceEx(%-14s): freeToCaller=%llu MB  total=%llu MB  totalFree=%llu MB\n",
               path, freeToCaller.QuadPart >> 20, total.QuadPart >> 20,
               totalFree.QuadPart >> 20);
    else
        printf("GetDiskFreeSpaceEx(%-14s): FAILED err=%lu\n", path, GetLastError());

    if (GetDiskFreeSpaceA(path, &spc, &bps, &clustersFree, &clustersTotal))
        printf("GetDiskFreeSpace(%-16s): sectorsPerCluster=%lu bytesPerSector=%lu "
               "freeClusters=%lu totalClusters=%lu -> %llu MB free\n",
               path, spc, bps, clustersFree, clustersTotal,
               ((unsigned long long)clustersFree * spc * bps) >> 20);
    else
        printf("GetDiskFreeSpace(%-16s): FAILED err=%lu\n", path, GetLastError());
}

static void misc(void)
{
    SYSTEM_INFO si;
    OSVERSIONINFOA os;
    char volume[MAX_PATH] = {0};
    DWORD serial = 0, maxComponent = 0, flags = 0;
    char tmp[MAX_PATH] = {0}, file[MAX_PATH] = {0};
    HANDLE h;
    DWORD written;

    ZeroMemory(&si, sizeof si);
    GetSystemInfo(&si);
    printf("GetSystemInfo           : processors=%lu pageSize=%lu allocGran=%lu\n",
           si.dwNumberOfProcessors, si.dwPageSize, si.dwAllocationGranularity);

    ZeroMemory(&os, sizeof os);
    os.dwOSVersionInfoSize = sizeof os;
    if (GetVersionExA(&os))
        printf("GetVersionEx            : %lu.%lu build %lu platform %lu sp='%s'\n",
               os.dwMajorVersion, os.dwMinorVersion, os.dwBuildNumber,
               os.dwPlatformId, os.szCSDVersion);
    else
        printf("GetVersionEx            : FAILED err=%lu\n", GetLastError());

    if (GetVolumeInformationA("C:\\", volume, MAX_PATH, &serial, &maxComponent, &flags, NULL, 0))
        printf("GetVolumeInformation(C:): name='%s' serial=%08lx flags=0x%lx maxComponent=%lu\n",
               volume, serial, flags, maxComponent);
    else
        printf("GetVolumeInformation(C:): FAILED err=%lu\n", GetLastError());

    printf("GetLogicalDrives        : 0x%08lx\n", GetLogicalDrives());

    if (GetTempPathA(MAX_PATH, tmp))
        printf("GetTempPath             : %s\n", tmp);

    if (GetTempFileNameA(tmp, "prb", 0, file)) {
        h = CreateFileA(file, GENERIC_WRITE, 0, NULL, CREATE_ALWAYS,
                        FILE_ATTRIBUTE_TEMPORARY, NULL);
        if (h != INVALID_HANDLE_VALUE) {
            char buf[64 * 1024];
            ZeroMemory(buf, sizeof buf);
            if (WriteFile(h, buf, sizeof buf, &written, NULL))
                printf("write test              : OK (%lu bytes to %s)\n", written, file);
            else
                printf("write test              : WriteFile FAILED err=%lu\n", GetLastError());
            CloseHandle(h);
            DeleteFileA(file);
        } else {
            printf("write test              : CreateFile FAILED err=%lu\n", GetLastError());
        }
    }
}

int main(void)
{
    /* A console-less runtime (FEXTendo) does not capture stdout: leave the
       report on the card as well, as C:\swapprobe.txt. */
    freopen("C:\\swapprobe.txt", "w", stdout);
    printf("=== swapprobe (i386) ===\n");
    memory();
    space("C:\\");
    space("C:\\FIFA 07");
    space("C:\\windows\\temp");
    misc();
    printf("=== fin ===\n");
    fclose(stdout);
    return 0;
}
