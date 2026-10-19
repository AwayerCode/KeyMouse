# KeyMouse Event Model v0

Status: Design draft, 2026-10-19

This document defines the normalized event model shared by the native core,
platform backends, C ABI consumers, TypeScript/Node.js, and Python. It
describes intended semantics only. No event kind or platform path in this
document is implemented or verified.

The event model is governed by the
[public contract v0](public-contract-v0.md). Related documents:

- [Project charter](../project-charter.md)
- [Repository structure](../architecture/repository-structure.md)
- [ADR 0001: public native boundary](../decisions/0001-public-native-boundary.md)

## 1. Goals

The model must:

- preserve the physical source and normalized meaning of an input without
  pretending they are the same thing;
- represent keyboard, mouse button, wheel, and pointer motion semantics across
  platforms without losing native identity;
- preserve ordering and expose loss;
- group platform input records into deterministic batches;
- support replay and conformance tests without real hardware;
- keep interception decisions separate from asynchronous observation;
- avoid capturing text, IME composition, window titles, or application data;
- remain extensible without silently reinterpreting unknown values.

## 2. Non-goals

Version 0 does not define:

- multi-touch contacts, gestures, force, or stylus pressure;
- text decoding or input-method composition;
- raw HID report streams;
- application or window context;
- event replacement, macros, or synthetic replay;
- a promise that native coordinate units are comparable across devices or
  operating systems.

If a platform exposes a touchpad as pointer motion, KeyMouse may report the
normalized pointer event and mark the device class as `touchpad`. That is not a
multi-touch event model.

## 3. Core invariants

1. Every normalized input event belongs to exactly one batch.
2. Event sequence numbers never decrease within one stream epoch.
3. A delivered batch is complete and internally ordered.
4. A queue drop discards whole batches and is visible through sequence gaps or
   loss counters.
5. Keyboard physical identity and semantic identity are separate fields.
6. Keyboard repeat is not a new press.
7. Key and mouse-button releases inherit the disposition of their press pair.
8. Platform-native codes are preserved where available but do not define
   cross-platform rule semantics.
9. Time is monotonic within a stream epoch. Wall-clock time is not required.
10. Native input is never silently rewritten into a different event.
11. State unknown after loss is represented as unknown, not guessed as
    released.
12. Event data is immutable once published.

## 4. Stream and sequence identity

Each successful start creates a new `stream_epoch`.

- `stream_epoch` is an opaque 128-bit or larger value that MUST differ between
  independent starts with high probability.
- The C ABI may expose it as a fixed byte array, two 64-bit integers, or an
  equivalent layout defined by the ABI. Bindings expose it as an opaque value.
- `(stream_epoch, event_seq)` uniquely identifies a normalized event within an
  instance.
- `event_seq` starts at 1 for each stream epoch and increments for every
  normalized event accepted by the core, including events that are later
  dropped from a notification queue.
- `batch_seq` starts at 1 for each stream epoch and increments for every
  accepted batch.
- Sequence exhaustion terminates the epoch and requires an explicit state
  reset. Wraparound without a new epoch is invalid.

`stream_epoch` is not a device serial, process identifier, installation
identifier, or stable cross-run identifier.

## 5. Event envelope

Every normalized input, device, or stream-control event has one immutable
envelope with the following semantics.

| Field | Semantics |
| --- | --- |
| `contract_version` | Public contract version used to interpret the record. |
| `event_model_version` | Event-model major version. Version 0 is draft. |
| `stream_epoch` | Opaque epoch identifier assigned at start. |
| `batch_seq` | Monotonic batch number within the epoch. |
| `event_seq` | Monotonic event number within the epoch. |
| `batch_index` | Zero-based position in the batch. |
| `batch_size` | Number of events in the complete batch. |
| `monotonic_ns` | Nondecreasing normalized timestamp. |
| `timestamp_quality` | How closely the timestamp represents source time. |
| `device` | Device reference and minimal classification. |
| `origin` | Hardware, injected, synthetic, or unknown source. |
| `modifiers_before` | Modifier and lock state immediately before the event. |
| `modifiers_after` | Modifier and lock state immediately after the event. |
| `state_confidence` | Confidence in pairing and modifier state. |
| `decision` | Native disposition and reason for input events. |
| `payload` | One typed event payload. |

The envelope MUST reject:

