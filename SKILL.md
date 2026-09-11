---
name: dify-workflow-dsl
description: Create, modify, repair, review, migrate, and validate import-ready Dify Workflow and Chatflow DSL YAML. Use for stateless workflow automation or multi-turn advanced-chat applications involving Dify graph nodes, models, knowledge retrieval, tools, HTTP, files, variables, memory, End nodes, or Answer nodes.
license: MIT
metadata:
  author: Kegbea
  version: "0.1.0"
---

# Dify Workflow DSL

Produce a complete Dify App DSL YAML that matches the user's business intent and the target workspace. Support both `workflow` and `advanced-chat`, but select exactly one mode for each generated app.

## Operating workflow

1. Determine the target Dify version and inspect a recent export from that workspace when available. For a new app with no stated target, assume Dify 1.17.x with App DSL `"0.7.0"`, state the assumption, and keep the version quoted.
2. Select the app mode:
   - Use `workflow` for one-shot processing, structured outputs, batch work, triggers, and backend/API orchestration.
   - Use `advanced-chat` for multi-turn interaction, conversation state, `sys.query`, chat uploads, memory, or streamed Answer responses.
   - If the request is genuinely ambiguous, ask only whether the app must retain multi-turn conversational context.
3. Clarify only facts that block a useful artifact: business inputs and outputs, required model/provider, external API contract, installed plugin identity, knowledge-base binding, state ownership, or required side effects. Use explicit placeholders for workspace-bound values that are unknown.
4. Write a compact intermediate representation before YAML: mode, inputs, outputs, node IDs/types, node input/output selectors, branches, containers, dependencies, and failure paths. For large graphs, build node payloads from this shared plan and assemble all nodes and edges centrally.
5. Read the common structure and exactly one mode guide, then load only the node and integration references needed by the graph.
6. Generate the complete YAML, including app metadata, quoted DSL version, dependencies, workflow variables, features, graph nodes, graph edges, and viewport.
7. Run the bundled validator in strict mode. Repair all errors. Keep a warning only when it represents an intentional, documented workspace-specific requirement.
8. Deliver the YAML together with the selected mode/version, validation result, placeholders to reconnect, and a concise Dify import/smoke-test checklist. Never claim runtime compatibility from static validation alone.

## Reference routing

Always read:

- [Common DSL structure](references/dsl-common.md)
- [Version and compatibility policy](references/version-policy.md)

Then read exactly one:

- For `workflow`: [Workflow mode](references/workflow-mode.md)
- For `advanced-chat`: [Chatflow mode](references/chatflow-mode.md)

Read when needed:

- Node selection and payloads: [Node reference](references/node-reference.md)
- Iteration, loops, parallel branches, and aggregation: [Graph patterns](references/graph-patterns.md)
- Models, plugins, tools, HTTP, knowledge bases, and secrets: [Dynamic integrations](references/dynamic-integrations.md)
- Validation behavior and delivery gates: [Validation](references/validation.md)

Start from a bundled template only when its mode and structure match the request:

- `assets/templates/minimal-workflow.yml`
- `assets/templates/minimal-chatflow.yml`

## Non-negotiable invariants

- Do not mix mode semantics. A normal `workflow` terminates at `end`; an `advanced-chat` produces user-visible responses through reachable `answer` nodes.
- Every executable node is reachable from the entry, every edge names existing endpoints, and every conditional outcome has a valid outgoing handle or an intentional terminal behavior.
- Template references use `{{#node_id.output#}}`. Prefer node IDs matching `[A-Za-z0-9_]{1,50}` so runtime interpolation remains portable.
- Structured selectors name an existing source and output. Keep edge `sourceType`/`targetType` synchronized with endpoint node types.
- Code node `main()` parameters match declared inputs, code compiles, returned keys match declared outputs, and output types reflect actual values.
- Preserve exact exported identifiers for models, plugins, tools, datasets, credentials, and dependencies. Never invent an exact dynamic plugin schema when no export or source metadata is available.
- Never include real API keys, passwords, tokens, credential IDs, private dataset IDs, personal data, or other secrets in a public artifact. Use environment variables or visible placeholders.
- Keep persistence, authorization, retries with durable state, long-running polling, audit, and cross-user isolation outside Dify unless the user explicitly chooses and validates a different architecture.

## Validation command

From the skill root:

```bash
python scripts/validate_dsl.py --strict --target-version 0.7.0 path/to/app.yml
```

If PyYAML is missing, install the dependency declared in `requirements.txt`. A successful result proves only the static invariants implemented by the validator; it does not prove provider credentials, plugin availability, dataset bindings, network calls, UI save/re-export behavior, or real execution.
