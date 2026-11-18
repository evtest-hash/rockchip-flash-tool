<?xml version='1.0' encoding='utf-8'?>
<TS version="2.1" language="zh_CN" sourcelanguage="en">
    <context>
        <name>Driver</name>
        <message>
            <location filename="../win_driver.py" line="111" />
            <source>Unsupported processor architecture: %(arch)s</source>
            <translation>不支持的处理器架构：%(arch)s</translation>
        </message>
        <message>
            <location filename="../win_driver.py" line="124" />
            <source>Unsupported Windows version: %(major)s.%(minor)s</source>
            <translation>不支持的 Windows 版本：%(major)s.%(minor)s</translation>
        </message>
        <message>
            <location filename="../win_driver.py" line="133" />
            <source>Driver package incomplete: %(path)s</source>
            <translation>驱动包不完整：%(path)s</translation>
        </message>
        <message>
            <location filename="../win_driver.py" line="179" />
            <source>Driver installation cancelled.</source>
            <translation>已取消驱动安装。</translation>
        </message>
        <message>
            <location filename="../win_driver.py" line="182" />
            <source>Failed to request administrator privileges (0x%(code)08X).</source>
            <translation>请求管理员权限失败（0x%(code)08X）。</translation>
        </message>
        <message>
            <location filename="../win_driver.py" line="195" />
            <source>Driver installation timed out.</source>
            <translation>驱动安装超时。</translation>
        </message>
        <message>
            <location filename="../win_driver.py" line="199" />
            <source>Could not read installer exit code (0x%(code)08X).</source>
            <translation>无法读取安装程序的退出码（0x%(code)08X）。</translation>
        </message>
        <message>
            <location filename="../win_driver.py" line="210" />
            <source>Internal error: invalid driver installation request.</source>
            <translation>内部错误：无效的驱动安装请求。</translation>
        </message>
        <message>
            <location filename="../win_driver.py" line="214" />
            <source>Windows rejected the driver installation (0x%(code)08X).</source>
            <translation>Windows 拒绝安装驱动（0x%(code)08X）。</translation>
        </message>
    </context>
    <context>
        <name>FlashWorker</name>
        <message>
            <location filename="../main_window.py" line="58" />
            <source>Flash completed successfully.</source>
            <translation>烧录成功完成。</translation>
        </message>
        <message>
            <location filename="../main_window.py" line="60" />
            <source>Flash failed.</source>
            <translation>烧录失败。</translation>
        </message>
        <message>
            <location filename="../main_window.py" line="65" />
            <source>

Suggestion:
%(suggestion)s</source>
            <translation>

建议：
%(suggestion)s</translation>
        </message>
        <message>
            <location filename="../main_window.py" line="72" />
            <source>Unexpected error: %(error)s

%(traceback)s</source>
            <translation>发生意外错误：%(error)s