- `event_seq == 0`;
- `batch_seq == 0`;
- `batch_size == 0`;
- `batch_index >= batch_size`;
- mismatched batch metadata inside one batch;
- decreasing `monotonic_ns`;
- a decision on a non-input event;
- NaN or infinite numeric coordinates or deltas;
- an unknown enum represented as a known valid action without an explicit
  unknown/future variant.

## 6. Time

### 6.1 Canonical time

`monotonic_ns` is an unsigned 64-bit count of nanoseconds on a monotonic
timeline scoped to the stream epoch. Its zero point is unspecified; only
differences are meaningful.

If the platform timestamp is unavailable, non-monotonic, or in a different
clock domain, the core uses the capture time and lowers `timestamp_quality`.

### 6.2 Timestamp quality

| Value | Meaning |
| --- | --- |
| `source_exact` | The source timestamp was converted without loss to the canonical timeline. |
| `source_adjusted` | A source timestamp was rescaled, clamped, or adjusted for clock-domain consistency. |
| `capture_fallback` | No usable source timestamp was available; native capture time was used. |
| `derived` | The time was inferred for a synthesized control record. |

Wall-clock time, timezone, and calendar date are not part of v0 event
notifications.

## 7. Batches and frames

A batch is the smallest unit that the core publishes atomically after
normalization. It preserves the source order of semantic events inside one
native synchronization unit.

Backend mapping:

| Backend boundary | Batch boundary |
| --- | --- |
| Windows low-level hook callback | One callback is at least a one-event batch unless the backend can prove a safe larger boundary. |
| macOS Event Tap callback | One callback is at least a one-event batch; related records may be normalized together only when their order and deadline permit it. |
| Linux evdev | One `SYN_REPORT`-terminated frame is one batch. |
| X11 event | One delivered X event is a one-event batch unless a later backend contract defines a safe grouping. |
| Registered shortcut activation | Not an input batch; delivered through activation notification. |

Rules:

- The core MUST finish normalizing a complete batch before publishing it for
  observation.
- Decisions for one event MUST NOT depend on a future batch.
- A platform-required interception deadline may force a smaller batch or a
  one-event decision. The backend MUST expose that constraint rather than
  delaying past the native deadline.
- Relative motion samples from one evdev frame SHOULD be combined into one
  semantic motion event. The event records `coalesced_sample_count`; the raw
  samples are not exposed as separate public motion events.
- Wheel axes remain separate semantic events unless a future contract defines
  a vector wheel payload.
- A device or stream-control record may share a batch with input records when
  the source boundary requires it, but its ordering remains explicit.
- A stream-control record synthesized because of delivery loss or state reset
  MAY be emitted as a one-event control batch immediately before the next
  delivered source batch. It consumes normal `batch_seq` and `event_seq`
  values; it does not pretend to be a native device frame.

## 8. Modifier and lock state

`modifiers_before` and `modifiers_after` contain:

- physical modifier state for left and right `ctrl`, `shift`, `alt`, and
  `meta`;
- normalized semantic modifiers `ctrl`, `shift`, `alt`, `meta`, and `altgr`;
- lock state for Caps Lock, Num Lock, and Scroll Lock;
- `known_mask` describing which groups were observable from the backend.

Rules:

- Exact duplicate left/right modifiers are represented separately.
- `altgr` is semantic and may be backed by right Alt or another platform
  mechanism. Its native interpretation remains platform-specific.
- Lock keys do not change shortcut matching unless a rule explicitly includes
  them.
- When state is incomplete after startup, device loss, or native queue
  overflow, `state_confidence` is `partial` or `unknown`.
- The core MUST NOT assume an unobserved key is released merely because state
  tracking was reset.

For a key event, `modifiers_before` is the state used for matching. The
`modifiers_after` snapshot describes the post-transition state. For non-key
events, both snapshots are normally equal.

## 9. Device reference

Each event includes a device reference:

- `device_id`: opaque identifier stable within the stream epoch when the backend
  can provide it, otherwise the shared `unspecified` value;
- `class`: `keyboard`, `mouse`, `touchpad`, `touchscreen`, `tablet`, `remote`,
  `virtual`, or `unknown`;
- `is_virtual`: whether the backend positively identifies a virtual source;
- `identity_quality`: `device`, `aggregate`, `synthetic`, or `unknown`.

Rules:

- Device IDs MUST NOT contain a serial number, filesystem path, hardware
  address, or user name.
