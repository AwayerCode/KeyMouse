# KeyMouse 全球化开源项目标准

## 目的

本页把“全球化、顶尖开源水平”从宣传语转换为仓库可以验证的标准。它讨论项目身份、README、许可证、文档站、社区文件、治理、安全、发布和国际化，不改变 KeyMouse 的 C++ 输入内核与 TypeScript/Python 双语言接口定位。

当前仓库仍是 pre-alpha，只有需求与调研，没有实现或运行验证。“全球化、顶尖开源水平”是项目目标，不是当前状态，也不能在发布材料中提前宣称。

调研日期：2026-10-19。外部状态在公开发布前必须重新核对。

## 什么算全球化与顶尖

**全球化**不等于只写英文 README，而是：

- 包名、品牌、文档和示例在主要市场都可发现、可理解、无地域假设。
- 英文是公共文档的规范来源，其他语言有明确维护方式。
- Windows、macOS、Linux X11 和 Wayland 的能力按事实分别声明。
- 键盘布局、输入法、时区和语言环境进入测试矩阵。
- 社区沟通异步、透明、可搜索，并对不同背景的贡献者可参与。

**顶尖**不等于 Star 数或功能宣传，而是以下证据的总和：

- 行为定义清楚，关键路径有单元、重放、压力、模糊和真实平台测试。
- 权限、隐私、安全披露、供应链和发布产物可审计。
- 安装、升级、弃用、版本和平台支持有稳定政策。
- README 能在几分钟内回答“是什么、是否适合我、能否使用、风险是什么”。
- API 参考、平台指南、故障恢复和迁移文档可版本化检索。
- 决策、维护者、贡献流程和利益冲突公开，不依赖个人记忆。

## 必须先解决的命名问题

当前名称存在明显搜索与品牌冲突：

