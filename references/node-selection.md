# Requirement-to-node selection

Choose the smallest graph that satisfies the contract.

| Requirement | Prefer |
|---|---|
| Generate or analyze language | LLM |
| Deterministic parsing, validation, normalization | Code |
| Render deterministic text | Template Transform |
| Branch on a value | IF/ELSE |
| Classify natural-language intent | Question Classifier |
| Extract named structured fields | Parameter Extractor or structured LLM output plus Code validation |
| Search Dify knowledge bases | Knowledge Retrieval |
| Call a remote REST service | HTTP Request |
| Call an installed provider capability | Tool |
| Process every array element | Iteration |
| Repeat until a bounded condition | Loop |
| Merge mutually exclusive branch values | Variable Aggregator |
| Persist Chatflow state | Assigner/Variable Assigner |
| Extract uploaded document text | Document Extractor |
| Filter, sort, or select list items | List Operator |
| Pause for a person | Human Input, only on supported versions |
| Start from schedule/webhook/plugin event | Matching Trigger node, only on supported versions |

## Selection rules

- Use Code for logic that must be deterministic; do not spend LLM calls on string parsing, schema checks, arithmetic, or routing that ordinary code can handle.
- Use an LLM when ambiguity or natural-language reasoning is essential. Give it the narrowest required context and a stable output contract.
- Do not use an Agent node when a fixed graph is sufficient. Agent autonomy is appropriate only when tool choice cannot be predetermined and the risk boundary is explicit.
- Use HTTP Request for a known endpoint contract. Use Tool when the workspace has an installed provider whose exact exported schema is available.
- Avoid hidden state. Pass node inputs explicitly and make state updates visible in the graph.
- For complex flows, separate acquisition, normalization, reasoning, validation, side effects, and response/output into distinct responsibilities.

## Unsupported or uncertain nodes

If a node type is not covered by a maintained fixture or matching official source:

1. Request or inspect a minimal export containing that node.
2. Preserve its payload shape and dependency identity.
3. Mark the result as requiring target-workspace import testing.
4. Do not invent undocumented parameters merely to make the YAML look complete.