- A device ID is not stable across stream epochs unless a future opt-in device
  identity contract says otherwise.
- `aggregate` means the event source is known only as a class or session and
  not as a physical device.
- Device descriptors may contain vendor/product identifiers only if a future
  privacy review approves them. V0 does not require them.
- Detailed device records are delivered through device events and the device
  listing operation. An event's minimal reference is not proof of device-level
  selection support.

## 10. Origin and injection

`origin` is one of:

- `hardware`;
- `injected_external`;
- `injected_same_instance`;
- `synthetic`;
- `unknown`.

The core MUST use the strongest classification available from the platform.
It MUST NOT claim `hardware` when the source cannot be distinguished.

`injected_same_instance` is reserved for a future replacement/replay feature and
is not expected in v0. A backend that cannot distinguish external injection
uses `unknown` and documents the limitation.

## 11. Decisions

Input events carry a decision:

| Field | Meaning |
| --- | --- |
| `disposition` | `pass`, `consume`, or `not_applicable`. |
| `reason` | `default`, `rule`, `paired_press`, or `backend_policy`. |
| `rule_id` | Present when a rule produced the original press decision. |
| `rule_generation` | Snapshot generation inherited from that press decision. |

Rules:

- `pass` means the original event may continue to its normal downstream
  consumer.
- `consume` means the original event must not reach the normal downstream
  consumer.
- `not_applicable` is valid only when interception was not requested for that
  event class.
- A `consume` result that the backend cannot enforce is an integrity failure,
  not a successful decision.
- The decision is assigned before the event is published for asynchronous
  observation.
- Event notification is not a request for the subscriber to approve or change
  the decision.

## 12. Keyboard events

### 12.1 Event kinds

- `key_down`: a new physical press begins.
- `key_repeat`: the source reports an automatic repeat for the active press.
- `key_up`: the active press ends.

An observed duplicate `key_down` without an intervening `key_up` does not start
an indistinguishable second press. The new event receives a new `press_id` and
`pairing_status = duplicate_down`; the earlier pair is marked unresolved through
a stream-control state reset.

### 12.2 Keyboard payload

| Field | Semantics |
| --- | --- |
| `press_id` | Opaque identifier shared by a press, its repeats, and its release. |
| `pairing_status` | `normal`, `orphan_up`, `duplicate_down`, or `after_reset`. |
| `physical_key` | Canonical physical key identifier or `unidentified`. |
| `physical_key_domain` | `w3c_ui_events_code` or `native_only`. |
| `logical_key` | Optional normalized semantic key value for shortcut matching. |
| `logical_key_status` | `available`, `unavailable`, `ambiguous`, or `not_applicable`. |
| `is_repeat` | True only for `key_repeat`; kept as a redundant explicit flag. |
| `repeat_count` | Optional count starting at 1 for the first repeat after `key_down`. |
| `native` | Optional native scan code, virtual key, keycode, and layout reference. |
| `modifier_key` | Optional normalized role when the key is a modifier. |

### 12.3 Physical identity

When a canonical mapping is available, `physical_key` uses the ASCII value
names defined for the W3C UI Events `KeyboardEvent.code` attribute, for
example `KeyA`, `Digit1`, `ControlLeft`, or `ArrowUp`.

- The canonical domain identifies the physical key position independently of
  the active character layout.
- `Unidentified` is not a wildcard. It means no canonical physical key was
  established.
- Media, vendor, or unusual keys without a current canonical mapping use
  `physical_key_domain = native_only` and preserve native metadata.
- Rules using the canonical physical domain cannot match `native_only` events
  unless they explicitly select a platform-native extension in a future
  contract.

The complete accepted value list and its validation table are part of the
future C ABI contract.

### 12.4 Logical identity

`logical_key` is an optional, normalized semantic key symbol resolved from the
active keyboard layout. It is not free-form committed text.

- Standard control keys use stable ASCII identifiers such as `Enter`, `Escape`,
  `Tab`, `Backspace`, `Delete`, `Home`, and `ArrowLeft`.
- Printable keys use a single Unicode scalar where the platform and backend can
  establish one unambiguously.
- The field describes a key symbol, not the complete text produced by an input
  method or the complete Shift/AltGr text transformation.
- Text, dead-key composition, candidate windows, and IME output are not part of
  v0.
- If the backend cannot resolve the active layout, logical identity is
  unavailable. The core MUST NOT guess from a US-layout mapping.

