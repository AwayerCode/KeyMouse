# KeyMouse Public Contract v0

Status: Design draft, 2026-10-19

This document defines the language-neutral behavior that every KeyMouse native
backend, C API implementation, and language binding must expose. It is a
design contract, not a statement that any capability is implemented or
verified.

The exact C declarations, allocator layout, package versions, and Python
binding technology are separate decisions. Where this document names data, it
names semantics rather than a frozen source-level structure.

Related documents:

- [Project charter](../project-charter.md)
- [Repository structure](../architecture/repository-structure.md)
- [Event model v0](event-model-v0.md)
- [ADR 0001: public native boundary](../decisions/0001-public-native-boundary.md)

## 1. Scope

KeyMouse is an embeddable native input library. Its public contract covers:

- global keyboard and mouse observation;
- native, rule-selected interception;
- shortcut activation derived from observed input;
- operating-system shortcut registration where a backend supports it;
- capability, permission, lifecycle, error, and recovery reporting;
- asynchronous, bounded notifications to language runtimes;
- equivalent semantics across TypeScript/Node.js and Python bindings.

A contract version identifies behavior, not implementation completeness.
Capability queries describe what the current platform and backend can do now.

## 2. Non-goals

Version 0 does not define:

- a GUI, configuration format, recorder, macro product, or automation service;
- synchronous interception decisions implemented in JavaScript or Python;
- event replacement, synthetic replay, macros, or arbitrary event mutation;
- multi-touch gesture recognition;
- access to secure desktops, Secure Input, protected processes, or every
  privileged window;
- application, window-title, clipboard, text, or IME-content capture;
- recording, persistence, telemetry, or upload of user input.

Unsupported behavior must not be implied by a successful operation. In
particular, observation never implies interception, and system shortcut
registration never implies access to a complete input stream.

## 3. Terms

- **Instance**: one opaque KeyMouse engine handle with independently owned
  configuration, state, rules, subscriptions, and statistics.
- **Backend**: the platform implementation that captures, classifies, and
  optionally suppresses native input.
- **Observation**: asynchronous notification of normalized input events without
  changing their destination.
- **Interception**: a synchronous native decision that passes or consumes an
  input event before it reaches the normal downstream consumer.
- **Registration**: an operating-system shortcut registration that produces an
  activation notification, normally without a complete raw event stream.
- **Capability**: one independently declared observation, interception,
  registration, device, or recovery ability.
- **Permission**: an operating-system or administrator-granted authorization
  required for a capability.
- **Batch**: the atomic, ordered unit of normalized events defined by the
  [event model](event-model-v0.md).
- **Rule snapshot**: an immutable, validated, ordered set of matching rules and
  dispositions. Replacing it is all-or-nothing.
- **Decision**: the `pass` or `consume` disposition assigned to a normalized
  input event.
- **Notification**: an asynchronous delivery from native code to a subscriber.
  Notifications never control the disposition of the event being reported.

The terms MUST, MUST NOT, SHOULD, SHOULD NOT, and MAY are normative.

## 4. Contract principles

1. Interception decisions MUST be made synchronously in native code before the
   platform's interception deadline. No JavaScript event loop, Python
   interpreter, GIL, IPC round trip, disk access, or network call may be on
   that decision path.
2. Observation callbacks MUST be asynchronous and MUST NOT be able to change an
   event that has already received a disposition.
3. A consumed event MUST NOT later be retroactively passed. A passed event MUST
   NOT later be retroactively consumed.
4. Capability, permission, runtime state, degradation, and error MUST be
   reported separately. A single boolean MUST NOT represent platform support.
5. All supported language bindings MUST expose the same contract values and
   behavior. Language-specific naming or asynchronous ergonomics may differ.
6. Requested capability failure MUST be explicit. KeyMouse MUST NOT silently
   replace a failed interception path with observation-only operation.
7. Events and rule snapshots MUST be immutable once published to subscribers or
   the event-processing path.
8. Native notification queues MUST be bounded. A slow language runtime MUST NOT
   stall input capture or interception.
