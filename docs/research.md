# KeyMouse 调研记录

## 来源与适用范围

本页保留 2026-10-17 的源码与文档调研，来自 [KeyMouse #1 的调研评论](https://github.com/AwayerCode/KeyMouse/issues/1#issuecomment-6251462686)，最初记录在 Sisi #35。

截至本次仓库初始化，已确定项目名称 KeyMouse，并创建公开仓库；尚未进行三平台运行验证。以下历史原文中“不创建实现仓库”等阶段安排已经被仓库创建取代，技术路线仍为候选。源码快照与外部问题状态应在选型前重新核对。

## 继续研究的重点

- 首版键鼠绑定范围、组合前缀、触发时机与冲突规则。
- 原生同步拦截与异步业务通知的边界。
- 各平台可用性、授权、事件配对和生命周期恢复。
- 复用与自研的维护成本、许可证及分发方式。

## 历史调研原文

## 2026-10-17 调研记录：跨平台全局键盘、鼠标快捷能力

### 当前安排

本次仅保存调研、明确候选方向，暂不开发、不创建实现仓库、不发布包。Issue 保持 open，后续由用户决定何时继续。下述架构为建议，复用或重写尚未最终选定；本次没有完成三平台运行验证。

### 已明确的需求与定位

- 面向 Node.js / Electron 的开源原生扩展；应用在后台、没有焦点时仍可触发功能。
- 用户可以配置单键和组合键、一个或多个绑定；需要考虑全局键盘及鼠标 Hook，区分只监听与阻止原始输入继续传递的拦截。
- 候选技术路线为 C++ 核心 + Node-API；不是 C#。Windows/macOS/Linux 是目标平台，但 Linux 必须分别描述 X11 与 Wayland 能力。
- 单独修饰键、左右修饰键、键鼠组合、长按、松开触发、任意多普通键组合等属于待确认的详细范围，不因本次讨论自动全部列为首版承诺。
- Electron globalShortcut 适合标准快捷键注册，没有完整全局键鼠事件流、鼠标 Hook、keyup 或逐事件吞键/透传接口，不能覆盖本任务讨论的全部 Hook 能力。

### 调研依据与候选库状态

本次通过 gh 下载公开源码到临时目录阅读，核查接口、原生分发、三个平台后端、构建配置和补丁；未编译或运行 Hook，也未申请系统输入权限。以下是读取到的源码快照，不代表所有 npm 发布二进制均已验证。

| 候选 | 本次源码状态 | 定位与维护注意事项 |
| --- | --- | --- |
| [uiohook-napi](https://github.com/SnosMe/uiohook-napi) | master `44e0d86`，提交日期 2026-03-21；package.json 版本 1.5.5；固定 libuiohook 子模块 `f259ff37e81125f6f91ebac5439e7cde1e78b296`，另有自带补丁 | C 编写的 Node-API 绑定，附 TypeScript 接口，提供预编译构建流程。不能将其等同于直接使用 libuiohook 最新分支。 |
| [libuiohook](https://github.com/kwhat/libuiohook) | 本次读取默认分支 HEAD `2a2d40f`，提交日期 2024-05-07 | C 编写的跨平台输入库；可由 C++ 调用。现有后端为 Windows、Darwin、X11，不能据“跨平台”推定完整 Wayland 支持。 |

这些提交日期是观察值，不能单凭日期判断项目已停止维护。[uiohook-napi 问题列表](https://github.com/SnosMe/uiohook-napi/issues) 中有 Windows 构建、Worker 生命周期、macOS 启动崩溃/延迟、键盘布局和 Linux ARM64 预编译等报告；这些是后续验证线索，不是本次复现结论，继续前需重新核对状态。

### 能力矩阵

“拦截”指阻止原始事件继续传给其他应用，不是单纯收到通知。

| 平台 | 全局键盘/鼠标监听 | 原版 uiohook-napi 拦截 | libuiohook 原生层拦截 |
| --- | --- | --- | --- |
| Windows | 支持，仍受系统场景限制 | 无接口 | 有消费事件的实现路径，需实测 |
| macOS | 支持，需要权限 | 无接口 | 有消费事件的实现路径，需实测 |
| Linux X11 | 支持，依赖 X server / XRecord 等条件 | 无接口 | 当前 XRecord 后端不能阻止原始事件 |
| Linux Wayland | 无完整原生全局后端 | 不支持 | 无现成完整后端；XWayland 不等于整个桌面覆盖 |

uiohook-napi 暴露 keydown/keyup、mousedown/mouseup、mousemove、click、wheel。可据此实现匹配逻辑，但鼠标事件不等于所有触控板手势、设备专有输入都支持。[接口源码](https://github.com/SnosMe/uiohook-napi/blob/44e0d86/src/index.ts)

### 核心发现：监听与拦截需要不同的接口设计

uiohook-napi 的 dispatch_proc 复制原生事件，再通过 napi_call_threadsafe_function(..., napi_tsfn_nonblocking) 异步发送给 JS。JS 收到的是副本，没有同步决定原始事件去留的通道；return false、修改 JS 事件或补一个表面的 preventDefault 都不能拦截原输入。[分发源码](https://github.com/SnosMe/uiohook-napi/blob/44e0d86/src/lib/addon.c#L11)

建议：JS 预先配置绑定及拦截规则，原生层同步匹配并决定吞键或透传，再异步通知 JS 执行业务。不要阻塞系统 Hook 等待 JS 返回；Windows 低级 Hook 有超时被静默移除的风险。[微软说明](https://learn.microsoft.com/en-us/windows/win32/winmsg/lowlevelkeyboardproc)

### 平台限制

**Windows**

- 使用 WH_KEYBOARD_LL / WH_MOUSE_LL。原生分发回调将 event.reserved 设为 0x01 后，底层可以不调用后续 Hook 并返回非零值，键盘和鼠标均有消费路径。
- 不能把普通桌面“全局”理解为所有安全桌面、权限级别和受保护输入都可覆盖；高权限窗口、锁屏返回、系统组合键需单独验证。
- Hook 必须快速返回。还需处理丢失事件、修饰键状态失步及重新初始化；uiohook-napi 已有 UIPI、前台窗口切换与修饰键状态补丁。
- 证据：[Windows 后端](https://github.com/kwhat/libuiohook/blob/2a2d40f/src/windows/input_hook.c)、[绑定自带补丁](https://github.com/SnosMe/uiohook-napi/blob/44e0d86/src/libuiohook.patch)。

**macOS**

- 使用 CGEventTapCreate，当前为可过滤事件的默认模式；消费事件时返回 NULL。
- 库会检查辅助功能信任状态；应用需处理授权、拒绝、撤销以及打包后身份变化的实际行为。
- Secure Input 会影响键盘事件监听；超时可能禁用 Event Tap，库已有重新启用路径，但恢复后的状态一致性仍需测试。
- C 接口可由 C++ 调用，不要求 Swift；周边 Cocoa 接口按需使用少量 Objective-C++。
- 证据：[Darwin 后端](https://github.com/kwhat/libuiohook/blob/2a2d40f/src/darwin/input_hook.c)、[权限检查](https://github.com/kwhat/libuiohook/blob/2a2d40f/src/darwin/input_helper.c)、[Karabiner 关于 Event Tap/Secure Input 的说明](https://github.com/pqrs-org/Karabiner-Elements/blob/main/DEVELOPMENT.md)。

**Linux X11**

- XRecord 用于观察事件；源码明确写有 “There is no way to consume the XRecord event.”，不能靠设置消费标志阻止原始输入。
- 若需拦截，要另设计 grab 等后端，并处理独占、冲突及不同事件语义，不能仅修改 Node 绑定解决。
- 证据：[X11 后端](https://github.com/kwhat/libuiohook/blob/2a2d40f/src/x11/input_hook.c#L800)。

**Linux Wayland**

- 当前没有完整原生后端。USE_EVDEV 涉及 X11 键码映射，不代表已经实现直接读取 Linux 输入设备的独立后端。
- GlobalShortcuts Portal 可注册受桌面环境和授权约束的快捷键，但不是任意键鼠全局监听及过滤接口。需要单独声明降级能力；自写 C++ 不会自动消除系统限制。
- 证据：[构建配置](https://github.com/SnosMe/uiohook-napi/blob/44e0d86/binding.gyp)、[X11 键码实现](https://github.com/kwhat/libuiohook/blob/2a2d40f/src/x11/input_helper.c)、[Wayland 议题](https://github.com/kwhat/libuiohook/issues/100)、[Portal 接口](https://flatpak.github.io/xdg-desktop-portal/docs/doc-org.freedesktop.portal.GlobalShortcuts.html)。

### 复用还是自研

- 只需监听并触发功能：优先用 uiohook-napi 验证需求，上层实现匹配。
- Windows/macOS 需要选择性拦截：可复用 libuiohook 并扩展原生规则接口，或自行实现精简平台后端；原版 uiohook-napi 不够用。
- Linux X11 拦截：需要额外后端。Wayland 不应承诺与其他平台具有完全相同的任意监听/拦截能力。
- 建议自研的重点是 C++ 快捷键引擎、原生同步拦截规则、Node-API 和能力查询；暂不认定必须重写所有输入采集代码。
- 许可证也是选型因素：uiohook-napi 为 MIT，但 libuiohook 源码声明 LGPL-3.0-or-later，当前 binding.gyp 静态链接底层。不能把整体依赖链当成纯 MIT；最终复用与分发方式需明确许可证要求。[底层声明](https://github.com/kwhat/libuiohook/blob/2a2d40f/include/uiohook.h)

候选架构：TypeScript 配置/业务 → Node-API → C++ 匹配与拦截引擎 → 平台输入后端。建议先验证 Windows/macOS，再对 Linux X11/Wayland 明确支持范围；这不是已经批准执行的实施计划。

### 后续继续时的检查项

1. 确认首版按键范围、键鼠组合、吞键/透传、重复触发和按下/松开语义。
2. 明确序列与组合的前缀处理：例如 A+B 在 A 按下时尚不能知道 B 是否随后按下；需决定是否先放行、延迟或其他策略，不能事后撤销已传出的 A。
3. 对比原库复用、扩展绑定与自写精简后端的修改量、许可证和维护成本，再决定实现仓库。
4. 在目标系统实测键盘/鼠标事件、左右修饰键、布局和输入法、权限拒绝/撤销、高权限窗口、休眠/锁屏恢复、按下/松开配对及 Hook 失效恢复。
5. 验证 Node/Electron 版本及目标 CPU 架构的安装、预编译加载、启停/退出和高频鼠标事件；不以 CI 构建成功代替功能验证。
6. 对不支持的能力明确返回状态或错误，避免静默降级；完成后将证据回写本 Issue。