%(traceback)s</translation>
        </message>
    </context>
    <context>
        <name>Flasher</name>
        <message>
            <location filename="../flasher.py" line="57" />
            <source>Scanning for Rockchip devices...</source>
            <translation>正在查找 Rockchip 设备…</translation>
        </message>
        <message>
            <location filename="../flasher.py" line="63" />
            <source>Move one board to a different USB port, then refresh.</source>
            <translation>请将其中一块板子换到其他 USB 端口，然后刷新。</translation>
        </message>
        <message>
            <location filename="../flasher.py" line="70" />
            <source>Please connect the board and enter Loader/Maskrom mode.</source>
            <translation>请连接设备，并使其进入 Loader 或 Maskrom 模式。</translation>
        </message>
        <message>
            <location filename="../flasher.py" line="76" />
            <source>Found %(chip)s in %(mode)s mode</source>
            <translation>已检测到 %(chip)s，当前为 %(mode)s 模式</translation>
        </message>
        <message>
            <location filename="../flasher.py" line="92" />
            <source>Could not determine chip model.</source>
            <translation>无法确定芯片型号。</translation>
        </message>
        <message>
            <location filename="../flasher.py" line="95" />
            <source>Analyzing image format...</source>
            <translation>正在识别镜像格式…</translation>
        </message>
        <message>
            <location filename="../flasher.py" line="105" />
            <source>No partition table found; writing as a raw image.</source>
            <translation>未检测到分区表，将按原始镜像写入。</translation>
        </message>
        <message>
            <location filename="../flasher.py" line="112" />
            <source>RK firmware detected, flashing via UF directly.</source>
            <translation>已识别 Rockchip 固件包，将直接烧录。</translation>
        </message>
        <message>
            <location filename="../flasher.py" line="120" />
            <source>Loader mode detected, flashing raw image directly.</source>
            <translation>当前为 Loader 模式，直接写入原始镜像。</translation>
        </message>
        <message>
            <location filename="../flasher.py" line="125" />
            <source>Starting flash...</source>
            <translation>开始烧录…</translation>
        </message>
        <message>
            <location filename="../flasher.py" line="129" />
            <source>Flashing failed.</source>
            <translation>烧录失败。</translation>
        </message>
        <message>
            <location filename="../flasher.py" line="130" />
            <source>Please reconnect the board and retry.</source>
            <translation>请重新连接设备后重试。</translation>
        </message>
        <message>
            <location filename="../flasher.py" line="135" />
            <source>Resetting device...</source>
            <translation>正在复位设备…</translation>
        </message>
        <message>
            <location filename="../flasher.py" line="138" />
            <source>Device reset did not confirm; power-cycle the board.</source>
            <translation>未能确认设备已复位，请将设备断电后重新上电。</translation>
        </message>
        <message>
            <location filename="../flasher.py" line="144" />
            <source>Flash completed successfully.</source>
            <translation>烧录成功完成。</translation>
        </message>
        <message>
            <location filename="../flasher.py" line="150" />
            <source>Check tool files and USB connection.</source>
            <translation>请检查工具文件和 USB 连接。</translation>
        </message>
        <message>
            <location filename="../flasher.py" line="157" />
            <source>Maskrom mode: downloading bootloader...</source>
            <translation>当前为 Maskrom 模式，正在向设备下载引导程序…</translation>
        </message>
        <message>
            <location filename="../flasher.py" line="163" />
            <source>No bootloader found for %(chip)s.</source>
            <translation>未找到适用于 %(chip)s 的引导程序。</translation>
        </message>
        <message>
            <location filename="../flasher.py" line="168" />
            <source>Make sure vendor/rkbin contains a matching loader.</source>
            <translation>请确认内置资源中包含匹配的 Loader。</translation>
        </message>
        <message>
            <location filename="../flasher.py" line="174" />
            <source>Downloading %(name)s</source>
            <translation>正在向设备下载 %(name)s…</translation>
        </message>
        <message>
            <location filename="../flasher.py" line="180" />
            <source>Bootloader download failed.</source>
            <translation>引导程序下载失败。</translation>
        </message>
        <message>
            <location filename="../flasher.py" line="187" />
            <source>Flashing...</source>
            <translation>正在烧录…</translation>
        </message>
    </context>
    <context>
        <name>ImageFormat</name>
        <message>
            <location filename="../image_format.py" line="41" />
            <source>Image file not found: %(path)s</source>
            <translation>未找到镜像文件：%(path)s</translation>
        </message>
    </context>
    <context>
        <name>MainWindow</name>
        <message>
            <location filename="../main_window.py" line="88" />
            <location filename="../main_window.py" line="224" />
            <location filename="../main_window.py" line="322" />
            <source>No device connected</source>
            <translation>未连接设备</translation>
        </message>
        <message>
            <location filename="../main_window.py" line="93" />
            <location filename="../main_window.py" line="222" />
            <location filename="../main_window.py" line="256" />
            <location filename="../main_window.py" line="604" />
            <source>Ready</source>
            <translation>就绪</translation>
        </message>
        <message>
            <location filename="../main_window.py" line="213" />
            <source>Rockchip Flash Tool</source>
            <translation>瑞芯微烧录工具</translation>
        </message>
        <message>
            <location filename="../main_window.py" line="215" />
            <source>Device</source>
            <translation>设备</translation>
        </message>
        <message>
            <location filename="../main_window.py" line="216" />
            <source>Firmware</source>
            <translation>固件</translation>
        </message>
        <message>
            <location filename="../main_window.py" line="217" />
            <source>Refresh</source>
            <translation>刷新</translation>
        </message>
        <message>
            <location filename="../main_window.py" line="218" />
            <source>Browse</source>
            <translation>浏览</translation>
        </message>
        <message>
            <location filename="../main_window.py" line="219" />
            <source>Start Flash</source>
            <translation>开始烧录</translation>
        </message>
        <message>
            <location filename="../main_window.py" line="220" />
            <source>Select firmware image file…</source>
            <translation>选择固件镜像文件…</translation>
        </message>
        <message>
            <location filename="../main_window.py" line="233" />
            <source>Rockchip Firmware (RKFW)</source>
            <translation>Rockchip 固件（RKFW）</translation>
        </message>
        <message>
            <location filename="../main_window.py" line="234" />
            <source>Rockchip Firmware (RKAF)</source>
            <translation>Rockchip 固件（RKAF）</translation>
        </message>
        <message>
            <location filename="../main_window.py" line="235" />
            <source>Raw Disk Image</source>
            <translation>原始磁盘镜像</translation>
        </message>
        <message>
            <location filename="../main_window.py" line="236" />
            <source>Unknown</source>
            <translation>未知格式</translation>
        </message>
        <message>
            <location filename="../main_window.py" line="248" />
            <source>Parse error</source>
            <translation>解析失败</translation>
        </message>
        <message>
            <location filename="../main_window.py" line="260" />
            <source>upgrade_tool not found</source>
            <translation>未找到 upgrade_tool</translation>
        </message>
        <message>
            <location filename="../main_window.py" line="323" />
            <source>Connected</source>
            <translation>已连接</translation>
        </message>
        <message>
            <location filename="../main_window.py" line="325" />
            <source>SN %(serial)s</source>
            <translation>序列号 %(serial)s</translation>
        </message>
        <message>
            <location filename="../main_window.py" line="336" />
            <source>Mode: %(mode)s   |   USB port ID: %(port)s   |   Serial: %(serial)s</source>
            <translation>模式：%(mode)s   |   USB 端口标识：%(port)s   |   序列号：%(serial)s</translation>
        </message>
        <message>
            <location filename="../main_window.py" line="406" />
            <source>Format: %(format)s  |  Size: %(size)s</source>
            <translation>格式：%(format)s  |  大小：%(size)s</translation>
        </message>
        <message>
            <location filename="../main_window.py" line="421" />
            <source>Device scan failed: %(error)s</source>
            <translation>设备扫描失败：%(error)s</translation>
        </message>
        <message>
            <location filename="../main_window.py" line="427" />
            <source>Scanning for devices...</source>
            <translation>正在查找 Rockchip 设备…</translation>
        </message>
        <message>
            <location filename="../main_window.py" line="434" />
            <source>Select Firmware</source>
            <translation>选择固件</translation>
        </message>
        <message>
            <location filename="../main_window.py" line="436" />
            <source>Images (*.img *.bin *.raw);;All Files (*)</source>
            <translation>镜像文件 (*.img *.bin *.raw);;所有文件 (*)</translation>
        </message>
        <message>
            <location filename="../main_window.py" line="456" />
            <source>Firmware loaded: %(name)s</source>
            <translation>已加载固件：%(name)s</translation>
        </message>
        <message>
            <location filename="../main_window.py" line="462" />
            <source>Firmware parse error: %(error)s</source>
            <translation>固件解析失败：%(error)s</translation>
        </message>
        <message>
            <location filename="../main_window.py" line="494" />
            <source>Error</source>
            <translation>错误</translation>
        </message>
        <message>
            <location filename="../main_window.py" line="494" />
            <source>upgrade_tool not found.</source>
            <translation>未找到 upgrade_tool。</translation>
        </message>
        <message>
            <location filename="../main_window.py" line="499" />
            <source>No Firmware</source>
            <translation>未选择固件</translation>
        </message>
        <message>
            <location filename="../main_window.py" line="499" />
            <source>Please select firmware first.</source>
            <translation>请先选择固件。</translation>
        </message>
        <message>
            <location filename="../main_window.py" line="503" />
            <source>File Not Found</source>
            <translation>文件不存在</translation>
        </message>
        <message>
            <location filename="../main_window.py" line="507" />
            <source>No Device</source>
            <translation>未选择设备</translation>
        </message>
        <message>
            <location filename="../main_window.py" line="507" />
            <source>Please select a device first.</source>
            <translation>请先选择设备。</translation>
        </message>
        <message>
            <location filename="../main_window.py" line="516" />
            <source>Starting flash...</source>
            <translation>开始烧录…</translation>
        </message>
        <message>
            <location filename="../main_window.py" line="544" />
            <source>Rockchip Driver Required</source>
            <translation>需要 Rockchip 驱动</translation>
        </message>
        <message>
            <location filename="../main_window.py" line="546" />
            <source>Rockchip USB driver is not detected on this Windows system.

