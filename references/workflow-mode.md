# Workflow mode

Use `app.mode: workflow` for a stateless or externally orchestrated operation that runs once per invocation and returns structured outputs.

## Input and output contract

- Declare business inputs in the Start node's `variables` list.
- Prefer explicit types such as `text-input`, `paragraph`, `number`, `select`, `file`, `file-list`, `json`, or the target workspace's exported equivalent.
- Mark required inputs deliberately and set realistic length/file constraints.
- Terminate normal paths at one or more `end` nodes with explicitly declared outputs.
- Outputs should be stable contracts for API consumers; normalize LLM text into structured values in Code or extraction nodes when callers require JSON.

Minimal shape:

```text
Start → processing nodes → End
```

## Mode restrictions

Do not use Chatflow behavior as implicit input or state:

- no dependency on `sys.query` or `sys.files` for normal input;
- no conversation memory as a substitute for persisted backend state;
- no `answer` node as the normal terminal;
- no assumption that repeated runs share a conversation.

If a Workflow must process files, declare file inputs on Start. If it must continue a durable business process, accept an explicit state/version identifier and let an external system own isolation, persistence, retries, audit, and idempotency.

## Branching and failures

- Provide explicit false/default paths for conditions and classifiers.
- Do not reference an output from a mutually exclusive branch without an aggregator or default-producing node.
- Separate transport success from business success for HTTP/tool calls.
- Use bounded retries only for safe transient failures. Do not retry non-idempotent side effects unless the contract supplies idempotency protection.
- Long-running polling should normally be moved to a worker; return a task ID when asynchronous completion is appropriate.

## Delivery tests

At minimum test normal input, empty/invalid input, every branch outcome, files present/absent when relevant, external integration success/failure, and the final output schema.

