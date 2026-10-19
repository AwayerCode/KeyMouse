# KeyMouse 调研记录

## 来源与适用范围

本页保留 2026-10-17 的源码与文档调研，并在 2026-10-19 根据用户澄清和新增源码阅读重写当前判断。KeyMouse Issue #1 已于 2026-10-19 删除，当前仓库没有 Issue；本页不是在线任务入口。

本次通过 `gh` 读取源码、README、平台文档和上游提交，没有编译第三方项目、加载系统 Hook、申请权限或执行键鼠功能测试。以下“能做到”均指源码或官方文档展示的机制，不是 KeyMouse 的实测能力。

本页不比较“复用还是选型”。所有项目只作为能力样本和故障样本；KeyMouse 的输入内核由 C++ 自研，不继承它们的 API、进程模型或实现。

仓库命名、README、许可证、文档站、治理、安全和发布标准另见 [全球化开源项目标准](open-source-strategy.md)。

## 当前决策

- KeyMouse 的输入内核使用 C++ 从零实现。
- 不采用 `uiohook-napi`、`libuiohook`、`rdev`、`Interception`、kanata、Karabiner-Elements、xremap、keyd 或其他现成输入项目作为内核。
- 不把第三方项目包装成 KeyMouse 的产品核心，也不以其行为直接定义 KeyMouse 的支持范围。
- 这些项目仅作为参考实现，用于研究平台 API、事件语义、状态机、生命周期、故障模式和测试样本。
- KeyMouse 对外提供 TypeScript/Node.js 与 Python 两套语言接口，二者必须复用同一个 C++ 输入内核。
- TypeScript/Node.js 计划通过 Node-API 接入；Python 的绑定技术尚未确定。事件解析、规则匹配和吞键/透传决策留在自研 C++ 内核。
- 项目目前没有实现或运行验证。README 中的平台矩阵是调研路径，不是已支持功能。

## 语言接口与 C++ 内核边界

项目的产品核心是 C++ 输入内核，不是 TypeScript 或 Python 包装层。语言接口的职责是把同一套内核能力映射为各语言习惯的 API，而不是在语言侧实现另一套事件或规则引擎。

| 层级 | 负责 | 不负责 |
| --- | --- | --- |
| TypeScript/Node.js API | 类型、配置构建、异步事件订阅、生命周期封装、错误映射 | 平台 Hook、同步拦截决策、帧状态、设备状态 |
| Python API | 同一语义的 Python 对象与异常、异步通知、生命周期封装 | 同上的任何同步输入决策 |
| Native binding boundary | ABI、所有权、线程切换、异常隔离、有界通知队列 | 业务匹配规则和平台后端语义 |
| 自研 C++ 内核 | 事件模型、规则快照、状态机、`Pass`/`Consume`、能力与生命周期 | 语言特有 API 和业务动作 |
| 平台后端 | Hook、Event Tap、evdev/uinput、权限和平台错误 | 跨平台规则语义 |

语言绑定边界仍需在以下方案中选择或组合：

- 稳定 C ABI：最适合隔离 Node-API、Python 扩展和不同 C++ 工具链，但需要自行设计 opaque handle、错误码、缓冲区和 ABI 版本。
- 直接 C++ API：绑定实现更直接，但要求语言扩展与内核使用兼容的编译器、标准库、异常和运行时；独立预编译分发的风险更高。
- C++ API + 稳定 C ABI facade：内核内部保持 C++ 设计，所有语言绑定只依赖 C ABI；代价是多一层受控接口和转换。

无论采用哪种边界，以下约束不变：

- TypeScript 和 Python 必须暴露相同的事件、规则、能力、状态和错误语义，只允许命名与语言习惯不同。
- 同步拦截只能依据原生层已注册的规则快照完成，不能等待 Promise、asyncio、Node.js 事件循环或 Python 回调返回。
- 原生事件线程不得进入 Node.js 事件循环，也不得获取 Python GIL。
- 原生到语言运行时的通知必须经过有界队列；语言侧变慢、关闭或销毁时必须能丢弃通知并继续处理输入。
- 语言回调抛错、对象释放、进程退出和热重载不能破坏原生内核或留下卡住的按键状态。

## 是否存在可直接采用的独立键鼠库

结论不是“完全没有”，而是“**有独立库，但没有一个满足 KeyMouse 所需的完整跨平台键鼠内核**”。

| 项目 | 是否独立库 | 键盘 | 鼠标 | 拦截能力 | 主要缺口 |
| --- | --- | --- | --- | --- | --- |
| `rdev` | 是，Rust 库 | 是 | 按键、滚轮、移动 | `unstable_grab` 可同步消费 | API 明确 unstable；Linux 帧/设备语义、macOS 恢复和回调线程不完整 |
| `libuiohook` | 是，C 库 | 是 | 按键、滚轮、移动 | Windows/macOS 原生可消费；X11 只能观察 | 无完整 Wayland；无设备级保证；事件模型和生命周期简单 |
| `Interception` | 是，Windows C 库 + 驱动 | 是 | 按键、滚轮、相对/绝对移动 | 是，支持设备过滤和优先级 | Windows only；需要安装内核驱动；签名、兼容性和商业许可成本高 |
| `libinput` | 是，Linux 库 | 设备事件输入 | 设备事件输入 | 不作为系统级拦截层 | 没有跨平台消费模型，不能替代全局 Hook |
| `global-hotkey` / Electron `globalShortcut` | 是，注册型库/API | 组合触发 | 否 | 非通用消费 | 没有原始事件流、鼠标事件或任意组合拦截 |
| `kanata` / `xremap` / `keyd` / `Karabiner-Elements` | 否，主要是 daemon/应用 | 是 | 依项目而异 | 有，但绑定各自运行模型 | 不能作为可嵌入 TypeScript/Node.js 与 Python 应用的精简 C++ 库直接复用 |

