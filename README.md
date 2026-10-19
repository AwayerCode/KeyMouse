# KeyMouse

Cross-platform system-global keyboard and mouse event monitoring and selective interception, built on a self-authored C++ core and exposed to TypeScript and Python.

KeyMouse 是一个以自研 C++ 输入内核为基础的跨平台系统级键鼠事件监听与选择性拦截库，对外提供 TypeScript/Node.js 和 Python 语言接口。快捷键绑定与动作触发是构建在输入内核之上的高层能力，不是项目唯一的产品边界。

## 项目状态

项目处于需求、API 和技术方案确认阶段。已完成一轮参考实现与平台机制调研，但尚未实现输入内核、语言绑定或平台后端，也没有完成任何目标平台的键鼠功能验证或发布。

本文描述项目定位和计划验证的方向，不代表已交付能力。

- [调研记录、源码快照与验证矩阵](docs/research.md)
- [全球化开源项目标准与仓库建设清单](docs/open-source-strategy.md)
- [贡献指南](CONTRIBUTING.md)
- [安全策略](SECURITY.md)
- [治理与维护者](GOVERNANCE.md)
- [Agent 协作规则](AGENTS.md)

## 项目定位

KeyMouse 的目标是成为全球化、达到顶尖开源水平的系统级输入基础设施，而不是只服务单一应用、单一语言社区或单一操作系统的快捷键工具。

- **全球化**：公共文档以英文为规范版本并维护中文翻译；项目名称、包名、平台支持和权限说明在所有市场保持一致。
- **顶尖开源水平**：通过行为测试、安全与隐私设计、可审计发布、版本兼容、长期支持、开放治理和真实平台证据来证明，而不是通过功能数量或宣传语定义。
- **当前阶段**：pre-alpha。上述内容是目标和验收标准，不代表 KeyMouse 已达到顶尖水平或可用于生产环境。

## 核心定位

KeyMouse 的核心是一个可被应用程序嵌入的系统级输入库：

- 在应用失去焦点或在后台运行时监听键盘和鼠标事件。
- 在原生层按预先注册的规则进行同步匹配，选择性消费命中的事件。
- 通过 TypeScript/Node.js 和 Python 提供一致的控制、配置与通知接口。
- 在 Windows、macOS、Linux X11 和 Linux Wayland 上分别声明能力、权限和限制。
- 将快捷键、组合前缀、长按和动作触发建立在同一事件模型与状态机之上。

“系统全局”指应用进程之外的输入会话范围，不表示能够覆盖锁屏、安全桌面、受保护输入或所有特权窗口。具体范围必须在每个平台实测后声明。

## 能力分层

以下能力必须分别设计、分别声明，不能用一个“全局快捷键”标签混同：

- **全局监听**：收到键盘或鼠标事件，但原事件仍继续传递。
- **系统快捷键注册**：向操作系统注册指定组合，主要得到“快捷键被触发”的通知；通常不是完整原始事件流。
- **指定规则拦截**：原生层按预先注册的规则同步匹配，只消费命中的事件。
- **任意事件消费**：每个事件都能在原生层同步决定放行或消费。这是最强约束，不能等待 TypeScript、Python 或其他语言运行时返回。
- **事件替换/重放**：消费原事件后生成新输入。该能力涉及顺序、回环识别、设备身份和失败恢复，首版不默认包含。

产品定位包含键盘和鼠标，但鼠标能力仍需按事件类型拆分声明。普通按键、滚轮、相对移动、高分辨率滚轮、绝对坐标设备、触控板和多指手势不能被一个“支持鼠标”标记概括。首版具体覆盖范围仍待确定。

## 架构方向

KeyMouse 不把现成输入库作为内核，也不以其包装层作为产品核心。目标结构：

```text
TypeScript / Node.js -> Node-API adapter -----+
                                              +--> native binding boundary
Python --------------> Python binding adapter -+             |
                                                              v
                                                self-authored C++ input kernel
                                                              |
                                                              v
                                                     platform backends
```

两套语言绑定必须共享同一个内核，不能各自维护事件解析、规则匹配或平台后端。绑定边界采用稳定 C ABI、C++ API 还是两者组合尚未定案；选型时必须处理版本兼容、内存所有权、异常转换、线程模型和独立分发。

### C++ 输入内核

自研内核负责：

- 平台事件采集、规范化与统一事件模型。
- 设备状态、Linux 输入帧状态和按下/松开配对。
- 修饰键、组合前缀、chord、长按和重复触发状态机。
- 不可变规则快照、冲突处理和同步 `Pass` / `Consume` 决策。
- 启动、停止、热插拔、Hook/Event Tap 失效、休眠和锁屏恢复。
- 平台能力、权限、降级状态和结构化错误。
- 面向语言绑定的有界异步通知与可观测背压计数。

### TypeScript 与 Python 接口

语言层只负责语言习惯、类型转换、对象生命周期和非决策型业务逻辑：

- 下发已经校验的不可变规则快照。
- 启停内核并查询平台能力、权限和运行状态。
- 订阅监听事件，接收异步业务通知。
- 将结构化错误和降级状态映射为各语言的原生错误。