9. KeyMouse MUST NOT persist or transmit input data unless a future,
   separately specified opt-in feature adds a bounded and reviewable data path.
10. A capability is not public support until it has platform evidence and
    contract tests. CI compilation alone is not platform evidence.

## 5. Public conceptual operations

Bindings may use language-idiomatic names and may combine calls, but the
following operations and their observable effects must remain available.

| Operation | Required semantics |
| --- | --- |
| Create instance | Return an opaque instance or a structured error. No native capture starts implicitly. |
| Destroy instance | Stop all activity, release native resources, and guarantee that no notification callback starts after destruction returns. |
| Probe capabilities | Return current capability records for the selected backend and platform. Probing does not request permission or start capture. |
| Inspect permissions | Return known permission records and which capabilities require them. |
| Request permission | Ask the platform to prompt or open its authorization surface, or report that programmatic request is unsupported. Returning from the call does not guarantee that permission was granted. |
| Replace rules | Validate and atomically publish a complete immutable rule snapshot. Reject the whole snapshot on any validation error. |
| Start | Attempt the explicitly requested channels and return the resulting per-channel status. |
| Stop | Stop accepting new input, release platform resources, and reach a terminal stopped state or return a structured stop failure. |
| Get status | Read the current lifecycle, channel, permission, active-rule, and last-error state. |
| Get statistics | Read monotonic counters for events, decisions, delivery, loss, and recovery. |
| Open subscription | Subscribe to event batches, activations, or status changes with a bounded delivery configuration. |
| Close subscription | Stop future deliveries for that subscription. Already copied data remains valid under the binding's ownership rules. |
| List devices | Return currently known device descriptors, subject to device capability and privacy constraints. |
| Register shortcut | Register a system shortcut through a backend when supported, independently from the raw interception contract. |

The contract does not require every language binding to expose a synchronous
native callback. In v0, interception is rule-driven. Arbitrary synchronous
per-event callbacks from TypeScript or Python are not part of the contract.

## 6. Instance model

- An instance is identified by an opaque handle. It is never represented as a
  raw C++ object, JavaScript object address, or Python object address across
  the native boundary.
- Different instances MUST NOT share mutable rule state, subscriptions,
  sequence numbers, or statistics.
- A process MAY create more than one instance only when the backend can keep
  their native capture domains independent or safely shared.
- If two instances contend for the same exclusive platform resource, the
  losing `start` operation MUST report `RESOURCE_BUSY` or an equivalent
  structured conflict. It MUST NOT silently join the other instance unless a
  future contract explicitly defines shared-instance semantics.
- Handles MAY be used from multiple threads unless a later ABI specification
  narrows that rule. Concurrent destruction requires the binding to ensure no
  other call is active.

## 7. Start request and channel status

`start` accepts an explicit request. At minimum, the request can select:

- keyboard and mouse observation by event class;
- rule-selected interception by event class;
- system shortcut registration entries;
- optional device filters when the `device.select` capability is ready;
- notification queue limits.

Each requested channel reports one of:

- `starting`;
- `active`;
- `degraded`;
- `failed`;
- `stopping`;
- `stopped`;
- `not_requested`.

Start completion MUST return the state of every requested channel. The overall
instance state is:

- `running` when every requested channel is active;
- `degraded` when at least one requested channel is active and at least one is
  degraded or failed;
- `failed` when no requested channel can become active;
- `stopped` only after an explicit stop or an unrecoverable shutdown that has
  completed resource release.

A missing permission, unavailable device, hook failure, or unsupported event
class MUST identify the affected channel and capability. It MUST NOT be
collapsed into an undifferentiated start failure.

## 8. Lifecycle

The observable lifecycle states are:

- `created`;
- `starting`;
- `running`;
- `degraded`;
- `stopping`;
- `stopped`;
- `failed`.

Required transitions:

| From | Operation or cause | To |
| --- | --- | --- |
| `created` | `start` | `starting` |
| `stopped` or `failed` | `start` | `starting` |
| `starting` | all requested channels active | `running` |
| `starting` | partial channel success | `degraded` |
| `starting` | no requested channel active | `failed` |
| `running` or `degraded` | tolerated channel failure | `degraded` |
| `running`, `degraded`, or `failed` | `stop` | `stopping` |
| `stopping` | native resources released | `stopped` |
| any running state | unrecoverable native failure | `degraded` or `failed` |

Rules:

- `start` while already `starting`, `running`, or `degraded` MUST return
  `INVALID_STATE` unless a later contract defines idempotent restart.
- `stop` on `created`, `stopped`, or `failed` MUST return `NOT_RUNNING`; it MUST
  NOT report a false teardown success.
- A transition to `failed` MUST preserve a structured last error.
- After `stop` reaches `stopped`, no new notification for the stopped channels
  may begin. Already queued notifications may be delivered before the final
  stopped status, or discarded according to the declared overflow policy.
- Destruction is terminal. The handle is invalid after `destroy` returns, even
  if the language binding keeps a wrapper object alive.

Dynamic failure includes hook removal, Event Tap disablement, permission
revocation, session changes, device loss, and backend reconstruction. A
backend MAY attempt recovery. During recovery it MUST report a non-active
channel state rather than pretending that capture is healthy.

## 9. Capability model

Capabilities are represented by stable ASCII IDs. Version 0 defines the
following semantic groups:

| Capability ID | Meaning |
| --- | --- |
| `observe.keyboard` | Receive normalized keyboard down, repeat, and up events globally. |
| `observe.mouse.buttons` | Receive normalized mouse-button down and up events globally. |
| `observe.mouse.relative_motion` | Receive relative pointer motion. |
| `observe.mouse.absolute_motion` | Receive absolute pointer position. |
| `observe.mouse.wheel` | Receive vertical or horizontal wheel movement. |
| `intercept.keyboard` | Apply synchronous pass/consume rules to keyboard events. |
| `intercept.mouse.buttons` | Apply synchronous pass/consume rules to mouse buttons. |
| `intercept.mouse.relative_motion` | Apply synchronous decisions to relative motion events. |
| `intercept.mouse.absolute_motion` | Apply synchronous decisions to absolute motion events. |
| `intercept.mouse.wheel` | Apply synchronous decisions to wheel events. |
| `register.system_shortcut` | Register an OS-level shortcut and receive activation. |
| `device.enumerate` | List input devices with a supported level of identity. |
| `device.select` | Limit observation or interception to a selected device set. |
| `device.source_identity` | Attach a stable-per-stream source device reference to events. |
| `recovery.state_reset` | Report that native input state was lost or resynchronized. |

A capability record contains:

- `id`;
- `status`: `ready`, `permission_required`, `temporarily_unavailable`,
  `unsupported`, or `unprobed`;
- `scope`: `system`, `session`, `device`, or `registered_only`;
- `required_permissions`;
- `constraints`: zero or more stable limitation IDs.

`ready` means the capability is available now under current permissions and
resources. It does not imply that a previous start operation succeeded.

Constraints include at least:

- `aggregate_source_only`;
- `no_device_identity`;
- `no_key_repeat`;
- `no_absolute_motion`;
- `no_high_resolution_wheel`;
- `system_reserved_events_excluded`;
- `requires_foreground_user_action`;
- `registration_only`;
- `state_recovery_required`.

These IDs are examples of the v0 vocabulary, not a guarantee that every
backend can report every distinction. A backend that cannot determine a
constraint MUST report that uncertainty in its platform documentation rather
than claiming the stronger behavior.

Rules:

- Bindings MUST expose the complete capability list, including unsupported
  entries.
- A caller MUST be able to determine whether interception is supported
  independently of observation.
- Mouse support MUST NOT be represented by one aggregate `mouse` capability.
- Device identity and device filtering MUST NOT be inferred from event capture.
- Capability results MAY change after permission, device, session, or backend
  changes. Callers MUST be able to re-probe and subscribe to status changes.

## 10. Permission model

A permission record contains:

- a stable permission ID;
- status: `unknown`, `not_required`, `promptable`, `denied`, `granted`,
  `revoked`, or `restricted`;
- whether KeyMouse can initiate a platform prompt;
- optional structured platform detail.

Rules:

- Permission records are platform-qualified. A generic `input` permission MUST
  NOT hide distinct OS permissions.
- `request_permission` may open a system UI and return before the user decides.
  A successful return means only that the request path was attempted.
- Permission grant and revocation MUST be observable through status changes or
  a fresh status query.
- Revocation during operation MUST move affected channels out of `active`.
- KeyMouse MUST NOT ask for administrator, accessibility, Input Monitoring,
  device, or system-extension access unless the requested capability can use
  it and the platform requires it.

## 11. Rules and decisions

### 11.1 Snapshot validity

A rule snapshot MUST be validated as a whole. Validation includes:

- unique rule IDs;
- supported trigger and context fields;
- valid physical or logical key domain;
- valid mouse button, wheel axis, and direction selectors;
- valid modifier mode;
- supported disposition;
- no dependency on an unavailable capability without an explicit validation
  error.

Rejected snapshots MUST leave the previous snapshot active.

### 11.2 Ordering and conflicts

- Rules are evaluated in the order supplied by the snapshot.
- The first matching rule that produces a terminal decision wins.
- No later rule may reclassify the same event.
- Rule IDs are application-defined, case-sensitive ASCII strings.
- If no rule matches, the default disposition is `pass`.
- A binding MUST NOT silently reorder rules by specificity, hash order, or
  language object iteration order.

### 11.3 Modifier and lock semantics

- Shortcut matching uses normalized modifier classes: `ctrl`, `shift`, `alt`,
  `meta`, and `altgr`.
- Rules select either an exact modifier set or a required-subset mode. The
  default for a chord helper is exact matching.
- Caps Lock, Num Lock, and Scroll Lock do not affect rule matching unless a
  rule explicitly includes them.
- Left and right modifier identity remains available in event data. A rule may
  require a side when its key domain supports it.
- Auto-repeat MUST NOT create a new key press and by default MUST NOT activate a
  new shortcut.

### 11.4 Decision ownership and key pairing

- A key or mouse-button press pair has one disposition that begins at `down`.
- `repeat` and `up` inherit the press disposition unless a future contract
  defines an independent release policy.
- This inheritance prevents an application from receiving an orphan release
  after KeyMouse consumed its matching press.
- Wheel and motion events are independent and receive one decision each.
- When a batch contains a coalesced motion sample, the decision applies to the
  complete normalized motion event.
- An orphan release has no press disposition to inherit. It defaults to `pass`
  and remains explicitly marked as an orphan in the event model.
- Rules that attempt to pass or consume a release independently are invalid in
  v0.

### 11.5 Prefixes, chords, and deadlines

Synchronous interception cannot both pass a first non-modifier key immediately
and later retract it if a second key turns the sequence into a chord.

Therefore v0 distinguishes:

- **immediate chords**, where all earlier non-modifier keys are intentionally
  consumed or are modifiers whose native state can remain active;
- **transparent deferred prefixes**, which consume a key temporarily and
  require replay or replacement to restore standalone behavior.

Immediate chords are part of the rule contract. Transparent deferred prefixes
are outside v0 and MUST NOT be advertised without a future replacement/replay
contract. A binding MUST NOT emulate them by blocking a hook callback or
waiting for a language runtime.

### 11.6 Snapshot replacement

- A successfully published snapshot receives a monotonically increasing
  `rule_generation`.
- Publishers may replace the snapshot while the instance is running.
- The active snapshot is latched at a batch boundary. A batch already being
  evaluated completes with the snapshot it started with.
- Held key and button pair dispositions survive snapshot replacement until the
  pair is released.
- A pending multi-event sequence from the old generation is cancelled when the
  new generation activates. Cancellation does not synthesize physical input.
- Callers can query the active generation. A snapshot publication result MUST
  not be described as applied until that generation is active.

