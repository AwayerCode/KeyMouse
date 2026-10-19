# ADR 0001: Use a Stable C ABI as the Public Native Boundary

Status: Proposed, 2026-10-19

## Context

KeyMouse needs a self-authored C++ core that serves TypeScript/Node.js and
Python without duplicating input behavior. The project also expects prebuilt
native packages, multiple compilers, several operating systems, and independent
language runtimes.

Exposing internal C++ classes directly would couple bindings to compiler ABI,
standard-library ABI, exception behavior, object layout, and symbol visibility.
Those constraints would make independent packaging and long-term compatibility
unnecessarily fragile.

The repository structure draft already places installable headers under
`include/keymouse` and prohibits bindings from depending on C++ internals.

## Decision

The public, installable native boundary is a versioned C ABI.

1. Language bindings depend only on the public C ABI and its public headers.
2. The C ABI exposes opaque handles and plain C-compatible records.
3. C++ classes, STL containers, exceptions, references, and templates do not
   cross the library boundary.
4. Platform SDK types do not cross the public ABI.
5. The C++ core remains the implementation and may use an internal idiomatic
   C++ API that is not part of the installed compatibility surface.
6. TypeScript/Node.js uses Node-API to adapt the C ABI.
7. Python uses a separately decided binding technology to adapt the same C ABI.
8. A C++ convenience wrapper MAY be added after the C ABI exists, but it must
   not become a second behavioral contract.

The ABI must eventually define and test:

- ABI and contract version reporting;
- opaque instance, subscription, and registration handle lifetimes;
- record sizes or equivalent extensibility metadata;
- UTF-8 and string-length rules;
- caller-owned versus library-owned memory;
- event-buffer lifetime;
- callback signatures and serialization guarantees;
- error retrieval and thread ownership;
- creation, start, stop, rule replacement, and destruction ordering;
- symbol visibility and calling convention on supported platforms.

The conceptual operations and semantics are defined by
[Public Contract v0](../contracts/public-contract-v0.md). The event records are
defined by [Event Model v0](../contracts/event-model-v0.md).

## Consequences

Positive:

- Node.js and Python can be packaged independently of the C++ compiler's class
  layout.
- ABI compatibility can be tested directly by a C harness.
- Internal C++ refactoring is possible without breaking language bindings.
- Third-party C or C++ applications can embed the same verified boundary.
- The public surface is small enough for one conformance suite.

Negative:

- Every binding needs explicit type, ownership, and callback adaptation.
- The project must design and maintain ABI versioning from the start.
- Performance-sensitive paths need measured call and copy costs.
- An additional conversion layer exists between the C++ core and bindings.
- The exact record layout remains a blocking implementation decision.

## Rejected alternatives

### Expose the C++ API directly

Rejected because it would make independent prebuilt packages depend on compiler
and standard-library ABI, and would make clean error and exception isolation
harder.

### Give each language binding its own native facade

Rejected because platform behavior, rules, and event semantics could diverge.

### Require a helper process for language access

Rejected for the core decision path because IPC latency and process failure
would violate the synchronous interception contract. A helper process may be
considered only for optional privileged or diagnostic paths.

## Follow-up

- Write the public C header and ABI layout ADR.
- Define and test ABI/version mismatch behavior.
- Add a C conformance harness before the first language binding.
- Measure event-buffer copying and callback dispatch on each target platform.