因此，若“独立库”只要求能监听并在原生层消费键盘和鼠标，**rdev、libuiohook 和 Interception 已经做过**。若要求跨 Windows/macOS/Linux、支持设备级选择、鼠标移动/触控板、稳定生命周期、明确能力错误，并同时提供 TypeScript/Node.js 与 Python 接口，则目前没有一个现成库可直接作为 KeyMouse 内核。

## 能力定义

| 能力 | 含义 | 不能混淆的点 |
| --- | --- | --- |
| 全局监听 | 应用未聚焦时收到键鼠事件通知 | 不表示原事件可以被阻止 |
| 系统快捷键注册 | 向操作系统注册指定组合并收到触发通知 | 通常没有完整鼠标事件、keyup、设备身份或任意事件流 |
| 指定组合拦截 | 原生层消费预先知道的组合 | 规则必须在系统回调允许的时间内同步完成 |
| 任意事件消费 | 每个事件都能在原生层决定放行、消费或替换 | 不能等待 TypeScript、Python 或其他语言运行时返回 |
| 事件修改/重放 | 消费原事件后产生新的键鼠输出 | 顺序、回环识别、设备身份和失败恢复都要自行负责 |

KeyMouse 的核心定位要求完整键鼠事件流和原生选择性拦截；注册型接口只能作为能力对照或后续便捷 API，不能代替输入内核。鼠标事件、keyup、组合前缀、长按/点按、键鼠混合或选择性吞键都要求完整事件流与原生状态机。产品范围已包含键盘与鼠标，但触控板、绝对坐标设备和多指手势仍需单独确定。

## 参考实现快照