### 11.7 Activation

An activation notification identifies:

- the `rule_id`;
- the triggering event's stream epoch and event sequence;
- the rule generation;
- the normalized timestamp;
- optional application-defined action metadata that contains no captured user
  content by default.

Activation delivery is asynchronous. A successful `consume` decision does not
wait for the action callback to finish.

## 12. System shortcut registration

System shortcut registration is a separate capability and API path.

- A registration entry has an application-defined ID, a normalized shortcut,
  and an activation target.
- Registration MAY fail because another process owns the shortcut.
- Registration MUST report when a platform consumes or reserves the shortcut
  differently from the requested behavior.
- Unregistering MUST remove future activations but cannot undo an activation
  already published.
- Registration MUST NOT be described as raw key observation or arbitrary
  interception.

## 13. Notifications and backpressure

### 13.1 Delivery classes

Version 0 defines three logical delivery classes:

- **event notifications**: immutable event batches from the event model;
- **activations**: rule or registered-shortcut activations;
- **status notifications**: lifecycle, capability, permission, device, and
  recovery changes.

Status is level-triggered: the current status is always queryable and a missed
status notification must not make the current state unknowable. Event and
activation notifications are at-most-once.

### 13.2 Delivery rules

- Native capture MUST NOT wait for a subscriber.
- Each subscription has a finite configured queue or equivalent bounded
  transport.
- Callbacks for one subscription are invoked serially.
- Library callbacks MUST NOT run on the platform's interception callback
  thread. A library-owned dispatcher or the binding's safe bridge delivers them
  asynchronously.
- Callback exceptions must be contained at the binding boundary. They must not
  unwind through C ABI frames or reach the native input path.
- Event batches are delivered atomically. A queue overflow MUST NOT deliver
  only part of a batch.
- The implementation MUST preserve relative order among notifications that are
  delivered.
- Subscriptions do not control event disposition in v0.

### 13.3 Overflow and loss

- Event-batch overflow SHOULD drop the oldest whole batches so newer input is
  observable.
- Every dropped batch MUST increase an overflow counter.
- The next delivered batch MUST be accompanied by a sequence-gap indication
  when a gap exists.
- Activation overflow MUST increment a separate counter. KeyMouse does not
  guarantee activation delivery while the consumer is persistently slower
  than the input source.
- Status notifications MAY be coalesced to the latest status. Coalescing MUST
  be counted.
- Exceeding a queue limit MUST NOT block, invoke user code, allocate without
  bound, or crash the input path.

### 13.4 Memory

Native event memory passed to a callback is immutable and borrowed for the
duration of that callback unless the ABI explicitly states otherwise. Language
bindings MUST copy or retain events under their own documented ownership rules
before returning control to native code.

## 14. Errors and results

Every failed public operation returns a structured error with:

- stable error code;
- category;
- human-readable message suitable for diagnostics but not program logic;
- retryability;
- affected capability or channel, when applicable;
- platform detail as structured fields, when available;
- optional underlying native error code and message.

The v0 stable code set includes:

| Code | Meaning |
| --- | --- |
| `INVALID_ARGUMENT` | A value or combination is malformed. |
| `INVALID_STATE` | The operation is not valid in the current lifecycle state. |
| `UNSUPPORTED` | The platform or backend cannot provide the requested capability. |
| `UNSUPPORTED_EVENT_CLASS` | A requested event class is not available. |
| `PERMISSION_REQUIRED` | Required permission has not been granted. |
| `PERMISSION_DENIED` | The platform reports a denied or restricted permission. |
| `RESOURCE_BUSY` | Another process or instance owns an exclusive resource. |
| `DEVICE_UNAVAILABLE` | A selected device is missing or unusable. |
| `BACKEND_FAILURE` | Native setup or operation failed. |
| `BACKEND_DEGRADED` | The backend remains usable only with reduced behavior. |
| `HOOK_DISABLED` | A platform hook or event tap stopped receiving events. |
| `STATE_RESET_REQUIRED` | Native input state was lost and must be resynchronized. |
| `QUEUE_OVERFLOW` | A bounded notification path discarded data. |
| `RULE_VALIDATION_FAILED` | A rule snapshot is invalid. |
| `ABI_MISMATCH` | Native and binding contract/ABI versions are incompatible. |
| `TIMEOUT` | A bounded native operation exceeded its deadline. |
| `NOT_RUNNING` | The requested operation requires an active instance. |
| `NOT_FOUND` | A referenced subscription, device, rule, or registration is absent. |
| `CANCELLED` | An operation was cancelled before completion. |
| `INTERNAL` | Unexpected invariant failure with no more specific public code. |