- `keymouse.com` 已是一个使用 `KeyMouse®` 标识的键盘/鼠标硬件及软件产品。
- PyPI 的 [`keymouse`](https://pypi.org/project/keymouse/) 已被另一个 Python 键鼠模块占用；最后版本为 2024-04-14 的 `0.0.6`。
- 公开 npm 查询在 2026-10-19 对 `keymouse` 返回 404，但这些数据变化快，不构成名称保留或商标可用结论。
- GitHub 上存在多个 KeyMouse、KeymouseGo、KeyMouseHook 等相近项目。
- `keymouse.dev`、`keymouse.io`、`keymouse.org` 在本次 DNS 查询中没有解析结果；这不等于域名可注册，更不等于商标可用。

因此，在公开发布 npm/PyPI 包、注册域名或投入品牌设计前，必须先完成：

1. 名称和商标的独立法律核验。
2. npm、PyPI、GitHub Organization、主要域名和社交账号的一致性核验。
3. 决定继续使用 KeyMouse 还是选择全球更独特的项目名。
4. 决定 npm scope、PyPI 项目名和 Python import name，避免三个平台各用不同品牌。

在名称未确定前，不应把当前的 “KeyMouse” 视为可安全全球推广的最终品牌。仓库名可以暂时保留，但包名、域名和 logo 不应先行投入。

## README

### 语言策略

- 公开预览前，根 `README.md` 应使用英文，作为规范版本。
- 中文版使用 `README.zh-CN.md`，通过 BCP 47 语言标签命名，并在两个版本之间互链。
- 英文和中文版本必须同步更新；不能让翻译版长期落后却仍标为当前文档。
- 代码、测试名、公开 API 名、错误码、提交信息和公开 Issue 默认使用英文。
- 内部研究文档可以继续使用中文，但对外发布前要提炼为英文规范文档。

### 推荐结构

1. 一句话定位和明确的目标用户。
2. 当前状态：pre-alpha / experimental / beta / stable，不能用 “production-ready” 代替证据。
3. 3–5 个最重要的真实能力；未实现能力不得出现。
4. 平台与事件类型支持矩阵，分别标注监听、拦截、设备和权限。
5. TypeScript/Node.js 与 Python 的安装方式。
6. 各自一个最小、可运行、经过 CI 检查的示例。
7. 监听与拦截的关键区别，说明规则在原生层同步匹配。
8. macOS、Windows、Linux 权限和安全警告。
9. 架构概览、版本兼容和 native ABI 说明。
10. 文档站、示例、迁移、贡献、安全披露和许可证入口。

### 展示规则

- 徽章只链接真实 CI、包页面、文档站、许可证和安全状态；不要添加装饰性或失效徽章。
- README 是电梯陈述和入口，不复制完整 API 参考。
- 示例必须与当前版本同步，并由文档测试验证。
- 不使用 “blazing fast”“best”“top-tier” 等未经基准或外部评价支持的形容词。
- 输入监听涉及隐私，必须在首屏明确说明默认不记录、不上传键鼠内容。
- 如果项目仍不可用，状态和不可用范围要放在徽章之后，而不是藏在末尾。

### GitHub 仓库元数据

- About 描述保持一句话，明确“C++ core”“keyboard/mouse”“TypeScript/Python bindings”和当前阶段。
- Topics 使用可搜索且稳定的词：`keyboard`、`mouse`、`input`、`global-hook`、`input-interception`、`cpp`、`node-api`、`python`、`electron`、`windows`、`macos`、`linux`、`wayland`。
- Website 字段在文档站上线前留空或指向仓库内文档，不指向未上线的营销站。
- Social preview 和 Logo 在名称、商标核验完成后再设计。
- Issue 标签至少覆盖平台、绑定语言、类型（bug/feature/security）、状态和 good first issue。
- 在公开接受贡献前确认 MFA、组织权限、私有漏洞报告和仓库转移/继任方案。

## 开源许可证

### 已采用方案

项目所有者已确认采用 `MIT OR Apache-2.0` 双许可证。选择该组合的原因：

- MIT 简单、生态兼容面广，降低 Electron、Python 和 C++ 用户的理解成本。
- Apache-2.0 提供明确的专利授权和专利反制条款，更适合被企业基础设施采用。
- Tauri 等项目采用 MIT/Apache-2.0 双许可证，说明该组合在跨平台原生应用生态可行。

本项目不采用 GPL/LGPL 作为首版许可证，以降低原生库、Node 扩展和 Python wheel 在链接、修改与分发解释上的采用成本。该决策不是法律意见；正式发布前仍需复核依赖许可证、平台 SDK 和分发方式。

### 对应文件

- `LICENSE`
- `LICENSE-MIT`
- `LICENSE-APACHE-2.0`
- `NOTICE`：项目版权、第三方组件和特殊归属。
- `CONTRIBUTING.md`：明确贡献以哪个 SPDX 表达式提交。
- 包清单：Node 使用 `"license": "MIT OR Apache-2.0"`；Python wheel/sdist 元数据使用对应 SPDX expression。
- 如未来采用文件级例外或第三方素材，增加 `REUSE.toml` 或 `LICENSES/`，避免许可证信息散落。

文档、图片、Logo 和商标不自动等于代码许可证的一部分。若允许复用文档，需单独声明文档许可证；Logo 和项目名称应通过独立的商标政策管理。

### 贡献者授权

- 默认使用 DCO sign-off，要求每个提交表明贡献者有权提交该代码。
- 不默认引入 CLA。只有计划未来闭源再授权、商业双许可或重新许可时才需要评估 CLA。
- 任何参考实现的代码都不能因为“架构相似”而直接复制；当前调研项目的许可证不自动成为 KeyMouse 的许可证。

## 是否需要官网

结论：

- **pre-alpha 不需要官网。** 一个只有宣传页、没有可安装版本和真实文档的“官网”会降低可信度。
- **首个公开 alpha 前需要文档站入口。** 可以先用 GitHub Pages，网站内容以安装、能力矩阵、API、权限和安全为主。
- **v1.0 前需要正式文档站。** 应支持版本选择、全文搜索、英文规范文档、中文翻译、API 参考、迁移指南和平台故障排查。
- **营销官网不是优先级。** 下载页、示例和文档才是库项目的“官网”核心；独立品牌宣传站可以等到有稳定用户与生态后再做。

工具可以在 API 稳定后选择，避免现在锁死：

- Docusaurus：版本化、国际化、SEO 和 React 生态较强。
- VitePress：Markdown 优先、轻量，适合以文字和代码示例为主的文档。
- Sphinx/MkDocs：Python 生态成熟；Sphinx 更适合 C++/Python API 文档与交叉引用。
- Doxygen：生成 C/C++ API 参考，通常作为文档站的一部分，而不是完整站点方案。

建议先用仓库内 Markdown 维持唯一事实来源，再在公开发布前选择静态站点生成器。不要让官网内容与仓库文档分叉。

## 仓库结构

推荐采用 monorepo，直到接口和发布节奏稳定：

```text
/
  README.md
  README.zh-CN.md
  LICENSE-MIT
  LICENSE-APACHE-2.0
  NOTICE
  CONTRIBUTING.md
  CODE_OF_CONDUCT.md
  SECURITY.md
  GOVERNANCE.md
  MAINTAINERS.md
  CHANGELOG.md
  SUPPORT.md
  .github/
    CODEOWNERS
    ISSUE_TEMPLATE/
    pull_request_template.md
    dependabot.yml
    workflows/
  core/
  bindings/
    node/
    python/
  platforms/
    windows/
    macos/
    linux/
  docs/
  examples/
  tests/
  benchmarks/
  tools/
```

不必在第一天创建所有空目录。真正开始实现时再建立结构，避免用空的“仪式文件”制造成熟度错觉。

### 当前最低文件集

在公开接受外部贡献前应具备：

- `README.md`
- 明确的 `LICENSE*`
- `CONTRIBUTING.md`
- `CODE_OF_CONDUCT.md`
- `SECURITY.md`
- `.github/ISSUE_TEMPLATE/`：至少区分 bug、功能请求和安全问题。
- `.github/pull_request_template.md`
- `.github/CODEOWNERS`
- `CHANGELOG.md`

`GOVERNANCE.md`、`MAINTAINERS.md` 和 `SUPPORT.md` 可以在出现第二个维护者或首次正式发布前补齐。单独的 `ROADMAP.md` 可选，除非它能维持更新频率；否则用 milestones 和 Issues 更诚实。

## 社区与治理

- 早期使用明确的 BDFL/主维护者模式，不伪装成基金会治理。
- 在 `GOVERNANCE.md` 中定义维护者权限、决策方式、平台后端批准条件、冲突处理和继任规则。
- 在 `MAINTAINERS.md` 中列出角色、负责领域和权限范围。
- `CODEOWNERS` 对平台后端、发布流水线、安全策略等敏感目录要求对应 owner。
- Code of Conduct 已采用 Contributor Covenant 2.1；当前临时指向所有者 GitHub
  主页公布的私密联系方式，正式招募外部贡献者前仍需建立专用私密举报渠道。
- Issue 表单应要求 OS/架构、Node/Electron/Python 版本、后端、权限状态、复现步骤、预期/实际行为和日志。
- 不要在社区规模不足时创建空的 Discord、论坛或多个聊天渠道；优先使用 Discussions/Issues，保证可搜索和可维护。
- 设计决策使用 ADR 或 RFC 记录，尤其是事件语义、native ABI、平台降级、许可证和发布政策。

## 安全与供应链

输入监听库直接接触用户的键盘和鼠标，安全与隐私是品牌成立的前提。

- `SECURITY.md` 提供 GitHub Private Vulnerability Reporting，不把漏洞引导到公开 Issue。
- 默认不记录键值、鼠标轨迹、窗口标题或应用内容；任何诊断/遥测必须显式选择并说明数据范围。
- 建立 threat model：权限提升、Hook 注入、驱动签名、IPC、配置反序列化、规则绕过、日志泄露、更新劫持。
- 为 Linux evdev 解析、平台事件解码和规则格式增加模糊测试。
- 在 C++ 核心启用 sanitizers、静态分析和可复现的本地测试入口。
- Dependabot/Renovate、secret scanning、push protection、CodeQL 和最小权限 Actions 在首个工作流建立时启用。
- GitHub Actions 固定到不可变 commit SHA，避免不受信任的 `pull_request_target`、脚本注入和过宽 token。
- 启用主分支保护：PR、CI 状态检查、评审、禁止强推和删除；管理员绕过策略也要有记录。
- 使用 OpenSSF Scorecard 跟踪仓库安全健康度，但把高风险检查视为工程问题，不把分数当作品质证明。

## 发布与版本

- 对 C++ 内核、Node 包和 Python 包使用 Semantic Versioning。
- native ABI 需要独立版本号；语言包版本不能单独代表 ABI 兼容性。
- `CHANGELOG.md` 按 Keep a Changelog 记录新增、变更、弃用、移除、修复和安全问题。
- 发布必须从同一个受保护提交和 CI 构建，不允许从开发者本机直接上传预编译产物。
- npm 使用 Trusted Publishing + provenance；PyPI 使用 Trusted Publishing，减少长期 API token。
- GitHub Release 提供校验和、签名/签名清单、构建来源证明和 SBOM。
- 为每个平台/架构建立预编译矩阵，并在发布说明中列出已验证和未验证组合。
- 明确支持窗口：哪些版本继续获得安全修复、何时 EOL、ABI 何时破坏。
- 包发布前验证 npm/PyPI 名称、许可证元数据、维护者账号 MFA 和仓库来源关联。

## 国际化与文档质量

- 英文是规范文档；中文是正式维护的翻译，不是一次性宣传稿。
- 公开 API 错误码使用稳定英文标识，展示文案由语言包映射，不把自然语言当逻辑判断。
- 平台指南覆盖键盘布局、输入法、Caps Lock/Num Lock、Secure Input、Wayland 权限等区域差异。
- 文档示例按版本测试；旧版本文档通过站点版本选择保留。
- 官网和文档需要基础可访问性、移动端可读性和无脚本降级路径。
- 版本、包名和文档链接在 README、GitHub About、npm/PyPI 元数据中保持一致。

## 成熟度门槛

| 阶段 | 必须具备 | 仍不宣称 |
| --- | --- | --- |
| 当前 pre-alpha | 明确定位、功能边界、调研记录、命名/许可证决策、基础安全策略 | 已可用、production-ready、全球化顶尖 |
| 首个公开 alpha | 英文根 README + 中文版、安装与权限文档、支持矩阵、CI、Issue/PR 模板、DCO、包 provenance | 全平台完整支持、稳定 ABI、无已知严重问题 |
| 公开 beta | 文档站、SemVer/CHANGELOG、预编译矩阵、漏洞响应流程、平台实测报告、安全威胁模型 | 大规模生产可用、长期支持承诺 |
| v1.0 | 稳定公共契约、ABI 兼容策略、至少两个维护者/清晰治理、OSPS Baseline Level 2、签名与 SBOM、支持/EOL 政策、迁移指南 | 所有平台/设备等价、覆盖所有安全桌面和协议 |
| 顶尖项目目标 | OSPS Level 3 适用项、持续基准与平台回归、外部安全评审、公开治理和可验证发布、真实用户证据 | 由 Star 数或单次发布自动获得 |

OpenSSF OSPS Baseline 当前版本为 2026.08.28。其 Level 1 已要求 MFA、主分支保护、公开变更历史、许可证、安全联系人和贡献流程；Level 2 进一步要求自动化测试、评审、发布签名/校验和以及更完整的治理与安全文档。KeyMouse 应把 Level 1 作为公开贡献前的最低线，并把 Level 2 作为稳定发布目标。[OSPS Baseline](https://baseline.openssf.org/versions/2026-08-28)

## 需要项目所有者决定

1. 是否最终继续使用 KeyMouse；若继续，如何完成商标与包名差异化。
2. 是否允许未来商业双许可或闭源再授权；当前 DCO 决策以不再授权假设为前提，变更前必须重新评估。
3. 何时将仓库迁移到项目 Organization，并指定至少第二个管理员。
4. 根 README 何时切换为英文优先，以及中文翻译的维护责任。
5. 文档站启用时间和域名；建议公开 alpha 前先上 GitHub Pages，v1.0 前再正式化。
6. npm/PyPI/GitHub/域名/社交账号的最终统一命名方案。
7. 专用安全与行为准则私密联系渠道、漏洞响应时限和首个受信任发布身份。

## 参考依据

- [GitHub：关于 README](https://docs.github.com/en/repositories/managing-your-repositorys-settings-and-features/customizing-your-repository/about-readmes)
- [GitHub：健康贡献与社区文件](https://docs.github.com/en/communities/setting-up-your-project-for-healthy-contributions)
- [GitHub：仓库最佳实践](https://docs.github.com/en/enterprise-cloud@latest/repositories/creating-and-managing-repositories/best-practices-for-repositories)
- [OpenSSF OSPS Baseline](https://baseline.openssf.org/versions/2026-08-28)
- [OpenSSF Scorecard](https://scorecard.dev/)
- [Choose a License：许可证比较](https://choosealicense.com/licenses/)
- [Apache License 2.0](https://www.apache.org/licenses/LICENSE-2.0.html)
- [npm Trusted Publishing](https://docs.npmjs.com/trusted-publishers/)
- [PyPI Trusted Publishing](https://docs.pypi.org/trusted-publishers/)
- [GitHub Artifact Attestations](https://docs.github.com/en/actions/how-tos/secure-your-work/use-artifact-attestations)
- [Semantic Versioning](https://semver.org/)
- [Keep a Changelog](https://keepachangelog.com/en/)
- [Tauri 仓库：MIT/Apache-2.0 与独立文档站示例](https://github.com/tauri-apps/tauri)
- [Electron 仓库：README 到独立文档站示例](https://github.com/electron/electron)
- [KeyMouse 商标使用示例](https://www.keymouse.com/)
- [PyPI：已存在的 keymouse 包](https://pypi.org/project/keymouse/)