| 项目 | 本次读取版本 | 许可证 | 调研价值 |
| --- | --- | --- | --- |
| [kanata](https://github.com/jtroo/kanata) | `44edba27f9849b2494a4b9f5f003a4a5e932e277`，2026-10-14，`1.13.0-prerelease-2` | LGPL-3.0-only | 跨平台复杂重映射器、状态机、各平台 I/O 路径 |
| [Karabiner-Elements](https://github.com/pqrs-org/Karabiner-Elements) | `caabc7afb2fb13d20056152427145d02c3cd71aa`，2026-10-19 | 主仓库 Unlicense；预编译依赖另核 | macOS 设备级捕获、虚拟 HID、权限和进程拆分 |
| [xremap](https://github.com/xremap/xremap) | `a9877f873f87f66adfc1b106f4ab18c7a2ff3bbb`，2026-10-18，`v0.15.15` | MIT | Linux evdev/uinput、X11/Wayland 无关路径 |
| [keyd](https://github.com/rvaiya/keyd) | `f564288ac2b19d2305a5b39023c474805ff8fce5`，2026-06-01，`2.6.0` | MIT/X | 精简 C 守护进程、键盘状态机、设备级 grab |
| [uiohook-napi](https://github.com/SnosMe/uiohook-napi) | `44e0d868ac6fedd2a68c7f8ad8163c73a3f36fc3`，2026-03-21，npm `1.5.5` | 包声明 MIT；固定 libuiohook 声明 LGPL-3.0-or-later | Node 异步分发、发布包与跨平台观察 |
| [libuiohook](https://github.com/kwhat/libuiohook) | 子模块固定 `f259ff37e81125f6f91ebac5439e7cde1e78b296` | LGPL-3.0-or-later | Windows/macOS/X11 后端与消费边界 |
| [libuiohook evdev 实验](https://github.com/kwhat/libuiohook/tree/evdev) | `38bbd3a7857461c11d8973b3219f7292a54ba94e`，2026-07-27 | 随项目声明 | evdev grab + uinput 重放的反例 |
| [rdev](https://github.com/Narsil/rdev) | `b7e201bf80be7b9632207366f277d29fe732b9c1`，2026-05-12，`0.6.0` | MIT | Rust 同步消费回调、各平台 grab |
| [node-global-key-listener](https://github.com/LaunchMenu/node-global-key-listener) | `949d7c200fdb08b09d588a9d26720bb73ee7077c`，2024-07-19 | MIT | Node/原生辅助进程、30 ms 超时协议 |
| [Interception](https://github.com/oblitum/Interception) | `39eecbbc46a52e0402f783b872ef62b0254a896a`，2021-08-09 | 非商业 LGPL；商业使用另授权 | Windows 驱动级过滤、设备优先级 |
| [tauri global-hotkey](https://github.com/tauri-apps/global-hotkey) | `c0ee632d8dd4725f2c299cb010453590baa6ecec`，2026-10-19 | Apache-2.0/MIT | 注册型快捷键边界 |

提交日期是本次观察值，不用于判断维护状态。继续设计前应重新核对可能变化的平台行为和上游状态。

### 参考实现能力总表

| 项目 | 平台 | 监听 | 同步消费 | 修改/替换 | 设备级 | 主要部署代价 |
| --- | --- | --- | --- | --- | --- | --- |
| kanata | Windows、macOS、Linux | 是 | 是 | 通过输出层重映射 | Windows Interception、macOS IOHID/虚拟 HID 可设备级；默认 Hook 路径有限 | daemon、权限；macOS 驱动；Windows 可选驱动 |
| Karabiner-Elements | macOS | 是 | 是 | 是 | 是 | root 服务、DriverKit 扩展、签名和多项权限 |
| xremap | Linux | 是 | 是 | 通过 uinput 重映射 | 输入可按设备；输出合并为一个虚拟设备 | `/dev/input`、`/dev/uinput` 权限；桌面桥接 |
| keyd | Linux | 是 | 是 | 通过 uinput 重映射 | 键盘按 ID 分组 | root 守护进程、udev/设备权限 |
| uiohook-napi + libuiohook | Windows、macOS、X11 | 是 | Node API 不支持；底层 Windows/macOS 有路径 | 否 | 否 | 原生模块、预编译与许可证；Wayland 不完整 |
| rdev `unstable_grab` | Windows、macOS、Linux evdev | 是 | 是 | 消费后重放；不能原地修改 | Windows 无稳定设备身份；Linux 是 | macOS 权限；Linux 设备权限；回调线程 |
| node-global-key-listener | Windows、macOS、X11 | 是 | Windows/macOS 可同步请求阻止 | 否 | 否 | 辅助进程、30 ms 响应窗口；项目已 archive |
| Interception | Windows | 是 | 是 | 是 | 是 | 管理员安装内核驱动；商业许可和兼容成本 |
| Electron `globalShortcut` | Windows、macOS、Linux/X11；Wayland 走 Portal | 仅注册组合触发 | 非通用消费 | 否 | 否 | 最简单，但只有有限的 down 通知 |
| tauri global-hotkey | Windows、macOS、Linux X11 | 仅注册组合触发 | 非通用消费 | 否 | 否 | 需要平台事件循环；不覆盖 Wayland |

### 键盘与鼠标能力拆分

“消费”表示原始事件可在继续传给其他应用前被同步拦截，不表示项目一定提供 KeyMouse 所需的通用绑定 API。

| 参考实现 | 键盘监听/消费 | 鼠标按键与滚轮监听/消费 | 鼠标移动监听/消费 | 实际边界 |
| --- | --- | --- | --- | --- |
| kanata | 是/是 | 是/是 | 是/否 | Windows 只消费已映射的鼠标按键和滚轮；鼠标移动透传。macOS 可观察并改写拖拽事件，但不抑制光标移动。Linux 未识别的相对事件直接重放。 |
| Karabiner-Elements | 是/是 | 是/是 | 是/是 | 对已 seize 的 HID 键盘和指针设备可消费选中的指针移动、滚轮和按键；Apple 触控板、Secure Input 和权限场景不能视为完整覆盖。 |
| xremap | 是/是 | 是/是 | 是/是 | 必须启用 `--mouse`；只支持相对鼠标，触控板、数位板和其他绝对设备不支持；输出合并为一个虚拟设备。 |
| keyd | 是/是 | 是/是 | 是/是 | Linux only；底层处理相对/绝对移动、按键和滚轮，但产品定位仍是键盘工具，鼠标支持有限且会改变输出设备身份。 |
| libuiohook 原生接口 | 是/Windows、macOS 是；X11 否 | 是/Windows、macOS 是；X11 否 | 是/Windows、macOS 是；X11 否 | 原生 dispatcher 收到可变事件，设置 `event.reserved = 1` 可消费；XRecord 后端无法消费。 |
| uiohook-napi | 是/否 | 是/否 | 是/否 | 先把事件复制后异步投递到 JavaScript，原生回调不读取 JavaScript 决策，因此没有消费通道。 |
| rdev `unstable_grab` | 是/是 | 是/是 | 是/是 | Windows LL Hook、macOS CGEventTap、Linux evdev grab；Linux 不做完整帧恢复，绝对设备和触摸板语义不足。 |
| node-global-key-listener | Windows、macOS 是/是；X11 是/否 | Windows、macOS 是/是；X11 是/否 | 否/否 | 只处理鼠标按键，不处理移动和滚轮；辅助进程协议有约 30 ms 响应窗口。 |
| Interception | 是/是 | 是/是 | 是/是 | Windows only；驱动级设备过滤，支持相对/绝对移动、按键和滚轮，但部署、签名、兼容和商业许可成本高。 |
| Electron `globalShortcut` / tauri global-hotkey | 仅注册触发/非通用消费 | 否/否 | 否/否 | 没有完整原始事件流，也没有鼠标事件。 |

源码依据：

- kanata 的 Windows 鼠标回调把 `Move(..)` 和 `Other(..)` 转为 `Err(())` 并放行，只消费已映射的按键、滚轮；macOS 鼠标移动分支明确返回 `Keep`。
- Karabiner-Elements 的 `mouse_motion_and_wheel_to_key` 会“consume the entire selected group”，未选中的轴和按键仍透传，说明它具备按轴消费能力，而不是只能观察。
- xremap 的 `--mouse` 明确说明不支持触控板、数位板等绝对设备；相对移动事件可以映射，未映射时通过虚拟设备重放。
- libuiohook 的 Windows/macOS 原生收尾逻辑检查 `event.reserved` 并返回消费；uiohook-napi 在 dispatcher 中先 `memcpy`，再通过 `napi_tsfn_nonblocking` 异步发送，无法回写该标志。
- node-global-key-listener 只把鼠标按键映射为事件；Windows/macOS 可请求阻止，X11 Raw 事件只能观察。
- rdev 的 grab 回调在 Windows 返回 1、macOS 将事件类型设为 `Null`、Linux 不把未放行事件写回 uinput，三者都实现了“消费原事件”。
- Interception 的过滤器覆盖鼠标按键、滚轮和移动，并提供绝对/相对移动属性。

## 能做什么、短板与对自研的启示

### kanata

**能做什么**

- 跨 Windows、macOS、Linux 的软件键盘重映射器，提供多层、tap-hold、宏、Unicode、leader 序列、鼠标按键/滚轮和部分游戏手柄能力。
- 有独立事件循环和处理循环，配置可热重载，并可通过 TCP 服务器与外部程序交换消息。
- Windows 支持低级 Hook + `SendInput`，另有 Interception 驱动变体；macOS 使用 IOHID 捕获并依赖 Karabiner DriverKit 虚拟 HID；Linux 使用 evdev + uinput。

**强项**

- 真实复杂状态机样本：组合、超时、按住/轻触、前缀和输出调度都在原生侧完成。
- 明确区分“读取设备事件”和“生成输出事件”，不是把业务回调塞进 Hook。
- 平台差异被放在 `oskbd` 等适配层，核心层使用规范化事件推进状态。
- 文档积累了大量实际兼容性问题，适合转为 KeyMouse 的测试语料。

**短板**

- 是守护进程/应用，不是可嵌入 TypeScript/Node.js 与 Python 应用的精简 C++ 内核；进程模型、配置语言和运行要求不能直接照搬。
- Windows LLHOOK 路径无法在默认动作前拦截 `Win+L` 等系统组合，AltGr、NumLock、其他 LLHOOK 应用冲突和 OS 级重映射差异均有记录。
- Interception 路径要求管理员安装驱动，睡眠或反复插拔设备后可能输入失效；驱动维护、签名、安全软件和反作弊兼容风险高。
- macOS 要求 root、Input Monitoring/Accessibility、Karabiner DriverKit 和匹配的驱动协议；驱动版本、签名和系统扩展批准增加部署成本。
- Linux 源码对 `SYN_DROPPED` 仍明确写着“不清楚如何处理”；高速事件、重复、设备身份和虚拟输出与 libinput 行为的差异需要自行解决。
- 主项目为 LGPL-3.0-only，不能因为“只参考架构”就复制实现。

**对自研的启示**

- 采用“平台采集 → 规范化事件 → 单线程核心状态机 → 平台输出”的分层，但接口和实现自行设计。
- 配置热更新应替换不可变规则快照，不能在事件处理线程解析配置或等待 TypeScript/Python 回调。
- 平台适配必须暴露能力降级和故障状态，不能把“进程还活着”当成“Hook 仍有效”。

证据入口：[平台已知问题](https://github.com/jtroo/kanata/blob/44edba2/docs/platform-known-issues.adoc)、[macOS 安装与权限](https://github.com/jtroo/kanata/blob/44edba2/docs/setup-macos.md)、[Linux 输入循环](https://github.com/jtroo/kanata/blob/44edba2/src/oskbd/linux.rs#L502)。

### Karabiner-Elements

**能做什么**

- macOS 专用键鼠重映射器，支持复杂 manipulator、条件匹配、应用/输入源上下文、虚拟键鼠输出和事件查看。
- 特权 Core Service 使用 IOKit seize 指定设备，再通过 Karabiner DriverKit Virtual HID Device 发送结果；用户态 agent/server 负责应用上下文和外部动作。
- 可选 CGEventTap fallback，但默认优先使用设备级 HID 路径。

**强项**

- 设备级捕获能获得来源设备，也支持只修改选定设备。
- 对 Caps Lock、修饰键状态、Secure Input 前后状态清理和虚拟设备回环有深入处理。
- 特权输入处理与用户态动作执行分离，避免在设备事件线程启动外部进程。
- 对 macOS 权限、签名身份变化、daemon/agent 注册和恢复问题有明确的工程记录。

**短板**

- 仅支持 macOS，且依赖 root 特权服务、系统扩展、Input Monitoring、Accessibility 和多进程签名一致性。
- IOKit 无法捕获 Apple 触控板事件，需要额外 CGEventTap；而 CGEventTap 无法可靠提供来源设备。
- Secure Event Input 开启时 CGEventTap 收不到事件，可能造成修饰键和按下状态失步。
- `CGEventPost` 的 `fn` 等特殊键行为与真实硬件不同；虚拟 HID 重入事件也无法可靠携带来源标记，需要自行去重。
- 驱动、系统扩展和签名审批使普通 npm/Python 分发包的交付复杂度显著上升。

**对自研的启示**

- macOS 若要求“设备级选择性拦截、完整特殊键、Secure Input 期间仍可处理”，只做 CGEventTap 不够。
- 若首版只要求有限组合，应认真考虑降低承诺，而不是先引入虚拟 HID 驱动。
- 必须设计 Secure Input 前后的状态失效、强制释放和重同步，不允许沿用旧修饰键状态。

证据入口：[Karabiner-Elements 捕获、输出、权限与回环说明](https://github.com/pqrs-org/Karabiner-Elements/blob/caabc7a/DEVELOPMENT.md)。

### xremap

**能做什么**

- Linux 键重映射器，使用 evdev 读取、uinput 输出，因此不依赖 X11 协议，可跨 X11 和 Wayland。
- 支持按键/组合/序列映射、tap-hold、virtual modifier、模式、应用/窗口/设备过滤、命令触发、设备热插拔监听。
- 有 `--mouse` 选项、设备枚举、配置热重载和多种桌面环境的窗口上下文桥接。

**强项**

- 展示了“一个输入事件循环 + 一个输出虚拟设备 + 桌面上下文旁路”的完整 Linux 架构。
- 明确处理 `EVIOCGRAB` 失败、设备消失和 `EBUSY`，并在启动 grab 前等待已有按键释放。
- 对不同 Wayland 合成器分别提供窗口信息桥接，避免把桌面差异硬塞进 evdev 层。

**短板**

- 需要 `/dev/input/event*` 与 `/dev/uinput` 权限；不以 root 运行时，用户账号具备读取所有输入设备的能力，本身是可键盘记录的权限。
- `--mouse` 明确不支持触控板、数位板和其他绝对坐标设备。
- 所有被 grab 的设备合并为一个虚拟输出设备，设备身份被改变；trackball 特殊行为、打字时禁用触控板等依赖设备类型的系统功能可能失效。
- 应用窗口信息并非所有 Wayland 桌面都直接可得，需要 GNOME 扩展、KDE 桥接或其他桌面协议。
- 单一输出设备也让键盘布局、LED、设备配对和专用按键语义更难保持。

**对自研的启示**

- Linux 方案必须决定“每个物理设备对应一个虚拟输出”还是“合并输出”，并明确设备身份损失。
- 触摸板/数位板不能沿用传统鼠标的相对位移模型；要求支持时必须实现绝对坐标和多指协议。
- 窗口上下文必须作为可选旁路，不能成为事件消费线程的同步依赖。

证据入口：[README 的设备与 `--mouse` 限制](https://github.com/xremap/xremap/blob/a9877f8/README.md)、[设备选择、grab 与虚拟输出](https://github.com/xremap/xremap/blob/a9877f8/src/device.rs)、[故障排查](https://github.com/xremap/xremap/blob/a9877f8/doc/troubleshooting.md)。

### keyd

**能做什么**

- Linux 系统级 C 守护进程，使用 evdev/uinput，在 X11、Wayland 和虚拟终端中工作。
- 支持层、oneshot、hybrid modifier、key overloading、chord、宏、Unicode、设备特定配置和 IPC。
- 使用单个事件循环、`EVIOCGRAB`、inotify 热插拔和虚拟键盘输出。

**强项**

- 小而直接的 C 实现，目标是把输入处理保持在远低于 1 ms 的路径内。
- 对层、修饰键和 chord 状态有清晰设计，配置和运行时状态分离。
- 键盘设备可按 ID 分组，同一配置文件内可共享状态。
- 明确提供故障恢复入口：错误配置可能让键盘不可用，因此保留特殊退出序列。

**短板**

- 主要是键盘工具；鼠标支持标记为实验性，通配设备只匹配键盘，部分鼠标可能被误识别或被改动后影响指针。
- 创建虚拟输入设备会改变上层工具看到的设备身份，`setxkbmap`/`xset` 等状态在重启后可能丢失。
- 以 root 守护进程运行，配置错误可影响整个系统输入。
- README 明确说明它“不是用来编程每个 key up/down 事件”的工具，事件模型不适合直接承载 KeyMouse 的任意绑定 API。
- 不覆盖 Windows/macOS。

**对自研的启示**

- 原生核心应尽量小、状态明确、事件路径可预测；复杂业务和外部动作放到事件线程之外。
- 必须提供“输入失效时的安全退出/恢复”机制，不能只依赖进程正常退出。
- 设备热插拔和虚拟设备身份要与键盘布局/LED 同步一起设计。

证据入口：[README 的能力与鼠标限制](https://github.com/rvaiya/keyd/blob/f564288/README.md)、[设备 grab 与热插拔](https://github.com/rvaiya/keyd/blob/f564288/src/device.c)、[keyd 手册](https://github.com/rvaiya/keyd/blob/f564288/docs/keyd.scdoc)。

### uiohook-napi 与 libuiohook

**能做什么**

- 提供跨平台键鼠观察事件，并暴露 keydown/keyup、鼠标按键、移动、点击和滚轮。
- Windows/macOS 后端具备原生消费事件的实现基础；X11 后端使用 XRecord。

**短板**

- Node 层通过 `napi_call_threadsafe_function(..., napi_tsfn_nonblocking)` 异步接收副本，不能同步决定原始事件去留。
- libuiohook 1.2 的 macOS 路径存在主队列 `dispatch_sync_f` 与 Node/Electron 线程模型冲突的死锁风险。
- XRecord 只能观察，不能消费；包装层无法补出拦截能力。
- 实验性 evdev 分支在 `EV_SYN` 前逐条重放 `REL_X/REL_Y` 和滚轮，移动/滚轮消费实际无效，触摸板仍是 TODO。
- npm 包声明 MIT 但静态链接声明 LGPL-3.0-or-later 的 libuiohook；Linux `arm64`/`loong64` 预编译文件实际是 x86-64。

**对自研的启示**

- 任何语言回调都不能位于消费决策路径上；`uiohook-napi` 只是用 JavaScript 暴露了这一通病。
- 监听 API 的成功不能作为拦截能力证据。
- Linux 必须先完成帧聚合，再决定整帧放行或消费；逐条 `EV_REL` 决策会破坏鼠标语义。

证据入口：[Node 异步分发](https://github.com/SnosMe/uiohook-napi/blob/44e0d86/src/lib/addon.c)、[evdev 实验限制](https://github.com/kwhat/libuiohook/blob/38bbd3a/FIXME.md)、[XRecord 不可消费](https://github.com/kwhat/libuiohook/blob/f259ff3/src/x11/input_hook.c)。

### rdev

**能做什么**

- Rust 库，提供跨平台全局监听、模拟和 `unstable_grab`。
- `unstable_grab` 回调在平台事件线程同步执行；返回 `None` 消费，返回 `Some(event)` 放行。
- Windows 使用 `WH_KEYBOARD_LL` + `WH_MOUSE_LL`，macOS 使用 CGEventTap，Linux 使用 evdev grab + 每设备 uinput clone。

**强项**

- 同步消费 API 的形态比 Node 异步回调更接近 KeyMouse 所需边界。
- Linux “原设备 grab，未被消费的事件重放”模型可作为理解设备级路径的样本。
- 源码直接暴露了许多系统限制，便于建立反例。

**短板**

- 回调运行在系统 Hook/Event Tap 线程，业务耗时直接导致输入延迟；没有独立的实时规则匹配层。
- macOS 全局回调使用 `static mut`，源码注释明确写为 “Totally UB”；Event Tap 超时恢复和恢复后的状态一致性不完整。
- Linux 对每个事件立即回调并重放，没有按 `SYN_REPORT` 帧聚合；源码仍有 `SYN_DROPPED` TODO，不支持触摸板绝对事件和高分辨率滚轮语义。
- 只能消费/放行，不能原地修改事件；替换必须自行消费后重发。
- README 的 grab 平台声明与 Cargo feature 选择并不完全一致，默认 feature 组合不能直接当作跨平台 grab 保证。

**对自研的启示**

- 同步回调只适合短时间、无阻塞、无分配的规则判断。
- macOS Event Tap 超时和 Linux 帧丢失必须有显式状态恢复，不可只重建回调。
- 设备级 grab 的输出设备身份、同步帧和热插拔必须整体设计。

证据入口：[macOS grab 回调](https://github.com/Narsil/rdev/blob/b7e201b/src/macos/grab.rs)、[Linux grab 与帧处理](https://github.com/Narsil/rdev/blob/b7e201b/src/linux/x11/grab.rs)、[grab API 限制](https://github.com/Narsil/rdev/blob/b7e201b/README.md#grabbing-global-events-requires-unstable_grab-feature)。

### node-global-key-listener

**能做什么**

- Node 包启动独立原生辅助进程，通过 stdout/stdin 交换事件和是否阻止的响应。
- Windows 使用低级键盘/鼠标 Hook，macOS 使用 Swift CGEventTap，Linux X11 使用 XInput2 Raw 事件。
- Windows/macOS 给 JavaScript 约 30 ms 响应窗口，超时则放行，避免无限阻塞系统输入线程。

**短板**

- 项目已进入寻找维护者的 archive 状态，不能作为长期依赖或架构基础。
- X11 Raw 事件只能观察，不能消费，也不覆盖鼠标移动和滚轮。
- 跨进程同步协议增加编码、进程退出、背压、超时和部分响应风险；30 ms 仍远高于输入处理应占用的时间。
- 项目 README 记录了崩溃、修饰键失步、锁屏后按键卡住和 Electron 打包问题。

**对自研的启示**

- 系统回调必须有硬截止时间，超时默认放行并记录降级。
- 原生处理优先于跨进程语言回调；如果未来保留辅助进程，只能承载非决策路径。
- 事件 ID、响应排序和超时竞争必须有确定性测试。

证据入口：[Windows 30 ms 超时协议](https://github.com/LaunchMenu/node-global-key-listener/blob/949d7c2/src/bin/WinKeyServer/main.cpp)、[macOS 30 ms 超时协议](https://github.com/LaunchMenu/node-global-key-listener/blob/949d7c2/src/bin/MacKeyServer/main.swift)、[X11 Raw 事件](https://github.com/LaunchMenu/node-global-key-listener/blob/949d7c2/src/bin/X11KeyServer/main.cpp)。

### Interception

**能做什么**

- Windows 驱动级输入过滤，支持键盘、鼠标按键、滚轮和移动。
- 可按设备过滤、设置优先级、接收原始 stroke，并选择发送、修改或丢弃。
- 提供设备硬件 ID，适合需要稳定区分设备的场景。

**短板**

- 需要管理员安装内核驱动，源码基于 WDK 7.1，部署、签名、系统更新和安全软件兼容成本高。
- 非商业版为 LGPL 且对驱动/安装资产分发有条件，商业使用需要单独授权。
- 睡眠、反复插拔设备后可能输入失效；游戏、反作弊和远程桌面场景风险高。
- 不适合作为普通 npm/Python 包的默认能力。

**对自研的启示**

- 设备级过滤、设备 ID、优先级和显式 send/drop 模型值得借鉴，但不应把内核驱动作为首版默认路线。
- 驱动方案必须有独立于应用进程的恢复手段，否则一次故障会波及整台机器的输入。

证据入口：[许可证与安装说明](https://github.com/oblitum/Interception/blob/39eecbb/README.md)、[过滤、优先级与收发 API](https://github.com/oblitum/Interception/blob/39eecbb/library/interception.h)。

### 注册型方案

- [Electron `globalShortcut`](https://www.electronjs.org/docs/latest/api/global-shortcut) 只注册 accelerator 并接收按下触发；没有任意事件流、鼠标 Hook、原始 keyup 或逐事件消费。Wayland 路径依赖 GlobalShortcuts Portal。
- [tauri global-hotkey](https://github.com/tauri-apps/global-hotkey) 支持 Windows、macOS 和 Linux X11，接口是 hotkey pressed；不覆盖 Wayland，也没有通用鼠标事件流。
- 注册型方案还可能遇到快捷键被占用、用户拒绝 portal 授权和组合表达受限，必须返回明确错误。

注册型方案可以作为后续便捷接口或能力对照，但无法满足 KeyMouse 的完整监听、鼠标事件流和选择性拦截定位，不能替代自研输入内核。

## 平台原生机制对照

| 平台与机制 | 监听 | 同步消费 | 修改/替换 | 设备身份 | 主要限制 |
| --- | --- | --- | --- | --- | --- |
| Windows 低级键盘/鼠标 Hook | 是 | 是，Hook 返回非零 | 消费后重发；非原地修改 | 通常无法稳定获得物理设备身份 | 超过 `LowLevelHooksTimeout` 会绕过，Hook 可能被静默移除 |
| Windows Raw Input | 是 | 否 | 否 | 是 | 适合观察，不是系统级同步过滤器 |
| Windows `RegisterHotKey` | 指定组合触发 | 注册组合范围内 | 否 | 否 | 无完整事件流、鼠标流或 keyup |
| macOS CGEventTap | 是 | 是，回调返回 `NULL` | 可创建替代事件；非原地修改 | 否 | Secure Input、超时禁用、辅助功能/Input Monitoring |
| macOS IOHIDManager + seize | 是 | 是 | 需虚拟 HID/注入输出 | 是 | root/权限、驱动、特殊键和设备覆盖复杂 |
| macOS DriverKit Virtual HID | 输出机制 | 不单独负责捕获 | 是 | 可命名虚拟设备 | 签名、系统扩展、驱动协议和回环识别 |
| Linux X11 XRecord | 是 | 否 | 否 | 有事件来源信息但不等于稳定物理设备 API | 只能观察 |
| Linux X11 `XGrabKey`/`XGrabButton` | 预先注册组合 | 是 | 否 | 否 | 冲突、独占、Caps/Num Lock 修饰状态 |
| Linux XInput2 Raw | 是 | 否 | 否 | 有设备 ID | 观察路径，不是通用消费接口 |
| Linux evdev + uinput | 是 | 是 | 消费后重放/生成新事件 | 是，但输出身份需自行保留 | 设备权限、帧协议、热插拔、触摸板、输出设备身份 |
| Wayland GlobalShortcuts | 指定快捷键激活 | 由合成器定义 | 否 | 否 | 不是任意事件流或通用吞键 |
| Wayland InputCapture | 合成器授权后捕获 | 是，范围受限 | 取决于合成器 | 取决于协议 | 当前按指针屏障触发，不能按普通快捷键立即开始 |

关键结论：平台之间的能力不能用一个“全局快捷键支持”布尔值表示。KeyMouse 的能力查询至少要分别报告监听、注册、消费、替换、设备级、鼠标/触控板、权限和恢复状态。

## C++ 自研内核必须解决的工程问题

1. **专用事件线程**

   系统 Hook、Event Tap 或 evdev 读取线程只做长度有界的规范化、状态机推进和决策。禁止进入 TypeScript/Python 运行时，也禁止磁盘、网络、弹窗、日志 I/O 或用户输入进入消费路径。

2. **不可变规则快照**

   TypeScript 或 Python 绑定下发已经验证并编译好的规则快照；事件线程只读取当前快照。更新通过原子交换完成，旧快照延迟回收，不能在 Hook 回调里解析配置或加长锁。

3. **统一事件模型**

   事件至少携带时间戳、来源设备、平台扫描码与规范化键值、按下/松开/重复状态、当前修饰键、坐标或位移、同步帧 ID、注入来源和平台原始信息。平台扫描码与字符/布局解释必须分层。

4. **确定性的配对状态机**

   明确处理按下/松开配对、自动重复、左右修饰键、组合前缀、chord、tap-hold、oneshot、多个绑定竞争和状态超时。状态机必须可重放测试，不能依赖真实时间抖动。

5. **“已放行不可撤销”语义**

   例如 `A+B`：A 按下时还不知道 B 是否到来。若立即放行 A，之后无法撤回；若先消费 A，则 A 单独按下会被延迟，并需要超时后重放。首版必须对允许的组合形态作选择，不能宣称任意前缀都无延迟且可拦截。

6. **明确的决策结果**

   原生层至少区分 `Pass`、`Consume` 和未来的 `Replace`。`Consume` 后是否重放、重放事件是否再次进入匹配器、失败时如何回滚，都必须有单一定义。

7. **Linux 帧级一致性**

   事件按 `SYN_REPORT` 组成帧。`SYN_DROPPED` 表示用户态队列溢出：必须忽略到下一 `SYN_REPORT`，查询设备当前状态并重建按下/修饰键状态。[Linux 输入协议](https://www.kernel.org/doc/html/latest/input/event-codes.html)

8. **注入事件与回环识别**

   Windows 要识别 `SendInput` 注入标志；macOS 虚拟 HID 重入事件缺少可靠来源标记，需要跟踪已发送事件；Linux 要识别自己创建的 uinput 设备并避免重新 grab。去重不能误吞真实重复事件。

9. **生命周期监管**

   启动时探测权限和能力；运行中检测 Hook 失效、Event Tap 超时、设备消失、uinput 故障、休眠/唤醒、锁屏、会话切换和权限撤销。失败必须进入明确状态并尝试重建，不能静默降级为“仅监听”。

10. **有界通知与背压**

    原生事件到 TypeScript/Python 的业务通知使用有界队列。任一语言运行时慢、关闭或不可用时，只允许丢弃可安全丢弃的通知或合并计数，不能让原生事件线程阻塞。所有丢弃、合并和超时都应有可观测计数。

11. **设备身份与输出模型**

    决定是每个物理设备对应一个虚拟输出，还是合并为一个虚拟设备。合并会破坏设备类型、特殊按键、libinput 规则和“打字时禁用触控板”等行为；逐设备输出则增加设备数量、热插拔和生命周期复杂度。

12. **能力与错误模型**

    平台不支持、权限不足、被其他进程独占、Hook 超时、观察可用但消费不可用、输出不可用，必须是不同错误/状态；不能只返回成功或一个通用失败。

13. **统一语言绑定边界**

    两套语言绑定必须共享同一套事件、规则和错误语义。应先确定稳定 C ABI、直接 C++ API 或二者组合，并固定 opaque handle 所有权、回调线程、对象销毁、异常和 ABI 版本规则；不能先在 TypeScript 和 Python 中各自演化一套行为。

## 仍需产品决策

- 鼠标已纳入产品定位；首版需确定普通按键、滚轮、相对移动之外，是否覆盖高分辨率滚轮、触控板、多指手势和绝对坐标设备。
- 是否支持 keyup 触发、长按、tap-hold、组合前缀、多个普通键 chord、重复触发和左右修饰键区分。
- 是否要求替换按键或生成宏；还是首版只有匹配后触发动作，原始输入仍完整透传。
- 是否需要按前台应用、窗口、设备或用户上下文匹配；这些上下文来源在 Wayland 上尤其不统一。
- 各平台是否允许“只监听”和“可消费”能力不同；如果允许，API 和 UI 如何显式呈现。
- 语言绑定边界采用稳定 C ABI、直接 C++ API 或二者组合；opaque handle、所有权和错误码如何定义。
- Python 绑定采用 CPython C API、CPython 扩展封装库、CFFI 或其他方案；分发目标是源码构建、wheel 还是两者。
- 是否接受系统级安装、root/daemon、系统扩展、驱动或 udev 规则；还是坚持普通用户级 npm/Python 包安装。
- macOS 是否必须支持 Secure Input、Fn、Apple 触控板和设备级过滤；如果必须，需评估虚拟 HID 路线。

## 首轮验证矩阵

每条记录都必须包含系统/架构、内核提交、语言绑定及 Node/Electron/Python 版本、后端、权限状态、复现步骤、结果和限制。以下项目只定义未来验证，不代表已经执行。

| 平台 | 首轮重点 |
| --- | --- |
| Windows | LL Hook 超时与恢复、`Win+L`、AltGr、NumLock、注入事件、UIPI/管理员窗口、锁屏、RDP、快速重复、Hook 被其他软件影响 |
| macOS | CGEventTap 与 IOHID 边界、Secure Input、Input Monitoring/Accessibility 拒绝与撤销、Tap 超时、Caps Lock/Fn、Apple 触控板、虚拟 HID 回环、睡眠/唤醒、签名变化 |
| Linux X11 | XRecord 观察、Grab 冲突、修饰锁状态、evdev 权限、uinput 输出、热插拔、`SYN_DROPPED`、高分辨率滚轮 |
| Linux Wayland | GlobalShortcuts 授权/拒绝、InputCapture 实际触发条件、evdev/uinput 权限、绝对坐标触摸板、libinput 设备识别、不同合成器桥接 |
| TypeScript/Node.js | Node-API 加载/卸载、Worker Thread、进程退出与重新启动、打包签名、按 OS/arch 验证、权限提示与恢复 |
| Python | 导入/卸载、解释器状态、asyncio/线程通知、进程退出与重新启动、wheel 或源码包按 OS/arch 验证、权限提示与恢复 |

## 当前结论

1. KeyMouse 输入内核采用自研 C++ 实现，第三方项目只作为参考实现和测试语料。
2. 同步消费决策必须在原生层完成，TypeScript 与 Python 只负责配置和异步业务。
3. “可监听”“可注册”“可消费”“可替换”必须分别声明，不能用一个平台支持标记概括。
4. Linux evdev/uinput 是跨 X11/Wayland 的系统级路径，但代价是权限、设备身份、帧协议和恢复复杂度。
5. macOS 的 CGEventTap 不是完整设备级输入方案；若要求 Secure Input 或设备级能力，必须正视虚拟 HID 和特权服务成本。
6. Windows 低级 Hook 是合理的最小消费路径，但必须设计硬超时、Hook 失效恢复和系统组合边界。
7. 在首版语义确定前，不开始承诺平台支持，也不对外宣称 KeyMouse 已具备全局监听或拦截能力。
8. TypeScript/Node.js 与 Python 必须共享同一个 C++ 内核和同一套公共语义，绑定技术选型不能改变平台能力或拦截结果。

## 历史调研原文

> 以下保留 2026-10-17 原文及其当时判断。KeyMouse Issue #1 已于 2026-10-19 删除；文中的“Issue 保持 open”“回写本 Issue”等表述仅代表历史状态。所有“候选库”“复用 libuiohook”或“再决定是否重写”的结论均已被文首的 C++ 自研内核决策取代，不再是当前技术路线。

## 2026-10-17 调研记录：跨平台全局键盘、鼠标快捷能力

### 当前安排

本次仅保存调研、明确候选方向，暂不开发、不创建实现仓库、不发布包。Issue 保持 open，后续由用户决定何时继续。下述架构为建议，复用或重写尚未最终选定；本次没有完成三平台运行验证。

### 已明确的需求与定位

- 面向 Node.js / Electron 的开源原生扩展；应用在后台、没有焦点时仍可触发功能。
- 用户可以配置单键和组合键、一个或多个绑定；需要考虑全局键盘及鼠标 Hook，区分只监听与阻止原始输入继续传递的拦截。
- 候选技术路线为 C++ 核心 + Node-API；不是 C#。Windows/macOS/Linux 是目标平台，但 Linux 必须分别描述 X11 与 Wayland 能力。
- 单独修饰键、左右修饰键、键鼠组合、长按、松开触发、任意多普通键组合等属于待确认的详细范围，不因本次讨论自动全部列为首版承诺。
- Electron globalShortcut 适合标准快捷键注册，没有完整全局键鼠事件流、鼠标 Hook、keyup 或逐事件吞键/透传接口，不能覆盖本任务讨论的全部 Hook 能力。

### 历史：当时读取的第三方库

本次通过 gh 下载公开源码到临时目录阅读，核查接口、原生分发、三个平台后端、构建配置和补丁；未编译或运行 Hook，也未申请系统输入权限。以下是读取到的源码快照，不代表所有 npm 发布二进制均已验证。

| 项目 | 本次源码状态 | 定位与维护注意事项 |
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

### 历史：当时的复用还是自研讨论

- 当时的建议是只需监听并触发功能时优先用 uiohook-napi 验证需求，上层实现匹配；该建议已废弃。
- 当时的建议是 Windows/macOS 选择性拦截可复用 libuiohook 或自写后端；当前已确定全部由自研 C++ 内核实现。
- Linux X11 拦截：需要额外后端。Wayland 不应承诺与其他平台具有完全相同的任意监听/拦截能力。
- 建议自研的重点是 C++ 快捷键引擎、原生同步拦截规则、Node-API 和能力查询；暂不认定必须重写所有输入采集代码。
- 许可证也是选型因素：uiohook-napi 为 MIT，但 libuiohook 源码声明 LGPL-3.0-or-later，当前 binding.gyp 静态链接底层。不能把整体依赖链当成纯 MIT；最终复用与分发方式需明确许可证要求。[底层声明](https://github.com/kwhat/libuiohook/blob/2a2d40f/include/uiohook.h)

当时设想的架构是 TypeScript 配置/业务 → Node-API → C++ 匹配与拦截引擎 → 平台输入后端。其中“自研 C++ 输入内核”仍是当前决策；当前定位另增 Python 接口，绑定边界和 Python 实现方式见文首。

### 后续继续时的检查项

1. 确认首版按键范围、键鼠组合、吞键/透传、重复触发和按下/松开语义。
2. 明确序列与组合的前缀处理：例如 A+B 在 A 按下时尚不能知道 B 是否随后按下；需决定是否先放行、延迟或其他策略，不能事后撤销已传出的 A。
3. 对比原库复用、扩展绑定与自写精简后端的修改量、许可证和维护成本，再决定实现仓库。
4. 在目标系统实测键盘/鼠标事件、左右修饰键、布局和输入法、权限拒绝/撤销、高权限窗口、休眠/锁屏恢复、按下/松开配对及 Hook 失效恢复。
5. 验证 Node/Electron 版本及目标 CPU 架构的安装、预编译加载、启停/退出和高频鼠标事件；不以 CI 构建成功代替功能验证。
6. 对不支持的能力明确返回状态或错误，避免静默降级；完成后将证据回写本 Issue。