Rules that require a logical key domain are invalid for a backend that cannot
provide it. A convenience binding MUST report this rather than silently
matching physical keys.

### 12.5 Native identity

`native` may contain:

- `platform`: Windows, macOS, X11, evdev, or another stable backend ID;
- `scan_code`;
- `virtual_key`;
- `native_keycode`;
- `layout_id`;
- `flags`.

These values are diagnostic and rule-extension inputs. They do not replace the
canonical fields. Raw platform event bytes are not part of v0.

## 13. Mouse button events

Event kinds:

- `mouse_button_down`;
- `mouse_button_up`.

Payload:

| Field | Semantics |
| --- | --- |
| `press_id` | Shared by the button press and release. |
| `pairing_status` | Same semantics as keyboard pairing. |
| `button` | `left`, `right`, `middle`, `back`, `forward`, `button_n`, or `unknown`. |
| `native_button` | Optional platform button number. |

Button releases inherit the disposition of their matching press. An orphan
release is explicitly marked, defaults to `pass`, and is never presented as a
normal completed pair.

## 14. Wheel events

Event kind: `wheel`.

Each event describes one axis. Positive directions are canonical:

- vertical positive means wheel up or away from the user;
- horizontal positive means right.

Payload:

| Field | Semantics |
| --- | --- |
| `axis` | `vertical` or `horizontal`. |
| `delta` | Signed normalized value in the declared unit. |
| `unit` | `detent_120`, `pixel`, `line`, or `native`. |
| `precision` | `discrete`, `high_resolution`, `estimated`, or `unknown`. |
| `phase` | `none`, `began`, `changed`, `ended`, `momentum`, or `unknown`. |
| `native_delta` | Optional source value before sign or unit conversion. |
| `native_unit` | Optional native unit identifier. |

Rules:

- Windows `WHEEL_DELTA = 120` maps naturally to `detent_120`.
- Linux high-resolution wheel values map to `detent_120` only when the backend
  can establish the device's declared relationship. Sign is normalized; the
  native value is preserved.
- Platforms that emit pixel or line deltas MUST NOT claim `detent_120`.
- Direction-based rules use the sign of `delta`. Exact-step rules are valid
  only when the declared unit and precision support the requested comparison.
- A wheel event is stateless and does not use press pairing.

## 15. Pointer motion events

### 15.1 Relative motion

Event kind: `pointer_motion_relative`.

Payload:

- `dx`: signed horizontal delta, positive right;
- `dy`: signed vertical delta, positive down;
- `unit`: `point`, `device_count`, or `native`;
- `coalesced_sample_count`: number of source samples represented by the event;
- optional native axis values.

Relative units are not guaranteed to be pixels, physical distances, or
comparable between devices. A backend MUST NOT convert device counts to pixels
without evidence from the platform.

### 15.2 Absolute motion

Event kind: `pointer_motion_absolute`.

Payload:

- `x` and `y`: signed finite coordinates;
- `space`: `screen`, `window`, `device`, `normalized`, or `native`;
- `unit`: `point`, `device_count`, `normalized_unit`, or `native`;
- optional `bounds_x`, `bounds_y`, `bounds_width`, and `bounds_height`;
- optional native axis values.

Coordinate origin is top-left when the platform coordinate space has a
top-left origin. If it does not, the backend must transform into the declared
space or report `native` semantics rather than silently flipping axes.

Absolute pointer events do not imply multi-touch or device-level absolute
capability.

## 16. Device events

Event kinds:

- `device_added`;
- `device_removed`;
- `device_changed`.

Payloads include a device descriptor with:

- opaque `device_id`;
- `class`;
- `is_virtual`;
- `identity_quality`;
- declared event classes;
- optional capability flags;
- change reason for removal or update.

Device events describe public input routing state only. They MUST NOT expose
device serial numbers, filesystem paths, MAC addresses, or user-identifying
properties.

## 17. Stream-control events

Stream-control events are part of the event stream, but not input events. They
do not carry interception decisions.

### 17.1 `stream_gap`

Used when an observation queue drops whole batches.

Payload:

- `first_missing_batch_seq`;
- `last_missing_batch_seq`;
- `missing_batch_count`;
- `reason`: `queue_overflow`, `transport_failure`, or `backend_loss`.

A stream gap is a notification record, not a claim that native input stopped.
Interception integrity is reported separately through status and errors.