`QUEUE_OVERFLOW` is not a fatal start error; it is reported through counters,
status, or a stream-gap notification. A loss of interception integrity is
different and must move the affected channel out of `active`.

Bindings map codes to idiomatic errors while preserving the code and structured
fields. A generic exception type MAY wrap the error, but MUST NOT erase its
code or category.

## 15. Threading and reentrancy

- Input capture threads must perform only bounded normalization, state
  tracking, rule evaluation, and disposition.
- Platform SDK callbacks must not allocate unbounded memory, write logs, access
  networks, open dialogs, acquire the Python GIL, or enter the Node.js event
  loop.
- A subscriber callback must return promptly. It MUST NOT call `start`, `stop`,
  `destroy`, or another operation documented as blocking.
- Native callbacks into a language binding must occur only after safely
  entering that runtime's supported callback mechanism.
- Locking order and lifetime rules must be documented by the ABI
  implementation. No callback may occur while an internal lock is held.

## 16. Binding parity

TypeScript/Node.js and Python bindings share the following obligations:

- expose the same capability IDs, states, error codes, rule semantics, and
  event-model versions;
- preserve unknown enum values or surface them as explicit forward-compatible
  values rather than silently mapping them to a valid known action;
- use asynchronous delivery for events and activations;
- query native status rather than inferring it from callback presence;
- keep platform SDK, matching, pairing, and device-state logic out of the
  language layer;
- pass contract conformance tests using the same language-neutral fixtures;
- document any language-specific limitation without redefining native
  behavior.

Convenience APIs may encode a rule, but they MUST compile to the same snapshot
and decision semantics.

## 17. Versioning

Version 0 is a design contract and has no compatibility promise.

Starting with contract v1:

- the public contract uses Semantic Versioning;
- a major version changes observable behavior or removes/incompatibly changes
  a public value;
- minor versions add backward-compatible capabilities, records, or values;
- patch versions clarify behavior or fix implementation defects without
  changing the intended contract;
- the native ABI major version, contract major version, package version, and
  event-model version are reported separately;
- unknown additive enum values must remain representable at the C ABI;
- a binding that cannot understand a newer event or capability must fail
  explicitly or expose an unknown record, never reinterpret it as a supported
  action.

The event envelope and payload version are defined in the
[event model](event-model-v0.md). A future public C header must report enough
version and size information for bindings to reject incompatible layouts
before use.

## 18. Contract evidence

Before this contract can become v1, the repository needs:

- a language-neutral capability conformance suite;
- replay fixtures for keyboard, mouse, loss, and state-reset behavior;
- rule validation and conflict tests;
- lifecycle tests for unsupported, permission-denied, busy, degraded, stop,
  restart, and destruction behavior;
- queue overflow and sequence-gap tests proving that input capture does not
  block;
- at least one real backend per claimed platform capability;
- a published platform capability matrix with evidence links;
- one independent implementation of the C ABI consumer, through either a
  language binding or a C conformance harness.

## 19. Open decisions

- Exact C record layout, allocator, callback signature, and buffer ownership.
- Notification queue defaults and whether all delivery classes share one
  bounded transport.
- Minimum C and C++ language versions.
- Public rule matcher surface and convenience bindings.
- Python binding technology.
- Whether v1 includes direct C++ convenience wrappers over the C ABI.
- First concrete platform backend.
- Detailed wheel normalization and touchpad semantics beyond the event model.
