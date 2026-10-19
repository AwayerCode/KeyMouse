# KeyMouse Repository Structure

Status: Design draft, 2026-10-19

This document defines the target repository layout and dependency direction. It
does not create implementation directories. A directory should be added only
when it contains a real file, contract, test, or build target.

Related documents:

- [Public contract v0](../contracts/public-contract-v0.md)
- [Event model v0](../contracts/event-model-v0.md)
- [ADR 0001: public native boundary](../decisions/0001-public-native-boundary.md)

## Goals

- Keep the C++ core, platform backends, and language bindings independently
  testable.
- Prevent Node.js and Python details from leaking into the native input path.
- Keep the public C ABI separate from internal C++ APIs.
- Keep platform-specific code identifiable and replaceable.
- Support deterministic replay tests without real input hardware.
- Keep documentation and contract versions reviewable in the same repository.

## Target Layout

```text
/
|-- CMakeLists.txt
|-- README.md
|-- LICENSE
|-- LICENSE-MIT
|-- LICENSE-APACHE-2.0
|-- NOTICE
|-- cmake/
|-- include/
|   `-- keymouse/
|       |-- keymouse.h
|       `-- keymouse_abi.h
|-- core/
|   |-- CMakeLists.txt
|   |-- include/keymouse/core/
|   |-- src/
|   `-- tests/
|-- platforms/
|   |-- api/
|   |-- windows/
|   |-- macos/
|   `-- linux/
|       |-- x11/
|       |-- wayland/
|       |-- evdev/
|       `-- uinput/
|-- bindings/
|   |-- node/
|   `-- python/
|-- tests/
|   |-- replay/
|   |-- conformance/
|   |-- integration/
|   `-- fixtures/
|-- examples/
|-- benchmarks/
|-- tools/
|-- docs/
|   |-- architecture/
|   |-- contracts/
|   |-- decisions/
|   |-- platforms/
|   `-- project-charter.md
`-- .github/
```

The tree is a target, not a requirement to create empty directories now.

## Layer Rules

| Layer | May depend on | Must not depend on |
| --- | --- | --- |
| `include/keymouse` | C ABI types and forward declarations only | C++ internals, OS SDKs, Node-API, Python |
| `core` | C++ standard library, platform interface | OS-specific headers, language runtimes |
| `platforms/api` | C++ standard library | `core`, concrete platform SDKs, bindings |
| `platforms/windows` | `platforms/api`, Windows SDK | Node-API, Python, unrelated platforms |
| `platforms/macos` | `platforms/api`, macOS SDKs | Node-API, Python, unrelated platforms |
| `platforms/linux` | `platforms/api`, Linux/X11/evdev APIs | Node-API, Python, unrelated platforms |
| `bindings/node` | public C ABI, Node-API | C++ core internals, OS SDKs |
| `bindings/python` | public C ABI, Python binding support | C++ core internals, OS SDKs |
| tests and tools | Any layer required by the test | Production-only shortcuts that hide behavior |

Concrete platform implementations are selected by composition and build
configuration. The core must not include a concrete backend header directly.

## Component Responsibilities

### `include/keymouse`

Contains the installable public headers:

- ABI version and feature queries.
- Opaque handle declarations.
- Error, capability, state, event, and rule records exposed across the ABI.
- No C++ classes, STL types, exceptions, or platform SDK types.

This stable C ABI is the only native boundary used by language bindings, as
proposed in [ADR 0001](../decisions/0001-public-native-boundary.md). The exact C
header and record layout remain a follow-up contract task.

### `core`

Contains platform-neutral behavior:

- Event normalization and sequencing.
- Rule validation, immutable snapshots, and deterministic matching.
- Keyboard and mouse state tracking.
- Lifecycle and error state machines.
- Bounded notification queues and statistics.
- Backpressure and event-drop accounting.

The core owns all interception decisions.

### `platforms/api`

Defines the internal contract between the core and concrete platform backends:

- Backend capability discovery.
- Start and stop operations.
- Event ingestion and normalized event callbacks.
- Permission status and permission change notifications.
- Hook failure, input reset, and device lifecycle notifications.
- Synchronous `Pass` / `Consume` result returned to the backend.

This interface is C++ internal and is not part of the public ABI.

### `platforms/windows`, `platforms/macos`, `platforms/linux`

Contain only platform integration, event decoding, permission handling, and
backend-specific recovery. They translate into the platform API and do not
implement public rule semantics independently.

Linux backends remain separate where their constraints differ:

- X11 event capture and grabs.
- Wayland portals and compositor integration.
- evdev frame parsing and device access.
- uinput synthesis, if and when replacement/replay is introduced.

### `bindings/node` and `bindings/python`

Bindings own:

- Native package build and loading.
- Conversion between language objects and the public C ABI.
- Async event delivery on the language runtime's thread.
- Lifecycle and garbage-collection integration.
- Idiomatic errors, types, and examples.

Bindings do not duplicate matching, state tracking, platform selection, or
interception decisions.

## Tests

- `core/tests`: unit tests for core-owned state and matching.
- `tests/replay`: language-neutral recorded event sequences and expected
  decisions/events.
- `tests/conformance`: one contract suite executed against every language
  binding.
- `tests/integration`: real platform tests that may require permissions or
  physical devices.
- `tests/fixtures`: sanitized fixtures only; no personal keystrokes, window
  titles, application content, or device serial numbers.

Unit tests must not require a specific operating system. Real platform tests
must record OS version, architecture, runtime version, permission state, and
known limitations.

## Documentation

- `docs/contracts`: normative public behavior and versioned event models.
- `docs/architecture`: internal boundaries and component design.
- `docs/decisions`: ADRs for choices that affect public behavior or
  compatibility.
- `docs/platforms`: per-platform permissions, capability evidence, and recovery
  behavior.
- `docs/project-charter.md`: highest-level project goal and stage gates.

Draft documents must include a status and date. Accepted contracts are
versioned; a changed public meaning requires a new contract version.

Current design set:

- [Public contract v0](../contracts/public-contract-v0.md): lifecycle,
  capabilities, permissions, rules, decisions, notifications, errors, and
  binding parity.
- [Event model v0](../contracts/event-model-v0.md): streams, batches, keyboard
  and mouse payloads, device references, state reset, and delivery semantics.
- [ADR 0001](../decisions/0001-public-native-boundary.md): stable C ABI as the
  public native boundary.

## Build Boundaries

The proposed build uses CMake and produces logical targets equivalent to:

- `keymouse_core`: internal platform-neutral core.
- `keymouse_platform_<id>`: one target per concrete backend.
- `keymouse`: public C ABI library composed with the selected backend.
- Node and Python packages: language artifacts that consume the public ABI.

Whether the public C ABI ships as a shared library, static library, or bundled
native artifact is still an open packaging decision.

## Naming

- Directories use lowercase names with hyphens only in documentation folders.
- C ABI symbols use the `km_` prefix.
- Internal C++ namespaces use `keymouse`.
- CMake targets use `keymouse_` or `keymouse_platform_` prefixes.
- Stable error codes use uppercase ASCII identifiers.
- Rule IDs are application-defined, case-sensitive ASCII strings.

## Creation Order

Implementation should begin in this order:

1. Review and accept the public contract and event model.
2. Public C ABI header and contract version constants.
3. Contract record types and validation tests.
4. Platform API.
5. Core event pipeline and replay harness.
6. One concrete platform backend.
7. One language binding and conformance tests.

Creating empty scaffold directories before these steps does not provide useful
evidence and is intentionally avoided.

## Open Decisions

- Minimum C and C++ language versions.
- Shared, static, or dual public C ABI packaging.
- Detailed C record layout, callback signature, and allocator rules.
- Python binding technology.
- First concrete platform backend.
- Whether benchmarks ship in the main repository or a separate evidence set.