You must install it before flashing.

Install driver now?</source>
            <translation>未检测到 Rockchip USB 驱动。

烧录前必须先安装驱动。

是否现在安装？</translation>
        </message>
        <message>
            <location filename="../main_window.py" line="554" />
            <source>Driver is required before flashing.</source>
            <translation>烧录前需要安装驱动。</translation>
        </message>
        <message>
            <location filename="../main_window.py" line="558" />
            <source>Installing Rockchip driver...</source>
            <translation>正在安装 Rockchip 驱动…</translation>
        </message>
        <message>
            <location filename="../main_window.py" line="562" />
            <source>Driver Installation</source>
            <translation>驱动安装</translation>
        </message>
        <message>
            <location filename="../main_window.py" line="563" />
            <source>Driver installation cancelled.</source>
            <translation>已取消驱动安装。</translation>
        </message>
        <message>
            <location filename="../main_window.py" line="565" />
            <location filename="../main_window.py" line="570" />
            <source>Driver Install Failed</source>
            <translation>驱动安装失败</translation>
        </message>
        <message>
            <location filename="../main_window.py" line="571" />
            <source>Unexpected error: %(error)s</source>
            <translation>发生意外错误：%(error)s</translation>
        </message>
        <message>
            <location filename="../main_window.py" line="578" />
            <source>Driver Not Detected</source>
            <translation>未检测到驱动</translation>
        </message>
        <message>
            <location filename="../main_window.py" line="580" />
            <source>Driver installation finished, but Rockchip driver is still not detected.

