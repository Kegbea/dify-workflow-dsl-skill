# Common Dify App DSL structure

## Required top-level shape

Graph-based apps use this shape:

```yaml
app:
  description: ""
  icon: "🤖"
  icon_background: "#FFEAD5"
  icon_type: emoji
  mode: workflow
  name: Example
  use_icon_as_answer_icon: false
dependencies: []
kind: app
version: "0.7.0"
workflow:
  conversation_variables: []
  environment_variables: []
  features: {}
  graph:
    edges: []
    nodes: []
    viewport:
      x: 0
      y: 0
      zoom: 0.8
```

Set `app.mode` to exactly one of `workflow` or `advanced-chat` for this skill. Quote `version` and string-like IDs.

## Node wrapper

Every executable graph node has an outer canvas wrapper and a runtime payload in `data`:

```yaml
- data:
    selected: false
    title: Process input
    type: code
  height: 90
  id: process_input
  position: {x: 340, y: 220}
  positionAbsolute: {x: 340, y: 220}
  selected: false
  sourcePosition: right
  targetPosition: left
  type: custom
  width: 244
```

Use readable, stable IDs. Keep generated IDs within `[A-Za-z0-9_]{1,50}`. Human-facing titles may contain any appropriate language.

## Edge wrapper

```yaml
- data:
    isInIteration: false
    isInLoop: false
    sourceType: code
    targetType: llm
  id: process_input_source_analyze_target
  selected: false
  source: process_input
  sourceHandle: source
  target: analyze
  targetHandle: target
  type: custom
  zIndex: 0
```

For linear edges, use `sourceHandle: source` and `targetHandle: target`. Conditional handles are mode-independent but node-specific:

- IF/ELSE: case ID or `false`.
- Question Classifier: class ID.
- Human Input: action ID or the exported timeout handle.
- Container internals: include the parent iteration/loop metadata required by a matching export.

## Variables and references

Use selectors for structured binding:

```yaml
value_selector:
  - process_input
  - result
```

Use interpolation only in text-capable fields:

```text
{{#process_input.result#}}
{{#sys.query#}}
{{#conversation.memory#}}
{{#env.API_BASE_URL#}}
```

Prefer two-part selectors such as `[process_input, result]`, `[sys, query]`, `[conversation, memory]`, and `[env, API_BASE_URL]`. When editing an export that uses another form, preserve the target workspace's working representation.

## Graph invariants

- Exactly one normal Start node unless the chosen version and workflow intentionally use trigger entry nodes.
- Node IDs are unique.
- Edge IDs are unique.
- Every edge endpoint exists.
- `sourceType` and `targetType` match the referenced nodes' `data.type`.
- Every executable node is reachable from an entry.
- Normal Workflow paths reach End; Chatflow response paths reach Answer.
- Acyclic flow is the default. Cycles belong only inside supported Loop structures.
- Branch outputs that later converge use an appropriate aggregator or deterministic merge node.

## Workflow variables

Environment variables are read-only configuration. Conversation variables carry Chatflow state. Use UUID-like internal IDs and selectors consistent with a real target export. Do not put secrets into exported default values.

## Dependencies

Declare every marketplace, package, or GitHub plugin referenced by models and tools. Preserve exact dependency blocks from an export whenever possible. Missing or fabricated identifiers can allow YAML parsing but still prevent successful import or execution.

