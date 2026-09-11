# Containers, Human Input, triggers, and Agent nodes

These nodes are structurally sensitive. Do not author them from a node payload alone.

## Iteration

An Iteration requires:

- an array input selector;
- an iteration container node;
- an internal iteration-start node;
- internal child nodes marked with the parent iteration ID;
- internal edges carrying the parent metadata;
- a valid output selector and output type;
- an explicit error policy and bounded parallelism.

Use stable child IDs. Keep each item independent when parallel execution is enabled. Do not perform unordered non-idempotent side effects in parallel.

## Loop

A Loop requires:

- supported Dify/DSL version evidence;
- loop variables and their initialization;
- loop-start/loop-end topology as required by the export;
- a deterministic termination condition;
- a strict maximum iteration count;
- child nodes and edges marked with the parent loop ID.

Reject unbounded loops. Prefer an external worker for long waits or asynchronous polling.

## Human Input

Copy the complete schema from the target version. User action IDs become outgoing edge handles; timeout uses the exact handle emitted by that version. Validate all action paths and the timeout path. Human delivery channels and contacts are workspace-bound and must be reconnected after import.

## Trigger nodes

Schedule, webhook, and plugin triggers replace or supplement normal entry behavior only when supported by the target version. Webhook URLs, subscription IDs, credentials, and schedules can be sanitized during export. Treat trigger-generated DSL as incomplete until the target workspace recreates those bindings.

## Agent nodes

Legacy Agent nodes and portable Agent v2 nodes have different schemas. For Agent v2, verify the top-level package/binding structures required by the target version. Never convert a legacy Agent node by changing a version field alone. Agent tools, skills, files, contacts, and credentials may not be portable.

## Validation boundary

The bundled validator checks common container references and graph consistency but is not a replacement for Dify's own node models. For these nodes, require at least target-source validation or real import before describing the artifact as compatible.

