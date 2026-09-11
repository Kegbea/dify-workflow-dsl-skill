# Behavioral evaluation scenarios

Use these prompts to evaluate the Skill with at least two capable coding agents. Run generated YAML through the bundled validator and, where possible, a matching Dify import environment.

1. Stateless text normalization: accept JSON text, validate required fields, return normalized JSON through End.
2. Workflow branching: classify an order amount into three deterministic bands plus a default/error path, then aggregate the branch output.
3. Workflow file processing: accept an optional file list, avoid empty-file failures, extract supported documents, summarize them, and return structured results.
4. Workflow HTTP integration: call a specified sandbox endpoint, distinguish transport and business success, and avoid unsafe retries.
5. Basic Chatflow: answer `sys.query` with an LLM and a reachable fallback Answer.
6. Stateful Chatflow: collect a brief across turns using a structured conversation variable and verify a fresh conversation is isolated.
7. Multimodal Chatflow: route files-present and text-only paths, use vision only on the file path, aggregate safely, and Answer.
8. RAG Chatflow: use a supplied target-workspace knowledge retrieval export and preserve its dataset/retrieval schema.
9. Invalid repair: fix malformed template IDs, mismatched IF handles, unreachable nodes, Code output mismatch, and wrong terminal mode in a supplied YAML.
10. Dynamic plugin: refuse to invent an unknown tool schema, request a minimal export, and still provide a clearly marked structural draft.

Pass criteria:

- Correct automatic mode selection.
- Minimal clarification only for import-blocking details.
- No Workflow/Chatflow field contamination.
- Complete YAML, not an illustrative fragment.
- Strict validator success or an explicit, justified limitation.
- Honest distinction among static validation, import verification, and runtime testing.