### 17.2 `state_reset`

Used when native state tracking cannot be trusted.

Payload:

- `reason`: `syn_dropped`, `hook_restarted`, `event_tap_recovered`,
  `device_reconnected`, `session_changed`, `permission_changed`, or
  `backend_reset`;
- `affected_domains`: keyboard, mouse buttons, modifiers, pointer, wheel, or
  devices;
- `state_confidence_after`: `partial` or `unknown`;
- optional `resync_source`: `device_query`, `os_state`, or `none`.

After `state_reset`, the core MUST NOT reuse an unfinished `press_id` as if the
pair completed. New events are marked `after_reset` until enough state is
observed to restore confidence.

### 17.3 `state_resynchronized`

Emitted after a reset when the backend can establish a new baseline.

Payload:

- `state_confidence_after`;
- current modifier and lock snapshot;
- list or count of known held keys and buttons, if the platform exposes them;
- optional source detail.

The core does not fabricate hardware-like `key_up` events for keys it can no
longer observe.

## 18. Pairing

- A successful new physical press gets a nonzero opaque `press_id`.
- Repeats and the release reuse that `press_id`.
- Presses are scoped by `stream_epoch`.
- If state is reset, unfinished press pairs become unresolved.
- Duplicate downs and orphan ups are explicit anomalies.
- Event pairing is a core responsibility and cannot be implemented differently
  in TypeScript and Python bindings.

## 19. Delivery

- A subscription receives complete event batches. The transport must preserve
  batch boundaries and internal `batch_index` order.
- No delivered event is duplicated by the transport.
- A dropped whole batch is not delivered later out of order.
- A sequence gap is surfaced before or with the next delivered batch.
- Motion coalescing happens during normalization, before public batch
  publication; it is not an asynchronous queue substitution.
- Consumers that require a gapless history must use a future lossless or
  elevated-privilege transport, not reinterpret the bounded default stream.

## 20. Examples

### 20.1 Ctrl+C decision

Context:

- `ControlLeft` down was passed in an earlier batch.
- The active rule consumes `KeyC` while `ctrl` is down.
- A physical `key_repeat` and `key_up` later occur.

Expected semantics:

- `ControlLeft` press and release remain passed.
- The `KeyC` down event is consumed with `reason = rule`.
- The `KeyC` repeat and release inherit `consume` with
  `reason = paired_press`.
- No asynchronous observation callback may change those dispositions.

### 20.2 Linux relative-motion frame

Source records:

- `REL_X +12`;
- `REL_Y -3`;
- `SYN_REPORT`.

Expected normalized batch:

- one `pointer_motion_relative` event with `dx = +12`, `dy = -3`,
  `coalesced_sample_count = 2`;
- the batch ends before the next `SYN_REPORT` frame.

No separate public X and Y events are required.

### 20.3 Native queue loss

If the notification queue drops batches 40 through 42:

- native processing continues;
- the next delivered batch follows a `stream_gap` with
  `first_missing_batch_seq = 40`;
- overflow counters increase;
- interception decisions are not retroactively changed.

## 21. Forward compatibility

- Payload kinds and enum values are versioned.
- Unknown additive fields MUST be skippable through the future ABI layout
  rules.
- A binding that encounters an unknown payload must expose an explicit unknown
  event or a typed unsupported-event error. It MUST NOT coerce it into a known
  key, button, wheel, or motion event.
- New event kinds cannot silently alter the meaning of existing decisions.

## 22. Event-model evidence

Before this event model becomes stable, tests must cover:

- keyboard press, repeat, release, duplicate down, and orphan up;
- left/right modifiers and layout-dependent logical identity;
- mouse button pairing;
- vertical/horizontal wheel sign and unit handling;
- high-resolution wheel behavior;
- relative and absolute motion units;
- Linux frame aggregation and `SYN_DROPPED`;
- event-tap or hook restart with state reset;
- notification queue overflow without blocked input;
- deterministic replay of the same fixture through C ABI and both bindings.

## 23. Open decisions

- Exact canonical physical-key value table and platform mappings.
- How much logical-key resolution is required in the first backend.
- Whether mouse-button chords require explicit release policies later.
- Public representation of high-resolution wheel precision and phase.
- Absolute-coordinate normalization per platform.
- Whether touchpad contacts and gestures become a separate event model or stay
  out of scope.