Please reopen this app after installing the driver as Administrator.</source>
            <translation>驱动安装完成，但仍未检测到 Rockchip 驱动。

请以管理员身份安装驱动后重新打开本应用。</translation>
        </message>
        <message>
            <location filename="../main_window.py" line="586" />
            <source>Rockchip driver ready.</source>
            <translation>Rockchip 驱动已就绪。</translation>
        </message>
        <message>
            <location filename="../main_window.py" line="606" />
            <location filename="../main_window.py" line="610" />
            <source>Flash completed.</source>
            <translation>烧录完成。</translation>
        </message>
        <message>
            <location filename="../main_window.py" line="606" />
            <source>Flash failed.</source>
            <translation>烧录失败。</translation>
        </message>
        <message>
            <location filename="../main_window.py" line="610" />
            <source>Success</source>
            <translation>成功</translation>
        </message>
        <message>
            <location filename="../main_window.py" line="613" />
            <source>Flash Failed</source>
            <translation>烧录失败</translation>
        </message>
    </context>
    <context>
        <name>UpgradeTool</name>
        <message>
            <location filename="../upgrade_tool.py" line="28" />
            <source>Command timed out: %(command)s</source>
            <translation>命令执行超时：%(command)s</translation>
        </message>
        <message>
            <location filename="../upgrade_tool.py" line="98" />
            <source>Unknown (PID=0x%(pid)04X)</source>
            <translation>未知（PID=0x%(pid)04X）</translation>
        </message>
        <message>
            <location filename="../upgrade_tool.py" line="119" />
            <source>upgrade_tool not found: %(path)s</source>
            <translation>未找到 upgrade_tool：%(path)s</translation>
        </message>
        <message>
            <location filename="../upgrade_tool.py" line="134" />
            <source>Bundled upgrade_tool not found: %(path)s</source>
            <translation>未找到内置的 upgrade_tool：%(path)s</translation>
        </message>
        <message>
            <location filename="../upgrade_tool.py" line="281" />
            <source>Failed to capture upgrade_tool output on Windows.</source>
            <translation>无法读取 upgrade_tool 的输出。</translation>
        </message>
        <message>
            <location filename="../upgrade_tool.py" line="603" />
            <source>No Rockchip device detected.</source>
            <translation>未检测到 Rockchip 设备。</translation>
        </message>
        <message>
            <location filename="../upgrade_tool.py" line="611" />
            <source>Device @%(id)s is no longer connected.</source>
            <translation>设备 @%(id)s 已断开连接。</translation>
        </message>
        <message>
            <location filename="../upgrade_tool.py" line="622" />
            <source>%(count)d devices report USB port ID %(id)s.</source>
            <translation>%(count)d 台设备报告相同的 USB 端口标识 %(id)s。</translation>
        </message>
        <message>
            <location filename="../upgrade_tool.py" line="665" />
            <source>Loader not found: %(path)s</source>
            <translation>未找到 Loader：%(path)s</translation>
        </message>
        <message>
            <location filename="../upgrade_tool.py" line="685" />
            <source>Firmware not found: %(path)s</source>
            <translation>未找到固件：%(path)s</translation>
        </message>
        <message>
            <location filename="../upgrade_tool.py" line="700" />
            <source>Image not found: %(path)s</source>
            <translation>未找到镜像文件：%(path)s</translation>
        </message>
    </context>
</TS>