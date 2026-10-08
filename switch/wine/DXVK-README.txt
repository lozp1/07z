Wine-NX build 108: the DXVK checkpoint, as an overlay for a card that
holds a full package. It replaces the runtime NRO with the one linked with
Mesa 26 (mesa-switch: OpenGL through nvc0, Vulkan through NVK), adds Wine's
Vulkan (vulkan-1.dll and winevulkan.dll), and adds the folder C:\dxvk with
DXVK v3.1-17-g878473ba's d3d9.dll and the Direct3D 9 test.

Keep your current switch/wine/wine-nx-runtime.nro somewhere else to go back,
then copy the switch folder to the SD card, merging folders.

Only programs in a folder that holds DXVK's d3d9.dll use DXVK: a program's own
folder comes first when Windows DLLs are found. Everything else keeps Wine's
d3d9, which draws through wined3d and OpenGL.

Frames of any size other than the screen's (800x600 or 640x480 in full screen)
are scaled into 1280x720 screen buffers, keeping the aspect ratio. Vulkan memory
of 32-bit programs stays in the driver's own mappings, outside their address
space.

- C:\dxvk\pe32-d3d9.exe and pe32-d3d9-800.exe: red, green and blue frames with
  a white triangle, read back every frame, ending in [D3D9 TEST] PASS.
- C:\dxvk\pe32-vulkan.exe: Vulkan memory, surface and swapchain checks.
- C:\dxvk\pe32-section.exe: sections with no file, which DXVK's d3d9 uses.
- Need for Speed Underground 2: copy C:\dxvk\d3d9.dll next to SPEED2.EXE
  (delete that copy to return to wined3d). C:\dxvk\nfsu2-hud\dxvk.conf, copied
  next to it too, draws DXVK's frame rate.