同步拦截不得依赖任一语言的回调返回值。系统事件线程不得进入 Node.js 事件循环或获取 Python GIL；语言运行时变慢时，只能按明确策略丢弃或合并可安全丢弃的通知，不能阻塞原生输入路径。

TypeScript/Node.js 计划使用 Node-API。Python 绑定技术尚未确定，不以当前文档中的候选方案视为已选型。

## 平台边界

下表是计划继续验证的原生机制，不是 KeyMouse 的实测支持声明，也不是对第三方项目的依赖选择。

| 平台 | 全局原始事件监听 | 选择性拦截 | 系统快捷键注册 | 主要边界 |
| --- | --- | --- | --- | --- |
| Windows | 低级键盘/鼠标 Hook | 低级 Hook 返回消费 | `RegisterHotKey` | Hook 超时会绕过并可能被静默移除；高权限窗口、安全桌面和系统组合需单独验证 |
| macOS | CGEventTap；设备级路径需 IOHID | CGEventTap；完整设备级能力需虚拟 HID | `RegisterEventHotKey` | 权限、签名、Secure Input、Tap 超时、Apple 触控板、虚拟设备回环 |
| Linux X11 | XRecord 或 XInput2 Raw | 预先 Grab 的组合；全事件流需 evdev/uinput | `XGrabKey` / `XGrabButton` | Grab 冲突、修饰锁状态、设备权限、输出设备身份 |
| Linux Wayland | 无通用全局原始事件流接口 | evdev/uinput 系统级路径；合成器协议范围有限 | GlobalShortcuts Portal | 合成器边界、用户授权、设备权限、帧同步、触控板和热插拔 |

监听、注册、选择性拦截和事件替换必须分别返回能力状态。平台不支持、权限不足、被其他进程独占和运行中失效不能表现为同一个通用错误，也不能静默降级。

## 参考实现的作用

外部项目只用于回答“原生机制能做什么”和“哪些故障必须提前设计”，不作为 KeyMouse 的依赖或产品核心：

- `uiohook-napi` / `libuiohook` 展示异步语言通知与同步消费的边界，以及 XRecord 不可消费、macOS 线程和 evdev 帧处理问题。
- `rdev` / `Interception` 展示同步消费和 Windows 设备级过滤，同时暴露 `unstable_grab`、驱动部署、许可和恢复成本。
- kanata / Karabiner-Elements 展示复杂原生状态机、独立事件循环、设备级捕获和虚拟 HID 的工程代价。
- xremap / keyd 展示 Linux evdev/uinput、设备热插拔、虚拟设备身份和 `SYN_DROPPED` 恢复问题。

详细能力矩阵、源码快照和故障模式见 [docs/research.md](docs/research.md)。

## 下一步

1. 完成项目名称、商标、npm/PyPI 包名和域名核验，并确定最终品牌；开源许可证与贡献者授权方式已经确定。
2. 固定语言无关的公共契约：事件模型、规则快照、能力查询、启停状态、通知背压和错误语义。
3. 决定语言绑定访问内核的 native 边界：稳定 C ABI、C++ API 或两者组合，并定义所有权与线程约束。
4. 建立可重放事件序列的 C++ 内核测试骨架，再接入任何平台 Hook 或语言绑定。
5. 用最小原生实验分别验证 Windows、macOS、X11 和 Wayland 的监听、消费、权限与恢复行为。
6. 分别建立 Node-API 与 Python 绑定的构建、打包、安装和版本兼容验证。
7. 在首版语义与平台证据确定后，再建立 npm/Python 包发布入口和对外支持矩阵。

## 开源与许可证

KeyMouse 已确定采用 `MIT OR Apache-2.0` 双许可证，使用者可以选择其中任一许可证。完整条款见：

- [LICENSE](LICENSE)：双许可证说明与 SPDX 标识
- [LICENSE-MIT](LICENSE-MIT)
- [LICENSE-APACHE-2.0](LICENSE-APACHE-2.0)
- [NOTICE](NOTICE)

外部贡献默认以同一 SPDX 表达式提交，并要求每个非合并提交包含 DCO sign-off；当前不要求 CLA。自研内核减少了第三方输入库的链接与重分发问题，但不自动解决以下事项：参考实现的代码不能直接复制；平台 SDK、驱动的虚拟 HID、预编译工具和安装器仍有各自许可证与分发条件。若未来引用、链接或分发任何第三方组件，需单独完成许可证评估。

## 社区、安全与治理

- [贡献指南](CONTRIBUTING.md)
- [行为准则](CODE_OF_CONDUCT.md)
- [安全策略](SECURITY.md)
- [支持范围](SUPPORT.md)
- [治理规则](GOVERNANCE.md)
- [维护者](MAINTAINERS.md)
- [变更记录](CHANGELOG.md)
- [GitHub 仓库安全设置清单](docs/repository-settings.md)

项目当前采用明确的单维护者/BDFL 模式，并在 v1.0 前至少增加一名独立维护者。安全漏洞必须通过 GitHub Private Vulnerability Reporting 私下报告，不得提交到公开 Issue。仓库级标准和建议见 [docs/open-source-strategy.md](docs/open-source-strategy.md)。
